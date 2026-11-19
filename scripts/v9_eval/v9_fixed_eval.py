"""Phương pháp cố định (không agent) trên bộ câu hỏi v9, chấm bằng `local/v9_score.py` (cùng thước đo với agent). Chạy từ gốc repo, python3 -I.

Khung: truy vấn = "tên trang. câu hỏi" (cột `question_hard` của subset) -> bộ truy xuất cho danh sách sự kiện -> LLM đọc (prompt của local/ingest_eval/reader.py)
chọn `selected_ids` -> đổi id thành [{date, text}] (order_gap: |năm sau - năm trước| của hai mốc đầu) -> `v9_score.score` so với gold `rev/<Trang>.json`.
Cấu hình (VARIANTS, cách nhau dấu phẩy): vec = sự kiện của chunk top-k (không đi ô); graph = chunk -> nút -> đi ô, tối đa 40 nút;
graph_tb = graph + cửa sổ thời gian từ câu hỏi, cắt theo thùng; graph_tt = graph + cửa sổ + lọc theo track.
Chế độ:
  DRY=1  chỉ truy xuất, KHÔNG gọi LLM: đếm prompt, và chấm "người đọc hoàn hảo" (chọn đúng các nút khớp gold trong danh sách đưa vào) = trần của truy xuất.
  (không DRY) gọi LLM, mỗi (câu, cấu hình) một lần, qua cache data/llm_cache/reader/ (cùng prompt với graph_eval.py nên trúng cache nếu đã chạy); ghi output/<thời điểm>/.
Biến môi trường: SUBSET (mặc định dataset/eval/v9_graph203_subset.json), VARIANTS, WORKERS (20), LIMIT (chỉ n câu đầu, để thử nhanh).
Ví dụ: DRY=1 python3 -I local/v9_fixed_eval.py
"""
from __future__ import annotations

import datetime
import json
import os
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src")); sys.path.insert(0, str(Path(__file__).parent))
import v9_score as V  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from tam.config.logging import _query_id  # noqa: E402
from tam.config.loader import load_config  # noqa: E402
from tam.embedding.factory import get_embedder  # noqa: E402
from tam.ingestion.events import post as ip  # noqa: E402
from tam.retrieval.timeline.retriever import TimelineRetriever  # noqa: E402
from tam.retrieval.timeline.window import parse_window  # noqa: E402
from tam.stores.graph.neo4j_store import Neo4jStore  # noqa: E402
from tam.stores.vector.qdrant_store import QdrantStore  # noqa: E402

DRY = os.environ.get("DRY") == "1"
VARS = os.environ.get("VARIANTS", "vec,graph,graph_tb,graph_tt").split(",")
SUBSET = os.environ.get("SUBSET", str(REPO / "dataset/eval/v9_graph203_subset.json"))
COLLECTION = os.environ.get("COLLECTION", "tam_chunks_dev_tune")  # kho vector của split (tam_chunks_dev_valid cho valid)
NODES_FILE = os.environ.get("NODES_FILE", str(REPO / "local/ingest_eval/judge_out/graph_nodes.json"))  # danh sách nút graph của các trang (graph_nodes_V.json cho valid)
# Prompt của local/ingest_eval/reader.py (sao nguyên văn tại 2026-11-15 để tái hiện được dù file đó đổi; đổi chữ nào là đổi khóa cache).
SYSTEM = """You answer a question about one subject using ONLY a dated timeline. Each line is "[id] date | text".
Return in `selected_ids` the ids of the timeline events that answer the question:
- a question asking to list or summarize: every event needed, in chronological order;
- a question asking which event came first, last or next: that single event (or all events sharing the same date if the question allows it);
- a question asking how many years (or months, days) passed between two events: the two events, in order.
Use only ids that appear in the timeline. Do not invent events. Answer only with the schema."""


class Ans(BaseModel):
    selected_ids: list[str] = Field(default_factory=list)


def retrieve(R, v, query, question):
    if v == "vec":
        return R.chunk_events(query)
    if v == "graph":
        return R.graph_timeline(query)
    if v == "graph_tb":
        return R.graph_timeline(query, window=parse_window(question), cut="bins")
    if v == "graph_tt":
        return R.graph_timeline(query, window=parse_window(question), question=question, track_mode="filter")
    raise SystemExit(f"cấu hình lạ: {v}")


def to_answer(q, sel, ev):
    """selected_ids -> câu trả lời theo khuôn của v9_score: số (order_gap) hoặc danh sách {date, text}."""
    sel = [x for x in sel if x in ev]
    if q["type"] == "order_gap":
        if len(sel) < 2:
            return None
        a, b = V.parse_date(ev[sel[0]]["date"]), V.parse_date(ev[sel[1]]["date"])
        return abs(a[0] - b[0]) if a and b else None
    return [{"date": ev[x]["date"], "text": ev[x]["text"]} for x in sel]


