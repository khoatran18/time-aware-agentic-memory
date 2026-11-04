import json,sys,os
base="batchB1"
os.makedirs(f"{base}/rev",exist_ok=True)
def load(n): return json.load(open(f"{base}/sub/{n}.json"))
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=more
    if flag:e["flag"]=flag
    return e
def fin(n,d):
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

# no change
for n in ["Entropa","President_of_Uruguay"]: fin(n,load(n))

# Zhansaya Abdumalik
n="Zhansaya_Abdumalik";d=load(n);c=pre(d)
d["events"]+=[ev("2010","other","title","Earned Woman FIDE Master (WFM) title after silver at World Youth Championships",c+"1","both","In the 2010 World Youth Championships in Porto Carras",more=[ex(c+"1","description","As a result , she earned the title"),ex(c+"2","description","of Woman FIDE Master ( WFM )")]),
 ev("2014-01","other","academy","Zhansaya Abdumalik Chess Academy newly established; Karpov visited Almaty to open it",c+"7","both","In January 2014 , Anatoly Karpov visited Almaty to open the newly established Zhansaya Abdumalik Chess Academy")]
d["undated_mentions"]=[u for u in d["undated_mentions"] if "Woman FIDE Master" not in u]
fin(n,d)

# Anmer Hall
n="Anmer_Hall";d=load(n);c=pre(d)
drop(d,"e11")
d["events"]+=[ev("1990","affiliation","","Lease to Hugh van Cutsem began (rented for the next decade)",c+"9","both","It was subsequently rented for the next decade by Hugh van Cutsem",flag=DD),
 ev("2000","affiliation","","Lease to Hugh van Cutsem ended (after the decade)",c+"9","both","It was subsequently rented for the next decade by Hugh van Cutsem",flag=DD)]
d["undated_mentions"]=[u for u in d["undated_mentions"] if "van Cutsem" not in u]
fin(n,d)

# Humberto De la Calle
n="Humberto_De_la_Calle";d=load(n);c=pre(d)
d["events"]+=[ev("1993","role","","Liberal Party followers of Gaviria suggested him as possible presidential candidate",c+"5","both","In 1993 followers of President Gaviria from the Liberal Party suggested De la Calle as a possible presidential candidate")]
fin(n,d)

# New Orleans Baby Cakes
n="New_Orleans_Baby_Cakes";d=load(n)
drop(d,"e7","e14")
d["undated_mentions"].append("Season-level: finished 2005 home games three days before Hurricane Katrina; 2017 lifetime-pass promotion for Louisiana-born children (not placed as events)")
fin(n,d)

# Open Knowledge Foundation
n="Open_Knowledge_Foundation";d=load(n);c=pre(d)
d["events"]+=[ev("2011","other","sponsorship","Funding from OSF obtained for two fellowships (Gray and Murray-Rust)",c+"16","both","in 2011 Jonathan Gray and Peter Murray-Rust successfully obtained funding from OSF for two fellowships")]
fin(n,d)

# Licia Albanese
n="Licia_Albanese";d=load(n);c=pre(d)
d["events"]+=[ev("1974","other","founding","The Licia Albanese-Puccini Foundation founded",c+"24","both","The Licia Albanese-Puccini Foundation , founded in 1974")]
fin(n,d)

# ACS Poli Timisoara
n="ACS_Poli_Timi_oara";d=load(n);c=pre(d)
txt(d,"e10","Last season in the top division before relegation (stayed there until 1959)")
txt(d,"e21","State order forced public institutions to relinquish and reorganize sports clubs (privatization)")
txt(d,"e25","Temporary businessman ownership ended")
d["events"]+=[ev("1948","naming","","Played as CSU Timișoara in its first Divizia A season",c+"10","both","in 1948 , and played under the name CSU Timișoara in the first season"),
 ev("1991","ownership_structure","","Non-profit association AFC Politehnica Timișoara created to own club records and IP",c+"18","date","to relinquish and reorganize any owned sports clubs in 1991",more=[ex(c+"18","description","alongside the newly organized football club appeared a non-profit association , AFC Politehnica Timișoara")]),
 ev("2000","ownership_structure","","Local authorities accepted Claudio Zambon's bid to take over Politehnica",c+"21","both","before the local authorities accepted the bid of an Italian investor , Claudio Zambon , to take over Politehnica",flag=DD),
 ev("2011","affiliation","","Relegated to Liga II after failing to meet licence requirements",c+"30","both","the club was relegated to Liga II after failing to meet the licence requirements",flag=DD)]
d["undated_mentions"]=[u for u in d["undated_mentions"] if "1948–49 season: played as CSU" not in u]
d["undated_mentions"].append("Feb 2016: ACS Poli sole owner of Politehnica brand and records after court decision (as-of status)")
fin(n,d)

# Vologda
n="Vologda";d=load(n);c=pre(d)
flag(d,SI,"e1")
noflag(d,"e4","e6","e25")
get(d,"e49")["evidence"]=[ex(c+"43","date","On October 6 , 1996 , the first mayoral elections"),ex(c+"43","description","Alexey Yakunichev was elected and became the head of the city")]
fin(n,d)
