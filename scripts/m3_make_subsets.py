"""Cơ chế 3: dựng bộ câu hỏi và danh sách trang cho một trạng thái (m3_state*/<tập>/pilot.json). Không gọi LLM.
Ghi trong m3_state*/<tập>/: subset.json (câu timeline = câu cơ chế 2 của các trang, nhãn nhóm dich/cung_chunk/cung_trang, edit_id, edit_type;
lấy từ dataset/eval/v9_graph_tune_subset.json), subset_mech3.json (câu questions/mech3/<tập> của các chỗ sửa), pages.txt.
Dùng: M3_STATE_NAME=m3_state_full python3 scripts/m3_make_subsets.py [--set tune]"""
import argparse, glob, json, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "dataset" / "organized"
M3 = os.environ.get("M3_STATE_NAME", "m3_state")

ap = argparse.ArgumentParser(description=__doc__)
ap.add_argument("--set", default="tune")
a = ap.parse_args()
S = a.set
d = ORG / M3 / S
P = json.loads((d / "pilot.json").read_text(encoding="utf-8"))
edits = P["edits"]
excl = {e["page"] for e in P.get("excluded", [])}
v9 = {c["idx"]: c for c in json.loads((ROOT / "dataset/eval" / f"v9_graph_{S}_subset.json").read_text(encoding="utf-8"))["cases"]}

cases, missing = [], []
for e in edits:
    if e["page"] in excl:
        continue
    for g, rows in e["groups"].items():
        for r in rows:
            idx = f'{e["page"]}:{r["qi"]}'
            if idx in v9:
                cases.append({**v9[idx], "group": g, "edit_id": e["edit_id"], "edit_type": e["type"]})
            else:
                missing.append(idx)
json.dump({"source": f"v9_graph_{S}_subset.json lọc theo {M3}/{S}/pilot.json", "missing_in_v9_subset": missing, "cases": cases}, open(d / "subset.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

import sys
sys.path.insert(0, str(ROOT / "src"))
from tam.tools.graph_tools import page_name
IDX = json.loads((ROOT / "data/text_corpus.index.json").read_text(encoding="utf-8"))
BYNAME = {page_name(k, True): k for k in IDX}  # tên trang chuẩn hóa -> page_id trong index văn bản

pe = {e["edit_id"]: e for e in edits if e["page"] not in excl}
gp = {c["edit_id"]: (c["page_id"], c["graph_page"]) for c in cases}
c3 = []
for f in glob.glob(str(ORG / "questions" / "mech3" / S / "*.jsonl")):
    for l in open(f, encoding="utf-8"):
        if not l.strip():
            continue
        q = json.loads(l)
        if q["edit_id"] in pe:
            e = pe[q["edit_id"]]
            if q["edit_id"] in gp:
                pid, g = gp[q["edit_id"]]
            else:  # trang không có câu timeline: lấy page_id từ index văn bản
                g = e["page"]
                pid = BYNAME[page_name(e["page"], True)]
            c3.append(dict(idx=q["qid"], page_id=pid, graph_page=g, type=f'{q["type"]}/{q["kind"]}', question=q["question"], question_hard=q["question"],
                           edit_id=q["edit_id"], answer=q["answer"], edit_type=q["type"], kind=q["kind"]))
json.dump({"source": f"questions/mech3/{S} lọc theo {M3}/{S}/pilot.json", "cases": c3}, open(d / "subset_mech3.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
(d / "pages.txt").write_text("\n".join(sorted(e["page"] for e in edits if e["page"] not in excl)) + "\n", encoding="utf-8")
print(f"{M3}/{S}: {len(pe)} chỗ sửa, {len(cases)} câu timeline (thiếu trong v9 subset: {len(missing)}), {len(c3)} câu mech3, {len(pe)} trang")
