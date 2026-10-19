"""Báo cáo chất lượng ingestion trên một bộ con: đọc `extractions.jsonl` (scripts/ingest.py) và `<subset>_subset.json`.

Không gọi LLM hay Qdrant. Nhãn thời gian của dataset (`time_start`, `time_end`) là khoảng hiệu lực của *sự việc trả lời câu hỏi*,
còn mốc của chunk là hợp các sự việc trong đoạn, nên các số "đúng năm / phủ / giao" chỉ là phép đo gián tiếp (xem docs/eval/01).
"""
from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

_YEAR = re.compile(r"\d{4}")


def label_year(label: str) -> int:
    """Năm trong nhãn của dataset: "2005", "Dec 1965" -> 2005, 1965."""
    m = _YEAR.search(label)
    if not m:
        raise ValueError(f"nhãn thời gian không có năm: {label!r}")
    return int(m.group())


def load_extractions(path: str | Path) -> dict[str, dict[str, Any]]:
    """Đọc extractions.jsonl thành {chunk_id: dòng}."""
    with open(path, encoding="utf-8") as f:
        return {row["chunk_id"]: row for row in map(json.loads, f)}


def alive_chunk_ids(rows: dict[str, dict[str, Any]]) -> set[str]:
    """Chunk đã vào kho: có `start` (không bị bỏ vì không mốc hay mốc sai)."""
    return {cid for cid, r in rows.items() if r.get("start")}


def ingestion_report(subset: dict[str, Any], rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Gộp số liệu: số chunk, chunk bị bỏ, `ongoing`, chunk đáp án còn sống, domain khớp, độ đúng của mốc."""
    loaded = {cid: r for cid, r in rows.items() if r.get("start")}
    skipped = Counter(r["skipped"] for r in rows.values() if r.get("skipped"))
    domain_sizes = Counter(len(r.get("domain", [])) for r in rows.values())

    gold_total = gold_alive = domain_hit = start_ok = end_ok = covers = overlaps = 0
    dropped: list[dict[str, str]] = []
    for case in subset["cases"]:
        t0, t1 = label_year(case["time_start"]), label_year(case["time_end"])
        for gid in case["gold_chunk_ids"]:
            gold_total += 1
            r = loaded.get(gid)
            if r is None:
                dropped.append({"chunk_id": gid, "reason": (rows.get(gid) or {}).get("skipped") or "missing"})
                continue
            gold_alive += 1
            domain_hit += case["domain"] in r.get("domain", [])
            s = int(r["start"][:4])
            e = int(r["end"][:4]) if r.get("end") else None
            start_ok += s == t0
            end_ok += e == t1
            covers += s <= t0 and (e is None or e >= t1)
            overlaps += s <= t1 and (e is None or e >= t0)

    return {
        "chunks_total": len(rows),
        "chunks_loaded": len(loaded),
        "skipped": dict(skipped),
        "ongoing_loaded": sum(bool(r["ongoing"]) for r in loaded.values()),
        "ongoing_downgraded": sum(bool(r.get("ongoing_downgraded")) for r in rows.values()),
        "domain_label_counts": {n: domain_sizes.get(n, 0) for n in range(4)},
        "gold_total": gold_total,
        "gold_alive": gold_alive,
        "gold_dropped": dropped,
        "domain_match": domain_hit,
        "start_year_equals_label": start_ok,
        "end_year_equals_label": end_ok,
        "span_covers_label": covers,
        "span_overlaps_label": overlaps,
    }


def compare_runs(subset: dict[str, Any], runs: dict[str, dict[str, dict[str, Any]]]) -> list[dict[str, Any]]:
    """Báo cáo của nhiều lần chạy cạnh nhau, mỗi phần tử có thêm khóa `run`."""
    return [{"run": name, **ingestion_report(subset, rows)} for name, rows in runs.items()]


def flat_keys(reports: Iterable[dict[str, Any]]) -> list[str]:
    """Các khóa số vô hướng chung của các báo cáo, để in thành bảng."""
    return [k for k, v in next(iter(reports)).items() if isinstance(v, int)]
