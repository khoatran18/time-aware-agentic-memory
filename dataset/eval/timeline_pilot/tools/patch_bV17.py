# Vá V17 (session chính đọc kiểm). Chạy: python3 -I tools/patch_bV17.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os
for b in ("batchV17",):
    os.makedirs(f"{b}/rev",exist_ok=True)
    for f in glob.glob(f"{b}/sub/*.json"): shutil.copy(f,f"{b}/rev/"+os.path.basename(f))
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
    d["events"]=sorted(ev2,key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def A(b,n,items,drop=()):
    d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
    d["events"]=[e for e in d["events"] if not any(s in e["text"] for s in drop)]
    for it in items:
        date,track,label,text,ch,role,q=it[:7]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,it[7] if len(it)>7 else None,it[8] if len(it)>8 else None))
    fin(b,n,d)
D="derived_date";AP="approximate_date"
A("batchV17","Teodor_Atanasiu",[
("2012","other","election","Ran for president of the Alba County Council and lost, coming second with 40.5%","13","both","At the 2012 local election , he ran for president of the Alba County Council , coming in second with 40.5% of the vote and losing"),
("2014","other","PNL presidency","Candidate for the PNL presidency, withdrew shortly before the vote and backed Alina Gorghiu","13","both","In late 2014 , he was a candidate for the PNL presidency , but withdrew from the race shortly before it was decided",AP),
("2016","other","election","Ran for the Senate at the 2016 election but lost","14","both","Senate at the 2016 election , but lost"),
])
