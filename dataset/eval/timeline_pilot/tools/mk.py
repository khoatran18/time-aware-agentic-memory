import sys,json,re
# usage: mk.py <name>  ; reads me/<name>.dsl -> me/<name>.json, verifies quotes against in/<name>.txt
base=sys.argv[1]; name=sys.argv[2]
txt=open(f"{base}/in/{name}.txt").read()
chunks={}
for m in re.finditer(r"=== CHUNK (\S+) ===\n(.*?)(?=\n=== CHUNK |\Z)",txt,re.S): chunks[m.group(1)]=m.group(2)
pid="/wiki/"+name
ev=[];und=[];bad=[]
for ln in open(f"{base}/me/{name}.dsl"):
    ln=ln.rstrip("\n")
    if not ln.strip() or ln.startswith("#"): continue
    if ln.startswith("UND|"): und.append(ln[4:]);continue
    date,track,text,evs=ln.split("|",3)
    label=""
    if ":" in track: track,label=track.split(":",1)
    grain={4:"year",7:"month",10:"day"}.get(len(date),"other")
    e=[]
    for it in evs.split(";;"):
        c,q=it.split("~",1); role="both"
        if c[0] in "DX" and c[1]==" ": pass
        cid=f"{pid}#{c}" if c.isdigit() else None
        if cid is None:
            role={"d":"date","x":"description"}[c[0]]; cid=f"{pid}#{c[1:]}"
        if q not in chunks.get(cid,""): bad.append((cid,q))
        e.append({"chunk_id":cid,"role":role,"quote":q})
    ev.append({"date":date,"grain":grain,"track":track,"label":label,"text":text,"evidence":e})
ev.sort(key=lambda x:x["date"])
for i,e in enumerate(ev,1): e["id"]=f"e{i}"
json.dump({"page_id":pid,"events":ev,"undated_mentions":und},open(f"{base}/me/{name}.json","w"),indent=1,ensure_ascii=False)
print(name,len(ev),"events; bad quotes:",bad)
