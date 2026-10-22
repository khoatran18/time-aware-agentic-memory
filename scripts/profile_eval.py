"""Chạy Profiler (Time Extractor) trên các câu hỏi của bộ con, ghi output/<timestamp>/profiler.jsonl. Chỉ gọi LLM, không cần Qdrant."""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.config.loader import load_config
from tam.config.logging import get_logger, get_run_dir, setup_logging
from tam.llm.cache import SqliteCache, open_cache
from tam.llm.factory import get_llm_for_role
from tam.llm.structured import LlmUnavailable
from tam.query import profiler as profiler_v1
from tam.query import range_profiler as profiler_v2
from tam.query.profiler import Profiler
from tam.query.range_profiler import RangeProfiler


class PacedCache(SqliteCache):
    """Cache SQLite riêng cho mỗi luồng; trượt cache (sắp gọi LLM) thì chờ tới lượt trong lịch chung, để cả các luồng không vượt `rpm` request/phút."""

    def __init__(self, path: Path, pacer: Pacer, *, refresh: bool = False) -> None:
        super().__init__(path, refresh=refresh)
        self._pacer = pacer

    def get(self, key: str):  # type: ignore[override]
        value = super().get(key)
        if value is None:
            self._pacer.wait()
        return value


class Pacer:
    """Lịch chung: hai lần bắt đầu request cách nhau ít nhất 60/rpm giây."""

    def __init__(self, rpm: float) -> None:
        self._gap, self._lock, self._next = 60.0 / rpm, threading.Lock(), time.monotonic()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self._gap
        time.sleep(max(0.0, start - now))


def main() -> None:
    """Profile từng câu hỏi (mức hard) và ghi kết quả."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="local")
    ap.add_argument("--level", choices=["hard", "easy"], default="hard", help="mức câu hỏi dùng để profile")
    ap.add_argument("--ranges", action="store_true",
                    help="dùng RangeProfiler: ghi khoảng [t_req = qs, t_end = qe] kèm t_start/t_end thô và bound (decisions/07 đề xuất 1)")
    ap.add_argument("--before-lower", default="point", choices=["point", "min"],
                    help="với --ranges: cận dưới của \"before X\": point (qs = qe = X) hoặc min (mở về 0001-01-01)")
    ap.add_argument("--workers", type=int, default=1,
                    help="số luồng (chỉ với --ranges); >1 thì mỗi luồng có cache SQLite riêng và dùng chung lịch --rpm; mặc định 1 = chạy tuần tự như cũ")
    ap.add_argument("--rpm", type=float, default=13.0, help="với --workers > 1: số request LLM tối đa mỗi phút (hạn mức Gemini miễn phí 15)")
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

    def make_row(profiler, case) -> dict:
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
        return row

    failed = 0
    if args.workers > 1:
        if not args.ranges or args.no_cache:
            ap.error("--workers > 1 cần --ranges và cache LLM (không dùng --no-cache)")
        pacer, local, stop = Pacer(args.rpm), threading.local(), threading.Event()
        if cache is not None:
            cache.close()  # mỗi luồng mở cache riêng; bản JSON xem nhanh được dựng lại ở lần mở sau
        done = [0]

        def work(case):
            if stop.is_set():
                return case["idx"], None
            if not hasattr(local, "profiler"):
                local.cache = PacedCache(ROOT / "data" / "llm_cache" / "cache.sqlite", pacer, refresh=args.refresh_cache)
                local.profiler = RangeProfiler(get_llm_for_role(cfg, "time_extractor"), cache=local.cache, before_lower=args.before_lower)
            try:
                row = make_row(local.profiler, case)
            except LlmUnavailable as exc:  # hết hạn mức hoặc Google quá tải kéo dài: dừng, chạy lại sẽ dùng cache cho phần đã xong
                logger.error("LLM chưa dùng được (%s): %s", case["idx"], str(exc)[:120])
                stop.set()
                return case["idx"], None
            done[0] += 1
            if done[0] % 20 == 0:
                print(f"{done[0]}/{len(subset['cases'])} câu", flush=True)
            return case["idx"], row

        with ThreadPoolExecutor(args.workers) as ex:
            results = list(ex.map(work, subset["cases"]))
        rows = [r for _, r in results if r is not None]
        failed = len(results) - len(rows)
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(r, ensure_ascii=False) + "\n" for r in rows)
        cache = None
    else:
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(json.dumps(make_row(profiler, case), ensure_ascii=False) + "\n" for case in subset["cases"])
    print(f"Ghi {out_path} ({len(subset['cases'])} câu)")
    if failed:
        print(f"{failed} câu chưa profile được (LLM chưa dùng được); chạy lại để làm tiếp từ cache")
        sys.exit(1)
    if cache is not None:
        print(f"Cache LLM: {cache.hits} lần dùng lại, {cache.misses} lần gọi LLM")
        cache.close()


if __name__ == "__main__":
    main()
