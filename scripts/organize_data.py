"""Gom dữ liệu thành `dataset/organized/` (chỉ COPY, không xóa thư mục cũ). Chạy lại được (ghi đè).

Cấu trúc đích (mỗi nhóm chia tiếp theo tập tune / valid / test_clean):
  source/<tập>/{text,chunks}/            văn bản gốc (.txt) và văn bản đã chia chunk (đầu vào ingest)
  vector/<tập>/chunks.jsonl              payload từng chunk trong Qdrant (nhãn thời gian), không gồm vector
  timeline_gold/<tập>/                   gold timeline theo trang (mốc vàng, do người/LLM duyệt)
  graph/<tập>/{ingest_10b,verdicts,nodes}/  mốc ingest 10b; verdict từng cặp (kèm nội dung hai mốc); nút graph theo trang
  questions/mech1/<tập>/                 bộ câu Cơ chế 1 (subset + cases, có đáp án `targets`)
  questions/mech1/_probe/                bộ kiểm khả năng (day, relative, no_anchor, open_end) và tune_base_subset
  questions/mech2/<tập>/              bộ câu v9 theo trang (jsonl); thêm `gold_events` (đáp án) nối từ timeline_gold
Danh sách trang mỗi tập: pages_<tập>.txt ở thư mục gốc `organized/`. Xuất vector cần Qdrant chạy (localhost:6333).
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "dataset" / "eval"
TP = EV / "timeline_pilot"
OT = TP / "outline_trial"
JO = ROOT / "local" / "ingest_eval" / "judge_out"
OUT = ROOT / "dataset" / "organized"
SPLITS = {"tune": "tune", "valid": "valid", "test_clean": "test"}   # tập -> tiền tố file danh sách trang
COL = {"tune": "tam_chunks_dev_tune", "valid": "tam_chunks_dev_valid", "test_clean": "tam_chunks_dev_test_clean"}
INGEST_DIR = {"tune": "out_p10b_ds_T", "valid": "out_p10b_ds_VN", "test_clean": "out_p10b_ds_TC"}
NODES = {"tune": "graph_nodes.json", "valid": "graph_nodes_V.json", "test_clean": "graph_nodes_C.json"}
VERDICT = {"tune": "graph_missing_T.json", "valid": "graph_missing_V.json", "test_clean": "graph_missing_C.json"}


# 3 trang tune mà gold/câu v9 (pilot5, pilot10) dùng tên cũ, khác tên trang trong batchN
ALIAS = {"Regius_Professor_Civil_Law": "Regius_Professor_of_Civil_Law_Oxford", "Carl_Ehrensvard": "Carl_August_Ehrensv_rd_1858_1944",
         "Southern_Military_District": "Southern_Military_District_Milo_S"}


def cp(src: Path, dst: Path) -> bool:
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def verdicts(s: str, ns: list[str]) -> None:
    """Một file mỗi trang: các cặp qua cổng, verdict (null = chưa có), kèm nội dung hai mốc. Id cặp `trang|i|j` theo thứ tự sau rule_merge."""
    sys.path.insert(0, str(ROOT / "src"))
    from tam.ingestion.events import nodes as nd, post as ip

    V = {v["id"]: v["verdict"] for v in json.loads((JO / VERDICT[s]).read_text(encoding="utf-8"))}
    d = OUT / "graph" / s / "verdicts"
    d.mkdir(parents=True, exist_ok=True)
    for n in ns:
        f = OT / INGEST_DIR[s] / f"{n}.json"
        if not f.exists():
            continue
        e = nd.rule_merge(json.loads(f.read_text(encoding="utf-8"))["events"])
        rows = []
        for i in range(len(e)):
            for j in range(i + 1, len(e)):
                a, b = e[i], e[j]
                if not a["date"] or not b["date"] or not ip.compat(a["date"], b["date"]):
                    continue
                ok_p = a["phase"] == b["phase"]
                ok_l = (a["section"] == 0) != (b["section"] == 0)
                sim = ip.jacc_u(a["text"], b["text"]) >= 0.15 or bool(ip.toks(a.get("object") or "") & ip.toks(b.get("object") or ""))
                if (ok_p and sim) or (ok_l and (sim or a["track"] == b["track"])):
                    pid = f"{n}|{i}|{j}"
                    sl = lambda x: {k: x.get(k) for k in ("date", "phase", "track", "section", "text")}
                    rows.append({"id": pid, "i": i, "j": j, "verdict": V.get(pid), "a": sl(a), "b": sl(b)})
        (d / f"{n}.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
        STAT[s]["verdict_pairs"] += len(rows)
        STAT[s]["verdict_missing"] += sum(r["verdict"] is None for r in rows)


STAT: dict = defaultdict(lambda: defaultdict(int))


def main() -> None:
    pages = {s: (ROOT / "local" / "ingest_eval" / f"{p}_pages.txt").read_text().split() for s, p in SPLITS.items()}
    split_of = {n: s for s, ns in pages.items() for n in ns}
    OUT.mkdir(parents=True, exist_ok=True)
    stat = STAT
    for s, ns in pages.items():
        (OUT / f"pages_{s}.txt").write_text("\n".join(ns) + "\n")

    # chunk đã chia (đầu vào ingest) + gold + bản đồ url -> tên trang
    url2page: dict[str, str] = {}
    for b in sorted(TP.glob("batch*")) + [TP / "pilot5", TP / "pilot10"]:
        for f in (b / "in").glob("*.txt") if b.name.startswith("batch") and (b / "in").exists() else []:
            n = f.stem
            if n not in split_of:
                continue
            s = split_of[n]
            if cp(f, OUT / "source" / s / "chunks" / f.name):
                stat[s]["chunks"] += 1
            for m in re.finditer(r"^=== CHUNK (\S+?)#\d+ ===", f.read_text(encoding="utf-8"), flags=re.M):
                url2page[m.group(1)] = n
        for f in (b / "rev").glob("*.json") if (b / "rev").exists() else []:
            n = ALIAS.get(f.stem, f.stem)
            if n in split_of and not (OUT / "timeline_gold" / split_of[n] / f"{n}.json").exists() and cp(f, OUT / "timeline_gold" / split_of[n] / f"{n}.json"):
                stat[split_of[n]]["gold"] += 1

    # văn bản gốc
    idx = json.loads((ROOT / "data" / "text_corpus.index.json").read_text(encoding="utf-8"))
    for url, v in idx.items():
        n = url2page.get(url)
        if n and cp(ROOT / "data" / "text_corpus" / v["file"], OUT / "source" / split_of[n] / "text" / v["file"]):
            stat[split_of[n]]["text"] += 1

    # timeline: ingest 10b, nút graph, verdict
    for s, ns in pages.items():
        for n in ns:
            if cp(OT / INGEST_DIR[s] / f"{n}.json", OUT / "graph" / s / "ingest_10b" / f"{n}.json"):
                stat[s]["ingest_10b"] += 1
        nodes = json.loads((JO / NODES[s]).read_text(encoding="utf-8"))
        d = OUT / "graph" / s / "nodes"
        d.mkdir(parents=True, exist_ok=True)
        for n in ns:
            if n in nodes:
                (d / f"{n}.json").write_text(json.dumps(nodes[n], ensure_ascii=False), encoding="utf-8")
                stat[s]["graph_nodes"] += 1
        verdicts(s, ns)

    # câu hỏi Cơ chế 1 và Cơ chế 2 (v9)
    for s in SPLITS:
        for f in (EV / f"{s}_subset.json", EV / f"{s}_subset_cases.csv"):
            cp(f, OUT / "questions" / "mech1" / s / f.name)
    for f in sorted((TP / "questions_v9").glob("*.jsonl")):
        n = ALIAS.get(f.stem, f.stem)
        if n not in split_of:
            continue
        s = split_of[n]
        gp = OUT / "timeline_gold" / s / f"{n}.json"
        ev = {e["id"]: e for e in json.loads(gp.read_text(encoding="utf-8"))["events"]} if gp.exists() else {}
        d = OUT / "questions" / "mech2" / s
        d.mkdir(parents=True, exist_ok=True)
        with open(d / f"{n}.jsonl", "w", encoding="utf-8") as o:
            for line in filter(str.strip, f.read_text(encoding="utf-8").splitlines()):
                q = json.loads(line)
                if q.get("page") != n:
                    q["page_orig"], q["page"] = q.get("page"), n
                q["gold_events"] = [{k: ev[i].get(k) for k in ("id", "date", "text", "track", "phase")} for i in q.get("gold_event_ids", []) if i in ev]
                o.write(json.dumps(q, ensure_ascii=False) + "\n")
        stat[s]["questions_v9"] += 1
    for f in list(EV.glob("v9_*graph*_subset.json")):
        cp(f, OUT / "questions" / "mech2" / "_subsets" / f.name)
    for f in (TP / "extras").glob("*.json"):
        cp(f, OUT / "questions" / "mech2" / "_extras" / f.name)
    for f in (TP / "derived_classify").glob("*.jsonl"):
        cp(f, OUT / "timeline_gold" / "_derived_classify" / f.name)
    for f in list((EV / "capability_probe").glob("*.jsonl")) + list(EV.glob("capability_probe*_subset.json")) + [EV / "tune_base_subset.json"]:
        cp(f, OUT / "questions" / "mech1" / "_probe" / f.name)
    cp(EV / "real_subset.json", OUT / "questions" / "mech1" / "_real" / "real_subset.json")

    # vector: payload Qdrant theo trang
    if "--no-vector" not in sys.argv:
        for s, col in COL.items():
            rows: dict[str, list] = defaultdict(list)
            nxt = None
            while True:
                body = {"limit": 512, "with_payload": True, "with_vector": False}
                if nxt:
                    body["offset"] = nxt
                req = urllib.request.Request(f"http://localhost:6333/collections/{col}/points/scroll",
                                             data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
                r = json.load(urllib.request.urlopen(req))["result"]
                for p in r["points"]:
                    rows[url2page.get(p["payload"].get("doc_id"), "?")].append(p["payload"])
                nxt = r.get("next_page_offset")
                if not nxt:
                    break
            d = OUT / "vector" / s
            d.mkdir(parents=True, exist_ok=True)
            with open(d / "chunks.jsonl", "w", encoding="utf-8") as f:
                for n, ps in sorted(rows.items()):
                    for p in ps:
                        f.write(json.dumps({"page": n, **p}, ensure_ascii=False) + "\n")
            stat[s]["vector_chunks"] = sum(len(v) for v in rows.values())
            stat[s]["vector_unmapped"] = len(rows.get("?", []))
    for s in SPLITS:
        print(s, dict(stat[s]))


if __name__ == "__main__":
    main()
