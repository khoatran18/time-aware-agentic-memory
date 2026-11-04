# Bổ sung sau khi session chính đọc kiểm V5/V6 (chạy SAU patch_bV5.py / patch_bV6.py; chạy lại được)
import json
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
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

A("batchV5","SECR_N_class",[
("1913","role",None,"Richard Maunsell appointed Chief Mechanical Engineer of the SECR","6","both","Richard Maunsell was appointed CME of the SECR in 1913"),
("1924","work","experiment","Worthington feed pump fitted to No. A819 as the class's first experiment","43","both","The first experiment entailed fitting a Worthington feed pump to No . A819 in 1924"),
("1925-05","other","exhibition","No. A866 put on display at the British Empire Exhibition at Wembley","37","both","A866 was put on display at the British Empire Exhibition at Wembley from May to November 1925"),
("1930-06","work","experiment","No. A816 withdrawn from service for experimental Anderson steam conservation equipment at Eastleigh Works","43","both","In June 1930 , No . A816 was withdrawn from service for the application of experimental Anderson steam conservation equipment at Eastleigh Works"),
("1931-08","work","experiment","No. A816 emerged from Eastleigh for trials of the Anderson equipment","45","both","No . A816 emerged from Eastleigh in August 1931 for trials"),
("1932","work","W class","Prototype W class produced from N class parts","23","both","The prototype W class was produced in 1932 from N class parts"),
("1933-10","work","experiment","No. 1850 had its Walschaerts valve gear replaced with Marshall valve gear at Eastleigh Works","47","both","The final experiment with performance enhancement began in October 1933"),
("1934-04","work","experiment","No. 1850 re-entered traffic with its Walschaerts valve gear re-fitted","48","both","No . 1850 re-entered traffic in April 1934"),
("1935-05","work","experiment","No. A816 converted back to standard form (work from May to August 1935)","45","both","converted back to standard form between May and August 1935"),
("1939","other","livery","Nos. 1413 and 1850 painted in unlined olive green because of labour shortages","53","both","In 1939 , shortly after the start of the Second World War , locomotives Nos . 1413 and 1850 were painted in unlined olive green because of labour shortages"),
("1941","other","livery","Nos. 1821, 1825, 1847, 1878 and 1403 run in unlined olive green with Bulleid's gilt block lettering","53","both","In 1941 , Nos . 1821 , 1825 , 1847 , 1878 and 1403 were run in unlined olive green with Bulleids gilt block lettering"),
("1946","other","livery","Two locomotives (Nos. 1817 and 1854) repainted in Bulleid's malachite green livery","54","both","In 1946 , two locomotives , Nos . 1817 and 1854 , were repainted in Bulleids malachite green livery"),
("1947","work","fuel trial","No. 1831 given electric lighting and converted to oil-burning for fuel trials","39","both","In 1947 , No . 1831 was given electric lighting and converted to oil-burning"),
("1948-12","work","fuel trial","No. 1831 reverted to coal-firing","40","both","reverted to coal-firing in December 1948"),
("1958-04-04","other","accident","No. 31867 hauling a parcels train overran signals and collided with an electric multiple unit at Gloucester Road Junction, Croydon; nine injured","51","both","On 4 April 1958 , locomotive No . 31867 was hauling a parcels train that overran signals and collided with an electric multiple unit at Gloucester Road Junction"),
("1998","other","preserved No. 1874","Preserved No. 1874 withdrawn because of firebox reconstruction needs","62","both","The locomotive was withdrawn in 1998 due to problems that require firebox reconstruction"),
("2012","other","preserved No. 1874","Preserved No. 1874 repainted into SR Wartime Black","62","both","In 2012 , the locomotive was repainted into its SR Wartime Black guise of 1874"),
("2014","location","preserved No. 1874","Preserved locomotive moved from the Mid-Hants Railway to the Swanage Railway","62","both","The locomotive was moved from the Mid-Hants Railway to the Swanage Railway in 2014"),
("2014-08","work","preserved No. 1874","Overhaul to return No. 31874 to operational condition began","62","both","In August 2014 , the overhaul to return 31874 to operational condition began")])

