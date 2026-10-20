"""Hard filter của Cơ chế 1: `invalidated_at IS NULL`, `start_time <= T_req`, facet theo domain_features."""
from __future__ import annotations

from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.stores.vector.base import VectorFilter

# Khóa con của domain_features được index (design 02, mục 2); lọc theo khóa khác sẽ quét toàn bộ nên bị từ chối
FACET_KEYS = frozenset({"domain", "country"})

def to_vector_filter(query: ProfiledQuery, *, exclude_invalidated: bool = True, use_range: bool = False) -> VectorFilter:
    """Dựng VectorFilter từ ProfiledQuery; `query.filters` chỉ được chứa khóa trong FACET_KEYS.

    `use_range=True` (chế độ khoảng, decisions/07): cận trên của `start_time` là `qe` (`query.t_end`, thiếu thì `t_req`) thay vì `t_req`."""
    unknown = set(query.filters) - FACET_KEYS
    if unknown:
        raise ValueError(f"Metadata_Filters chứa khóa không được index: {sorted(unknown)}; cho phép: {sorted(FACET_KEYS)}")
    upper = query.t_end if use_range and query.t_end is not None else query.t_req
    return VectorFilter(t_req=upper, exclude_invalidated=exclude_invalidated, facets=dict(query.filters))


def passes_hard_filter(chunk: Chunk, flt: VectorFilter) -> bool:
    """Kiểm tra bằng Python cùng điều kiện mà store áp ở DB; dùng làm chốt chặn cuối và cho store giả khi test."""
    if flt.undated:
        if chunk.start_time is not None:
            return False
    elif flt.apply_time and (chunk.start_time is None or chunk.start_time > flt.t_req):
        return False
    if flt.exclude_invalidated and chunk.invalidated_at is not None:
        return False
    return all(_facet_matches(chunk.domain_features.get(key), value) for key, value in flt.facets.items())


def _facet_matches(have: object, want: str) -> bool:
    """Facet của chunk có thể là một giá trị hoặc danh sách (domain có tới 3 nhãn): danh sách thì `want` nằm trong nó."""
    return want in have if isinstance(have, list) else have == want
