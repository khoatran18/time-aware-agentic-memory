"""Kiểu dữ liệu trung gian của ingestion: tài liệu thô -> chunk thô -> (thêm mốc thời gian) -> `tam.schemas.Chunk`."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Section:
    """Một đơn vị cấu trúc của tài liệu (đoạn/mục của bài, một điều luật)."""

    title: str
    text: str


@dataclass(frozen=True)
class RawDoc:
    """Tài liệu thô do loader trả về, chưa có mốc thời gian."""

    doc_id: str  # tài liệu cụ thể trong source (vd /wiki/Knox_Cunningham)
    title: str
    source: str  # nơi phát hành (vd Wikipedia, tên báo); do loader quyết định
    sections: tuple[Section, ...]
    domain_features: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RawChunk:
    """Một chunk theo cấu trúc, chưa có mốc thời gian."""

    chunk_id: str
    doc_id: str
    section_title: str
    text: str
    content_hash: str


@dataclass(frozen=True)
class TimeSpan:
    """Khoảng hiệu lực đã chuẩn hóa; `end = None` nghĩa là còn hiệu lực."""

    start: datetime
    end: datetime | None


@dataclass(frozen=True)
class TimeResult:
    """Kết quả trích mốc thời gian của một chunk: có `span`, hoặc `reason` giải thích vì sao không có."""

    span: TimeSpan | None
    reason: str | None = None  # "no_time" | "invalid_time"
