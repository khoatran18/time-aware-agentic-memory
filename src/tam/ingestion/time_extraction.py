"""Trích khoảng hiệu lực [start_time, end_time] của chunk bằng LLM (role `ingestion_time`), rồi chuẩn hóa.

Một lệnh gọi LLM cho cả lô chunk của cùng tài liệu: rẻ hơn gọi từng chunk và LLM thấy được các mốc lân cận để hiểu
"năm sau". Chunk không trích được mốc thì KHÔNG vào kho time-aware (bất biến của đồ án).
"""
from __future__ import annotations

import calendar
import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from tam.config.logging import get_logger
from tam.ingestion.types import RawChunk, TimeResult, TimeSpan
from tam.llm.cache import JsonCache
from tam.llm.structured import invoke_structured
from tam.schemas.domains import MAX_DOMAINS_PER_CHUNK, domains_prompt, normalize_domains

logger = get_logger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "llm" / "prompts" / "ingestion_time.md"
_PARTIAL_DATE = re.compile(r"^(-?)(\d{1,9})(?:-(\d{1,2}))?(?:-(\d{1,2}))?$")
# Dấu hiệu "còn hiệu lực" mà câu bằng chứng của `ongoing` phải chứa (heuristic cho tiếng Anh, docs/decisions/02)
_ONGOING_CUES = re.compile(
    r"\b(since|present|current|currently|still|remains?|remaining|continues?|continuing|to date|this day|today|now|ongoing|"
    r"incumbent|as of|up to the)\b", re.IGNORECASE)


class ChunkTime(BaseModel):
    """Mốc thời gian LLM trả cho một chunk."""

    index: int = Field(description="Index of the chunk this item refers to")
    start: str | None = Field(default=None, description="Earliest date: YYYY, YYYY-MM or YYYY-MM-DD; null if none")
    reason_domain: str = Field(
        default="",
        description="One short sentence: which words or facts in the chunk make you choose these topic labels. "
                    "Write it BEFORE choosing `domain`",
    )
    domain: list[str] = Field(
        default_factory=list,
        description=f"0 to {MAX_DOMAINS_PER_CHUNK} topic labels from the closed list, dominant topic first",
    )
    reason_end_date: str = Field(
        default="",
        description="One short sentence: why `end` and `ongoing` have these values (which words or chunk show the "
                    "situation stopped or continues, or that nothing says so). Write it BEFORE deciding end/ongoing",
    )
    ongoing_evidence: str = Field(
        default="",
        description="Only when `ongoing` is true: the exact words copied from the chunks that show the situation "
                    "still continues (e.g. 'since 2012', 'is still at the club'). Empty when `ongoing` is false",
    )
    end: str | None = Field(default=None, description="Latest date, same format; null if ongoing or none")
    ongoing: bool = Field(default=False, description="True if the situation continues to the present")


class BatchTimes(BaseModel):
    """Đầu ra có cấu trúc: một mục cho mỗi chunk."""

    items: list[ChunkTime]


_BEFORE_COMMON_ERA = datetime(1, 1, 1, tzinfo=timezone.utc)


def parse_partial_date(raw: str, *, end: bool) -> datetime:
    """'1985' / '1985-06' / '1985-06-15' -> datetime UTC. Mốc đầu lấy ngày đầu kỳ, mốc cuối lấy ngày cuối kỳ (bao gồm).

    Chỉ-năm: start -> YYYY-01-01, end -> YYYY-12-31. Chỉ-tháng: ngày 1 hoặc ngày cuối tháng.

    Năm trước Công nguyên viết dạng âm ('-44', '-300000') hoặc '0'. `datetime` không biểu diễn được năm < 1 nên mọi mốc
    đó bị chặn về `0001-01-01` (mất thứ tự giữa các mốc trước Công nguyên, nhưng vẫn đứng trước mọi `t_req` thực tế).
    """
    m = _PARTIAL_DATE.match(raw.strip())
    if not m:
        raise ValueError(f"không phải ngày dạng YYYY[-MM[-DD]]: {raw!r}")
    year = -int(m.group(2)) if m.group(1) else int(m.group(2))
    month = int(m.group(3)) if m.group(3) else None
    day = int(m.group(4)) if m.group(4) else None
    if year < 1:
        return _BEFORE_COMMON_ERA
    if year > 9999:
        raise ValueError(f"năm không hỗ trợ: {raw!r}")
    if month is None:
        month, day = (12, 31) if end else (1, 1)
    elif day is None:
        day = calendar.monthrange(year, month)[1] if end else 1
    return datetime(year, month, day, tzinfo=timezone.utc)


