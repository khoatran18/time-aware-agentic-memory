"""Chỉ số từng bước của một lần truy xuất (docs/eval/03, đợt 2): ứng viên, lọc cứng, trước và sau điểm thời gian, Profiler.

Dùng `RetrievalTrace` do retriever trả. Mọi hàm là thuần (không gọi LLM); chỉ `gold_filter_status` và `profiler_stage` cần kho để tra chunk.
"""
from __future__ import annotations

from collections.abc import Collection, Sequence
from datetime import datetime
from typing import Any

from tam.retrieval.temporal.filters import passes_hard_filter
from tam.schemas.result import RetrievalTrace
from tam.stores.vector.base import VectorFilter, VectorStore


def best_rank(ids: Sequence[str], gold: Collection[str]) -> int | None:
    """Hạng (từ 1) của chunk đúng đứng đầu trong `ids`; None nếu không có."""
    for rank, i in enumerate(ids, start=1):
        if i in gold:
            return rank
    return None


def stage_ranks(trace: RetrievalTrace, gold: Collection[str]) -> dict[str, int | None]:
    """Hạng tốt nhất của chunk đúng ở từng bước: dense, sparse, fused (trước điểm thời gian), final (sau điểm thời gian)."""
    return {
        "dense": best_rank(trace.dense_ids, gold),
        "sparse": best_rank(trace.sparse_ids, gold),
        "fused": best_rank(trace.fused_ids, gold),
        "final": best_rank(trace.ranked_ids, gold),
    }


def gold_filter_status(store: VectorStore, gold: Collection[str], flt: VectorFilter) -> dict[str, bool]:
    """Chunk đúng nào qua được hard filter (`False` = bị lọc cứng, thường do `start_time > t_req` hoặc không mốc)."""
    chunks = {c.chunk_id: c for c in store.get_chunks(sorted(gold))}
    return {gid: gid in chunks and passes_hard_filter(chunks[gid], flt) for gid in gold}


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def summarize_stages(rows: Sequence[dict[str, Any]], ks: Sequence[int]) -> dict[str, Any]:
    """Gộp số liệu từng bước trên các dòng có `stages` (mỗi dòng: `stages` từ `stage_ranks`, `gold_pass_filter` nếu có).

    - `cand_recall_*`: tỉ lệ câu có chunk đúng trong danh sách ứng viên của nhánh (dense, sparse) hoặc sau RRF (fused).
    - `gold_blocked_by_filter`: câu mà mọi chunk đúng đều bị hard filter chặn (không thể trúng dù thuật toán tốt).
    - `hit@k_pre`/`mrr_pre`: xếp hạng ngay sau RRF (chưa có điểm thời gian); `mrr_post`: sau điểm thời gian.
    - `temporal_helped/hurt/same`: điểm thời gian đẩy chunk đúng lên, xuống hay giữ nguyên hạng (so fused với final).
    """
    rated = [r for r in rows if r.get("has_gold") and r.get("stages")]
    n = len(rated)

    def present(stage: str) -> float | None:
        return _mean([float(r["stages"][stage] is not None) for r in rated])

    def rr(stage: str) -> float | None:
        return _mean([1.0 / r["stages"][stage] if r["stages"][stage] else 0.0 for r in rated])

    helped = hurt = same = 0
    for r in rated:
        a, b = r["stages"]["fused"], r["stages"]["final"]
        if a is None or b is None:
            continue
        helped += b < a
        hurt += b > a
        same += b == a
    out: dict[str, Any] = {
        "stage_n": n,
        "cand_recall_dense": present("dense"),
        "cand_recall_sparse": present("sparse"),
        "cand_recall_fused": present("fused"),
        **{f"hit@{k}_pre": _mean([float((r["stages"]["fused"] or 10**9) <= k) for r in rated]) for k in ks},
        "mrr_pre": rr("fused"),
        "mrr_post": rr("final"),
        "temporal_helped": helped, "temporal_hurt": hurt, "temporal_same": same,
    }
    with_filter = [r for r in rated if r.get("gold_pass_filter") is not None]
    if with_filter:
        out["gold_blocked_by_filter"] = sum(not any(r["gold_pass_filter"].values()) for r in with_filter)
    return out


def profiler_stage(
    subset: dict[str, Any], profiled: dict[str, dict[str, Any]], store: VectorStore | None = None
) -> dict[str, Any]:
    """Chất lượng bước Profiler so với nhãn: sai lệch năm của `t_req`, `t_req` trong khoảng nhãn, domain điền và khớp chunk đáp án."""
    from tam.evaluation.ingestion_report import label_year  # tránh import vòng
    from tam.evaluation.retrieval_eval import oracle_t_req

    errs: list[float] = []
    in_range = given = domain_checked = domain_hit = usable = 0
    for c in subset["cases"]:
        row = profiled.get(c["idx"])
        if not row or row.get("error"):
            continue
        usable += 1
        t_req = datetime.fromisoformat(row["t_req"])
        errs.append(abs((t_req - oracle_t_req(c)).days) / 365.25)
        in_range += label_year(c["time_start"]) <= t_req.year <= label_year(c["time_end"])
        domain = (row.get("filters") or {}).get("domain")
        if not domain:
            continue
        given += 1
        if store is not None:
            gold = store.get_chunks(c["gold_chunk_ids"])
            if gold:
                domain_checked += 1
                domain_hit += any(domain in (ch.domain_features.get("domain") or []) for ch in gold)
    return {
        "profiler_usable": usable,
        "t_req_abs_error_years_mean": _mean(errs),
        "t_req_in_label_range": in_range,
        "domain_given": given,
        "domain_in_gold_chunk": domain_hit,
        "domain_checked_with_alive_gold": domain_checked,
    }
