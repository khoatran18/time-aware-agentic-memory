"""Chạy Profiler (Time Extractor) trên các câu hỏi của bộ con, ghi output/<timestamp>/profiler.jsonl. Chỉ gọi LLM, không cần Qdrant."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.config.loader import load_config
from tam.config.logging import get_logger, get_run_dir, setup_logging
from tam.llm.cache import open_cache
from tam.llm.factory import get_llm_for_role
from tam.query.profiler import Profiler


def main() -> None:
    """Profile từng câu hỏi (mức hard) và ghi kết quả."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="local")
    ap.add_argument("--level", choices=["hard", "easy"], default="hard", help="mức câu hỏi dùng để profile")
    ap.add_argument("--no-cache", action="store_true", help="không dùng cache LLM")
    ap.add_argument("--refresh-cache", action="store_true", help="bỏ qua cache cũ, gọi lại LLM và ghi đè")
    args = ap.parse_args()

    cfg = load_config()
    setup_logging(cfg)
    logger = get_logger("profile_eval")
    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    cache = None if args.no_cache else open_cache(ROOT / "data" / "llm_cache", refresh=args.refresh_cache)
    profiler = Profiler(get_llm_for_role(cfg, "time_extractor"), cache=cache)
    t_now = datetime.now(timezone.utc)

    out_path = get_run_dir() / "profiler.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for case in subset["cases"]:
            question = case[f"question_{args.level}"]
            try:
                q = profiler.profile(question, t_now)
                row = {"idx": case["idx"], "question": question, "t_now": t_now.date().isoformat(), "semantic_query": q.semantic_query,
                       "t_req": q.t_req.isoformat(), "filters": q.filters, "error": None}
            except ValueError as exc:  # t_req rác: ghi lại chứ không dừng cả lượt
                logger.error("Profile lỗi (%s): %s", case["idx"], exc)
                row = {"idx": case["idx"], "question": question, "error": str(exc)}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Ghi {out_path} ({len(subset['cases'])} câu)")
    if cache is not None:
        print(f"Cache LLM: {cache.hits} lần dùng lại, {cache.misses} lần gọi LLM")
        cache.close()


if __name__ == "__main__":
    main()
