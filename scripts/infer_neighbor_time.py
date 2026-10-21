"""Tạo collection mới từ collection nguồn, thêm mốc thời gian suy từ chunk liền kề (decisions/07 đề xuất 11). Không gọi LLM, không nhúng lại.

Sao chép nguyên vector từ collection nguồn, chỉ đổi `start_time`/`end_time`/`end_status` và thêm `time_inferred` ở các chunk được suy.
Collection nguồn giữ nguyên. Ví dụ:
  python scripts/infer_neighbor_time.py --source tam_chunks_dev_real_v2 --target tam_chunks_dev_real_v3a \
      --extractions output/20261021_174115/extractions.jsonl --start-rule prev_end --end-rule next_start
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from qdrant_client import QdrantClient, models

from tam.config.loader import load_config
from tam.ingestion.infer_time import END_RULES, START_RULES, group_pages, infer_page
from tam.stores.vector.qdrant_store import PAYLOAD_INDEXES


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--extractions", required=True)
    ap.add_argument("--start-rule", choices=START_RULES, default="none")
    ap.add_argument("--end-rule", choices=END_RULES, default="none")
    ap.add_argument("--max-gap-years", type=float, default=None, help="bỏ suy `end` nếu chunk dated kế tiếp cách quá số năm này")
    ap.add_argument("--cap-years", type=float, default=10.0, help="với start-rule prev_end_cap: chỉ lấy end của chunk trước nếu khoảng của nó <= số năm này")
    args = ap.parse_args()

    cfg = load_config()
    client = QdrantClient(url=cfg.vector_store.url, api_key=cfg.vector_store.get("api_key"))
    if client.collection_exists(args.target):
        raise SystemExit(f"Collection {args.target} đã có; chọn tên khác (script không xóa collection nào).")
    rows = [json.loads(line) for line in Path(args.extractions).read_text(encoding="utf-8").splitlines()]
    inferred = {}
    for page_rows in group_pages(rows).values():
        inferred.update(infer_page(page_rows, start_rule=args.start_rule, end_rule=args.end_rule,
                                   max_gap_years=args.max_gap_years, cap_years=args.cap_years))

    src = client.get_collection(args.source).config.params
    client.create_collection(args.target, vectors_config=src.vectors, sparse_vectors_config=src.sparse_vectors)
    for field, schema in PAYLOAD_INDEXES.items():
        client.create_payload_index(args.target, field_name=field, field_schema=schema)

    n, counts, offset = 0, Counter(), None
    while True:
        points, offset = client.scroll(args.source, limit=256, offset=offset, with_vectors=True, with_payload=True)
        batch = []
        for p in points:
            payload = dict(p.payload)
            new = inferred.get(payload["chunk_id"])
            payload["time_inferred"] = None
            if new is not None:
                payload["start_time"] = new.start.isoformat()
                payload["end_time"] = new.end.isoformat() if new.end else None
                payload["end_status"] = new.end_status
                payload["time_inferred"] = new.inferred
                counts[new.inferred] += 1
            batch.append(models.PointStruct(id=p.id, vector=p.vector, payload=payload))
        if batch:
            client.upsert(args.target, points=batch)
            n += len(batch)
        if offset is None:
            break
    print(json.dumps({"target": args.target, "points": n, "inferred": dict(counts), "start_rule": args.start_rule, "end_rule": args.end_rule,
                      "max_gap_years": args.max_gap_years}, ensure_ascii=False))


if __name__ == "__main__":
    main()
