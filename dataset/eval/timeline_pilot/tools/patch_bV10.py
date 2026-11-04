# Vá V10 (cloud đọc kiểm). Chạy từ dataset/eval/timeline_pilot: python3 -I tools/patch_bV10.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os
B="batchV10"
os.makedirs(f"{B}/rev",exist_ok=True)
for f in glob.glob(f"{B}/sub/*.json"): shutil.copy(f,f"{B}/rev/"+os.path.basename(f))
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date.lstrip("-"))],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=[{"chunk_id":chunk.split("#")[0]+"#"+m[0],"role":m[1],"quote":m[2]} for m in more]
    if flag:e["flag"]=flag
    return e
def fin(n,d):
    seen=set();ev2=[]
    for e in d["events"]:
        k=(e["date"],e["text"])
        if k not in seen: seen.add(k);ev2.append(e)
    d["events"]=sorted(ev2,key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{B}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def load(n): return json.load(open(f"{B}/rev/{n}.json"))
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def get(d,i): return next(e for e in d["events"] if e["id"]==i)
def A(n,items,d=None):
    d=d or load(n);c=pre(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,it[7] if len(it)>7 else None,it[8] if len(it)>8 else None))
    fin(n,d)
D="derived_date";AP="approximate_date"

# Gerhard_Schr_der e65 và Federation_of_the_Greens e87: quote không chứa năm, năm suy ra từ câu trước -> derived_date.
n="Gerhard_Schr_der";d=load(n)
get(d,"e65")["flag"]=D
fin(n,d)
n="Federation_of_the_Greens";d=load(n)
get(d,"e87")["flag"]=D
fin(n,d)

# Không đổi nội dung: chỉ đánh số lại (haiku đã đủ sau khi gap.py/view.py kiểm).
for n in ["Alfred_Drury","Fernand_Braudel","Galatasaray_S_K_football","International_Mathematical_Union","Liina_Tennosaar","Meg_Whitman","Writers_Guild_of_America_West","Y_Combinator"]: fin(n,load(n))
