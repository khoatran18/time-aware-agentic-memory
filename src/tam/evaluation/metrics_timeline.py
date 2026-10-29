"""Chỉ số của Cơ chế 2: độ phủ ngữ cảnh, và chấm đầu ra cuối của LLM (EM/F1 cho đáp án đơn, F1 tập hợp và thứ tự cho danh sách, đúng số cho đếm).

Độ phủ đo ngữ cảnh đưa vào LLM (bước truy xuất); chấm đầu ra đo câu trả lời sau bước sinh. Tách hai tầng để biết lỗi do thiếu ngữ cảnh hay do LLM.
"""
from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

from tam.generation.scoring import contains, exact_match, f1_score, normalize


def event_coverage(context_chunk_ids: Sequence[str], events: Sequence[dict[str, Any]]) -> dict[str, float]:
    """Tỉ lệ sự kiện chuẩn mà ngữ cảnh chunk chứa: `strict` khi có đủ mọi chunk của sự kiện, `loose` khi có ít nhất một chunk."""
    if not events:
        return {"strict": 0.0, "loose": 0.0}
    have = set(context_chunk_ids)
    strict = sum(1 for e in events if e["chunk_ids"] and set(e["chunk_ids"]) <= have)
    loose = sum(1 for e in events if have & set(e["chunk_ids"]))
    return {"strict": strict / len(events), "loose": loose / len(events)}


def _match(pred: str, gold: str) -> bool:
    """Hai giá trị coi là một nếu chuẩn hóa bằng nhau, một chuỗi chứa chuỗi kia theo từ, hoặc F1 theo từ từ 0.8."""
    return exact_match(pred, [gold]) == 1.0 or contains(pred, [gold]) == 1.0 or contains(gold, [pred]) == 1.0 or f1_score(pred, [gold]) >= 0.8


def score_list(pred: Sequence[str] | None, gold: Sequence[str]) -> dict[str, float]:
    """Danh sách dự đoán so với danh sách chuẩn (có thứ tự).

    `precision`/`recall`/`f1`: ghép mỗi giá trị chuẩn với tối đa một giá trị dự đoán chưa dùng. `order`: trong các giá trị đã ghép, tỉ lệ cặp
    có thứ tự tương đối đúng (1.0 khi chưa đủ hai giá trị để so). `exact`: đúng cả tập và thứ tự.
    """
    pred = [p for p in (pred or []) if p]
    used: set[int] = set()
    matched: list[tuple[int, int]] = []  # (vị trí chuẩn, vị trí dự đoán)
    for gi, g in enumerate(gold):
        for pi, p in enumerate(pred):
            if pi not in used and _match(p, g):
                used.add(pi)
                matched.append((gi, pi))
                break
    tp = len(matched)
    precision, recall = (tp / len(pred) if pred else 0.0), (tp / len(gold) if gold else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if tp else 0.0
    pairs = [(a, b) for i, a in enumerate(matched) for b in matched[i + 1:]]
    order = sum(1 for a, b in pairs if a[1] < b[1]) / len(pairs) if pairs else 1.0
    return {"precision": precision, "recall": recall, "f1": f1, "order": order, "exact": float(tp == len(gold) == len(pred) and order == 1.0)}


_NUMBER = re.compile(r"\d+")
_WORD_NUMBERS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten".split())}


def parse_count(pred: Any) -> int | None:
    """Đọc số nguyên từ đầu ra (số, chuỗi "3", "three", "3 coaches"); không đọc được -> None."""
    if isinstance(pred, bool):
        return None
    if isinstance(pred, int):
        return pred
    if isinstance(pred, str):
        m = _NUMBER.search(pred)
        if m:
            return int(m.group())
        return next((n for w, n in _WORD_NUMBERS.items() if w in normalize(pred).split()), None)
    return None


def score_answer(question: dict[str, Any], pred: Any) -> dict[str, float]:
    """Chấm đầu ra cuối của LLM cho một câu hỏi cấu trúc (xem `timeline_gold.make_questions`). Từ chối (rỗng/None) tính 0 ở mọi chỉ số."""
    atype, gold = question["answer_type"], question["gold_answer"]
    if atype == "list":
        return score_list(pred if isinstance(pred, list) else None, gold)
    if atype == "count":
        return {"exact": float(parse_count(pred) == gold)}
    text = pred if isinstance(pred, str) else None
    return {"exact": exact_match(text, [gold]), "f1": f1_score(text, [gold]), "contains": contains(text, [gold])}
