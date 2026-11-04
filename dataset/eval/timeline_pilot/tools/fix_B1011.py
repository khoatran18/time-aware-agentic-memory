# Bổ sung sau khi session chính đọc kiểm B10/B11 (chạy SAU patch_bB10.py / patch_bB11.py)
import json
def ev(date,track,label,text,chunk,role,quote,flag=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
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
b="batchB11";n="Sastamala";d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
d["events"]+=[
 ev("1962-11-26","other","heraldry","Coat of arms (later Sastamala's) approved by the Karkku municipal council",c+"3","both","originally approved by the Karkku municipal council on November 26 , 1962"),
 ev("1963-02-12","other","heraldry","Coat of arms (later Sastamala's) approved for use by the Ministry of the Interior",c+"3","both","approved for use by the Ministry of the Interior on February 12 , 1963")]
fin(b,n,d)
b="batchB11";n="Brian_Higgins";d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
d["events"]+=[ev("1993","other","award","Rated Buffalo's Best Lawmaker in a Buffalo News survey during his final year on the Council",c+"3","both","Higgins was rated Buffalos Best Lawmaker in a 1993 Buffalo News Survey")]
fin(b,n,d)
