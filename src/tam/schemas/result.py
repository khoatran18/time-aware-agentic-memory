"""Kết quả truy xuất, dùng chung cho cả 3 cơ chế."""
from __future__ import annotations

from pydantic import BaseModel, Field

from tam.schemas.chunk import Chunk
from tam.schemas.query import Mechanism


class ScoredChunk(BaseModel):
    chunk: Chunk = Field(description="Chunk gốc được chấm điểm")
    semantic_score: float = Field(
        default=0.0,
        description="Độ liên quan về nội dung: RRF của nhánh dense + BM25, min-max về [0,1] trên Top-N",
    )
    temporal_score: float = Field(
        default=0.0,
        description="Độ khớp về thời gian với T_req: 1.0 nếu T_req nằm trong [start_time, end_time] (TH1), "
        "ngược lại exp(-λ·Δyears) (TH2)",
    )
    final_score: float = Field(
        default=0.0,
        description="Điểm xếp hạng cuối = W1·semantic_score + W2·temporal_score; dùng để lấy Top-K",
    )


class RetrievalResult(BaseModel):
    mechanism: Mechanism
    chunks: list[ScoredChunk] = Field(default_factory=list)
