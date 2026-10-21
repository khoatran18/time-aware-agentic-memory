"""Cross-encoder rerank (decisions/07 đề xuất 4): chấm lại cặp (câu hỏi, chunk) để thay hoặc trộn với Semantic_Score.

Bi-encoder nhúng câu hỏi và chunk riêng rồi so vector; cross-encoder đọc hai văn bản cùng lúc nên phân biệt tốt hơn
đoạn nào chứa đáp án. Chỉ chấm vài chục ứng viên đầu nên chi phí nhỏ. Tùy chọn, mặc định tắt.
"""
from __future__ import annotations

import hashlib
import os
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from tam.schemas.chunk import Chunk

RERANK_MODES = ("replace", "mix")
RERANK_POOLS = ("final", "semantic")


class Reranker(Protocol):
    """Chấm điểm mỗi văn bản theo độ liên quan với câu hỏi (cao hơn = liên quan hơn); thang điểm tùy model."""

    def score(self, query: str, texts: Sequence[str]) -> list[float]:
        """Điểm cùng thứ tự với `texts`."""
        ...


class CrossEncoderReranker:
    """Bọc fastembed `TextCrossEncoder`; tải model lười (lần gọi đầu).

    `score_cache`: đường dẫn file sqlite lưu điểm theo (model, câu hỏi, văn bản) để các lượt đánh giá lặp cùng cặp không chấm lại
    (chỉ thêm, không xóa; an toàn khi nhiều tiến trình ghi cùng lúc nhờ WAL)."""

    def __init__(self, model_name: str, *, cache_dir: str | Path | None = None, threads: int | None = None,
                 score_cache: str | Path | None = None) -> None:
        self.model_name = model_name
        self._cache_dir = str(cache_dir) if cache_dir else None
        self._threads = threads or int(os.environ.get("TAM_RERANK_THREADS", "0")) or None  # biến môi trường để chạy song song nhiều lượt đánh giá mà không tranh luồng
        self._model = None
        self._db = None
        if score_cache:
            Path(score_cache).parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(str(score_cache), timeout=60)
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("CREATE TABLE IF NOT EXISTS scores (k TEXT PRIMARY KEY, v REAL NOT NULL)")
            self._db.commit()

    def _key(self, query: str, text: str) -> str:
        return hashlib.sha1(f"{self.model_name}\x00{query}\x00{text}".encode()).hexdigest()

    def score(self, query: str, texts: Sequence[str]) -> list[float]:
        """Điểm thô của cross-encoder (logit) cho từng văn bản."""
        if not texts:
            return []
        keys = [self._key(query, t) for t in texts]
        got: dict[str, float] = {}
        if self._db is not None:
            marks = ",".join("?" * len(keys))
            got = dict(self._db.execute(f"SELECT k, v FROM scores WHERE k IN ({marks})", keys).fetchall())
        miss = [i for i, k in enumerate(keys) if k not in got]
        if miss:
            if self._model is None:
                from fastembed.rerank.cross_encoder import TextCrossEncoder
                self._model = TextCrossEncoder(model_name=self.model_name, cache_dir=self._cache_dir, threads=self._threads)
            fresh = [float(s) for s in self._model.rerank(query, [texts[i] for i in miss])]
            for i, v in zip(miss, fresh, strict=True):
                got[keys[i]] = v
            if self._db is not None:
                self._db.executemany("INSERT OR REPLACE INTO scores VALUES (?, ?)", [(keys[i], v) for i, v in zip(miss, fresh, strict=True)])
                self._db.commit()
        return [got[k] for k in keys]


def minmax(values: Sequence[float]) -> list[float]:
    """Đưa về [0,1]; mọi giá trị bằng nhau thì trả 1.0 (không phân biệt được)."""
    if not values:
        return []
    lo, hi = min(values), max(values)
    return [1.0] * len(values) if hi == lo else [(v - lo) / (hi - lo) for v in values]


def mix_scores(old: Sequence[float], ce: Sequence[float], mode: str, alpha: float) -> list[float]:
    """Semantic mới của các ứng viên: `replace` = min-max điểm CE; `mix` = `alpha·old + (1-alpha)·minmax(CE)` (old đã ở [0,1])."""
    if mode not in RERANK_MODES:
        raise ValueError(f"rerank_mode không hợp lệ: {mode!r}; cho phép {RERANK_MODES}")
    norm = minmax(ce)
    if mode == "replace":
        return norm
    return [alpha * o + (1 - alpha) * c for o, c in zip(old, norm, strict=True)]


def rerank_text(chunk: Chunk, *, with_time: bool) -> str:
    """Văn bản đưa cho cross-encoder; `with_time` ghép khoảng hiệu lực (năm) ở đầu để model thấy được thời gian."""
    if not with_time or chunk.start_time is None:
        return chunk.text
    end = "now" if chunk.end_time is None else str(chunk.end_time.year)
    return f"[{chunk.start_time.year}-{end}] {chunk.text}"
