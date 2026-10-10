"""Chunk: đơn vị lưu trong kho time-aware (xem docs/design/02, mục 2)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def _to_utc(value: datetime) -> datetime:
    """datetime không có múi giờ coi là UTC; có múi giờ thì quy về UTC."""
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class Chunk(BaseModel):
    """Một đoạn văn bản kèm mốc thời gian hiệu lực; đơn vị lưu trong VectorDB."""

    chunk_id: str = Field(description="Mã duy nhất; cũng là con trỏ Boomerang từ GraphDB về sau")
    text: str = Field(description="Nội dung chunk (đơn vị cấu trúc, vd một điều luật); được embed dense + BM25")
    source: str = Field(description="Nơi phát hành (vd Wikipedia, tên báo); trích dẫn khi sinh đáp án, khóa tra độ tin cậy ở CC3")
    doc_id: str | None = Field(default=None, description="Tài liệu cụ thể trong source (vd /wiki/Knox_Cunningham, URL bài báo); không index")
    start_time: datetime = Field(description="Thời điểm thông tin bắt đầu đúng; mốc chỉ-năm chuẩn hóa YYYY-01-01")
    end_time: datetime | None = Field(default=None, description="None = còn hiệu lực")
    invalidated_at: datetime | None = Field(default=None, description="Khác None = sai từ gốc (Falsehood), CC1 loại hẳn")
    domain_features: dict[str, Any] = Field(default_factory=dict, description='VD {"domain": "Luật", "country": "VN"}')

    @field_validator("start_time", "end_time", "invalidated_at")
    @classmethod
    def _utc(cls, value: datetime | None) -> datetime | None:
        """Quy datetime về UTC (không có múi giờ thì coi là UTC)."""
        return None if value is None else _to_utc(value)

    @model_validator(mode="after")
    def _check_range(self) -> Chunk:
        """end_time không được nhỏ hơn start_time."""
        if self.end_time is not None and self.end_time < self.start_time:
            raise ValueError(f"end_time {self.end_time} nhỏ hơn start_time {self.start_time} (chunk {self.chunk_id})")
        return self
