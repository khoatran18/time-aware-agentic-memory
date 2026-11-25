"""Cơ chế 3, pilot: dựng trạng thái graph CŨ cho các trang đã chọn (`m3_select_pilot.py` -> m3_state/<tập>/pilot.json).

Các bước (mặc định chỉ `plan`, KHÔNG gọi LLM, KHÔNG ghi kho):
  inputs   ghi văn bản trang bản cũ (chunk sửa thay bằng bản `@past`) vào m3_state/<tập>/old_in/batch0/in/<trang>.txt
  plan     DRY: đếm số lượt LLM cần (trích cửa sổ cũ + gộp cặp), in tóm tắt; không gọi LLM
  selftest không LLM: thay mốc cửa sổ bằng chính mốc `real`, chạy gộp cấp trang, so với nút `real` đã lưu (kiểm đường ống)
  extract  GỌI LLM: trích đúng một cửa sổ mỗi trang (prompt 10b nguyên bản, opencode_deepseek_flash, thinking tắt, cache `m3_ingest_nothink`)
  finish   (cần extract) thay mốc cửa sổ, gộp cặp (verdict cũ theo nội dung; cặp mới gọi LLM, cache `m3_pair_nothink`), ghi nút cũ

Prompt trích và bước lọc lấy NGUYÊN từ dataset/eval/timeline_pilot/outline_trial/pass3_p10b_oc.py (exec bản vá chỉ lọc cửa sổ, file gốc không đổi).
Ghi: dataset/organized/m3_state/<tập>/old/{ingest_10b,nodes}/<trang>.json
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ORG = ROOT / "dataset" / "organized"
M3 = os.environ.get("M3_STATE_NAME", "m3_state")  # thư mục trạng thái (mặc định m3_state; m3_state_ext cho đợt mở rộng)
OT = ROOT / "dataset" / "eval" / "timeline_pilot" / "outline_trial"
SCRIPT = OT / "pass3_p10b_oc.py"
PAIRS_PER = 25  # như local/ingest_eval/judge.py

from tam.ingestion.events import nodes as nd, post as ip  # noqa: E402


def blocks(path: Path) -> list[tuple[str, str]]:
    parts = re.split(r"^=== CHUNK (.+?) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    return [(parts[i], parts[i + 1].rstrip("\n")) for i in range(1, len(parts), 2)]


def write_blocks(path: Path, bl: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(f"=== CHUNK {c} ===\n{b}\n\n" for c, b in bl), encoding="utf-8")


def load_pilot(S: str) -> dict:
    return json.loads((ORG / M3 / S / "pilot.json").read_text(encoding="utf-8"))


def old_dir(S: str) -> Path:
    return ORG / M3 / S / "old_in"


def make_inputs(S: str, P: dict) -> None:
    for c in P["edits"]:
        src = blocks(ORG / "source" / S / "chunks" / f"{c['page']}.txt")
        past = dict(blocks(ORG / "past" / S / "chunks" / f"{c['page']}.txt"))
        body = past[c["chunk_id"] + "@past"]
        assert any(cid == c["chunk_id"] for cid, _ in src)
        write_blocks(old_dir(S) / "batch0" / "in" / f"{c['page']}.txt", [(cid, body if cid == c["chunk_id"] else b) for cid, b in src])


def run_extract(S: str, P: dict, out: Path, dry: bool) -> str:
    """Chạy pass3_p10b_oc.py nguyên bản nhưng chỉ cho các cửa sổ đã chọn. Trả stdout."""
    only = {(c["page"], c["window"]["section"], c["window"]["window"]) for c in P["edits"]}
    src = SCRIPT.read_text(encoding="utf-8")
    hook = "            ctx = ch[lo - 1] if lo > 0 else None\n"
    assert src.count(hook) == 1
    src = src.replace(hook, "            if ONLY is not None and (name, k, w) not in ONLY: continue\n" + hook)
    g = {"__name__": "__main__", "__file__": str(SCRIPT), "ONLY": only}
    argv, env = sys.argv, dict(os.environ)
    sys.argv = [str(SCRIPT), str(ROOT), str(old_dir(S)), str(out), *[c["page"] for c in P["edits"]]]
    os.environ.update({"DRY": "1" if dry else "0", "PROFILE": "opencode_deepseek_flash", "INGEST_CACHE": "m3_ingest_nothink", "WORKERS": os.environ.get("M3_WORKERS", "5"),
                       "TAM_LLM_METRICS_FILE": str(ROOT / "local" / "m3" / f"llm_calls_old_extract_{S}{'' if os.environ.get('M3_STATE_NAME', 'm3_state') == 'm3_state' else '_' + os.environ['M3_STATE_NAME']}.jsonl")})
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(src, str(SCRIPT), "exec", dont_inherit=True), g)
    except SystemExit:
        pass
    finally:
        sys.argv = argv
        os.environ.clear()
        os.environ.update(env)
    return buf.getvalue()


# ---- gộp cấp trang ----
def key(x: dict) -> tuple:
    return tuple(x.get(k) for k in ("date", "phase", "track", "section", "text"))


def gated_pairs(e: list[dict]) -> list[tuple[int, int]]:
    """Cổng cặp, đúng như scripts/organize_data.py (verdicts)."""
    out = []
    for i in range(len(e)):
        for j in range(i + 1, len(e)):
            a, b = e[i], e[j]
            if not a["date"] or not b["date"] or not ip.compat(a["date"], b["date"]):
                continue
            ok_p = a["phase"] == b["phase"]
            ok_l = (a["section"] == 0) != (b["section"] == 0)
            sim = ip.jacc_u(a["text"], b["text"]) >= 0.15 or bool(ip.toks(a.get("object") or "") & ip.toks(b.get("object") or ""))
            if (ok_p and sim) or (ok_l and (sim or a["track"] == b["track"])):
                out.append((i, j))
    return out


def stored_verdicts(S: str, page: str) -> dict:
    rows = json.loads((ORG / "graph" / S / "verdicts" / f"{page}.json").read_text(encoding="utf-8"))
    d = {}
    for r in rows:
        d[(key(r["a"]), key(r["b"]))] = r["verdict"]
        d[(key(r["b"]), key(r["a"]))] = r["verdict"]
    return d


def replace_window(real_events: list[dict], new_events: list[dict], win_ids: set, section: int) -> list[dict]:
    """Bỏ mốc của cửa sổ (cùng mục, cid trong cửa sổ), chèn mốc mới tại vị trí mốc đầu tiên bị bỏ (hoặc sau mốc cuối của mục)."""
    out, placed = [], False
    last_sec = -1
    for k, x in enumerate(real_events):
        if x["section"] == section and x["cid"] in win_ids:
            if not placed:
                out.extend(new_events)
                placed = True
            continue
        out.append(x)
        if x["section"] <= section:
            last_sec = len(out)
    if not placed:
        out[last_sec if last_sec >= 0 else len(out):last_sec if last_sec >= 0 else len(out)] = new_events
    return out


def build_nodes(S: str, page: str, events: list[dict], judge=None) -> tuple[list[dict], dict]:
    """Gộp quy tắc, gộp cặp theo verdict (cũ theo nội dung; cặp mới -> judge(page, pairs) nếu có), to_nodes. Trả (nút, thống kê)."""
    e = nd.rule_merge(events)
    V = stored_verdicts(S, page)
    pairs = gated_pairs(e)
    same, new, none = [], [], 0
    for i, j in pairs:
        k = (key(e[i]), key(e[j]))
        if k in V:
            v = V[k]
            if v == "same":
                same.append((i, j))
            elif v is None:
                none += 1
        else:
            new.append((i, j))
    if new and judge is not None:
        for (i, j), v in zip(new, judge(page, e, new)):
            if v == "same":
                same.append((i, j))
    e2, st = nd.merge_pairs(e, same)
    st.update(gated=len(pairs), new_pairs=len(new), none_verdict=none)
    return nd.to_nodes(page, e2), st


def real_events(S: str, page: str) -> list[dict]:
    return json.loads((ORG / "graph" / S / "ingest_10b" / f"{page}.json").read_text(encoding="utf-8"))["events"]


PAIR_PROMPT_FILE = ROOT / "src" / "tam" / "llm" / "prompts" / "pair_m2.md"


def pair_prompt() -> str:
    """Prompt gộp cặp sự kiện (`pair_m2.md`, cùng bản với lúc nạp graph Cơ chế 2)."""
    return PAIR_PROMPT_FILE.read_text(encoding="utf-8")


def make_judge(S: str, tag: str = "old_pairs"):
    """judge(page, events, pairs) -> danh sách verdict ("same"/"different") theo thứ tự pairs; 25 cặp mỗi lượt, cache m3_pair_nothink."""
    from pydantic import BaseModel, Field

    from tam.config.loader import load_config
    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured

    class PairV(BaseModel):
        id: str
        verdict: str

    class PairOut(BaseModel):
        verdicts: list[PairV] = Field(default_factory=list)

    os.environ["TAM_LLM_METRICS_FILE"] = str(ROOT / "local" / "m3" / f"llm_calls_{tag}_{S}{'' if os.environ.get('M3_STATE_NAME', 'm3_state') == 'm3_state' else '_' + os.environ['M3_STATE_NAME']}.jsonl")
    cfg = load_config()
    prof = "opencode_deepseek_flash"
    P = cfg.llm.profiles[prof]
    if P.get("session_header"):
        import time
        hd = dict(P.get("default_headers") or {})
        hd[P["session_header"]] = f"m3-old-pairs-{int(time.time())}"
        P._data["default_headers"] = hd
    llm = get_llm(cfg, prof)
    chain = llm.with_structured_output(PairOut)
    cache = SqliteCache(ROOT / "data" / "llm_cache" / "m3_pair_nothink" / "cache.sqlite", threadsafe=True)
    system_t = pair_prompt()
    calls = {"n": 0}

    def judge(page: str, e: list[dict], pairs: list[tuple[int, int]]) -> list[str]:
        f = lambda x: {"date": x["date"], "text": x["text"], "quote": x.get("quote")}
        out = []
        for k in range(0, len(pairs), PAIRS_PER):
            part = pairs[k:k + PAIRS_PER]
            ids = [f"{page}|{i}|{j}" for i, j in part]
            human = "\n".join(f"[{pid}] A: {json.dumps(f(e[i]), ensure_ascii=False)}\n     B: {json.dumps(f(e[j]), ensure_ascii=False)}" for pid, (i, j) in zip(ids, part))
            r = invoke_structured(llm, chain, PairOut, [("system", system_t.format(title=page.replace("_", " "))), ("human", human)], max_attempts=3, cache=cache)
            calls["n"] += 1
            v = {x.id: x.verdict for x in r.verdicts} if r else {}
            out.extend(v.get(pid, "different") for pid in ids)  # thiếu verdict = coi là khác (giống backlog)
        return out

    judge.calls = calls
    judge.cache = cache
    return judge


def finish(S: str, P: dict, judge) -> None:
    od = ORG / M3 / S / "old"
    (od / "ingest_10b").mkdir(parents=True, exist_ok=True)
    (od / "nodes").mkdir(parents=True, exist_ok=True)
    print(f"{'trang':<34}{'loại':<5}{'nút cũ':>7}{'nút real':>9}{'chỉ cũ':>7}{'chỉ real':>9}{'cặp mới':>8}  sự kiện sửa còn trong bản cũ?")
    for c in P["edits"]:
        pg, win, sec = c["page"], set(c["window"]["chunk_ids"]), c["window"]["section"]
        new = json.loads((od / "extract" / f"{pg}.json").read_text(encoding="utf-8"))
        real = real_events(S, pg)
        merged = replace_window(real, new["events"], win, sec)
        (od / "ingest_10b" / f"{pg}.json").write_text(json.dumps({"events": merged, "window_dropped": new.get("dropped", [])}, ensure_ascii=False, indent=1), encoding="utf-8")
        nodes, st = build_nodes(S, pg, merged, judge)
        (od / "nodes" / f"{pg}.json").write_text(json.dumps(nodes, ensure_ascii=False), encoding="utf-8")
        rn = json.loads((ORG / "graph" / S / "nodes" / f"{pg}.json").read_text(encoding="utf-8"))
        a, b = {n["node_id"] for n in nodes}, {n["node_id"] for n in rn}
        ed = ((c.get("event") or {}).get("date") or "")[:4]
        present = any(c["chunk_id"] in n["cids"] and ed and n["date"].startswith(ed) for n in nodes)
        print(f"{pg[:33]:<34}{c['type']:<5}{len(a):>7}{len(b):>9}{len(a - b):>7}{len(b - a):>9}{st['new_pairs']:>8}  {'có' if present else 'không'} (năm {ed})")
    if judge is not None:
        print("lượt gộp cặp gọi:", judge.calls["n"], "| cache hit", judge.cache.hits, "miss", judge.cache.misses)


def load_graph(S: str, P: dict, url: str) -> None:
    """Nạp nút cũ vào Neo4j m3 (KHÔNG dùng cổng 7687 của kho `real`)."""
    assert ":7687" not in url, "từ chối: đây là cổng kho real"
    from neo4j import GraphDatabase

    from tam.config.loader import load_config
    from tam.stores.graph.neo4j_store import Neo4jStore

    g = load_config().graph_store
    store = Neo4jStore(GraphDatabase.driver(url, auth=(g.user, g.password)))
    store.ensure_schema()
    n = 0
    for c in P["edits"]:
        nodes = json.loads((ORG / M3 / S / "old" / "nodes" / f"{c['page']}.json").read_text(encoding="utf-8"))
        n += store.upsert_page(c["page"], nodes)
    print("đã nạp", n, "nút của", len(P["edits"]), "trang vào", url, "| đếm:", store.count())
    store.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["inputs", "plan", "selftest", "extract", "finish", "load"], help="extract/finish gọi LLM; load ghi Neo4j m3")
    ap.add_argument("--neo4j-url", default="bolt://127.0.0.1:7688")
    ap.add_argument("--set", default="tune")
    a = ap.parse_args()
    S = a.set
    P = load_pilot(S)

    if a.step == "inputs":
        make_inputs(S, P)
        print("đã ghi", len(P["edits"]), "trang bản cũ vào", old_dir(S).relative_to(ROOT))
        return

    if a.step == "plan":
        make_inputs(S, P)
        out = run_extract(S, P, Path("/tmp/m3_plan_unused"), dry=True)
        print(out.strip())
        tot_pairs = tot_batches = 0
        for c in P["edits"]:
            win = set(c["window"]["chunk_ids"])
            ev = real_events(S, c["page"])
            e = nd.rule_merge(ev)
            V = stored_verdicts(S, c["page"])
            inw = lambda x: bool(set(x.get("cids", [x["cid"]])) & win)
            gp = gated_pairs(e)
            involve = [(i, j) for i, j in gp if inw(e[i]) or inw(e[j])]
            nb = -(-len(involve) // PAIRS_PER)
            tot_pairs += len(involve)
            tot_batches += nb
            print(f"{c['page'][:34]:<34} {c['type']} cửa sổ {len(win)} chunk | cặp qua cổng {len(gp)}, liên quan cửa sổ {len(involve)} -> {nb} lượt gộp cặp")
        print(f"\nTỔNG: trích cửa sổ = số trang ({len(P['edits'])}); cặp cần phán quyết lại tối đa {tot_pairs} -> tối đa {tot_batches} lượt (mỗi lượt <= {PAIRS_PER} cặp)")
        return

    if a.step == "extract":
        make_inputs(S, P)
        out = ORG / M3 / S / "old" / "extract"
        (ROOT / "local" / "m3").mkdir(parents=True, exist_ok=True)
        print(run_extract(S, P, out, dry=False).strip()[-1500:])
        return

    if a.step == "finish":
        (ROOT / "local" / "m3").mkdir(parents=True, exist_ok=True)
        finish(S, P, make_judge(S))
        return

    if a.step == "load":
        load_graph(S, P, a.neo4j_url)
        return

    if a.step == "selftest":
        ok = bad = 0
        for c in P["edits"]:
            win = set(c["window"]["chunk_ids"])
            ev = real_events(S, c["page"])
            same_win = [x for x in ev if x["section"] == c["window"]["section"] and x["cid"] in win]
            rebuilt = replace_window(ev, same_win, win, c["window"]["section"])
            nodes, st = build_nodes(S, c["page"], rebuilt)
            want = {n["node_id"] for n in json.loads((ORG / "graph" / S / "nodes" / f"{c['page']}.json").read_text(encoding="utf-8"))}
            got = {n["node_id"] for n in nodes}
            if got == want and st["new_pairs"] == 0:
                ok += 1
            else:
                bad += 1
                print("LỆCH", c["page"], len(got), len(want), st)
        print(f"selftest: {ok}/{ok + bad} trang tái tạo đúng nút `real` (không cặp mới, không gọi LLM)")


if __name__ == "__main__":
    main()
