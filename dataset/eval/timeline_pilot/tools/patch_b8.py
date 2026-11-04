import json,sys
base="batch8"
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
for n in ["Republic_of_Cospaia","Corpus_vasorum_antiquorum"]: fin(n,load(n))
# St Luke's
n="St_Luke_s_Anglican_Church_Liverpool";d=load(n);c=pre(d)
d["events"]+=[ev("1840","work","","Rectory replaced",c+"1","both","A rectory was built about the same time but was replaced in 1840"),
 ev("1820-12","other","visit","Governor Macquarie attended a service",c+"2","both","Governor Macquarie attended a service in December 1820")]
fin(n,d)
# Amalric
n="Amalric_of_Jerusalem";d=load(n);c=pre(d)
d["events"]+=[ev("1163","family","","Marriage to Agnes of Courtenay annulled as condition for accession",c+"7","both","Baldwin III died on 10 February 1163",flag=DD,
  more=[ex(c+"8","description","Amalric agreed and ascended the throne without a wife")])]
fin(n,d)
# Mary Raine
n="Mary_Raine";d=load(n);c=pre(d)
d["events"]+=[ev("1900-11-20","location","","Arrived in Australia aboard Jumna",c+"4","both","In 1900 , at the age of 23 , Carter sailed with her sister Daisy to Moreton Bay in Queensland , Australia , on Jumna , arriving on 20 November"),
 ev("1918","family","","First husband William Thomas died after falling from a horse",c+"12","both","He died in 1918 after falling from a horse")]
fin(n,d)
# Fort Tilden
n="Fort_Tilden";d=load(n);c=pre(d)
flag(d,DD,"e10","e16")
d["events"]+=[ev("1951","other","armament","Additional four-gun 90 mm battery in the area (begins)",c+"15","both","An additional four-gun 90 mm battery was in the area 1951-54",flag=DD),
 ev("1954","other","armament","Additional four-gun 90 mm battery in the area (ends)",c+"15","both","An additional four-gun 90 mm battery was in the area 1951-54",flag=DD)]
fin(n,d)
# Slade Gorton
n="Slade_Gorton";d=load(n);c=pre(d)
get(d,"e13")["track"]="affiliation"
d["events"]+=[ev("2010","other","institute","National Bureau of Asian Research founded the Slade Gorton International Policy Center",c+"14","both","In 2010 , the National Bureau of Asian Research founded the Slade Gorton International Policy Center"),
 ev("2013","family","","Wife Sally died",c+"16","both","Sally died in 2013")]
fin(n,d)
# Ralph Lauren
n="Ralph_Lauren_Corporation";d=load(n);c=pre(d)
flag(d,SI,"e2");flag(d,DD,"e8");drop(d,"e48")
d["events"]+=[ev("2015-09","role","","Announced Stefan Larsson would replace Ralph Lauren as CEO",c+"10","both","In September 2015 , it was announced that Stefan Larsson would replace the companys founder"),
 ev("2019","work","","Second American Living line sold at Macys discontinued",c+"22","both","A second American Living line was sold at Macys ; this American Living line only included womens clothing and was discontinued in 2019")]
fin(n,d)
# Atlanta Dream
n="Atlanta_Dream";d=load(n);c=pre(d)
d["events"]+=[ev("2008-05-17","other","record","Lost 17 consecutive games, WNBA all-time record (streak ended July 5)",c+"11","both","From May 17 , 2008 , with a season opening loss against the Connecticut Sun to July 3 , 2008"),
 ev("2009-08","ownership_structure","","Owner Ron Terwilliger announced he wanted to give up primary ownership",c+"14","both","announced in August that he wanted to give up his position as the primary owner",flag=DD),
 ev("2021","location","","Team began playing at Gateway Center Arena in College Park",c+"25","both","for the 2020 season ( later delayed to the 2021 season )")]
fin(n,d)
# Hasselhoff
n="David_Hasselhoff";d=load(n);c=pre(d)
drop(d,"e5","e68","e103");flag(d,DD,"e26")
get(d,"e73")["evidence"]=[ex(c+"17","both","In 2007 , he again played himself in the Jamie Kennedy comedy Kickin It Old Skool")]
d["events"]+=[ev("1982","work","","Left The Young and the Restless as Dr. Snapper Foster",c+"7","both","from 1975 to 1982 , leaving the series"),
 ev("2006-11","work","","Mel Brooks announced Hasselhoff would play Roger DeBris in Las Vegas production of The Producers",c+"19","both","In November 2006 , Mel Brooks announced Hasselhoff would portray Roger DeBris"),
 ev("2010-12","work","","Played Captain Hook in New Wimbledon Theatre pantomime Peter Pan (Dec 2010-Jan 2011)",c+"27","both","playing Captain Hook in the New Wimbledon Theatre production of the pantomime Peter Pan from December 2010 to January 2011"),
 ev("2019-12-02","work","","Starred in 9 to 5: The Musical at Savoy Theatre, West End (to 8 Feb 2020)",c+"32","both","David Hasselhoff will star in 9 to 5 : The Musical at the Savoy Theatre in Londons West End from December 2 , 2019 , until February 8 , 2020")]
fin(n,d)
