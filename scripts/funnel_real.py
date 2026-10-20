"""Phân loại câu theo chỗ rớt của chunk đúng (phễu) cho vài cấu hình chính của một bộ, ghi CSV để vẽ `funnel.svg`.

Đầu vào: TSV `nhãn<TAB>thư mục output` của các lần chạy (như `summarize_runs.py`), `--extractions` và `--profiler` của bộ đó.
Mỗi câu có chunk đáp án rơi vào đúng một nhóm: trúng top-5; không vào ứng viên; bị lọc cứng vì chunk đúng không có mốc;
bị lọc cứng vì `start` sau `t_req`; vào ứng viên nhưng xếp sau top-5.
Dùng: python scripts/funnel_real.py runs.tsv --subset real --extractions ... --out dataset/eval/real_funnel.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_runs import describe

# (nhãn trong biểu đồ, điều kiện chọn lần chạy)
PICKS = [
    ("Plain RAG · dense", lambda i, c: i["kind"] == "baseline" and i["base"] == "dense"),
    ("Cơ chế 1 · hybrid · stored · tắt", lambda i, c: i["base"] == "hybrid" and i["end_mode"] == "stored" and i["t_unknown"] == "" and not i["neighbors"] and i["facets"] == "none" and not i["only_filter"]),
    ("Cơ chế 1 · dense · stored · tắt", lambda i, c: i["base"] == "dense" and i["end_mode"] == "stored" and i["t_unknown"] == "" and not i["neighbors"] and i["facets"] == "none" and not i["only_filter"]),
    ("Cơ chế 1 · dense · stored · t_unknown 0.1", lambda i, c: i["base"] == "dense" and i["end_mode"] == "stored" and i["t_unknown"] == 0.1 and not i["neighbors"] and i["facets"] == "none" and not i["only_filter"]),
    ("Cơ chế 1 · dense · unknown decay 0.1 · t_unknown 0.1", lambda i, c: i["base"] == "dense" and i["end_mode"] == "unknown decay 0.1" and i["t_unknown"] == 0.1 and not i["neighbors"] and i["facets"] == "none"),
]
GROUPS = ["trúng top-5", "không vào ứng viên", "bị lọc: chunk đúng không có mốc", "bị lọc: start sau t_req", "xếp sau top-5"]


def classify(pred: dict, gold: list[str], extractions: dict, *, filtered: bool, keeps_undated: bool) -> str:
    """Nhóm của một câu có đáp án. `filtered`: cấu hình có lọc thời gian (Plain RAG thì không); `keeps_undated`: bật `t_unknown`,
    khi đó chunk không mốc qua được bộ lọc nên chỉ còn lỗi xếp hạng."""
    if pred["hit"]["5"] == 1.0:
        return GROUPS[0]
    undated = all(extractions.get(g) is None or extractions[g]["start"] is None for g in gold)
    if filtered and not any(pred["gold_pass_filter"].values()) and not (undated and keeps_undated):
        return GROUPS[2] if undated else GROUPS[3]
    st = pred["stages"]
    return GROUPS[1] if st.get("fused") is None else GROUPS[4]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs")
    ap.add_argument("--subset", default="real")
    ap.add_argument("--extractions", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    gold = {c["idx"]: c["gold_chunk_ids"] for c in subset["cases"]}
    ext = {}
    for line in (ROOT / args.extractions).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        ext[r["chunk_id"]] = r
    runs = []
    for line in Path(args.runs).read_text(encoding="utf-8").splitlines():
        _label, d, rc = (line.split("\t") + ["", "0"])[:3]
        if d and rc.strip() in ("", "0"):
            runs.append(d)
    rows = []
    for label, cond in PICKS:
        for d in runs:
            m = json.loads((ROOT / d / "metrics.json").read_text(encoding="utf-8"))
            info = describe(m["config"])
            if m["config"].get("mode", "e2e") == "e2e" and cond(info, m["config"]):
                preds = [json.loads(x) for x in (ROOT / d / "predictions.jsonl").read_text(encoding="utf-8").splitlines()]
                filtered = m["config"].get("method", "temporal") == "temporal"
                keeps = m["config"].get("retrieval", {}).get("t_unknown") is not None
                cnt = Counter(classify(p, gold[p["id"]], ext, filtered=filtered, keeps_undated=keeps) for p in preds if p["has_gold"])
                rows.append({"config": label, "n": sum(cnt.values()), **{g: cnt.get(g, 0) for g in GROUPS}, "dir": Path(d).name})
                break
    with open(args.out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["config", "n", *GROUPS, "dir"])
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r["config"], {g: r[g] for g in GROUPS})


if __name__ == "__main__":
    main()
