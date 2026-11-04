import json,sys
base="batch7"
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
 
def addund(d,t): d["undated_mentions"].append(t)
# no change
for n in ["Konrad_Wolf_Film_University_of_Babelsberg","GMMTV","German_submarine_U_254"]: fin(n,load(n))
# Campaign Against Homophobia
n="Campaign_Against_Homophobia";d=load(n);c=pre(d);drop(d,"e5","e8","e9","e13");noflag(d,"e3")
txt(d,"e4","Robert Biedron's presidency ended; successor took over (name missing in source)");txt(d,"e7","President changed (names missing in source)")
txt(d,"e10","Agata Chaber's presidency began");txt(d,"e12","Agata Chaber's presidency ended; successor took over (name missing in source)")
for i in ("e2","e4"):
    get(d,i)["evidence"]=[ex(c+"12","both","Robert Biedroń , from 11 September 2001 to 22 February 2009")]
d["events"]+=[ev("2013","role","","Miroslawa Makuchowska appointed to ILGA-Europe executive board",c+"4","both","and in 2013 , Mirosława Makuchowska")]
fin(n,d)
# Talk im Turm
n="Talk_im_Turm";d=load(n);c=pre(d);drop(d,"e11","e14");txt(d,"e15","Comeback: five election specials with Erich Bohme (26 Aug-23 Sep 2002)")
get(d,"e5")["evidence"]=[ex(c+"1","both","In 1990 Florian Fischer-Fabian and Heidi Schüller presented the show together , in the course of the year they were replaced by Erich Böhme and Sandra Maischberger")]
d["events"]+=[ev("1998","role","","Erich Bohme's term as main presenter ended",c+"8","both","Erich Böhme ( 1990–1998 )")]
fin(n,d)
# Leahy
n="William_D__Leahy";d=load(n);c=pre(d);flag(d,AP,"e13")
get(d,"e18")["evidence"]=[ex(c+"13","date","in April 1918 went to command"),ex(c+"13","description","It was during this tour that he was awarded the Navy Cross")]
get(d,"e34")["evidence"]=[ex(c+"1","both","the United States Ambassador to France 1940–42")]
get(d,"e37")["evidence"]=[ex(c+"20","both","He was recalled in May 1942")]
get(d,"e38")["evidence"]=[ex(c+"22","both","On July 6 , 1942 , Leahy was appointed Chief of Staff to the Commander in Chief")]
get(d,"e43")["evidence"]=[ex(c+"27","both","Five months later , he went with President Truman to the Potsdam Conference")]
get(d,"e45")["evidence"]=[ex(c+"29","both","Leahy again retired from the Navy in March 1949")]
d["events"]+=[ev("1942-04-21","family","","Wife Louise Harrington Leahy died",c+"31","both","died with Leahy at her side on 21 April 1942")]
fin(n,d)
# Jimmy Lai
n="Jimmy_Lai";d=load(n);flag(d,AP,"e3","e18");drop(d,"e23");get(d,"e28")["flag"]="derived_date";fin(n,d)
# British Rail Class 40
n="British_Rail_Class_40";d=load(n);c=pre(d)
drop(d,"e2","e7","e9","e10","e11","e13","e14","e15","e16","e17","e20","e21","e23","e24","e29","e32","e34")
txt(d,"e1","Precursor prototype diesel locomotives ordered 1947-1954")
d["events"]+=[ev("2002-11-30","other","service","40 145 hauled enthusiasts railtour, first mainline passenger run by a Class 40 for over sixteen years",c+"34","both","on 30 November 2002 , over sixteen years after the last Class 40 had hauled a mainline passenger train")]
fin(n,d)
# Veliky Novgorod
n="Veliky_Novgorod";d=load(n);c=pre(d);noflag(d,"e6")
get(d,"e6")["evidence"]=[ex(c+"13","date","In 1136 , the Novgorodians dismissed their prince Vsevolod Mstislavich"),ex(c+"13","description","The year is seen as the traditional beginning of the Novgorod Republic")]
ev1=get(d,"e1")["evidence"];seen=[];new=[]
for x in ev1:
    k=(x["chunk_id"],x["quote"])
    if k not in seen: seen.append(k);new.append(x)
get(d,"e1")["evidence"]=new
d["events"]+=[ev("1080","work","","Visby merchants established trading post Gutagard in Novgorod",c+"12","both","At Novgorod in 1080 , Visby merchants established a trading post"),
 ev("1229","other","privileges","German merchants at Novgorod granted privileges",c+"12","both","in 1229 , German merchants at Novgorod were granted certain privileges"),
 ev("1240","other","battle","Swedish army defeated in the Battle of the Neva (Novgorodian sources)",c+"26","both","a Swedish army was defeated in the Battle of the Neva in 1240"),
 ev("1242","other","battle","Baltic German campaigns ended in failure after the Battle on the Ice",c+"26","both","The Baltic German campaigns ended in failure after the Battle on the Ice in 1242"),
 ev("1494","other","kontor","Hanseatic League kontor closed and goods seized by Muscovite forces",c+"27","both","The Hanseatic League kontor was closed in 1494"),
 ev("1603","work","","German trading post reestablished",c+"30","both","The German trading post was reestablished in 1603"),
 ev("1964","work","","Museum of wooden architecture established at Vitoslavlitsy",c+"53","both","a museum of wooden architecture was established in 1964"),
 ev("2006","other","airport","Yurievo commercial airport decommissioned",c+"55","both","Yurievo was decommissioned in 2006")]
fin(n,d)
# Hanover
n="Hanover";d=load(n);c=pre(d);drop(d,"e2","e25","e26","e27")
d["events"]+=[ev("2000","other","expo","Hosted Expo 2000 (Expo-Park site)",c+"45","both","the former site of EXPO 2000")]
fin(n,d)
