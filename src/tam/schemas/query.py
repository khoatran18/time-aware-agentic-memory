"""ProfiledQuery: đầu ra của Time Extractor, đầu vào của mọi Retriever."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Mechanism = Literal["temporal", "timeline", "conflict"]


class ProfiledQuery(BaseModel):
    """Câu hỏi sau khi Time Extractor xử lý: nội dung cần tìm, mốc T_req tuyệt đối, bộ lọc."""

    semantic_query: str = Field(description="Nội dung cần tìm, đã bỏ phần thời gian")
    t_req: datetime = Field(description="Mốc thời gian tuyệt đối (đã quy đổi từ thời gian tương đối bằng T_now)")
    filters: dict[str, Any] = Field(default_factory=dict, description='Metadata_Filters, VD {"country": "VN"}')
    mechanism: Mechanism = "temporal"

    @field_validator("t_req")
    @classmethod
    def _utc(cls, value: datetime) -> datetime:
        """Quy t_req về UTC (không có múi giờ thì coi là UTC)."""
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
