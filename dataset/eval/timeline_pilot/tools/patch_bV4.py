import json,sys,os
base="batchV4"
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


# no change (kiểm tay, không sửa)
for n in ["Choi_Yoo_jung_singer","International_Association_for_Political_Science_Students","Willy_Hernang_mez","Young_Girl_with_a_Flower_Basket"]: fin(n,load(n))

n="Chelyabinsk";d=load(n)
add(n,d,[
("1892","other","railway","Samara-Zlatoust Railway completed, connecting the city with Moscow and European Russia","10","both","In 1892 , the Samara-Zlatoust Railway was completed"),
("1892","work",None,"Construction of the Trans-Siberian Railway started from Chelyabinsk","10","both","Also in 1892 , construction of the Trans-Siberian Railway started from Chelyabinsk"),
("1913","other","museum","Chelyabinsk Regional Museum founded","43","both","Chelyabinsk Regional Museum was founded in 1913"),
("1930","education",None,"Chelyabinsk State Agroengineering Academy founded, the oldest university in the city","30","both","The oldest , Chelyabinsk State Agroengineering Academy , was founded in 1930"),
("1933","work","factory","Chelyabinsk Tractor Plant built","2","both","Tractor Plant was built in 1933"),
("1934","education",None,"Chelyabinsk State Pedagogical University founded","30","both","followed by the Chelyabinsk State Pedagogical University in 1934"),
("2007","work","shopping mall","Gorky shopping mall built","36","both","Gorky ( English : Hills ) , built in 2007"),
("2007","other","museum","Museum of Military Equipment in the Garden of Victory founded","46","both","The Museum of Military Equipment in the Garden of Victory was founded in 2007"),
("2011","work","shopping mall","Rodnik shopping mall built","36","both","Rodnik ( English : Spring ) built in 2011"),
("2011","other","agreement","Beeline and the city transport signed an agreement to provide passengers free internet","37","both","In 2011 the telecommunications company Beeline and Chelyabinsk city transport signed an agreement to provide passengers free internet"),
("2013-02-15","other","meteor","Superbolide meteor exploded over the Ural Mountains, with fragments falling in and around the city and over a thousand people injured","15","both","Shortly after dawn on February 15 , 2013 , a superbolide meteor descended")])
fin(n,d)

n="HMAS_Cairns_J183";d=load(n)
add(n,d,[("1938","other","naval board","Australian Commonwealth Naval Board identified the need for a general purpose local defence vessel for anti-submarine and mine-warfare duties","1","both","In 1938 , the Australian Commonwealth Naval Board ( ACNB ) identified the need for a general purpose local defence vessel")])
fin(n,d)

n="FC_Flora";d=load(n)
add(n,d,[
("2016","location","stadium","Expansion of A. Le Coq Arena began","16","both","expanded from 2016 to 2018"),
("2018","location","stadium","Expansion of A. Le Coq Arena completed","16","both","expanded from 2016 to 2018")])
fin(n,d)

n="Helmut_Lang_fashion_brand";d=load(n)
add(n,d,[("1997","location",None,"Helmut Lang moved to New York","5","both","Lang moved to New York in 1997")])
fin(n,d)

n="Igor_Grabar";d=load(n)
add(n,d,[
("1897-01","work","article","Published article in Niva defending avant-garde art against Vladimir Stasov, provoking Stasov's campaign against Repin","17","both","In January–February 1897 , Grabar , obliged to write for Niva , published an article defending avant-garde art against Vladimir Stasov","approximate_date"),
("1899","work","article","Published article that caused a conflict between Ilya Repin and Mir iskusstva","17","both","Another article published in 1899 caused a conflict between Ilya Repin and Mir iskusstva"),
("1918-06","other","nationalization","Tretyakov Gallery nationalized","37","both","nationalization in June 1918"),
("1921","role",None,"Became the first professor of Art restoration at Moscow State University","2","both","In 1921 Grabar became the first professor of Art restoration at the Moscow State University"),
("1926","role",None,"Replaced as head of the Tretyakov Gallery by architect Aleksey Shchusev","38","both","in 1926 Grabar was replaced with architect Aleksey Shchusev"),
("1948","other","campaign","Caught in another campaign against random targets in art and science","53","both","in 1948 Grabar was caught in another campaign against random targets in art and science")])
fin(n,d)

n="Vladimir_Bukovsky";d=load(n)
add(n,d,[
("1971-03-12","other","letter","Bukovsky's letter on psychiatric abuse appeared in The Times (London)","20","date","The documents were released to the press in March 1971","derived_date",[("20","description","Bukovskys letter appeared on 12 March in The Times ( London )")]),
("1985","other","organisation","Resistance International expanded into the American Foundation for Resistance International","34","both","In 1985 it expanded into the American Foundation for Resistance International"),
("1987-03","other","open letter","With nine other emigre authors raised doubts about the substance and sincerity of Gorbachev's reforms","36","both","In March 1987 , Bukovsky and nine other émigré authors ( Ernst Neizvestny , Yury Lyubimov , Vasily Aksyonov and Leonid Plyushch among them ) caused a furore in the West"),
("2005-12-18","work","op-ed","Op-ed in The Washington Post recounting his torture in Lefortovo prison","55","both","In an 18 December 2005 op-ed in The Washington Post"),
("2007-12-14","role","candidacy","Grigory Yavlinsky announced he would forgo his own campaign and support Bukovsky's candidacy","65","both","announced on 14 December 2007 at the Yabloko party conference"),
("2010-03-10","other","manifesto","Among the first 34 signatories of the online anti-Putin manifesto Putin must go","68","both","Putin must go , an online anti-Putin manifesto published on 10 March 2010")])
fin(n,d)
