"""Chấm recall cho trang tùy ý và thống kê actor. python3 -I score2.py <repo> <out_dir>... -- <trang>..."""
import json,sys
from pathlib import Path
a=sys.argv[1:]; i=a.index("--"); dirs=a[1:i] if False else a[:i]; pages=a[i+1:]
P=Path("."); 
for d in dirs:
    T=H=E=Ho=Eo=0; oth=[]
    for n in pages:
        gold=json.load(open(next(P.glob(f"batch*/rev/{n}.json"))))["events"]
        ev=json.load(open(P/"outline_trial"/d/f"{n}.json"))["events"]
        def match(evs):
            used=set();h=0
            for g in gold:
                gc={x["chunk_id"] for x in g["evidence"]}
                for k,e in enumerate(evs):
                    if k in used: continue
                    if e["date"]==g["date"] and e["cid"] in gc: used.add(k);h+=1;break
            return h
        keep=[e for e in ev if e.get("actor","subject")!="other"]
        h=match(ev); ho=match(keep)
        print(f"  {d} {n}: {h}/{len(gold)} (trích {len(ev)}); bỏ actor=other: {ho} (trích {len(keep)})")
        T+=len(gold);H+=h;E+=len(ev);Ho+=ho;Eo+=len(keep)
        oth+=[(n[:6],e["date"],e["text"][:70]) for e in ev if e.get("actor","subject")=="other"]
    print(d,f"TỔNG {H}/{T}={H/T:.1%} trích {E}; bỏ actor=other: {Ho}/{T}={Ho/T:.1%} trích {Eo}; số mốc other: {E-Eo}")
    if "-v" in sys.argv: 
        for o in oth: print("    other:",o)