A("batchV6","Sergio_P_rez",[
("2006","other","A1 Grand Prix","Took part in a single round of the A1 Grand Prix for A1 Team Mexico (2006-07 season)","16","both","In the 2006–07 A1 Grand Prix season , Pérez took part in a single round of the championship for A1 Team Mexico","approximate_date"),
("2008","affiliation","GP2 Asia","Drove for Campos Grand Prix in the GP2 Asia Series (2008-09 season)","19","both","Pérez drove for the Campos Grand Prix team in the 2008–09 GP2 Asia Series","approximate_date"),
("2015","other","podium","Podium in Russia, Force India's third ever","47","both","His best race of the season was in Russia , where he scored his first podium of 2015 and Force Indias third ever"),
("2016","other","podium","Sixth career podium at Monaco, Force India's fourth, in wet and changing conditions","50","description","In Monaco , Pérez scored his sixth ( and Force Indias fourth ) podium finish in wet and changing conditions","derived_date",[("49","date","2016 . Pérez experienced a difficult start to the season")]),
("2018","other","podium","Eighth career podium, third at the Azerbaijan Grand Prix","55","description","He then achieved his eighth career podium finish at the Azerbaijan Grand Prix , finishing 3rd after an incident-strewn race","derived_date",[("55","date","making him the first driver to finish on the podium twice at the Baku City Circuit ( in 2016 and 2018 )")]),
("2018","other","administration","Force India put into administration after the Hungarian Grand Prix following legal action by creditors including Pérez","57","description","After the Hungarian Grand Prix , Force India was put into administration","derived_date",[("2","date","He remained with Force India when the team went into administration in 2018")]),
("2018","ownership_structure","administration","Force India's assets purchased by a consortium led by Lawrence Stroll; team re-admitted to the championship","57","description","Force Indias assets were purchased by a consortium of investors led by Lawrence Stroll","derived_date",[("2","date","He remained with Force India when the team went into administration in 2018")])])
A("batchV5","Flatiron_Building",[
("1892","other","building code","New York City building code change eliminated the masonry fireproofing requirement, making steel-skeleton construction feasible","52","both","a change to New York Citys building codes in 1892"),
("1911","other","restaurant","Flatiron Restaurant bought by Louis Bustanoby and converted into the 400-seat French restaurant Taverne Louis","32","both","in 1911 the Flatiron Restaurant was bought by Louis Bustanoby"),
("1959","other","tenant","St. Martin's Press moved into the building","39","both","In 1959 , St . Martins Press moved into the building"),
("2004","other","tenant","Macmillan rented all 21 floors of the building's office space","39","both","until by 2004 , all 21 floors of the Flatiron Buildings office space was rented by Macmillan"),
("2017-07","other","tenant","Macmillan announced it would consolidate all its New York offices in the Equitable Building at 120 Broadway","46","both","In July 2017 , Macmillan announced that it was consolidating all of its New York offices to the Equitable Building at 120 Broadway"),
("2019-06","other","tenant","Macmillan had left the building; all 21 office floors vacant","46","both","By June 2019 , Macmillan had left the building , and all 21 office floors were vacant")])
A("batchV5","Gamvik",[
("1982-03-12","other","air crash","Widerøe Twin Otter LN-BNK crashed into the sea near Mehamn, killing all fifteen on board","6","both","On 12 March 1982 , a Widerøe Twin Otter , registration number LN-BNK , crashed into the sea near Mehamn , killing all fifteen on board")])
A("batchV6","LB_amp_SCR_E4_class",[
("1942","other","air raid","No. 2483 Hellingly severely damaged by enemy action at Eastbourne motive power depot during the Baedeker Blitz","4","both","No . 2483 Hellingly , was severely damaged as a result of enemy action against Eastbourne motive power depot in 1942"),
("1944-07","other","scrapped","Hellingly scrapped","4","both","Hellingly was scrapped in July 1944"),
("1947","work","trial","No. 2510 tested unsuccessfully on the Isle of Wight railways","4","both","No . 2510 , was tested on the railways of the Isle of Wright in 1947"),
("1971","other","preserved No. 32473","Preserved No. 32473 withdrawn from traffic and dismantled","10","both","The engine was withdrawn from traffic in 1971 and dismantled"),
("1997","other","preserved No. 32473","Preserved No. 32473 returned to traffic after a long overhaul","10","both","following a long overhaul , she returned to traffic in 1997"),
("2005","other","preserved No. 32473","Preserved No. 32473 repainted into British Railways lined black mixed traffic livery","11","both","In 2005 she was repainted into British Railways lined black mixed traffic livery"),
("2008-05","other","preserved No. 32473","Preserved No. 32473 withdrawn from service and taken into the Bluebell workshops for overhaul","11","both","Following withdrawal from service in May 2008"),
("2010-01","other","preserved No. 32473","Overhaul and repaint into 1920s Southern Railway green completed","11","both","This was completed during January 2010")])
A("batchV6","Gleaston_Castle",[
("1291","ownership_structure","Aldingham manor","Aldingham manor (Muchland) came into the ownership of the Harrington family","3","both","in 1291 it came into the ownership of the Harrington family")])
# Manto: bỏ các tuyển tập ghi năm 1955 (có thể là di cảo, ông mất 1955-01-18); chuyển vào undated_mentions
b="batchV6";n="Saadat_Hasan_Manto";d=json.load(open(f"{b}/rev/{n}.json"))
gone=[e for e in d["events"] if e["date"]=="1955" and e["track"]=="work"]
if gone:
    d["events"]=[e for e in d["events"] if e not in gone]
    d["undated_mentions"]+=["Collections and story attributed to 1955 (year only; may be posthumous): "+"; ".join(e["text"].replace("Published ","").rstrip(".") for e in gone)]
fin(b,n,d)
