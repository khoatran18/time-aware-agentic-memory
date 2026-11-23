"""Cơ chế 3, hệ Window-replace: từ trạng thái CŨ (m3_state/<tập>/old), thay mốc của cả cửa sổ 8 chunk bằng mốc trích bản mới.

Mốc bản mới của cửa sổ lấy từ ingest 10b `real` đã lưu (cùng prompt, cùng thinking tắt, cùng cửa sổ) nên không tốn lượt LLM; bước 3, 4 dùng lại
build_nodes (luật + verdict lưu theo nội dung, cặp mới gọi LLM nếu có). Kết quả phải trùng nút `real` (đã kiểm bằng selftest của m3_build_old).
Ghi: dataset/organized/m3_state/<tập>/window_replace/{ingest_10b,nodes}/<trang>.json
  run   dựng và in so sánh với bản cũ và `real`
  load  nạp vào Neo4j m3 (cổng 7688)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m3_build_old as b  # noqa: E402

ROOT, ORG, M3 = b.ROOT, b.ORG, b.M3


def system_dir(S: str) -> Path:
    return ORG / M3 / S / "window_replace"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", choices=["run", "load"])
    ap.add_argument("--neo4j-url", default="bolt://127.0.0.1:7688")
    ap.add_argument("--set", default="tune")
    a = ap.parse_args()
    S = a.set
    P = b.load_pilot(S)
    sd = system_dir(S)
    if a.step == "load":
        assert ":7687" not in a.neo4j_url
        from neo4j import GraphDatabase

        from tam.config.loader import load_config
        from tam.stores.graph.neo4j_store import Neo4jStore

        g = load_config().graph_store
        store = Neo4jStore(GraphDatabase.driver(a.neo4j_url, auth=(g.user, g.password)))
        store.ensure_schema()
        n = sum(store.upsert_page(c["page"], json.loads((sd / "nodes" / f"{c['page']}.json").read_text(encoding="utf-8"))) for c in P["edits"])
        print("đã nạp", n, "nút vào", a.neo4j_url, "| đếm:", store.count())
        store.close()
        return
    for sub in ("ingest_10b", "nodes"):
        (sd / sub).mkdir(parents=True, exist_ok=True)
    print(f"{'trang':<34}{'loại':<5}{'mốc cửa sổ':>11}{'nút':>5}{'nút cũ':>7}{'mất':>5}{'thêm':>5}{'cặp mới':>8}{'=real':>6}")
    for c in P["edits"]:
        pg, win, sec = c["page"], set(c["window"]["chunk_ids"]), c["window"]["section"]
        real = b.real_events(S, pg)
        new = [x for x in real if x["section"] == sec and x["cid"] in win]
        base = json.loads((ORG / M3 / S / "old" / "ingest_10b" / f"{pg}.json").read_text(encoding="utf-8"))["events"]
        merged = b.replace_window(base, new, win, sec)
        (sd / "ingest_10b" / f"{pg}.json").write_text(json.dumps({"events": merged}, ensure_ascii=False, indent=1), encoding="utf-8")
        nodes, st = b.build_nodes(S, pg, merged)
        (sd / "nodes" / f"{pg}.json").write_text(json.dumps(nodes, ensure_ascii=False), encoding="utf-8")
        old = {n["node_id"] for n in json.loads((ORG / M3 / S / "old" / "nodes" / f"{pg}.json").read_text(encoding="utf-8"))}
        rl = {n["node_id"] for n in json.loads((ORG / "graph" / S / "nodes" / f"{pg}.json").read_text(encoding="utf-8"))}
        ids = {n["node_id"] for n in nodes}
        print(f"{pg[:33]:<34}{c['type']:<5}{len(new):>11}{len(ids):>5}{len(old):>7}{len(old - ids):>5}{len(ids - old):>5}{st['new_pairs']:>8}{'có' if ids == rl else 'KHÔNG':>6}")


if __name__ == "__main__":
    main()
