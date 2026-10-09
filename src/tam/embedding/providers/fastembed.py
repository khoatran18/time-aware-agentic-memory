"""fastembed: chạy local bằng ONNX, miễn phí, có cả dense lẫn sparse (BM25)."""
from __future__ import annotations

from typing import Any

from tam.config.logging import get_logger
from tam.embedding.base import DenseEmbedder, SparseEmbedder, SparseVec
from tam.embedding.registry import register_dense, register_sparse

logger = get_logger(__name__)


@register_dense("fastembed")
class FastEmbedDense(DenseEmbedder):
    """Dense qua fastembed (vd BAAI/bge-small-en-v1.5)."""

    def __init__(self, model_id: str, cache_dir: str | None = None) -> None:
        """Nạp model; chưa có trong cache thì fastembed tự tải từ HuggingFace. cache_dir=None dùng thư mục tạm."""
        from fastembed import TextEmbedding  # import trễ: nặng, test không cần

        logger.info("Nạp fastembed dense: %s", model_id)
        self._model = TextEmbedding(model_name=model_id, cache_dir=cache_dir)
        self.dim = len(next(iter(self._model.embed(["dim probe"]))))  # đo số chiều bằng cách embed thử 1 câu

    @classmethod
    def from_profile(cls, profile: dict[str, Any]) -> FastEmbedDense:
        """Tạo từ MỘT KHỐI dưới `embedding.profiles.dense` trong configs/config.*.yaml (đã đổi sang dict), ví dụ:

            embedding:
              profiles:
                dense:
                  bge_small_en:                  # <- tên profile
                    provider: "fastembed"
                    model_id: "BAAI/bge-small-en-v1.5"
                    # cache_dir: "data/models"   (tùy chọn)

        Khóa dùng ở đây: `model_id`, `cache_dir`. Tên profile không nằm trong dict; factory dùng nó để chọn khối.
        """
        return cls(profile["model_id"], profile.get("cache_dir"))

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed lô tài liệu; mỗi vector từ numpy được đổi sang list thường."""
        return [v.tolist() for v in self._model.embed(texts)]

    def embed_query(self, text: str) -> list[float]:
        """Embed câu hỏi bằng `query_embed` (một số model thêm tiền tố riêng cho câu hỏi)."""
        return next(iter(self._model.query_embed(text))).tolist()


@register_sparse("fastembed")
class FastEmbedSparse(SparseEmbedder):
    """Sparse qua fastembed (vd Qdrant/bm25)."""

    def __init__(self, model_id: str, cache_dir: str | None = None) -> None:
        """Nạp model sparse; cách tải/cache giống FastEmbedDense."""
        from fastembed import SparseTextEmbedding

        logger.info("Nạp fastembed sparse: %s", model_id)
        self._model = SparseTextEmbedding(model_name=model_id, cache_dir=cache_dir)

    @classmethod
    def from_profile(cls, profile: dict[str, Any]) -> FastEmbedSparse:
        """Tạo từ MỘT KHỐI dưới `embedding.profiles.sparse` trong configs/config.*.yaml (đã đổi sang dict), ví dụ:

            embedding:
              profiles:
                sparse:
                  bm25:                  # <- tên profile
                    provider: "fastembed"
                    model_id: "Qdrant/bm25"
                    # cache_dir: "data/models"   (tùy chọn)

        Khóa dùng ở đây: `model_id`, `cache_dir`. Tên profile không nằm trong dict; factory dùng nó để chọn khối.
        """
        return cls(profile["model_id"], profile.get("cache_dir"))

    def embed(self, texts: list[str]) -> list[SparseVec]:
        """Embed lô tài liệu thành các SparseVec."""
        return [SparseVec(v.indices.tolist(), v.values.tolist()) for v in self._model.embed(texts)]

    def embed_query(self, text: str) -> SparseVec:
        """Embed câu hỏi thành một SparseVec."""
        v = next(iter(self._model.query_embed(text)))
        return SparseVec(v.indices.tolist(), v.values.tolist())
