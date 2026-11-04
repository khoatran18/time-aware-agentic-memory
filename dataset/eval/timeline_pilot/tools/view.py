import sys,json,re
base,name=sys.argv[1],sys.argv[2]
txt=open(f"{base}/in/{name}.txt").read()
d=json.load(open(f"{base}/sub/{name}.json"))
ch=re.findall(r"=== CHUNK \S+#(\d+) ===\n(.*?)(?=\n=== CHUNK |\Z)",txt,re.S)
byc={}
for e in d["events"]:
    for x in e["evidence"]: byc.setdefault(x["chunk_id"].split("#")[-1],[]).append(e["id"])
print("### CHUNKS");
for n,t in ch: print(f"[{n}] "+re.sub(r"\n"," / ",t.strip())+f"\n   -> events: {byc.get(n,[])}")
print("\n### EVENTS (id date track|label | text | chunks+role | flag)")
for e in d["events"]:
    print(e["id"],e["date"],e["track"]+("|"+e["label"] if e.get("label") else ""),"|",e["text"],"|",",".join(x["chunk_id"].split("#")[-1]+":"+{"both":"B","date":"D","description":"x"}[x["role"]] for x in e["evidence"]),"|",e.get("flag",""))
print("\n### UNDATED"); [print("-",u) for u in d.get("undated_mentions",[])]
