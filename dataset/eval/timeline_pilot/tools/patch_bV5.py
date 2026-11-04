import json,sys,os
base="batchV5"
os.makedirs(f"{base}/rev",exist_ok=True)
def load(n): return json.load(open(f"{base}/sub/{n}.json"))
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=more
    if flag:e["flag"]=flag
    return e
def fin(n,d):
    for e in d["events"]:
        if len(e["date"].split("-")[0])==3: e["date"]="0"+e["date"]
    d["events"]=sorted(d["events"],key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def drop(d,*ids): d["events"]=[e for e in d["events"] if e["id"] not in ids]
def get(d,i): return next(e for e in d["events"] if e["id"]==i)
def flag(d,f,*ids):
    for i in ids: get(d,i)["flag"]=f
def ex(chunk,role,quote): return {"chunk_id":chunk,"role":role,"quote":quote}
AP="approximate_date";DD="derived_date";SI="source_inconsistent"
def txt(d,i,t): get(d,i)["text"]=t
def noflag(d,*ids):
    for i in ids: get(d,i).pop("flag",None)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def undrop(d,*subs): d["undated_mentions"]=[u for u in d["undated_mentions"] if not any(s in u for s in subs)]
def quote(d,i,q): get(d,i)["evidence"][0]["quote"]=q

def add(n,d,items):
    c=pre(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]; fl=it[7] if len(it)>7 else None; more=it[8] if len(it)>8 else None
        if more: more=[ex(c+m[0],m[1],m[2]) for m in more]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,fl,more))

def setev(d,i,l): get(d,i)["evidence"]=l


# no change
for n in ["Arnolfini_Portrait","Eleni_Theocharous","Helsingin_Sanomat","Steven_Ozment"]: fin(n,load(n))

n="Gamvik";d=load(n)
add(n,d,[("1972-06","work",None,"Construction started for a landside terminal and a SOSUS cable into the sea","6","both","In June 1972 construction started for [ a landside terminal and ] running a SOSUS cable")])
fin(n,d)

n="Penrhyn_Castle";d=load(n)
drop(d,"e4")  # compensation of the owner = event of another entity
fin(n,d)

n="Flatiron_Building";d=load(n)
add(n,d,[("1899","ownership_structure",None,"After Amos Eno's death his assets were liquidated and the lot went up for sale","6","both","after his death in 1899 his assets were liquidated , and the lot went up for sale")])
fin(n,d)

n="John_Plumbe";d=load(n)
add(n,d,[("1829","work",None,"Surveying sites for future railroad routes as a civil engineer","2","both","by 1829 was surveying sites for future railroad routes",AP)])
fin(n,d)

n="Ruud_Lubbers";d=load(n);c=pre(d)
setev(d,"e10",[ex(c+"1","description","serving from 8 June"),ex(c+"2","date","8 September 1977")])
add(n,d,[("1986","role",None,"Formed Cabinet Lubbers II and continued as Prime Minister for a second term","3","both","For the election of 1986 Lubbers served as Lijsttrekker",DD),
("1989","role",None,"Formed Cabinet Lubbers III and continued as Prime Minister for a third term","4","both","1989 Lubbers again served as Lijsttrekker and following another successful cabinet formation formed the Cabinet Lubbers III",DD)])
fin(n,d)

n="SECR_N_class";d=load(n)
add(n,d,[("1977","other","preservation","Preserved No. 1874 steamed for the first time in preservation on the Mid-Hants Railway","61","both","it was steamed for the first time in preservation in 1977")])
fin(n,d)
