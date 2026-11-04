import json,sys,os
base="batchB9"
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

def add(n,d,items):
    c=pre(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]; fl=it[7] if len(it)>7 else None; more=it[8] if len(it)>8 else None
        if more: more=[ex(c+m[0],m[1],m[2]) for m in more]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,fl,more))

# no change
for n in ["Milan_Metro_Line_2","Irina_Levitina"]: fin(n,load(n))

n="Arnulf_of_Carinthia";d=load(n);fin(n,d)

n="The_Chris_Gethard_Show";d=load(n);c=pre(d)
setev(d,"e5",[ex(c+"5","date","but in May 2014 wrote on"),ex(c+"6","description","his Tumblr blog that they had elected not to air the episode")])
fin(n,d)

n="Volvo_9700";d=load(n)
add(n,d,[
("2003","other","regulation","EU and EEA limited maximum length of a two-axle vehicle to 13.5 m, affecting these models","7","both","However , in 2003 the European Union and European Economic Area limited the maximum length of a"),
("2007","work",None,"Second generation Volvo 9900 became a full member of the 9700 family","24","both","When the second generation was introduced in 2007 , it became a full member of the 9700 family"),
("2010","work",None,"Wroclaw-built Volvo 9500 introduced as low-price alternative at IAA Hannover","22","both","The Wrocław-built Volvo 9500 was introduced as a low-price alternative at IAA Hannover in 2010"),
("2015","work",None,"Volvo 9800 launched as replacement for the Mexican market","1","both","In 2015 , the Volvo 9800 was launched as a replacement for the Mexican market"),
("2018-03","work",None,"Double-decker Volvo 9800DD launched","1","both","followed by the double-decker 9800DD in March 2018")])
fin(n,d)

n="Esteban_Ocon";d=load(n);drop(d,"e8")
add(n,d,[
("2013","other","first win","First single-seater victory at Le Castellet in Formula Renault 2.0","5","description","as well as his first victory at Le Castellet",DD,[("5","date","For 2013 , he decided to switch to the ART Junior Team")]),
("2017","other","first points","Scored first Formula One point in first race for Force India","12","description","Ocon scored his first Formula One point in his first race for Force India",DD,[("11","date","Force India ( 2017–2018 ) . 2017 .")])])
fin(n,d)

n="Rezidor_Hotel_Group";d=load(n)
flag(d,SI,"e25")
add(n,d,[
("2012-01","naming",None,"Announced that Carlson and Rezidor hotel groups would operate under the single name Carlson Rezidor Hotel Group","13","both","In January 2012 , it was announced that Carlson hotel group and Rezidor hotel group would runs hotels under one name Carlson Rezidor Hotel Group"),
("2017","naming",None,"Parent company Carlson Hotels, Inc. renamed Radisson Hospitality, Inc. (fourth quarter)","16","both","was renamed to Radisson Hospitality , Inc . in the fourth quarter of 2017",AP)])
fin(n,d)

n="44_Union_Square";d=load(n)
add(n,d,[
("1928-12","work",None,"Much of the structure substantially complete","10","description","and by December much of the structure was substantially complete",DD,[("9","date","In January 1928 , a month after the purchase of the site")]),
("2020","work",None,"Prospective tenant Slack Technologies withdrew from the project","24","both","Prospective tenant Slack Technologies , which was slated to take all the space in 2019 , ultimately withdrew from the project in early 2020",AP)])
fin(n,d)

