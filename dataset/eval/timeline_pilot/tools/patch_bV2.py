import json,sys,os
base="batchV2"
os.makedirs(f"{base}/rev",exist_ok=True)
def load(n): return json.load(open(f"{base}/sub/{n}.json"))
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=more
    if flag:e["flag"]=flag
    return e
def fin(n,d):
    for e in d["events"]:
        if len(e["date"].split("-")[0])==3: e["date"]="0"+e["date"]
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

def add(n,d,items):
    c=pre(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]; fl=it[7] if len(it)>7 else None; more=it[8] if len(it)>8 else None
        if more: more=[ex(c+m[0],m[1],m[2]) for m in more]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,fl,more))

def setev(d,i,l): get(d,i)["evidence"]=l


# no change
for n in ["Stefano_Pioli","Vologda_Governorate","Zerelda_James"]: fin(n,load(n))

n="The_Clitheroe_Kid";d=load(n);c=pre(d)
setev(d,"e3",[ex(c+"0","both","originally broadcast between April 1957")])
fin(n,d)

n="Sydney_Trains_K_set";d=load(n);c=pre(d)
setev(d,"e9",[ex(c+"2","both","This was replaced with sheet glass in 1993 .")])
add(n,d,[("1988","work",None,"Four-carriage sets no longer ran together as one eight-car set in practice (until 1988)","2","both","often ran together as one eight-car set until 1988")])
fin(n,d)

n="Numedal_Line";d=load(n)
drop(d,"e16")
txt(d,"e18","Derailment on the line (April 2014); the entire stretch was afterwards upgraded with new sleepers");noflag(d,"e18")
fin(n,d)

n="James_Lanier";d=load(n)
add(n,d,[
("1885","family",None,"Daughter Louisa Morris Lanier died","11","both","Louisa Morris Lanier ( 1835–1885 )"),
("1895","family",None,"Son Alexander Chalmers Lanier died","9","both","Alexander Chalmers Lanier ( 1820–1895 )"),
("1903","family",None,"Daughter Drucilla Ann Lanier died","9","both","Drucilla Ann Lanier ( 1824–1903 )"),
("1910","family",None,"Daughter Elizabeth Frances Lanier died","9","both","Elizabeth Frances Lanier ( 1822–1910 )"),
("1926","family",None,"Son Charles D. Lanier died","11","both","Charles D . Lanier ( 1837–1926 )")])
fin(n,d)

n="Dixie_State_University";d=load(n)
undrop(d,"Men's soccer won","Stadium renamed Greater Zion")
add(n,d,[
("2014-12","other","dismissal","Theater professor Varlo Davenport received notice of dismissal and termination of employment","17","both","In December 2014 , theater professor Varlo Davenport received a notice of dismissal and termination of employment"),
("2016","other","championship","Men's soccer won the PacWest 2016 championship, first in school history","33","both","Dixies Mens soccer team , won the PacWest 2016 championship by going 13–0 , for the first time in school history"),
("2019-08","other","fraternity","Students created a nationally recognized chapter of Kappa Sigma Fraternity","27","both","In August 2019 , students of DSU created a nationally recognized chapter of the Kappa Sigma Fraternity"),
("2020-01","naming",None,"Stadium named Greater Zion Stadium under naming-rights agreement with Washington County tourism office","36","both","As of January 2020 , the Dixie State stadium is now known as Greater Zion Stadium")])
fin(n,d)

n="European_Central_Bank";d=load(n)
add(n,d,[("2019-07","role",None,"EU leaders nominated Christine Lagarde to replace Mario Draghi as ECB President","40","both","In July 2019 , EU leaders nominated Christine Lagarde to replace Mario Draghi as ECB President")])
fin(n,d)

n="B_o_B";d=load(n);c=pre(d)
drop(d,"e11","e20")
setev(d,"e35",[ex(c+"21","date","The album , released April 27 , 2010 , was given generally positive reviews"),ex(c+"21","description","In July , B.o.B announced he will")])
setev(d,"e36",[ex(c+"25","both","on September 12 , 2010")])
setev(d,"e40",[ex(c+"27","date","In early 2011 , Odd Futures Tyler , the Creator released a song titled Yonkers"),ex(c+"28","description","25 , B.o.B released No Future a song in which he takes aim at the hip hop collective and their leader")]);flag(d,DD,"e40")
setev(d,"e44",[ex(c+"32","date","On September 23 , 2011 , B.o.B released a trailer"),ex(c+"32","description","causing the single to be released on iTunes on September 27")]);flag(d,DD,"e44")
setev(d,"e48",[ex(c+"37","date","On February 14 , 2012 , B.o.B released a trailer for the second official single"),ex(c+"37","description","was released on February 21")]);flag(d,DD,"e48")
setev(d,"e55",[ex(c+"48","date","On May 12 , 2013 B.o.B tweeted"),ex(c+"48","description","In May , B.o.B also premiered a music video for a newly released song of his titled Through My Head")]);flag(d,DD,"e55")
setev(d,"e57",[ex(c+"49","both","The song would be released to retail on May 21 , 2013")])
setev(d,"e78",[ex(c+"60","description","a follow-up , Southmatic , was released the following year"),ex(c+"70","date","Southmatic ( 2019 )")])
add(n,d,[
("2009","other","chart milestone","Nothin on You reached number one in the US and the UK","2","both","reached number one in both the United States and the United Kingdom in 2009"),
("2010-08-14","work",None,"Announced as main support for Paramore's November UK tour","24","both","On August 14 , 2010 , Hayley Williams announced via the Official Paramore Fan Club that B.o.B would be the main support for Paramores November UK Tour"),
("2011-03-22","work",None,"Song New York New York featured in the Crysis 2 launch trailer","26","both","On March 22 , 2011 , Electronic Arts released the Launch Trailer for the upcoming first-person-shooter Crysis 2 which featured a song by B.o.B titled New York New York"),
("2014-10-07","affiliation",None,"Singer Tora Woloshin announced she signed to his label No Genre","54","both","On October 7 , 2014 , an up-and-coming singer named Tora Woloshin , announced she signed to No Genre"),
("2016-08-02","other","certification","Debut album certified 2x platinum by the RIAA","25","both","B.o.B Presents : The Adventures of Bobby Ray was certified 2x platinum by the RIAA on August 2 , 2016")])
fin(n,d)
