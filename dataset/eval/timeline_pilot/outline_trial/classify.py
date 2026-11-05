import json,glob,re,sys,random
from pathlib import Path
P=Path("/home/tmkhoa-1812/CodingSpace/HUST/DATN/TimeAwareAgenticMemory/time-aware-agentic-memory/dataset/eval/timeline_pilot")
SRC={"Irina_Levitina":"out_p3","Aleksandra_Goryachkina":"out_p3b","HMS_Warrior_R31":"out_p3b","Mannheim_Observatory":"out_p3b","Rezidor_Hotel_Group":"out_p3b",
     "Karls_y":"out_p3c","Orchard_Supply_Hardware":"out_p3c","Rainier_Brewing_Company":"out_p3c","Brian_Higgins":"out_p3c","Carlos_Sainz_Jr":"out_p3c"}
arm=sys.argv[1] if len(sys.argv)>1 else "A"
rows=[]
for n,d in SRC.items():
    txt=next(P.glob(f"batch*/in/{n}.txt")).read_text(encoding="utf-8")
    parts=re.split(r"^=== CHUNK (\S+) ===\n",txt,flags=re.M); ctext={c:b.partition("\n")[2].strip() for c,b in zip(parts[1::2],parts[2::2])}
    gold=json.load(open(next(P.glob(f"batch*/rev/{n}.json"))))["events"]
    gk={(g["date"],e["chunk_id"]) for g in gold for e in g["evidence"]}; gd={g["date"] for g in gold}
    gy={(g["date"][:4],e["chunk_id"]) for g in gold for e in g["evidence"]}
    for e in json.load(open(f"{d}/{n}_{arm}.json"))["events"]:
        c=ctext.get(e["cid"],""); dt=e["date"]
        if not dt: cat="null_date"
        elif (dt,e["cid"]) in gk: cat="match_gold"
        elif dt in gd: cat="gold_date_other_chunk"
        elif (dt[:4],e["cid"]) in gy: cat="same_year_chunk_diff_precision"
        else:
            yr=dt[:4]; cat="not_in_gold_year_in_chunk" if yr in c else "not_in_gold_year_NOT_in_chunk"
        rows.append(dict(page=n,cat=cat,date=dt,text=e["text"],cid=e["cid"],chunk=c))
from collections import Counter
cnt=Counter(r["cat"] for r in rows); tot=len(rows)
print("arm",arm,"tổng mốc trích",tot)
for k,v in cnt.most_common(): print(f"  {k:36}{v:5} ({v/tot:.0%})")
json.dump(rows,open(f"rows_{arm}.json","w"),ensure_ascii=False)
