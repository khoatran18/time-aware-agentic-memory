import json,sys
base="batch4"
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
def noflag(d,*ids):
    for i in ids: get(d,i).pop("flag",None)
# Stefan Hesse
n="Stefan_He_e";d=load(n);txt(d,"e1","Born");noflag(d,"e18","e21");und(d,"Attended George","Studied theology");fin(n,d)
# Steele Hall
n="Steele_Hall";d=load(n);txt(d,"e1","Born");noflag(d,"e8","e24");fin(n,d)
# SCAF
n="Supreme_Council_of_the_Armed_Forces";d=load(n);drop(d,"e14","e16");fin(n,d)
# Washington Spirit
n="Washington_Spirit";d=load(n);drop(d,"e10","e24","e28");flag(d,AP,"e18");fin(n,d)
# Maidan
n="Maidan_Nezalezhnosti";d=load(n);c=d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
txt(d,"e2","Khreshchatyk Square name ended (used until 1871)")
d["events"]+=[ev("1894","work","","Kyiv tram line reached the square",c+"15","both","reached the square in 1894"),
 ev("2014-02","work","","Trade-Unions House severely damaged by fire",c+"25","both","Trade-Unions House was severely damaged during the fire in February 2014")]
fin(n,d)
# Monir
n="Monir_Shahroudy_Farmanfarmaian";d=load(n);c=d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
drop(d,"e28","e29","e31");txt(d,"e1","Born (lifespan start; source gives 16 December 1922)")
d["events"]+=[ev("1991","family","","Husband Abolbashar Farmanfarmaian died of leukemia",c+"14","both","In 1991 , Abolbashar died of leukemia")]
fin(n,d)
# Condor
n="Condor__airline";d=load(n);c=d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
drop(d,"e2","e16");get(d,"e17")["evidence"]=[ex(c+"13","date","During 1995 , Condor expanded its shareholdings in other ventures"),ex(c+"13","description","assumed ownership of the 40% stake held by parent airline Lufthansa in SunExpress")];noflag(d,"e17");flag(d,AP,"e35")
for x in get(d,"e9")["evidence"]:
    if x["chunk_id"].endswith("#8"): x["quote"]="In 1961 , Deutsche Flugdienst took over its rival Condor-Luftreederei ( which had been founded in 1957 by Oetker ) , subsequently changing its name to Condor Flugdienst GmbH"
d["events"]+=[ev("2013-10-01","naming","","Thomas Cook Group introduced unified brand symbol; Sunny Heart added to aircraft tails",c+"22","both","On 1 October 2013 , the Thomas Cook Group began presenting itself under the new unified brand symbol"),
 ev("1996","other","livery","Boeing 757 redecorated by James Rizzi as flying work of art for 40th anniversary",c+"14","both","1996 was Condor Flugdienst GmbHs 40th anniversary ; to mark the occasion , American artist James Rizzi redecorated a Boeing 757")]
fin(n,d)
# Meet the Press
n="Meet_the_Press";d=load(n);c=d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
drop(d,"e29","e30","e31");und(d,"Ronald Reagan","Brian Williams","Mark Whitaker")
d["events"]+=[ev("2014-08-14","role","","Announced Chuck Todd would take over as moderator",c+"27","both","On August 14 , 2014 , Turness announced")]
fin(n,d)
# TU Leuna
n="Technical_University_Leuna_Merseburg";d=load(n);c=d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
get(d,"e56")["evidence"]=[ex(c+"19","date","1967 : Institute of Socialist Economic Management"),ex(c+"19","description","the Institute of Petroleum Chemistry and Organic Intermediates was formed from the Institutes")]
get(d,"e57")["evidence"]=[ex(c+"19","date","1967 : Institute of Socialist Economic Management"),ex(c+"19","description","the Institute of Anorganic and Technical Chemistry was formed from the Institutes")]
fin(n,d)
# Matthias Blubaum
n="Matthias_Bl_baum";d=load(n);txt(d,"e1","Born")
get(d,"e18")["evidence"]=[ex(get(d,"e16")["evidence"][0]["chunk_id"],"description","from 25 October to 2 November , he achieved his third GM norm"),ex(get(d,"e16")["evidence"][1]["chunk_id"],"date","At the 2014 Bavarian Chess Championship , held")];noflag(d,"e18")
txt(d,"e18","Earned third GM norm at 2014 Bavarian Chess Championship (25 Oct-2 Nov)")
for b,e,t in [("e26","e28","Competed in Aeroflot Open (21 Feb-1 Mar); tied for 21st"),("e30","e32","Competed in European Individual Chess Championship (30 May-10 Jun); 12th, qualified for World Cup"),
 ("e34","e35","Competed in 45th Dortmund Sparkassen Chess Meeting (15-22 Jul); fifth"),("e37","e38","Played board 3 for Germany at European Team Chess Championship (28 Oct-6 Nov); Germany eighth"),
 ("e41","e42","Competed in 5th Grenke Chess Classic (31 Mar-9 Apr); sixth, beat Anand"),("e45","e46","Played board 3 for Germany at 43rd Chess Olympiad (24 Sep-5 Oct); Germany 13th"),
 ("e49","e50","Competed in Grenke Chess Open (18-22 Apr); sixth on tiebreak"),("e51","e52","Competed in German Masters, Magdeburg (25 May-1 Jun); fifth of eight"),
 ("e53","e54","Competed in FIDE Grand Swiss (10-21 Oct); placed 81st"),("e55","e56","Played for Germany at European Team Chess Championship, Batumi (24 Oct-2 Nov); Germany eighth"),
 ("e61","e62","Competed in Tegernsee Masters (31 Oct-8 Nov); second")]:
    txt(d,b,t); drop(d,e)
drop(d,"e16");fin(n,d)
