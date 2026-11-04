# Vá V12 (session chính đọc kiểm). Chạy từ dataset/eval/timeline_pilot: python3 -I tools/patch_bV12.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os,re
B="batchV12"
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
def abbr(d):  # quote có khoảng năm viết tắt "( 1946–47 )" hoặc "2018–19" -> derived_date
    for e in d["events"]:
        for x in e["evidence"]:
            if x["role"] in ("both","date") and e["date"].lstrip("-")[:4] not in x["quote"] and e.get("flag")!="source_inconsistent": e["flag"]=D
def both(d,ids):  # đổi role description có chứa năm thành both
    for e in d["events"]:
        if e["id"] in ids:
            for x in e["evidence"]:
                if x["role"]=="description" and e["date"] in x["quote"]: x["role"]="both"

# ---- baseline: chuẩn hóa grain, đánh lại id cho mọi trang
for _n in sorted(os.path.basename(f)[:-5] for f in glob.glob(f"{B}/sub/*.json")):
    A(_n,[])
A("Atl_tico_Madrid",[],fix=lambda d:(abbr(d),both(d,("e76","e77","e92"))))
A("Maurizio_Sarri",[],fix=abbr)
A("Michel_Zink",[
("1972","work","book","Published La Pastourelle: poésie et folklore au Moyen Âge (Bordas)","5","both","La Pastourelle : poésie et folklore au Moyen Âge , Paris , Bordas , coll . Études , 1972 , 160 p ."),
])
A("Atl_tico_Madrid",[
("2017","ownership_structure","ISL","Ended its franchise partnership with the Indian Super League club in Kolkata","4","both","in 2017 Atlético decided to end its franchise partnership with the ISL club due to broken commitments"),
("2017","location","stadium","Stopped playing home games at the Estadio Vicente Calderón","77","both","The club played their home games at the 54,990 seat Estadio Vicente Calderón in southern Madrid until 2017"),
("2020-07","location","stadium","Former home Vicente Calderón demolished and replaced by a park","78","both","The Vicente Calderón has been demolished in July 2020"),
])
