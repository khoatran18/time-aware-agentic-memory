"""Hợp đồng VectorStore: chỉ qdrant_store.py biết cú pháp Qdrant."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from tam.schemas.chunk import Chunk


@dataclass(frozen=True)
class VectorFilter:
    """Hard filter áp trong từng nhánh tìm kiếm (docs/design/02, bước 2)."""

    t_req: datetime  # start_time <= t_req (chặn tương lai)
    exclude_invalidated: bool = True  # invalidated_at IS NULL
    facets: dict[str, Any] = field(default_factory=dict)  # khóa con của domain_features, VD {"country": "VN"}


@dataclass(frozen=True)
class SearchHit:
    """Một kết quả của một nhánh tìm kiếm: chunk và điểm gốc (cosine hoặc BM25)."""

    chunk: Chunk
    score: float  # điểm gốc của nhánh (cosine hoặc BM25); chưa chuẩn hóa


@dataclass(frozen=True)
class BranchHits:
    """Hai danh sách xếp hạng độc lập; RRF và min-max làm ở retrieval/temporal/fusion.py."""

    dense: list[SearchHit]
    sparse: list[SearchHit]


class VectorStore(Protocol):
    """Hợp đồng kho vector; chỉ qdrant_store.py biết cú pháp Qdrant."""

    def ensure_collection(self, *, recreate: bool = False) -> None:
        """Tạo collection và các payload index nếu chưa có; `recreate=True` thì xóa rồi tạo lại."""
        ...

    def upsert(self, chunks: list[Chunk]) -> int:
        """Embed và ghi các chunk; trả về số chunk đã ghi."""
        ...

    def search(self, query_text: str, flt: VectorFilter, top_n: int) -> BranchHits:
        """Tìm theo hai nhánh dense và BM25, mỗi nhánh đã áp hard filter; trả về hai danh sách xếp hạng riêng."""
        ...

    def count(self) -> int:
        """Số chunk trong collection."""
        ...
