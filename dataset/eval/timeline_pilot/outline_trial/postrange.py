"""Bổ sung mốc kết thúc của khoảng đọc từ chính chunk (không phụ thuộc cách model chép date_text).
python3 -I postrange.py <timeline_pilot_dir> <in_out_dir_name> <out_dir_name> <trang>..."""
import json,re,sys
from pathlib import Path
pilot=Path(sys.argv[1]); src=pilot/"outline_trial"/sys.argv[2]; dst=pilot/"outline_trial"/sys.argv[3]; dst.mkdir(exist_ok=True)
ISO=r"(\d{4}-\d{2}-\d{2})"
PAT=[re.compile(ISO+r"\s*[–—-]\s*"+ISO),
     re.compile(r"(?<![\d-])(\d{4})\s*[–—-]\s*(\d{4})(?![\d-])"),
     re.compile(r"(?:from|between)\s+(\d{4})\s+(?:to|and|until)\s+(\d{4})",re.I)]
tot=0
for n in sys.argv[4:]:
    txt=next(pilot.glob(f"batch*/in/{n}.txt")).read_text()
    parts=re.split(r"^=== CHUNK (\S+) ===\n",txt,flags=re.M); ch={c:b for c,b in zip(parts[1::2],parts[2::2])}
    j=json.load(open(src/f"{n}.json")); ev=j["events"]; add=[]
    for cid,body in ch.items():
        here=[e for e in ev if e["cid"]==cid]
        for p in PAT:
            for m in p.finditer(body):
                a,b=m.group(1),m.group(2)
                if a[:4]==b[:4] and len(a)==4: continue
                st=[e for e in here if e["date"] and e["date"].startswith(a)]
                if not st or any(e["date"] and e["date"].startswith(b) for e in here+add if e["cid"]==cid): continue
                e0=st[0]; add.append(dict(e0,text="End of: "+e0["text"],date=b,flags=e0["flags"]+["range_end_added"]))
    j["events"]=ev+add; tot+=len(add)
    (dst/f"{n}.json").write_text(json.dumps(j,ensure_ascii=False,indent=1),encoding="utf-8")
print("thêm",tot,"mốc kết thúc")
