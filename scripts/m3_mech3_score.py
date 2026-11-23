"""Chấm câu mech3 của agent bằng luật có sẵn (validate_past_questions.match, không gọi LLM). Dùng: m3_mech3_score.py <thư mục output> ..."""
import json, sys
from collections import defaultdict
sys.path.insert(0, "scripts")
import re
from validate_past_questions import match as _match


# Câu trả lời từ chối ("I cannot determine this: no page ... was found") không phải đáp án: trước đây từ "no" trong câu từ chối bị lấy làm "No" và được điểm nếu gold là "No" (sửa 2026-11-24).
DECLINE = re.compile(r"(cannot|can'?t|can not|unable to|not able to|could not|couldn'?t)\s+(be\s+)?(determin|confirm|verif|answer|find|tell)|not enough|insufficient|no (information|passage|source|page|mention|record)|not (stated|mentioned|specified)|does not (say|state|mention|specify)|unknown|unclear", re.I)


def match(q, a):
    """Như validate_past_questions.match, nhưng câu có/không lấy từ yes/no đầu tiên trong câu trả lời (agent có thể mở đầu bằng 'The source states...').
    Câu trả lời không mở đầu bằng yes/no mà có cụm từ chối ("cannot determine", "no passage"...) tính là sai (không phải đáp án)."""
    a = a or ''
    if not re.match(r'\s*(yes|no)\b', a, re.I) and DECLINE.search(a):
        return False
    m = re.search(r'\b(yes|no)\b', a, re.I)
    return _match(q, (m.group(1) + ' ' + a) if m else a)
Q = {}
QALL = {}
import glob
for f in glob.glob(f"dataset/organized/questions/mech3/{__import__('os').environ.get('M3_SET', 'tune')}/*.jsonl"):
    for l in open(f):
        if l.strip():
            q = json.loads(l); Q[q["qid"]] = q; QALL.setdefault(q["qid"], []).append(q)


def _cases():
    return json.load(open(f"dataset/organized/{__import__('os').environ.get('M3_STATE_NAME', 'm3_state')}/{__import__('os').environ.get('M3_SET', 'tune')}/subset_mech3.json"))["cases"]


def _pick(qs, text):
    for q in qs:
        if q["question"] == text:
            return q
    return None


def getq(r, pos=None, cases=None, nv=1):
    """Câu hỏi của một dòng kết quả. Trong tune có 14 qid dùng chung cho hai câu khác nhau (valid không có):
    dòng agent có `question` -> chọn câu có nội dung nằm trong đó; dòng cấu hình cố định (không có nội dung câu) được ghi đúng thứ tự (câu x biến thể)
    nên ghép theo vị trí với subset_mech3.json (score() kiểm thứ tự trước khi dùng). Không ghép được thì lấy câu nạp sau."""
    c = QALL[r["idx"]]
    if len(c) > 1:
        if r.get("question"):
            for q in c:
                if q["question"] in r["question"]:
                    return q
        if pos is not None and cases is not None and pos // nv < len(cases) and cases[pos // nv]["idx"] == r["idx"]:
            q = _pick(c, cases[pos // nv]["question"])
            if q:
                return q
    return Q[r["idx"]]


def score(d):
    """Một thư mục output -> {biến thể ('' nếu agent): ({nhóm: [đúng/sai]}, [idx sai])}."""
    out = {}
    R = [json.loads(l) for l in open(f"{d}/results.jsonl")]
    cases, nv = None, 1
    if R and all("v" in r for r in R):
        vs = list(dict.fromkeys(r["v"] for r in R)); cs = _cases()
        if len(R) == len(vs) * len(cs) and all(R[i]["idx"] == cs[i // len(vs)]["idx"] and R[i]["v"] == vs[i % len(vs)] for i in range(len(R))):
            cases, nv = cs, len(vs)   # thứ tự dòng = thứ tự (câu x biến thể): ghép theo vị trí an toàn
    for pos, r in enumerate(R):
        q = getq(r, pos, cases, nv); ok = match(q, r["answer"] or "")
        t, bad = out.setdefault(r.get("v", ""), (defaultdict(list), []))
        for k in ("ALL", q["type"], q["type"] + "/" + q["kind"]):
            t[k].append(ok)
        if not ok: bad.append(r["idx"])
    return out


if __name__ == "__main__":
    for d in sys.argv[1:]:
        for v, (t, bad) in score(d).items():
            print(d, v, "  ".join(f"{k}={sum(x)}/{len(x)}" for k, x in sorted(t.items(), key=lambda x: (len(x[0]) > 3, x[0]))))
            print("  sai:", bad)
