import json,sys
base="batch3"
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
def und(d,*keys): d["undated_mentions"]=[u for u in d["undated_mentions"] if not any(k in u for k in keys)]
def flag(d,f,*ids):
    for i in ids: get(d,i)["flag"]=f
def ex(chunk,role,quote): return {"chunk_id":chunk,"role":role,"quote":quote}
AP="approximate_date"
# 2AM
n="2AM_band";d=load(n);c=d["page_id"]+"#"
get(d,"e16")["evidence"].append(ex(c+"22","both","2AM 1st Japan Tour Never Let You Go ( 2012 )"))
get(d,"e14")["evidence"].append(ex(c+"22","both","2AM 1st Asia Tour The Way Of Love ( 2012 )"))
d["events"]+=[
 ev("2010","work","","Began 1st tour Saint O Clock",c+"22","both","2AM 1st Tour Saint O Clock ( 2010-2011 )"),
 ev("2011","work","","Ended 1st tour Saint O Clock",c+"22","both","2AM 1st Tour Saint O Clock ( 2010-2011 )"),
 ev("2011","work","","Held Come On Christmas Concert",c+"22","both","2AM Come On Christmas Concert ( 2011 )"),
 ev("2013","work","","Held 1st World Tour Nocturne Symphony Of The Night",c+"22","both","2AM 1st World Tour Nocturne Symphony Of The Night ( 2013 )"),
 ev("2015","other","hiatus","Group entered hiatus",c+"16","both","2015–present : Hiatus"),
 ev("2017-11-28","other","military_service","Seulong enlisted for mandatory military service",c+"18","both","On November 28 , 2017 , Seulong enlisted for his mandatory military service"),
 ev("2018-08","other","military_service","Jo Kwon enlisted for mandatory military service",c+"18","both","In August 2018 , Jo Kwon enlisted to fulfil mandatory military service requirement"),
 ev("2019-01-17","other","military_service","Announced Jinwoon would enlist in March",c+"18","both","On January 17 , 2019 , it was announced Jinwoon would enlist in March")]
und(d,"Hiatus period"); fin(n,d)
# Albuquerque
n="Albuquerque_Dukes";d=load(n);c=d["page_id"]+"#"
drop(d,"e7")
d["events"]+=[ev("1955","affiliation","","West Texas-New Mexico League stepped up to Class B",c+"2","date","In 1955 the West Texas–New Mexico",more=[ex(c+"3","description","League stepped up one more level , to Class B .")])]
fin(n,d)
# Breitscheidplatz
n="Breitscheidplatz";d=load(n);c=d["page_id"]+"#"
d["events"]+=[
 ev("1895","work","","Kaiser Wilhelm Memorial Church consecrated",c+"3","both","It was consecrated in 1895"),
 ev("1916","work","","Building on Europa-Center site began housing the Romanisches Café (after 1916)",c+"4","both","which after 1916 housed the Romanisches Café",AP),
 ev("1928","other","speech","Goebbels made a speech attacking the establishments around the church (by 1928)",c+"6","both","By 1928 , when Joseph Goebbels made a speech attacking the commercial establishments",AP),
 ev("1930-04-01","work","","The Blue Angel premiered at the Gloria-Palast",c+"5","both","where The Blue Angel premièred on 1 April 1930"),
 ev("1961","work","","New Gedächtniskirche consecrated",c+"9","date","was consecrated in 1961",more=[ex(c+"8","description","The new Gedächtniskirche")])]
fin(n,d)
# David Young
n="David_Young_Iowa_politician";d=load(n);c=d["page_id"]+"#"
get(d,"e13").pop("flag",None); get(d,"e1")["text"]="Born"
d["events"]+=[
 ev("2017-03","other","vote","Opposed the original Republican effort to repeal Obamacare",c+"12","both","Young opposed the original March 2017 Republican effort to repeal Obamacare"),
 ev("2017-09","other","vote","Supported refunding of the Childrens Health Insurance Program",c+"15","both","In September 2017 , Young supported the refunding of the Childrens Health Insurance Program"),
 ev("2018-01","other","statement","Reiterated support for legal status for DREAMers",c+"19","both","In January 2018 , Young reiterated support for permanent legal status for so-called DREAMers")]
fin(n,d)
# Shackleton Bailey
n="D_R_Shackleton_Bailey";d=load(n);c=d["page_id"]+"#"
get(d,"e5").pop("flag",None); flag(d,"derived_date","e16"); get(d,"e1")["text"]="Born"; get(d,"e58")["text"]="Died"
d["events"]+=[
 ev("1958","work","","Began Oxford OCT edition of Cicero Epistulae (4 volumes)",c+"9","both","Oxford , OCT , 1958-1982"),
 ev("1982","work","","Completed Oxford OCT edition of Cicero Epistulae (4 volumes)",c+"9","both","Oxford , OCT , 1958-1982")]
fin(n,d)
# Fulk
n="Fulk_King_of_Jerusalem";d=load(n)
flag(d,AP,"e1","e4","e5","e9"); fin(n,d)
# Garnidelia
n="Garnidelia";d=load(n);fin(n,d)
# Lower Norrland
n="Lower_Norrland_Military_District";d=load(n);drop(d,"e28","e29","e42","e46");fin(n,d)
# Vindobona
n="Vindobona_train";d=load(n);drop(d,"e9","e16","e21");flag(d,AP,"e18")
d["undated_mentions"].append("Name Vindobona reused for Railjet line Prague-Vienna-Graz (after December 2018, date not stated)")
fin(n,d)
# Michael Batty
n="Michael_Batty";d=load(n);c=d["page_id"]+"#"
drop(d,"e43","e44"); get(d,"e1")["text"]="Born"
get(d,"e14")["text"]="Chair of CHOPS ended (source gives 1986-1980)"; get(d,"e27")["text"]="Appointed to UCL"
d["events"]+=[ev("1995","other","founding","Centre for Advanced Spatial Analysis set up",c+"0","both","set up when he was appointed to UCL in 1995")]
d["undated_mentions"].append("William Alonso Prize a second time for The New Science of Cities (2017-2018, range not placeable)")
fin(n,d)
