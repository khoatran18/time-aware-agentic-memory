import sys,json,re
base=sys.argv[1]
TRACKS={"role","affiliation","location","ownership_structure","work","naming","family","education","other"}
tot=0
for name in sys.argv[2:]:
    txt=open(f"{base}/in/{name}.txt").read()
    ch={m.group(1):m.group(2) for m in re.finditer(r"=== CHUNK (\S+) ===\n(.*?)(?=\n=== CHUNK |\Z)",txt,re.S)}
    try: d=json.load(open(f"{base}/"+__import__("os").environ.get("DIR","sub")+f"/{name}.json"))
    except Exception as e: print(name,"INVALID JSON",e); continue
    err=[]
    ev=d.get("events",[])
    prev=""
    seen=set()
    for i,e in enumerate(ev,1):
        w=f"{e.get('id')}({e.get('date')})"
        if e.get("id")!=f"e{i}": err.append(f"{w}: id không tuần tự")
        dt=str(e.get("date",""))
        if not re.fullmatch(r"-?\d{4}(-\d{2}(-\d{2})?)?",dt): err.append(f"{w}: định dạng date"); 
        else:
            g={4:"year",7:"month",10:"day"}[len(dt.lstrip("-"))]
            if e.get("grain")!=g: err.append(f"{w}: grain {e.get('grain')}≠{g}")
            if prev and int(dt.lstrip("-")[:4])*(-1 if dt[0]=="-" else 1)<int(prev.lstrip("-")[:4])*(-1 if prev[0]=="-" else 1): err.append(f"{w}: không sắp theo ngày")
            prev=dt
        if e.get("track") not in TRACKS: err.append(f"{w}: track lạ {e.get('track')}")
        if e.get("track")=="other" and not e.get("label"): err.append(f"{w}: other thiếu label")
        k=(dt,e.get("text","").lower())
        if k in seen: err.append(f"{w}: trùng date+text")
        seen.add(k)
        roles=[]
        for x in e.get("evidence",[]):
            c=ch.get(x.get("chunk_id"))
            if c is None: err.append(f"{w}: chunk_id lạ {x.get('chunk_id')}"); continue
            q=x.get("quote","")
            if q not in c: err.append(f"{w}: quote không nguyên văn: {q[:50]!r}")
            r=x.get("role"); roles.append(r)
            if r not in("both","date","description"): err.append(f"{w}: role lạ")
            yr=str(int(dt.lstrip("-")[:4])+1) if dt[0]=="-" else (dt[:4].lstrip("0") or dt[:4])
            if r in("both","date") and yr not in q and e.get("flag")!="derived_date": err.append(f"{w}: quote {r} không chứa năm {yr}")
            if r=="description" and re.search(r"\b%s\b"%yr,q): err.append(f"{w}: quote description chứa năm {yr}")
        if not("both" in roles or ("date" in roles and "description" in roles)): err.append(f"{w}: thiếu bộ chunk tối thiểu {roles}")
        if re.search(r"\d0s\b|century",e.get("text","")): err.append(f"{w}: có vẻ mốc thập kỷ/thế kỷ")
    print(f"{name}: {len(ev)} sự kiện, {len(d.get('undated_mentions',[]))} undated, {len(err)} lỗi mã kiểm")
    for x in err: print("   -",x)
    tot+=len(err)
print("TỔNG lỗi:",tot)
