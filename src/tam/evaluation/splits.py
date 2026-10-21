"""Chia tập tune, valid và test sạch (decisions/08), không gọi LLM.

Quy tắc: không trùng `idx` và không trùng `page_id` giữa các tập; trang của mọi câu D/test, của bộ `real` và bộ `local` bị loại khỏi
tune và valid; test sạch chỉ lấy câu D/test có `idx` và trang chưa nằm trong `real`/`local`. Mỗi domain `per_domain` câu cho tune và valid,
ưu tiên D/train, thiếu thì bù từ C (dev rồi train). Các tập được chia xoay vòng theo trang để cùng tỉ lệ nguồn D/C. Câu được lấy theo trang (tối đa `max_per_page` câu mỗi domain mỗi trang) để ít trang cần nạp kho.
"""
from __future__ import annotations

import random
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from tam.evaluation.subset import gold_paragraph_indices, mentions_bce, paragraph_spans, read_jsonl
from tam.schemas.domains import relation_domain

# Thứ tự nguồn: D trước (do người viết), C (sinh theo mẫu) bù sau
SOURCES = ("D/train", "C/dev", "C/train")


def assign_pages(
    pool: dict[str, dict[str, list[dict[str, Any]]]], sets: Sequence[str], quotas: dict[str, int], sources: Sequence[str],
    *, max_per_page: int, seed: int, allow_short: bool = False,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, str]]:
    """Chia câu cho các tập `sets` sao cho trang chỉ thuộc một tập.

    `pool[domain][source]` = danh sách câu (mỗi câu có `page_id`). Với mỗi tập rồi mỗi domain: duyệt nguồn theo thứ tự `sources`, trang theo thứ tự
    ngẫu nhiên (seed), lấy tối đa `max_per_page` câu của domain ở trang đó cho tới khi đủ `quotas[domain]`. Trả (tập -> danh sách câu, trang -> tập).
    """
    rng = random.Random(seed)
    owner: dict[str, str] = {}
    out: dict[str, list[dict[str, Any]]] = {s: [] for s in sets}
    shuffled: dict[tuple[str, str], list[str]] = {}
    by_page: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = {}
    for dom, srcs in sorted(pool.items()):
        for src in sources:
            pages: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in sorted(srcs.get(src, []), key=lambda r: r["idx"]):
                pages[row["page_id"]].append(row)
            order = sorted(pages)
            rng.shuffle(order)
            shuffled[(dom, src)], by_page[(dom, src)] = order, pages
    for dom in sorted(pool):
        need = {s: quotas[dom] for s in sets}
        turn = 0  # xoay vòng giữa các tập để mỗi tập nhận cùng tỉ lệ nguồn (D/C) và cùng phân bố
        for src in sources:
            for pid in shuffled[(dom, src)]:
                if not any(need.values()):
                    break
                if pid in owner:
                    s = owner[pid]
                    if need[s] <= 0:
                        continue
                else:
                    open_sets = [x for x in sets if need[x] > 0]
                    s = open_sets[turn % len(open_sets)]
                    turn += 1
                rows = by_page[(dom, src)][pid][: min(max_per_page, need[s])]
                owner[pid] = s
                out[s].extend({**r, "_source": src} for r in rows)
                need[s] -= len(rows)
        short = {s: n for s, n in need.items() if n > 0}
        if short and not allow_short:
            raise ValueError(f"{dom}: thiếu câu so với hạn mức {quotas[dom]}: {short}")
    return out, owner


