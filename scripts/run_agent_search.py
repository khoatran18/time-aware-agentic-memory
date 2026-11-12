"""Chạy agent search kiểu A (kho text thuần, `data/text_corpus`) trên một bộ con câu hỏi TimeQA. GỌI LLM THẬT (role `agent`).

Kiểu A (mặc định): grep/read_page trên text thuần. Kiểu B (`--kind B`): vector_search/read_chunk trên kho Qdrant đã có (collection theo split của câu hỏi, embed cục bộ).
Ghi vào output/<timestamp>/: `run.log`, `agent_trace.jsonl`, `agent_calls.jsonl` (prompt, câu trả lời, TTFT/TPOT/token mỗi lần gọi), `llm_calls.jsonl`,
`results.jsonl` (mỗi câu một dòng) và in tóm tắt.
Ví dụ: python scripts/run_agent_search.py --n 1          # thử một câu
       python scripts/run_agent_search.py --n 20 --seed 1
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.agents.loop import AgentLoop, load_system_prompt
from tam.config.loader import load_config
from tam.config.logging import get_logger, get_run_dir, setup_logging
from tam.generation.scoring import contains
from tam.llm.cache import SqliteCache
from tam.llm.factory import get_llm_for_role
from tam.llm.metrics import percentile
from tam.tools.text_corpus import TextCorpus
from tam.tools.text_tools import text_tools
from tam.tools.vector_tools import VectorTools

logger = get_logger("run_agent_search")


def build_vector_tools(cfg, cases: list[dict], args):
    """Công cụ kiểu B trên kho Qdrant đã có. Collection = `tam_chunks_dev_<split>`; các câu hỏi phải cùng một split (mỗi lần chạy một kho)."""
    from tam.embedding.factory import get_embedder
    from tam.stores.vector.qdrant_store import QdrantStore

    index = json.loads((ROOT / "data/text_corpus.index.json").read_text(encoding="utf-8"))  # page_id -> {file, split}: tune | valid | test_clean (khác trường `split` của TimeQA)
    splits = {index[c["page_id"]]["split"] for c in cases}
    if not args.collection and len(splits) != 1:
        raise SystemExit(f"các câu hỏi thuộc nhiều split {sorted(map(str, splits))}; dùng --collection hoặc --subset khác")
    name = args.collection or f"{cfg.vector_store.collection}_{splits.pop()}"
    store = QdrantStore.from_config(cfg, get_embedder(cfg), name)
    logger.info("Kiểu B: collection %s, k_cap=%d, show_time=%s", name, args.k_cap, not args.hide_time)
    return VectorTools(store, None, k_cap=args.k_cap, show_time=not args.hide_time).tools()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default=str(ROOT / "dataset/eval/tune_base_subset.json"), help="bộ con có `cases` (mỗi case: idx, page_id, question_hard, targets, gold_chunk_ids)")
    ap.add_argument("--corpus", default=str(ROOT / "data/text_corpus"))
    ap.add_argument("--kind", choices=["A", "B"], default="A", help="A = text thuần (grep/read_page); B = kho Qdrant (vector_search/read_chunk)")
    ap.add_argument("--collection", default="", help="kiểu B: tên collection Qdrant; mặc định tam_chunks_dev_<split> theo split của các câu hỏi")
    ap.add_argument("--k-cap", type=int, default=50, help="kiểu B: trần cứng của k trong vector_search")
    ap.add_argument("--hide-time", action="store_true", help="kiểu B: ẩn khoảng hiệu lực của chunk khỏi kết quả (agent chỉ dựa vào văn bản)")
    ap.add_argument("--n", type=int, default=1, help="số câu lấy ngẫu nhiên")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--question-field", default="question_hard")
    ap.add_argument("--t-now", default="2026-11-03", help="ngày hiện tại đưa vào prompt (như bộ test T_now ở docs/weekly_reports/week_6)")
    ap.add_argument("--max-steps", type=int, default=5, help="số lần gọi LLM tối đa mỗi câu")
    ap.add_argument("--max-tokens", type=int, default=200_000)
    ap.add_argument("--prompt", default="v2", help="phiên bản prompt: v1 = trung tính (P0), v2 = có hướng dẫn suy luận thời gian (P1)")
    ap.add_argument("--no-cache", action="store_true", help="không dùng cache lần gọi LLM (mặc định: tra rồi ghi vào --cache-dir)")
    ap.add_argument("--cache-dir", default=str(ROOT / "data/llm_cache/agent"), help="thư mục cache riêng của agent (cache.sqlite), tách khỏi data/llm_cache/cache.sqlite của pipeline")
    ap.add_argument("--repeat-id", default="0", help="đưa vào khóa cache: cùng số thì tái dùng kết quả, khác số thì gọi mới (dùng khi lặp để đo dao động)")
    ap.add_argument("--refresh-cache", action="store_true", help="bỏ qua mục đã có và ghi đè bằng lần gọi mới")
    ap.add_argument("--workers", type=int, default=1, help="số câu chạy song song (mỗi câu một luồng, một mã phiên riêng)")
    ap.add_argument("--no-budget-notice", action="store_true", help="tắt báo số lượt còn lại và ép trả lời ở lượt cuối")
    ap.add_argument("--pick", default="", help="chỉ chạy các câu này, theo số thứ tự 1-based trong mẫu --n/--seed (vd 12,15,16,18,19)")
    ap.add_argument("--no-stream", action="store_true", help="gọi thường, không streaming (mất TTFT và TPOT)")
    ap.add_argument("--log-prompts", choices=["full", "delta", "off"], default="full")
    args = ap.parse_args()

    cfg = load_config()
    run_dir = setup_logging(cfg)
    role = cfg.llm.roles.agent
    session_header = cfg.llm.profiles[role].get("session_header")  # vd OpenCode Go: x-opencode-session
    llm = get_llm_for_role(cfg, "agent")
    cases = json.loads(Path(args.subset).read_text(encoding="utf-8"))["cases"]
    picked = random.Random(args.seed).sample(cases, min(args.n, len(cases)))
    corpus = TextCorpus.load(args.corpus)
    positions = [int(x) for x in args.pick.split(",") if x.strip()] or list(range(1, len(picked) + 1))
    chosen = [(pos, picked[pos - 1]) for pos in positions]
    profile = cfg.llm.profiles[role]
    cache = None if args.no_cache else SqliteCache(Path(args.cache_dir) / "cache.sqlite", refresh=args.refresh_cache, threadsafe=True)
    tools = text_tools(corpus) if args.kind == "A" else build_vector_tools(cfg, [c for _, c in chosen], args)
    agent = AgentLoop(llm, tools, load_system_prompt(args.t_now, args.prompt), budget_notice=not args.no_budget_notice, cache=cache,
                      cache_model=str(profile.get("cache_model") or profile.get("model_id") or role), cache_salt=args.repeat_id, max_steps=args.max_steps, max_total_tokens=args.max_tokens,
                      stream=not args.no_stream, model_name=role, log_prompts=args.log_prompts,
                      request_headers=(lambda qid: {session_header: f"{run_dir.name}-{qid}"}) if session_header else None)
    logger.info("Chạy %d câu, role agent=%s, prompt=%s, budget_notice=%s, max_steps=%d, cache=%s (repeat_id=%s), %d trang trong kho text", len(chosen), role,
                args.prompt, not args.no_budget_notice, args.max_steps, "tắt" if cache is None else args.cache_dir, args.repeat_id, len(corpus.pages))

    def run_one(item):
        i, case = item
        run = agent.run(case[args.question_field], query_id=f"q{i:03d}")
        gold_chunks = set(case["gold_chunk_ids"])
        first_seen = run.first_step_showing(case["targets"])
        return i, case, run, {"i": i, "idx": case["idx"], "question": case[args.question_field], "targets": case["targets"], "answer": run.answer,
                              "contains_target": contains(run.answer or "", case["targets"]) if run.answer else 0.0, "stop_reason": run.stop_reason,
                              "steps": run.steps, "tool_calls": run.tool_calls, "input_tokens": run.input_tokens, "output_tokens": run.output_tokens,
                              "cached_input_tokens": run.cached_input_tokens, "cache_hits": run.cache_hits, "llm_time_s": round(run.llm_time_s, 3), "tool_time_s": round(run.tool_time_s, 3),
                              "wall_s": round(run.wall_s, 3), "ttft_s": [round(t, 3) for t in run.ttft_s],
                              "gold_chunk_listed": bool(gold_chunks & set(run.chunk_ids)),  # chunk gold có trong danh sách trả về (lạc quan: grep chỉ trả đoạn trích)
                              "gold_text_step": first_seen, "saw_gold_text": first_seen is not None,  # lượt đầu tiên văn bản công cụ chứa chuỗi đáp án
                              "gold_chunk_ids": sorted(gold_chunks)}

    rows = []
    t0 = time.perf_counter()
    with (run_dir / "results.jsonl").open("w", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for i, case, run, row in pool.map(run_one, chosen):  # pool.map giữ thứ tự đầu vào; các câu vẫn chạy song song
            rows.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{i}/{len(picked)}] {run.stop_reason} steps={run.steps} tools={run.tool_calls} tokens={run.input_tokens}/{run.output_tokens} "
                  f"wall={run.wall_s:.1f}s | {case[args.question_field][:80]} -> {(run.answer or '')[:80]!r} (gold {case['targets']})")
    total_wall = time.perf_counter() - t0

    ok = [r for r in rows if r["stop_reason"] == "answer"]
    ttft = [t for r in rows for t in r["ttft_s"]]
    print(f"\nTóm tắt {len(rows)} câu: trả lời {len(ok)}, dừng khác {len(rows) - len(ok)}; chứa đáp án {sum(r['contains_target'] for r in rows):.0f}; "
          f"chunk gold có trong danh sách {sum(r['gold_chunk_listed'] for r in rows)}; chuỗi đáp án hiện trong văn bản công cụ {sum(r['saw_gold_text'] for r in rows)}")
    seen = [r["gold_text_step"] for r in rows if r["saw_gold_text"]]
    if seen:
        print(f"  lượt đầu tiên thấy chuỗi đáp án: p50={percentile(seen, 50):.1f} p90={percentile(seen, 90):.1f} max={max(seen)}")
    for key in ("steps", "tool_calls", "input_tokens", "output_tokens", "wall_s"):
        vals = [r[key] for r in rows]
        print(f"  {key}: p50={percentile(vals, 50):.1f} p90={percentile(vals, 90):.1f} max={max(vals):.1f} tổng={sum(vals):.0f}")
    if ttft:
        print(f"  TTFT (s) từng lượt: p50={percentile(ttft, 50):.2f} p90={percentile(ttft, 90):.2f} n={len(ttft)}")
    print(f"  lượt LLM trả từ cache: {sum(r['cache_hits'] for r in rows)}/{sum(r['steps'] for r in rows)} (số đo token/TTFT của lượt này lấy từ lần gọi thật trước đó)")
    print(f"Thời gian thực cả loạt: {total_wall:.1f}s (workers={args.workers})")
    print(f"Log: {get_run_dir()}")


if __name__ == "__main__":
    main()
