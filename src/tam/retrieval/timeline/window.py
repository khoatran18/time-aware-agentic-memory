"""Tách khoảng năm [from, to] từ câu hỏi bằng quy tắc (không LLM). Bắt: năm, thập niên ("the 1970s"), early/mid/late, before/after/up to/until/through/between...and/from...to/onward/since/in/during.
Bound nới rộng (bao cả mốc biên) để không loại nhầm mốc đáp án. Trả (từ, đến) dạng chuỗi năm 4 chữ số; None ở phía không giới hạn; (None, None) nếu không thấy khoảng."""
from __future__ import annotations

import re

_TOK = re.compile(r"(?:(early|mid|late)[- ])?(?:the )?(?:(?:beginning|end) of the )?(\d{4})(s?)", re.I)
_PART = {"early": (0, 3), "mid": (4, 6), "late": (7, 9)}


def _span(m: re.Match) -> tuple[int, int]:
    part, year, dec = m.group(1), int(m.group(2)), m.group(3)
    if dec:  # thập niên
        a, b = _PART.get((part or "").lower(), (0, 9))
        return year + a, year + b
    return year, year


def parse_window(q: str) -> tuple[str | None, str | None]:
    toks = [(m, _span(m)) for m in _TOK.finditer(q)]
    toks = [(m, s) for m, s in toks if 1000 <= s[0] <= 2100]
    if not toks:
        return None, None
    pre = lambda m: q[max(0, m.start() - 30):m.start()].lower()
    f = lambda y: None if y is None else f"{y:04d}"
    m1, s1 = toks[0]
    p1 = pre(m1)
    if len(toks) >= 2:
        m2, s2 = toks[1]
        mid = q[m1.end():m2.start()].lower()
        if (re.search(r"\bbetween\b", p1) and "and" in mid) or (re.search(r"\bfrom\b", p1) and re.search(r"\b(to|through|until|and)\b", mid)):
            return f(s1[0]), f(s2[1])
    if re.search(r"\b(before|prior to)\b", p1):
        return None, f(s1[0])
    if re.search(r"\b(up to|until|through)\b", p1):
        return None, f(s1[1])
    if re.search(r"\bafter\b", p1):
        return f(s1[1]), None
    if re.search(r"\b(since|from)\b", p1) or re.search(r"\bonward", q[m1.end():m1.end() + 20].lower()):
        return f(s1[0]), None
    if re.search(r"\b(in|during)\b", p1):
        return f(s1[0]), f(s1[1])
    return None, None
