"""TemporalRetriever: hybrid search + hard filter -> RRF -> Temporal_Score -> re-rank Top-K (Cơ chế 1)."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from tam.config.loader import Config
from tam.config.logging import get_logger
from tam.retrieval.base import Retriever
from tam.retrieval.temporal.expansion import PAGE_EXPANDS, neighbor_ids, page_candidate_ids
from tam.retrieval.temporal.filters import passes_hard_filter, to_vector_filter
from tam.retrieval.temporal.fusion import fuse
from tam.retrieval.temporal.rerank import (
    RERANK_MODES,
    RERANK_POOLS,
    CrossEncoderReranker,
    Reranker,
    mix_scores,
    rerank_text,
)
from tam.retrieval.temporal.scoring import (
    OVERLAPS,
    TIME_MODES,
    DecayFrom,
    EndMode,
    Overlap,
    TimeMode,
    domain_score,
    final_score,
    is_exact_match,
    temporal_score,
    temporal_score_range,
)
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
        time_mode: TimeMode = "point",
        overlap: Overlap = "binary",
        page_expand: str = "none",
        page_top: int = 3,
        page_per: int = 2,
        reranker: Reranker | None = None,
        rerank_top: int = 20,
        rerank_mode: str = "replace",
        rerank_alpha: float = 0.5,
        rerank_pool: str = "final",
        rerank_time: bool = False,
        inferred_factor: float = 1.0,
    ) -> None:
        """`top_n`: số ứng viên mỗi nhánh lấy từ store; `top_k`: số chunk trả về sau re-rank.

        `w3`: trọng số Domain_Match (0 = tắt). `end_mode`/`open_decay`: cách chấm chunk `ongoing`/`unknown` (scoring.py).
        `t_unknown`: nếu đặt (vd 0.5) thì thêm nhánh chunk không mốc với điểm thời gian cố định này (decisions/04); None = tắt.
        `sparse_weight`: trọng số nhánh BM25 trong RRF (dense luôn 1); 1 = RRF thường, 0 = chỉ dense (bỏ BM25).
        `decay_from`: mốc tính khoảng cách của TH2 (chunk đã hết hạn): `start` (mặc định, như design 02) hoặc `end` (decisions/07).
        `time_mode`: `point` (mặc định) dùng một điểm `t_req`; `range` dùng khoảng `[t_req, t_end]` của ProfiledQuery (lọc `start <= t_end`, điểm
        chồng lấn; decisions/07 đề xuất 1). Thiếu `t_end` thì khoảng suy biến về một điểm. `overlap`: `binary` hoặc `coverage` (chỉ chế độ range).
        `neighbor_window`: số chunk liền kề mỗi phía của Top-K đưa vào `RetrievalResult.neighbors` (0 = tắt).
        `page_expand` (decisions/07 đề xuất 7; chỉ dùng khi `neighbor_window` = 0): `none` (tắt) | `time` (lấy `page_top` trang đầu của Top-K, mỗi trang
        thêm tối đa `page_per` chunk cùng trang còn hợp lệ tại `t_req` (point) hoặc giao `[t_req, t_end]` (range), gần chunk của Top-K nhất trước)
        | `page` (như `time` nhưng chỉ qua hard filter, không đòi hợp lệ theo thời gian: đối chứng).
        `reranker` (decisions/07 đề xuất 4; None = tắt): cross-encoder chấm lại `rerank_top` ứng viên đầu (chọn theo `rerank_pool`: `final` = hạng cuối
        hiện tại, `semantic` = hạng Semantic) rồi tính lại Final; `rerank_mode`: `replace` (Semantic mới = min-max điểm CE) | `mix`
        (`rerank_alpha·Semantic cũ + (1-rerank_alpha)·min-max CE`); `rerank_time`: ghép khoảng hiệu lực của chunk vào văn bản đưa cho CE.
        Ứng viên ngoài nhóm rerank giữ thứ tự cũ, xếp sau nhóm rerank.
        `inferred_factor` (đề xuất 11): hệ số (0, 1] nhân điểm thời gian của chunk có mốc suy từ chunk liền kề; 1.0 = như mốc thật.
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
        if time_mode not in TIME_MODES:
            raise ValueError(f"time_mode không hợp lệ: {time_mode!r}; cho phép {TIME_MODES}")
        if overlap not in OVERLAPS:
            raise ValueError(f"overlap không hợp lệ: {overlap!r}; cho phép {OVERLAPS}")
        self._time_mode, self._overlap = time_mode, overlap
        if page_expand not in PAGE_EXPANDS:
            raise ValueError(f"page_expand không hợp lệ: {page_expand!r}; cho phép {PAGE_EXPANDS}")
        if page_top < 1 or page_per < 1:
            raise ValueError(f"Cần page_top >= 1 và page_per >= 1, nhận {page_top}, {page_per}")
        self._page_expand, self._page_top, self._page_per = page_expand, page_top, page_per
        if rerank_mode not in RERANK_MODES or rerank_pool not in RERANK_POOLS:
            raise ValueError(f"rerank_mode {RERANK_MODES}, rerank_pool {RERANK_POOLS}; nhận {rerank_mode!r}, {rerank_pool!r}")
        if rerank_top < 1 or not 0 <= rerank_alpha <= 1:
            raise ValueError(f"Cần rerank_top >= 1 và 0 <= rerank_alpha <= 1, nhận {rerank_top}, {rerank_alpha}")
        if not 0 < inferred_factor <= 1:
            raise ValueError(f"inferred_factor phải thuộc (0, 1], nhận {inferred_factor}")
        self._reranker, self._rerank_top, self._rerank_mode, self._rerank_alpha = reranker, rerank_top, rerank_mode, rerank_alpha
        self._rerank_pool, self._rerank_time, self._inferred_factor = rerank_pool, rerank_time, inferred_factor

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
            time_mode=r.get("time_mode", "point"),
            overlap=r.get("overlap", "binary"),
            page_expand=r.get("page_expand", "none"),
            page_top=r.get("page_top", 3),
            page_per=r.get("page_per", 2),
            reranker=CrossEncoderReranker(r.get("rerank"), cache_dir=r.get("rerank_cache_dir"), score_cache=r.get("rerank_score_cache")) if r.get("rerank") else None,
            rerank_top=r.get("rerank_top", 20),
            rerank_mode=r.get("rerank_mode", "replace"),
            rerank_alpha=r.get("rerank_alpha", 0.5),
            rerank_pool=r.get("rerank_pool", "final"),
            rerank_time=r.get("rerank_time", False),
            inferred_factor=r.get("inferred_factor", 1.0),
        )

    def retrieve(self, query: ProfiledQuery) -> RetrievalResult:
        """Trả Top-K chunk theo `Final = W1·Semantic + W2·Temporal`, đã loại tin giả và thông tin tương lai."""
        flt = to_vector_filter(query, use_range=self._time_mode == "range")
        hits = _guard(self._store.search(query.semantic_query, flt, self._top_n), flt)  # chốt chặn: store lỗi cũng không để lọt tương lai/tin giả
        if self._t_unknown is not None:  # nhánh chunk không mốc, gộp vào cùng danh sách ứng viên của từng nhánh
            und_flt = replace(flt, undated=True)
            und = _guard(self._store.search(query.semantic_query, und_flt, self._top_n), und_flt)
            hits = merge_branches(hits, und, self._top_n)
        fused = fuse(hits, self._rrf_k, self._top_n, self._sparse_weight)

        scored = [self._score(chunk, sem, query) for chunk, sem in fused]
        # Hòa điểm: ưu tiên chunk đúng thời điểm hơn, rồi chunk_id để kết quả tái lập được
        scored.sort(key=_rank_key)
        if self._reranker is not None:
            scored = self._rerank(query, scored)
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

    def _rerank(self, query: ProfiledQuery, scored: list[ScoredChunk]) -> list[ScoredChunk]:
        """Cross-encoder chấm lại nhóm đầu của `scored` (đã xếp theo Final), tính lại Final, xếp lại nhóm đó; phần còn lại giữ nguyên phía sau."""
        pool = scored if self._rerank_pool == "final" else sorted(scored, key=lambda s: (-s.semantic_score, s.chunk.chunk_id))
        head, head_ids = pool[: self._rerank_top], {s.chunk.chunk_id for s in pool[: self._rerank_top]}
        ce = self._reranker.score(query.semantic_query, [rerank_text(s.chunk, with_time=self._rerank_time) for s in head])
        sem = mix_scores([s.semantic_score for s in head], ce, self._rerank_mode, self._rerank_alpha)
        redone = sorted(
            (s.model_copy(update={"semantic_score": v, "final_score": final_score(v, s.temporal_score, self._w1, self._w2, s.domain_score, self._w3)})
             for s, v in zip(head, sem, strict=True)), key=_rank_key)
        return redone + [s for s in scored if s.chunk.chunk_id not in head_ids]

    def _neighbors(self, top: list[ScoredChunk], query: ProfiledQuery) -> list[Chunk]:
        """Chunk liền kề của Top-K, vẫn qua hard filter (không tương lai, không tin giả) nhưng không lọc facet domain."""
        if not top:
            return []
        if self._window == 0:
            return self._page_neighbors(top, query) if self._page_expand != "none" else []
        ids = neighbor_ids([s.chunk.chunk_id for s in top], self._window)
        upper = query.t_end if self._time_mode == "range" and query.t_end is not None else query.t_req
        flt = VectorFilter(t_req=upper)
        return [c for c in self._store.get_chunks(ids) if passes_hard_filter(c, flt)]

    def _page_neighbors(self, top: list[ScoredChunk], query: ProfiledQuery) -> list[Chunk]:
        """Chunk cùng trang với Top-K (đề xuất 7): mỗi trang trong `page_top` trang đầu lấy tối đa `page_per` chunk, gần chunk của Top-K nhất trước."""
        upper = query.t_end if self._time_mode == "range" and query.t_end is not None else query.t_req
        flt = VectorFilter(t_req=upper)
        out: list[Chunk] = []
        for ids in page_candidate_ids([s.chunk.chunk_id for s in top], self._page_top).values():
            by_id = {c.chunk_id: c for c in self._store.get_chunks(ids)}
            ok = [c for cid in ids if (c := by_id.get(cid)) is not None and passes_hard_filter(c, flt)
                  and (self._page_expand == "page" or _covers(c, query.t_req))]
            out.extend(ok[: self._page_per])
        return out

    def _score(self, chunk: Chunk, semantic: float, query: ProfiledQuery) -> ScoredChunk:
        """Chấm Temporal_Score và Final_Score cho một chunk đã có Semantic_Score."""
        if self._time_mode == "range":
            temporal = temporal_score_range(chunk, query.t_req, query.t_end or query.t_req, self._lambda, end_mode=self._end_mode,
                                            open_decay=self._open_decay, t_unknown=self._t_unknown, decay_from=self._decay_from,
                                            overlap=self._overlap, inferred_factor=self._inferred_factor)
        else:
            temporal = temporal_score(chunk, query.t_req, self._lambda, end_mode=self._end_mode, open_decay=self._open_decay,
                                      t_unknown=self._t_unknown, decay_from=self._decay_from, inferred_factor=self._inferred_factor)
        domain = domain_score(chunk, query.domains) if self._w3 else 0.0
        return ScoredChunk(
            chunk=chunk,
            semantic_score=semantic,
            temporal_score=temporal,
            domain_score=domain,
            final_score=final_score(semantic, temporal, self._w1, self._w2, domain, self._w3),
        )


