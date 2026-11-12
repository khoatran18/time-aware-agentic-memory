"""Dựng kho text thuần cho agent search kiểu A (docs/planning/02_AGENT_SEARCH_BASELINE.md). Không gọi LLM, không nạp kho.

Mỗi trang của tune, valid và test_clean (đúng tập trang các bộ con dùng, không thừa) thành một file `.txt` trong `--out`. Mỗi đoạn mở đầu
bằng `[#i]` rồi đúng văn bản chunk mà ingestion tạo ra (`chunking.chunk_document`: tiêu đề trang và mục, rồi nội dung), nên `[#i]` khớp
`chunk_id = <page_id>#<i>`, và agent A với agent B nhìn cùng một văn bản. File chỉ chứa văn bản gốc, không có mốc `start`/`end` hay nhãn
nào do LLM gán. Bảng ánh xạ (tên file, `page_id`, tập) ghi ở `--index`, ngoài thư mục `--out` để công cụ `list_pages` của agent không thấy.

Ví dụ: python scripts/build_text_corpus.py            # ghi data/text_corpus/*.txt và data/text_corpus.index.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.tools.text_corpus import build_corpus, write_index

SPLITS = {"tune": "tune_subset.json", "valid": "valid_subset.json", "test_clean": "test_clean_subset.json"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pages", default=str(ROOT / "dataset/full_dataset/pages.jsonl"))
    ap.add_argument("--eval-dir", default=str(ROOT / "dataset/eval"))
    ap.add_argument("--out", default=str(ROOT / "data/text_corpus"))
    ap.add_argument("--index", default=str(ROOT / "data/text_corpus.index.json"))
    args = ap.parse_args()

    split_of: dict[str, str] = {}
    for split, fname in SPLITS.items():
        for pid in json.loads((Path(args.eval_dir) / fname).read_text(encoding="utf-8"))["page_ids"]:
            if pid in split_of:
                raise SystemExit(f"page_id nằm trong hai tập ({split_of[pid]} và {split}): {pid}")
            split_of[pid] = split

    index = build_corpus(args.pages, split_of, args.out)
    out = Path(args.out)

    missing = sorted(set(split_of) - set(index))
    write_index(index, args.index)
    counts = {s: sum(v["split"] == s for v in index.values()) for s in SPLITS}
    print(f"đã ghi {len(index)} file vào {out} ({counts}); index: {args.index}")
    if missing:
        print(f"CẢNH BÁO: {len(missing)} page_id không có trong pages.jsonl hoặc không có đoạn nào: {missing[:5]}")


if __name__ == "__main__":
    main()
