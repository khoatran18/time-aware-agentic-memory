import json,sys,os
base="batchB8"
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

def add(n,d,items):
    c=pre(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]; fl=it[7] if len(it)>7 else None; more=it[8] if len(it)>8 else None
        if more: more=[ex(c+m[0],m[1],m[2]) for m in more]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,fl,more))

# no change
fin("Lenin_Peak",load("Lenin_Peak"))
d=load("Josep_Rull");c=pre(d)
setev(d,"e20",[ex(c+"1","both","Between 2 November and 4 December 2017 , he was jailed"),ex(c+"10","description","On 4 December he and some other members of the Government were released on bail")])
fin("Josep_Rull",d)

n="Marc_Bohan";d=load(n)
add(n,d,[
("1962","family",None,"First wife Dominique Gaborit died","7","both","Bohans first wife , Dominique Gaborit , whom he married in 1950 , died in 1962"),
("1967","work",None,"Princess Grace supported Bohan by opening the Baby Dior boutique","5","both","Princess Grace supported Bohan by opening the Baby Dior boutique in 1967")])
fin(n,d)

n="Carrier_Air_Group_Seventeen";d=load(n)
add(n,d,[
("1945-02-07","other","deployment","CVG-82 aboard Bennington reached the U.S. 5th Fleet","3","both","Bennington reached the U.S . 5th Fleet on 7 February 1945"),
("1945-02-16","other","combat operation","CVG-82 attacked targets in the Tokyo area, nine days after reaching 5th Fleet","4","description","CVG-82 attacked targets in the Tokyo area , mainly the airfields at Nachijo Jima , Nanpo Shoto , Mikatagahara , and Hamamatsu",DD,[("3","date","Bennington reached the U.S . 5th Fleet on 7 February 1945"),("3","description","Nine days later .")])])
fin(n,d)

n="Diane_Downs";d=load(n)
add(n,d,[
("1974","family",None,"Daughter Christie Ann born","3","both","Their first child , Christie Ann , was born in 1974"),
("1976","family",None,"Daughter Cheryl Lynn born","3","both","Cheryl Lynn followed in 1976"),
("1979","family",None,"Son Stephen Daniel (Danny) born","3","both","with Stephen Daniel being born in 1979"),
("1982-05-08","family",None,"Gave birth to a daughter through surrogacy and gave the child to her intended parents","4","both","On May 8 , 1982 , Downs gave birth to a daughter through surrogacy"),
("1984","family",None,"Gave birth to Amy Elizabeth about a month after her trial; the child was later seized and adopted","14","both","gave birth to a girl , whom she named Amy Elizabeth , a month after her 1984 trial",AP),
("1986","family",None,"Fred Hugi and his wife adopted her two surviving children","13","both","He and his wife Joanne adopted them in 1986"),
("1987","other","book","Ann Rule published the book Small Sacrifices about Downs","19","both","Author Ann Rule wrote the book Small Sacrifices ( 1987 ) detailing Downs life and murder trial"),
("1989","other","TV movie","Made-for-TV movie Small Sacrifices aired on ABC","19","both","aired on ABC in 1989")])
fin(n,d)

n="Simferopol";d=load(n)
drop(d,"e9")
add(n,d,[("1991-02-12","role",None,"Became capital of the Crimean Autonomous Soviet Socialist Republic after Crimean Oblast was upgraded","12","description","Simferopol became the capital of the Crimean Autonomous Soviet Socialist Republic .",DD,[("11","date","the Crimean Oblast was upgraded an Autonomous Soviet Socialist Republic on 12 February 1991")])])
fin(n,d)

n="Carlos_Sainz_Jr";d=load(n)
add(n,d,[
("2013","other","podium","First GP3 podium at Valencia, third place","15","description","scoring a podium for the first time in GP3",DD,[("10","date","In 2013 , Sainz signed with Arden to compete in the GP3 series")]),
("2014","other","title","Won the Formula Renault 3.5 championship with DAMS","0","both","He raced for DAMS in the 2014 Formula Renault 3.5 season , winning the championship"),
("2020","other","fastest lap","First fastest lap in Formula One at the Styrian Grand Prix","39","description","finished with his first fastest lap in Formula One",DD,[("39","date","2020 season Sainz began the season with a fifth place")])])
fin(n,d)

