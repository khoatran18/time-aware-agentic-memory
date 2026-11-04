# Liệt kê câu có năm trong chunk mà không mốc nào trích dẫn: gợi ý mốc sót. Dùng: python3 -I tools/gap.py batchBN <tên trang>  (đọc rev/)
import json,re,sys
b,n=sys.argv[1],sys.argv[2]
txt=open(f"{b}/in/{n}.txt").read()
d=json.load(open(f"{b}/rev/{n}.json"))
ch=dict(re.findall(r"=== CHUNK \S+#(\d+) ===\n(.*?)(?=\n=== CHUNK |\Z)",txt,re.S))
cov={}
for e in d["events"]:
    for x in e["evidence"]: cov.setdefault(x["chunk_id"].split("#")[-1],[]).append(e["date"][:4]+" "+x["quote"])
for k,t in ch.items():
    t=t.split("\n",1)[1] if "\n" in t else t
    for m in re.finditer(r"[^.]*?\b((?:1[0-9]|20)\d\d)\b[^.]*\.",t):
        y=m.group(1); s=m.group(0).strip()
        if not any(y in c for c in cov.get(k,[])): print(f"[{k}] {y}: {s[:220]}")
