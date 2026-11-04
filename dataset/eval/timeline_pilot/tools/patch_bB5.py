import json,sys,os
base="batchB5"
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
for n in ["Tyne_and_Wear_Passenger_Transport_Executive","Ferdinand_Sch_rner"]: fin(n,load(n))

# PEN America: date 2011 is stated in the source, flag was wrong
n="PEN_America";d=load(n);noflag(d,"e4");fin(n,d)

# NSW C38
n="New_South_Wales_C38_class_locomotive";d=load(n);c=pre(d)
d["events"]+=[ev("1970-08","work","","3801 hauled the Western Endeavour to Perth after the Sydney-Perth line was converted to standard gauge",c+"11","both","In August 1970 , 3801 hauled the Western Endeavour to Perth"),
 ev("1972","other","overhaul","Overhaul of 3813 by the NSW Rail Transport Museum was forced to stop on the commissioner's order",c+"13","both","after an overhaul in 1972 by the former NSW Rail Transport Museum was forced to be stopped"),
 ev("1974","other","film","3801 featured in the short film A Steam Train Passes",c+"12","both","featured in an evocative 1974 short film"),
 ev("1988-04","work","","3801 again operated to Perth during the Australian Bicentenary",c+"11","both","In April 1988 , 3801 again operated to Perth during the Australian Bicentenary")]
fin(n,d)

# Cambridge
n="George_Cambridge_2nd_Marquess_of_Cambridge";d=load(n);c=pre(d)
d["events"]+=[ev("1924-09-24","family","birth of daughter","Daughter Lady Mary Cambridge born",c+"7","both","The couple had one child , Lady Mary Cambridge ( 24 September 1924 – 13 December 1999 )")]
fin(n,d)

# Carisbrooke
n="Alexander_Mountbatten_1st_Marquess_of_Carisbrooke";d=load(n);c=pre(d)
drop(d,"e13","e19")
d["events"]+=[ev("1915-07-15","role","","Promoted to captain (seniority date)",c+"8","both","ranking as a Captain with seniority of 15 July 1915",flag=DD),
 ev("1920-01-13","family","birth of daughter","Daughter Lady Iris Mountbatten born",c+"15","both","Lady Iris Mountbatten ( 13 January 1920 – 1 September 1982 )")]
fin(n,d)

# Becquerel
n="Henri_Becquerel";d=load(n);c=pre(d)
d["events"]+=[ev("1896-02-27","work","","Described his phosphorescence experiments to the French Academy of Sciences",c+"11","both","Describing them to the French Academy of Sciences on 27 February 1896"),
 ev("1896-03-02","work","","Reported to the Academy that uranium salts kept in darkness still produced photographic images",c+"14","both","On 2 March 1896 he reported")]
fin(n,d)

# Whitney
n="William_Dwight_Whitney";d=load(n);c=pre(d)
drop(d,"e5")
K=[("1857-08-16","Son Edward Baldwin Whitney born","6","Edward Baldwin Whitney was born August 16 , 1857"),
 ("1859-04-02","Son Williston Clapp Whitney born","6","Williston Clapp Whitney was born April 2 , 1859"),
 ("1861-02-06","Daughter Marian Parker Whitney born","7","Marian Parker Whitney was born February 6 , 1861"),
 ("1861-03-11","Son Williston Clapp Whitney died","6","Williston Clapp Whitney was born April 2 , 1859 but died March 11 , 1861"),
 ("1863-01-06","Son Roger Sherman Baldwin Whitney born","8","Roger Sherman Baldwin Whitney was born January 6 , 1863"),
 ("1864-08-29","Daughter Emily Henrietta Whitney born","8","Emily Henrietta Whitney was born August 29 , 1864"),
 ("1866-11-19","Daughter Margaret Dwight Whitney born","8","Margaret Dwight Whitney was born November 19 , 1866"),
 ("1874-01-17","Son Roger Sherman Baldwin Whitney died","8","Roger Sherman Baldwin Whitney was born January 6 , 1863 , but died January 17 , 1874")]
