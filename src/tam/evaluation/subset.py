"""Dựng bộ câu hỏi con từ TimeQA D/test (bộ local/bộ thật) và nhãn `gold_chunk_ids` ở mức chunk, không gọi LLM."""
from __future__ import annotations

import json
import random
import re
from collections import defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from tam.schemas.domains import relation_domain


def read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Đọc file jsonl thành list dict."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def paragraph_spans(context: str, paragraphs: Sequence[dict[str, str]]) -> list[tuple[int, int] | None]:
    """Vị trí [start, end) của từng đoạn trong `context`, tìm tuần tự; không thấy thì None (cursor không nhích)."""
    spans: list[tuple[int, int] | None] = []
    cursor = 0
    for p in paragraphs:
        text = p["text"].strip()
        pos = context.find(text, cursor) if text else -1
        if pos < 0:
            spans.append(None)
            continue
        spans.append((pos, pos + len(text)))
        cursor = pos + len(text)
    return spans


def gold_paragraph_indices(
    spans: Sequence[tuple[int, int] | None], starts: Sequence[int], ends: Sequence[int]
) -> tuple[list[int], list[str]]:
    """Chỉ số đoạn chứa từng cặp [from, end) của đáp án, cùng các cờ cảnh báo.

    Đáp án rơi vào khe giữa các đoạn (tiêu đề mục) thì lấy đoạn kế tiếp, cờ `answer_in_heading`. Đáp án vắt qua nhiều đoạn
    thì lấy đủ các đoạn, cờ `answer_spans_paragraphs`. Không xác định được thì cờ `unmapped`.
    """
    found: list[int] = []
    flags: list[str] = []
    for s, e in zip(starts, ends):
        hit = [i for i, sp in enumerate(spans) if sp and sp[0] < e and s < sp[1]]
        if not hit:
            nxt = next((i for i, sp in enumerate(spans) if sp and sp[0] >= e), None)
            if nxt is None:
                flags.append("unmapped")
                continue
            hit = [nxt]
            flags.append("answer_in_heading")
        elif len(hit) > 1:
            flags.append("answer_spans_paragraphs")
        found.extend(hit)
    return sorted(set(found)), sorted(set(flags))


def group_of(row: dict[str, Any], group_by: str) -> str:
    """Nhóm của một câu: `relation` (P…) hoặc `domain` (suy từ relation theo TOPICS.md)."""
    return row["relation"] if group_by == "relation" else relation_domain(row["relation"])


def sample_cases(
    hard_rows: Sequence[dict[str, Any]], groups: Sequence[str], per_group: int, seed: int, *, group_by: str = "relation"
) -> list[dict[str, Any]]:
    """Mỗi nhóm lấy ngẫu nhiên `per_group` câu (seed cố định, sắp theo idx trước khi lấy để tái lập).

    `group_by="domain"`: mỗi domain lấy đều trên các câu của nó, nên relation phổ biến (vd P54 trong `sports`) chiếm nhiều hơn.
    """
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(hard_rows, key=lambda r: r["idx"]):
        by_group[group_of(row, group_by)].append(row)
    rng = random.Random(seed)
    picked: list[dict[str, Any]] = []
    for g in groups:
        pool = by_group.get(g, [])
        if len(pool) < per_group:
            raise ValueError(f"{g} chỉ có {len(pool)} câu, cần {per_group}")
        picked.extend(rng.sample(pool, per_group))
    return sorted(picked, key=lambda r: r["idx"])


def build_subset(
    dataset_dir: str | Path, *, split: str = "D/test", group_by: str = "relation", groups: Sequence[str],
    per_group: int, seed: int,
) -> dict[str, Any]:
    """Dựng bộ con: các câu (hard + easy cùng idx), trang cần nạp và nhãn chunk đúng."""
    root = Path(dataset_dir)
    hard = read_jsonl(root / f"{split}.hard.jsonl")
    easy = {r["idx"]: r for r in read_jsonl(root / f"{split}.easy.jsonl")}
    chosen = sample_cases(hard, groups, per_group, seed, group_by=group_by)
    wanted = {r["page_id"] for r in chosen}
    pages: dict[str, dict[str, Any]] = {}
    for page in read_jsonl(root / "pages.jsonl"):
        if page["page_id"] in wanted:
            pages[page["page_id"]] = page

    cases = []
    for row in chosen:
        page = pages[row["page_id"]]
        spans = paragraph_spans(page["context"], page["paragraphs"])
        idxs, flags = gold_paragraph_indices(spans, row["from"], row["end"])
        cases.append({
            "idx": row["idx"], "page_id": row["page_id"], "relation": row["relation"],
            "domain": relation_domain(row["relation"]),
            "question_hard": row["question"], "question_easy": easy[row["idx"]]["question"],
            "targets": row["targets"], "time_start": row["time_start"], "time_end": row["time_end"],
            "gold_chunk_ids": [f"{row['page_id']}#{i}" for i in idxs], "flags": flags,
        })
    return {
        "split": split, "seed": seed, "group_by": group_by, "groups": list(groups), "per_group": per_group,
        "n_cases": len(cases), "page_ids": sorted(pages), "cases": cases,
    }


