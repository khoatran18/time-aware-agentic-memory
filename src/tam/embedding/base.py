"""Hợp đồng embedding, gồm hai tầng:

- Tầng provider (`DenseEmbedder`, `SparseEmbedder`): một provider phải cài những hàm nào. Provider KẾ THỪA tường minh;
  thiếu hàm thì Python báo lỗi ngay khi tạo đối tượng. Tách dense/sparse vì không phải provider nào cũng có cả hai
  (OpenAI chỉ có dense).
- Tầng store (`Embedder`): thứ `QdrantStore` cần. `factory.HybridEmbedder` kế thừa nó, ghép một dense + một sparse.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SparseVec:
    """Vector thưa: chỉ lưu các chiều khác 0. indices[i] là mã từ, values[i] là trọng số của từ đó."""

    indices: list[int]
    values: list[float]


class DenseEmbedder(ABC):
    """Provider tạo vector dense (ngữ nghĩa). Mọi vector trả về có cùng số chiều `dim`."""

    dim: int  # số chiều vector; QdrantStore dùng để khai báo kích thước collection

    @classmethod
    @abstractmethod
    def from_profile(cls, profile: dict[str, Any]) -> DenseEmbedder:
        """Tạo từ khối `embedding.dense` trong yaml (model_id, api_key, ...). Factory chỉ gọi hàm này."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed một lô văn bản TÀI LIỆU (lúc ingestion). Trả về 1 vector cho mỗi văn bản, giữ nguyên thứ tự."""

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Embed MỘT CÂU HỎI (lúc truy vấn). Tách khỏi `embed` vì có model xử lý câu hỏi khác tài liệu."""


class SparseEmbedder(ABC):
    """Provider tạo vector sparse (từ khóa, kiểu BM25)."""

    @classmethod
    @abstractmethod
    def from_profile(cls, profile: dict[str, Any]) -> SparseEmbedder:
        """Tạo từ khối `embedding.sparse` trong yaml."""

    @abstractmethod
    def embed(self, texts: list[str]) -> list[SparseVec]:
        """Embed một lô văn bản TÀI LIỆU (lúc ingestion)."""

    @abstractmethod
    def embed_query(self, text: str) -> SparseVec:
        """Embed MỘT CÂU HỎI (lúc truy vấn)."""


class Embedder(ABC):
    """Giao diện duy nhất mà QdrantStore biết: một cặp dense + sparse."""

    dense_dim: int

    @abstractmethod
    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        """Vector dense cho một lô tài liệu (dùng trong upsert)."""

    @abstractmethod
    def embed_sparse(self, texts: list[str]) -> list[SparseVec]:
        """Vector sparse cho một lô tài liệu (dùng trong upsert)."""

    @abstractmethod
    def embed_dense_query(self, text: str) -> list[float]:
        """Vector dense cho một câu hỏi (dùng trong search)."""

    @abstractmethod
    def embed_sparse_query(self, text: str) -> SparseVec:
        """Vector sparse cho một câu hỏi (dùng trong search)."""
