import json,sys,os
base="batchB6"
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
def undrop(d,*subs): d["undated_mentions"]=[u for u in d["undated_mentions"] if not any(s in u for s in subs)]
def quote(d,i,q): get(d,i)["evidence"][0]["quote"]=q

def setev(d,i,l): get(d,i)["evidence"]=l

# no change
for n in ["Line_15_Beijing_Subway","Milan_Metro_Line_3","MS_GNV_Azzurra","Rainier_Brewing_Company","Wetten_dass"]: fin(n,load(n))

# Orchard Supply Hardware
n="Orchard_Supply_Hardware";d=load(n);c=pre(d)
d["events"]+=[ev("2013-08","other","store_closure","Preparations made to close seventeen of the ninety-nine stores",c+"16","both","In August 2013 , preparations were made to close seventeen of the ninety-nine stores")]
fin(n,d)

# Sirotkin
n="Sergey_Sirotkin_racing_driver";d=load(n);c=pre(d)
D17=ex(c+"17","date","In January 2018 , he was announced by Williams as their new driver for the season")
d["events"]+=[ev("2011","other","title","Won the Formula Abarth European Series title",c+"3","description","He won the European Series title with a race to spare",more=[ex(c+"2","date","Sirotkin remained in Formula Abarth , and with Jenzer , for a second season in 2011")],flag=DD),
 ev("2012","other","win","Scored first Auto GP win at Valencia, becoming the youngest Auto GP winner",c+"5","description","becoming the youngest Auto GP winner in the process",more=[ex(c+"4","date","In 2012 , Sirotkin continued his collaboration with Euronova Racing into the Auto GP World Series")],flag=DD),
 ev("2014","other","win","Won his first Formula Renault 3.5 Series race at Moscow Raceway",c+"9","description","won his first Formula Renault 3.5 Series race on his home soil at Moscow Raceway",more=[ex(c+"9","date","For 2014 Sirotkin switched to the Fortec Motorsport team")]),
 ev("2015","other","win","Won first GP2 race, the feature race at Silverstone",c+"10","description","He achieved his first victory at Silverstone",more=[ex(c+"10","date","In February 2015 , it was announced that Sirotkin would debut in the series with Rapax")],flag=DD),
 ev("2018","other","points","Scored his first World Championship point after Grosjean's disqualification",c+"23","description","scoring his first ever World Championship point after Romain Grosjean was disqualified for technical infringements",more=[D17],flag=DD),
 ev("2018","role","","Announced he would not continue with Williams in 2019 after SMP Racing ended its backing",c+"27","description","it was announced that Sirotkin would not continue to race with Williams in 2019",more=[D17],flag=DD)]
fin(n,d)

# Panair
n="Panair_do_Brasil";d=load(n);c=pre(d)
setev(d,"e38",[ex(c+"23","description","allotted its international route concessions to Varig and domestic to Cruzeiro do Sul"),ex(c+"23","date","forced to cease operations abruptly on February 10 , 1965")])
d["events"]+=[ev("1965","other","joint service","Voo da amizade joint service with TAP ended",c+"20","both","Between November 30 , 1960 and 1965 Panair operated with TAP-Transportes Aéreos Portugueses the Voo da amizade")]
fin(n,d)

# Mike Lee
n="Mike_Lee_American_politician";d=load(n);c=pre(d)
d["events"]+=[ev("2010","role","","Lee's name placed on the Republican primary ballot after the state convention",c+"13","description","Both Bridgewater and Lee received enough support to have their names placed on the primary ballot",more=[ex(c+"12","date","Lee ran for the U.S . Senate in 2010")],flag=DD)]
fin(n,d)

# U-96
n="German_submarine_U_96_1940";d=load(n);c=pre(d)
drop(d,"e14","e25","e49","e70")
txt(d,"e20","Sinks British ship Black Osprey from convoy HX 107")
D=lambda k,q:ex(c+k,"date",q)
S="On 2 August 1941 , U-96 left for her sixth patrol in the North Atlantic"
setev(d,"e26",[ex(c+"27","description","U-96 made for port in St . Nazaire , France , where she arrived after 30 days at sea on 28 February"),D("23","On 23 February 1941 , U-96 made contact with convoy OB 288")])
setev(d,"e28",[ex(c+"29","description","On 16 April , the U-boat made contact with convoy OB 309 and was immediately attacked by an escort"),D("29","On 12 April 1941 U-96 set to sea again for her fourth war patrol")])
setev(d,"e43",[ex(c+"38","description","On 12 August , the U-boat was part of group Greenland"),D("38",S)])
setev(d,"e44",[ex(c+"38","description","Two weeks later , on 28 August , she joined group Prince-Elector"),D("38",S)])
setev(d,"e46",[ex(c+"38","description","On 12 September she entered St.Nazaire after 42 days at sea"),D("38",S)])
flag(d,DD,"e26","e28","e43","e44","e46")
d["undated_mentions"].append("Ships whose names are missing in the source (sunk 16 Jan 1941, OB 288 commodore's ship 24 Feb 1941, Dutch ship hit 31 Oct 1941, sick crew transfer 3 Jan 1943) are not recorded as events")
fin(n,d)