def valid_rows(root: Path, split: str, pages: dict[str, dict[str, Any]], skip_pages: set[str], skip_idx: set[str]) -> dict[str, list[dict[str, Any]]]:
    """Câu hard hợp lệ (xác định được chunk đáp án, không có dấu BC) theo domain; bỏ trang `skip_pages` và `idx` `skip_idx`."""
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in read_jsonl(root / f"{split}.hard.jsonl"):
        if row["page_id"] in skip_pages or row["idx"] in skip_idx:
            continue
        page = pages[row["page_id"]]
        spans = paragraph_spans(page["context"], page["paragraphs"])
        idxs, flags = gold_paragraph_indices(spans, row["from"], row["end"])
        if not idxs:
            continue
        gold_text = " ".join(page["paragraphs"][i]["text"] for i in idxs)
        if mentions_bce(row["question"], str(row["time_start"]), str(row["time_end"]), " ".join(row["targets"]), gold_text):
            continue
        by_domain[relation_domain(row["relation"])].append({**row, "_gold": idxs, "_flags": flags})
    return by_domain


def to_case(row: dict[str, Any], easy: dict[str, str], source: str) -> dict[str, Any]:
    """Một câu ở định dạng của bộ con `real` (thêm `source`)."""
    return {
        "idx": row["idx"], "page_id": row["page_id"], "relation": row["relation"], "domain": relation_domain(row["relation"]),
        "split": source, "source": source, "question_hard": row["question"], "question_easy": easy[row["idx"]],
        "targets": row["targets"], "time_start": row["time_start"], "time_end": row["time_end"],
        "gold_chunk_ids": [f"{row['page_id']}#{i}" for i in row["_gold"]], "flags": row["_flags"],
    }


def subset_doc(name: str, cases: Iterable[dict[str, Any]], *, seed: int, extra: dict[str, Any]) -> dict[str, Any]:
    """Tài liệu bộ con (cùng khuôn `real_subset.json`)."""
    cases = sorted(cases, key=lambda c: c["idx"])
    return {"name": name, "seed": seed, "group_by": "domain", "n_cases": len(cases), "page_ids": sorted({c["page_id"] for c in cases}), **extra, "cases": cases}


def match_distribution(
    rows: Sequence[dict[str, Any]], target: dict[str, int], total: int, *, max_per_page: int, seed: int, min_per_relation: int = 2,
) -> list[dict[str, Any]]:
    """Chọn tối đa `total` câu sao cho phân bố relation bám `target` (relation -> số câu của tập đích), phủ mọi relation của `target` ít nhất `min_per_relation` câu
    nếu còn đủ. Trong mỗi relation ưu tiên trang đã được chọn (giảm số trang phải nạp), mỗi trang tối đa `max_per_page` câu. Phần còn thiếu (relation hết câu)
    được bù bằng câu của các relation khác, theo thứ tự relation của `target` rồi các relation còn lại."""
    rng = random.Random(seed)
    by_rel: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in sorted(rows, key=lambda r: r["idx"]):
        by_rel[r["relation"]].append(r)
    for lst in by_rel.values():
        rng.shuffle(lst)
    n_target = sum(target.values())
    quota = {rel: max(min_per_relation, round(total * c / n_target)) for rel, c in target.items()}
    chosen: list[dict[str, Any]] = []
    used: set[str] = set()
    per_page: dict[str, int] = defaultdict(int)

    def take(rel: str, want: int) -> int:
        got = 0
        # trang đã dùng trước, rồi trang mới
        for prefer in (True, False):
            for r in by_rel.get(rel, []):
                if got >= want or len(chosen) >= total:
                    return got
                if r["idx"] in used or (r["page_id"] in per_page) != prefer or per_page[r["page_id"]] >= max_per_page:
                    continue
                chosen.append(r)
                used.add(r["idx"])
                per_page[r["page_id"]] += 1
                got += 1
        return got

    order = sorted(target, key=lambda x: -target[x])
    for rel in order:  # trước hết phủ mọi relation của tập đích
        take(rel, min_per_relation)
    for rel in order:  # rồi bám tỉ lệ
        take(rel, quota[rel] - sum(x["relation"] == rel for x in chosen))
    for rel in [*sorted(target, key=lambda x: -target[x]), *sorted(set(by_rel) - set(target))]:
        if len(chosen) >= total:
            break
        take(rel, total - len(chosen))
    return chosen


