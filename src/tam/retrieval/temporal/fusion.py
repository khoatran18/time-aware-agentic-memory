"""Gộp hai nhánh dense + BM25 bằng RRF rồi min-max về [0,1] thành Semantic_Score (docs/design/02, bước 4a)."""
from __future__ import annotations

from collections.abc import Sequence

from tam.schemas.chunk import Chunk
from tam.stores.vector.base import BranchHits, SearchHit


def rrf(rankings: Sequence[Sequence[str]], k: int = 60) -> dict[str, float]:
    """`RRF(d) = Σ 1/(k + rank_i(d))` với rank bắt đầu từ 1; chunk chỉ có ở một nhánh vẫn được giữ.

    Mỗi phần tử của `rankings` là danh sách id đã xếp hạng của một nhánh. Id lặp trong cùng nhánh chỉ tính lần đầu.
    Thứ tự khóa của kết quả là thứ tự gặp đầu tiên, để tie-break tất định.
    """
    if k < 0:
        raise ValueError(f"k phải >= 0, nhận {k}")
    scores: dict[str, float] = {}
    for ranking in rankings:
        seen: set[str] = set()
        rank = 0
        for chunk_id in ranking:
            if chunk_id in seen:
                continue
            seen.add(chunk_id)
            rank += 1
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


def normalize_minmax(scores: Sequence[float]) -> list[float]:
    """`(s - min)/(max - min)`; mọi điểm bằng nhau (hoặc chỉ một phần tử) thì trả 1.0."""
    if not scores:
        return []
    lo, hi = min(scores), max(scores)
    if hi == lo:
        return [1.0] * len(scores)
    return [(s - lo) / (hi - lo) for s in scores]


def fuse(hits: BranchHits, k: int, top_n: int) -> list[tuple[Chunk, float]]:
    """RRF hai nhánh, giữ `top_n` chunk điểm cao nhất, min-max trên đúng tập đó; trả `(chunk, semantic_score)` giảm dần."""
    chunks: dict[str, Chunk] = {}  # chunk_id -> Chunk, lấy bản gặp đầu tiên (dense trước)
    for hit in (*hits.dense, *hits.sparse):
        chunks.setdefault(hit.chunk.chunk_id, hit.chunk)
    fused = rrf([_ids(hits.dense), _ids(hits.sparse)], k)
    ranked = sorted(fused, key=fused.__getitem__, reverse=True)[:top_n]  # sort ổn định: hòa điểm giữ thứ tự gặp
    semantic = normalize_minmax([fused[cid] for cid in ranked])
    return [(chunks[cid], s) for cid, s in zip(ranked, semantic)]


def _ids(hits: list[SearchHit]) -> list[str]:
    """Danh sách chunk_id theo thứ hạng của một nhánh."""
    return [h.chunk.chunk_id for h in hits]