n="Game_Grumps";d=load(n)
add(n,d,[
("2016-03-30","other","live show","Game Grumps Live special performance at Hollywood Improv (March 30 and 31)","14","description","appear at Hollywood Improv for a special performance of Game Grumps Live on March 30 and 31",DD,[("14","date","In February 2016 , it was announced that Avidan and Hanson would appear at Hollywood Improv")]),
("2016-04-29","other","live show","Game Grumps Live performances at Levity Live, Nyack (April 29 and 30)","14","description","performances of Game Grumps Live on April 29 and 30",DD,[("14","date","Later , in April 2016 , it was announced that Avidan and Hanson would appear at Levity Live in Nyack")]),
("2019-11","work",None,"Channel posted two videos covering Dendy console games, start of the Soviet Jump Game promotion","40","both","In November 2019 , the channel posted two videos covering games for the Dendy video game console"),
("2019-12-03","work",None,"Hanson discovered a multiplayer battle royale game for the Dendy console","40","both","It was followed by a video on December 3 , 2019 , where Arin Hanson discovered a multiplayer battle royale game for the console")])
fin(n,d)

n="Bill_Goldberg";d=load(n);c=pre(d)
setev(d,"e27",[ex(c+"43","description","defeated him for the World Heavyweight Championship at Unforgiven on September 21"),ex(c+"2","date","wrestled for All Japan Pro Wrestling ( AJPW ) between 2002 and 2003 , and for WWE between 2003 and 2004")]);flag(d,DD,"e27")
setev(d,"e61",[ex(c+"61","description","At Super ShowDown on February 27 , Goldberg defeated The Fiend to win the Universal Championship for the second time"),ex(c+"61","date","After six months of inactivity , Goldberg returned to WWE on the February 7 , 2020 episode of SmackDown")]);flag(d,DD,"e61")
add(n,d,[
("1997","other","pay-per-view debut","Made pay-per-view debut at Starrcade, defeating Steve McMichael","13","description","Goldberg made his pay-per-view debut at Starrcade",DD,[("13","date","On the September 22 , 1997 episode of Nitro , Goldberg defeated Hugh Morrus in his debut match")]),
("1998","other","award","Pro Wrestling Illustrated Rookie of the Year","88","both","Rookie of the Year ( 1998 )"),
("1998","other","award","Pro Wrestling Illustrated Inspirational Wrestler of the Year","88","both","Inspirational Wrestler of the Year ( 1998 )"),
("1998","other","award","Wrestling Observer Newsletter Rookie of the Year","90","both","Wrestling Observer Newsletter - Rookie of the Year ( 1998 )"),
("1998-04-22","other","title defense","First successful title defense of the US Heavyweight Championship against Mike Enos on Thunder","15","description","Two days later on the April 22 episode of Thunder , he made his first successful title defense against Mike Enos",DD,[("14","date","In early 1998 , Goldberg squashed Brad Armstrong at SuperBrawl VIII")]),
("1999","other","title","Won second WCW United States Heavyweight Championship from Sid Vicious at Halloween Havoc","24","description","Goldberg defeated Sid via referee stoppage , and thus won his second United States Heavyweight Championship",DD,[("22","date","prepare for his movie debut in the 1999 film alongside Timecop film star Jean-Claude Van Damme")]),
("1999","other","title","Won WCW World Tag Team Championship with Bret Hart, losing it a week later","27","description","teaming with him to defeat Creative Control for the WCW World Tag Team Championship",DD,[("22","date","prepare for his movie debut in the 1999 film alongside Timecop film star Jean-Claude Van Damme")]),
("2002-08","affiliation",None,"Served as color commentator for Pride Fighting Championship","79","both","In August 2002 , during his professional wrestling tenure in Japan , Goldberg served as color commentator in mixed martial arts ( MMA ) promotion Pride Fighting Championship"),
("2016","other","award","Pro Wrestling Illustrated Comeback of the Year","88","both","Comeback of the Year ( 2016 )"),
("2018-01-15","other","honour","ESPN announced Goldberg would headline the WWE Hall of Fame Class of 2018","59","both","On January 15 , 2018 , ESPN announced that Goldberg would be inducted as the headliner of the WWE Hall of Fame Class of 2018"),
("2021","other","title match","Faced Drew McIntyre for the WWE Championship at the Royal Rumble, unsuccessful","63","both","After a 9-month hiatus , Goldberg faced Drew McIntyre for the WWE Championship at the 2021 Royal Rumble")])
fin(n,d)
