"""Time Extractor trả KHOẢNG thời gian `[qs, qe]` thay vì một điểm (decisions/07 đề xuất 1). Không thay `Profiler`; dùng thêm khi cần.

LLM ghi mốc một phần (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`) ở độ mịn câu hỏi nêu cùng `bound` (exact/after/before/none); `time_range.expand_range` đổi
thành ngày đầu và ngày cuối. `t_req` của kết quả là `qs` (tương thích mọi nơi đang dùng `t_req`), `t_end` là `qe`.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from tam.config.logging import get_logger
from tam.llm.cache import CacheStore
from tam.llm.structured import invoke_structured
from tam.query.time_range import BEFORE_LOWER_MODES, Bound, expand_range
from tam.retrieval.temporal.filters import FACET_KEYS
from tam.schemas.query import ProfiledQuery

logger = get_logger(__name__)

PROMPT_VERSION = "v2"  # v1 (một điểm) vẫn nằm ở time_extractor_v1.md và query/profiler.py; xem decisions/03
PROMPT_PATH = Path(__file__).resolve().parents[1] / "llm" / "prompts" / f"time_extractor_{PROMPT_VERSION}.md"


class RangeExtraction(BaseModel):
    """Đầu ra có cấu trúc mà LLM phải trả (dùng với `with_structured_output`)."""

    semantic_query: str = Field(description="What to search for, without the time expression and filler words")
    t_start: str | None = Field(
        default=None, description="Start of the period at the precision the question uses: YYYY, YYYY-MM or YYYY-MM-DD; null if no time is mentioned")
    t_end: str | None = Field(
        default=None, description="End of a two-ended period at its own precision (YYYY, YYYY-MM, YYYY-MM-DD); null for a single time unit, after/before, or no time")
    bound: Bound = Field(default="exact", description="exact (the named time itself) | after | before | none (no time mentioned)")
    use_t_now: bool = Field(
        default=False, description="True if the answer depends on today's date (relative time, now/current/latest, or no time mentioned)")
    domain: str | None = Field(default=None, description="Lowercase English domain word, only if the question states it explicitly")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code, only if the question states it explicitly")


class RangeProfiler:
    """Biến câu hỏi thô thành ProfiledQuery có `t_req` (= qs) và `t_end` (= qe). LLM và đồng hồ đều được tiêm vào."""

    def __init__(self, llm: BaseChatModel, *, prompt: str | None = None, cache: CacheStore | None = None, before_lower: str = "point") -> None:
        """`before_lower`: cận dưới của "before X": `point` (qs = qe = X, mặc định) hoặc `min` (mở về 0001-01-01), xem `expand_range`."""
        if before_lower not in BEFORE_LOWER_MODES:
            raise ValueError(f"before_lower không hợp lệ: {before_lower!r}; cho phép {BEFORE_LOWER_MODES}")
        self._llm, self._cache, self._before_lower = llm, cache, before_lower
        self._chain = llm.with_structured_output(RangeExtraction)
        self._prompt = prompt if prompt is not None else PROMPT_PATH.read_text(encoding="utf-8")

    def extract(self, question: str, t_now: datetime) -> RangeExtraction:
        """Gọi LLM, trả đầu ra thô (cache theo prompt chưa thay {t_now}; câu phụ thuộc T_now không ghi cache vì kết quả đổi theo ngày)."""
        if t_now.tzinfo is None:
            t_now = t_now.replace(tzinfo=timezone.utc)
        system = self._prompt.replace("{t_now}", t_now.date().isoformat())
        out = invoke_structured(self._llm, self._chain, RangeExtraction, [("system", system), ("human", question)],
                                cache=self._cache, key_messages=[("system", self._prompt), ("human", question)],
                                cacheable=lambda e: not e.use_t_now and bool(e.t_start))
        if out is None:
            raise ValueError(f"LLM không trả JSON hợp lệ cho câu hỏi: {question!r}")
        return out

    def profile(self, question: str, t_now: datetime) -> ProfiledQuery:
        """Tách `semantic_query`, khoảng `[t_req, t_end]`, `filters` của câu hỏi."""
        return self.build(self.extract(question, t_now), question, t_now)

    def build(self, out: RangeExtraction, question: str, t_now: datetime) -> ProfiledQuery:
        """Từ đầu ra thô của LLM dựng ProfiledQuery (tách riêng để script ghi được cả đầu ra thô mà không gọi LLM hai lần)."""
        if t_now.tzinfo is None:
            t_now = t_now.replace(tzinfo=timezone.utc)
        try:
            qs, qe = expand_range(out.t_start, out.t_end, out.bound, t_now, before_lower=self._before_lower)
        except ValueError as exc:
            raise ValueError(f"LLM trả mốc thời gian không hợp lệ: {exc} (câu hỏi: {question!r})") from exc
        filters = {}
        if out.domain and out.domain.strip():
            filters["domain"] = out.domain.strip().lower()
        if out.country and out.country.strip():
            filters["country"] = out.country.strip().upper()
        assert set(filters) <= FACET_KEYS
        semantic_query = out.semantic_query.strip() or question.strip()
        logger.info("RangeProfile: T_now=%s [%s, %s] bound=%s filters=%s semantic_query=%r", t_now.date(), qs.date(), qe.date(), out.bound, filters, semantic_query)
        return ProfiledQuery(semantic_query=semantic_query, t_req=qs, t_end=qe, filters=filters)
