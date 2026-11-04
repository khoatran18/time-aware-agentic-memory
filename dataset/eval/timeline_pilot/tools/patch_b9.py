import json,sys
base="batch9"
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
for n in ["David_Morgan_art_historian","SCM_Gloria_Buz_u","Chicago_Red_Stars","Luftflotte_3"]: fin(n,load(n))
# Costa Allegra
n="MS_Costa_Allegra";d=load(n);c=pre(d)
d["events"]+=[ev("2010","affiliation","","Chartered to the Paquet Cruises brand for eleven cruises (four spring, seven autumn)",c+"10","both","used Costa Allegra , marketed in France under the name Allegra and the Paquet Cruises brand , for four spring cruises and seven cruises in autumn of 2010")]
fin(n,d)
# BAMF
n="Federal_Office_for_Migration_and_Refugees";d=load(n);drop(d,"e11");txt(d,"e3","Bribe scandal (2000-2018): agency alleged to have accepted bribes for asylum grants")
fin(n,d)
# Sam Selvon
n="Sam_Selvon";d=load(n);c=pre(d)
d["events"]+=[ev("1938","education","","Left Naparima College at age 15 to work",c+"1","both","before leaving at the age of 15 to work",flag=DD)]
fin(n,d)
# Janet Frame
n="Janet_Frame";d=load(n)
get(d,"e3")["date"]="1945";get(d,"e3")["grain"]="year";get(d,"e4")["date"]="1945";get(d,"e4")["grain"]="year"
drop(d,"e72","e73","e74","e75","e76","e77","e78","e79")
fin(n,d)
# Late Late Show
n="The_Late_Late_Show_American_talk_show";d=load(n);c=pre(d);flag(d,SI,"e3")
d["events"]+=[ev("2004-09-20","role","","Series of guest-host on-air auditions began; Drew Carey first guest host",c+"26","both","Drew Carey was the first guest host on September 20 , 2004"),
 ev("2015-02-20","role","","Peter Lassally retired as executive producer with the taping of Arnett's show",c+"48","both","retired from television after a six decade career with the taping of Arnetts show on February 20 , 2015"),
 ev("2015-03-23","other","format","House band introduced with Corden; Reggie Watts first bandleader",c+"50","both","Cordens hosting tenure is the first to have a house band",flag=DD)]
fin(n,d)
# Los Angeles Rams
n="Los_Angeles_Rams";d=load(n);c=pre(d)
drop(d,"e18","e22","e23","e24","e28","e29","e34","e36","e37")
get(d,"e47")["evidence"]=[ex(c+"5","date","St . Louis in 1999"),ex(c+"3","description","the team won Super Bowl XXXIV in a 23\u201316 victory over the Tennessee Titans")]
get(d,"e58")["date"]="2008-12-22";get(d,"e58")["evidence"]=[ex(c+"74","both","after the resignation of former president of football operations and general manager Jay Zygmunt on December 22")]
get(d,"e86")["evidence"]=[ex(c+"91","both","The Rams relocated to their new stadium in Inglewood in 2020")]
flag(d,AP,"e70")
d["undated_mentions"]=[u for u in d["undated_mentions"] if "Suspended operations" not in u]
d["undated_mentions"].append("NFC Championship Game losses and playoff exits in 1967, 1974, 1975, 1976, 1978, 1985 and 1989 (season results)")
d["events"]+=[ev("1936","affiliation","","Joined the newly formed American Football League",c+"6","date","The Cleveland Rams were founded in 1936 by Ohio attorney Homer Marshman",more=[ex(c+"6","description","The team was part of the newly formed American Football League")]),
 ev("1943","other","suspension","Suspended operations and sat out the season because of a player shortage in World War II",c+"10","both","The franchise suspended operations and sat out the 1943 season because of a shortage of players during World War II"),
 ev("2015-02-24","location","","Inglewood City Council approved the new stadium",c+"91","both","On February 24 , 2015 , the Inglewood City Council approved the stadium and the initiative"),
 ev("2016-01-15","location","","Press conference at The Forum announcing return to Los Angeles",c+"93","both","The team held a press conference at The Forum in Inglewood on January 15 , 2016 , to announce its return to Los Angeles")]
fin(n,d)
