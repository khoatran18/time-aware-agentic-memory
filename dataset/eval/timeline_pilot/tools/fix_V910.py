# Bổ sung sau khi session chính đọc kiểm V9, V10 (chạy SAU patch_bV9.py và patch_bV10.py). Idempotent nhờ fin.
import json
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date.lstrip("-"))],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=[{"chunk_id":chunk.split("#")[0]+"#"+m[0],"role":m[1],"quote":m[2]} for m in more]
    if flag:e["flag"]=flag
    return e
def fin(base,n,d):
    seen=set();ev2=[]
    for e in d["events"]:
        k=(e["date"],e["text"])
        if k not in seen: seen.add(k);ev2.append(e)
    d["events"]=sorted(ev2,key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def A(b,n,items,drop=()):
    d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
    d["events"]=[e for e in d["events"] if not any(s in e["text"] for s in drop)]
    for it in items:
        date,track,label,text,ch,role,q=it[:7]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,it[7] if len(it)>7 else None,it[8] if len(it)>8 else None))
    fin(b,n,d)
D="derived_date";AP="approximate_date"


AP="approximate_date";D="derived_date"
# ---- V10
A("batchV10","Meg_Whitman",[
("2010-09","other","scandal","Nicky Diaz Santillan revealed she had worked as Whitman's housekeeper despite being undocumented","42","both","In September 2010 , Nicky Diaz Santillan revealed that she was employed in the Whitman household as a housekeeper and nanny from 2000 to 2009 despite her status as an illegal worker"),
("2020-10","role","Quibi","Quibi closed while she was its CEO","0","both","She was also the CEO of Quibi before its closure in October 2020"),
])
A("batchV10","Gerhard_Schr_der",[
("1998","other","election","SPD under Schröder increased its vote share in the Lower Saxony state election","16","both","In the 1998 state elections , Schöders Social Democrats increased their share of the vote by about four percentage points"),
("2017-11","other","Paradise Papers","Named in the ICIJ Paradise Papers list of politicians","77","both","In November 2017 , an investigation conducted by the International Consortium of Investigative Journalism cited his name in the list of politicians named in Paradise Papers allegations"),
])
A("batchV10","Galatasaray_S_K_football",[
("1905","other","league","Joined the Istanbul League in the 1905-1906 season","13","both","Galatasaray joined the Istanbul League that was consisting of English and Greek teams in the season of 1905–1906",AP),
("1908","other","title","Won first championship title in 1908-1909","13","both","With their first championship title they won in 1908–1909",AP),
("1986","other","title","Won national championships in 15 sport branches in the 1986-87 season","17","both","winning national championships in 15 different sport branches in the 1986–87 season",AP),
("1988","other","Europe","Reached the European Cup semi-final in the 1988-89 season","17","both","reaching the semi-final of the European Cup in the 1988–89 season",AP),
("1999","other","title","Completed a quadruple in the 1999-2000 season","2","both","In the 1999–2000 season , the club achieved the rare feat of completing a quadruple",AP),
("2014","other","title","Won 20th league championship in the 2014-15 season","5","both","the teams 20th championship for the 2014–15 Süper Lig season",AP),
("2011","location","stadium","Previous home stadium demolished after the move to Türk Telekom Stadium","44","both","The stadium was in 2011 demolished after Galatsaray moved to the newly built Türk Telekom Stadium"),
])
A("batchV10","Federation_of_the_Greens",[
("2006","role","Minister of the Environment","Alfonso Pecoraro Scanio began as minister of the Environment","13","both","In 2006–2008 Pecoraro Scanio served as minister of the Environment"),
("2008","role","Minister of the Environment","Alfonso Pecoraro Scanio ended as minister of the Environment","13","both","In 2006–2008 Pecoraro Scanio served as minister of the Environment"),
("2006-11","other","party congress","Party congress confirmed Pecoraro Scanio's political line","14","both","In November 2006 Pecoraro Scanios political line was confirmed in a party congress"),
])
# ---- V9
A("batchV9","KF_Sk_nderbeu_Kor",[
("1958","other","Albanian Cup","Lost the Albanian Cup final","16","both","a three time finalist in the Albanian Cup in 1958 , 1965 and 1976"),
("1965","other","Albanian Cup","Lost the Albanian Cup final","16","both","a three time finalist in the Albanian Cup in 1958 , 1965 and 1976"),
("1976","other","Albanian Cup","Lost the Albanian Cup final","16","both","a three time finalist in the Albanian Cup in 1958 , 1965 and 1976"),
("2012","other","Albanian Cup","Lost the Albanian Cup final","25","both","before the 2012 final"),
("1976","other","First Division","Won the Albanian First Division in 1976-77","16","both","win the Albanian First Division in 1976–77",AP),
("2008","other","First Division","Won the Albanian First Division in 2008-09 and promotion to the Superliga","16","both","with the last win in 2008–09 season",AP),
("2012","other","Europe","First ever Champions League and European win, over Debrecen, in the 2012-13 campaign","26","both","They kicked off the 2012–13 campaign with their first ever Champions League and European win",AP),
])
A("batchV9","Helsingin_Jalkapalloklubi",[
])
A("batchV9","Anna_Karina",[
("1973","work","novel","Published the first of her four novels","21","both","Karina wrote four novels : ( 1973 )"),
("1988","work","novel","Published her third novel","21","both","( 1988 )"),
])
A("batchV9","S_rgio_Concei_o",[
("1998","other","UEFA Cup Winners' Cup","Played a significant part in Lazio's 1998-99 UEFA Cup Winners' Cup success","3","both","1998–99 UEFA Cup Winners Cup success",AP),
("2007","other","Belgian Cup","Lost the Belgian Cup final with Standard","7","both","losing the 2007 final of the Belgian Cup"),
("2008","role","captain","Promoted to team captain in 2008-09","9","both","In 2008–09 , Conceição was promoted to team captain",AP),
])
