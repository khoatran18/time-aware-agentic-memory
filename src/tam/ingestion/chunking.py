"""Structural chunking + content hash (design 01/02): mỗi đoạn/mục của tài liệu là một chunk."""
from __future__ import annotations

import hashlib
import re

from tam.ingestion.types import RawChunk, RawDoc


def content_hash(text: str) -> str:
    """SHA-256 của văn bản đã chuẩn hóa (gộp khoảng trắng, chữ thường); hash trùng = nội dung trùng."""
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def chunk_document(doc: RawDoc) -> list[RawChunk]:
    """Mỗi section thành một chunk; section rỗng bị bỏ.

    Văn bản chunk có tiêu đề tài liệu và tên mục ở đầu ("Knox Cunningham | Early career\\n..."), vì đoạn đơn lẻ thường chỉ
    nói "he", "the club" và không chứa tên thực thể: thiếu tiêu đề thì cả embedding lẫn BM25 đều không tìm ra.
    `chunk_id = <doc_id>#<chỉ số section>` ổn định giữa các lần chạy nên ghi lại là ghi đè, không nhân đôi.
    """
    chunks = []
    for i, section in enumerate(doc.sections):
        body = section.text.strip()
        if not body:
            continue
        header = doc.title if section.title.strip() in ("", doc.title) else f"{doc.title} | {section.title.strip()}"
        text = f"{header}\n{body}"
        chunks.append(RawChunk(
            chunk_id=f"{doc.doc_id}#{i}", doc_id=doc.doc_id, section_title=section.title, text=text,
            content_hash=content_hash(text),
        ))
    return chunks
