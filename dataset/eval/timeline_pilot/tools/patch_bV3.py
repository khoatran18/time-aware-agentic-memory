import json,sys,os
base="batchV3"
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

# no change
for n in ["Evandro_Brand_o","Gordon_W_McKay","Newton_D_Baker_House"]: fin(n,load(n))

n="Amber_Diceless_Roleplaying_Game";d=load(n)
add(n,d,[
("2010-05","other","license","Rite Publishing secured a license from Diceless by Design to use the rules system for a new product","12","both","In May 2010 , Rite Publishing secured a license from Diceless by Design to use the rules system"),
("2013-11","work",None,"Lords of Gossamer and Shadow (Diceless), built on the game's rules, released publicly in print and PDF","12","both","Nov 2013 Lords of Gossamer and Shadow ( Diceless ) was released publicly")])
fin(n,d)

n="EMD_SDP40F";d=load(n);c=pre(d)
drop(d,"e5")
setev(d,"e3",[ex(c+"10","both","The locomotives entered revenue service on June 22 , 1973")])
fin(n,d)

n="Tibbers_Castle";d=load(n);c=pre(d)
txt(d,"e12","Site surveyed")
quote(d,"e12","surveyed in 1912")
add(n,d,[("1451","other","toun","A toun or township at Tibbers was mentioned","8","both","A toun or township at Tibbers was mentioned in 1451")])
fin(n,d)

n="John_Campbell_Brown";d=load(n);c=pre(d)
setev(d,"e9",[ex(c+"5","both","astronomy research assistant in 1968–70 and lecturer from 1970")])
undrop(d,"OBE")
add(n,d,[("2016","other","honour","Appointed Officer of the Order of the British Empire (OBE) in the Birthday Honours","10","both","Officer of the Order of the British Empire ( OBE ) in the 2016 Birthday Honours")])
fin(n,d)

n="Lee_Nogan";d=load(n)
add(n,d,[("1995","other","play-off final","Played in Reading's defeat in the 1995 First Division play-off final at Wembley","1","both","played in the clubs defeat in the 1995 First Division play-off final at Wembley")])
fin(n,d)

n="Carles_Puigdemont";d=load(n);c=pre(d)
add(n,d,[("2018-03-23","other","arrest_warrant","European arrest warrant reissued against him","33","date","On 25 March 2018 , while returning to Brussels from a trip to Finland",DD,[("33","description","the European warrant that had been reissued against him two days previously")])])
fin(n,d)

n="Nik_Stauskas";d=load(n);c=pre(d)
drop(d,"e19","e21","e52")
setev(d,"e38",[ex(c+"48","date","the Big Ten Network , Stauskas declared for the 2014 NBA draft"),ex(c+"47","description","On April 15 , in a joint press conference with Robinson on")])
setev(d,"e60",[ex(c+"66","date","On February 4 , 2019 , Stauskas was traded to the Cleveland Cavaliers"),ex(c+"66","description","He was waived by the Pacers on February 8")])
flag(d,DD,"e38","e60")
fin(n,d)
