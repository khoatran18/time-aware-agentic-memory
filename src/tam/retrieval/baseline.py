"""Baseline plain RAG để so với Cơ chế 1: không lọc thời gian, không điểm thời gian, không loại tin giả.

Ba phương pháp, lên thang từ đơn giản đến gần Cơ chế 1 (docs/eval/03, đợt 1):
- `dense`: chỉ nhánh dense (RAG phổ biến nhất).
- `bm25`: chỉ nhánh BM25.
- `hybrid`: dense + BM25 gộp RRF, vẫn không lọc và không điểm thời gian.
Cơ chế 1 với `--no-temporal` (thêm lọc `start_time <= t_req`) và Cơ chế 1 đầy đủ là hai bậc tiếp theo, chạy bằng `TemporalRetriever`.
"""
from __future__ import annotations

from tam.retrieval.base import Retriever
from tam.retrieval.temporal.expansion import neighbor_ids
from tam.retrieval.temporal.fusion import fuse
from tam.retrieval.temporal.rerank import RERANK_MODES, Reranker, minmax, mix_scores
from tam.schemas.query import ProfiledQuery
from tam.schemas.result import RetrievalResult, RetrievalTrace, ScoredChunk
from tam.stores.vector.base import BranchHits, VectorFilter, VectorStore

METHODS = ("dense", "bm25", "hybrid")


class PlainRetriever(Retriever):
    """Plain RAG: `t_req` bị bỏ qua; chunk tương lai và chunk bị vô hiệu vẫn có thể trả về (đo bằng `leakage_rate`)."""

    mechanism = "temporal"

    def __init__(self, store: VectorStore, *, method: str = "hybrid", top_n: int = 50, top_k: int = 5, rrf_k: int = 60,
                 neighbor_window: int = 0, reranker: Reranker | None = None, rerank_top: int = 20, rerank_mode: str = "replace",
                 rerank_alpha: float = 0.5) -> None:
        """`method` thuộc `METHODS`. `neighbor_window`: chunk liền kề mỗi phía của Top-K làm ngữ cảnh (0 = tắt); Plain RAG không lọc gì nên lấy cả chunk tương lai.
        `reranker` (tùy chọn, đối chứng công bằng cho đề xuất 4): chấm lại `rerank_top` chunk đầu bằng cross-encoder (`replace` hoặc `mix`), vẫn không lọc thời gian."""
        if method not in METHODS:
            raise ValueError(f"method không hợp lệ: {method!r}; cho phép {METHODS}")
        if top_k < 1 or top_n < top_k:
            raise ValueError(f"Cần 1 <= top_k <= top_n, nhận top_k={top_k}, top_n={top_n}")
        if neighbor_window < 0:
            raise ValueError(f"neighbor_window phải >= 0, nhận {neighbor_window}")
        self._window = neighbor_window
        if rerank_mode not in RERANK_MODES or rerank_top < 1:
            raise ValueError(f"rerank_mode {RERANK_MODES}, rerank_top >= 1; nhận {rerank_mode!r}, {rerank_top}")
        self._reranker, self._rerank_top, self._rerank_mode, self._rerank_alpha = reranker, rerank_top, rerank_mode, rerank_alpha
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
        if self._reranker is not None and ranked:
            ranked = self._rerank(query.semantic_query, ranked)
        ids = [s.chunk.chunk_id for s in ranked]
        trace = RetrievalTrace(
            dense_ids=[h.chunk.chunk_id for h in hits.dense], sparse_ids=[h.chunk.chunk_id for h in hits.sparse],
            fused_ids=ids, ranked_ids=ids,
        )
        top = ranked[: self._top_k]
        neighbors = self._store.get_chunks(neighbor_ids([s.chunk.chunk_id for s in top], self._window)) if self._window and top else []
        return RetrievalResult(mechanism=self.mechanism, chunks=top, neighbors=neighbors, trace=trace)

    def _rerank(self, text: str, ranked: list[ScoredChunk]) -> list[ScoredChunk]:
        """Cross-encoder chấm lại nhóm đầu; phần còn lại giữ thứ tự cũ phía sau."""
        head = ranked[: self._rerank_top]
        ce = self._reranker.score(text, [s.chunk.text for s in head])
        sem = mix_scores(minmax([s.semantic_score for s in head]), ce, self._rerank_mode, self._rerank_alpha)
        redone = sorted((s.model_copy(update={"semantic_score": v, "final_score": v}) for s, v in zip(head, sem, strict=True)),
                        key=lambda s: (-s.final_score, s.chunk.chunk_id))
        return redone + ranked[self._rerank_top:]
