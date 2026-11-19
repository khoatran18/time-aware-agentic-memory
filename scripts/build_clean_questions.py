"""Gộp mọi đợt câu hỏi đã qua kiểm LLM-trả-lời (*.final.jsonl) của một tập thành <prefix>.final.jsonl (bỏ trùng, sửa dấu vết token hóa 'XYZs' -> "XYZ's").
Sau đó chạy: python scripts/audit_questions.py --split tune --prefix <prefix>  -> <prefix>.clean.jsonl (bộ sạch sau kiểm mơ hồ).
Chạy: python scripts/build_clean_questions.py --split tune --prefix questions_v7 --parts questions questions_A2 questions_manual ...
Chú ý: đợt 'questions' cũ có câu A bản 2 câu; giữ cả hai (khác câu, bỏ trùng theo (edit_id, câu hỏi))."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ap = argparse.ArgumentParser()
ap.add_argument("--split", default="tune")
ap.add_argument("--prefix", default="questions_v7")
ap.add_argument("--parts", nargs="+", required=True)
a = ap.parse_args()
d = ROOT / "dataset" / "organized" / "past" / a.split
seen, out = set(), []
for p in a.parts:
    f = d / f"{p}.final.jsonl"
    for l in filter(str.strip, f.read_text(encoding="utf-8").splitlines()):
        r = json.loads(l)
        r["question"] = r["question"].replace("CBSs", "CBS's")
        k = (r["edit_id"], r["question"].lower())
        if k not in seen:
            seen.add(k)
            out.append(r)
(d / f"{a.prefix}.final.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out) + "\n", encoding="utf-8")
print("gộp", len(out), "câu từ", a.parts)
