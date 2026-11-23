"""Cơ chế 3: cấu hình cố định (không agent) đọc câu hỏi mech3. Một lượt LLM mỗi (câu, biến thể).

Truy xuất giống v9_fixed_eval (TimelineRetriever: vector chọn trang/chunk vào -> timeline graph), LLM chỉ thấy dòng timeline lấy từ graph
(không có văn bản chunk), trả lời văn bản ngắn; chấm bằng scripts/m3_mech3_score.py (luật, không gọi LLM).
Biến thể (nhãn theo docs/planning/02 mục 14): vec = d, graph = f, graph_tb = f', graph_tt = f''.

Biến môi trường: SUBSET (subset_mech3.json), NEO4J_URL, COLLECTION (mặc định tam_chunks_dev_tune), VARIANTS (mặc định cả bốn), STATE_FILTER=1,
ALLOWED_PAGES_FILE (pages.txt), WORKERS (mặc định 3), LIMIT, THINKING=off (bắt buộc cho lần chạy chính thức), CACHE_DIR (mặc định
data/llm_cache/m3_fixed_mech3_nothink), DRY=1 (chỉ truy xuất, không gọi LLM).
Ghi output/<thời điểm>/: results.jsonl (idx, v, answer, ...), prompts.jsonl (prompt đầy đủ), llm_calls.jsonl (số đo LLM), run_meta.json.
"""
from __future__ import annotations

import datetime
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(REPO / "scripts" / "v9_eval"))
from pydantic import BaseModel  # noqa: E402
import v9_fixed_eval as F  # noqa: E402  (module-level chỉ đọc biến môi trường)
from tam.config.logging import _query_id  # noqa: E402
from tam.config.loader import load_config  # noqa: E402
from tam.embedding.factory import get_embedder  # noqa: E402
from tam.retrieval.timeline.retriever import TimelineRetriever  # noqa: E402
from tam.stores.graph.neo4j_store import Neo4jStore  # noqa: E402
from tam.stores.vector.qdrant_store import QdrantStore  # noqa: E402

SUBSET = os.environ.get("SUBSET", str(REPO / "dataset/organized" / os.environ.get("M3_STATE_NAME", "m3_state") / os.environ.get("M3_SET", "tune") / "subset_mech3.json"))
F.SUBSET = SUBSET
VARS = os.environ.get("VARIANTS", "vec,graph,graph_tb,graph_tt").split(",")
T_NOW = "2026-11-03"
SYSTEM = f"""You answer a question about one subject using ONLY a dated timeline. Each line is "[id] date | text". Today's date is {T_NOW}.
A line that ends with "(ended <date>)" describes a state that ended on that date: it was true before then and is no longer true today.
Answer in plain text. For a yes/no question start with "Yes" or "No", then give the reason in one sentence with the correct detail.
For any other question give the value (a year, a name) in one sentence. Use only the timeline; if it does not contain enough to answer, answer "UNKNOWN"."""


class Ans(BaseModel):
    answer: str


