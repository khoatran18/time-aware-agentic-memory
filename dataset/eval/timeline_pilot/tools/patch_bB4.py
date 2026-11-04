import json,sys,os
base="batchB4"
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

# no change
for n in ["Counselor_to_the_President"]: fin(n,load(n))

# Luftflotte 5
n="Luftflotte_5";d=load(n);c=pre(d)
d["events"]+=[ev("1944","naming","","Ground commands renamed: LgK Norwegen became K.G. in Norwegen, LgK Finnland became K.G. Finnland",c+"9","description","On the ground LgK Norwegen became Kommandierende General der Luftwaffe ( K.G. ) in Norwegen",more=[ex(c+"9","date","In 1944 these formations were reorganized again")],flag=DD)]
fin(n,d)

# Line 7 Beijing Subway
n="Line_7_Beijing_Subway";d=load(n)
quote(d,"e2","In 1983 Line 6 was dissolved into two distinct lines .")
fin(n,d)

# Daniel Fleetwood
n="Daniel_M_Fleetwood";d=load(n);c=pre(d)
d["events"]+=[ev("1998","other","award","Mobile-proton memory chip recognized as Discover magazine's Invention of the Year in computer hardware and electronics",c+"5","both","also recognized as Discover magazines 1998 Invention of the Year")]
fin(n,d)

# Oxenstierna
n="Johan_Gabriel_Oxenstierna";d=load(n);c=pre(d)
drop(d,"e5")
quote(d,"e17","until his assassination in 1792 , shortly before which Oxenstierna was made a Riksmarskalk")
d["events"]+=[ev("1788","role","","Became a member of the Cabinet during the Russo-Swedish War",c+"12","both","in the absence of the king during the Russo-Swedish War ( 1788–1790 ) , he was a member of the Cabinet",flag=DD),
 ev("1790","role","","Membership of the Cabinet ended with the Russo-Swedish War",c+"12","both","in the absence of the king during the Russo-Swedish War ( 1788–1790 ) , he was a member of the Cabinet",flag=DD)]
undrop(d,"Member of the Cabinet during the Russo-Swedish War")
fin(n,d)

# David N. Livingstone (named lectures listed under professional distinctions)
n="David_N_Livingstone";d=load(n);c=pre(d)
L=[("1994","11","Charles Lyell Lecturer , British Association for the Advancement of Science , 1994–95","Charles Lyell Lecturer, BAAS (1994-95)"),
 ("2001","11","Hettner Lectures , University of Heidelberg , 2001","Hettner Lectures, University of Heidelberg"),
 ("2002","11","Murrin Lectures , University of British Columbia , 2002","Murrin Lectures, University of British Columbia"),
 ("2005","11","Progress in Human Geography Lecture , Royal Geographical Society , 2005","Progress in Human Geography Lecture, RGS"),
 ("2007","11","Appleton Lecture , University of Hull , 2007","Appleton Lecture, University of Hull"),
 ("2007","12","Von Humboldt Lecture , U.C.L.A. , 2007","Von Humboldt Lecture, UCLA"),
 ("2007","13","Gordon Manley Lecture , Royal Holloway , University of London , 2007","Gordon Manley Lecture, Royal Holloway"),
 ("2009","13","Gunning Lecture , University of Edinburgh , 2009","Gunning Lecture, University of Edinburgh"),
 ("2010","13","Gregory Lecture , University of Southampton , 2010","Gregory Lecture, University of Southampton"),
 ("2014","13","Gifford Lectures , University of Aberdeen , 2014","Gifford Lectures, University of Aberdeen"),
 ("2015","13","Dudleian Lecture , Harvard University , 2015","Dudleian Lecture, Harvard University")]
for y,ch,q,t in L: d["events"].append(ev(y,"other","lecture","Delivered "+t,c+ch,"both",q))
fin(n,d)

# Masters (snooker)
n="Masters_snooker";d=load(n);c=pre(d)
quote(d,"e40","2011 event , and the use of wild-cards was discontinued at the same time")
d["events"]+=[ev("2015","other","maximum break","Marco Fu made the third maximum break at the Masters",c+"4","both","Hong Kongs Marco Fu made the third in 2015"),
 ev("2020","other","title","Stuart Bingham won the Masters, the oldest champion at 43",c+"2","both","The oldest Masters champion is Stuart Bingham , who was aged 43 years and 243 days in 2020",flag=DD)]
d["undated_mentions"].append("Yearly seeding exceptions (2006, 2013, 2014, 2015, 2018, 2020, 2021: suspensions, withdrawals, COVID replacements) not recorded as events")
fin(n,d)

