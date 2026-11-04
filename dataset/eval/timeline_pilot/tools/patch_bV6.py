import json,sys,os
base="batchV6"
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
for n in ["Escadron_de_Chasse_1_2_Cigognes","LB_amp_SCR_E4_class","La_Japonaise_painting","Saadat_Hasan_Manto","Fergie_singer","Wilhelm_K_lz"]: fin(n,load(n))

n="SV_Darmstadt_98";d=load(n)
quote(d,"e8","from the time of the formation of the Bundesliga in 1963")
txt(d,"e8","Second-division run resumed with formation of the Bundesliga")
fin(n,d)

n="Chemnitz";d=load(n)
drop(d,"e47")  # concert = event of another entity
fin(n,d)

n="Gleaston_Castle";d=load(n);c=pre(d)
drop(d,"e9","e10","e11","e12")  # artists' depictions = events of the works
setev(d,"e3",[ex(c+"1","both","until 1458 when it passed to William Bonville through marriage"),ex(c+"6","both","The Harington family owned Gleaston Castle until William Harington , 5th Baron Harington died in 1458")])
quote(d,"e8","In 1671 Thomas Preston , 3rd Baronet Preston bought Aldingham manor")
fin(n,d)

n="Sergio_P_rez";d=load(n);c=pre(d)
get(d,"e25")["evidence"][0]["quote"]="was moved up to 10th to get his first point for Force India"
add(n,d,[("1997","other","karting",   "Raced in karting Youth Class as youngest driver; one win, five podiums, fourth in championship","7","both","In 1997 , he participated in the karting Youth Class , where he was the youngest driver in the category"),
("2000","other","karting","Raced in the Shifter 80 cc Championship and three Shifter 125 cc races","10","both","In 2000 , he raced in the Shifter 80 cc Championship"),
("2002","other","karting","National runner-up in the Shifter 125 cc category with six wins","11","both","With six wins in 2002 , Pérez finished as the national runner-up in the Shifter 125 cc category"),
("2012-09-28","affiliation",None,"Confirmed as Lewis Hamilton's replacement at McLaren for 2013","38","date","On 28 September 2012 , Lewis Hamiltons decision to leave McLaren for Mercedes in 2013 was announced",None,[("38","description","Pérez was subsequently confirmed as Hamiltons replacement")])])
fin(n,d)


