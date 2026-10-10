"""Cần Qdrant chạy thật (docker compose up -d qdrant). Dùng embedder giả để không phải tải model."""
import hashlib
import uuid
from datetime import datetime, timezone

import pytest
from qdrant_client import QdrantClient

from tam.embedding.base import SparseVec
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import VectorFilter
from tam.stores.vector.qdrant_store import PAYLOAD_INDEXES, QdrantStore

pytestmark = pytest.mark.qdrant

DIM = 16
VOCAB = 1000


def _tokens(text: str) -> list[str]:
    return text.lower().split()


def _h(tok: str, mod: int) -> int:
    return int(hashlib.md5(tok.encode()).hexdigest(), 16) % mod


class FakeEmbedder:
    dense_dim = DIM

    def _dense(self, text):
        v = [0.0] * DIM
        for t in _tokens(text):
            v[_h(t, DIM)] += 1.0
        return v

    def _sparse(self, text):
        counts: dict[int, float] = {}
        for t in _tokens(text):
            counts[_h(t, VOCAB)] = counts.get(_h(t, VOCAB), 0.0) + 1.0
        return SparseVec(list(counts), list(counts.values()))

    def embed_dense(self, texts):
        return [self._dense(t) for t in texts]

    def embed_sparse(self, texts):
        return [self._sparse(t) for t in texts]

    def embed_dense_query(self, text):
        return self._dense(text)

    def embed_sparse_query(self, text):
        return self._sparse(text)


def utc(y, m=1, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


@pytest.fixture
def store():
    client = QdrantClient(url="http://localhost:6333")
    try:
        client.get_collections()
    except Exception:  # noqa: BLE001  (mọi lỗi kết nối đều nghĩa là không có server)
        pytest.skip("Qdrant không chạy ở localhost:6333")
    name = f"tam_test_{uuid.uuid4().hex[:8]}"
    s = QdrantStore(client, name, FakeEmbedder())
    s.ensure_collection()
    yield s
    client.delete_collection(name)


def chunks():
    return [
        Chunk(chunk_id="law2015", text="luat xay dung 2015 quy dinh", source="a", start_time=utc(2015), end_time=utc(2018),
              domain_features={"domain": "law", "country": "VN"}),
        Chunk(chunk_id="law2018", text="luat xay dung 2018 quy dinh", source="a", start_time=utc(2018),
              domain_features={"domain": "law", "country": "VN"}),
        Chunk(chunk_id="law2021", text="luat xay dung 2021 quy dinh", source="a", start_time=utc(2021),
              domain_features={"domain": "law", "country": "VN"}),
        Chunk(chunk_id="fake", text="luat xay dung gia quy dinh", source="b", start_time=utc(2016), invalidated_at=utc(2017),
              domain_features={"domain": "law", "country": "VN"}),
        Chunk(chunk_id="old", text="luat xay dung thoi xua quy dinh", source="c", start_time=utc(1850),
              domain_features={"domain": "law", "country": "FR"}),
    ]


def ids(hits):
    return {h.chunk.chunk_id for h in hits}


def test_only_four_payload_indexes(store):
    assert store.payload_index_fields() == set(PAYLOAD_INDEXES)


def test_upsert_is_idempotent(store):
    assert store.upsert(chunks()) == 5
    store.upsert(chunks())
    assert store.count() == 5


def test_hard_filters_block_future_and_invalidated(store):
    store.upsert(chunks())
    hits = store.search("luat xay dung quy dinh", VectorFilter(t_req=utc(2020)), top_n=10)
    for branch in (hits.dense, hits.sparse):
        got = ids(branch)
        assert "law2021" not in got  # chặn tương lai
        assert "fake" not in got  # invalidated_at != NULL
        assert {"law2015", "law2018", "old"} <= got


def test_invalidated_returned_when_not_excluded(store):
    store.upsert(chunks())
    hits = store.search("luat xay dung quy dinh", VectorFilter(t_req=utc(2020), exclude_invalidated=False), top_n=10)
    assert "fake" in ids(hits.dense)


def test_facet_filter(store):
    store.upsert(chunks())
    hits = store.search("luat", VectorFilter(t_req=utc(2020), facets={"country": "FR"}), top_n=10)
    assert ids(hits.dense) == ids(hits.sparse) == {"old"}


def test_pre_1970_roundtrip(store):
    store.upsert(chunks())
    hits = store.search("thoi xua", VectorFilter(t_req=utc(1900)), top_n=10)
    assert ids(hits.dense) == {"old"}
    assert hits.dense[0].chunk.start_time == utc(1850)


def test_very_old_start_times_are_filtered_correctly(store):
    """TimeQA có mốc từ năm 1136 và 346/830 câu trước 1970: datetime âm epoch phải lọc đúng trong Qdrant."""
    store.upsert([
        Chunk(chunk_id="y1136", text="king ruled", source="a", start_time=utc(1136)),
        Chunk(chunk_id="y1955", text="king ruled", source="a", start_time=utc(1955, 6, 15)),
        Chunk(chunk_id="y1969", text="king ruled", source="a", start_time=utc(1969, 12, 31)),
        Chunk(chunk_id="y1971", text="king ruled", source="a", start_time=utc(1971)),
    ])
    got = store.search("king ruled", VectorFilter(t_req=utc(1969, 12, 31)), top_n=10)
    assert ids(got.dense) == ids(got.sparse) == {"y1136", "y1955", "y1969"}
    got = store.search("king ruled", VectorFilter(t_req=utc(1500)), top_n=10)
    assert ids(got.dense) == {"y1136"}
    assert {h.chunk.start_time for h in got.dense} == {utc(1136)}
