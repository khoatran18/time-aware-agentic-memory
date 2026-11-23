"""Phân tích agent đầy đủ công cụ trên câu mech3: agent có dùng graph (timeline) không, hay trả lời từ văn bản/vector?
Dùng: m3_agent_tool_usage.py <tên>=<thư mục output> ...   (chấm bằng m3_mech3_score.match; không gọi LLM)
Mỗi câu: công cụ đã gọi (agent_calls.jsonl), kết quả công cụ (tool_texts.jsonl). In theo bản:
  đúng        số câu đúng
  timeline    số câu có gọi timeline
  chỉ_vector  số câu KHÔNG gọi timeline (trả lời từ vector/text)
  đúng|không_tl  số câu đúng mà không gọi timeline (không nhờ graph)
  tl_có_cũ    số câu mà kết quả công cụ có giá trị cũ (past_value) của câu C/F (graph/văn bản bản cũ gây nhiễu)
  tl_có_mới   số câu mà kết quả công cụ có giá trị mới (real_value)
"""
import collections, glob, json, sys
sys.path.insert(0, "scripts")
from m3_mech3_score import match
Q = {}
for f in glob.glob(f"dataset/organized/questions/mech3/{__import__('os').environ.get('M3_SET', 'tune')}/*.jsonl"):
    for l in open(f):
        if l.strip():
            q = json.loads(l); Q[q["qid"]] = q
for arg in sys.argv[1:]:
    name, d = arg.split("=")
    R = [json.loads(l) for l in open(f"{d}/results.jsonl")]
    qid = {f"q{r['i']:03d}": r["idx"] for r in R}
    names = collections.defaultdict(set)
    for l in open(f"{d}/agent_calls.jsonl"):
        c = json.loads(l)
        for t in c["output"].get("tool_calls", []):
            names[c["query_id"]].add(t.get("name") or t.get("function", {}).get("name"))
    TT = {json.loads(l)["idx"]: json.loads(l)["tool_texts"] for l in open(f"{d}/tool_texts.jsonl")}
    n = ok = tl = ok_notl = pv_n = rv_n = cf = 0
    for qk, idx in qid.items():
        q = Q[idx]; r = next(x for x in R if x["idx"] == idx)
        good = match(q, r["answer"] or ""); used = "timeline" in names[qk]
        n += 1; ok += good; tl += used; ok_notl += good and not used
        if q["past_value"]:
            cf += 1; txt = " ".join(t for s, t in TT[idx] if isinstance(t, str)).lower()
            pv_n += str(q["past_value"]).lower() in txt; rv_n += str(q["real_value"]).lower() in txt
    print(f"{name:6s} câu={n} đúng={ok} ({ok/n:.3f}) timeline={tl} ({tl/n:.2f}) chỉ_vector={n-tl} đúng|không_tl={ok_notl} | câu C/F={cf}: kết quả công cụ có giá trị cũ={pv_n}, có giá trị mới={rv_n}")
