"""Dựng graph lý tưởng (oracle) và bộ câu hỏi cấu trúc của Cơ chế 2 từ chú thích TimeQA. Không gọi LLM.

    python scripts/build_timeline_gold.py [--subset real] [--predictions output/<lần chạy truy xuất>]

Ghi `dataset/eval/timeline_gold_<subset>.json` (ô và sự kiện), `dataset/eval/timeline_questions_<subset>.jsonl` (câu hỏi, đáp án chuẩn, chunk đáp án,
ngữ cảnh graph, đầu ra lý tưởng của bước sinh) và in thống kê token: graph lý tưởng so với đúng các chunk đáp án và cả trang. Có `--predictions`
thì thêm độ phủ của vector top-k (dùng xếp hạng của chính các câu hỏi điểm-thời-gian trong ô làm xấp xỉ).
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.evaluation.metrics_timeline import event_coverage, score_answer  # noqa: E402
from tam.evaluation.subset import read_jsonl  # noqa: E402
from tam.evaluation.timeline_gold import build_cells, count_tokens, graph_context, make_questions  # noqa: E402

DATA = ROOT / "dataset" / "full_dataset"
EVAL = ROOT / "dataset" / "eval"


def relation_labels() -> dict[str, str]:
    """`P54 -> member of sports team` đọc từ bảng trong RELATIONS.md."""
    labels = {}
    for line in (DATA / "RELATIONS.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(P\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            labels[m.group(1)] = m.group(2)
    return labels


def chunk_text(page: dict, chunk_id: str) -> str:
    return page["paragraphs"][int(chunk_id.rsplit("#", 1)[1])]["text"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", default="real")
    ap.add_argument("--predictions", default=None, help="thư mục lần chạy truy xuất có predictions.jsonl của bộ con này")
    args = ap.parse_args()

    page_ids = set(json.loads((EVAL / f"{args.subset}_subset.json").read_text(encoding="utf-8"))["page_ids"])
    pages = {p["page_id"]: p for p in read_jsonl(DATA / "pages.jsonl") if p["page_id"] in page_ids}
    rows = [r for sp in ("D/test", "D/train", "C/dev", "C/train", "C/test") for r in read_jsonl(DATA / f"{sp}.hard.jsonl") if r["page_id"] in page_ids]
    cells = build_cells(pages, rows, relation_labels())
    cell_by_id = {c["cell_id"]: c for c in cells}

    questions = []
    for cell in cells:
        for q in make_questions(cell):
            ctx = graph_context(cell, q["gold_event_ids"] if q["kind"] in ("first", "last", "successor", "order") else None)
            page = pages[cell["page_id"]]
            q["graph_context"] = ctx
            q["ideal_output"] = {"answer": q["gold_answer"]}
            q["tokens"] = {
                "graph": count_tokens(ctx),
                "gold_chunks": count_tokens("\n".join(chunk_text(page, c) for c in q["gold_chunk_ids"])),
                "page": count_tokens("\n".join(p["text"] for p in page["paragraphs"])),
            }
            questions.append(q)

    EVAL.mkdir(exist_ok=True)
    (EVAL / f"timeline_gold_{args.subset}.json").write_text(json.dumps({"subset": args.subset, "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(EVAL / f"timeline_questions_{args.subset}.jsonl", "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")

    # kiểm tra bộ chấm: đầu ra lý tưởng phải được 1.0 ở mọi chỉ số
    bad = [q["qid"] for q in questions if any(v != 1.0 for k, v in score_answer(q, q["ideal_output"]["answer"]).items() if k not in ("precision", "recall"))]
    print(f"{len(cells)} ô, {sum(c['complete'] for c in cells)} ô đủ chuỗi, {sum(len(c['events']) for c in cells)} sự kiện; tự kiểm chấm: {len(bad)} lỗi {bad[:3]}")
    ev_counts = Counter(min(len(c["events"]), 6) for c in cells)
    print("sự kiện/ô:", dict(sorted(ev_counts.items())))
    print("câu hỏi:", dict(Counter(q["kind"] for q in questions)), "| tin cậy:", sum(q["reliable"] for q in questions), "/", len(questions))

    print("\nToken trung vị theo loại (graph lý tưởng / đúng các chunk đáp án / cả trang) và tỉ lệ graph nhỏ hơn chunk đáp án:")
    for kind in ("list", "count", "first", "last", "successor", "order"):
        qs = [q for q in questions if q["kind"] == kind and q["reliable"]]
        if qs:
            t = {k: statistics.median(q["tokens"][k] for q in qs) for k in ("graph", "gold_chunks", "page")}
            win = sum(q["tokens"]["graph"] < q["tokens"]["gold_chunks"] for q in qs) / len(qs)
            print(f"  {kind:10s} n={len(qs):4d}  graph={t['graph']:6.0f}  chunk_đáp_án={t['gold_chunks']:6.0f}  cả_trang={t['page']:6.0f}  graph<chunk={win:.0%}")

    if args.predictions:
        preds = {r["id"]: r["ranked_ids"] for r in read_jsonl(Path(args.predictions) / "predictions.jsonl")}
        by_cell = defaultdict(list)
        for pid, ranked in preds.items():
            by_cell[pid.rsplit("#", 1)[0]].append(ranked)
        print("\nĐộ phủ sự kiện của vector top-k (xấp xỉ: xếp hạng của câu hỏi điểm-thời-gian của ô; graph lý tưởng = 1.00 theo định nghĩa):")
        for k in (3, 5, 10, 20):
            strict, loose, n = [], [], 0
            for cid, rankeds in by_cell.items():
                cell = cell_by_id.get(cid)
                if not cell or not cell["complete"] or len(cell["events"]) < 3:
                    continue
                for ranked in rankeds:
                    cov = event_coverage(ranked[:k], cell["events"])
                    strict.append(cov["strict"]); loose.append(cov["loose"])
            if strict:
                print(f"  k={k:2d}  chặt={statistics.mean(strict):.2f}  lỏng={statistics.mean(loose):.2f}  (n={len(strict)} lượt trên ô ≥3 sự kiện)")


if __name__ == "__main__":
    main()
