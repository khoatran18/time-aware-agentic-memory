"""Chạy agent search kiểu A (kho text thuần, `data/text_corpus`) trên một bộ con câu hỏi TimeQA. GỌI LLM THẬT (role `agent`).

Kiểu A (mặc định): grep/read_page trên text thuần. Kiểu B (`--kind B`, thêm `--graph` cho timeline/events_of_chunk trên Neo4j): vector_search/read_chunk trên kho Qdrant đã có (collection theo split của câu hỏi, embed cục bộ).
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


def load_allowed(path: str) -> set[str] | None:
    """--pages-file -> tập tên trang đã chuẩn hóa (None nếu không đặt cờ)."""
    if not path:
        return None
    from tam.tools.graph_tools import page_name
    return {page_name(l, True) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()}


# Cấu hình X (`2d10bbb571`, cấu hình chính của Cơ chế 1 từ 2026-11-03; docs/eval/07 mục 9, docs/eval/09 mục 10), bọc làm công cụ `temporal_search`.
# `top_k` do công cụ cắt theo `k` của agent nên đặt bằng trần; `rerank_score_cache` để trống: cache điểm làm thời gian đo không còn là thời gian chấm thật.
X_SETTINGS = dict(w1=0.7, w2=0.3, decay_lambda=0.25, rrf_k=60, top_n=50, end_mode="unknown_decay", open_decay=0.05, decay_from="end",
                  time_mode="range", overlap="binary", t_unknown=0.2, sparse_weight=0.0, rerank_top=20, rerank_mode="replace",
                  rerank_pool="final", rerank_norm="minmax", neighbor_window=0, page_expand="none")
X_RERANK_MODEL = "BAAI/bge-reranker-v2-m3-int8"


def build_temporal_retriever(cfg, store, k_cap: int):
    """TemporalRetriever cấu hình X cho `temporal_search`. Cross-encoder chạy cục bộ trừ khi đặt TAM_RERANK_REMOTE_URL (server GPU); ghi lựa chọn đó vào log lần chạy."""
    from tam.retrieval.temporal.retriever import TemporalRetriever
    from tam.retrieval.temporal.rerank import CrossEncoderReranker
    remote = bool(__import__("os").environ.get("TAM_RERANK_REMOTE_URL"))
    logger.info("temporal_search: cấu hình X, cross-encoder %s (%s)", X_RERANK_MODEL, "server GPU từ xa" if remote else "cục bộ")
    reranker = CrossEncoderReranker(X_RERANK_MODEL, cache_dir=cfg.retrieval.get("rerank_cache_dir"), score_cache=None)
    return TemporalRetriever(store, top_k=k_cap, reranker=reranker, **X_SETTINGS)


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
    retriever = build_temporal_retriever(cfg, store, args.k_cap) if args.temporal_search else None
    tools = VectorTools(store, retriever, k_cap=args.k_cap, show_time=not args.hide_time, max_neighbors=args.max_neighbors).tools()
    if args.graph:
        from tam.stores.graph.neo4j_store import Neo4jStore
        from tam.tools.graph_tools import GraphTools

        if args.neo4j_url:
            from neo4j import GraphDatabase
            store = Neo4jStore(GraphDatabase.driver(args.neo4j_url, auth=(cfg.graph_store.user, cfg.graph_store.password)))
        else:
            store = Neo4jStore.from_config(cfg)
        allowed = load_allowed(args.pages_file)
        tools += GraphTools(store, allowed_pages=allowed, show_state=args.show_state, events_cap=args.events_cap, compact=args.compact_timeline, normalize_names=args.normalize_page_names, track_hint=args.track_hint, source_hint=args.source_hint).tools()
    return tools


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default=str(ROOT / "dataset/eval/tune_base_subset.json"), help="bộ con có `cases` (mỗi case: idx, page_id, question_hard, targets, gold_chunk_ids)")
    ap.add_argument("--corpus", default=str(ROOT / "data/text_corpus"))
    ap.add_argument("--events-cap", type=int, default=50, help="trần số mốc mỗi lần gọi timeline (mặc định 50)")
    ap.add_argument("--compact-timeline", action="store_true", help="dòng timeline gọn: bỏ phase/track/kind/tier, chunk id rút còn #n")
    ap.add_argument("--source-hint", action="store_true", help="timeline: mô tả công cụ nói mỗi dòng có chunk nguồn mà read_chunk đọc được")
    ap.add_argument("--track-hint", action="store_true", help="timeline: tiêu đề nêu số sự kiện mỗi track, mô tả công cụ nhắc lọc theo track")
    ap.add_argument("--normalize-page-names", action="store_true", help="timeline: chuẩn hóa tên trang theo luật đặt tên của graph")
    ap.add_argument("--max-neighbors", type=int, default=5, help="trần `neighbors` của read_chunk (mặc định 5)")
    ap.add_argument("--kind", choices=["A", "B", "C"], default="A", help="A = text thuần (grep/read_page); B = kho Qdrant (vector_search/read_chunk); C = B + text (đủ text, vector, và graph nếu thêm --graph)")
    ap.add_argument("--collection", default="", help="kiểu B: tên collection Qdrant; mặc định tam_chunks_dev_<split> theo split của các câu hỏi")
    ap.add_argument("--k-cap", type=int, default=50, help="kiểu B: trần cứng của k trong vector_search")
    ap.add_argument("--graph", action="store_true", help="kiểu B: thêm công cụ graph (timeline, events_of_chunk) trên Neo4j; graph hiện chỉ có 35 trang")
    ap.add_argument("--pages-file", default="", help="file một tên trang (đã chuẩn hóa) mỗi dòng: text và graph chỉ thấy các trang này (cơ chế 3); mặc định không lọc")
    ap.add_argument("--neo4j-url", default="", help="kiểu B --graph: bolt URL thay cho graph_store.url của config (vd bolt://127.0.0.1:7688 cho Neo4j m3)")
    ap.add_argument("--graph-only", action="store_true", help="chỉ giữ công cụ graph (timeline, events_of_chunk) và list_pages (chỉ tên trang): câu trả lời chỉ phụ thuộc nút graph (đo trạng thái cơ chế 3); dùng --cache-dir riêng")
    ap.add_argument("--show-state", action="store_true", help="graph: ẩn sự kiện invalidated_at, ghi (ended ...) cho sự kiện có end_time (cơ chế 3)")
    ap.add_argument("--temporal-search", action="store_true", help="kiểu B/C: thêm công cụ `temporal_search` (nguyên pipeline Cơ chế 1, cấu hình X, cross-encoder bge-v2-m3) cạnh `vector_search`; dùng --cache-dir riêng")
    ap.add_argument("--hide-time", action="store_true", help="kiểu B: ẩn khoảng hiệu lực của chunk khỏi kết quả (agent chỉ dựa vào văn bản)")
    ap.add_argument("--n", type=int, default=1, help="số câu lấy ngẫu nhiên")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--per-type", type=int, default=0, help=">0: lấy ngần này câu mỗi `type` (bộ v9), thay cho --n; --n lớn hơn tổng số câu thì lấy hết")
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
    ap.add_argument("--no-thinking", action="store_true", help="tắt chế độ suy luận (extra_body thinking disabled); cache chuyển sang data/llm_cache/agent_nothink/ nếu --cache-dir để mặc định, vì khóa cache không chứa cờ này")
    ap.add_argument("--no-stream", action="store_true", help="gọi thường, không streaming (mất TTFT và TPOT)")
    ap.add_argument("--log-prompts", choices=["full", "delta", "off"], default="full")
    args = ap.parse_args()

    cfg = load_config()
    run_dir = setup_logging(cfg)
    role = cfg.llm.roles.agent
    session_header = cfg.llm.profiles[role].get("session_header")  # vd OpenCode Go: x-opencode-session
    default_cache = str(ROOT / "data/llm_cache/agent")
    if args.no_thinking:
        prof = cfg.llm.profiles[role]
        prof._data["extra_body"] = {**(prof.get("extra_body") or {}), "thinking": {"type": "disabled"}}
        if args.cache_dir == default_cache:
            args.cache_dir = str(ROOT / "data/llm_cache/agent_nothink")
    if args.kind == "C" and args.cache_dir in (default_cache, str(ROOT / "data/llm_cache/agent_nothink")):
        args.cache_dir += "_C"   # kiểu C có bộ công cụ khác: cache riêng, không trộn với A/B (khóa cache không chứa danh sách công cụ)
    llm = get_llm_for_role(cfg, "agent")
    cases = json.loads(Path(args.subset).read_text(encoding="utf-8"))["cases"]
    rng = random.Random(args.seed)
    if args.per_type:
        by_type: dict[str, list[dict]] = {}
        for c in cases:
            by_type.setdefault(str(c.get("type")), []).append(c)
        picked = [c for t in sorted(by_type) for c in rng.sample(by_type[t], min(args.per_type, len(by_type[t])))]
    else:
        picked = rng.sample(cases, min(args.n, len(cases)))
    corpus = TextCorpus.load(args.corpus)
    if args.pages_file:
        from tam.tools.graph_tools import page_name
        corpus = corpus.restrict(load_allowed(args.pages_file), lambda n: page_name(n, True))
    positions = [int(x) for x in args.pick.split(",") if x.strip()] or list(range(1, len(picked) + 1))
    chosen = [(pos, picked[pos - 1]) for pos in positions]
    profile = cfg.llm.profiles[role]
    cache = None if args.no_cache else SqliteCache(Path(args.cache_dir) / "cache.sqlite", refresh=args.refresh_cache, threadsafe=True)
    if args.kind == "A":
        tools = text_tools(corpus)
    else:
        tools = build_vector_tools(cfg, [c for _, c in chosen], args)
        if args.kind == "C":
            tools = tools + text_tools(corpus)
    if args.graph_only:
        tools = [t for t in tools if t.name in {"timeline", "events_of_chunk", "list_pages"}]
    agent = AgentLoop(llm, tools, load_system_prompt(args.t_now, args.prompt), budget_notice=not args.no_budget_notice, cache=cache,
                      cache_model=str(profile.get("cache_model") or profile.get("model_id") or role), cache_salt=args.repeat_id, max_steps=args.max_steps, max_total_tokens=args.max_tokens,
                      stream=not args.no_stream, model_name=role, log_prompts=args.log_prompts,
                      request_headers=(lambda qid: {session_header: f"{run_dir.name}-{qid}"}) if session_header else None)
    logger.info("Chạy %d câu, role agent=%s, prompt=%s, budget_notice=%s, max_steps=%d, cache=%s (repeat_id=%s), %d trang trong kho text", len(chosen), role,
                args.prompt, not args.no_budget_notice, args.max_steps, "tắt" if cache is None else args.cache_dir, args.repeat_id, len(corpus.pages))

    (run_dir / "run_meta.json").write_text(json.dumps(dict(
        kind=args.kind, graph=args.graph, tools=[t.name for t in tools], thinking="tắt" if args.no_thinking else "theo profile", role=role,
        model=str(profile.get("model_id")), prompt=args.prompt, subset=args.subset, n_cases=len(chosen), workers=args.workers, max_steps=args.max_steps,
        k_cap=args.k_cap, hide_time=args.hide_time, show_state=args.show_state, cache_dir=None if cache is None else args.cache_dir, t_now=args.t_now), ensure_ascii=False, indent=1), encoding="utf-8")

    def run_one(item):
        i, case = item
        run = agent.run(case[args.question_field], query_id=f"q{i:03d}")
        gold_chunks = set(case.get("gold_chunk_ids", []))  # câu v9 (make_v9_graph_subset.py) không có targets chuỗi hay chunk gold: chấm bằng bộ chấm riêng
        first_seen = run.first_step_showing(case.get("targets", []))
        return i, case, run, {"i": i, "idx": case["idx"], "question": case[args.question_field], "targets": case.get("targets", []), "type": case.get("type"), "answer": run.answer,
                              "contains_target": contains(run.answer or "", case["targets"]) if run.answer and case.get("targets") else 0.0, "stop_reason": run.stop_reason,
                              "steps": run.steps, "tool_calls": run.tool_calls, "input_tokens": run.input_tokens, "output_tokens": run.output_tokens,
                              "cached_input_tokens": run.cached_input_tokens, "cache_hits": run.cache_hits, "llm_time_s": round(run.llm_time_s, 3), "retry_wait_s": round(run.retry_wait_s, 3), "attempts": run.attempts, "tool_time_s": round(run.tool_time_s, 3),
                              "wall_s": round(run.wall_s, 3), "ttft_s": [round(t, 3) for t in run.ttft_s],
                              "gold_chunk_listed": bool(gold_chunks & set(run.chunk_ids)),  # chunk gold có trong danh sách trả về (lạc quan: grep chỉ trả đoạn trích)
                              "gold_text_step": first_seen, "saw_gold_text": first_seen is not None,  # lượt đầu tiên văn bản công cụ chứa chuỗi đáp án
                              "gold_chunk_ids": sorted(gold_chunks)}

    rows = []
    t0 = time.perf_counter()
    with (run_dir / "results.jsonl").open("w", encoding="utf-8") as out, (run_dir / "tool_texts.jsonl").open("w", encoding="utf-8") as ttout, ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        for i, case, run, row in pool.map(run_one, chosen):  # pool.map giữ thứ tự đầu vào; các câu vẫn chạy song song
            rows.append(row)
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            out.flush()
            ttout.write(json.dumps({"idx": case["idx"], "tool_texts": run.tool_texts}, ensure_ascii=False) + "\n")  # văn bản công cụ trả về: để chấm "đủ mốc" offline
            ttout.flush()
            print(f"[{i}/{len(picked)}] {run.stop_reason} steps={run.steps} tools={run.tool_calls} tokens={run.input_tokens}/{run.output_tokens} "
                  f"wall={run.wall_s:.1f}s | {case[args.question_field][:80]} -> {(run.answer or '')[:80]!r} (gold {case.get('targets')})")
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
