"""Mở rộng ngữ cảnh theo tài liệu (chunk_id = `<doc_id>#<chỉ số đoạn>`): chunk liền kề (`Doc#12` -> `Doc#11`, `Doc#13`) hoặc chunk cùng trang."""
from __future__ import annotations

from collections.abc import Sequence

PAGE_EXPANDS = ("none", "page", "time")
MAX_PAGE_CHUNKS = 100  # ingestion giữ tối đa 100 đoạn mỗi trang (chỉ số 0..99)


def split_chunk_id(chunk_id: str) -> tuple[str, int] | None:
    """`('/wiki/X', 12)` từ `/wiki/X#12`; None nếu id không có chỉ số đoạn."""
    doc, sep, idx = chunk_id.rpartition("#")
    return (doc, int(idx)) if sep and idx.isdigit() else None


def neighbor_ids(ranked_ids: Sequence[str], window: int) -> list[str]:
    """Id liền kề trong phạm vi `window` mỗi phía của các chunk đã xếp hạng, không gồm chính chúng.

    Thứ tự: theo hạng của chunk gốc, rồi theo khoảng cách (trước rồi sau). Id lặp chỉ giữ lần đầu.
    """
    own = set(ranked_ids)
    out: list[str] = []
    seen: set[str] = set()
    for cid in ranked_ids:
        parts = split_chunk_id(cid)
        if parts is None:
            continue
        doc, idx = parts
        for d in range(1, window + 1):
            for j in (idx - d, idx + d):
                nid = f"{doc}#{j}"
                if j >= 0 and nid not in own and nid not in seen:
                    seen.add(nid)
                    out.append(nid)
    return out


def top_pages(ranked_ids: Sequence[str], page_top: int) -> dict[str, list[int]]:
    """Tối đa `page_top` trang đầu tiên xuất hiện trong danh sách xếp hạng -> chỉ số các chunk của trang đó nằm trong danh sách (theo hạng)."""
    pages: dict[str, list[int]] = {}
    for cid in ranked_ids:
        parts = split_chunk_id(cid)
        if parts is None:
            continue
        doc, idx = parts
        if doc not in pages and len(pages) >= page_top:
            continue
        pages.setdefault(doc, []).append(idx)
    return pages


def page_candidate_ids(ranked_ids: Sequence[str], page_top: int) -> dict[str, list[str]]:
    """Với mỗi trang trong `top_pages`: id mọi chunk còn lại của trang (`#0..#99`), không gồm chunk đã có trong `ranked_ids`.

    Sắp theo khoảng cách chỉ số tới chunk gần nhất của trang đã có trong danh sách, hòa thì chỉ số nhỏ trước."""
    own = set(ranked_ids)
    out: dict[str, list[str]] = {}
    for doc, have in top_pages(ranked_ids, page_top).items():
        idxs = sorted((j for j in range(MAX_PAGE_CHUNKS) if f"{doc}#{j}" not in own), key=lambda j: (min(abs(j - i) for i in have), j))
        out[doc] = [f"{doc}#{j}" for j in idxs]
    return out
