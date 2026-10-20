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
from tam.query import profiler as profiler_v1
from tam.query import range_profiler as profiler_v2
from tam.query.profiler import Profiler
from tam.query.range_profiler import RangeProfiler


def main() -> None:
    """Profile từng câu hỏi (mức hard) và ghi kết quả."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="local")
    ap.add_argument("--level", choices=["hard", "easy"], default="hard", help="mức câu hỏi dùng để profile")
    ap.add_argument("--ranges", action="store_true",
                    help="dùng RangeProfiler: ghi khoảng [t_req = qs, t_end = qe] kèm t_start/t_end thô và bound (decisions/07 đề xuất 1)")
    ap.add_argument("--before-lower", default="point", choices=["point", "min"],
                    help="với --ranges: cận dưới của \"before X\": point (qs = qe = X) hoặc min (mở về 0001-01-01)")
    ap.add_argument("--no-cache", action="store_true", help="không dùng cache LLM")
    ap.add_argument("--refresh-cache", action="store_true", help="bỏ qua cache cũ, gọi lại LLM và ghi đè")
    args = ap.parse_args()

    cfg = load_config()
    setup_logging(cfg)
    logger = get_logger("profile_eval")
    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    cache = None if args.no_cache else open_cache(ROOT / "data" / "llm_cache", refresh=args.refresh_cache)
    llm = get_llm_for_role(cfg, "time_extractor")
    profiler = RangeProfiler(llm, cache=cache, before_lower=args.before_lower) if args.ranges else Profiler(llm, cache=cache)
    t_now = datetime.now(timezone.utc)

    prompt_version = (profiler_v2 if args.ranges else profiler_v1).PROMPT_VERSION  # ghi vào từng dòng để benchmark biết dùng prompt nào
    out_path = get_run_dir() / "profiler.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for case in subset["cases"]:
            question = case[f"question_{args.level}"]
            try:
                raw = profiler.extract(question, t_now) if args.ranges else None
                q = profiler.build(raw, question, t_now) if args.ranges else profiler.profile(question, t_now)
                row = {"idx": case["idx"], "question": question, "t_now": t_now.date().isoformat(), "semantic_query": q.semantic_query,
                       "t_req": q.t_req.isoformat(), "filters": q.filters, "prompt_version": prompt_version, "error": None}
                if args.ranges:
                    row.update({"t_end": q.t_end.isoformat(), "bound": raw.bound, "t_start_raw": raw.t_start, "t_end_raw": raw.t_end,
                                "use_t_now": raw.use_t_now})
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
