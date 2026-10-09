"""Embedding dense + sparse (BM25) bằng fastembed. Tách khỏi store để đổi model độc lập với DB."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from tam.config.loader import Config
from tam.config.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SparseVec:
    indices: list[int]
    values: list[float]


class Embedder(Protocol):
    dense_dim: int

    def embed_dense(self, texts: list[str]) -> list[list[float]]: ...
    def embed_sparse(self, texts: list[str]) -> list[SparseVec]: ...
    def embed_dense_query(self, text: str) -> list[float]: ...
    def embed_sparse_query(self, text: str) -> SparseVec: ...


class FastEmbedEmbedder:
    def __init__(self, dense_model_id: str, sparse_model_id: str) -> None:
        from fastembed import SparseTextEmbedding, TextEmbedding  # import trễ: nặng, test không cần

        logger.info("Nạp embedding dense=%s sparse=%s", dense_model_id, sparse_model_id)
        self._dense = TextEmbedding(model_name=dense_model_id)
        self._sparse = SparseTextEmbedding(model_name=sparse_model_id)
        self.dense_dim = len(next(iter(self._dense.embed(["dim probe"]))))

    @classmethod
    def from_config(cls, cfg: Config) -> "FastEmbedEmbedder":
        if cfg.embedding.provider != "fastembed":
            raise ValueError(f"embedding.provider={cfg.embedding.provider!r} chưa được hỗ trợ")
        return cls(cfg.embedding.dense_model_id, cfg.embedding.sparse_model_id)

    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        return [v.tolist() for v in self._dense.embed(texts)]

    def embed_sparse(self, texts: list[str]) -> list[SparseVec]:
        return [SparseVec(v.indices.tolist(), v.values.tolist()) for v in self._sparse.embed(texts)]

    def embed_dense_query(self, text: str) -> list[float]:
        return next(iter(self._dense.query_embed(text))).tolist()

    def embed_sparse_query(self, text: str) -> SparseVec:
        v = next(iter(self._sparse.query_embed(text)))
        return SparseVec(v.indices.tolist(), v.values.tolist())
