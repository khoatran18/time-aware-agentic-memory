import json,sys,os
base="batchB10"
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

n="Andrew_Mellon_Building";d=load(n)
add(n,d,[
("1922","other","residence","Andrew W. Mellon occupies the top floor of the building as his residence","4","both","occupying the top floor from 1922 until his death in 1937"),
("1937","other","residence","Andrew W. Mellon's occupancy of the top floor ends with his death","4","both","occupying the top floor from 1922 until his death in 1937"),
("2010","ownership_structure",None,"National Trust board pulls the building off the market after Moe stepped down","7","description","the organizations board of directors decided to pull the building off the market so that Meeks",DD,[("7","date","stepped down in early 2010")]),
]);fin(n,d)

n="Eastern_Army_Division";d=load(n)
add(n,d,[("2000","other","medal","Commemorative medal of the Eastern Army Division established","10","both","In 2000 , the Östra arméfördelningens ( 4.förd ) minnesmedalj")]);fin(n,d)

n="Karls_y";d=load(n)
add(n,d,[("1909","naming",None,"Spelling of the name changed from Karlsø to Karlsøy (by 1909)","6","both","Prior to 1909 , the name was spelled Karlsø",DD)])
undrop(d,"Karlsø");fin(n,d)

n="Keith_Emerson";d=load(n);c=pre(d)
setev(d,"e39",[ex(c+"58","both","In 2002 Emerson reformed and toured with the Nice")])
add(n,d,[
("1973","work",None,"ELP album Brain Salad Surgery released","1","both","Brain Salad Surgery ( 1973 )"),
("1992","work",None,"ELP album Black Moon released","56","both","Black Moon ( 1992 )"),
("1994","work",None,"ELP album In the Hot Seat released","56","both","In the Hot Seat ( 1994 )"),
("1993","other","surgery","Underwent nerve-graft surgery on his arm","68","both","nearly career-ending nerve-graft surgery in 1993"),
("2010-09","other","health","Announced urgent surgery after colonoscopy found a polyp; autumn touring postponed","73","both","In September 2010 , Emerson released a message stating"),
]);fin(n,d)

n="Lowell_State_College";d=load(n)
add(n,d,[("1914","other","first African American graduates","Teresa Garland Lew and Marion Scott Lew, first African Americans to graduate from the Normal School (Class of 1914)","11","both","Teresa Garland Lew and Marion Scott Lew were notable graduates of the Lowell Normal School ( Class of 1914 )")]);fin(n,d)

n="Sarah_Palfrey_Cooke";d=load(n)
add(n,d,[
("1942-12","family",None,"Daughter born to her and Elwood Cooke","11","both","and their daughter was born in December 1942"),
("1952-12","family",None,"Son born to her and Jerome Danzig","12","both","son was born in December 1952"),
]);fin(n,d)

n="Senate_of_Canada_Building";d=load(n)
add(n,d,[("2011-01-29","other","exhibition","Berlin Wall section removed from display inside the main entrance","19","both","until January 29 , 2011")]);fin(n,d)

n="Sevilla_FC_Puerto_Rico";d=load(n);fin(n,d)

n="Swedish_Air_Force_Flying_School";d=load(n)
add(n,d,[
("1658","other","military use","Moor at Ljungby adopted for military use by the Scanian Hussar Regiment as a training ground","1","both","The moor at Ljungby was adopted for military use in 1658 by the Scanian Hussar Regiment as a training ground"),
("1910","other","first flights","First flights commenced from the grounds","1","both","In 1910 , the first flights were commenced from the grounds"),
("1983","other","meteorology school","Air Force school of meteorology begins to be located at Ljungbyhed","1","both","Between 1983 and 1996 the Air Force school of meteorology was also located at Ljungbyhed"),
("1996","other","meteorology school","Air Force school of meteorology ceases to be located at Ljungbyhed","1","both","Between 1983 and 1996 the Air Force school of meteorology was also located at Ljungbyhed"),
]);fin(n,d)

n="Werner_Hartmann";d=load(n)
drop(d,"e16");flag(d,AP,"e15")
txt(d,"e15","Commanded boat patrolling Spanish waters during the Civil War, 1937-38 (boat name missing)")
txt(d,"e29","Received U-boat War Badge with Diamonds")
add(n,d,[("1939-08-19","work","first patrol","Began first patrol on U-37 from Wilhelmshaven","8","both","Hartmanns first patrol ( 19 August 1939")]);fin(n,d)
