"""TemporalRetriever: hybrid search + hard filter -> RRF -> Temporal_Score -> re-rank Top-K (Cơ chế 1)."""
from __future__ import annotations

from dataclasses import replace

from tam.config.loader import Config
from tam.config.logging import get_logger
from tam.retrieval.base import Retriever
from tam.retrieval.temporal.expansion import neighbor_ids
from tam.retrieval.temporal.filters import passes_hard_filter, to_vector_filter
from tam.retrieval.temporal.fusion import fuse
from tam.retrieval.temporal.scoring import DecayFrom, EndMode, domain_score, final_score, is_exact_match, temporal_score
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.schemas.result import RetrievalResult, RetrievalTrace, ScoredChunk
from tam.stores.vector.base import BranchHits, VectorFilter, VectorStore, merge_branches

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
        w3: float = 0.0,
        end_mode: EndMode = "stored",
        open_decay: float = 0.1,
        neighbor_window: int = 0,
        t_unknown: float | None = None,
        sparse_weight: float = 1.0,
        decay_from: DecayFrom = "start",
    ) -> None:
        """`top_n`: số ứng viên mỗi nhánh lấy từ store; `top_k`: số chunk trả về sau re-rank.

        `w3`: trọng số Domain_Match (0 = tắt). `end_mode`/`open_decay`: cách chấm chunk `ongoing`/`unknown` (scoring.py).
        `t_unknown`: nếu đặt (vd 0.5) thì thêm nhánh chunk không mốc với điểm thời gian cố định này (decisions/04); None = tắt.
        `sparse_weight`: trọng số nhánh BM25 trong RRF (dense luôn 1); 1 = RRF thường, 0 = chỉ dense (bỏ BM25).
        `decay_from`: mốc tính khoảng cách của TH2 (chunk đã hết hạn): `start` (mặc định, như design 02) hoặc `end` (decisions/07).
        `neighbor_window`: số chunk liền kề mỗi phía của Top-K đưa vào `RetrievalResult.neighbors` (0 = tắt).
        """
        if top_k < 1 or top_n < top_k:
            raise ValueError(f"Cần 1 <= top_k <= top_n, nhận top_k={top_k}, top_n={top_n}")
        self._store = store
        self._w1, self._w2, self._lambda = w1, w2, decay_lambda
        self._rrf_k, self._top_n, self._top_k = rrf_k, top_n, top_k
        if neighbor_window < 0:
            raise ValueError(f"neighbor_window phải >= 0, nhận {neighbor_window}")
        if sparse_weight < 0:
            raise ValueError(f"sparse_weight phải >= 0, nhận {sparse_weight}")
        self._t_unknown, self._sparse_weight = t_unknown, sparse_weight
        self._w3, self._end_mode, self._open_decay, self._window = w3, end_mode, open_decay, neighbor_window
        self._decay_from = decay_from

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
            w3=r.get("w3", 0.0),
            end_mode=r.get("end_mode", "stored"),
            open_decay=r.get("open_decay", 0.1),
            neighbor_window=r.get("neighbor_window", 0),
            t_unknown=r.get("t_unknown", None),
            sparse_weight=r.get("sparse_weight", 1.0),
            decay_from=r.get("decay_from", "start"),
        )

    def retrieve(self, query: ProfiledQuery) -> RetrievalResult:
        """Trả Top-K chunk theo `Final = W1·Semantic + W2·Temporal`, đã loại tin giả và thông tin tương lai."""
        flt = to_vector_filter(query)
        hits = _guard(self._store.search(query.semantic_query, flt, self._top_n), flt)  # chốt chặn: store lỗi cũng không để lọt tương lai/tin giả
        if self._t_unknown is not None:  # nhánh chunk không mốc, gộp vào cùng danh sách ứng viên của từng nhánh
            und_flt = replace(flt, undated=True)
            und = _guard(self._store.search(query.semantic_query, und_flt, self._top_n), und_flt)
            hits = merge_branches(hits, und, self._top_n)
        fused = fuse(hits, self._rrf_k, self._top_n, self._sparse_weight)

        scored = [self._score(chunk, sem, query) for chunk, sem in fused]
        # Hòa điểm: ưu tiên chunk đúng thời điểm hơn, rồi chunk_id để kết quả tái lập được
        scored.sort(key=lambda s: (-s.final_score, -s.temporal_score, s.chunk.chunk_id))
        top = scored[: self._top_k]
        trace = RetrievalTrace(
            dense_ids=[h.chunk.chunk_id for h in hits.dense], sparse_ids=[h.chunk.chunk_id for h in hits.sparse],
            fused_ids=[c.chunk_id for c, _ in fused], ranked_ids=[s.chunk.chunk_id for s in scored],
        )

        th1 = sum(is_exact_match(s.chunk, query.t_req) for s in scored)  # chunk không mốc tính vào TH2
        logger.info(
            "temporal t_req=%s: dense=%d sparse=%d -> %d ứng viên (TH1=%d, TH2=%d) -> top %d",
            query.t_req.date(), len(hits.dense), len(hits.sparse), len(scored), th1, len(scored) - th1, len(top),
        )
        for s in top:
            logger.debug(
                "  %s sem=%.3f temp=%.3f final=%.3f", s.chunk.chunk_id, s.semantic_score, s.temporal_score, s.final_score
            )
        return RetrievalResult(mechanism=self.mechanism, chunks=top, neighbors=self._neighbors(top, query), trace=trace)

    def _neighbors(self, top: list[ScoredChunk], query: ProfiledQuery) -> list[Chunk]:
        """Chunk liền kề của Top-K, vẫn qua hard filter (không tương lai, không tin giả) nhưng không lọc facet domain."""
        if self._window == 0 or not top:
            return []
        ids = neighbor_ids([s.chunk.chunk_id for s in top], self._window)
        flt = VectorFilter(t_req=query.t_req)
        return [c for c in self._store.get_chunks(ids) if passes_hard_filter(c, flt)]

    def _score(self, chunk: Chunk, semantic: float, query: ProfiledQuery) -> ScoredChunk:
        """Chấm Temporal_Score và Final_Score cho một chunk đã có Semantic_Score."""
        temporal = temporal_score(chunk, query.t_req, self._lambda, end_mode=self._end_mode, open_decay=self._open_decay,
                                  t_unknown=self._t_unknown, decay_from=self._decay_from)
        domain = domain_score(chunk, query.domains) if self._w3 else 0.0
        return ScoredChunk(
            chunk=chunk,
            semantic_score=semantic,
            temporal_score=temporal,
            domain_score=domain,
            final_score=final_score(semantic, temporal, self._w1, self._w2, domain, self._w3),
        )


def _guard(hits: BranchHits, flt: VectorFilter) -> BranchHits:
    """Bỏ mọi hit vi phạm hard filter; có hit bị bỏ nghĩa là store không áp filter đúng nên ghi cảnh báo."""
    dense = [h for h in hits.dense if passes_hard_filter(h.chunk, flt)]
    sparse = [h for h in hits.sparse if passes_hard_filter(h.chunk, flt)]
    dropped = len(hits.dense) + len(hits.sparse) - len(dense) - len(sparse)
    if dropped:
        logger.warning("Store trả %d hit vi phạm hard filter (t_req=%s); đã loại", dropped, flt.t_req)
    return BranchHits(dense=dense, sparse=sparse)