for dt,t,ch,q in K: d["events"].append(ev(dt,"family","birth" if "born" in t else "death",t,c+ch,"both",q))
d["events"]+=[ev("1857","work","","Atharva Veda edition with Rudolf von Roth completed",c+"17","both","Atharva Veda , editor with Rudolf von Roth ( 1856–1857 )"),
 ev("1891","work","","First edition of The Century Dictionary completed",c+"15","both","which appeared from 1889 to 1891")]
fin(n,d)

# Beugro
n="Beugr";d=load(n);c=pre(d)
setev(d,"e4",[ex(c+"4","description","was uploaded on Videa ( a Hungarian video sharing website ) between March 13 and April 26"),ex(c+"4","date","it started as a weekly series on March 14 , 2008")])
setev(d,"e6",[ex(c+"4","description","was uploaded on Videa ( a Hungarian video sharing website ) between March 13 and April 26"),ex(c+"4","date","it started as a weekly series on March 14 , 2008")])
setev(d,"e8",[ex(c+"20","both","the second between August 25 and November 18 , 2008")])
setev(d,"e17",[ex(c+"7","description","Season 3 started with the New Years Eve performance at 10:40 pm on Friday , February 13"),ex(c+"7","date","March 21–22 , 2009")])
flag(d,DD,"e17")
d["events"]+=[ev("2009-12","work","","Board game sold out",c+"25","both","The game was sold out by December 2009",flag=AP),
 ev("2010-09-27","work","","Season 6 recording began",c+"20","both","the sixth between September 27 and November 23 , 2010")]
fin(n,d)

# Goryachkina
n="Aleksandra_Goryachkina";d=load(n);c=pre(d)
D12=ex(c+"12","date","Her biggest yearly ratings jump took place in 2011")
D23=ex(c+"23","date","Goryachkina returned to the 2500s in rating in the second half of 2018")
d["events"]+=[ev("2008","other","award","Won the Russian PriFR under-18 event",c+"12","both","winning the 2008 Russian PriFR under-18 event"),
 ev("2011","other","title","Clinched the Woman International Master (WIM) title at the Czech Open",c+"13","description","she clinched the Woman International Master ( WIM ) title and also earned a WGM norm",more=[D12],flag=DD),
 ev("2011","other","tournament","Competed in her first European Individual Women's Chess Championship",c+"12","description","She then competed in her first European Individual Womens Chess Championship and scored 5½/11",more=[D12],flag=DD),
 ev("2011","other","award","Won the Lyudmila Rudenko Memorial",c+"13","description","clear first at the Lyudmila Rudenko Memorial",more=[D12],flag=DD),
 ev("2012","other","award","Joint second at the Russian under-20 junior girls championship",c+"15","both","a victory over GM Davit Petrosian at the 2012 Aeroflot Open B , and a joint second-place finish at the Russian under-20 junior girls championship"),
 ev("2013","other","title","Earned an International Master (IM) norm at the European Individual Women's Championship",c+"17","both","one International Master ( IM ) norm in 2013 and 2014 at the European Individual Womens Chess Championship and the open European Individual Chess Championship respectively"),
 ev("2014","other","title","Earned an International Master (IM) norm at the open European Individual Championship",c+"17","both","one International Master ( IM ) norm in 2013 and 2014 at the European Individual Womens Chess Championship and the open European Individual Chess Championship respectively"),
 ev("2015","other","title","Earned her third and final IM norm at the European Individual Championship",c+"19","both","She earned her third and final IM norm at the 2015 European Individual Championship"),
 ev("2017","other","award","Won silver at the European Individual Women's Championship",c+"22","description","She won a silver medal at the tournament with a score of 8/11",more=[ex(c+"21","date","Goryachkina began improving her rating again in 2017")],flag=DD),
 ev("2018","other","tournament","Lost in the second round of the Women's World Chess Championship for the third consecutive edition",c+"24","description","she lost in the second round of the Womens World Chess Championship for the third consecutive edition",more=[D23],flag=DD),
 ev("2018-08","other","ranking","Entered the women's top 10 for the first time",c+"24","description","she also became ranked in the womens top 10 for the first time",more=[D23],flag=DD),
 ev("2019","other","award","Russia won silver at the World Team Championship",c+"38","both","At the 2019 World Team Championship , Russia won the silver medal behind China")]
fin(n,d)
