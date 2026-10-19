"""Chạy retrieval Cơ chế 1 trên bộ con và ghi metrics.json, predictions.jsonl vào output/<timestamp>/.

Chế độ `oracle`: t_req lấy từ nhãn dataset (đo riêng chất lượng retrieval). Chế độ `e2e`: t_req do Profiler tạo (cần
--profiler profiler.jsonl từ scripts/profile_eval.py). `--no-temporal` đặt W1=1, W2=0 (bỏ điểm thời gian, vẫn giữ lọc cứng thời gian).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.config.loader import load_config
from tam.config.logging import get_run_dir, setup_logging
from tam.embedding.factory import get_embedder
from tam.evaluation.funnel import profiler_stage
from tam.evaluation.ingestion_report import alive_chunk_ids, load_extractions
from tam.evaluation.metrics_temporal import evaluate_retrieval, hit_at_k, reciprocal_rank
from tam.evaluation.profiler_report import load_profiled
from tam.evaluation.retrieval_eval import build_cases
from tam.retrieval.baseline import METHODS, PlainRetriever
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.retrieval.temporal.scoring import END_MODES
from tam.stores.vector.qdrant_store import QdrantStore

KS = (1, 3, 5)


def main() -> None:
    """Dựng retriever từ config, chạy các case, in và ghi metric."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="local")
    ap.add_argument("--mode", choices=["oracle", "e2e"], default="oracle")
    ap.add_argument("--profiler", help="profiler.jsonl (bắt buộc với e2e; với oracle thì dùng semantic_query của nó)")
    ap.add_argument("--extractions", help="extractions.jsonl của lần nạp hiện tại, để biết chunk đáp án nào còn sống")
    ap.add_argument("--facets", choices=["none", "domain", "boost"], default="none",
                    help="domain của Profiler: domain = lọc cứng, boost = cộng điểm W3 (cần --w3 > 0); chỉ e2e")
    ap.add_argument("--no-temporal", action="store_true", help="W1=1, W2=0: bỏ điểm thời gian")
    ap.add_argument("--method", choices=["temporal", *METHODS], default="temporal",
                    help="temporal = Cơ chế 1; dense | bm25 | hybrid = baseline plain RAG (không lọc, không điểm thời gian)")
    ap.add_argument("--t-unknown", type=float, help="bật nhánh chunk không mốc với điểm thời gian cố định này (kho phải nạp bằng --keep-undated)")
    ap.add_argument("--w3", type=float, help="ghi đè retrieval.w3 (trọng số Domain_Match)")
    ap.add_argument("--end-mode", choices=list(END_MODES), help="ghi đè retrieval.end_mode: stored (C) | open (A) | decay (B)")
    ap.add_argument("--open-decay", type=float, help="ghi đè retrieval.open_decay (chỉ với --end-mode decay)")
    ap.add_argument("--neighbors", type=int, help="ghi đè retrieval.neighbor_window: số chunk liền kề mỗi phía lấy làm ngữ cảnh")
    ap.add_argument("--level", choices=["hard", "easy"], default="hard")
    args = ap.parse_args()
    if args.mode == "e2e" and not args.profiler:
        ap.error("--mode e2e cần --profiler")

    cfg = load_config()
    setup_logging(cfg)
    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    profiled = load_profiled(args.profiler) if args.profiler else None
    alive = alive_chunk_ids(load_extractions(args.extractions)) if args.extractions else None

    store = QdrantStore.from_config(cfg, get_embedder(cfg))
    r = cfg.retrieval
    settings = {
        "w1": 1.0 if args.no_temporal else r.w1, "w2": 0.0 if args.no_temporal else r.w2,
        "w3": r.get("w3", 0.0) if args.w3 is None else args.w3,
        "decay_lambda": r.decay_lambda, "rrf_k": r.rrf_k, "top_n": r.top_n, "top_k": r.top_k,
        "end_mode": args.end_mode or r.get("end_mode", "stored"),
        "open_decay": r.get("open_decay", 0.1) if args.open_decay is None else args.open_decay,
        "neighbor_window": r.get("neighbor_window", 0) if args.neighbors is None else args.neighbors,
        "t_unknown": r.get("t_unknown", None) if args.t_unknown is None else args.t_unknown,
    }
    if args.method == "temporal":
        retriever = TemporalRetriever(store, **settings)
    else:
        retriever = PlainRetriever(store, method=args.method, top_n=settings["top_n"], top_k=settings["top_k"], rrf_k=settings["rrf_k"])
    if args.facets == "boost" and settings["w3"] <= 0:
        ap.error("--facets boost cần --w3 > 0")

    cases = build_cases(subset, mode=args.mode, profiled=profiled, alive_ids=alive, facets=args.facets, level=args.level)
    result = evaluate_retrieval(retriever, cases, KS, store=store)
    if args.mode == "e2e":
        result["summary"].update(profiler_stage(subset, profiled, store))

    # Hit@k tính trên MỌI câu theo nhãn gốc (chunk đáp án bị bỏ lúc ingestion vẫn tính là trượt) để thấy trần của ingestion
    gold_all = {c["idx"]: set(c["gold_chunk_ids"]) for c in subset["cases"]}
    rows = result["cases"]
    for k in KS:
        result["summary"][f"hit@{k}_all_gold"] = sum(hit_at_k(r["ranked_ids"], gold_all[r["id"]], k) for r in rows) / len(rows)
    result["summary"]["mrr_all_gold"] = sum(reciprocal_rank(r["ranked_ids"], gold_all[r["id"]]) for r in rows) / len(rows)
    result["summary"]["config"] = {"mode": args.mode, "facets": args.facets, "method": args.method, "no_temporal": args.no_temporal, "retrieval": settings,
                                   "level": args.level, "n_cases_run": len(cases)}

    run_dir = get_run_dir()
    (run_dir / "metrics.json").write_text(json.dumps(result["summary"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with open(run_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"Ghi vào {run_dir}")


if __name__ == "__main__":
    main()
