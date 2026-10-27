"""Chấm câu trả lời ngắn: EM, F1 theo từ và `contains`, so với danh sách đáp án (lấy điểm cao nhất).

Chuẩn hóa theo SQuAD: chữ thường, bỏ dấu câu, bỏ mạo từ a/an/the, gộp khoảng trắng. Từ chối (answer rỗng/None) được tính 0 ở mọi chỉ số;
tỉ lệ từ chối được báo riêng ở scripts/generate_answers.py.
"""
from __future__ import annotations

import re
import string
import unicodedata
from collections import Counter

_ARTICLES = re.compile(r"\b(a|an|the)\b")
_PUNCT = set(string.punctuation) | {"“", "”", "‘", "’", "–", "—"}


def normalize(text: str) -> str:
    """Chữ thường, bỏ dấu phụ (Köln -> koln), bỏ dấu câu và mạo từ, gộp khoảng trắng."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = "".join(ch if ch not in _PUNCT else " " for ch in text)
    return " ".join(_ARTICLES.sub(" ", text).split())


def exact_match(pred: str | None, golds: list[str]) -> float:
    if not pred:
        return 0.0
    p = normalize(pred)
    return float(bool(p) and any(p == normalize(g) for g in golds))


def _f1(pred: str, gold: str) -> float:
    p, g = normalize(pred).split(), normalize(gold).split()
    common = sum((Counter(p) & Counter(g)).values())
    if not p or not g or common == 0:
        return 0.0
    precision, recall = common / len(p), common / len(g)
    return 2 * precision * recall / (precision + recall)


def f1_score(pred: str | None, golds: list[str]) -> float:
    return max((_f1(pred, g) for g in golds), default=0.0) if pred else 0.0


def contains(pred: str | None, golds: list[str]) -> float:
    """1.0 nếu câu trả lời chứa trọn một đáp án (theo từ, sau chuẩn hóa)."""
    if not pred:
        return 0.0
    p = f" {normalize(pred)} "
    return float(any(g and f" {g} " in p for g in map(normalize, golds)))
