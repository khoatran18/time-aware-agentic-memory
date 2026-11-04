import json,sys
base="batch2"
def load(n): return json.load(open(f"{base}/sub/{n}.json"))
def ev(date,track,label,text,chunk,role,quote,flag=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if flag:e["flag"]=flag
    return e
def fin(n,d):
    d["events"]=sorted(d["events"],key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def drop(d,*ids): d["events"]=[e for e in d["events"] if e["id"] not in ids]
def get(d,i): return next(e for e in d["events"] if e["id"]==i)
def und(d,*keys): d["undated_mentions"]=[u for u in d["undated_mentions"] if not any(k in u for k in keys)]
def dv(d,*ids):
    for i in ids: get(d,i)["flag"]="derived_date"
D="derived_date"
# Aero Union
n="Aero_Union";d=load(n);c="/wiki/Aero_Union#"
d["events"]+=[ev("1961","ownership_structure","","Purchased first two B-17 Flying Fortresses",c+"1","both","The following year they purchased their first two B-17 Flying Fortresses",D),
 ev("1961","naming","","Company renamed Aero Union",c+"1","both","changed their name to Aero Union",D),
 ev("2007-08","work","","MAFFS II flight testing took place",c+"12","both","with flight testing that following August",D),
 ev("2011-08","ownership_structure","","Failed to make lease payments to the City of Chico",c+"7","both","August Aero Union failed to make its lease payments to the City of Chico",D),
 ev("2011-09","location","","City of Chico declared the lease invalid",c+"7","both","the lease was declared invalid by the city that September",D)]
und(d,"Bought first two B-17","Failed to make lease","City of Chico declared","flight testing"); fin(n,d)
# August Maus
n="August_Maus";d=load(n);c="/wiki/August_Maus#"
drop(d,"e11","e12")
d["events"]+=[ev("1934-09-27","affiliation","","Assigned to a light cruiser",c+"1","both","and one day later , he was assigned to the light cruiser",D),
 ev("1937-04-01","affiliation","","Returned to the cruiser Nürnberg",c+"3","both","On 1 April 1937 he was promoted to Leutnant zur See and returned to the cruiser Nürnberg"),
 ev("1943-08-11","other","combat","U-185 shot down a B-24 bomber during the U-604 rescue",c+"7","both","Maus of U-185 ordered to open fire on the aircraft , which was shot down , killing ten men",D),
 ev("1943-08-24","other","scuttling","Gave order to abandon and scuttle U-185",c+"8","both","August Maus gave the order to abandon ship and scuttle",D)]
und(d,"one day later","B-24","abandon ship"); fin(n,d)
# CS Aerostar
n="CS_Aerostar_Bacau";d=load(n);c="/wiki/CS_Aerostar_Bacău#"
drop(d,"e8"); dv(d,"e4","e6","e10")
d["events"]+=[ev("1995","role","","Doru Damaschin became the new club president",c+"11","both","in the summer of 1995 . The Airmen were enrolled in the Divizia D , having in the lead also a new president , in the person of Doru Damaschin"),
 ev("2018","affiliation","","Promoted back to Liga II",c+"15","both","Aerostar promoted back to Liga II after 26 years of absence and 18 years after its return in the Liga III , in 1999",D)]
und(d,"Doru Damaschin","Promoted back to Liga II")
d["undated_mentions"].append("Excluded from Divizia C over financial problems during the 1993–94 season (season-level, not placeable in a year)"); fin(n,d)
# First Air Group
n="First_Air_Group";d=load(n);c="/wiki/First_Air_Group#"
d["events"]+=[ev("1957-09-30","role","","Deputy commander position added after the airbase areas were decommissioned",c+"12","both","After the airbase areas were decommissioned on 30 September 1957 , a deputy commander position was added")]
e=ev("1995","ownership_structure","","Traditions and history transferred to the Chief of Air Force Staff",c+"8","date","until it was decommissioned in 1995")
e["evidence"].append({"chunk_id":c+"9","role":"description","quote":"the traditions and history of the First Air Group were transferred to the Chief of Air Force Staff"})
d["events"].append(e); und(d,"Deputy commander position added"); fin(n,d)
# Klemzig
n="Klemzig_South_Australia";d=load(n)
drop(d,"e2","e3","e4","e5","e7","e8","e9","e11","e12","e13","e14","e15","e16","e17","e18","e19"); fin(n,d)
# Lev
n="Lev_Polugaevsky";d=load(n);c="/wiki/Lev_Polugaevsky#"
get(d,"e24")["evidence"][0]["quote"]="the New in Chess Editorial team , 1995"
d["events"].append(ev("1969","other","collaboration","Worked with Boris Spassky preparing his world championship match",c+"11","both","Polugaevsky had worked with Boris Spassky as the latter was preparing for his successful 1969 world championship match"))
und(d,"one of the strongest players","by the late 1960s"); fin(n,d)
# Martin
n="Martin_de_Gurrea_y_Aragon";d=load(n);c="/wiki/Martín_de_Gurrea_y_Aragón#"
d["events"].append(ev("1581","role","","Duchy of Villahermosa, County of Ribagorza and other titles inherited by son Fernando",c+"12","both","finally dying in 1581 . The Duchy of Villahermosa , County of Ribagorza and his other titles were inherited by his son Fernando")); fin(n,d)
# Quelli
n="Quelli_che_il_Calcio";d=load(n); drop(d,"e13","e18"); fin(n,d)
# Fearnley
n="Thomas_Fearnley";d=load(n);c="/wiki/Thomas_Fearnley#"
dv(d,"e12","e19")
d["events"]+=[ev("1833","location","","Visited Sicily",c+"7","both","visited Sicily the following summer",D),
 ev("1836","location","","Visited London",c+"7","both","visited London the next year",D)]
und(d,"Sicily","London","went to Germany"); fin(n,d)
# Toungoo
n="Toungoo_dynasty";d=load(n);c="/wiki/Toungoo_dynasty#"
get(d,"e4")["text"]="Burmese–Siamese War begins; Tabinshwehti defeated at Ayutthaya."; dv(d,"e5")
d["events"].append(ev("1740","other","rebellion","Mon rebellion in Lower Burma began, founding the Restored Hanthawaddy Kingdom",c+"4","both","In 1740 , the Mon people in Lower Burma began a rebellion , founding the Restored Hanthawaddy Kingdom")); fin(n,d)
