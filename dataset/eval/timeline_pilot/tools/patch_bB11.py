import json,sys,os
base="batchB11"
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


n="Brian_Higgins";d=load(n);drop(d,"e13");fin(n,d)
n="Casus_Belli_magazine";d=load(n)
add(n,d,[("2009","ownership_structure",None,"Casus Belli Presse formed as a new publisher","2","both","Casus Belli Presse , a new publisher , was formed in 2009")]);fin(n,d)
n="Charlotte_Fitch_Roberts";d=load(n);fin(n,d)
n="Greenbelt_News_Review";d=load(n);fin(n,d)
n="Jean_Lassalle";d=load(n);drop(d,"e8");fin(n,d)
n="Sastamala";d=load(n)
add(n,d,[("2011-07","other","museum opened","Finnish Book Museum Pukstaavi opened in Sastamala","9","both","In July 2011 , the Finnish Book Museum Pukstaavi was also opened in Sastamala")]);fin(n,d)
n="Tyyni_Tuulio";d=load(n);fin(n,d)
n="Yugoslavia_Davis_Cup_team";d=load(n)
add(n,d,[("1952","other","defection","Players Dragutin Mitic and Milan Branovic defected from the Federal People's Republic of Yugoslavia","4","both","In 1952 , Dragutin Mitić and Milan Branović")]);fin(n,d)
