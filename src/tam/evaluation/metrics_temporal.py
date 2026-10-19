"""Metric đánh giá retrieval Cơ chế 1 (Temporal) theo `chunk_id`, không gọi LLM (kế hoạch: process/03 mục 5, việc 3).

Đo riêng chất lượng truy xuất của Cơ chế 1: Hit@k, MRR và hai tỉ lệ vi phạm bất biến (rò rỉ tương lai, lấy tin giả),
kỳ vọng đều bằng 0%. Cơ chế 2/3 có file riêng: metrics_timeline.py, metrics_conflict.py (chưa làm).
"""
from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from tam.config.logging import get_logger
from tam.evaluation.funnel import gold_filter_status, stage_ranks, summarize_stages
from tam.retrieval.base import Retriever
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.stores.vector.base import VectorFilter, VectorStore

logger = get_logger(__name__)


@dataclass(frozen=True)
class EvalCase:
    """Một câu hỏi eval retrieval với nhãn ở mức chunk."""

    id: str
    query: str
    t_req: datetime | str
    gold_ids: frozenset[str] = frozenset()      # chunk đúng; rỗng = không có đáp án hợp lệ tại t_req
    forbidden_ids: frozenset[str] = frozenset() # chunk tuyệt đối không được xuất hiện (tương lai, tin giả, sai facet)
    filters: dict[str, Any] = field(default_factory=dict)
    domains: tuple[str, ...] = ()               # domain gợi ý để cộng điểm (W3), không lọc


def cases_from_corpus(data: dict) -> list[EvalCase]:
    """Đổi `cases` của tests/fixtures/temporal_corpus.json thành EvalCase."""
    return [
        EvalCase(
            id=c["id"], query=c["query"], t_req=c["t_req"],
            gold_ids=frozenset([c["expect_top"]]) if c.get("expect_top") else frozenset(),
            forbidden_ids=frozenset(c.get("expect_absent", [])),
            filters=c.get("filters", {}),
        )
        for c in data["cases"]
    ]


def hit_at_k(ranked_ids: Sequence[str], gold_ids: Collection[str], k: int) -> float:
    """1.0 nếu có chunk đúng trong top-k, ngược lại 0.0."""
    return float(any(i in gold_ids for i in ranked_ids[:k]))


def reciprocal_rank(ranked_ids: Sequence[str], gold_ids: Collection[str]) -> float:
    """1/hạng của chunk đúng đầu tiên; 0.0 nếu không có."""
    for rank, i in enumerate(ranked_ids, start=1):
        if i in gold_ids:
            return 1.0 / rank
    return 0.0


def recall_at_k(ranked_ids: Sequence[str], gold_ids: Collection[str], k: int) -> float:
    """Tỉ lệ chunk đúng nằm trong top-k (câu cần 2 chunk mà tìm được 1 thì 0.5)."""
    return len(set(ranked_ids[:k]) & set(gold_ids)) / len(gold_ids) if gold_ids else 0.0


def all_hit_at_k(ranked_ids: Sequence[str], gold_ids: Collection[str], k: int) -> float:
    """1.0 nếu MỌI chunk đúng nằm trong top-k (khác Hit@k chỉ cần một); dùng cho câu cần nhiều chunk."""
    return float(bool(gold_ids) and set(gold_ids) <= set(ranked_ids[:k]))


def is_future_leak(chunk: Chunk, t_req: datetime) -> bool:
    """Chunk bắt đầu sau T_req: vi phạm 'không rò rỉ tương lai'."""
    return chunk.start_time is not None and chunk.start_time > t_req


def is_invalidated(chunk: Chunk) -> bool:
    """Chunk đã bị đánh dấu sai từ gốc (Falsehood): Cơ chế 1 phải lọc hẳn."""
    return chunk.invalidated_at is not None


