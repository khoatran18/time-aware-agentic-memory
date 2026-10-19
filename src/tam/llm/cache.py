"""Cache kết quả LLM trên đĩa: cùng (schema, model, nội dung prompt) thì dùng lại, không gọi LLM nữa.

Khóa gồm tên schema, định danh model được cấu hình và toàn bộ messages (đã gồm prompt hệ thống), nên đổi prompt hoặc đổi model
trong config thì tự trượt cache. Giới hạn: `model` ở đây là tên trong config (vd combo `basic-gemini-3.5-flash-lite` của 9router);
combo có thể đổi model phía sau, muốn buộc gọi lại dùng `refresh=True`.

Hai nơi lưu song song, cùng giao diện `CacheStore`:
- `SqliteCache`: **nguồn sự thật**, một file `.sqlite`, truy vấn được để phân tích (SELECT theo model, schema, thời gian...).
- `JsonViewCache`: **bản xem nhanh**, một file `.json` {hash: mục}, mở bằng trình soạn thảo. Không bao giờ được đọc để quyết định
  trúng cache trong `MirroredCache`; mất hoặc cũ thì dựng lại từ SQLite.
`MirroredCache` ghép hai phần: đọc từ SQLite, ghi vào cả hai. Dùng `open_cache(thư mục)` để tạo.
"""
from __future__ import annotations

import atexit
import hashlib
import json
import os
import sqlite3
import tempfile
from abc import ABC, abstractmethod
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tam.config.logging import get_logger

logger = get_logger(__name__)

PREVIEW_CHARS = 160


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CacheStore(ABC):
    """Giao diện chung của mọi nơi lưu cache: `key`, `get`, `put`, `close`, bộ đếm `hits`/`misses`."""

    hits: int
    misses: int

    @staticmethod
    def key(*parts: str) -> str:
        """SHA-256 của các phần ghép lại (có dấu phân cách để ("ab","c") khác ("a","bc"))."""
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    @abstractmethod
    def get(self, key: str) -> dict[str, Any] | None:
        """Giá trị đã lưu hoặc None (chưa có, đang refresh, hoặc dữ liệu hỏng)."""

    @abstractmethod
    def put(self, key: str, value: dict[str, Any], meta: dict[str, str] | None = None) -> None:
        """Ghi giá trị. `meta` (tùy chọn): `schema`, `model`, `preview` để tiện phân tích; không tham gia khóa."""

    def close(self) -> None:
        """Ghi nốt dữ liệu còn đệm và đóng tài nguyên; gọi nhiều lần không sao."""


# ======================= Phần 1: SQLite (nguồn sự thật) =======================
class SqliteCache(CacheStore):
    """Bảng `cache(key, schema, model, created_at, preview, value)`; `value` là JSON dạng chuỗi.

    Bật WAL và chờ khóa tối đa 30 giây, nên chạy ingestion và Profiler song song không hỏng dữ liệu.
    """

    def __init__(self, path: str | Path, *, refresh: bool = False) -> None:
        """`refresh=True`: bỏ qua mục đã có (luôn coi là chưa có) nhưng vẫn ghi đè kết quả mới."""
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._refresh = refresh
        self.hits = 0
        self.misses = 0
        self._db = sqlite3.connect(self._path, timeout=30)
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, schema TEXT, model TEXT, created_at TEXT, "
            "preview TEXT, value TEXT NOT NULL)"
        )
        self._db.commit()

    def get(self, key: str) -> dict[str, Any] | None:
        """Giá trị đã lưu hoặc None."""
        if not self._refresh:
            row = self._db.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
            if row is not None:
                try:
                    value = json.loads(row[0])
                    self.hits += 1
                    return value
                except ValueError:
                    logger.warning("Cache hỏng, bỏ qua: %s", key)
        self.misses += 1
        return None

    def put(self, key: str, value: dict[str, Any], meta: dict[str, str] | None = None) -> None:
        """Ghi hoặc ghi đè một mục."""
        meta = meta or {}
        self._db.execute(
            "INSERT OR REPLACE INTO cache (key, schema, model, created_at, preview, value) VALUES (?, ?, ?, ?, ?, ?)",
            (key, meta.get("schema"), meta.get("model"), _now(), meta.get("preview"), json.dumps(value, ensure_ascii=False)),
        )
        self._db.commit()

    def count(self) -> int:
        """Số mục đang lưu."""
        return self._db.execute("SELECT COUNT(*) FROM cache").fetchone()[0]

    def entries(self) -> Iterator[tuple[str, dict[str, Any]]]:
        """(khóa, mục) theo thời gian ghi, mục = {schema, model, created_at, preview, value}; dùng để dựng bản JSON."""
        for key, schema, model, created_at, preview, value in self._db.execute(
            "SELECT key, schema, model, created_at, preview, value FROM cache ORDER BY created_at, key"
        ):
            yield key, {"schema": schema, "model": model, "created_at": created_at, "preview": preview, "value": json.loads(value)}

    def close(self) -> None:
        """Đóng kết nối."""
        try:
            self._db.close()
        except sqlite3.ProgrammingError:
            pass


