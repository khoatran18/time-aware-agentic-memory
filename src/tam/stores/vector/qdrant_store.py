"""Qdrant: một collection, hai vector (dense + BM25 sparse), đúng 4 payload index."""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient, models

from tam.config.loader import Config
from tam.config.logging import get_logger
from tam.embeddings.fastembed_embedder import Embedder
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import BranchHits, SearchHit, VectorFilter

logger = get_logger(__name__)

DENSE = "dense"
SPARSE = "bm25"

# Chỉ 4 trường này được index (design 02, mục 2). source, chunk_id, end_time cố ý KHÔNG index.
PAYLOAD_INDEXES: dict[str, models.PayloadSchemaType] = {
    "start_time": models.PayloadSchemaType.DATETIME,
    "invalidated_at": models.PayloadSchemaType.DATETIME,
    "domain_features.domain": models.PayloadSchemaType.KEYWORD,
    "domain_features.country": models.PayloadSchemaType.KEYWORD,
}


def point_id(chunk_id: str) -> str:
    """Qdrant chỉ nhận UUID/int làm id; chunk_id gốc vẫn nằm trong payload."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def build_filter(flt: VectorFilter) -> models.Filter:
    must: list[models.Condition] = [
        models.FieldCondition(key="start_time", range=models.DatetimeRange(lte=flt.t_req)),
    ]
    if flt.exclude_invalidated:
        must.append(models.IsNullCondition(is_null=models.PayloadField(key="invalidated_at")))
    for key, value in flt.facets.items():
        must.append(models.FieldCondition(key=f"domain_features.{key}", match=models.MatchValue(value=value)))
    return models.Filter(must=must)


class QdrantStore:
    def __init__(self, client: QdrantClient, collection: str, embedder: Embedder) -> None:
        self._client = client
        self._collection = collection
        self._embedder = embedder

    @classmethod
    def from_config(cls, cfg: Config, embedder: Embedder) -> "QdrantStore":
        vs = cfg.vector_store
        client = QdrantClient(url=vs.url, api_key=vs.get("api_key"))
        return cls(client, vs.collection, embedder)

    def ensure_collection(self, *, recreate: bool = False) -> None:
        exists = self._client.collection_exists(self._collection)
        if exists and recreate:
            logger.warning("Xóa và tạo lại collection %s", self._collection)
            self._client.delete_collection(self._collection)
            exists = False
        if not exists:
            self._client.create_collection(
                self._collection,
                vectors_config={
                    DENSE: models.VectorParams(size=self._embedder.dense_dim, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
            )
            logger.info("Tạo collection %s (dim=%d)", self._collection, self._embedder.dense_dim)
        for field_name, schema in PAYLOAD_INDEXES.items():
            self._client.create_payload_index(self._collection, field_name=field_name, field_schema=schema)

    def payload_index_fields(self) -> set[str]:
        return set(self._client.get_collection(self._collection).payload_schema)

    def upsert(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        texts = [c.text for c in chunks]
        dense = self._embedder.embed_dense(texts)
        sparse = self._embedder.embed_sparse(texts)
        points = [
            models.PointStruct(
                id=point_id(c.chunk_id),
                vector={DENSE: d, SPARSE: models.SparseVector(indices=s.indices, values=s.values)},
                payload=c.model_dump(mode="json"),  # giữ khóa None để IsNull khớp invalidated_at
            )
            for c, d, s in zip(chunks, dense, sparse)
        ]
        self._client.upsert(self._collection, points=points)
        return len(points)

    def search(self, query_text: str, flt: VectorFilter, top_n: int) -> BranchHits:
        qfilter = build_filter(flt)
        dense = self._client.query_points(
            self._collection,
            query=self._embedder.embed_dense_query(query_text),
            using=DENSE,
            query_filter=qfilter,
            limit=top_n,
            with_payload=True,
        )
        sv = self._embedder.embed_sparse_query(query_text)
        sparse = self._client.query_points(
            self._collection,
            query=models.SparseVector(indices=sv.indices, values=sv.values),
            using=SPARSE,
            query_filter=qfilter,
            limit=top_n,
            with_payload=True,
        )
        hits = BranchHits(dense=_to_hits(dense.points), sparse=_to_hits(sparse.points))
        logger.debug("search %r: dense=%d sparse=%d ứng viên sau hard filter", query_text, len(hits.dense), len(hits.sparse))
        return hits

    def count(self) -> int:
        return self._client.count(self._collection, exact=True).count


def _to_hits(points: list[Any]) -> list[SearchHit]:
    return [SearchHit(chunk=Chunk.model_validate(p.payload), score=float(p.score)) for p in points]