# Museum fuer Moderne Kunst
n="Museum_f_r_Moderne_Kunst";d=load(n);c=pre(d)
txt(d,"e3","Peter Iden expanded the collection with works of recent decades, 1981-1987")
txt(d,"e20","Exhibition Eric Fischl: Works from the 1980s & Travel of Romance held".replace("Works from the 1980s","early works"))
get(d,"e20")["evidence"][0]["quote"]="2000 : Eric Fischl"
txt(d,"e65","Exhibition Not in Fashion: fashion and photography held")
d["events"]+=[ev("1987","role","","Peter Iden's term as founding director ended",c+"1","both","founding director of the museum ( 1978-1987 )")]
fin(n,d)

# Bohemond IV
n="Bohemond_IV_of_Antioch";d=load(n);c=pre(d)
txt(d,"e11","Surprised by a coup of Raymond-Roupen's supporters, sought refuge in the citadel, then defeated them")
d["events"]+=[ev("1188","ownership_structure","conquest","Saladin conquered the County of Tripoli except the capital and two fortresses",c+"0","description","conquered the county , save for the capital and two fortresses",more=[ex(c+"1","date","summer 1188")],flag=AP),
 ev("1194","location","","Hurried from Tripoli to Antioch with his army to help his brother, forcing the Armenian troops back to Cilicia",c+"12","description","Bohemond hurried from Tripoli to Antioch at the head of his army to help his brother",more=[ex(c+"12","date","he captured and imprisoned Bohemond III in early 1194")],flag=DD),
 ev("1207","other","imprisonment","Captured and imprisoned the Latin patriarch Peter of Angoulême",c+"25","description","He captured and imprisoned the Latin patriarch who refused to acknowledge him as the lawful prince",more=[ex(c+"25","date","Peter of Angoulême helped Raymond-Roupens supporters to return from Cilicia to Antioch in late 1207")],flag=DD),
 ev("1217","location","","Marched with his vassals to Acre to join the Fifth Crusade",c+"32","description","Bohemond and his vassals marched to Acre",more=[ex(c+"32","date","Duke Leopold VI of Austria , who landed at Acre in late summer 1217")],flag=DD),
 ev("1224","family","imprisonment","Son Philip captured and imprisoned by Constantine of Baberon",c+"35","both","Philip and his supporters were captured and imprisoned at the end of 1224")]
undrop(d,"Hurried from Tripoli to Antioch to help his brother")
fin(n,d)

# Good Game
n="Good_Game_TV_program";d=load(n);c=pre(d)
d["events"]+=[ev("2008-10-06","role","","Andrew Bindi Hansen first appeared as guest host (series 4, episode 25)",c+"42","both","He originally guest appeared on 6 October 2008 in series 4 , episode 25"),
 ev("2009-08-24","work","","100th episode aired, with returning former presenters interviewed",c+"32","both","he returned for an interview for the 100th episode on 24 August 2009"),
 ev("2010-06-19","other","appearance","Hosts Bajo and Hex hosted an episode of ABC music video show Rage",c+"20","both","hosting an episode of the ABC music video show Rage on 19 June 2010"),
 ev("2011-03-21","role","","Callout for a new field reporter posted on Facebook",c+"33","both","after a callout via a Facebook post on 21 March 2011"),
 ev("2013","affiliation","","Hosts became ambassadors for the schools filmmaking competition Screen It",c+"20","both","In 2013 , the two hosts became ambassadors for the national schools filmmaking competition Screen It"),
 ev("2013","other","event","Bajo and Hex held an AMA with fans on Reddit",c+"73","both","In 2013 , Bajo and Hex had an AMA with their fans on Reddit"),
 ev("2014","other","event","Hosts spoke at the Perth Writers Festival in The Game Changers talks",c+"20","both","In 2014 , they spoke at the Perth Writers Festival"),
 ev("2014","other","event","Hosts hosted the MCV Pacific Awards for gaming",c+"20","both","They also hosted the 2014 MCV Pacific Awards for gaming"),
 ev("2014","work","","Viewer poll of the 100 best games run, aired as The Good Game Top 100 special",c+"78","both","In 2014 , Good Game ran a poll asking its viewers for their votes of the 100 best games"),
 ev("2015-02-04","role","","Michael Hing's role as first host of Good Game Pocket announced",c+"40","both","his involvement as the host was announced on 4 February 2015"),
 ev("2016-07","role","","Michael Hing's final episode as host of Good Game Well Played",c+"40","both","his final episode was in July 2016")]
fin(n,d)
