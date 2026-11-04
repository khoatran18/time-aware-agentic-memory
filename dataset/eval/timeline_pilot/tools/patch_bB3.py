import json,sys,os
base="batchB3"
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

# no change
for n in ["Rush_Holt_Jr","Irene_Kharisma_Sukandar","Hugh_Scott","World_Festival_of_Black_Arts"]: fin(n,load(n))

# Milton Friedman
n="Milton_Friedman";d=load(n);c=pre(d)
d["events"]+=[ev("1945-02-12","family","birth of son","Son David D. Friedman born",c+"25","both","On February 12 , 1945 , his only son , David D . Friedman"),
 ev("1966","work","","Began weekly columns for Newsweek magazine (to 1984)",c+"29","both","weekly columns for Newsweek magazine ( 1966–84 )"),
 ev("1980","work","","Companion book Free To Choose published, bestselling nonfiction book of 1980",c+"40","both","was the bestselling nonfiction book of 1980"),
 ev("1996","other","founding","Founded the Friedman Foundation for Educational Choice with his wife",c+"73","both","In 1996 , Friedman , together with his wife , founded the Friedman Foundation for Educational Choice")]
fin(n,d)

# Razorfish
n="Razorfish_company";d=load(n);c=pre(d)
d["events"]+=[ev("2000-02","other","media","Founders Kanarick and Dachis interviewed on 60 Minutes II; widely viewed as a disaster",c+"13","both","In February 2000 , Craig Kanarick and Jeff Dachis were interviewed by Bob Simon on 60 Minutes II"),
 ev("2006","other","award","Forrester ranked Razorfish a top-tier web design agency in its Web Design Agency Shootout",c+"23","both","Forrester Research ranked it as a top-tier web design agency in its 2006 Web Design Agency Shootout"),
 ev("2007-05-18","ownership_structure","announcement","Microsoft announced its intention to acquire Avenue A | Razorfish (via aQuantive)",c+"16","both","Microsoft announced on May 18 , 2007 its intention to acquire Avenue A | Razorfish"),
 ev("2007-12","other","award","Forrester Wave report on interactive marketing agencies cited Razorfish as a leader",c+"23","date","report published in December 2007",more=[ex(c+"22","description","Forrester Research cited the company as a leader in")]),
 ev("2012","other","award","Ad Age placed Razorfish number 4 on its Agency A-List",c+"24","both","2012 . Ad Age placed Razorfish at number 4 on their annual Agency A-List"),
 ev("2013","other","award","Ad Age placed Razorfish number 9 on its Agency A-List",c+"24","both","In 2013 , Razorfish was again recognized by Ad Age , placing number 9 on their annual Agency A-List")]
fin(n,d)

# First Things
n="First_Things";d=load(n);c=pre(d)
txt(d,"e12","David Blum begins as executive/senior editor")
d["events"]+=[ev("2010","role","","David Blum's executive/senior editor term ends",c+"15","both","David Blum ( 2010 )"),
 ev("2017-05","role","","Shalom Carmy begins regular column Litvak at large",c+"12","both","Since May 2017 Shalom Carmy")]
fin(n,d)

# Hsu Hsin-liang
n="Hsu_Hsin_liang";d=load(n);c=pre(d)
txt(d,"e25","Ended Pan-Blue Coalition support")
flag(d,SI,"e18","e24")
d["events"]+=[ev("1979","role","removal","Impeached by the government and removed from office for two years",c+"3","description","The government impeached him and removed him from office for two years",more=[ex(c+"3","date","Hsu was involved in opposition activity during the first part of 1979")],flag=DD),
 ev("2004","other","endorsement","Publicly supported Lien Chan and James Soong in the 2004 presidential election",c+"9","both","Hsu publicly supported Lien Chen and James Soong in the 2004 presidential election"),
 ev("2004-03","other","declaration","Co-published the Joint Declaration of the Tang Wai participants criticising Chen Shui-bian",c+"9","both","In March 2004 , Hsu and a dozen other prominent politicians involved in the Tangwai movement published The Joint Declaration"),
 ev("2008","other","endorsement","Supported DPP candidate Frank Hsieh in the 2008 presidential election",c+"14","both","Hsu then came out to support DPP candidate Frank Hsieh in the 2008 presidential election"),
 ev("2013-04","other","statement","Called for cross-strait political dialogue at a press conference",c+"16","both","In mid-April 2013 during a press conference , Hsu called for a cross-strait political dialogue")]
undrop(d,"Impeached and removed")
fin(n,d)

# Henry Stommel
n="Henry_Stommel";d=load(n);c=pre(d)
d["events"]+=[ev("1978","affiliation","","Left MIT and returned to Woods Hole until his retirement",c+"2","both","where he remained until 1978 , returning to Woods Hole until his retirement",flag=DD)]
undrop(d,"Returned to Woods Hole")
fin(n,d)

# Permanent Secretary to the Treasury
n="Permanent_Secretary_to_the_Treasury";d=load(n);c=pre(d)
d["events"]+=[ev("1909","other","incident","Sir George Murray lobbied Crossbench peers to reject the Chancellor's budget, breaching neutrality",c+"1","both","in 1909 Sir George Murray was involved in lobbying various Crossbench peers in the House of Lords"),
 ev("2014","other","incident","Sir Nicholas Macpherson published private advice to the Chancellor during the Scottish referendum campaign",c+"1","both","In 2014 , during the Scottish Independence referendum campaign , Sir Nicholas Macpherson broke with convention by publishing private advice")]
d["undated_mentions"].append("Since March 2009 Tom Scholar served as Second Permanent Secretary; Head of Government Economic Service held by Nicholas Stern until June 2007 (other posts, not recorded)")
fin(n,d)
