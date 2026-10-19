"""Cache kết quả LLM trên đĩa: cùng (schema, model, nội dung prompt) thì dùng lại, không gọi LLM nữa.

Khóa gồm tên schema, định danh model được cấu hình và toàn bộ messages (đã gồm prompt hệ thống), nên đổi prompt hoặc đổi model
trong config thì tự trượt cache. Giới hạn: `model` ở đây là tên trong config (vd combo `basic-llm` của 9router), mà model thật
phía sau combo có thể đổi theo thời gian; muốn buộc gọi lại dùng `refresh=True`.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from tam.config.logging import get_logger

logger = get_logger(__name__)


class JsonCache:
    """Mỗi mục một file JSON: <thư mục>/<2 ký tự đầu của khóa>/<khóa>.json. Ghi nguyên tử nên chạy song song không hỏng file."""

    def __init__(self, directory: str | Path, *, refresh: bool = False) -> None:
        """`refresh=True`: bỏ qua mục đã có (luôn coi là chưa có) nhưng vẫn ghi đè kết quả mới."""
        self._dir = Path(directory)
        self._refresh = refresh
        self.hits = 0
        self.misses = 0

    @staticmethod
    def key(*parts: str) -> str:
        """SHA-256 của các phần ghép lại (có dấu phân cách để ("ab","c") khác ("a","bc"))."""
        return hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()

    def _path(self, key: str) -> Path:
        return self._dir / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        """Giá trị đã lưu hoặc None (chưa có, đang refresh, hoặc file hỏng)."""
        if not self._refresh:
            try:
                value = json.loads(self._path(key).read_text(encoding="utf-8"))
                self.hits += 1
                return value
            except FileNotFoundError:
                pass
            except (OSError, ValueError):
                logger.warning("Cache hỏng, bỏ qua: %s", self._path(key))
        self.misses += 1
        return None

    def put(self, key: str, value: dict[str, Any]) -> None:
        """Ghi giá trị; ghi ra file tạm rồi đổi tên để không để lại file dở dang."""
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(value, f, ensure_ascii=False)
            os.replace(tmp, path)
        except BaseException:
            Path(tmp).unlink(missing_ok=True)
            raise
