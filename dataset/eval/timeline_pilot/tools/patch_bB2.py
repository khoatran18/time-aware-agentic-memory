import json,sys,os
base="batchB2"
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
for n in ["Real_Madrid_Baloncesto","Department_of_Computing_Imperial_College_London","Luftflotte_1"]: fin(n,load(n))

# Charles Lee
n="Charles_Lee_general";d=load(n);c=pre(d)
d["events"]+=[ev("1763","role","","Regiment disbanded; retired on half pay as a major after return to England",c+"11","both","His regiment was disbanded and he was retired on half pay as a major",flag=DD)]
undrop(d,"retired on half pay")
fin(n,d)

# Desmond Costello
n="Desmond_Patrick_Costello";d=load(n);c=pre(d)
get(d,"e28")["evidence"]=[ex(c+"17","both","where he remained until his sudden death in 1964"),ex(c+"0","date","31 January 1912 – 23 February 1964")]
d["events"]+=[ev("1961","other","questioning","Questioned about the Kroger passports after the 1961 spy arrests; denied knowledge",c+"19","both","When questioned after the arrests , he denied any knowledge of the Krogers",more=[ex(c+"18","date","In 1961 several people were arrested in London and charged with spying")],flag=DD)]
undrop(d,"Questioned about the Kroger")
fin(n,d)

# Humongous
n="Humongous_Entertainment";d=load(n);c=pre(d)
drop(d,"e15","e18","e28","e29","e34","e35","e45","e47","e48","e50","e55","e56")
txt(d,"e58","Sold to parent and majority stockholder Infogrames")
d["events"]+=[ev("1995","other","division","Cavedog Entertainment established as company division in Seattle",c+"5","both","In 1995 , Gilbert and Day established a company division , Cavedog Entertainment , in Seattle"),
 ev("1997","work","","Cavedog released Total Annihilation",c+"5","both","and released Total Annihilation , a real-time strategy ( RTS ) game , in 1997"),
 ev("1998","work","","Cavedog released two Total Annihilation expansion packs",c+"5","both","This was followed by two expansion packs in 1998"),
 ev("1999-11","ownership_structure","","Parent GT Interactive acquired by Infogrames and renamed Infogrames, Inc.",c+"6","both","In November 1999 , GT Interactive was acquired by Infogrames and renamed it Infogrames , Inc ."),
 ev("2001","affiliation","","Co-founders and many key employees left Humongous and formed Hulabee Entertainment",c+"7","both","The founders soon left Humongous , alongside many other key employees , and formed a new studio , Hulabee Entertainment , in 2001"),
 ev("2003-05","ownership_structure","","Parent Infogrames, Inc. bought Hasbro Interactive and was renamed Atari, Inc.",c+"7","date","In May 2003 , after Infogrames , Inc",more=[ex(c+"8","description","purchased Hasbro Interactive—which owned the rights to the Atari brand—the company was renamed Atari , Inc")]),
 ev("2013","ownership_structure","bankruptcy","Atari SA filed bankruptcy for Humongous, Inc. and other US subsidiaries",c+"10","both","filed bankruptcy for three of its American subsidiaries , Atari , Inc. , Atari Interactive and Humongous , Inc . in 2013"),
 ev("2013","ownership_structure","","Backyard Sports series acquired by The Evergreen Group in the bankruptcy resolution",c+"10","both","the Backyard Sports series was acquired by The Evergreen Group",flag=DD),
 ev("2013","ownership_structure","","MoonBase Commander acquired by Rebellion Developments in the bankruptcy resolution",c+"10","both","MoonBase Commander by Rebellion Developments",flag=DD)]
undrop(d,"Backyard Sports series acquired","MoonBase Commander acquired","Founders and many key employees left")
d["undated_mentions"].append("Twelve game releases whose titles are missing from the source list (Freddi Fish 1996/1998/1999/2001, Pajama Sam 1996/1998/2000/2003, Spy Fox 1999/2001, Putt-Putt 2003, Blue's Clues 2000) not recorded as events")
fin(n,d)

# Air Component Command
n="Air_Component_Command";d=load(n);c=pre(d)
drop(d,"e44","e45","e54")
d["events"]+=[ev("1994-07-01","other","founding","Air Force Tactical Center formed in Linköping",c+"1","date","on 1 July 1994 , the Air Force Command",more=[ex(c+"1","description","the Air Tactical Center ( Flygvapnets taktiska centrum ) in Linköping")])]
fin(n,d)

# Frans Hals Museum
n="Frans_Hals_Museum";d=load(n)
drop(d,"e2")
d["undated_mentions"].append("1752: Dutch Society of Science founded (context, not a museum event)")
fin(n,d)

# Georges Duby
n="Georges_Duby";d=load(n);c=pre(d)
d["events"]+=[ev("1978","work","","The Chivalrous Society published (English translation of portions of La Société)",c+"21","both","portions translated in The Chivalrous Society ( 1978 ; repr . 1981 )"),
 ev("1984","work","","William Marshal: The Flower of Chivalry published (English translation of Guillaume le Maréchal)",c+"24","both","tr . as William Marshal : The Flower of Chivalry ( 1984 )"),
 ev("1990","work","","The Legend of Bouvines published (English translation of Le Dimanche de Bouvines)",c+"22","both","Translated in English as The Legend of Bouvines ( 1990 )"),
 ev("1994","work","","History Continues published (English translation of L'histoire continue)",c+"15","both","( History Continues ) ( 1991 ; Engl . trans . 1994 )")]
fin(n,d)

# London Fire Brigade
n="London_Fire_Brigade";d=load(n);c=pre(d)
get(d,"e33")["evidence"]=[ex(c+"9","both","With the formation of Greater London in 1965 , this absorbed most of the Middlesex Fire Brigade"),ex(c+"19","both","On the creation of the Greater London Council in 1965 , the brigade was enlarged"),ex(c+"88","both","The creation of the Greater London Council in 1965 saw the number of LFB stations increase")]
d["events"]+=[ev("1834","other","incident","Fire at the Palace of Westminster, one of the large fires that spurred public provision of the brigade",c+"7","both","Several large fires , most notably at the Palace of Westminster in 1834"),
 ev("1965","other","reorganisation","New authority organised the brigade into 11 divisions (A to L) with three control rooms",c+"62","both","Upon the founding of the London County Council in 1965 , the new authority was organised into 11 divisions"),
 ev("2016","work","","Began providing first aid for some life-threatening medical emergencies",c+"4","both","Since 2016 , the LFB has provided first aid for some life-threatening medical emergencies")]
fin(n,d)
