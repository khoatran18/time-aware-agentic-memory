"""Báo cáo Profiler trên một bộ con: đọc `profiler.jsonl` (scripts/profile_eval.py), nhãn thời gian và nhãn domain của chunk."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tam.evaluation.ingestion_report import label_year


def load_profiled(path: str | Path) -> dict[str, dict[str, Any]]:
    """Đọc profiler.jsonl thành {idx: dòng}."""
    with open(path, encoding="utf-8") as f:
        return {row["idx"]: row for row in map(json.loads, f)}


def profiler_report(
    subset: dict[str, Any], profiled: dict[str, dict[str, Any]], extractions: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """Số câu lỗi, `t_req` nằm trong khoảng nhãn, và `domain` Profiler điền có khớp nhãn chunk đáp án không.

    `domain_filter_would_drop_gold`: số câu Profiler điền domain nhưng chunk đáp án (còn sống) không có nhãn đó, tức nếu
    lọc cứng theo domain thì chunk đúng bị loại (xem docs/decisions/01).
    """
    errors = in_range = domain_set = domain_agree = would_drop = n_ok = 0
    for case in subset["cases"]:
        row = profiled.get(case["idx"])
        if row is None or row.get("error"):
            errors += 1
            continue
        n_ok += 1
        year = int(row["t_req"][:4])
        in_range += label_year(case["time_start"]) <= year <= label_year(case["time_end"])
        domain = (row.get("filters") or {}).get("domain")
        if not domain:
            continue
        domain_set += 1
        alive = [extractions[g] for g in case["gold_chunk_ids"] if extractions.get(g, {}).get("start")]
        if not alive:
            continue
        agree = any(domain in r.get("domain", []) for r in alive)
        domain_agree += agree
        would_drop += not agree
    return {
        "n_cases": len(subset["cases"]), "errors": errors,
        "t_req_in_label_range": in_range, "t_req_checked": n_ok,
        "domain_set": domain_set, "domain_null": n_ok - domain_set,
        "domain_agrees_with_gold_chunk": domain_agree, "domain_filter_would_drop_gold": would_drop,
    }