def to_span(item: ChunkTime) -> TimeResult:
    """Chuẩn hóa một mục LLM trả thành TimeSpan, hoặc giải thích vì sao bỏ."""
    note = item.reason_end_date
    domains = tuple(normalize_domains(item.domain))
    if not item.start:
        return TimeResult(None, "no_time", item.ongoing, note, domains, item.reason_domain, item.ongoing_evidence)
    try:
        start = parse_partial_date(item.start, end=False)
        end = None
        if not item.ongoing:
            end = parse_partial_date(item.end or item.start, end=True)
    except ValueError as exc:
        logger.warning("Mốc thời gian không hợp lệ (index=%s): %s", item.index, exc)
        return TimeResult(None, "invalid_time", item.ongoing, note, domains, item.reason_domain, item.ongoing_evidence)
    if end is not None and end < start:
        logger.warning("end < start (index=%s): start=%s end=%s", item.index, item.start, item.end)
        return TimeResult(None, "invalid_time", item.ongoing, note, domains, item.reason_domain, item.ongoing_evidence)
    return TimeResult(
        TimeSpan(start, end), None, item.ongoing, note, domains, item.reason_domain, item.ongoing_evidence)


def _norm(text: str) -> str:
    """Chữ thường, gộp khoảng trắng; dùng để so khớp câu bằng chứng với văn bản."""
    return re.sub(r"\s+", " ", text).strip().lower()


def ongoing_evidence_ok(evidence: str, corpus_norm: str) -> bool:
    """Bằng chứng `ongoing` đạt khi (a) nằm nguyên văn trong văn bản của lô chunk (cả trang) và (b) chứa dấu hiệu còn hiệu lực.

    Cho phép bằng chứng ở chunk khác của trang: cùng một sự việc có thể được nói tiếp ở chunk sau (vd chunk 0 "joined City
    in 2010", chunk 1 "is still at the club"). Đã thử bắt bằng chứng nằm trong chính chunk rồi bỏ, xem decisions/02.

    Bỏ qua dấu ngoặc kép bao quanh. Đây là kiểm tra heuristic cho tiếng Anh; xem docs/decisions/02_END_TIME_ONGOING.md.
    """
    ev = _norm(evidence).strip("\"'` ")
    return bool(ev) and ev in corpus_norm and bool(_ONGOING_CUES.search(ev))


class TimeExtractor:
    """Gọi LLM trích mốc thời gian cho các chunk của một tài liệu; LLM được tiêm vào."""

    def __init__(
        self, llm: BaseChatModel, *, prompt: str | None = None, batch_size: int = 30, max_attempts: int = 3,
        cache: JsonCache | None = None,
    ) -> None:
        """`llm`: chat model (role ingestion_time). `batch_size`: số chunk tối đa trong một lệnh gọi."""
        self._llm = llm
        self._chain = llm.with_structured_output(BatchTimes)
        self._prompt = prompt if prompt is not None else PROMPT_PATH.read_text(encoding="utf-8")
        self._batch_size = batch_size
        self._max_attempts = max_attempts
        self._cache = cache

    def extract(self, doc_title: str, chunks: Sequence[RawChunk]) -> list[TimeResult]:
        """Kết quả cùng thứ tự với `chunks`. Chunk LLM bỏ sót được coi là không có mốc."""
        results: list[TimeResult] = []
        for lo in range(0, len(chunks), self._batch_size):
            results.extend(self._extract_batch(doc_title, chunks[lo:lo + self._batch_size]))
        return results

    def _extract_batch(self, doc_title: str, batch: Sequence[RawChunk]) -> list[TimeResult]:
        """Một lệnh gọi LLM cho một lô; index trong lô bắt đầu từ 0."""
        system = self._prompt.replace("{doc_title}", doc_title).replace("{domains}", domains_prompt())
        body = "\n\n".join(f"[{i}] {c.text}" for i, c in enumerate(batch))
        messages = [("system", system), ("human", body)]
        out = invoke_structured(self._llm, self._chain, BatchTimes, messages, max_attempts=self._max_attempts, cache=self._cache)
        if out is None:  # lỗi định dạng sau mọi lần thử: không đoán, đánh dấu riêng để không lẫn với "không có mốc"
            return [TimeResult(None, "llm_error") for _ in batch]
        corpus = _norm(" ".join(c.text for c in batch))
        downgraded: set[int] = set()
        for item in out.items:
            if item.ongoing and not ongoing_evidence_ok(item.ongoing_evidence, corpus):
                logger.warning("Hạ ongoing (chunk %d): bằng chứng không đạt: %r", item.index, item.ongoing_evidence[:80])
                item.ongoing = False
                downgraded.add(item.index)
            logger.debug("Mốc chunk %d: start=%s end=%s ongoing=%s | %s | %s", item.index, item.start, item.end,
                         item.ongoing, item.reason_end_date, item.reason_domain)
        by_index = {item.index: item for item in out.items}
        results = []
        for i in range(len(batch)):
            if i not in by_index:
                results.append(TimeResult(None, "no_time"))
                continue
            res = to_span(by_index[i])
            results.append(replace(res, ongoing_downgraded=True) if i in downgraded else res)
        return results
