# Vá V11 (session chính đọc kiểm). Chạy từ dataset/eval/timeline_pilot: python3 -I tools/patch_bV11.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os,re
B="batchV11"
os.makedirs(f"{B}/rev",exist_ok=True)
for f in glob.glob(f"{B}/sub/*.json"): shutil.copy(f,f"{B}/rev/"+os.path.basename(f))
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date.lstrip("-"))],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=[{"chunk_id":chunk.split("#")[0]+"#"+m[0],"role":m[1],"quote":m[2]} for m in more]
    if flag:e["flag"]=flag
    return e
def fin(base,n,d):
    seen=set();ev2=[]
    for e in d["events"]:
        k=(e["date"],e["text"])
        if k not in seen: seen.add(k);ev2.append(e)
    d["events"]=sorted(ev2,key=lambda e:(e["date"].lstrip("-")[:4] if not e["date"].startswith("-") else "-"+e["date"][1:5],0 if len(e["date"].lstrip("-"))==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def load(n): return json.load(open(f"{B}/rev/{n}.json"))
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def A(n,items,drop=(),fix=None):
    d=load(n);c=pre(d)
    d["events"]=[e for e in d["events"] if not any(s in e["text"] for s in drop)]
    for e in d["events"]:  # grain theo độ dài date
        e["grain"]={4:"year",7:"month",10:"day"}[len(e["date"].lstrip("-"))]
    if fix: fix(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,it[7] if len(it)>7 else None,it[8] if len(it)>8 else None))
    fin(B,n,d)
D="derived_date";AP="approximate_date"
def abbr(d):  # quote có khoảng năm viết tắt "( 1921–23 )" -> derived_date
    for e in d["events"]:
        for x in e["evidence"]:
            if re.search(r"\(\s*\d{4}\s*[–-]\s*\d{2}\s*\)",x["quote"]) and e["date"] not in x["quote"]: e["flag"]=D

# ---- baseline: chuẩn hóa grain, đánh lại id cho mọi trang
for _n in sorted(os.path.basename(f)[:-5] for f in glob.glob(f"{B}/sub/*.json")):
    A(_n,[])
A("PFC_Levski_Sofia",[],fix=abbr)
A("Rachel_Ruysch",[],drop=("Gallery of Honor",))
A("Paul_Sturrock",[
("2008-07","other","health","Announced he had a mild form of Parkinson's disease","3","both","Sturrock announced in July 2008 that he was suffering from a mild form of Parkinsons disease"),
])
