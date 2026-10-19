"""Dựng bộ câu hỏi con (mặc định: bộ local) từ TimeQA D/test và ghi ra JSON. Không gọi LLM."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.evaluation.subset import build_subset

# (nhóm theo, danh sách nhóm, số câu mỗi nhóm). local: 8 domain × 5 (bỏ `other`, chỉ 5 câu trên cả D/test); real: 15 relation × 20
PRESETS = {
    "local": ("domain", ["business", "sports", "career", "person", "politics", "place", "media_arts", "military"], 5),
    "real": ("relation", ["P54", "P488", "P39", "P108", "P127", "P26", "P1448", "P937", "P102", "P137", "P551", "P463",
                          "P4791", "P27", "P69"], 20),
}


def main() -> None:
    """Đọc tham số, dựng bộ con, ghi file và in tóm tắt."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", choices=PRESETS, default="local")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dataset-dir", default=str(ROOT / "dataset" / "full_dataset"))
    ap.add_argument("--out", default=None, help="mặc định dataset/eval/<subset>_subset.json")
    args = ap.parse_args()

    group_by, groups, per_group = PRESETS[args.subset]
    data = build_subset(args.dataset_dir, group_by=group_by, groups=groups, per_group=per_group, seed=args.seed)
    out = Path(args.out) if args.out else ROOT / "dataset" / "eval" / f"{args.subset}_subset.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    flags = Counter(f for c in data["cases"] for f in c["flags"])
    multi = sum(len(c["gold_chunk_ids"]) > 1 for c in data["cases"])
    print(f"Ghi {out}: {data['n_cases']} câu, {len(data['page_ids'])} trang, seed={args.seed}")
    print(f"Câu có nhiều chunk đúng: {multi}; cờ: {dict(flags) or 'không'}")


if __name__ == "__main__":
    main()