# ======================= Phần 2: JSON (bản xem nhanh) =======================
class JsonViewCache(CacheStore):
    """Một file JSON {hash: {schema, model, created_at, preview, value}}, ghi nguyên tử (file tạm rồi đổi tên).

    Giữ toàn bộ trong bộ nhớ và chỉ ghi ra đĩa mỗi `flush_every` lần `put` hoặc khi `close`/thoát chương trình, vì ghi lại cả file
    mỗi lần sẽ chậm khi số mục tăng. Chết đột ngột chỉ mất tối đa `flush_every` mục ở bản xem này (SQLite vẫn đủ).
    """

    def __init__(self, path: str | Path, *, flush_every: int = 20) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._flush_every = flush_every
        self._dirty = 0
        self.hits = 0
        self.misses = 0
        self._data: dict[str, dict[str, Any]] = {}
        try:
            self._data = json.loads(self._path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            pass
        except (OSError, ValueError):
            logger.warning("File JSON cache hỏng, sẽ dựng lại từ SQLite: %s", self._path)

    def get(self, key: str) -> dict[str, Any] | None:
        """Giá trị trong bản xem (MirroredCache không dùng hàm này để quyết định trúng cache)."""
        entry = self._data.get(key)
        if entry is None:
            self.misses += 1
            return None
        self.hits += 1
        return entry["value"]

    def put(self, key: str, value: dict[str, Any], meta: dict[str, str] | None = None) -> None:
        """Ghi một mục vào bộ nhớ; ra đĩa theo chu kỳ."""
        meta = meta or {}
        self._data[key] = {
            "schema": meta.get("schema"), "model": meta.get("model"), "created_at": _now(),
            "preview": meta.get("preview"), "value": value,
        }
        self._dirty += 1
        if self._dirty >= self._flush_every:
            self.flush()

    def keys(self) -> set[str]:
        """Các khóa đang có trong bản xem."""
        return set(self._data)

    def replace_all(self, entries: Iterator[tuple[str, dict[str, Any]]]) -> None:
        """Thay toàn bộ nội dung bằng `entries` (dựng lại từ SQLite) rồi ghi ra đĩa."""
        self._data = dict(entries)
        self._dirty = 1
        self.flush()

    def flush(self) -> None:
        """Ghi file nếu có thay đổi chưa ghi."""
        if not self._dirty:
            return
        fd, tmp = tempfile.mkstemp(dir=self._path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, self._path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
        self._dirty = 0

    def close(self) -> None:
        """Ghi nốt."""
        self.flush()


# ======================= Ghép hai phần =======================
class MirroredCache(CacheStore):
    """Đọc từ SQLite (nguồn sự thật), ghi vào cả SQLite lẫn bản JSON.

    Lúc mở, nếu bản JSON thiếu hoặc lệch khóa so với SQLite thì dựng lại từ SQLite. Tự đóng (ghi nốt JSON) khi thoát chương trình.
    """

    def __init__(self, primary: SqliteCache, mirror: JsonViewCache) -> None:
        self._primary, self._mirror = primary, mirror
        if mirror.keys() != {k for k, _ in primary.entries()}:
            logger.info("Dựng lại bản JSON từ SQLite (%d mục)", primary.count())
            mirror.replace_all(primary.entries())
        atexit.register(self.close)

    @property
    def hits(self) -> int:  # type: ignore[override]
        """Số lần trúng cache (đếm ở SQLite)."""
        return self._primary.hits

    @property
    def misses(self) -> int:  # type: ignore[override]
        """Số lần trượt cache (đếm ở SQLite)."""
        return self._primary.misses

    def get(self, key: str) -> dict[str, Any] | None:
        """Chỉ đọc SQLite."""
        return self._primary.get(key)

    def put(self, key: str, value: dict[str, Any], meta: dict[str, str] | None = None) -> None:
        """Ghi SQLite trước (nguồn sự thật), rồi bản JSON."""
        self._primary.put(key, value, meta)
        self._mirror.put(key, value, meta)

    def close(self) -> None:
        """Ghi nốt JSON rồi đóng SQLite."""
        self._mirror.close()
        self._primary.close()


def open_cache(directory: str | Path, *, refresh: bool = False) -> MirroredCache:
    """Mở cache chuẩn của dự án: `<thư mục>/cache.sqlite` (nguồn sự thật) và `<thư mục>/cache.json` (xem nhanh)."""
    d = Path(directory)
    return MirroredCache(SqliteCache(d / "cache.sqlite", refresh=refresh), JsonViewCache(d / "cache.json"))
