"""Dựng "graph lý tưởng" (oracle) của Cơ chế 2 từ chú thích câu hỏi TimeQA và sinh câu hỏi cấu trúc có đáp án xác định. Không gọi LLM.

Đơn vị là **ô** = (trang, quan hệ). Mỗi câu hỏi TimeQA của ô cho một cửa sổ thời gian (`time_start`..`time_end`), các giá trị đúng (`targets`) và vị trí
đáp án trong ngữ cảnh. Gộp theo giá trị ta có sự kiện: giá trị, khoảng thời gian (hợp các cửa sổ chứa giá trị đó), chunk chứa đáp án.
Khoảng thời gian chỉ là **xấp xỉ** (biên của cửa sổ chú thích, không phải ngày thật) và dòng thời gian có thể thiếu đoạn (`q_index` không liên tục),
nên mỗi ô có cờ `complete` và báo cáo chính chỉ dùng ô `complete`. Xem `docs/eval/08_TIMELINE_EVAL_DESIGN.md`.
"""
from __future__ import annotations

import itertools
import re
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

from tam.evaluation.subset import gold_paragraph_indices, paragraph_spans
from tam.generation.scoring import normalize

_MONTHS = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), start=1)}


def month_index(text: str, *, end: bool = False) -> int | None:
    """"May 1997" -> 1997*12+5; chỉ có năm: đầu năm (tháng 1) hoặc cuối năm (tháng 12) nếu `end`; không đọc được -> None."""
    parts = text.split()
    try:
        if len(parts) == 2 and parts[0] in _MONTHS:
            return int(parts[1]) * 12 + _MONTHS[parts[0]]
        if len(parts) == 1:
            return int(parts[0]) * 12 + (12 if end else 1)
    except ValueError:
        return None
    return None


def month_label(idx: int | None) -> str:
    if idx is None:
        return "?"
    year, month = divmod(idx - 1, 12)
    return f"{list(_MONTHS)[month]} {year}"


def build_cells(pages: dict[str, dict[str, Any]], rows: Sequence[dict[str, Any]], labels: dict[str, str]) -> list[dict[str, Any]]:
    """Gộp các dòng câu hỏi (mỗi `idx` một dòng, bỏ trùng C/D) thành các ô với danh sách sự kiện đã sắp theo thời gian."""
    by_cell: dict[tuple[str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_cell[(row["page_id"], row["relation"])].setdefault(row["q_index"], row)

    cells = []
    spans_cache: dict[str, list] = {}
    for (page_id, relation), qmap in sorted(by_cell.items()):
        page = pages[page_id]
        spans = spans_cache.setdefault(page_id, paragraph_spans(page["context"], page["paragraphs"]))
        events: dict[str, dict[str, Any]] = {}
        for q_index, row in sorted(qmap.items()):
            lo, hi = month_index(row["time_start"]), month_index(row["time_end"], end=True)
            for ans in row["answers"]:
                key = normalize(ans["answer"])
                ev = events.setdefault(key, {
                    "value": ans["answer"], "start": lo, "end": hi, "chunk_ids": set(), "q_indexes": [], "flags": set()})
                if lo is not None and (ev["start"] is None or lo < ev["start"]):
                    ev["start"] = lo
                if hi is not None and (ev["end"] is None or hi > ev["end"]):
                    ev["end"] = hi
                idxs, flags = gold_paragraph_indices(spans, [ans["from"]], [ans["end"]])
                ev["chunk_ids"].update(f"{page_id}#{i}" for i in idxs)
                ev["flags"].update(flags)
                ev["q_indexes"].append(q_index)
        ordered = sorted(events.values(), key=lambda e: (e["start"] or 0, e["end"] or 0, e["value"]))
        q_idx = sorted(qmap)
        cells.append({
            "cell_id": f"{page_id}#{relation}", "page_id": page_id, "relation": relation, "relation_label": labels.get(relation, relation),
            "complete": q_idx == list(range(len(q_idx))), "n_questions": len(q_idx),
            "events": [{**e, "start_label": month_label(e["start"]), "end_label": month_label(e["end"]),
                        "chunk_ids": sorted(e["chunk_ids"]), "q_indexes": sorted(set(e["q_indexes"])), "flags": sorted(e["flags"])}
                       for e in ordered],
        })
    return cells


def entity_name(page_id: str) -> str:
    return re.sub(r"_", " ", page_id.removeprefix("/wiki/"))


def make_questions(cell: dict[str, Any]) -> list[dict[str, Any]]:
    """Câu hỏi cấu trúc có đáp án xác định từ dòng thời gian của ô. Ô có dưới 2 giá trị khác nhau thì không sinh câu nào.

    Loại câu: `list` (liệt kê theo thứ tự), `count`, `first`, `last`, `order` (A trước hay B trước), `successor` (kế nhiệm liền kề).
    Chỉ sinh `successor`/`last` khi ô `complete` (nếu thiếu đoạn thì "ngay sau" và "gần nhất" không đáng tin).
    """
    events, label, name = cell["events"], cell["relation_label"], entity_name(cell["page_id"])
    if len(events) < 2:
        return []
    values = [e["value"] for e in events]

    def q(kind: str, text: str, answer: Any, atype: str, event_ids: list[int]) -> dict[str, Any]:
        chunks = sorted({c for i in event_ids for c in events[i]["chunk_ids"]})
        return {"qid": f"{cell['cell_id']}#{kind}{'-' + str(event_ids[0]) if kind in ('successor', 'order') else ''}",
                "cell_id": cell["cell_id"], "kind": kind, "question": text, "gold_answer": answer, "answer_type": atype,
                "gold_event_ids": event_ids, "gold_chunk_ids": chunks, "reliable": cell["complete"]}

    all_ids = list(range(len(events)))
    out = [
        q("list", f"List all values of '{label}' for {name} in chronological order.", values, "list", all_ids),
        q("count", f"How many different values of '{label}' has {name} had?", len(values), "count", all_ids),
        q("first", f"What was the earliest known value of '{label}' for {name}?", values[0], "entity", [0]),
    ]
    if cell["complete"]:
        out.append(q("last", f"What is the latest known value of '{label}' for {name}?", values[-1], "entity", [len(events) - 1]))
        for i, j in itertools.pairwise(all_ids):
            if events[i]["q_indexes"][-1] + 1 == events[j]["q_indexes"][0]:
                out.append(q("successor", f"For {name}, what '{label}' came right after '{values[i]}'?", values[j], "entity", [i, j]))
    for i, j in itertools.combinations(all_ids, 2):
        if events[i]["end"] is not None and events[j]["start"] is not None and events[i]["end"] <= events[j]["start"]:
            out.append(q("order", f"For {name}, which came first as '{label}': '{values[j]}' or '{values[i]}'?", values[i], "entity", [i, j]))
            break
    return out


def graph_context(cell: dict[str, Any], event_ids: Sequence[int] | None = None) -> str:
    """Văn bản ngữ cảnh mà graph đưa cho LLM: một dòng mỗi sự kiện (giá trị, khoảng thời gian), theo thứ tự thời gian."""
    ids = range(len(cell["events"])) if event_ids is None else sorted(event_ids)
    lines = [f"{cell['relation_label']} of {entity_name(cell['page_id'])}:"]
    for i in ids:
        e = cell["events"][i]
        lines.append(f"- {e['value']} ({e['start_label']} to {e['end_label']})")
    return "\n".join(lines)


def count_tokens(text: str) -> int:
    """Ước lượng token bằng số ký tự chia 4 (không phụ thuộc tokenizer cụ thể); chỉ dùng để so sánh tương đối."""
    return max(1, round(len(text) / 4))
