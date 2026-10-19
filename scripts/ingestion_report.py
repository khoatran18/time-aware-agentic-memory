"""So sánh chất lượng ingestion của một hoặc nhiều lần chạy (thư mục output/<timestamp>/) và, nếu có, đánh giá Profiler."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.evaluation.ingestion_report import compare_runs, flat_keys, load_extractions
from tam.evaluation.profiler_report import load_profiled, profiler_report


def main() -> None:
    """In bảng so sánh các lần chạy; ghi JSON nếu có --out."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("runs", nargs="+", help="thư mục output/<timestamp> có extractions.jsonl; đặt tên bằng tên=thư_mục")
    ap.add_argument("--subset", default="local")
    ap.add_argument("--profiler", help="profiler.jsonl để đánh giá Profiler so với nhãn chunk của lần chạy cuối")
    ap.add_argument("--out", help="ghi toàn bộ kết quả ra file JSON này")
    args = ap.parse_args()

    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    runs = {}
    for spec in args.runs:
        name, _, path = spec.rpartition("=")
        runs[name or Path(path).name] = load_extractions(Path(path) / "extractions.jsonl")
    reports = compare_runs(subset, runs)

    keys = flat_keys(reports)
    print(f"{'':32}" + "".join(f"{r['run'][:14]:>16}" for r in reports))
    for k in keys:
        print(f"{k:32}" + "".join(f"{r[k]:>16}" for r in reports))
    for r in reports:
        print(f"{r['run']}: bỏ vì {r['skipped']}; chunk đáp án bị bỏ: {[d['chunk_id'] for d in r['gold_dropped']]}")

    result: dict = {"ingestion": reports}
    if args.profiler:
        pr = profiler_report(subset, load_profiled(args.profiler), list(runs.values())[-1])
        print("Profiler:", pr)
        result["profiler"] = pr
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
