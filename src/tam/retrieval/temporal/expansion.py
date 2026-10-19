"""Mở rộng sang chunk liền kề cùng tài liệu: `Doc#12` -> `Doc#11`, `Doc#13` (chunk_id = `<doc_id>#<chỉ số đoạn>`)."""
from __future__ import annotations

from collections.abc import Sequence


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
