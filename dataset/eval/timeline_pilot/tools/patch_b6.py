import json,sys
base="batch6"
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
# Alemannia
n="Alemannia_Aachen";d=load(n);c=pre(d);flag(d,AP,"e4","e29","e32");drop(d,"e20")
addund(d,"Finished second in the Bundesliga 1968-69 (best ever result; season-level)")
d["events"]+=[ev("1999","role","","Trainer Werner Fuchs died unexpectedly",c+"12","date","In 1999 , the team played well and delivered an especially strong second half",None,[ex(c+"12","description","tragedy struck with the unexpected death of Fuchs")]),
 ev("1908","work","","Old Tivoli stadium built",c+"21","both","it was built in 1908")]
fin(n,d)
# Minuta slavy
n="Minuta_slavy";d=load(n);keep={"e1","e14","e16","e27","e29","e33","e47"}
drop(d,*[e["id"] for e in d["events"] if e["id"] not in keep])
txt(d,"e14","Weekly cash prize giveaway with Eldorado network (5 Oct-29 Dec 2009)");txt(d,"e27","International tournament held in two parts (9 and 16 July), judged by Garmash, Neyolova, Rodnina, Kusturica")
txt(d,"e33","First international competition on two scenes, two grand finals (3 and 17 June)");fin(n,d)
# Tryggve Gran
n="Tryggve_Gran";d=load(n);flag(d,AP,"e6","e21");drop(d,"e10","e44","e50")
txt(d,"e9","Accompanied geological expedition to the western mountains (Nov 1911-Feb 1912)");fin(n,d)
# Jerzy Buzek
n="Jerzy_Buzek";d=load(n);c=pre(d);noflag(d,"e27");drop(d,"e36","e38");und(d,"Resigned as chairman of AWS")
d["events"]+=[ev("2001","role","","Resigned as chairman of AWS Social Movement, replaced by Mieczyslaw Janowski",c+"9","both","Buzek resigned as the chairman of AWS Social Movement and was replaced by Mieczysław Janowski","derived_date")]
fin(n,d)
# John Mann
n="John_Mann__Baron_Mann";d=load(n);drop(d,"e12","e19","e20","e22","e24","e25","e26","e32");noflag(d,"e17")
txt(d,"e10","Campaigned to save Bassetlaw Hospital A&E department (2003-2004)");fin(n,d)
# Bal des debutantes
n="Bal_des_debutantes";d=load(n);drop(d,"e5");fin(n,d)
# Pelican Island
n="Pelican_Island_National_Wildlife_Refuge";fin(n,load(n))
# Jacqueline Cochran
n="Jacqueline_Cochran";d=load(n);flag(d,AP,"e2","e26","e42");txt(d,"e2","Married Robert Cochran (circa 1920)")
drop(d,"e16","e20","e24","e27","e39","e44","e46","e53","e54","e55","e56","e57","e58","e59")
txt(d,"e17","Distinguished Service Medal announced in War Department press release");txt(d,"e18","Set six world speed records in F-51 (1947-1951)")
txt(d,"e38","Set series of speed, distance, altitude records in Northrop T-38A (Aug-Oct 1961)")
txt(d,"e41","Set 69 intercity/intercapital records New Orleans to Bonn; first woman to fly a jet across the Atlantic")
txt(d,"e45","Set three world speed records in F-104C Starfighter (May-June 1964)");fin(n,d)
# D (band)
n="D__band_";d=load(n);c=pre(d);drop(d,"e4","e35","e54","e58","e60","e66","e67","e85")
txt(d,"e34","Genetic World tour (April-May 2009)");txt(d,"e52","Second European tour (first stop 20 April, last show 9 May in Russia)")
txt(d,"e56","Danzai no Gunner promotion tour (July-August)");txt(d,"e83","MASTER KEY tour (November to final on 11 December at Akasaka Blitz)")
get(d,"e30")["evidence"]=[ex(c+"38","both","Snow White ( January 21 , 2009 )")]
get(d,"e38")["evidence"]=[ex(c+"40","both","Kaze ga Mekuru Page ( 風がめくる頁 ) ( March 10 , 2010 )")]
get(d,"e39")["evidence"]=[ex(c+"46","both","7th Rose ( March 24 , 2010 )")]
for x in get(d,"e47")["evidence"]:
    if x["role"]=="description": x["quote"]="After returning to Japan , they released the single Torikago Goten"
und(d,"First EP New Blood","Hide-Zou replaced Sin","Mad Tea Party Magazine launched","Hiatus ended")
d["events"]+=[ev("2003-07-18","work","","Released first EP New Blood",c+"0","both","They released their first EP , New Blood on July 18","derived_date"),
 ev("2003-09-27","affiliation","","Ruiza released from hospital; D officially resumed activities with Hide-Zou replacing Sin",c+"1","both","Once Ruiza was released from the hospital on September 27 , D officially resumed activities with Hide-Zou replacing Sin on guitar","derived_date"),
 ev("2005-08-07","work","","Launched own publication Mad Tea Party Magazine",c+"5","date","August 7","derived_date",[ex(c+"4","description","D launched their own publication called Mad Tea Party Magazine on")]),
 ev("2015","other","hiatus","Hiatus ended (mid 2015)",c+"28","both","Ds hiatus ended in mid 2015",AP)]
fin(n,d)
# Eliot Engel
n="Eliot_Engel";d=load(n);c=pre(d);drop(d,"e19","e31","e41","e42","e49","e56");flag(d,AP,"e17")
d["events"]+=[ev("2003","other","vote","Voted against bill immunizing firearm manufacturers and dealers from civil liability",c+"28","both","He voted against a 2003 bill that immunized firearm manufacturers and dealers from civil liability for gun misuse")]
fin(n,d)
