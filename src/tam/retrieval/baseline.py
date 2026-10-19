"""Baseline plain RAG để so với Cơ chế 1: không lọc thời gian, không điểm thời gian, không loại tin giả.

Ba phương pháp, lên thang từ đơn giản đến gần Cơ chế 1 (docs/eval/03, đợt 1):
- `dense`: chỉ nhánh dense (RAG phổ biến nhất).
- `bm25`: chỉ nhánh BM25.
- `hybrid`: dense + BM25 gộp RRF, vẫn không lọc và không điểm thời gian.
Cơ chế 1 với `--no-temporal` (thêm lọc `start_time <= t_req`) và Cơ chế 1 đầy đủ là hai bậc tiếp theo, chạy bằng `TemporalRetriever`.
"""
from __future__ import annotations

from tam.retrieval.base import Retriever
from tam.retrieval.temporal.fusion import fuse
from tam.schemas.query import ProfiledQuery
from tam.schemas.result import RetrievalResult, RetrievalTrace, ScoredChunk
from tam.stores.vector.base import BranchHits, VectorFilter, VectorStore

METHODS = ("dense", "bm25", "hybrid")


class PlainRetriever(Retriever):
    """Plain RAG: `t_req` bị bỏ qua; chunk tương lai và chunk bị vô hiệu vẫn có thể trả về (đo bằng `leakage_rate`)."""

    mechanism = "temporal"

    def __init__(self, store: VectorStore, *, method: str = "hybrid", top_n: int = 50, top_k: int = 5, rrf_k: int = 60) -> None:
        """`method` thuộc `METHODS`."""
        if method not in METHODS:
            raise ValueError(f"method không hợp lệ: {method!r}; cho phép {METHODS}")
        if top_k < 1 or top_n < top_k:
            raise ValueError(f"Cần 1 <= top_k <= top_n, nhận top_k={top_k}, top_n={top_n}")
        self._store, self._method, self._top_n, self._top_k, self._rrf_k = store, method, top_n, top_k, rrf_k

    def retrieve(self, query: ProfiledQuery) -> RetrievalResult:
        """Top-K theo độ liên quan nội dung, không dùng thời gian."""
        flt = VectorFilter(t_req=query.t_req, exclude_invalidated=False, apply_time=False)
        hits = self._store.search(query.semantic_query, flt, self._top_n)
        if self._method == "dense":
            pairs = [(h.chunk, h.score) for h in hits.dense]
        elif self._method == "bm25":
            pairs = [(h.chunk, h.score) for h in hits.sparse]
        else:
            pairs = fuse(BranchHits(dense=hits.dense, sparse=hits.sparse), self._rrf_k, self._top_n)
        ranked = [ScoredChunk(chunk=c, semantic_score=s, final_score=s) for c, s in pairs[: self._top_n]]
        ids = [s.chunk.chunk_id for s in ranked]
        trace = RetrievalTrace(
            dense_ids=[h.chunk.chunk_id for h in hits.dense], sparse_ids=[h.chunk.chunk_id for h in hits.sparse],
            fused_ids=ids, ranked_ids=ids,
        )
        return RetrievalResult(mechanism=self.mechanism, chunks=ranked[: self._top_k], trace=trace)
