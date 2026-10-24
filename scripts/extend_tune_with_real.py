"""Bổ sung vào tập tune các câu của bộ data 400 câu (`real`) có trang không nằm trong valid và test_clean (decisions/08, ghi chú 22/10).

Giữ bản tune gốc ở `tune_base_subset.json` (lần đầu chạy tự sao từ `tune_subset.json`); mỗi lần chạy đọc lại bản gốc nên chạy lại cho cùng kết quả. Không đụng `real_subset.json` và mọi kết quả cũ của real. Không gọi LLM.
Ví dụ: python scripts/extend_tune_with_real.py
"""
from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

from tam.evaluation.splits import subset_doc

ROOT = Path(__file__).resolve().parents[1]
EVAL = ROOT / "dataset" / "eval"


def load(name: str) -> dict:
    return json.loads((EVAL / f"{name}_subset.json").read_text(encoding="utf-8"))


def main() -> None:
    base_path = EVAL / "tune_base_subset.json"
    if not base_path.exists():
        shutil.copyfile(EVAL / "tune_subset.json", base_path)
    base = json.loads(base_path.read_text(encoding="utf-8"))
    real, valid, test = load("real"), load("valid"), load("test_clean")
    blocked = set(valid["page_ids"]) | set(test["page_ids"])
    have = {c["idx"] for c in base["cases"]}
    added = [{**c, "source": c.get("source", c["split"])} for c in real["cases"] if c["page_id"] not in blocked and c["idx"] not in have]
    extra = {k: base[k] for k in ("per_domain", "max_per_page", "valid_mode")}
    extra["note"] = f"tune gốc {len(base['cases'])} câu + {len(added)} câu của real có trang không nằm trong valid/test_clean (scripts/extend_tune_with_real.py)"
    extra["from_real"] = sorted(c["idx"] for c in added)
    doc = subset_doc("tune", base["cases"] + added, seed=base["seed"], extra=extra)
    (EVAL / "tune_subset.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    with open(EVAL / "tune_subset_cases.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["idx", "domain", "relation", "source", "question_hard", "targets", "time_start", "time_end", "gold_chunk_ids"])
        for c in doc["cases"]:
            w.writerow([c["idx"], c["domain"], c["relation"], c["source"], c["question_hard"], " | ".join(c["targets"]), c["time_start"], c["time_end"], " ".join(c["gold_chunk_ids"])])
    new_pages = set(doc["page_ids"]) - set(base["page_ids"])
    print(f"tune: {len(base['cases'])} + {len(added)} = {doc['n_cases']} câu; {len(doc['page_ids'])} trang ({len(new_pages)} trang mới cần nạp kho)")
    print("trùng trang valid:", len(set(doc["page_ids"]) & set(valid["page_ids"])), "| trùng test_clean:", len(set(doc["page_ids"]) & set(test["page_ids"])))


if __name__ == "__main__":
    main()
