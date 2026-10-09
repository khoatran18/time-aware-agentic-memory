"""Trích khoảng hiệu lực [start_time, end_time] của chunk bằng LLM (role `ingestion_time`), rồi chuẩn hóa.

Một lệnh gọi LLM cho cả lô chunk của cùng tài liệu: rẻ hơn gọi từng chunk và LLM thấy được các mốc lân cận để hiểu
"năm sau". Chunk không trích được mốc thì KHÔNG vào kho time-aware (bất biến của đồ án).
"""
from __future__ import annotations

import calendar
import re
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from tam.config.logging import get_logger
from tam.ingestion.types import RawChunk, TimeResult, TimeSpan

logger = get_logger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "llm" / "prompts" / "ingestion_time.md"
_PARTIAL_DATE = re.compile(r"^(\d{1,4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?$")


class ChunkTime(BaseModel):
    """Mốc thời gian LLM trả cho một chunk."""

    index: int = Field(description="Index of the chunk this item refers to")
    start: str | None = Field(default=None, description="Earliest date: YYYY, YYYY-MM or YYYY-MM-DD; null if none")
    end: str | None = Field(default=None, description="Latest date, same format; null if ongoing or none")
    ongoing: bool = Field(default=False, description="True if the situation continues to the present")


class BatchTimes(BaseModel):
    """Đầu ra có cấu trúc: một mục cho mỗi chunk."""

    items: list[ChunkTime]


def parse_partial_date(raw: str, *, end: bool) -> datetime:
    """'1985' / '1985-06' / '1985-06-15' -> datetime UTC. Mốc đầu lấy ngày đầu kỳ, mốc cuối lấy ngày cuối kỳ (bao gồm).

    Chỉ-năm: start -> YYYY-01-01, end -> YYYY-12-31. Chỉ-tháng: ngày 1 hoặc ngày cuối tháng. Năm < 1 bị từ chối.
    """
    m = _PARTIAL_DATE.match(raw.strip())
    if not m:
        raise ValueError(f"không phải ngày dạng YYYY[-MM[-DD]]: {raw!r}")
    year = int(m.group(1))
    month = int(m.group(2)) if m.group(2) else None
    day = int(m.group(3)) if m.group(3) else None
    if year < 1:
        raise ValueError(f"năm không hỗ trợ: {raw!r}")
    if month is None:
        month, day = (12, 31) if end else (1, 1)
    elif day is None:
        day = calendar.monthrange(year, month)[1] if end else 1
    return datetime(year, month, day, tzinfo=timezone.utc)


def to_span(item: ChunkTime) -> TimeResult:
    """Chuẩn hóa một mục LLM trả thành TimeSpan, hoặc giải thích vì sao bỏ."""
    if not item.start:
        return TimeResult(None, "no_time")
    try:
        start = parse_partial_date(item.start, end=False)
        end = None
        if not item.ongoing:
            end = parse_partial_date(item.end or item.start, end=True)
    except ValueError as exc:
        logger.warning("Mốc thời gian không hợp lệ (index=%s): %s", item.index, exc)
        return TimeResult(None, "invalid_time")
    if end is not None and end < start:
        logger.warning("end < start (index=%s): start=%s end=%s", item.index, item.start, item.end)
        return TimeResult(None, "invalid_time")
    return TimeResult(TimeSpan(start, end))


class TimeExtractor:
    """Gọi LLM trích mốc thời gian cho các chunk của một tài liệu; LLM được tiêm vào."""

    def __init__(self, llm: BaseChatModel, *, prompt: str | None = None, batch_size: int = 30) -> None:
        """`llm`: chat model (role ingestion_time). `batch_size`: số chunk tối đa trong một lệnh gọi."""
        self._chain = llm.with_structured_output(BatchTimes)
        self._prompt = prompt if prompt is not None else PROMPT_PATH.read_text(encoding="utf-8")
        self._batch_size = batch_size

    def extract(self, doc_title: str, chunks: Sequence[RawChunk]) -> list[TimeResult]:
        """Kết quả cùng thứ tự với `chunks`. Chunk LLM bỏ sót được coi là không có mốc."""
        results: list[TimeResult] = []
        for lo in range(0, len(chunks), self._batch_size):
            results.extend(self._extract_batch(doc_title, chunks[lo:lo + self._batch_size]))
        return results

    def _extract_batch(self, doc_title: str, batch: Sequence[RawChunk]) -> list[TimeResult]:
        """Một lệnh gọi LLM cho một lô; index trong lô bắt đầu từ 0."""
        system = self._prompt.replace("{doc_title}", doc_title)
        body = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(batch))
        out = self._chain.invoke([("system", system), ("human", body)])
        if isinstance(out, dict):
            out = BatchTimes.model_validate(out)
        by_index = {item.index: item for item in out.items}
        return [to_span(by_index[i]) if i in by_index else TimeResult(None, "no_time") for i in range(len(batch))]
