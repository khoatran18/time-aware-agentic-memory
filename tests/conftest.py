import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Test không phụ thuộc .env hay biến môi trường của máy."""
    for name in ("APP_ENV", "TAM_CONFIG_DIR", "TAM_PROJECT_ROOT", "TAM_OUTPUT_DIR"):
        monkeypatch.delenv(name, raising=False)


# ---- Kho vector giả + corpus nhiều chủ đề, để test retrieval không cần Qdrant hay embedding ----
import json
import re
from pathlib import Path

from tam.retrieval.temporal.filters import passes_hard_filter
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import BranchHits, SearchHit, VectorFilter, VectorStore

FIXTURES = Path(__file__).parent / "fixtures"


def _words(text: str) -> set[str]:
    """Tập từ chữ thường của một chuỗi."""
    return set(re.findall(r"\w+", text.lower()))


class FakeVectorStore(VectorStore):
    """VectorStore giả: áp hard filter bằng Python, dense = Jaccard từ, sparse = số từ trùng (xếp hạng tất định)."""

    def __init__(self, chunks: list[Chunk]) -> None:
        """`chunks`: toàn bộ dữ liệu của kho."""
        self.chunks = chunks

    def ensure_collection(self, *, recreate: bool = False) -> None:
        """Không cần làm gì với kho trong bộ nhớ."""

    def upsert(self, chunks: list[Chunk]) -> int:
        """Thêm chunk vào bộ nhớ."""
        self.chunks.extend(chunks)
        return len(chunks)

    def count(self) -> int:
        """Số chunk đang có."""
        return len(self.chunks)

    def search(self, query_text: str, flt: VectorFilter, top_n: int) -> BranchHits:
        """Hai nhánh xếp hạng riêng, mỗi nhánh đã lọc; hòa điểm xếp theo chunk_id."""
        q = _words(query_text)
        pool = [c for c in self.chunks if passes_hard_filter(c, flt)]

        def rank(score_fn) -> list[SearchHit]:
            scored = [(score_fn(q, _words(c.text)), c) for c in pool]
            scored = [(s, c) for s, c in scored if s > 0]
            scored.sort(key=lambda t: (-t[0], t[1].chunk_id))
            return [SearchHit(chunk=c, score=s) for s, c in scored[:top_n]]

        return BranchHits(
            dense=rank(lambda a, b: len(a & b) / len(a | b)),
            sparse=rank(lambda a, b: float(len(a & b))),
        )


@pytest.fixture(scope="session")
def corpus_data() -> dict:
    """Nội dung thô của tests/fixtures/temporal_corpus.json (chunks và cases)."""
    return json.loads((FIXTURES / "temporal_corpus.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def corpus_chunks(corpus_data) -> list[Chunk]:
    """Các chunk của corpus nhiều chủ đề."""
    return [Chunk.model_validate(c) for c in corpus_data["chunks"]]


@pytest.fixture
def fake_store(corpus_chunks) -> FakeVectorStore:
    """Kho giả nạp sẵn corpus."""
    return FakeVectorStore(corpus_chunks)
