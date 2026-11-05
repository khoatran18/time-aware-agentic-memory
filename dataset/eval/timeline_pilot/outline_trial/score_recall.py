import json,sys
from pathlib import Path
P=Path(sys.argv[1]); dirs=sys.argv[2:]
pages=["Aleksandra_Goryachkina","Brian_Higgins","Karls_y","Mannheim_Observatory","Rainier_Brewing_Company"]
for d in dirs:
    T=H=E=0; miss=[]
    for n in pages:
        gold=json.load(open(next(P.glob(f"batch*/rev/{n}.json"))))["events"]
        ev=json.load(open(P/"outline_trial"/d/f"{n}.json"))["events"]
        used=set(); h=0
        for g in gold:
            gc={x["chunk_id"] for x in g["evidence"]}; ok=False
            for i,e in enumerate(ev):
                if i in used: continue
                if e["date"]==g["date"] and e["cid"] in gc: used.add(i); ok=True; break
            h+=ok
            if not ok: miss.append((n,g["date"],g["text"][:70]))
        T+=len(gold); H+=h; E+=len(ev)
        print(f"  {d} {n}: {h}/{len(gold)} (trích {len(ev)})")
    print(d,f"TỔNG {H}/{T} = {H/T:.1%}; tổng mốc trích {E}")
    if "v4_35" in d:
        for m in miss: print("   trượt",m)
