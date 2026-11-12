"""Chấm các lần chạy agent search ĐÃ CÓ (không gọi LLM): đọc output/<run>/results.jsonl và agent_calls.jsonl.

Chấm theo dòng `Answer:` (không tính phần Basis, nơi câu trả lời hay nhắc lại đáp án) và gán mỗi câu một nhóm:
  correct            dòng Answer chứa đáp án
  refused            dòng Answer nói "cannot be determined"
  wrong_seen         trả lời sai dù chuỗi đáp án đã hiện trong văn bản công cụ (thấy mà không chốt)
  wrong_not_seen     trả lời sai và chuỗi đáp án chưa từng hiện (tìm không ra, hoặc gold không khớp văn bản)
  refused_seen       từ chối dù chuỗi đáp án đã hiện (thấy mà không chốt)
  no_answer          không có câu trả lời (chạm trần)
Khớp chuỗi là so khớp thô, chưa phải LLM judge: một câu trả lời đúng ý nhưng khác chữ sẽ bị tính sai.
Ví dụ: python scripts/score_agent_runs.py 20261112_134606 20261112_134848 20261112_173317 20261112_173317_2
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.generation.scoring import contains, normalize

PRICE = {"in": 0.15, "cache": 0.003, "out": 0.60}  # USD / 1M token, DeepSeek V4.1 Flash giờ thấp điểm (gấp đôi giờ cao điểm)
REFUSAL = re.compile(r"cannot be determined|can't be determined|not enough information|no passage", re.IGNORECASE)


def answer_line(text: str) -> str:
    """Phần sau `Answer:` đến trước `Basis:`/`Type:`; không có nhãn thì lấy cả văn bản."""
    m = re.search(r"Answer:\s*(.*?)(?:\n\s*\n|\n\s*Basis:|\n\s*Type:|$)", text, re.DOTALL | re.IGNORECASE)
    return (m.group(1) if m else text).strip()


def first_seen_steps(run_dir: Path) -> dict[int, int | None]:
    """Từ agent_calls.jsonl (chế độ full): lượt đầu tiên văn bản công cụ chứa đáp án, cho mỗi câu. Cần results.jsonl cùng thư mục."""
    targets = {}
    for line in (run_dir / "results.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        targets[r["i"]] = [g for g in map(normalize, r["targets"]) if g]
    last: dict[int, dict] = {}
    for line in (run_dir / "agent_calls.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r.get("prompt_mode") != "full":
            continue
        q = int(r["query_id"][1:])
        if q not in last or r["step"] >= last[q]["step"]:
            last[q] = r
    out: dict[int, int | None] = {}
    for q, r in last.items():
        step, first = 0, None
        for m in r["prompt"]:
            if m["role"] in ("ai", "assistant"):
                step += 1
            if m["role"] == "tool" and first is None:
                padded = f" {normalize(m['content'])} "
                if any(f" {g} " in padded for g in targets.get(q, [])):
                    first = step
        out[q] = first
    return out


def classify(row: dict, seen_step: int | None) -> str:
    ans = row["answer"]
    if not ans:
        return "no_answer"
    line = answer_line(ans)
    if contains(line, row["targets"]):
        return "correct"
    if REFUSAL.search(line):
        return "refused_seen" if seen_step is not None else "refused"
    return "wrong_seen" if seen_step is not None else "wrong_not_seen"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="tên thư mục trong output/")
    ap.add_argument("--detail", action="store_true", help="in từng câu không đúng")
    args = ap.parse_args()
    print(f"{'run':<22}{'n':>3}{'correct':>8}{'raw':>5}  nhóm lỗi | lượt/câu  in(cache) out  USD")
    for name in args.runs:
        d = ROOT / "output" / name
        rows = [json.loads(line) for line in (d / "results.jsonl").open(encoding="utf-8")]
        seen = first_seen_steps(d)
        cats = {r["i"]: classify(r, seen.get(r["i"])) for r in rows}
        cnt = Counter(cats.values())
        tin = sum(r["input_tokens"] for r in rows)
        cached = sum(r["cached_input_tokens"] for r in rows)
        tout = sum(r["output_tokens"] for r in rows)
        usd = ((tin - cached) * PRICE["in"] + cached * PRICE["cache"] + tout * PRICE["out"]) / 1e6
        errs = ", ".join(f"{k}={v}" for k, v in sorted(cnt.items()) if k != "correct")
        print(f"{name:<22}{len(rows):>3}{cnt['correct']:>8}{sum(r['contains_target'] for r in rows):>5.0f}  {errs or '-'} | {sum(r['steps'] for r in rows) / len(rows):.2f}  "
              f"{tin}({cached * 100 // max(tin, 1)}%) {tout}  {usd:.4f}")
        if args.detail:
            for r in rows:
                if cats[r["i"]] != "correct":
                    print(f"    q{r['i']:<3}{cats[r['i']]:<15}seen_step={seen.get(r['i'])} gold={r['targets']} | {answer_line(r['answer'] or '')[:110]!r}")


if __name__ == "__main__":
    main()