def _qtype(question: str) -> str:
    """Kiểu nêu thời gian của câu hỏi: between | before | after | in | other."""
    q = question.lower()
    return next((k for k in ("between", "before", "after", "in") if re.search(rf"\b{k}\b", q)), "other")


def difficulty_features(row: dict[str, Any], pages: dict[str, dict[str, Any]]) -> dict[str, str]:
    """Đặc trưng thay cho độ khó (chưa có thước đo độ khó thật): relation, kiểu nêu thời gian, khoảng hay mốc, số chunk đáp án,
    cỡ trang (số đoạn), độ dài câu hỏi, vị trí chunk đáp án trong trang (đầu, giữa, cuối)."""
    n_par = len(pages[row["page_id"]]["paragraphs"])
    gold = row["_gold"]
    qlen = len(row["question"].split())
    pos = sum(gold) / len(gold) / max(1, n_par - 1)
    return {
        "relation": row["relation"], "qtype": _qtype(row["question"]),
        "span": "khoảng" if row["time_start"] != row["time_end"] else "mốc",
        "n_gold": "1" if len(gold) == 1 else "2+",
        "page": "<=15" if n_par <= 15 else ("<=30" if n_par <= 30 else ">30"),
        "qlen": "<=11" if qlen <= 11 else ("<=16" if qlen <= 16 else ">16"),
        "pos": "đầu" if pos < 0.33 else ("giữa" if pos < 0.66 else "cuối"),
    }


def pick_similar(
    candidates: Sequence[dict[str, Any]], reference: Sequence[dict[str, Any]], n: int, pages: dict[str, dict[str, Any]], *, seed: int,
    max_per_page: int = 2,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, dict[str, float]]]]:
    """Chọn `n` câu từ `candidates` có đặc trưng độ khó (`difficulty_features`) giống phân bố của `reference`.

    Chọn tham lam: mỗi bước lấy câu làm tổng chênh lệch phân bố từng đặc trưng (so với `reference`) giảm nhiều nhất; hòa thì theo thứ tự ngẫu nhiên (seed).
    Trả (câu đã chọn, báo cáo: đặc trưng -> giá trị -> {tham chiếu, đã chọn, toàn bộ ứng viên} dưới dạng tỉ lệ)."""
    rng = random.Random(seed)
    ref_f = [difficulty_features(r, pages) for r in reference]
    feats = list(ref_f[0])
    ref_dist = {f: Counter(x[f] for x in ref_f) for f in feats}
    order = list(candidates)
    rng.shuffle(order)
    cand_f = {id(r): difficulty_features(r, pages) for r in order}
    chosen: list[dict[str, Any]] = []
    cnt = {f: Counter() for f in feats}
    per_page: Counter = Counter()

    def gap(extra: dict[str, str] | None) -> float:
        k = len(chosen) + (1 if extra else 0)
        total = 0.0
        for f in feats:
            c = cnt[f] + Counter({extra[f]: 1} if extra else {})
            for v in set(ref_dist[f]) | set(c):
                total += abs(c[v] / k - ref_dist[f][v] / len(ref_f))
        return total

    while len(chosen) < n:
        best, best_gap = None, None
        for r in order:
            if r in chosen or per_page[r["page_id"]] >= max_per_page:
                continue
            g = gap(cand_f[id(r)])
            if best_gap is None or g < best_gap - 1e-12:
                best, best_gap = r, g
        if best is None:
            break
        chosen.append(best)
        per_page[best["page_id"]] += 1
        for f in feats:
            cnt[f][cand_f[id(best)][f]] += 1
    all_f = list(cand_f.values())
    report = {}
    for f in feats:
        vals = set(ref_dist[f]) | set(cnt[f]) | {x[f] for x in all_f}
        report[f] = {v: {"tham_chieu": ref_dist[f][v] / len(ref_f), "da_chon": cnt[f][v] / max(1, len(chosen)),
                         "ung_vien": sum(x[f] == v for x in all_f) / max(1, len(all_f))} for v in sorted(vals)}
    return chosen, report
