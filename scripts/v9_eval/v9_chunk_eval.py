"""Cấu hình a (dense thuần) và b (hybrid dense + BM25) trên bộ v9: top-k chunk THÔ đưa cho LLM, một lần gọi, chấm bằng `local/v9_score.py`. Chạy từ gốc repo, python3 -I.

Truy vấn = "tên trang. câu hỏi" (cột `question_hard`), không lọc thời gian. a: nhánh dense top-k. b: dense + BM25 gộp RRF (top_n 50 mỗi nhánh, rrf_k 60), top-k.
LLM trả JSON {kind, number, events[{date,text}]} (cùng khuôn và cùng quy tắc với agent_v5, bỏ phần công cụ), chấm như agent. Mỗi (câu, cấu hình) một lần, qua cache data/llm_cache/chunk_eval/.
DRY=1: chỉ truy xuất, đếm prompt, ước token (4 ký tự = 1 token). Ghi output/<thời điểm>/: results.jsonl (mỗi dòng một cặp câu x cấu hình: điểm, thời gian truy xuất,
thời gian chờ LLM, wall, token vào/ra/cache, cache cục bộ, số lần thử), llm_calls.jsonl (mọi lần gọi, khóa query_id = "<cấu hình>:<qid>"), run.log, retrieved.jsonl (chunk_id đã lấy).
Biến môi trường: VARIANTS (dense,hybrid), K (15), WORKERS (20), LIMIT, SUBSET, THINKING=off (tắt suy luận).
"""
from __future__ import annotations

import datetime
import json
import os
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
from tam.stores.vector.base import VectorFilter  # noqa: E402
from tam.stores.vector.qdrant_store import QdrantStore  # noqa: E402

DRY = os.environ.get("DRY") == "1"
VARS = os.environ.get("VARIANTS", "dense,hybrid").split(",")
K = int(os.environ.get("K", "15"))
NO_THINK = os.environ.get("THINKING") == "off"  # THINKING=off: tắt suy luận; cache riêng chunk_eval_nothink
SUBSET = os.environ.get("SUBSET", str(REPO / "dataset/eval/v9_graph203_subset.json"))
COLLECTION = os.environ.get("COLLECTION", "tam_chunks_dev_tune")  # kho vector của split (tam_chunks_dev_valid cho valid)

SYSTEM = (Path(__file__).resolve().parents[2] / "src" / "tam" / "llm" / "prompts" / "archive" / "answer_m2_chunk.md").read_text(encoding="utf-8")  # nội dung ở file này (prompts/README.md)


class Ev(BaseModel):
    date: str = ""
    text: str = ""


class Ans(BaseModel):
    kind: str = "events"
    number: int | None = None
    events: list[Ev] = Field(default_factory=list)


