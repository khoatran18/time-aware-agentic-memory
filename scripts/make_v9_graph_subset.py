"""Tạo bộ con câu hỏi v9 (timeline) thuộc các trang đã có trong graph Neo4j. KHÔNG gọi LLM.

Ghi `dataset/eval/v9_graph_subset.json` với `cases` cùng khuôn `run_agent_search.py` đọc: idx = qid (Trang:chỉ số), page_id = tên trang trong kho (`/wiki/...`,
lấy từ chunk_id của sự kiện vì tên trang trong graph đã bỏ dấu và ngoặc), question_hard (= "tên trang. câu hỏi", cùng định dạng truy vấn của graph_eval.py), question (gốc), type, graph_page. Trang có chunk không còn trong kho vector bị loại (A và B không đọc đủ).
Ví dụ: python scripts/make_v9_graph_subset.py
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.config.loader import load_config
from tam.stores.graph.neo4j_store import Neo4jStore


def qdrant_chunk_ids(url: str, collection: str) -> set[str]:
    """Mọi `chunk_id` của một collection Qdrant (phân trang scroll)."""
    out: set[str] = set()
    off = None
    while True:
        body = {"limit": 1000, "with_payload": ["chunk_id"], "with_vector": False, **({"offset": off} if off else {})}
        req = urllib.request.Request(f"{url}/collections/{collection}/points/scroll", json.dumps(body).encode(), {"Content-Type": "application/json"})
        res = json.load(urllib.request.urlopen(req))["result"]
        out |= {p["payload"]["chunk_id"] for p in res["points"]}
        off = res.get("next_page_offset")
        if not off:
            return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--collection", default="tam_chunks_dev_tune", help="kho vector dùng để kiểm chunk có đủ")
    ap.add_argument("--out", default=str(ROOT / "dataset/eval/v9_graph_subset.json"))
    args = ap.parse_args()
    cfg = load_config()
    graph = Neo4jStore.from_config(cfg)
    rows = graph._run("MATCH (e:Event)-[:FROM_CHUNK]->(c:Chunk) RETURN e.page AS p, collect(DISTINCT c.chunk_id) AS c")
    have = qdrant_chunk_ids(str(cfg.vector_store.url), args.collection)
    pages: dict[str, str] = {}
    dropped = []
    for r in rows:
        stems = {c.split("#")[0] for c in r["c"]}
        if len(stems) != 1 or not all(c in have for c in r["c"]):
            dropped.append(r["p"])
            continue
        pages[r["p"]] = stems.pop()
    cases = []
    for f in sorted((ROOT / "dataset/eval/timeline_pilot/questions_v9").glob("*.jsonl")):
        i = 0
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            q = json.loads(line)
            if q["page"] in pages:
                cases.append({"idx": f"{f.stem}:{i}", "page_id": pages[q["page"]], "graph_page": q["page"], "type": q["type"], "question": q["question"],
                              "question_hard": f"{q['page'].replace('_', ' ')}. {q['question']}"})  # như truy vấn của local/ingest_eval/graph_eval.py: câu v9 không nêu thực thể nên ghép tên trang vào đầu
            i += 1
    Path(args.out).write_text(json.dumps({"source": "questions_v9 ∩ graph pages", "dropped_pages": dropped, "cases": cases}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(cases)} câu, {len(pages)} trang; loại trang {dropped}; {dict(Counter(c['type'] for c in cases))} -> {args.out}")


if __name__ == "__main__":
    main()
