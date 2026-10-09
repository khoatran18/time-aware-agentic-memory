"""Kết quả truy xuất, dùng chung cho cả 3 cơ chế."""
from __future__ import annotations

from pydantic import BaseModel, Field

from tam.schemas.chunk import Chunk
from tam.schemas.query import Mechanism


class ScoredChunk(BaseModel):
    chunk: Chunk
    semantic_score: float = 0.0
    temporal_score: float = 0.0
    final_score: float = 0.0


class RetrievalResult(BaseModel):
    mechanism: Mechanism
    chunks: list[ScoredChunk] = Field(default_factory=list)
