"""Time Extractor: câu hỏi + T_now + LLM -> ProfiledQuery (tầng Query Processing, design 02 mục 3.2)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from dateutil.parser import isoparse
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from tam.config.logging import get_logger
from tam.retrieval.temporal.filters import FACET_KEYS
from tam.schemas.query import ProfiledQuery

logger = get_logger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "llm" / "prompts" / "time_extractor.md"


class Extraction(BaseModel):
    """Đầu ra có cấu trúc mà LLM phải trả (dùng với `with_structured_output`)."""

    semantic_query: str = Field(description="What to search for, without the time expression and filler words")
    t_req: str | None = Field(default=None, description="Absolute point in time as ISO YYYY-MM-DD; null if the question mentions no time")
    domain: str | None = Field(default=None, description="Lowercase English domain word, only if the question states it explicitly")
    country: str | None = Field(default=None, description="ISO 3166-1 alpha-2 country code, only if the question states it explicitly")


def parse_t_req(raw: str) -> datetime:
    """Đọc mốc ISO của LLM (chấp nhận "2020", "2020-03", "2020-03-01", có hoặc không giờ) thành datetime UTC."""
    parsed = isoparse(raw.strip())
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed.astimezone(timezone.utc)


class Profiler:
    """Biến câu hỏi thô thành ProfiledQuery. LLM và đồng hồ đều được tiêm vào, không đọc gì từ bên ngoài."""

    def __init__(self, llm: BaseChatModel, *, prompt: str | None = None) -> None:
        """`llm`: chat model (role time_extractor). `prompt`: mẫu có chỗ {t_now}; mặc định đọc time_extractor.md."""
        self._chain = llm.with_structured_output(Extraction)
        self._prompt = prompt if prompt is not None else PROMPT_PATH.read_text(encoding="utf-8")

    def profile(self, question: str, t_now: datetime) -> ProfiledQuery:
        """Tách `semantic_query`, `t_req`, `filters` của câu hỏi. `t_now` luôn được tiêm vào system prompt."""
        if t_now.tzinfo is None:
            t_now = t_now.replace(tzinfo=timezone.utc)
        system = self._prompt.replace("{t_now}", t_now.date().isoformat())
        out = self._chain.invoke([("system", system), ("human", question)])
        if isinstance(out, dict):
            out = Extraction.model_validate(out)

        if out.t_req:
            try:
                t_req = parse_t_req(out.t_req)
            except ValueError as exc:
                raise ValueError(f"LLM trả t_req không phải ISO: {out.t_req!r} (câu hỏi: {question!r})") from exc
        else:
            t_req = t_now.astimezone(timezone.utc)  # không nhắc thời gian = hỏi về hiện tại
        if t_req > t_now:
            logger.warning("t_req %s nằm sau T_now %s (câu hỏi: %r)", t_req.date(), t_now.date(), question)

        filters = {}
        if out.domain and out.domain.strip():
            filters["domain"] = out.domain.strip().lower()
        if out.country and out.country.strip():
            filters["country"] = out.country.strip().upper()
        assert set(filters) <= FACET_KEYS

        semantic_query = out.semantic_query.strip() or question.strip()
        logger.info("Profile: T_now=%s T_req=%s filters=%s semantic_query=%r", t_now.date(), t_req.date(), filters, semantic_query)
        return ProfiledQuery(semantic_query=semantic_query, t_req=t_req, filters=filters)
