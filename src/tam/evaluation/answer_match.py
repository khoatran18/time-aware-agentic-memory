"""Chỉ số theo chuỗi đáp án (decisions/07 đề xuất 5): bổ sung cho Hit@k theo `chunk_id`, không thay thế.

Hit@k theo `chunk_id` chỉ đúng khi trúng đúng đoạn được gắn nhãn (đoạn chứa vị trí đáp án). Hai chỉ số ở đây hỏi gần hơn với "người đọc
có đủ chất liệu để trả lời không":
- `ans_hit@k`: văn bản top-k có chứa chuỗi đáp án, chunk nào cũng được (cách đo answer recall của truy xuất cho QA mở).
- `ans_valid_hit@k`: có chunk top-k vừa chứa chuỗi đáp án vừa **hợp lệ tại `t_req`** (`start_time <= t_req <= end_time`; `end_time` rỗng là còn
  hiệu lực). Với câu hỏi khoảng `[t_req, t_end]`: chunk hợp lệ nếu khoảng của nó **giao** khoảng hỏi. Chunk không có mốc không tính là hợp lệ
  (cách chặt).
Cả hai là xấp xỉ: có dương tính giả (chuỗi đáp án ngắn và chung) và âm tính giả (cách viết khác của cùng đáp án); `ans_valid_hit@k` còn dựa vào
nhãn thời gian do chính ingestion gán nên chỉ là chỉ số chẩn đoán, không phải con số chính.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from datetime import datetime

from tam.schemas.chunk import Chunk

_NON_WORD = re.compile(r"[^\w\s]")
_SPACES = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Chữ thường, dấu câu thành khoảng trắng, gộp khoảng trắng liền nhau (cách chuẩn hóa của đo answer recall trong DPR)."""
    return _SPACES.sub(" ", _NON_WORD.sub(" ", text.lower())).strip()


def contains_answer(answers: Iterable[str], text: str) -> bool:
    """True nếu MỘT trong các đáp án (đã chuẩn hóa) là chuỗi liên tục trong `text` (đã chuẩn hóa), không dính vào chữ khác.

    Không so từng ký tự rời và không so gần đúng: đáp án "Aston Villa" không khớp đoạn chỉ có "Villa"; đáp án "colonel" không khớp "colonels".
    """
    hay = normalize(text)
    for answer in answers:
        needle = normalize(answer)
        if needle and re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", hay):
            return True
    return False


def is_valid_at(chunk: Chunk, t_req: datetime, t_end: datetime | None = None) -> bool:
    """Chunk có mốc và còn hiệu lực tại `t_req` (hoặc giao khoảng `[t_req, t_end]`); chunk không có `start_time` coi là không hợp lệ."""
    upper = t_end if t_end is not None else t_req
    return chunk.start_time is not None and chunk.start_time <= upper and (chunk.end_time is None or t_req <= chunk.end_time)


def answer_hits(
    answers: Sequence[str], chunks: Sequence[Chunk], t_req: datetime, ks: Sequence[int], t_end: datetime | None = None
) -> tuple[dict[int, float], dict[int, float]]:
    """(`ans_hit`, `ans_valid_hit`) theo từng k: 1.0 nếu có chunk trong top-k thỏa điều kiện, ngược lại 0.0."""
    plain = [contains_answer(answers, c.text) for c in chunks]
    valid = [p and is_valid_at(c, t_req, t_end) for p, c in zip(plain, chunks, strict=True)]
    return ({k: float(any(plain[:k])) for k in ks}, {k: float(any(valid[:k])) for k in ks})
