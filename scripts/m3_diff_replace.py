"""Cơ chế 3, hệ Diff-replace: bắt đầu từ trạng thái CŨ (m3_state/<tập>/old), chỉ trích lại chunk đổi của bản mới.

Bước 2 (khác hai hệ kia): cửa sổ bản mới vẫn đưa đủ vào prompt 10b nguyên bản nhưng chỉ chunk đổi là chunk cần trích, các chunk còn lại
của cửa sổ gắn "(context only)". Mốc thô của chunk đổi (cùng mục, cid = chunk đổi) bị bỏ, mốc mới chèn thay; mốc của chunk khác giữ nguyên.
Nút gộp nhiều chunk chỉ mất phần của chunk đổi khi gộp lại cấp trang (bước 3 chạy lại luật + verdict cũ; cặp mới gọi LLM). Không có bước LLM quyết định.
Bước 1 = scripts/m3_diff.py (diff.json); bước 3, 4 dùng lại build_nodes/to_nodes của m3_build_old.py.

  plan     DRY: số lượt trích (không gọi LLM)
  extract  GỌI LLM: một lượt mỗi chỗ sửa (cache data/llm_cache/m3_diffrep_nothink, opencode_deepseek_flash, thinking tắt)
  finish   thay mốc chunk đổi, gộp cấp trang (cặp mới gọi LLM, cache m3_pair_nothink), ghi nút
  load     nạp nút vào Neo4j m3 (cổng 7688; từ chối 7687)
Ghi: dataset/organized/m3_state/<tập>/diff_replace/{extract,ingest_10b,nodes}/<trang>.json
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m3_build_old as b  # noqa: E402

ROOT, ORG, M3, S0 = b.ROOT, b.ORG, b.M3, os.environ.get("M3_SET", "tune")


def system_dir(S: str) -> Path:
    return ORG / M3 / S / "diff_replace"


def make_inputs(S: str, P: dict) -> Path:
    d = system_dir(S) / "in" / "batch0" / "in"  # bản MỚI của trang (nguồn)
    d.mkdir(parents=True, exist_ok=True)
    for c in P["edits"]:
        shutil.copy(ORG / "source" / S / "chunks" / f"{c['page']}.txt", d / f"{c['page']}.txt")
    return system_dir(S) / "in"


def run_extract(S: str, P: dict, out: Path, dry: bool) -> str:
    only = {(c["page"], c["window"]["section"], c["window"]["window"]): c["chunk_id"] for c in P["edits"]}
    src = b.SCRIPT.read_text(encoding="utf-8")
    hook = "            ctx = ch[lo - 1] if lo > 0 else None\n"
    old_job = "jobs.append((name, k, w, chunks[0][1], s[\"title\"], ctx, ch[lo:lo + WINDOW]))"
    assert src.count(hook) == 1 and src.count(old_job) == 1
    src = src.replace(hook, "            if (name, k, w) not in ONLY: continue\n" + hook)
    # chỉ chunk đổi được trích; các chunk khác của cửa sổ là context
    src = src.replace(old_job, "jobs.append((name, k, w, chunks[0][1], s[\"title\"], ctx, [(i, x if chunks[i][0] == ONLY[(name, k, w)] else '(context only) ' + x) for i, x in ch[lo:lo + WINDOW]]))")
    g = {"__name__": "__main__", "__file__": str(b.SCRIPT), "ONLY": only}
    argv, env = sys.argv, dict(os.environ)
    sys.argv = [str(b.SCRIPT), str(ROOT), str(make_inputs(S, P)), str(out), *[c["page"] for c in P["edits"]]]
    os.environ.update({"DRY": "1" if dry else "0", "PROFILE": "opencode_deepseek_flash", "INGEST_CACHE": "m3_diffrep_nothink", "WORKERS": os.environ.get("M3_WORKERS", "5"),
                       "TAM_LLM_METRICS_FILE": str(ROOT / "local" / "m3" / f"llm_calls_diffrep_extract_{S}{'' if os.environ.get('M3_STATE_NAME', 'm3_state') == 'm3_state' else '_' + os.environ['M3_STATE_NAME']}.jsonl")})
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(src, str(b.SCRIPT), "exec", dont_inherit=True), g)
    except SystemExit:
        pass
    finally:
        sys.argv = argv
        os.environ.clear()
        os.environ.update(env)
    return buf.getvalue()


def finish(S: str, P: dict, judge) -> None:
    sd = system_dir(S)
    for sub in ("ingest_10b", "nodes"):
        (sd / sub).mkdir(parents=True, exist_ok=True)
    print(f"{'trang':<34}{'loại':<5}{'mốc mới':>8}{'bỏ ctx':>7}{'nút':>5}{'nút cũ':>7}{'mất':>5}{'thêm':>5}{'cặp mới':>8}  sự kiện sửa trong kết quả?")
    for c in P["edits"]:
        pg, cid, sec = c["page"], c["chunk_id"], c["window"]["section"]
        ex = json.loads((sd / "extract" / f"{pg}.json").read_text(encoding="utf-8"))
        new = [e for e in ex["events"] if e["cid"] == cid]
        ctx_ev = len(ex["events"]) - len(new)  # mốc ở chunk context (lỗi của mô hình), bỏ
        base = json.loads((ORG / M3 / S / "old" / "ingest_10b" / f"{pg}.json").read_text(encoding="utf-8"))["events"]
        merged = b.replace_window(base, new, {cid}, sec)
        (sd / "ingest_10b" / f"{pg}.json").write_text(json.dumps({"events": merged, "dropped": ex.get("dropped", [])}, ensure_ascii=False, indent=1), encoding="utf-8")
        nodes, st = b.build_nodes(S, pg, merged, judge)
        (sd / "nodes" / f"{pg}.json").write_text(json.dumps(nodes, ensure_ascii=False), encoding="utf-8")
        old = json.loads((ORG / M3 / S / "old" / "nodes" / f"{pg}.json").read_text(encoding="utf-8"))
        a, o = {n["node_id"] for n in nodes}, {n["node_id"] for n in old}
        ed = ((c.get("event") or {}).get("date") or "")[:4]
        present = any(cid in n["cids"] and ed and n["date"].startswith(ed) for n in nodes)
        print(f"{pg[:33]:<34}{c['type']:<5}{len(new):>8}{ctx_ev:>7}{len(a):>5}{len(o):>7}{len(o - a):>5}{len(a - o):>5}{st['new_pairs']:>8}  {'có' if present else 'không'} (năm {ed})")
    if judge is not None:
        print("lượt gộp cặp gọi:", judge.calls["n"], "| cache hit", judge.cache.hits, "miss", judge.cache.misses)


def load_graph(S: str, P: dict, url: str) -> None:
    assert ":7687" not in url, "từ chối: đây là cổng kho real"
    from neo4j import GraphDatabase

    from tam.config.loader import load_config
    from tam.stores.graph.neo4j_store import Neo4jStore

    g = load_config().graph_store
    store = Neo4jStore(GraphDatabase.driver(url, auth=(g.user, g.password)))
    store.ensure_schema()
    n = sum(store.upsert_page(c["page"], json.loads((system_dir(S) / "nodes" / f"{c['page']}.json").read_text(encoding="utf-8"))) for c in P["edits"])
    print("đã nạp", n, "nút vào", url, "| đếm:", store.count())
    store.close()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["plan", "extract", "finish", "load"])
    ap.add_argument("--neo4j-url", default="bolt://127.0.0.1:7688")
    ap.add_argument("--set", default=S0)
    a = ap.parse_args()
    S = a.set
    P = b.load_pilot(S)
    (ROOT / "local" / "m3").mkdir(parents=True, exist_ok=True)
    if a.step == "plan":
        print(run_extract(S, P, Path("/tmp/m3_diffrep_unused"), True).strip())
    elif a.step == "extract":
        print(run_extract(S, P, system_dir(S) / "extract", False).strip()[-1500:])
    elif a.step == "finish":
        finish(S, P, b.make_judge(S))
    else:
        load_graph(S, P, a.neo4j_url)


if __name__ == "__main__":
    main()
