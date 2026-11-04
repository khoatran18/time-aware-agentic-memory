import json,sys
base=sys.argv[1]
def load(n): return json.load(open(f"{base}/sub/{n}.json"))
def ev(date,track,label,text,chunk,role,quote,flag=None,extra=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if flag:e["flag"]=flag
    return e
def fin(n,d):
    d["events"].sort(key=lambda e:e["date"][:4]) if False else None
    d["events"]=sorted(d["events"],key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def drop(d,*ids): d["events"]=[e for e in d["events"] if e["id"] not in ids]
def get(d,i): return next(e for e in d["events"] if e["id"]==i)
def rmev(d,i,chunk): e=get(d,i); e["evidence"]=[x for x in e["evidence"] if x["chunk_id"]!=chunk]
P="/wiki/"
# Carl
n="Carl_Ehrensvard";d=load(n);c=P+"Carl_August_Ehrensvärd_(1858–1944)#"
rmev(d,"e20",c+"0")
d["events"]+= [ev("1911","role","","Minister for Naval Affairs term ended (intro gives 1907–1911)",c+"0","both","Minister for Naval Affairs 1907–1911","source_inconsistent"),
 ev("1910","role","","Appointed station commander in Stockholm",c+"3","both","admiral in 1910 and appointed station commander in Stockholm")]
d["undated_mentions"]=[u for u in d["undated_mentions"] if "Stockholm" not in u]; fin(n,d)
# Malvik
n="Malvik";d=load(n);fin(n,d)
# Real Audiencia
n="Real_Audiencia_of_Guatemala";d=load(n);c=P+n+"#"
drop(d,"e2")
d["events"]+= [ ev("1786","ownership_structure","","Crown established intendancies in the area (Bourbon Reforms)",c+"15","both","in 1786 the crown established a series of intendancies")]
fin(n,d)
# Whitley
n="John_Henry_Whitley";d=load(n);c=P+n+"#"
fin(n,d)
# Seibu, Frederick unchanged
for n in ["Seibu_Shinjuku_Line","Frederick_Ralph_Sharp"]: fin(n,load(n))
# Butch
n="Butch_Levy";d=load(n);c=P+n+"#"
drop(d,"e16","e19","e10")
d["undated_mentions"].append("Broke foot midway through the 1941-42 season, missing the rest of the year (date not placeable)")
d["events"].append(ev("1997","family","","First wife Lucky died",c+"12","both","Lucky died in 1997"))
get(d,"e9")["flag"]="source_inconsistent"; fin(n,d)
# Telekids
n="Telekids";d=load(n);c=P+n+"#"
get(d,"e6")["evidence"][0]["quote"]="In the spring of 1993 Boszhard returned again"
for x in get(d,"e7")["evidence"]:
    if x["chunk_id"].endswith("#8"): x["quote"]="Starting in the 1993-1994 television season"
for i in ("e5","e16","e17"): get(d,i)["flag"]="source_inconsistent"
d["events"]+= [ev("1993","work","","Cartoon Express (Van Santen) began",c+"2","both","Cartoon Express ( 1993-1999 )"),
 ev("1999","work","","Cartoon Express ended",c+"2","both","Cartoon Express ( 1993-1999 )"),
 ev("1995","naming","","Teleteens became NOW TV when Veronica joined RTL",c+"2","both","When the omroep Veronica joined RTL as a channel in 1995")]
fin(n,d)
# Regius
n="Regius_Professor_Civil_Law";d=load(n);c=P+"Regius_Professor_of_Civil_Law_(Oxford)#"
rmev(d,"e53",c+"15");rmev(d,"e56",c+"20");rmev(d,"e60",c+"16");get(d,"e1")["flag"]="approximate_date"
d["events"]+= [ev("1546","role","","Robert Weston begins as professor (jointly with John Story)",c+"18","both","1546–1553 : Robert Weston"),
 ev("1989","role","","Peter Birks begins as professor per list (prose says 1988)",c+"20","both","1989–2004 : Peter Birks","source_inconsistent"),
 ev("2006-02","role","","Vacancy of the chair ends",c+"20","both","July 2004 – February 2006 : vacant")]
fin(n,d)
# Southern
n="Southern_Military_District";d=load(n);c=P+"Southern_Military_District_(Milo_S)#"
d["events"]+= [ev("1942","other","founding","I Military District (predecessor) created",c+"1","both","created in 1942"),
 ev("2000","other","medal","Commemorative Medal of the Southern Military District Staff established",c+"21","both","In 2000 , the Södra militärområdesstabens"),
 ev("1983","other","coat_of_arms","First staff coat of arms in use (1983–1994)",c+"19","both","Southern Military District Staff 1983–1994"),
 ev("1994","other","coat_of_arms","First staff coat of arms ceased (1983–1994)",c+"19","both","Southern Military District Staff 1983–1994"),
 ev("1994","other","coat_of_arms","Second staff coat of arms in use (1994–2000)",c+"20","both","Southern Military District Staff 1994–2000"),
 ev("2000","other","coat_of_arms","Second staff coat of arms ceased (1994–2000)",c+"20","both","Southern Military District Staff 1994–2000")]
fin(n,d)
