"""Hợp đồng chung của mọi Retriever (3 cơ chế); mỗi cơ chế kế thừa `Retriever` tường minh."""
from __future__ import annotations

from abc import ABC, abstractmethod

from tam.schemas.query import ProfiledQuery
from tam.schemas.result import RetrievalResult


class Retriever(ABC):
    """Một cơ chế truy xuất; tools/, pipeline/, evaluation/ chỉ phụ thuộc hợp đồng này."""

    mechanism: str  # "temporal" | "timeline" | "conflict"

    @abstractmethod
    def retrieve(self, query: ProfiledQuery) -> RetrievalResult:
        """Nhận câu hỏi đã profile, trả về các chunk đã xếp hạng."""
        raise NotImplementedError
