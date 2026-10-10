"""Loader cho `pages.jsonl` của TimeQA enriched: mỗi dòng một trang Wikipedia, `paragraphs` = [{title, text}]."""
from __future__ import annotations

import json
from collections.abc import Collection, Iterator
from pathlib import Path

from tam.ingestion.types import RawDoc, Section


def page_title(page_id: str) -> str:
    """'/wiki/Knox_Cunningham' -> 'Knox Cunningham'."""
    return page_id.removeprefix("/wiki/").replace("_", " ")


def load_pages(
    path: str | Path, page_ids: Collection[str] | None = None, *, source: str = "Wikipedia"
) -> Iterator[RawDoc]:
    """Đọc từng trang; nếu có `page_ids` thì chỉ trả các trang đó. Trang không có đoạn nào bị bỏ qua.

    `source` là nơi phát hành gắn cho mọi trang của file này (mặc định Wikipedia, vì TimeQA là Wikipedia); loader cho
    nguồn khác truyền giá trị riêng. Tài liệu cụ thể nằm ở `RawDoc.doc_id`, không trộn vào `source`.
    """
    wanted = set(page_ids) if page_ids is not None else None
    with open(path, encoding="utf-8") as f:
        for line in f:
            page = json.loads(line)
            if wanted is not None and page["page_id"] not in wanted:
                continue
            sections = tuple(Section(title=p["title"], text=p["text"]) for p in page["paragraphs"])
            if not sections:
                continue
            title = page_title(page["page_id"])
            yield RawDoc(doc_id=page["page_id"], title=title, source=source, sections=sections)