def _rank_key(s: ScoredChunk) -> tuple[float, float, str]:
    """Hòa điểm: ưu tiên chunk đúng thời điểm hơn, rồi chunk_id để kết quả tái lập được."""
    return (-s.final_score, -s.temporal_score, s.chunk.chunk_id)


def _covers(chunk: Chunk, t_req: datetime) -> bool:
    """Chunk có mốc và còn hiệu lực tại `t_req` (`end_time` rỗng là còn hiệu lực); cận trên `start_time` đã do hard filter kiểm (point: `t_req`, range: `qe`)."""
    return chunk.start_time is not None and (chunk.end_time is None or t_req <= chunk.end_time)


def _guard(hits: BranchHits, flt: VectorFilter) -> BranchHits:
    """Bỏ mọi hit vi phạm hard filter; có hit bị bỏ nghĩa là store không áp filter đúng nên ghi cảnh báo."""
    dense = [h for h in hits.dense if passes_hard_filter(h.chunk, flt)]
    sparse = [h for h in hits.sparse if passes_hard_filter(h.chunk, flt)]
    dropped = len(hits.dense) + len(hits.sparse) - len(dense) - len(sparse)
    if dropped:
        logger.warning("Store trả %d hit vi phạm hard filter (t_req=%s); đã loại", dropped, flt.t_req)
    return BranchHits(dense=dense, sparse=sparse)
