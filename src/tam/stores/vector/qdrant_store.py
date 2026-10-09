"""Qdrant: một collection, hai vector (dense + BM25 sparse), đúng 4 payload index."""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient, models

from tam.config.loader import Config
from tam.config.logging import get_logger
from tam.embedding.base import Embedder
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import BranchHits, SearchHit, VectorFilter

logger = get_logger(__name__)

# Tên hai vector đặt cho mỗi điểm trong Qdrant; khi truy vấn dùng `using=` để chọn nhánh nào
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
    """Dịch VectorFilter sang filter Qdrant: `start_time <= t_req`, `invalidated_at` rỗng, và facet theo `domain_features`."""
    must: list[models.Condition] = [
        models.FieldCondition(key="start_time", range=models.DatetimeRange(lte=flt.t_req)),
    ]
    if flt.exclude_invalidated:
        must.append(models.IsNullCondition(is_null=models.PayloadField(key="invalidated_at")))
    for key, value in flt.facets.items():
        must.append(models.FieldCondition(key=f"domain_features.{key}", match=models.MatchValue(value=value)))
    return models.Filter(must=must)


class QdrantStore:
    """Cài VectorStore bằng Qdrant: một collection, hai vector (dense và BM25)."""

    def __init__(self, client: QdrantClient, collection: str, embedder: Embedder) -> None:
        """`client`: kết nối Qdrant; `collection`: tên collection; `embedder`: tạo vector từ text."""
        self._client = client
        self._collection = collection
        self._embedder = embedder

    @classmethod
    def from_config(cls, cfg: Config, embedder: Embedder) -> QdrantStore:
        """Tạo từ khối `vector_store` trong config; `embedder` do bên ngoài đưa vào."""
        vs = cfg.vector_store
        client = QdrantClient(url=vs.url, api_key=vs.get("api_key"))  # api_key rỗng (None) khi Qdrant local không bật khóa
        return cls(client, vs.collection, embedder)

    def ensure_collection(self, *, recreate: bool = False) -> None:
        """Tạo collection và đúng 4 payload index nếu chưa có; `recreate=True` thì xóa rồi tạo lại."""
        exists = self._client.collection_exists(self._collection)
        if exists and recreate:  # đổi model dense làm đổi số chiều nên phải tạo lại
            logger.warning("Xóa và tạo lại collection %s", self._collection)
            self._client.delete_collection(self._collection)
            exists = False
        if not exists:
            # dense: kích thước lấy từ embedder, đo độ giống bằng cosine
            # sparse (BM25): Modifier.IDF để Qdrant tự nhân trọng số IDF lúc truy vấn
            self._client.create_collection(
                self._collection,
                vectors_config={
                    DENSE: models.VectorParams(size=self._embedder.dense_dim, distance=models.Distance.COSINE)
                },
                sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
            )
            logger.info("Tạo collection %s (dim=%d)", self._collection, self._embedder.dense_dim)
        # Gọi lại khi index đã có thì Qdrant bỏ qua, nên chạy ensure_collection nhiều lần được
        for field_name, schema in PAYLOAD_INDEXES.items():
            self._client.create_payload_index(self._collection, field_name=field_name, field_schema=schema)

    def payload_index_fields(self) -> set[str]:
        """Các trường đang có payload index (dùng để kiểm tra đúng 4 trường)."""
        return set(self._client.get_collection(self._collection).payload_schema)

    def upsert(self, chunks: list[Chunk]) -> int:
        """Embed `text` rồi ghi vector và payload; trả về số chunk. Ghi lại cùng `chunk_id` thì ghi đè."""
        if not chunks:
            return 0
        # Chỉ `text` được embed; các trường còn lại (thời gian, nguồn...) đi vào payload để lọc
        texts = [c.text for c in chunks]
        dense = self._embedder.embed_dense(texts)
        sparse = self._embedder.embed_sparse(texts)
        # Mỗi điểm = id + hai vector (dense, sparse) + payload là toàn bộ chunk
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
        """Chạy nhánh dense và nhánh BM25 riêng, mỗi nhánh áp cùng hard filter và lấy `top_n`."""
        qfilter = build_filter(flt)  # cùng một filter cho cả hai nhánh, để không nhánh nào lọt chunk tương lai/tin giả
        # Nhánh 1: dense, so vector câu hỏi với vector dense của chunk
        dense = self._client.query_points(
            self._collection,
            query=self._embedder.embed_dense_query(query_text),
            using=DENSE,
            query_filter=qfilter,
            limit=top_n,
            with_payload=True,
        )
        # Nhánh 2: sparse (BM25), so từ khóa
        sv = self._embedder.embed_sparse_query(query_text)
        sparse = self._client.query_points(
            self._collection,
            query=models.SparseVector(indices=sv.indices, values=sv.values),
            using=SPARSE,
            query_filter=qfilter,
            limit=top_n,
            with_payload=True,
        )
        # Không gộp ở đây: RRF và min-max làm ở retrieval/temporal/fusion.py
        hits = BranchHits(dense=_to_hits(dense.points), sparse=_to_hits(sparse.points))
        logger.debug("search %r: dense=%d sparse=%d ứng viên sau hard filter", query_text, len(hits.dense), len(hits.sparse))
        return hits

    def count(self) -> int:
        """Số điểm trong collection."""
        return self._client.count(self._collection, exact=True).count


def _to_hits(points: list[Any]) -> list[SearchHit]:
    """Đổi các điểm Qdrant thành SearchHit (dựng lại Chunk từ payload)."""
    return [SearchHit(chunk=Chunk.model_validate(p.payload), score=float(p.score)) for p in points]