def evaluate_retrieval(
    retriever: Retriever, cases: Sequence[EvalCase], ks: Sequence[int] = (1, 3, 5), store: VectorStore | None = None
) -> dict[str, Any]:
    """Chạy retriever trên các case (bỏ qua profiler: chế độ oracle t_req) và gộp metric.

    Hit@k và MRR chỉ tính trên case có đáp án (gold_ids không rỗng). `leakage_rate`, `invalidated_rate`,
    `forbidden_rate` tính trên mọi case: tỉ lệ câu hỏi có ít nhất một chunk vi phạm trong kết quả.
    `store` (tùy chọn): nếu có thì thêm `gold_pass_filter` (chunk đúng có qua hard filter không) để đếm câu bị lọc cứng chặn.
    Trả về {"summary": {...}, "cases": [chi tiết từng câu]} để ghi thẳng ra metrics.json / predictions.jsonl.
    """
    rows = []
    for case in cases:
        query = ProfiledQuery(semantic_query=case.query, t_req=case.t_req, filters=case.filters, domains=list(case.domains))
        result = retriever.retrieve(query)
        ids = [s.chunk.chunk_id for s in result.chunks]
        rows.append({
            "id": case.id,
            "ranked_ids": ids,
            "has_gold": bool(case.gold_ids),
            "n_gold": len(case.gold_ids),
            "neighbor_ids": [c.chunk_id for c in result.neighbors],
            "hit": {k: hit_at_k(ids, case.gold_ids, k) for k in ks},
            "recall": {k: recall_at_k(ids, case.gold_ids, k) for k in ks},
            "all_hit": {k: all_hit_at_k(ids, case.gold_ids, k) for k in ks},
            "ctx_hit": hit_at_k(ids + [c.chunk_id for c in result.neighbors], case.gold_ids, len(ids) + len(result.neighbors)),
            "ctx_recall": recall_at_k(ids + [c.chunk_id for c in result.neighbors], case.gold_ids, len(ids) + len(result.neighbors)),
            "ctx_all_hit": all_hit_at_k(ids + [c.chunk_id for c in result.neighbors], case.gold_ids, len(ids) + len(result.neighbors)),
            "ctx_size": len(ids) + len(result.neighbors),
            "rr": reciprocal_rank(ids, case.gold_ids),
            "future_leak": any(is_future_leak(s.chunk, query.t_req) for s in result.chunks),
            "invalidated": any(is_invalidated(s.chunk) for s in result.chunks),
            "forbidden": any(i in case.forbidden_ids for i in ids),
            "undated_in_results": any(s.chunk.start_time is None for s in result.chunks),
            "stages": stage_ranks(result.trace, case.gold_ids) if result.trace else None,
            "gold_pass_filter": (
                gold_filter_status(store, case.gold_ids, VectorFilter(t_req=query.t_req)) if store and case.gold_ids else None
            ),
        })

    answerable = [r for r in rows if r["has_gold"]]

    def mean(values: list[float]) -> float | None:
        return sum(values) / len(values) if values else None

    multi = [r for r in answerable if r["n_gold"] >= 2]
    summary: dict[str, Any] = {
        "n_cases": len(rows),
        "n_answerable": len(answerable),
        **{f"hit@{k}": mean([r["hit"][k] for r in answerable]) for k in ks},
        "mrr": mean([r["rr"] for r in answerable]),
        **{f"recall@{k}": mean([r["recall"][k] for r in answerable]) for k in ks},
        # câu cần từ 2 chunk trở lên: Hit@k (một chunk) dễ đánh giá quá cao, nên đo thêm all_hit (đủ chunk) và recall
        "n_multi_gold": len(multi),
        **{f"multi_all_hit@{k}": mean([r["all_hit"][k] for r in multi]) for k in ks},
        **{f"multi_recall@{k}": mean([r["recall"][k] for r in multi]) for k in ks},
        # ngữ cảnh = Top-K + chunk liền kề (khi neighbor_window > 0); bằng Top-K nếu không mở rộng
        "ctx_hit": mean([r["ctx_hit"] for r in answerable]),
        "ctx_recall": mean([r["ctx_recall"] for r in answerable]),
        "ctx_multi_all_hit": mean([r["ctx_all_hit"] for r in multi]),
        "ctx_size_mean": mean([float(r["ctx_size"]) for r in rows]),
        "rescued_by_neighbors": sum(
            1 for r in answerable if r["ctx_hit"] and not any(r["hit"][k] for k in ks[-1:])
        ),
        "leakage_rate": mean([float(r["future_leak"]) for r in rows]),
        "invalidated_rate": mean([float(r["invalidated"]) for r in rows]),
        "forbidden_rate": mean([float(r["forbidden"]) for r in rows]),
        "undated_in_results_rate": mean([float(r["undated_in_results"]) for r in rows]),
        **summarize_stages(rows, ks),
    }
    logger.info("Eval retrieval: %s", summary)
    return {"summary": summary, "cases": rows}