def retrieve(vec, v, query):
    """Chunk theo thứ hạng: dense (a) hoặc dense + BM25 gộp RRF (b); trả [(chunk_id, text)]."""
    flt = VectorFilter(t_req=datetime.datetime.now(datetime.timezone.utc), exclude_invalidated=False, apply_time=False)
    h = vec.search(query, flt, 50)
    if v == "dense":
        return [(x.chunk.chunk_id, x.chunk.text) for x in h.dense[:K]]
    score, text = defaultdict(float), {}
    for lst in (h.dense, h.sparse):
        for r, x in enumerate(lst):
            score[x.chunk.chunk_id] += 1.0 / (60 + r + 1); text[x.chunk.chunk_id] = x.chunk.text
    return [(c, text[c]) for c, _ in sorted(score.items(), key=lambda t: -t[1])[:K]]

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
    vec = QdrantStore.from_config(cfg, get_embedder(cfg), collection=COLLECTION)
    cases = json.load(open(SUBSET))["cases"][: int(os.environ.get("LIMIT", "100000"))]
    Q = {q["qid"]: q for q in V.load_questions(REPO)}; Eg = {}
    items = []
    for c in cases:
        q = Q[c["idx"]]
        if c["graph_page"] not in Eg:
            Eg[c["graph_page"]] = V.load_gold(REPO, c["graph_page"])
        ids = q["gold_event_ids"] if q["type"] != "first_last_next" else q["answer_ids"]
        gold = {x["chunk_id"] for i in ids for x in Eg[c["graph_page"]][i]["evidence"]}
        for v in VARS:
            t0 = time.perf_counter(); got = retrieve(vec, v, c["question_hard"]); t_ret = time.perf_counter() - t0
            body = "\n\n".join(f"[{i + 1}] {t}" for i, (_, t) in enumerate(got))
            items.append(dict(qid=c["idx"], page=c["graph_page"], v=v, q=q, got=got, retrieval_s=t_ret, gold=gold,
                              human=f"PASSAGES\n{body}\n\nQUESTION\n{q['question']}"))
    n_chars = sum(len(SYSTEM) + len(i["human"]) for i in items)
    print(f"{len(items)} mục, k={K}, đầu vào TB {n_chars // len(items) // 4} token ước ({n_chars // 4:,} token ước tổng)")
    cov = {v: sum(i["gold"] <= {c for c, _ in i["got"]} for i in items if i["v"] == v) / max(1, sum(i["v"] == v for i in items)) for v in VARS}
    print("độ phủ chunk gold:", {v: round(x, 3) for v, x in cov.items()})
    if DRY:
        return

    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured
    out_dir = REPO / "output" / datetime.datetime.now().strftime("%Y%m%d_%H%M%S"); out_dir.mkdir(parents=True)
    os.environ["TAM_LLM_METRICS_FILE"] = str(out_dir / "llm_calls.jsonl")
    prof = "opencode_deepseek_flash"; P0 = cfg.llm.profiles[prof]
    if P0.get("session_header"):
        hd = dict(P0.get("default_headers") or {}); hd[P0["session_header"]] = f"chunk-{int(time.time())}"; P0._data["default_headers"] = hd
    if NO_THINK:
        P0._data["extra_body"] = {**(P0.get("extra_body") or {}), "thinking": {"type": "disabled"}}
    no_think = ((P0.get("extra_body") or {}).get("thinking") or {}).get("type") == "disabled"  # theo cấu hình thực tế của profile
    meta0 = write_meta(out_dir, cfg, prof, dict(collection=COLLECTION, k=K, n_items=len(items), n_questions=len(cases), variants=VARS))
    print("thinking:", meta0["thinking"], "| kho", COLLECTION)
    llm = get_llm(cfg, prof); chain = llm.with_structured_output(Ans)
    cache = SqliteCache(REPO / "data/llm_cache" / ("chunk_eval_nothink" if no_think else "chunk_eval") / "cache.sqlite", threadsafe=True)

    def call(it):
        _query_id.set(f"{it['v']}:{it['qid']}")
        t0 = time.perf_counter()
        out = invoke_structured(llm, chain, Ans, [("system", SYSTEM), ("human", it["human"])], max_attempts=3, cache=cache)
        return it, out, time.perf_counter() - t0
    t_all = time.perf_counter()
    with ThreadPoolExecutor(int(os.environ.get("WORKERS", "20"))) as ex:
        res = list(ex.map(call, items))
    wall_total = time.perf_counter() - t_all

    per = defaultdict(lambda: dict(input_tokens=0, output_tokens=0, cached_input_tokens=0, llm_s=0.0, calls=0, attempts=0, cache_hit=False))
    for line in open(out_dir / "llm_calls.jsonl"):
        r = json.loads(line); d = per[r["query_id"]]
        if r["kind"] == "llm_call":
            d["input_tokens"] += r.get("input_tokens") or 0; d["output_tokens"] += r.get("output_tokens") or 0
            d["cached_input_tokens"] += r.get("cached_input_tokens") or 0; d["llm_s"] += r.get("e2e_s") or 0; d["calls"] += 1
        elif r["kind"] == "invoke":
            d["attempts"] = r.get("attempts", 0); d["cache_hit"] = bool(r.get("cache_hit"))

    rows = []
    with open(out_dir / "retrieved.jsonl", "w") as fr:
        for it, out, wall in res:
            q = it["q"]; exp = V.expected(q, Eg[it["page"]])
            ans = None if out is None else ({"kind": out.kind, "number": out.number, "events": [e.model_dump() for e in out.events]})
            pred = None if ans is None else (ans["number"] if q["type"] == "order_gap" else ans["events"])  # cùng cách lấy đáp án như v9_agent_score.py
            s = V.score(exp, pred)
            m = per[f"{it['v']}:{it['qid']}"]; got = {c for c, _ in it["got"]}
            rows.append(dict(qid=it["qid"], v=it["v"], type=q["type"], k=K, fail=out is None, gold_covered=it["gold"] <= got, n_gold_chunks=len(it["gold"]),
                             gold_chunks_hit=len(it["gold"] & got), retrieval_s=round(it["retrieval_s"], 3), llm_s=round(m["llm_s"], 3), wall_s=round(wall, 3),
                             input_tokens=m["input_tokens"], output_tokens=m["output_tokens"], cached_input_tokens=m["cached_input_tokens"],
                             local_cache_hit=m["cache_hit"], llm_calls=m["calls"], attempts=m["attempts"], answer=ans, **s))
            fr.write(json.dumps(dict(qid=it["qid"], v=it["v"], chunks=[c for c, _ in it["got"]]), ensure_ascii=False) + "\n")
    (out_dir / "system_prompt.txt").write_text(SYSTEM, encoding="utf-8")
    with open(out_dir / "prompts.jsonl", "w") as fp:  # prompt người dùng + đáp án thô của từng (cấu hình, câu); system prompt ở system_prompt.txt
        for it, out, _ in res:
            fp.write(json.dumps(dict(qid=it["qid"], v=it["v"], human=it["human"], answer=None if out is None else out.model_dump()), ensure_ascii=False) + "\n")
    with open(out_dir / "results.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\ncache cục bộ: hit {cache.hits} miss {cache.misses}; tổng thời gian chạy {wall_total:.0f}s ({os.environ.get('WORKERS', '20')} luồng)\n== {out_dir.name} ==")
    print(f"{'cấu hình':8s} {'loại':16s} {'câu':>4s} {'exact':>6s} {'F1':>6s} {'phủ gold':>8s} {'tok vào':>8s} {'tok ra':>7s} {'cache':>7s} {'llm_s':>6s} {'hỏng':>5s}")
    for v in VARS:
        for t in ("ALL", "list", "summary", "first_last_next", "order_gap"):
            r = [x for x in rows if x["v"] == v and (t == "ALL" or x["type"] == t)]
            if not r:
                continue
            f1 = [x["f1"] for x in r if "f1" in x]; n = len(r)
            print(f"{v:8s} {t:16s} {n:4d} {sum(x['exact'] for x in r) / n:6.3f} {(sum(f1) / len(f1) if f1 else float('nan')):6.3f} {sum(x['gold_covered'] for x in r) / n:8.3f} "
                  f"{sum(x['input_tokens'] for x in r) / n:8.0f} {sum(x['output_tokens'] for x in r) / n:7.0f} {sum(x['cached_input_tokens'] for x in r) / n:7.0f} "
                  f"{sum(x['llm_s'] for x in r) / n:6.1f} {sum(x['fail'] for x in r):5d}")


if __name__ == "__main__":
    main()
