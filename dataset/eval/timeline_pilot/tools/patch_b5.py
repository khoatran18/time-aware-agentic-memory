import json,sys
base="batch5"
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
def und(d,*keys): d["undated_mentions"]=[u for u in d["undated_mentions"] if not any(k in u for k in keys)]
def flag(d,f,*ids):
    for i in ids: get(d,i)["flag"]=f
def ex(chunk,role,quote): return {"chunk_id":chunk,"role":role,"quote":quote}
AP="approximate_date"
def txt(d,i,t): get(d,i)["text"]=t
def txt(d,i,t): get(d,i)["text"]=t
def noflag(d,*ids):
    for i in ids: get(d,i).pop("flag",None)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
# Antonio, Wilhelm: no change
for n in ["Antonio_Razzi","Wilhelm_Liebknecht"]: fin(n,load(n))
# USS LCS
n="USS_LCS_L__3__102";d=load(n);drop(d,"e5");noflag(d,"e4");txt(d,"e4","Participated in Gunto operation (Battle of Okinawa), 18-30 June");fin(n,d)
# Ich bin ein Star
n="Ich_bin_ein_Star__Holt_mich_hier_raus_";d=load(n);c=pre(d);flag(d,AP,"e3")
d["events"]+=[ev("2021-01-15","work","","Spin-off Die grosse Dschungelshow began airing",c+"3","both","on 15 January 2021 will begin airing a spin-off show")]
fin(n,d)
# Journal de 20 heures
n="Journal_de_20_heures";d=load(n);c=pre(d);noflag(d,"e10");drop(d,"e12","e13");und(d,"Jean-Marie Cavada")
d["events"]+=[ev("1975-01-06","role","","Jean-Marie Cavada was the first presenter",c+"1","date","installed Le Journal dAntenne 2 every evening at 8 p.m . on 6 January 1975",None,[ex(c+"1","description","Jean-Marie Cavada was the first presenter")]),
 ev("1992-09-07","naming","","Antenne 2 became France 2",c+"3","both","On 7 September 1992 , Antenne 2 became France 2"),
 ev("2017-09-10","work","","20h30 le dimanche began airing after 20 Heures on Sundays",c+"6","both","September 10 , 2017 , after 20 Heures , for about 30 minutes on Sundays comes 20h30 le dimanche")]
fin(n,d)
# Lothar
n="Lothar_von_Trotha";d=load(n);c=pre(d);drop(d,"e4")
d["events"]+=[ev("1905","family","","First wife Bertha Neumann died",c+"2","both","Bertha Neumann , who died in 1905")]
fin(n,d)
# Allsang
n="Allsang_pa_Skansen";d=load(n);txt(d,"e12","Anders Lundin also hosted in 2003 (list note)");fin(n,d)
# Agenzia
n="Agenzia_Nazionale_Stampa_Associata";d=load(n);drop(d,"e33","e34")
txt(d,"e13","Giovanni Giovannini became ANSA president");txt(d,"e16","Giovanni Giovannini's term as ANSA president ended");txt(d,"e31","ANSA scooped world media on Pope Benedict XVI's resignation")
fin(n,d)
# Dark Eye
n="The_Dark_Eye";d=load(n);flag(d,AP,"e5","e23");fin(n,d)
# One Show
n="The_One_Show";d=load(n);c=pre(d);drop(d,"e25","e44");flag(d,"source_inconsistent","e27");txt(d,"e28","Matt Baker announced as Manford's replacement")
und(d,"Myleene Klass replaced")
d["events"]+=[ev("2007-07-09","role","","Myleene Klass replaced Nadia Sawalha as co-host",c+"9","both","Sawalha was replaced by Myleene Klass","derived_date"),
 ev("2011","role","","Alex Jones and Matt Baker began co-hosting together",c+"1","both","who hosted together between 2011 and 2020")]
fin(n,d)
