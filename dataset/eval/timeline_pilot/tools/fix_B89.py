# Bổ sung sau khi session chính đọc kiểm B8/B9 (chạy SAU patch_bB8.py / patch_bB9.py)
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
    d["events"]=ev2
    d["events"]=sorted(d["events"],key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
b="batchB8";n="Zambia";d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
d["events"]+=[
 ev("1855","other","exploration","Livingstone became the first European to see the Zambezi waterfalls and named them Victoria Falls",c+"51","both","He was the first European to see the magnificent waterfalls on the Zambezi River in 1855 , naming them the Victoria Falls"),
 ev("1895","other","exploration","Rhodes asked scout Frederick Russell Burnham to look for minerals and river navigation; Burnham found major copper deposits",c+"54","both","In 1895 , Rhodes asked his American scout Frederick Russell Burnham to look for minerals and ways to improve river navigation in the region")]
fin(b,n,d)