def main():
    cfg = load_config()
    vec = QdrantStore.from_config(cfg, get_embedder(cfg), collection=os.environ.get("COLLECTION", f"tam_chunks_dev_{os.environ.get('M3_SET', 'tune')}"))
    gr = Neo4jStore.from_config(cfg) if not os.environ.get("NEO4J_URL") else Neo4jStore(__import__("neo4j").GraphDatabase.driver(os.environ["NEO4J_URL"], auth=(cfg.graph_store.user, cfg.graph_store.password)))
    allowed = None
    if os.environ.get("ALLOWED_PAGES_FILE"):
        from tam.tools.graph_tools import page_name
        allowed = {page_name(l, True) for l in open(os.environ["ALLOWED_PAGES_FILE"], encoding="utf-8").read().splitlines() if l.strip()}
    R = TimelineRetriever(vec, gr, state_filter=os.environ.get("STATE_FILTER") == "1", allowed_pages=allowed)
    cases = json.load(open(SUBSET, encoding="utf-8"))["cases"][: int(os.environ.get("LIMIT", "100000"))]
    items = []
    for c in cases:
        for v in VARS:
            t0 = time.perf_counter(); o = F.retrieve(R, v, c["question"], c["question"]); t_ret = time.perf_counter() - t0
            ev = sorted(o["events"], key=lambda e: (e["date"], e["phase"]))
            tl = "\n".join(f"[{i + 1}] {e['date']} | {e['text']}" for i, e in enumerate(ev))
            items.append(dict(idx=c["idx"], v=v, edit_id=c.get("edit_id"), page=o["page"], page_ok=o["page"] == c["graph_page"], n_ev=len(ev), retrieval_s=round(t_ret, 3),
                              human=f"TIMELINE\n{tl}\n\nQUESTION\n{c['question']}"))
    uniq = len({SYSTEM + i["human"] for i in items})
    print(f"{len(cases)} câu x {len(VARS)} biến thể = {len(items)} mục, {uniq} prompt khác nhau (số lần gọi LLM tối đa); trang đúng {sum(i['page_ok'] for i in items)}/{len(items)}")
    if os.environ.get("DRY") == "1":
        gr.close(); return

    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured
    out_dir = REPO / "output" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out_dir.mkdir(parents=True)
    os.environ["TAM_LLM_METRICS_FILE"] = str(out_dir / "llm_calls.jsonl")
    prof = "opencode_deepseek_flash"; P0 = cfg.llm.profiles[prof]
    if P0.get("session_header"):
        hd = dict(P0.get("default_headers") or {}); hd[P0["session_header"]] = f"m3fixed-{int(time.time())}"; P0._data["default_headers"] = hd
    if os.environ.get("THINKING") == "off":
        P0._data["extra_body"] = {**(P0.get("extra_body") or {}), "thinking": {"type": "disabled"}}
    no_think = ((P0.get("extra_body") or {}).get("thinking") or {}).get("type") == "disabled"
    if not no_think:
        raise SystemExit("thinking đang bật: đặt THINKING=off (quy tắc dự án: mọi lần chạy thinking tắt, cache riêng)")
    meta = F.write_meta(out_dir, cfg, prof, dict(kind="m3_fixed_mech3", collection=os.environ.get("COLLECTION", f"tam_chunks_dev_{os.environ.get('M3_SET', 'tune')}"), n_items=len(items), variants=VARS))
    print("thinking:", meta["thinking"], "| neo4j:", os.environ.get("NEO4J_URL", "mặc định"), "| lọc trạng thái:", os.environ.get("STATE_FILTER") == "1")
    (out_dir / "system_prompt.txt").write_text(SYSTEM, encoding="utf-8")
    with open(out_dir / "prompts.jsonl", "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(dict(idx=it["idx"], v=it["v"], human=it["human"]), ensure_ascii=False) + "\n")
    llm = get_llm(cfg, prof); chain = llm.with_structured_output(Ans)
    cache = SqliteCache(Path(os.environ.get("CACHE_DIR", REPO / "data/llm_cache/m3_fixed_mech3_nothink")) / "cache.sqlite", threadsafe=True)

    def call(it):
        _query_id.set(f"{it['v']}:{it['idx']}")
        t0 = time.perf_counter()
        out = invoke_structured(llm, chain, Ans, [("system", SYSTEM), ("human", it["human"])], max_attempts=3, cache=cache)
        return it, (out.answer if out else None), time.perf_counter() - t0
    t_all = time.perf_counter()
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "3"))) as ex:
        res = list(ex.map(call, items))
    print("cache: hit", cache.hits, "miss", cache.misses, f"; tổng thời gian {time.perf_counter() - t_all:.0f}s")
    with open(out_dir / "results.jsonl", "w", encoding="utf-8") as f:
        for it, ans, w in res:
            f.write(json.dumps(dict(idx=it["idx"], v=it["v"], edit_id=it["edit_id"], page=it["page"], page_ok=it["page_ok"], n_ev=it["n_ev"], retrieval_s=it["retrieval_s"], answer=ans, fail=ans is None, wall_s=round(w, 3)), ensure_ascii=False) + "\n")
    print("Log:", out_dir)
    gr.close()


if __name__ == "__main__":
    main()
