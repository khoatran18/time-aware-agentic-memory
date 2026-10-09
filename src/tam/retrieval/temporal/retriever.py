"""TemporalRetriever: hybrid search + hard filter -> RRF -> Temporal_Score -> re-rank Top-K (Cơ chế 1)."""
from __future__ import annotations

from tam.config.loader import Config
from tam.config.logging import get_logger
from tam.retrieval.base import Retriever
from tam.retrieval.temporal.filters import passes_hard_filter, to_vector_filter
from tam.retrieval.temporal.fusion import fuse
from tam.retrieval.temporal.scoring import final_score, is_exact_match, temporal_score
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.schemas.result import RetrievalResult, ScoredChunk
from tam.stores.vector.base import BranchHits, VectorFilter, VectorStore

logger = get_logger(__name__)


class TemporalRetriever(Retriever):
    """Truy xuất point-in-time: chỉ cần VectorStore, không dùng LLM hay đồ thị."""

    mechanism = "temporal"

    def __init__(
        self,
        store: VectorStore,
        *,
        w1: float = 0.7,
        w2: float = 0.3,
        decay_lambda: float = 0.5,
        rrf_k: int = 60,
        top_n: int = 50,
        top_k: int = 5,
    ) -> None:
        """`top_n`: số ứng viên mỗi nhánh lấy từ store; `top_k`: số chunk trả về sau re-rank."""
        if top_k < 1 or top_n < top_k:
            raise ValueError(f"Cần 1 <= top_k <= top_n, nhận top_k={top_k}, top_n={top_n}")
        self._store = store
        self._w1, self._w2, self._lambda = w1, w2, decay_lambda
        self._rrf_k, self._top_n, self._top_k = rrf_k, top_n, top_k

    @classmethod
    def from_config(cls, cfg: Config, store: VectorStore) -> TemporalRetriever:
        """Tạo từ khối `retrieval` trong config."""
        r = cfg.retrieval
        return cls(
            store,
            w1=r.w1,
            w2=r.w2,
            decay_lambda=r.decay_lambda,
            rrf_k=r.rrf_k,
            top_n=r.top_n,
            top_k=r.top_k,
        )

    def retrieve(self, query: ProfiledQuery) -> RetrievalResult:
        """Trả Top-K chunk theo `Final = W1·Semantic + W2·Temporal`, đã loại tin giả và thông tin tương lai."""
        flt = to_vector_filter(query)
        raw = self._store.search(query.semantic_query, flt, self._top_n)
        hits = _guard(raw, flt)  # chốt chặn: store lỗi cũng không để lọt tương lai/tin giả vào tính điểm
        fused = fuse(hits, self._rrf_k, self._top_n)

        scored = [self._score(chunk, sem, query) for chunk, sem in fused]
        # Hòa điểm: ưu tiên chunk đúng thời điểm hơn, rồi chunk_id để kết quả tái lập được
        scored.sort(key=lambda s: (-s.final_score, -s.temporal_score, s.chunk.chunk_id))
        top = scored[: self._top_k]

        th1 = sum(is_exact_match(s.chunk, query.t_req) for s in scored)
        logger.info(
            "temporal t_req=%s: dense=%d sparse=%d -> %d ứng viên (TH1=%d, TH2=%d) -> top %d",
            query.t_req.date(), len(hits.dense), len(hits.sparse), len(scored), th1, len(scored) - th1, len(top),
        )
        for s in top:
            logger.debug(
                "  %s sem=%.3f temp=%.3f final=%.3f", s.chunk.chunk_id, s.semantic_score, s.temporal_score, s.final_score
            )
        return RetrievalResult(mechanism=self.mechanism, chunks=top)

    def _score(self, chunk: Chunk, semantic: float, query: ProfiledQuery) -> ScoredChunk:
        """Chấm Temporal_Score và Final_Score cho một chunk đã có Semantic_Score."""
        temporal = temporal_score(chunk, query.t_req, self._lambda)
        return ScoredChunk(
            chunk=chunk,
            semantic_score=semantic,
            temporal_score=temporal,
            final_score=final_score(semantic, temporal, self._w1, self._w2),
        )


def _guard(hits: BranchHits, flt: VectorFilter) -> BranchHits:
    """Bỏ mọi hit vi phạm hard filter; có hit bị bỏ nghĩa là store không áp filter đúng nên ghi cảnh báo."""
    dense = [h for h in hits.dense if passes_hard_filter(h.chunk, flt)]
    sparse = [h for h in hits.sparse if passes_hard_filter(h.chunk, flt)]
    dropped = len(hits.dense) + len(hits.sparse) - len(dense) - len(sparse)
    if dropped:
        logger.warning("Store trả %d hit vi phạm hard filter (t_req=%s); đã loại", dropped, flt.t_req)
    return BranchHits(dense=dense, sparse=sparse)
