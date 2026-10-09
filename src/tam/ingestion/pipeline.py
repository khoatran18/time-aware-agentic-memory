"""Chuỗi ingestion: tài liệu -> chunk -> khử trùng hash -> trích mốc thời gian -> sink (kho đích).

Hiện chỉ có VectorSink; CC2/3 sẽ thêm GraphSink vào cùng danh sách `sinks`, không sửa file này (planning mục 7.4).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass

from tam.config.logging import get_logger
from tam.ingestion.chunking import chunk_document
from tam.ingestion.time_extraction import TimeExtractor
from tam.ingestion.types import RawDoc
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import VectorStore

logger = get_logger(__name__)


class Sink(ABC):
    """Đích ghi của ingestion (VectorDB, sau này GraphDB)."""

    @abstractmethod
    def write(self, chunks: list[Chunk]) -> None:
        """Ghi một lô chunk đã có mốc thời gian."""
        raise NotImplementedError


class VectorSink(Sink):
    """Ghi vào VectorStore (embed dense + BM25 nằm trong store)."""

    def __init__(self, store: VectorStore) -> None:
        """`store`: kho vector đã `ensure_collection`."""
        self._store = store

    def write(self, chunks: list[Chunk]) -> None:
        """Upsert chunk vào kho vector."""
        self._store.upsert(chunks)


@dataclass
class IngestStats:
    """Bộ đếm một lần ingestion (planning mục 4.3: số nạp, bỏ vì không mốc, bỏ vì hash trùng)."""

    docs: int = 0
    chunks_total: int = 0
    ingested: int = 0
    skipped_no_time: int = 0
    skipped_invalid_time: int = 0
    skipped_duplicate: int = 0

    def to_dict(self) -> dict[str, int]:
        """Dạng dict để in hoặc ghi json."""
        return asdict(self)


class IngestionPipeline:
    """Chạy ingestion; chunker là hàm thuần, LLM nằm trong `extractor`, kho nằm trong `sinks`."""

    def __init__(self, extractor: TimeExtractor, sinks: Sequence[Sink]) -> None:
        """`sinks`: ghi lần lượt theo thứ tự."""
        self._extractor = extractor
        self._sinks = list(sinks)

    def run(self, docs: Iterable[RawDoc]) -> IngestStats:
        """Nạp toàn bộ `docs`; hash trùng trong cùng lần chạy chỉ nạp bản đầu tiên."""
        stats = IngestStats()
        seen: set[str] = set()
        for doc in docs:
            stats.docs += 1
            raw_chunks = chunk_document(doc)
            stats.chunks_total += len(raw_chunks)

            fresh = []
            for rc in raw_chunks:
                if rc.content_hash in seen:
                    stats.skipped_duplicate += 1
                else:
                    seen.add(rc.content_hash)
                    fresh.append(rc)

            results = self._extractor.extract(doc.title, fresh) if fresh else []
            out: list[Chunk] = []
            for rc, res in zip(fresh, results):
                if res.span is None:
                    if res.reason == "invalid_time":
                        stats.skipped_invalid_time += 1
                    else:
                        stats.skipped_no_time += 1
                    continue
                out.append(Chunk(
                    chunk_id=rc.chunk_id, text=rc.text, source=doc.source,
                    start_time=res.span.start, end_time=res.span.end, domain_features=dict(doc.domain_features),
                ))
            if out:
                for sink in self._sinks:
                    sink.write(out)
                stats.ingested += len(out)
            logger.debug("Ingest %s: %d chunk, nạp %d", doc.doc_id, len(raw_chunks), len(out))
        logger.info("Ingestion xong: %s", stats.to_dict())
        return stats
