"""get_embedder(cfg): đọc tên profile ở embedding.dense / embedding.sparse, tra embedding.profiles.<role> để lấy provider +
model_id, chọn class theo `provider`, ghép thành Embedder cho store.

THÊM PROVIDER MỚI (vd OpenAI): viết class kế thừa DenseEmbedder trong providers/openai.py, dán @register_dense("openai")
lên class, thêm một dòng import vào providers/__init__.py. Factory không phải sửa.
"""
from __future__ import annotations

from typing import Any

from tam.config.loader import Config
from tam.embedding import providers as _providers  # noqa: F401  (nạp provider để chúng tự đăng ký)
from tam.embedding.base import DenseEmbedder, Embedder, SparseEmbedder, SparseVec
from tam.embedding.registry import DENSE_PROVIDERS, SPARSE_PROVIDERS


class HybridEmbedder(Embedder):
    """Ghép một dense và một sparse thành `Embedder` mà QdrantStore dùng. Chỉ chuyển tiếp lời gọi."""

    def __init__(self, dense: DenseEmbedder, sparse: SparseEmbedder) -> None:
        self._dense = dense
        self._sparse = sparse
        self.dense_dim = dense.dim

    def embed_dense(self, texts: list[str]) -> list[list[float]]:
        """Chuyển cho dense.embed (lô tài liệu)."""
        return self._dense.embed(texts)

    def embed_sparse(self, texts: list[str]) -> list[SparseVec]:
        """Chuyển cho sparse.embed (lô tài liệu)."""
        return self._sparse.embed(texts)

    def embed_dense_query(self, text: str) -> list[float]:
        """Chuyển cho dense.embed_query (câu hỏi)."""
        return self._dense.embed_query(text)

    def embed_sparse_query(self, text: str) -> SparseVec:
        """Chuyển cho sparse.embed_query (câu hỏi)."""
        return self._sparse.embed_query(text)


def _profile(cfg: Config, role: str) -> dict[str, Any]:
    """Lấy profile mà `embedding.<role>` (role = "dense" | "sparse") đang trỏ tới, dưới dạng dict."""
    name = cfg.embedding[role]
    profiles = cfg.embedding.profiles[role]
    if name not in profiles:
        raise ValueError(f"embedding.{role}={name!r} không có trong embedding.profiles.{role}; hiện có: {sorted(profiles)}")
    return profiles[name].to_dict(masked=False)


def _build(role: str, table: dict[str, Any], profile: dict[str, Any]):
    """Tra `profile["provider"]` trong `table` rồi gọi `from_profile`; provider lạ thì báo lỗi kèm danh sách có sẵn."""
    name = profile.get("provider")
    if name not in table:
        raise ValueError(f"Profile của embedding.{role} có provider={name!r} chưa hỗ trợ; hiện có: {sorted(table)}")
    return table[name].from_profile(profile)


def get_dense(cfg: Config) -> DenseEmbedder:
    """Tạo embedder dense từ profile mà `embedding.dense` chọn."""
    return _build("dense", DENSE_PROVIDERS, _profile(cfg, "dense"))


def get_sparse(cfg: Config) -> SparseEmbedder:
    """Tạo embedder sparse từ profile mà `embedding.sparse` chọn."""
    return _build("sparse", SPARSE_PROVIDERS, _profile(cfg, "sparse"))


def get_embedder(cfg: Config) -> HybridEmbedder:
    """Điểm vào chính: tạo cả dense và sparse từ config rồi ghép lại, sẵn để đưa vào QdrantStore."""
    return HybridEmbedder(get_dense(cfg), get_sparse(cfg))
