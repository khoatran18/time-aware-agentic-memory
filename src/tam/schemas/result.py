"""Kết quả truy xuất, dùng chung cho cả 3 cơ chế."""
from __future__ import annotations

from pydantic import BaseModel, Field

from tam.schemas.chunk import Chunk
from tam.schemas.query import Mechanism


class ScoredChunk(BaseModel):
    """Một chunk cùng ba điểm: semantic, temporal và final."""

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
    domain_score: float = Field(default=0.0, description="1.0 nếu nhãn domain của chunk trùng domain của câu hỏi, ngược lại 0.0")
    final_score: float = Field(
        default=0.0,
        description="Điểm xếp hạng cuối = W1·semantic_score + W2·temporal_score + W3·domain_score; dùng để lấy Top-K",
    )


class RetrievalTrace(BaseModel):
    """Vết từng bước của một lần truy xuất, để đo mỗi bước (docs/eval/03): ứng viên từng nhánh, trước và sau điểm thời gian."""

    dense_ids: list[str] = Field(default_factory=list, description="Nhánh dense sau hard filter, theo hạng")
    sparse_ids: list[str] = Field(default_factory=list, description="Nhánh BM25 sau hard filter, theo hạng")
    fused_ids: list[str] = Field(default_factory=list, description="Sau RRF, TRƯỚC điểm thời gian, theo hạng (Top-N)")
    ranked_ids: list[str] = Field(default_factory=list, description="Sau điểm thời gian: toàn bộ Top-N theo hạng cuối")


class RetrievalResult(BaseModel):
    """Kết quả của một Retriever: các chunk đã xếp hạng, kèm cơ chế đã dùng."""

    mechanism: Mechanism
    chunks: list[ScoredChunk] = Field(default_factory=list)
    trace: RetrievalTrace | None = Field(default=None, description="Vết từng bước; chỉ để đánh giá")
    neighbors: list[Chunk] = Field(
        default_factory=list,
        description="Chunk liền kề (cùng tài liệu) của Top-K, đã qua hard filter; chỉ làm ngữ cảnh khi sinh câu trả lời, không xếp hạng",
    )