n="John_Franklin";d=load(n)
add(n,d,[
("1824","family",None,"Daughter Eleanor Isabella born","9","description","Their daughter , Eleanor Isabella , was born the following year",DD,[("9","date","In 1823 , after returning to England , Franklin married the poet Eleanor Anne Porden")]),
("1825","family",None,"First wife Eleanor Anne Porden died of tuberculosis","9","both","His wife died of tuberculosis in 1825"),
("1846-09","other","ships icebound","Erebus and Terror trapped in ice off King William Island","28","both","Terror and Erebus became trapped in ice off King William Island in September 1846"),
("1849","family",None,"Daughter Eleanor Isabella married Reverend John Philip Gell","9","both","Eleanor Isabella married Reverend John Philip Gell in 1849"),
("1850","other","search","Several search expeditions converged off Beechey Island and found first relics of the expedition","31","both","In the summer of 1850 , several expeditions , including three from England as well as one from the United States , joined in the search"),
("1852-10","role",None,"Promoted to Rear-Admiral of the Blue (unintentional posthumous promotion)","31","both","he was promoted to Rear-Admiral of the Blue in October 1852"),
("1854","other","discovery","John Rae learned the true fate of the Franklin party from Inuit hunters","32","both","In 1854 , the Scottish explorer John Rae , while surveying the Boothia Peninsula for the Hudsons Bay Company , discovered the true fate of the Franklin party"),
("1860","family",None,"Daughter Eleanor Isabella died","9","both","She died in 1860"),
("1996","other","heritage designation","Wintering site of Franklin's second Canadian expedition designated a National Historic Site of Canada","38","both","The wintering site of Franklins second Canadian expedition , in Deline , Northwest Territories , was designated a National Historic Site of Canada in 1996"),
("2009","other","memorial","Special service of Thanksgiving and rededication of the national monument to Sir John Franklin","40","both","In 2009 , a special service of Thanksgiving was held in the chapel at the Royal Naval College to accompany the rededication of the national monument to Sir John Franklin"),
("2014-09","other","discovery","Wreck of Erebus rediscovered in Wilmot and Crampton Bay","41","both","In September 2014 , the wreck of was rediscovered in Wilmot and Crampton Bay near the Adelaide Peninsula"),
("2016-09","other","discovery","Wreck of Terror discovered in Terror Bay, King William Island","41","both","in September 2016 the wreck of was discovered , in Terror Bay on the south coast of King William Island")])
fin(n,d)

n="Zambia";d=load(n)
add(n,d,[
("1897-12","other","rebellion","Ngoni rebelled under Tsinco, son of King Mpezeni; rebellion put down","54","both","in December 1897 a group of the Angoni or Ngoni ( originally from Zululand ) rebelled under Tsinco"),
("1978-09-03","other","attack","Rhodesia's Operation Gatling raided Nkomo's guerilla bases in Zambia (Green Leader Raid)","62","description","Rhodesia responded with Operation Gatling , an attack on Nkomos guerilla bases in Zambia",DD,[("62","date","On 3 September 1978 , civilian airliner , Air Rhodesia Flight 825 , was shot down near Kariba")]),
("2010","other","recognition","World Bank named Zambia one of the world's fastest economically reformed countries","5","both","In 2010 , the World Bank named Zambia one of the worlds fastest economically reformed countries")])
fin(n,d)

n="The_Mercury_News";d=load(n)
c=pre(d)
setev(d,"e57",[ex(c+"39","both","From February 1967 to September 2014 , the papers were headquartered in a campus in suburban North San Jose"),ex(c+"36","description","a downtown office building that September")])
add(n,d,[
("1881","work",None,"Owen proposed lighting San Jose with a moonlight tower; the tower was dedicated that year","12","both","In 1881 , Owen proposed to light San Jose with a moonlight tower"),
("2005-10-21","work",None,"Announced closure and sale of Viet Mercury","30","description","On October 21 , it also announced the closure of and sale of Viet Mercury to a group of Vietnamese-American businessmen",DD,[("30","date","In June 2005 , the Mercury News closed its Hanoi bureau")]),
("2006-04-26","ownership_structure",None,"MediaNews Group announced planned purchase of the Mercury News","31","description","On April 26 , Denver-based MediaNews Group ( now Digital First Media ) announced a planned $ purchase of the Mercury News",DD,[("31","date","On March 13 , 2006 , The McClatchy Company purchased Knight Ridder for $")]),
("2006-06-12","ownership_structure",None,"Federal regulators asked for more time to review the MediaNews purchase on antitrust concerns","31","both","However , on June 12 , 2006 , federal regulators from the"),
("2006-07","other","lawsuit","Antitrust lawsuit filed seeking to undo MediaNews purchase of the Mercury News","33","both","a lawsuit claiming antitrust violations by MediaNews and the Hearst Corporation had also been filed in July 2006"),
("2013-04","ownership_structure",None,"MediaNews announced it would sell the Mercury News campus on Ridder Park Drive","35","both","In April 2013 , MediaNews announced that it would sell the Mercury News campus on Ridder Park Drive in North San Jose")])
fin(n,d)
