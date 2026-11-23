"""Câu hỏi riêng cho cơ chế 3 (questions/mech3/tune) của các chỗ sửa trong pilot -> subset cho run_agent_search.py.
Dùng: m3_mech3_questions.py  -> m3_state/tune/subset_mech3.json (idx = qid, type = <loại sửa>/<kind>)."""
import json, glob
import os
O = "dataset/organized/"
SET = os.environ.get("M3_SET", "tune"); ST = os.environ.get("M3_STATE_NAME", "m3_state")
P = json.load(open(O + f"{ST}/{SET}/pilot.json"))
S = json.load(open(O + f"{ST}/{SET}/subset.json"))["cases"]
pg = {c["edit_id"]: (c["page_id"], c["graph_page"]) for c in S}
pe = {e["edit_id"] for e in P["edits"]}
cases = []
for f in glob.glob(O + f"questions/mech3/{SET}/*.jsonl"):
    for l in open(f):
        if not l.strip():
            continue
        q = json.loads(l)
        if q["edit_id"] in pe and q["edit_id"] in pg:
            pid, gp = pg[q["edit_id"]]
            cases.append(dict(idx=q["qid"], page_id=pid, graph_page=gp, type=f'{q["type"]}/{q["kind"]}', question=q["question"], question_hard=q["question"], edit_id=q["edit_id"], answer=q["answer"], edit_type=q["type"], kind=q["kind"]))
json.dump(dict(source=f"questions/mech3/{SET} lọc theo {ST}/{SET}/pilot.json", cases=cases), open(O + f"{ST}/{SET}/subset_mech3.json", "w"), ensure_ascii=False, indent=1)
print(len(cases), "câu,", len({c["edit_id"] for c in cases}), "chỗ sửa")
