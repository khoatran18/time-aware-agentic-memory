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
from tam.retrieval.temporal.expansion import PAGE_EXPANDS
from tam.retrieval.temporal.rerank import RERANK_MODES, RERANK_NORMS, RERANK_POOLS, CrossEncoderReranker
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.retrieval.temporal.scoring import DECAY_FROMS, END_MODES, OVERLAPS, TIME_MODES
from tam.stores.vector.qdrant_store import QdrantStore, collection_for

KS = (1, 3, 5)


def main() -> None:
    """Dựng retriever từ config, chạy các case, in và ghi metric."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collection", help="tên collection Qdrant; mặc định: tên trong config với bộ local, <tên>_<subset> với bộ khác")
    ap.add_argument("--subset", default="local")
    ap.add_argument("--mode", choices=["oracle", "e2e"], default="oracle")
    ap.add_argument("--profiler", help="profiler.jsonl (bắt buộc với e2e; với oracle thì dùng semantic_query của nó)")
    ap.add_argument("--extractions", help="extractions.jsonl của lần nạp hiện tại, để biết chunk đáp án nào còn sống")
    ap.add_argument("--facets", choices=["none", "domain", "boost"], default="none",
                    help="domain của Profiler: domain = lọc cứng, boost = cộng điểm W3 (cần --w3 > 0); chỉ e2e")
    ap.add_argument("--w2", type=float, help="ghi đè retrieval.w2 (trọng số điểm thời gian); w1 = 1 - w2")
    ap.add_argument("--no-temporal", action="store_true", help="W1=1, W2=0: bỏ điểm thời gian")
    ap.add_argument("--method", choices=["temporal", *METHODS], default="temporal",
                    help="temporal = Cơ chế 1; dense | bm25 | hybrid = baseline plain RAG (không lọc, không điểm thời gian)")
    ap.add_argument("--t-unknown", type=float, help="bật nhánh chunk không mốc với điểm thời gian cố định này (kho phải nạp bằng --keep-undated)")
    ap.add_argument("--w3", type=float, help="ghi đè retrieval.w3 (trọng số Domain_Match)")
    ap.add_argument("--end-mode", choices=list(END_MODES), help="ghi đè retrieval.end_mode: stored (C) | open (A) | decay (B) | unknown_decay (chỉ unknown giảm dần, ongoing giữ 1.0)")
    ap.add_argument("--open-decay", type=float, help="ghi đè retrieval.open_decay (với --end-mode decay hoặc unknown_decay)")
    ap.add_argument("--sparse-weight", type=float, help="ghi đè retrieval.sparse_weight: trọng số BM25 trong RRF (1 = thường, 0 = bỏ BM25, chỉ dense)")
    ap.add_argument("--decay-from", choices=list(DECAY_FROMS), help="ghi đè retrieval.decay_from: mốc tính khoảng cách của chunk đã hết hạn (TH2): start (mặc định) | end")
    ap.add_argument("--time-mode", choices=list(TIME_MODES), help="ghi đè retrieval.time_mode: point (mặc định, một điểm t_req) | range (khoảng [t_req, t_end], cần profiler.jsonl chạy bằng profile_eval.py --ranges)")
    ap.add_argument("--overlap", choices=list(OVERLAPS), help="ghi đè retrieval.overlap (chỉ với --time-mode range): binary | coverage (độ phủ |C ∩ Q| / |Q|)")
    ap.add_argument("--neighbors", type=int, help="ghi đè retrieval.neighbor_window: số chunk liền kề mỗi phía lấy làm ngữ cảnh")
    ap.add_argument("--page-expand", choices=list(PAGE_EXPANDS), help="ghi đè retrieval.page_expand: none | time (chunk cùng trang còn hợp lệ theo thời gian) | page (cùng trang, không lọc thời gian; đối chứng)")
    ap.add_argument("--page-top", type=int, help="ghi đè retrieval.page_top: số trang (xếp theo Top-K) được mở rộng")
    ap.add_argument("--page-per", type=int, help="ghi đè retrieval.page_per: số chunk thêm tối đa mỗi trang")
    ap.add_argument("--rerank", help="bật cross-encoder rerank (decisions/07 đề xuất 4): tên model fastembed, vd Xenova/ms-marco-MiniLM-L-6-v2")
    ap.add_argument("--rerank-top", type=int, help="ghi đè retrieval.rerank_top: số ứng viên đầu được chấm lại")
    ap.add_argument("--rerank-mode", choices=list(RERANK_MODES), help="ghi đè retrieval.rerank_mode: replace | mix")
    ap.add_argument("--rerank-alpha", type=float, help="ghi đè retrieval.rerank_alpha (chỉ mix): trọng số Semantic cũ")
    ap.add_argument("--rerank-pool", choices=list(RERANK_POOLS), help="ghi đè retrieval.rerank_pool: nhóm được chấm lại theo final | semantic")
    ap.add_argument("--rerank-norm", choices=list(RERANK_NORMS), help="ghi đè retrieval.rerank_norm: cách chuẩn hóa điểm cross-encoder (mặc định minmax)")
    ap.add_argument("--rerank-no-temporal", action="store_true", help="sau khi cross-encoder chấm, xếp nhóm chỉ theo điểm cross-encoder (không cộng Temporal lần hai)")
    ap.add_argument("--rerank-time", action="store_true", help="ghép khoảng hiệu lực của chunk vào văn bản đưa cho cross-encoder")
    ap.add_argument("--inferred-factor", type=float, help="ghi đè retrieval.inferred_factor: hệ số (0,1] cho điểm thời gian của chunk có mốc suy luận")
    ap.add_argument("--top-k", type=int, help="ghi đè retrieval.top_k: số chunk trả về (Plain RAG cũng dùng; để vẽ đường cong ngữ cảnh)")
    ap.add_argument("--level", choices=["hard", "easy"], default="hard")
    args = ap.parse_args()
    if args.mode == "e2e" and not args.profiler:
        ap.error("--mode e2e cần --profiler")

    cfg = load_config()
    setup_logging(cfg)
    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    profiled = load_profiled(args.profiler) if args.profiler else None
    alive = alive_chunk_ids(load_extractions(args.extractions)) if args.extractions else None

    store = QdrantStore.from_config(cfg, get_embedder(cfg), collection_for(cfg, args.subset, args.collection))
    r = cfg.retrieval
    settings = {
        "w1": 1.0 if args.no_temporal else (r.w1 if args.w2 is None else 1.0 - args.w2),
        "w2": 0.0 if args.no_temporal else (r.w2 if args.w2 is None else args.w2),
        "w3": r.get("w3", 0.0) if args.w3 is None else args.w3,
        "decay_lambda": r.decay_lambda, "rrf_k": r.rrf_k, "top_n": r.top_n, "top_k": args.top_k or r.top_k,
        "end_mode": args.end_mode or r.get("end_mode", "stored"),
        "open_decay": r.get("open_decay", 0.1) if args.open_decay is None else args.open_decay,
        "neighbor_window": r.get("neighbor_window", 0) if args.neighbors is None else args.neighbors,
        "t_unknown": r.get("t_unknown", None) if args.t_unknown is None else args.t_unknown,
        "sparse_weight": r.get("sparse_weight", 1.0) if args.sparse_weight is None else args.sparse_weight,
        "decay_from": args.decay_from or r.get("decay_from", "start"),
        "time_mode": args.time_mode or r.get("time_mode", "point"),
        "overlap": args.overlap or r.get("overlap", "binary"),
        "page_expand": args.page_expand or r.get("page_expand", "none"),
        "page_top": args.page_top or r.get("page_top", 3),
        "page_per": args.page_per or r.get("page_per", 2),
        "rerank_top": args.rerank_top or r.get("rerank_top", 20),
        "rerank_mode": args.rerank_mode or r.get("rerank_mode", "replace"),
        "rerank_alpha": r.get("rerank_alpha", 0.5) if args.rerank_alpha is None else args.rerank_alpha,
        "rerank_pool": args.rerank_pool or r.get("rerank_pool", "final"),
        "rerank_time": args.rerank_time or r.get("rerank_time", False),
        "rerank_norm": args.rerank_norm or r.get("rerank_norm", "minmax"),
        "rerank_temporal": False if args.rerank_no_temporal else r.get("rerank_temporal", True),
        "inferred_factor": r.get("inferred_factor", 1.0) if args.inferred_factor is None else args.inferred_factor,
    }
    rerank_model = args.rerank or r.get("rerank")
    if settings["time_mode"] == "range" and args.mode != "e2e":
        ap.error("--time-mode range chỉ dùng với --mode e2e")
    if args.method == "temporal":
        reranker = CrossEncoderReranker(rerank_model, cache_dir=r.get("rerank_cache_dir"), score_cache=r.get("rerank_score_cache")) if rerank_model else None
        retriever = TemporalRetriever(store, reranker=reranker, **settings)
    else:
        retriever = PlainRetriever(store, method=args.method, top_n=settings["top_n"], top_k=settings["top_k"], rrf_k=settings["rrf_k"],
                                   neighbor_window=settings["neighbor_window"],
                                   reranker=CrossEncoderReranker(rerank_model, cache_dir=r.get("rerank_cache_dir"), score_cache=r.get("rerank_score_cache")) if rerank_model else None,
                                   rerank_top=settings["rerank_top"], rerank_mode=settings["rerank_mode"], rerank_alpha=settings["rerank_alpha"])
    if args.facets == "boost" and settings["w3"] <= 0:
        ap.error("--facets boost cần --w3 > 0")

    cases = build_cases(subset, mode=args.mode, profiled=profiled, alive_ids=alive, facets=args.facets, level=args.level,
                        use_range=settings["time_mode"] == "range")
    result = evaluate_retrieval(retriever, cases, KS, store=store)
    if args.mode == "e2e":
        result["summary"].update(profiler_stage(subset, profiled, store))

    # Hit@k tính trên MỌI câu theo nhãn gốc (chunk đáp án bị bỏ lúc ingestion vẫn tính là trượt) để thấy trần của ingestion
    gold_all = {c["idx"]: set(c["gold_chunk_ids"]) for c in subset["cases"]}
    rows = result["cases"]
    for k in KS:
        result["summary"][f"hit@{k}_all_gold"] = sum(hit_at_k(r["ranked_ids"], gold_all[r["id"]], k) for r in rows) / len(rows)
    result["summary"]["mrr_all_gold"] = sum(reciprocal_rank(r["ranked_ids"], gold_all[r["id"]]) for r in rows) / len(rows)
    result["summary"]["config"] = {"subset": args.subset, "collection": collection_for(cfg, args.subset, args.collection), "mode": args.mode, "facets": args.facets, "method": args.method, "no_temporal": args.no_temporal, "retrieval": {**settings, "rerank": rerank_model},
                                   "level": args.level, "n_cases_run": len(cases)}

    run_dir = get_run_dir()
    (run_dir / "metrics.json").write_text(json.dumps(result["summary"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with open(run_dir / "predictions.jsonl", "w", encoding="utf-8") as f:
        f.writelines(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"Ghi vào {run_dir}")


if __name__ == "__main__":
    main()