def match_nodes(E, gid, ev):
    """Nút trong danh sách đưa vào khớp mốc gold `gid` nhất (cùng luật độ phủ của v9_agent_score.coverage), hoặc None."""
    g = E[gid]; gc = {x["chunk_id"] for x in g["evidence"]}; best = None
    for nid, e in ev.items():
        if not ip.compat(g["date"], e["date"]):
            continue
        sim = ip.jacc_u(g["text"], e["text"]); share = bool(gc & set(e.get("cids", [])))
        if (share and sim >= 0.05) or sim >= 0.15:
            if best is None or sim > best[0]:
                best = (sim, nid)
    return best[1] if best else None


def perfect_selection(q, E, ev):
    ids = q["gold_event_ids"] if q["type"] == "order_gap" else (q["answer_ids"] if q["type"] == "first_last_next" else q["gold_event_ids"])
    sel = [match_nodes(E, i, ev) for i in ids]
    return [s for s in sel if s]

def write_meta(out_dir, cfg, prof, extra):
    """run_meta.json: điều kiện chạy (thinking thực tế của profile, mô hình, kho, bộ câu hỏi, luồng, phiên bản mã) để tái hiện và để không lẫn chế độ khi so số liệu."""
    import subprocess
    P = cfg.llm.profiles[prof]; eb = P.get("extra_body") or {}
    try:
        rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
    except Exception:
        rev = ""
    meta = dict(started=datetime.datetime.now().isoformat(timespec="seconds"), profile=prof, model_id=P.get("model_id"), extra_body=eb, thinking="off" if (eb.get("thinking") or {}).get("type") == "disabled" else "on",
                git_rev=rev, subset=SUBSET, workers=int(os.environ.get("WORKERS", "20")), env={k: os.environ[k] for k in ("VARIANTS", "K", "LIMIT", "COLLECTION", "NODES_FILE", "THINKING", "CACHE_DIR") if k in os.environ}, **extra)
    (out_dir / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=lambda o: getattr(o, "_data", str(o))), encoding="utf-8")
    return meta


def main():
    cfg = load_config()
    vec = QdrantStore.from_config(cfg, get_embedder(cfg), collection=COLLECTION); gr = Neo4jStore.from_config(cfg)
    R = TimelineRetriever(vec, gr)
    NODES = json.load(open(NODES_FILE))
    cases = json.load(open(SUBSET))["cases"][: int(os.environ.get("LIMIT", "100000"))]
    Q = {q["qid"]: q for q in V.load_questions(REPO)}; Egold = {}
    items = []
    for c in cases:
        q = Q[c["idx"]]; page = c["graph_page"]
        if page not in Egold:
            Egold[page] = V.load_gold(REPO, page)
        ids = {x["node_id"] for x in NODES[page]}
        for v in VARS:
            t0 = time.perf_counter(); o = retrieve(R, v, c["question_hard"], q["question"]); t_ret = time.perf_counter() - t0
            ev = {e["node_id"]: e for e in sorted(o["events"], key=lambda e: (e["date"], e["phase"])) if e["node_id"] in ids}
            tl = "\n".join(f"[{n}] {e['date']} | {e['text']}" for n, e in ev.items())
            items.append(dict(qid=c["idx"], page=page, v=v, q=q, ev=ev, retrieval_s=t_ret, page_ok=o["page"] == page, human=f"TIMELINE\n{tl}\n\nQUESTION\n{q['question']}"))
    uniq = len({SYSTEM + i["human"] for i in items})
    print(f"{len(items)} mục, {uniq} prompt khác nhau (số lần gọi LLM tối đa)")

    if DRY:
        sels = {(i["qid"], i["v"]): perfect_selection(i["q"], Egold[i["page"]], i["ev"]) for i in items}
        report(items, Egold, sels, "TRẦN TRUY XUẤT (người đọc hoàn hảo, không gọi LLM)")
        gr.close(); return

    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured
    out_dir = REPO / "output" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out_dir.mkdir(parents=True)
    os.environ["TAM_LLM_METRICS_FILE"] = str(out_dir / "llm_calls.jsonl")
    prof = "opencode_deepseek_flash"; P0 = cfg.llm.profiles[prof]
    if P0.get("session_header"):
        hd = dict(P0.get("default_headers") or {}); hd[P0["session_header"]] = f"fixed-{int(time.time())}"; P0._data["default_headers"] = hd
    if os.environ.get("THINKING") == "off":  # THINKING=off: tắt suy luận (extra_body thinking disabled)
        P0._data["extra_body"] = {**(P0.get("extra_body") or {}), "thinking": {"type": "disabled"}}
    no_think = ((P0.get("extra_body") or {}).get("thinking") or {}).get("type") == "disabled"  # theo cấu hình thực tế của profile; cache riêng reader_nothink
    meta0 = write_meta(out_dir, cfg, prof, dict(collection=COLLECTION, nodes_file=NODES_FILE, n_items=len(items), n_questions=len(cases), variants=VARS))
    print("thinking:", meta0["thinking"], "| kho", COLLECTION, "| nút", NODES_FILE)
    llm = get_llm(cfg, prof); chain = llm.with_structured_output(Ans)
    cache = SqliteCache(Path(os.environ.get("CACHE_DIR", REPO / "data/llm_cache" / ("reader_nothink" if no_think else "reader"))) / "cache.sqlite", threadsafe=True)

    def call(it):
        _query_id.set(f"{it['v']}:{it['qid']}")  # để gom số đo LLM theo từng (cấu hình, câu)
        t0 = time.perf_counter()
        out = invoke_structured(llm, chain, Ans, [("system", SYSTEM), ("human", it["human"])], max_attempts=3, cache=cache)
        return (it["qid"], it["v"]), (out.selected_ids if out else None), time.perf_counter() - t0
    t_all = time.perf_counter()
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "20"))) as ex:
        res = list(ex.map(call, items))
    sels = {k: sel for k, sel, _ in res}; walls = {k: w for k, _, w in res}
    print("cache: hit", cache.hits, "miss", cache.misses, f"; tổng thời gian chạy {time.perf_counter() - t_all:.0f}s")
    per = defaultdict(lambda: dict(input_tokens=0, output_tokens=0, cached_input_tokens=0, llm_s=0.0, llm_calls=0, attempts=0, local_cache_hit=False))
    for line in open(out_dir / "llm_calls.jsonl"):
        r = json.loads(line); d = per[r["query_id"]]
        if r["kind"] == "llm_call":
            d["input_tokens"] += r.get("input_tokens") or 0; d["output_tokens"] += r.get("output_tokens") or 0
            d["cached_input_tokens"] += r.get("cached_input_tokens") or 0; d["llm_s"] += r.get("e2e_s") or 0; d["llm_calls"] += 1
        elif r["kind"] == "invoke":
            d["attempts"] = r.get("attempts", 0); d["local_cache_hit"] = bool(r.get("cache_hit"))
    meta = {k: dict(per[f"{k[1]}:{k[0]}"], wall_s=round(walls[k], 3)) for k in sels}
    (out_dir / "system_prompt.txt").write_text(SYSTEM, encoding="utf-8")
    with open(out_dir / "prompts.jsonl", "w") as fp:  # prompt người dùng đưa cho LLM + đáp án thô (id đã chọn) của từng (cấu hình, câu); system prompt ở system_prompt.txt
        for it in items:
            fp.write(json.dumps(dict(qid=it["qid"], v=it["v"], human=it["human"], node_ids=list(it["ev"]), selected_ids=sels[(it["qid"], it["v"])]), ensure_ascii=False) + "\n")
    report(items, Egold, sels, f"LLM đọc ({out_dir.name})", out_dir, meta)
    gr.close()


