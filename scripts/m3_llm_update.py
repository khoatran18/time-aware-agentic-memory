"""Cơ chế 3, hệ "LLM quyết định": một lượt LLM mỗi chỗ sửa (prompt trong m3_update_prompt.py), mã kiểm, rồi áp lên nút cũ.

  run --edits tune-102,tune-037  GỌI LLM (opencode_deepseek_flash, thinking tắt, cache data/llm_cache/m3_update_nothink); ghi
      m3_state/<tập>/mech3/{raw,nodes}/...; in quyết định để đọc tay.
Áp dụng (mức nút, không dựng lại mốc thô): edit = đổi trường + tính lại node_id; close = đặt end_time; invalidate = đặt invalidated_at;
add = mốc mới -> to_nodes, bỏ nếu trùng node_id. Chưa làm trong bản thử: gộp cặp bằng LLM giữa mốc `add` và nút cũ (bước 3 đầy đủ).
Nút đóng/vô hiệu mang thuộc tính end_time / invalidated_at; kho Neo4j và công cụ agent hiện CHƯA đọc hai thuộc tính này.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m3_build_old as b  # noqa: E402
import m3_update_prompt as up  # noqa: E402

ROOT, ORG, M3 = b.ROOT, b.ORG, b.M3
nd = b.nd


def system_dir(S: str) -> Path:
    return ORG / M3 / S / "mech3"


def make_caller(S: str):
    from tam.config.loader import load_config
    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured

    os.environ["TAM_LLM_METRICS_FILE"] = str(ROOT / "local" / "m3" / f"llm_calls_mech3_{S}{'' if os.environ.get('M3_STATE_NAME', 'm3_state') == 'm3_state' else '_' + os.environ['M3_STATE_NAME']}.jsonl")
    cfg = load_config()
    prof = "opencode_deepseek_flash"
    P = cfg.llm.profiles[prof]
    if P.get("session_header"):
        import time
        hd = dict(P.get("default_headers") or {})
        hd[P["session_header"]] = f"m3-update-{int(time.time())}"
        P._data["default_headers"] = hd
    llm = get_llm(cfg, prof)
    chain = llm.with_structured_output(up.Update)
    cache = SqliteCache(ROOT / "data" / "llm_cache" / "m3_update_nothink" / "cache.sqlite", threadsafe=True)

    def call(system: str, human: str):
        return invoke_structured(llm, chain, up.Update, [("system", system), ("human", human)], max_attempts=3, cache=cache)

    call.cache = cache
    return call


def apply(page: str, c: dict, old_nodes: list[dict], idmap: dict, ok_c: list, ok_a: list) -> tuple[list[dict], list[str]]:
    nodes = [dict(n) for n in old_nodes]
    byid = {n["node_id"]: n for n in nodes}
    log = []
    for ch in ok_c:
        n = byid[idmap[ch.node]]
        if ch.op == "close":
            n["end_time"] = ch.end_date
        elif ch.op == "invalidate":
            n["invalidated_at"] = "revision"
        log.append(f"{ch.op} {ch.node}")
    have = {n["node_id"] for n in nodes}
    for ev in ok_a:
        raw = dict(ev.model_dump(), cid=c["chunk_id"], section=c["window"]["section"], flags=[])
        for n in nd.to_nodes(page, [raw]):
            if n["node_id"] in have:
                log.append(f"add TRÙNG {n['node_id']}")
            else:
                n["_added"] = True
                nodes.append(n)
                have.add(n["node_id"])
                log.append(f"add {n['date']} {n['text'][:60]}")
    return nodes, log


def dedup_adds(page: str, nodes: list[dict], judge) -> tuple[list[dict], dict]:
    """Bước 3 đầy đủ cho cơ chế 3: cặp (mốc `add`, nút cũ chưa vô hiệu) qua cổng như organize_data, phán quyết bằng PAIR_PROMPT (judge); `same` -> bỏ mốc `add`,
    hợp chunk nguồn vào nút cũ. Chỉ xét cặp có ít nhất một mốc `add` (cặp cũ-cũ đã có phán quyết lúc ingest)."""
    live = [n for n in nodes if not n.get("invalidated_at")]
    ev = [dict(n, section=0 if n.get("is_lead") else 1, cid=n["cids"][0]) for n in live]
    pairs = [(i, j) for i, j in b.gated_pairs(ev) if live[i].get("_added") or live[j].get("_added")]
    verdicts = judge(page, ev, pairs) if pairs and judge is not None else []
    drop, st = set(), {"pairs": len(pairs), "same": 0}
    for (i, j), v in zip(pairs, verdicts):
        if v != "same":
            continue
        a, c = (i, j) if live[i].get("_added") else (j, i)
        if live[c].get("_added") and not live[a].get("_added"):
            a, c = c, a
        if live[a].get("_added") and a not in drop and (not live[c].get("_added") or c not in drop):
            live[c]["cids"] = sorted(set(live[c]["cids"]) | set(live[a]["cids"]))
            drop.add(a)
            st["same"] += 1
    gone = {live[k]["node_id"] for k in drop}
    out = [n for n in nodes if n["node_id"] not in gone or not n.get("_added")]
    for n in out:
        n.pop("_added", None)
    return out, st


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["run", "load"])
    ap.add_argument("--neo4j-url", default="bolt://127.0.0.1:7688")
    ap.add_argument("--edits", default="all", help="edit_id cách nhau dấu phẩy, hoặc all")
    ap.add_argument("--set", default="tune")
    ap.add_argument("--dedup", action="store_true", help="bước 3 đầy đủ: gộp cặp bằng LLM giữa mốc add và nút cũ (cache m3_pair_nothink)")
    a = ap.parse_args()
    S = a.set
    P = b.load_pilot(S)["edits"]
    sel = P if a.edits == "all" else [c for c in P if c["edit_id"] in a.edits.split(",")]
    sd = system_dir(S)
    if a.step == "load":
        assert ":7687" not in a.neo4j_url
        from neo4j import GraphDatabase

        from tam.config.loader import load_config
        from tam.stores.graph.neo4j_store import Neo4jStore

        g = load_config().graph_store
        store = Neo4jStore(GraphDatabase.driver(a.neo4j_url, auth=(g.user, g.password)))
        store.ensure_schema()
        n = sum(store.upsert_page(c["page"], json.loads((sd / "nodes" / f"{c['page']}.json").read_text(encoding="utf-8"))) for c in P)
        print("đã nạp", n, "nút vào", a.neo4j_url, "| đếm:", store.count())
        store.close()
        return
    for sub in ("raw", "nodes"):
        (sd / sub).mkdir(parents=True, exist_ok=True)
    (ROOT / "local" / "m3").mkdir(parents=True, exist_ok=True)
    call = make_caller(S)
    judge = b.make_judge(S, tag="mech3_pairs") if a.dedup else None
    for c in sel:
        system, human, idmap = up.build(S, c)
        r = call(system, human)
        page = c["page"]
        new_chunk = dict(up.chunk_blocks(ORG / "source" / S / "chunks" / f"{page}.txt"))[c["chunk_id"]]
        page_text = (ORG / "source" / S / "chunks" / f"{page}.txt").read_text(encoding="utf-8")
        print(f"\n=== {c['edit_id']} {c['type']} {page} | nút đưa vào {len(idmap)} | LLM {'ok' if r else 'FAIL'}")
        if r is None:
            continue
        (sd / "raw" / f"{c['edit_id']}.json").write_text(json.dumps({"idmap": idmap, "output": r.model_dump()}, ensure_ascii=False, indent=1), encoding="utf-8")
        ok_c, ok_a, rej = up.validate(r, new_chunk, page_text, idmap)
        old = json.loads((ORG / M3 / S / "old" / "nodes" / f"{page}.json").read_text(encoding="utf-8"))
        nodes, log = apply(page, c, old, idmap, ok_c, ok_a)
        if a.dedup:
            nodes, st = dedup_adds(page, nodes, judge)
            log.append(f"gộp cặp: {st}")
        else:
            for n in nodes:
                n.pop("_added", None)
        (sd / "nodes" / f"{page}.json").write_text(json.dumps(nodes, ensure_ascii=False), encoding="utf-8")
        byid = {n["node_id"]: n for n in old}
        for ch in r.changes:
            n = byid.get(idmap.get(ch.node, ""), {})
            print(f"  {ch.op:<10}{ch.node} [{n.get('date')}] {str(n.get('text'))[:70]} | end={ch.end_date} | ev: {ch.evidence[:80]}")
        for ev in r.add:
            print(f"  add       [{ev.date}] {ev.phase} {ev.track}: {ev.text[:80]} | ev: {ev.evidence[:60]}")
        for x, why in rej:
            print("  BỊ LOẠI:", why, "|", str(x)[:120])
        print("  áp dụng:", log or "(không đổi)")
    print("\ncache hit", call.cache.hits, "miss", call.cache.misses)


if __name__ == "__main__":
    main()
