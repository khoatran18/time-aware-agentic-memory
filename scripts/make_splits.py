"""Tạo bộ con tune, valid và test sạch (decisions/08) từ TimeQA, ghi vào dataset/eval/. Không gọi LLM, không nạp kho.

Tune/valid: mỗi domain `--per-domain` câu, ưu tiên D/train, thiếu thì bù C (dev rồi train). Test sạch: câu D/test có idx chưa nằm trong bộ real/local (trang có thể trùng; `--clean-exclude-seen-pages` loại cả trang).
Ví dụ: python scripts/make_splits.py            # ghi tune_subset.json, valid_subset.json, test_clean_subset.json và CSV
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tam.evaluation.splits import (
    SOURCES,
    assign_pages,
    match_distribution,
    pick_similar,
    subset_doc,
    to_case,
    valid_rows,
)
from tam.evaluation.subset import read_jsonl
from tam.schemas.domains import relation_domain

DOMAINS = ["business", "sports", "career", "person", "politics", "place", "media_arts", "military"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-domain", type=int, default=50)
    ap.add_argument("--max-per-page", type=int, default=5, help="số câu tối đa của một domain lấy từ một trang")
    ap.add_argument("--clean-exclude-seen-pages", action="store_true", help="test sạch loại cả trang đã nằm trong real/local (nghiêm hơn, ít câu hơn); mặc định chỉ loại idx")
    ap.add_argument("--valid-mode", choices=["pooled", "match-test", "balanced"], default="pooled",
                    help="pooled: gộp D/train và D/test (cùng phân phối), test sạch cân bằng domain tối đa --test-per-domain câu (military, media_arts lấy từ D/train), tune cân bằng, valid là phần D còn lại bám relation của test; match-test: valid chỉ lấy D/train, bám phân bố relation của test_clean và phủ mọi relation của nó (domain không cân bằng); balanced: tune và valid cân bằng domain, bù C")
    ap.add_argument("--test-per-domain", type=int, default=50, help="chế độ pooled: số câu tối đa mỗi domain của test sạch")
    ap.add_argument("--valid-size", type=int, default=400)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dataset-dir", default=str(ROOT / "dataset" / "full_dataset"))
    ap.add_argument("--out-dir", default=str(ROOT / "dataset" / "eval"))
    args = ap.parse_args()

    root, out_dir = Path(args.dataset_dir), Path(args.out_dir)
    pages = {p["page_id"]: p for p in read_jsonl(root / "pages.jsonl")}
    seen_idx, seen_pages = set(), set()
    for name in ("real", "local"):
        doc = json.loads((out_dir / f"{name}_subset.json").read_text(encoding="utf-8"))
        seen_idx |= {c["idx"] for c in doc["cases"]}
        seen_pages |= set(doc["page_ids"])
    test_pages = {r["page_id"] for r in read_jsonl(root / "D" / "test.hard.jsonl")}
    easy: dict[str, str] = {}
    for sub in ("D/train", "D/test", "C/dev", "C/train"):
        group, split = sub.split("/")
        easy.update({r["idx"]: r["question"] for r in read_jsonl(root / group / f"{split}.easy.jsonl")})

    skip_pages = test_pages | seen_pages
    pool: dict[str, dict[str, list]] = {d: {} for d in DOMAINS}
    for src in SOURCES:
        group, split = src.split("/")
        for dom, rows in valid_rows(root / group, split, pages, skip_pages, seen_idx).items():
            if dom in pool:
                pool[dom][src] = rows
    avail = {d: {s: len(r) for s, r in pool[d].items()} for d in DOMAINS}
    quotas = {d: args.per_domain for d in DOMAINS}
    clean_rows = valid_rows(root / "D", "test", pages, set(seen_pages) if args.clean_exclude_seen_pages else set(), seen_idx)
    clean = [r for rows in clean_rows.values() for r in rows]
    fill_report: dict = {}
    if args.valid_mode == "pooled":
        d_pool: dict[str, dict[str, list]] = {d: {} for d in DOMAINS}
        for split in ("test", "train"):
            for dom, rows in valid_rows(root / "D", split, pages, set(), seen_idx).items():
                if dom in d_pool:
                    d_pool[dom][f"D/{split}"] = rows
        test_sets, _ = assign_pages(d_pool, ["test"], {d: args.test_per_domain for d in DOMAINS}, ("D/test", "D/train"),
                                    max_per_page=args.max_per_page, seed=args.seed, allow_short=True)
        test_rows = test_sets["test"]
        for dom in DOMAINS:  # domain thiếu câu D thì bù từ C, chọn câu có đặc trưng độ khó giống câu D của domain đó
            short = args.test_per_domain - sum(1 for r in test_rows if r["relation"] and relation_domain(r["relation"]) == dom)
            if short <= 0:
                continue
            blocked_ = {r["page_id"] for r in test_rows}
            ids_ = {r["idx"] for r in test_rows}
            cands = []
            for src in ("C/dev", "C/train", "C/test"):
                g_, s_ = src.split("/")
                cands += [dict(r, _source=src) for r in valid_rows(root / g_, s_, pages, blocked_, seen_idx | ids_).get(dom, [])]
            ref = [r for rows in d_pool[dom].values() for r in rows]
            picked, rep = pick_similar(cands, ref, short, pages, seed=args.seed)
            test_rows += picked
            fill_report[dom] = {"them_tu_C": len(picked), "so_ung_vien": len(cands), "so_cau_D_tham_chieu": len(ref), "phan_bo": rep}
            print(f"{dom}: thiếu {short} câu D, bù {len(picked)} câu C (từ {len(cands)} ứng viên), nguồn {dict(Counter(r['_source'] for r in picked))}")
        test_pages_ = {r["page_id"] for r in test_rows}
        test_ids = {r["idx"] for r in test_rows}
        full: dict[str, dict[str, list]] = {d: {} for d in DOMAINS}
        for src in ("D/test", "D/train", "C/dev", "C/train"):
            group, split = src.split("/")
            for dom, rows in valid_rows(root / group, split, pages, test_pages_, seen_idx | test_ids).items():
                if dom in full:
                    full[dom][src] = rows
        left = [dict(r, _source=src) for d in DOMAINS for src in ("D/test", "D/train") for r in full[d].get(src, [])]
        target = Counter(r["relation"] for r in test_rows)
        valid_rows_ = match_distribution(left, dict(target), args.valid_size, max_per_page=args.max_per_page, seed=args.seed)
        v_pages, v_ids = {r["page_id"] for r in valid_rows_}, {r["idx"] for r in valid_rows_}
        rest = {d: {s: [r for r in rows if r["page_id"] not in v_pages and r["idx"] not in v_ids] for s, rows in full[d].items()} for d in DOMAINS}
        tune_sets, _ = assign_pages(rest, ["tune"], quotas, ("D/test", "D/train", "C/dev", "C/train"), max_per_page=args.max_per_page,
                                    seed=args.seed, allow_short=True)
        tune_rows = tune_sets["tune"]
        sets = {"tune": tune_rows, "valid": valid_rows_}
        clean = test_rows
        print(f"pooled: test {len(test_rows)} câu (nguồn {dict(Counter(r['_source'] for r in test_rows))}), valid {len(valid_rows_)} câu bám relation của test; "
              f"relation test chưa phủ ở valid: {sorted(set(target) - {r['relation'] for r in valid_rows_}) or 'không'}")
    elif args.valid_mode == "balanced":
        sets, _ = assign_pages(pool, ["tune", "valid"], quotas, SOURCES, max_per_page=args.max_per_page, seed=args.seed)
    else:
        target = Counter(r["relation"] for r in clean)
        d_rows = [dict(r, _source="D/train") for d in DOMAINS for r in pool[d].get("D/train", [])]
        d_rows += [dict(r, _source="D/train") for r in valid_rows(root / "D", "train", pages, skip_pages, seen_idx).get("other", [])]
        valid_rows_ = match_distribution(d_rows, dict(target), args.valid_size, max_per_page=args.max_per_page, seed=args.seed)
        valid_pages = {r["page_id"] for r in valid_rows_}
        rest = {d: {s: [r for r in rows if r["page_id"] not in valid_pages] for s, rows in pool[d].items()} for d in DOMAINS}
        tune_sets, _ = assign_pages(rest, ["tune"], quotas, SOURCES, max_per_page=args.max_per_page, seed=args.seed)
        sets = {"tune": tune_sets["tune"], "valid": valid_rows_}
        missing = sorted(set(target) - {r["relation"] for r in valid_rows_})
        print(f"valid bám test_clean: {len(valid_rows_)} câu; relation của test_clean chưa được phủ: {missing or 'không'}")

    docs = {}
    for name, rows in sets.items():
        docs[name] = subset_doc(name, [to_case(r, easy, r["_source"]) for r in rows], seed=args.seed,
                                extra={"per_domain": args.per_domain, "max_per_page": args.max_per_page, "valid_mode": args.valid_mode})
    docs["test_clean"] = subset_doc("test_clean", [to_case(r, easy, r.get("_source", "D/test")) for r in clean], seed=args.seed,
                                    extra={"note": "chạy MỘT lần với cấu hình đã khóa", "bu_tu_C": fill_report})

    # kiểm tra: không trùng idx và không trùng trang giữa các tập (kể cả với real/local)
    ids = {n: {c["idx"] for c in d["cases"]} for n, d in docs.items()}
    pgs = {n: set(d["page_ids"]) for n, d in docs.items()}
    names = list(docs)
    for i, a in enumerate(names):
        assert not ids[a] & seen_idx, f"{a} trùng idx với real/local"
        assert args.valid_mode == "pooled" or (a == "test_clean" and not args.clean_exclude_seen_pages) or not pgs[a] & seen_pages, f"{a} trùng trang với real/local"
        for b in names[i + 1:]:
            assert not ids[a] & ids[b], f"{a} và {b} trùng idx"
            assert not pgs[a] & pgs[b], f"{a} và {b} trùng trang"

    for name, d in docs.items():
        path = out_dir / f"{name}_subset.json"
        path.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        with open(out_dir / f"{name}_subset_cases.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["idx", "domain", "relation", "source", "question_hard", "targets", "time_start", "time_end", "gold_chunk_ids"])
            for c in d["cases"]:
                w.writerow([c["idx"], c["domain"], c["relation"], c["source"], c["question_hard"], " | ".join(c["targets"]), c["time_start"], c["time_end"], " ".join(c["gold_chunk_ids"])])
        chunks = sum(len(pages[p]["paragraphs"]) for p in d["page_ids"])
        print(f"{name}: {d['n_cases']} câu, {len(d['page_ids'])} trang, ~{chunks} đoạn; domain {dict(Counter(c['domain'] for c in d['cases']))}; nguồn {dict(Counter(c['source'] for c in d['cases']))}")
    print("Còn lại trong kho ứng viên (sau khi loại trang/idx đã thấy), theo domain × nguồn:", json.dumps(avail))


if __name__ == "__main__":
    main()
