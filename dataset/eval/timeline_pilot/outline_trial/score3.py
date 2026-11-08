"""Chấm recall hai chế độ: nghiêm (chunk ∈ evidence) và lỏng (chunk lệch <= SLACK so với một chunk của evidence).
Ghép một-một, hai lượt: lượt 1 ghép nghiêm, lượt 2 chỉ ghép lỏng cho phần còn lại (để mốc lỏng không cướp mốc nghiêm).
Dùng: python3 -I outline_trial/score3.py <out_dir>... -- <trang>...   (chạy trong timeline_pilot; SLACK=1 mặc định; -v in các cặp chỉ khớp lỏng)"""
import json, sys, os
from pathlib import Path
a = sys.argv[1:]; i = a.index("--"); dirs = a[:i]; pages = [x for x in a[i+1:] if x != "-v"]
SL = int(os.environ.get("SLACK", "1")); P = Path(".")
idx = lambda c: int(c.split("#")[-1])
import re
STOPW = {"that","this","with","from","were","was","his","her","their","after","before","first","into","and","the","for","became","become"}
def toks(t): return {w.lower().rstrip("s") for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}|\d{2,}", t)} - STOPW
def overlap(a, b): return len(toks(a) & toks(b))
MINOV = int(os.environ.get("MINOV", "1"))
for d in dirs:
    T = S = L = 0; extra = []
    for n in pages:
        gold = json.load(open(next(P.glob(f"batch*/rev/{n}.json"))))["events"]
        ev = json.load(open(P / "outline_trial" / d / f"{n}.json"))["events"]
        used = set(); hit = {}
        for g in gold:                       # lượt 1: nghiêm
            gc = {x["chunk_id"] for x in g["evidence"]}
            for k, e in enumerate(ev):
                if k not in used and e["date"] == g["date"] and e["cid"] in gc: used.add(k); hit[g["id"]] = "S"; break
        for g in gold:                       # lượt 2: lỏng cho phần còn lại
            if g["id"] in hit: continue
            gc = [idx(x["chunk_id"]) for x in g["evidence"]]
            for k, e in enumerate(ev):
                if k not in used and e["date"] == g["date"] and any(abs(idx(e["cid"]) - c) <= SL for c in gc) and overlap(g["text"], e["text"]) >= MINOV:
                    used.add(k); hit[g["id"]] = "L"; extra.append((n, g["id"], g["date"], g["text"][:55], e["text"][:55])); break
        s = sum(v == "S" for v in hit.values()); l = len(hit)
        T += len(gold); S += s; L += l
    print(f"{d}: nghiêm {S}/{T}={S/T:.1%} | lỏng(±{SL}) {L}/{T}={L/T:.1%} | chỉ khớp lỏng: {L-S}")
    if "-v" in sys.argv:
        for x in extra: print("     ", x)
