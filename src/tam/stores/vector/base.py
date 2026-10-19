"""Hợp đồng VectorStore (ABC): chỉ qdrant_store.py biết cú pháp Qdrant."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from tam.schemas.chunk import Chunk


@dataclass(frozen=True)
class VectorFilter:
    """Hard filter áp trong từng nhánh tìm kiếm (docs/design/02, bước 2)."""

    t_req: datetime  # start_time <= t_req (chặn tương lai)
    exclude_invalidated: bool = True  # invalidated_at IS NULL
    apply_time: bool = True  # False: không lọc thời gian (chỉ dùng cho baseline plain RAG)
    undated: bool = False  # True: chỉ lấy chunk không có mốc (start_time IS NULL), thay cho lọc thời gian
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


class VectorStore(ABC):
    """Hợp đồng kho vector; chỉ qdrant_store.py biết cú pháp Qdrant."""

    @abstractmethod
    def ensure_collection(self, *, recreate: bool = False) -> None:
        """Tạo collection và các payload index nếu chưa có; `recreate=True` thì xóa rồi tạo lại."""
        raise NotImplementedError

    @abstractmethod
    def upsert(self, chunks: list[Chunk]) -> int:
        """Embed và ghi các chunk; trả về số chunk đã ghi."""
        raise NotImplementedError

    @abstractmethod
    def search(self, query_text: str, flt: VectorFilter, top_n: int) -> BranchHits:
        """Tìm theo hai nhánh dense và BM25, mỗi nhánh đã áp hard filter; trả về hai danh sách xếp hạng riêng."""
        raise NotImplementedError

    def get_chunks(self, chunk_ids: list[str]) -> list[Chunk]:
        """Lấy chunk theo `chunk_id` (không tìm kiếm, không lọc); id không có trong kho thì bỏ qua. Dùng mở rộng chunk liền kề."""
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """Số chunk trong collection."""
        raise NotImplementedError


def merge_branches(a: BranchHits, b: BranchHits, top_n: int) -> BranchHits:
    """Gộp hai kết quả của cùng loại nhánh (vd nhánh có mốc và nhánh không mốc) theo điểm gốc giảm dần, giữ `top_n` mỗi nhánh."""
    def merged(x: list[SearchHit], y: list[SearchHit]) -> list[SearchHit]:
        return sorted([*x, *y], key=lambda h: -h.score)[:top_n]

    return BranchHits(dense=merged(a.dense, b.dense), sparse=merged(a.sparse, b.sparse))
