"""Nạp bộ con (mặc định: local) vào kho time-aware: chunk -> LLM gán mốc thời gian -> Qdrant.

`--dry-run` chỉ chạy tới bước LLM (không cần Qdrant/embedding). Kết quả từng chunk ghi vào output/<timestamp>/extractions.jsonl.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.config.loader import load_config
from tam.config.logging import get_logger, get_run_dir, setup_logging
from tam.ingestion.loaders.timeqa import load_pages
from tam.ingestion.pipeline import IngestionPipeline, VectorSink
from tam.ingestion.time_extraction import TimeExtractor
from tam.llm.cache import JsonCache
from tam.llm.factory import get_llm_for_role


def main() -> None:
    """Nạp các trang của bộ con; in IngestStats."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="local", help="đọc dataset/eval/<subset>_subset.json")
    ap.add_argument("--dry-run", action="store_true", help="chỉ gọi LLM và ghi extractions.jsonl, không ghi Qdrant")
    ap.add_argument("--recreate", action="store_true", help="xóa và tạo lại collection trước khi nạp")
    ap.add_argument("--no-cache", action="store_true", help="không dùng cache LLM")
    ap.add_argument("--refresh-cache", action="store_true", help="bỏ qua cache cũ, gọi lại LLM và ghi đè")
    ap.add_argument("--limit-pages", type=int, default=None, help="chỉ nạp N trang đầu (để thử nhanh)")
    args = ap.parse_args()

    cfg = load_config()
    setup_logging(cfg)
    logger = get_logger("ingest")

    subset = json.loads((ROOT / "dataset" / "eval" / f"{args.subset}_subset.json").read_text(encoding="utf-8"))
    page_ids = subset["page_ids"][: args.limit_pages]
    docs = load_pages(ROOT / "dataset" / "full_dataset" / "pages.jsonl", page_ids)

    sinks = []
    if not args.dry_run:
        from tam.embedding.factory import get_embedder
        from tam.stores.vector.qdrant_store import QdrantStore

        store = QdrantStore.from_config(cfg, get_embedder(cfg))
        store.ensure_collection(recreate=args.recreate)
        sinks.append(VectorSink(store))

    out_path = get_run_dir() / "extractions.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        def record(rc, res) -> None:
            """Ghi một dòng cho mỗi chunk LLM đã xử lý (kể cả chunk bị bỏ)."""
            row = {
                "chunk_id": rc.chunk_id,
                "start": res.span.start.isoformat() if res.span else None,
                "end": res.span.end.isoformat() if res.span and res.span.end else None,
                "domain": list(res.domains), "ongoing": res.ongoing, "skipped": res.reason, "reason_end_date": res.note, "reason_domain": res.domain_note,
                "ongoing_evidence": res.ongoing_evidence, "ongoing_downgraded": res.ongoing_downgraded,
                "text": rc.text[:300],
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            f.flush()

        cache = None if args.no_cache else JsonCache(ROOT / "data" / "llm_cache", refresh=args.refresh_cache)
        extractor = TimeExtractor(get_llm_for_role(cfg, "ingestion_time"), cache=cache)
        stats = IngestionPipeline(extractor, sinks, on_result=record).run(docs)

    logger.info("Kết quả: %s", stats.to_dict())
    if cache is not None:
        print(f"Cache LLM: {cache.hits} lần dùng lại, {cache.misses} lần gọi LLM")
    print(f"{stats.to_dict()}\nChi tiết từng chunk: {out_path}")


if __name__ == "__main__":
    main()
