import json,sys,os
base="batchV1"
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
for n in ["Knox_Cunningham","USCGC_Southwind","Liga_Veneta_Repubblica"]: fin(n,load(n))

n="Lykkehjulet";d=load(n)
add(n,d,[
("1989","other","format change","Top wheel value in round 2 raised to 2,500 kroner","4","both","value amounts originally ranged from 100 to 1,500 kroner ( 2,500 starting in round 2 in 1989 )"),
("1990","other","format change","Top value becomes 3,000 kr in round 1 and 5,000 kr from round 2 onwards","5","both","Beginning in 1990 , the top value was 3,000 kr . in Round 1 then 5,000 kr . from Round 2 onwards"),
("1999","other","format change","Top value becomes 5,000 kr in every round","5","both","By 1999 , the top value was 5,000 kr . in every round"),
("2001","other","format change","Top values changed to 2,500 points in round one, 7,500 in rounds two and three, 10,000 in round four","5","both","In 2001 , the top values were 2,500 points in round one , 7,500 in rounds two and three and 10,000 between two garbage cans in round four")])
fin(n,d)

n="James_Marape";d=load(n)
add(n,d,[
("2020-11-17","other","budget","Parliament passed the 2021 budget while the opposition was absent in Vanimo","14","description","on 17 of November -with the opposition absent in Vanimo- the budget for 2021 was passed",DD,[("12","date","On 10th of November 2020 Marape was confronted by an attempt to topple him from power")])])
fin(n,d)

n="Valladolid";d=load(n)
add(n,d,[
("1084","other","foundation","Project for the foundation of the city already underway (by 1084)","14","both","By 1084 the project for the foundation of the city was already underway",AP),
("1092","naming",None,"Name documented in the variant Valleolide","5","both","Valleolide ( 1092 )"),
("1095","naming",None,"Name documented in the variants Valleolit, Valleoleti and Valleoliti","5","both","Valleoliti ( 1095 )"),
("1241","other","university","University of Valladolid founded by Alfonso VIII","27","both","The University of Valladolid ( UVA ) was founded in 1241 by Alfonso VIII of Castille"),
("1469","other","royal wedding","Queen Isabella I of Castile and King Ferdinand of Aragon married in the city","16","both","In 1469 , Queen Isabella I of Castile and King Ferdinand of Aragon were married in the city"),
("1506","other","death in city","Christopher Columbus died in Valladolid","16","both","In 1506 , Christopher Columbus died in Valladolid"),
("1554","other","regency seat","Joanna of Austria established herself in Valladolid as regent (1554 to 1559)","17","both","From 1554 to 1559 , Joanna of Austria , sister of Philip II , served as regent , establishing herself in Valladolid"),
("1668","work",None,"Main body of the unfinished cathedral opened","34","both","its main body was not opened until 1668"),
("1730","work",None,"Main front of the cathedral finished","34","both","Decades later , in 1730 , finished the work on the main front"),
("1861","work",None,"Teatro Lope de Vega built in classical style","35","both","The Teatro Lope de Vega is a theater built in the classical style in 1861"),
("1890-09-29","work",None,"Bullring Plaza de toros de Valladolid opened","63","both","The Plaza de toros de Valladolid , a bullring , opened on 29 September 1890"),
("1950","other","company founded","ENDASA founded","23","both","companies such as ENDASA ( 1950 )"),
("1953","other","company founded","FASA-Renault founded to assemble Renault-branded vehicles","40","both","since the founding of FASA-Renault in 1953",SI),
("1954","other","company founded","FASA founded","23","both","FASA ( 1954 )",SI),
("1956","other","company founded","TECNAUTO founded","23","both","TECNAUTO ( 1956 )"),
("1957","other","company founded","SAVA founded, producing commercial vehicles","40","both","in 1957 , Sava was founded and started producing commercial vehicles"),
("1982","work",None,"Estadio Nuevo José Zorrilla built as a venue for the 1982 FIFA World Cup","60","both","was built as a venue for the 1982 FIFA World Cup"),
("1990","ownership_structure",None,"Sava, previously absorbed by Pegaso, taken over by Iveco","40","both","since 1990 by the Italian truck manufacturer Iveco"),
("2007-12-22","work",None,"Madrid–Valladolid high-speed rail line inaugurated","45","both","The Madrid–Valladolid high-speed rail line was inaugurated on 22 December 2007")])
fin(n,d)

n="Alex_McLeish";d=load(n)
setev(d,"e5",[ex(d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#9","both","in a 4–1 victory over Rangers in the 1982 Scottish Cup Final")])
c=pre(d)
setev(d,"e47",[ex(c+"45","both","In August 2014 , he was appointed manager of Belgian club Genk")])
add(n,d,[
("1998","other","relegation","Hibernian relegated from the Scottish Premier Division under McLeish","16","both","which was relegated from the Scottish Premier Division in 1998"),
("2007-03-24","other","first match","First game in charge of Scotland, 2-1 win over Georgia at Hampden Park","29","both","first game in charge of the national team was a UEFA Euro 2008 qualifying match , a 2–1 victory against Georgia on 24 March 2007")])
fin(n,d)

n="Dennis_Quaid";d=load(n)
txt(d,"e36","Hospital mistakenly gave his ten-day-old twins a heparin dose 1,000 times the common dosage; Quaid later sued the manufacturer")
fin(n,d)

n="Jon_Gruden";d=load(n)
add(n,d,[
("2008-11-30","other","milestone","Earned 100th career victory, against the New Orleans Saints","28","description","On November 30 , Gruden earned his 100th career victory , which came against the New Orleans Saints",DD,[("28","date","In 2008 , Gruden was rewarded with a contract extension through the 2011 season")])])
fin(n,d)

n="Scottish_National_Party";d=load(n);c=pre(d)
setev(d,"e41",[ex(c+"10","date","1974 was to prove something of an annus mirabilis for the party"),ex(c+"10","description","The SNP gained 6 seats at the February general election")]);flag(d,DD,"e41")
add(n,d,[
("1983","other","election","Electoral disappointment at the 1983 general election","15","both","through the electoral disappointments of 1983 and 1987"),
("2003","other","leadership challenge","Unsuccessful leadership challenge against John Swinney","25","both","After an unsuccessful leadership challenge in 2003"),
("2004","role",None,"Nicola Sturgeon elected Depute Leader","25","description","Nicola Sturgeon was elected Depute Leader",DD,[("25","date","following disappointing results in the European elections of 2004")])])
fin(n,d)