# Dấu hiệu năm trước Công nguyên trong văn bản tiếng Anh ("500 BC", "44 B.C.", "BCE"); xem decisions/05.
BCE_PATTERN = re.compile(r"\b(?:BC|BCE|B\.C\.(?:E\.)?)(?![A-Za-z])")


def mentions_bce(*texts: str) -> bool:
    """True nếu một trong các văn bản có dấu hiệu năm trước Công nguyên."""
    return any(BCE_PATTERN.search(t) for t in texts if t)


def sample_balanced(pool: Sequence[dict[str, Any]], n: int, rng: random.Random) -> list[dict[str, Any]]:
    """Lấy tối đa `n` câu, xoay vòng qua các relation (mỗi lượt một câu ngẫu nhiên của mỗi relation còn câu), để không
    relation lớn lấn hết domain. Pool nhỏ hơn `n` thì lấy hết."""
    by_rel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in sorted(pool, key=lambda r: r["idx"]):
        by_rel[row["relation"]].append(row)
    for rows in by_rel.values():
        rng.shuffle(rows)
    picked: list[dict[str, Any]] = []
    while len(picked) < n and any(by_rel.values()):
        for rel in sorted(by_rel):
            if by_rel[rel] and len(picked) < n:
                picked.append(by_rel[rel].pop())
    return picked


def build_topup_subset(
    dataset_dir: str | Path, *, groups: Sequence[str], per_group: int, seed: int,
    primary: str = "D/test", reserve: str = "D/train",
) -> dict[str, Any]:
    """Bộ thật: mỗi domain `per_group` câu, ưu tiên `primary`, thiếu thì mượn từ `reserve`; bỏ câu trước Công nguyên.

    Câu không xác định được chunk đáp án cũng bị bỏ. Câu bị bỏ vì BC nếu câu hỏi, nhãn thời gian, đáp án hoặc đoạn chứa đáp án có dấu hiệu BC (`mentions_bce`, decisions/05).
    Câu mượn từ `reserve` có `split` = "D/train" và nằm trong `borrowed_from_train`: phải loại khỏi mẫu tinh chỉnh.
    """
    root = Path(dataset_dir)
    pages = {p["page_id"]: p for p in read_jsonl(root / "pages.jsonl")}
    rng = random.Random(seed)
    cases: list[dict[str, Any]] = []
    dropped_bce = {primary: 0, reserve: 0}
    dropped_unmapped = {primary: 0, reserve: 0}
    pools: dict[str, dict[str, list[dict[str, Any]]]] = {}
    easy: dict[str, str] = {}
    for split in (primary, reserve):
        easy.update({r["idx"]: r["question"] for r in read_jsonl(root / f"{split}.easy.jsonl")})
        by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in read_jsonl(root / f"{split}.hard.jsonl"):
            page = pages[row["page_id"]]
            spans = paragraph_spans(page["context"], page["paragraphs"])
            idxs, flags = gold_paragraph_indices(spans, row["from"], row["end"])
            if not idxs:  # không xác định được chunk đáp án: không chấm được
                dropped_unmapped[split] += 1
                continue
            gold_text = " ".join(page["paragraphs"][i]["text"] for i in idxs)
            if mentions_bce(row["question"], str(row["time_start"]), str(row["time_end"]), " ".join(row["targets"]), gold_text):
                dropped_bce[split] += 1
                continue
            row = {**row, "_gold": idxs, "_flags": flags, "_split": split}
            by_domain[relation_domain(row["relation"])].append(row)
        pools[split] = by_domain
    for g in groups:
        chosen = sample_balanced(pools[primary].get(g, []), per_group, rng)
        if len(chosen) < per_group:
            chosen += sample_balanced(pools[reserve].get(g, []), per_group - len(chosen), rng)
        if len(chosen) < per_group:
            raise ValueError(f"{g} chỉ có {len(chosen)} câu hợp lệ, cần {per_group}")
        cases.extend(chosen)
    cases.sort(key=lambda r: r["idx"])
    out = [{
        "idx": r["idx"], "page_id": r["page_id"], "relation": r["relation"], "domain": relation_domain(r["relation"]),
        "split": r["_split"], "question_hard": r["question"], "question_easy": easy[r["idx"]],
        "targets": r["targets"], "time_start": r["time_start"], "time_end": r["time_end"],
        "gold_chunk_ids": [f"{r['page_id']}#{i}" for i in r["_gold"]], "flags": r["_flags"],
    } for r in cases]
    return {
        "split": f"{primary}+{reserve}", "seed": seed, "group_by": "domain", "groups": list(groups), "per_group": per_group,
        "n_cases": len(out), "page_ids": sorted({c["page_id"] for c in out}),
        "borrowed_from_train": [c["idx"] for c in out if c["split"] == reserve], "dropped_bce": dropped_bce,
        "dropped_unmapped": dropped_unmapped, "cases": out,
    }
