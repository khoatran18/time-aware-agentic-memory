import json,sys,os
base="batchB7"
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
for n in ["Andrzej_Panufnik","Archaeologia_Cambrensis","Westover_Plantation"]: fin(n,load(n))

# Pelican egg
n="Pelican_Faberg_egg";d=load(n)
get(d,"e1")["evidence"][2]["role"]="description"
txt(d,"e4","Period began in which Lillian Thomas Pratt purchased the egg from Hammer Galleries (between 1936 and 1938)")
txt(d,"e5","Period ended in which Lillian Thomas Pratt purchased the egg from Hammer Galleries")
fin(n,d)

# Exxon Valdez
n="Exxon_Valdez";d=load(n);c=pre(d)
setev(d,"e10",[ex(c+"10","description","which renamed the ship , once again , to Dong Fang Ocean"),ex(c+"10","date","In early 2008 , SeaRiver Maritime")])
d["events"]+=[ev("2012-07-30","other","permission","Supreme Court of India granted permission to beach Oriental Nicety at Alang for dismantling",c+"13","description","the Supreme Court of India granted permission for the owners of Oriental Nicety to beach her at Gujarat coast to be dismantled",more=[ex(c+"12","date","On 30 July 2012 ,")])]
fin(n,d)

# CEU
n="Central_European_University";d=load(n);c=pre(d)
d["events"]+=[ev("1996","other","start","CEU Summer University began",c+"55","both","Since 1996 , CEUs Summer University has involved 269 Hungarian faculty members"),
 ev("2007-10-14","role","","Leon Botstein elected new Chairman of the CEU Board for a two-year term",c+"12","description","was elected as new Chairman for a two-year term",more=[ex(c+"12","date","On 14 October 2007 George Soros stepped down as Chairman of CEU Board")],flag=DD),
 ev("2017-03-29","other","press conference","Ignatieff and pro-rectors held a press conference against the higher education bill",c+"20","description","Éva Fodor held a press conference",more=[ex(c+"20","date","On 29 March 2017 , Michael Ignatieff , the President and Rector of CEU")]),
 ev("2020","other","start","Two new bachelors degree programs introduced in the 2020-2021 academic year",c+"40","both","two new bachelors degree programs were introduced in the 2020-2021 academic year",flag=AP)]
fin(n,d)

# Mannheim Observatory
n="Mannheim_Observatory";d=load(n);c=pre(d)
d["events"]+=[ev("1769-06-03","other","observation","Mayer observed the second Transit of Venus in St Petersburg",c+"4","both","Mayer travelled for a year to St . Petersburg and observed there , another Transit of Venus on 3 June 1769"),
 ev("1866","work","","First variable star observation results published",c+"16","both","Nos . 32 and 39 ( 1866 and 1875 )"),
 ev("1875","work","","Second variable star observation results published",c+"16","both","Nos . 32 and 39 ( 1866 and 1875 )")]
fin(n,d)

# HMS Warrior
n="HMS_Warrior_R31";d=load(n);c=pre(d)
d["events"]+=[ev("1953","other","refit","Refit at Devonport Dockyard ended",c+"24","both","The ship underwent refit during most of 1952 and 1953 at Devonport Dockyard",flag=AP),
 ev("1945-05","work","","Negotiations completed with Canada for the naval air squadrons to man the carrier",c+"12","description","Negotiations were completed in May for the naval air squadrons that would be needed to man the aircraft carrier",more=[ex(c+"11","date","negotiations being finalised in April 1945")],flag=DD)]
fin(n,d)

# The News Quiz
n="The_News_Quiz";d=load(n);c=pre(d)
d["events"]+=[ev("2013-06-28","work","","The News Quiz paid tribute to Radio 4 announcer Rory Morrison",c+"3","both","On 28 June 2013 , the News Quiz paid tribute to Radio 4 announcer Rory Morrison")]
fin(n,d)

# Charles Holden
n="Charles_Holden";d=load(n);c=pre(d)
d["events"]+=[ev("1905","work","","Wrote anonymous essay If Whitman had been an Architect",c+"73","both","In 1905 , in an essay titled If Whitman had been an Architect , Holden made an anonymous plea to architects"),
 ev("1913","affiliation","","Lionel Pearson became partner; practice renamed Adams, Holden & Pearson",c+"25","both","Adams , Holden & Pearson when Lionel Pearson became a partner in 1913"),
 ev("1951","other","honour","Declined a knighthood for the second time",c+"80","both","He twice declined a knighthood , in 1943 and 1951"),
 ev("1953","other","sponsorship","Acted as sponsor at the RIBA Royal Gold Medal award to Le Corbusier",c+"67","both","when he acted as a sponsor at the award of the RIBAs Royal Gold Medal to Le Corbusier in 1953"),
 ev("1957","work","","Wrote a 1957 essay on architecture",c+"77","both","In a 1957 essay on architecture , he wrote")]
fin(n,d)
