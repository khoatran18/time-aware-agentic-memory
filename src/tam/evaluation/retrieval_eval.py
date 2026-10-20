"""Dựng EvalCase cho retrieval từ bộ con (oracle t_req hoặc t_req của Profiler) rồi chấm bằng `evaluate_retrieval`."""
from __future__ import annotations

from collections.abc import Collection
from datetime import datetime, timezone
from typing import Any

from tam.evaluation.ingestion_report import label_year
from tam.evaluation.metrics_temporal import EvalCase


def oracle_t_req(case: dict[str, Any]) -> datetime:
    """Điểm giữa khoảng nhãn, tính theo năm: từ 1/1 của `time_start` đến 31/12 của `time_end`.

    Nhãn là khoảng hiệu lực của sự việc đáp án nên điểm giữa luôn nằm trong khoảng đó; đây là một lựa chọn quy ước, không phải mốc
    người hỏi nói (câu hỏi nêu tháng/khoảng khác).
    """
    lo = datetime(label_year(case["time_start"]), 1, 1, tzinfo=timezone.utc)
    hi = datetime(label_year(case["time_end"]), 12, 31, tzinfo=timezone.utc)
    return lo + (hi - lo) / 2


def build_cases(
    subset: dict[str, Any], *, mode: str, profiled: dict[str, dict[str, Any]] | None = None,
    alive_ids: Collection[str] | None = None, facets: str = "none", level: str = "hard", use_range: bool = False,
) -> list[EvalCase]:
    """EvalCase cho mỗi câu. `mode`: "oracle" (t_req từ nhãn, semantic_query của Profiler nếu có) hoặc "e2e" (t_req và domain từ Profiler).

    `alive_ids`: nếu có, `gold_ids` chỉ giữ chunk đã vào kho, nên câu mà chunk đúng bị bỏ lúc ingestion có `gold_ids` rỗng
    (không tính vào Hit@k, MRR). `facets`: "none" không dùng domain; "domain" lọc cứng theo domain của Profiler; "boost" chỉ cộng điểm
    (cần `w3` > 0 ở retriever). Cả hai chỉ dùng được với e2e.
    `use_range` (chỉ e2e): lấy thêm `t_end` (điểm cuối khoảng hỏi) từ dòng Profiler chạy bằng `profile_eval.py --ranges`; thiếu `t_end` thì báo lỗi.
    Facet `country` không bao giờ được dùng: chunk TimeQA không có `country` nên lọc theo nó làm kết quả rỗng.
    """
    if mode not in ("oracle", "e2e"):
        raise ValueError(f"mode không hợp lệ: {mode!r}")
    cases = []
    for c in subset["cases"]:
        gold = frozenset(c["gold_chunk_ids"]) if alive_ids is None else frozenset(c["gold_chunk_ids"]) & set(alive_ids)
        row = (profiled or {}).get(c["idx"])
        usable = bool(row) and not row.get("error")
        if mode == "oracle":
            # cùng semantic_query với e2e (nếu có Profiler) để hai chế độ chỉ khác nhau ở t_req
            t_req, query, filters = oracle_t_req(c), row["semantic_query"] if usable else c[f"question_{level}"], {}
            boost = ()
        else:
            if not usable:
                continue  # Profiler lỗi: không có t_req để truy xuất
            t_req, query = datetime.fromisoformat(row["t_req"]), row["semantic_query"]
            t_end = None
            if use_range:
                if not row.get("t_end"):
                    raise ValueError(f"Dòng Profiler {c['idx']} không có t_end: chạy profile_eval.py --ranges")
                t_end = datetime.fromisoformat(row["t_end"])
            domain = (row.get("filters") or {}).get("domain")
            filters = {"domain": domain} if facets == "domain" and domain else {}
            boost = (domain,) if facets == "boost" and domain else ()
        cases.append(EvalCase(id=c["idx"], query=query, t_req=t_req, gold_ids=gold, filters=filters, domains=boost,
                              answers=tuple(c.get("targets") or ()), t_end=t_end if mode == "e2e" else None))
    return cases
