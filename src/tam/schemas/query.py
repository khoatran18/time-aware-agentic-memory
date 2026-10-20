"""ProfiledQuery: đầu ra của Time Extractor, đầu vào của mọi Retriever."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

Mechanism = Literal["temporal", "timeline", "conflict"]


class ProfiledQuery(BaseModel):
    """Câu hỏi sau khi Time Extractor xử lý: nội dung cần tìm, mốc T_req tuyệt đối, bộ lọc."""

    semantic_query: str = Field(description="Nội dung cần tìm, đã bỏ phần thời gian")
    t_req: datetime = Field(description="Mốc thời gian tuyệt đối (đã quy đổi từ thời gian tương đối bằng T_now); với khoảng là điểm đầu `qs`")
    t_end: datetime | None = Field(
        default=None,
        description="Điểm cuối `qe` của khoảng hỏi (decisions/07 đề xuất 1); None = câu hỏi một điểm (bằng t_req). Retriever hiện chưa dùng.",
    )
    filters: dict[str, Any] = Field(default_factory=dict, description='Metadata_Filters, VD {"country": "VN"}')
    domains: list[str] = Field(
        default_factory=list, description="Domain gợi ý để cộng điểm (không lọc): chunk có nhãn trùng được W3·Domain_Match"
    )
    mechanism: Mechanism = "temporal"

    @field_validator("t_req", "t_end")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        """Quy t_req và t_end về UTC (không có múi giờ thì coi là UTC)."""
        if value is None:
            return None
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