def report(items, Egold, sels, title, out_dir=None, meta=None):
    rows = []
    for it in items:
        sel = sels[(it["qid"], it["v"])]; q = it["q"]; exp = V.expected(q, Egold[it["page"]])
        ids = q["gold_event_ids"] if q["type"] == "order_gap" else (q["answer_ids"] if q["type"] == "first_last_next" else q["gold_event_ids"])
        full = all(match_nodes(Egold[it["page"]], i, it["ev"]) for i in ids)  # danh sách đưa vào có đủ mốc gold
        s = V.score(exp, None if sel is None else to_answer(q, sel, it["ev"]))
        rows.append(dict(qid=it["qid"], v=it["v"], type=q["type"], page_ok=it["page_ok"], n_ev=len(it["ev"]), chars=len(it["human"]), fail=sel is None, avail=full, selected=sel, retrieval_s=round(it["retrieval_s"], 3), **(meta or {}).get((it["qid"], it["v"]), {}), **s))
    if out_dir:
        with open(out_dir / "results.jsonl", "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n== {title} ==")
    print(f"{'cấu hình':9s} {'loại':16s} {'câu':>4s} {'exact':>6s} {'F1':>6s} {'trang đúng':>10s} {'đủ mốc':>7s} {'nút TB':>7s} {'token TB':>8s} {'hỏng':>5s}")
    for v in VARS:
        for t in ("ALL", "list", "summary", "first_last_next", "order_gap"):
            r = [x for x in rows if x["v"] == v and (t == "ALL" or x["type"] == t)]
            if not r:
                continue
            f1 = [x["f1"] for x in r if "f1" in x]
            print(f"{v:9s} {t:16s} {len(r):4d} {sum(x['exact'] for x in r) / len(r):6.3f} {(sum(f1) / len(f1) if f1 else float('nan')):6.3f} {sum(x['page_ok'] for x in r):10d} "
                  f"{sum(x['avail'] for x in r):7d} {sum(x['n_ev'] for x in r) / len(r):7.1f} {sum(x['chars'] for x in r) / len(r) / 4:8.0f} {sum(x['fail'] for x in r):5d}")


if __name__ == "__main__":
    main()
