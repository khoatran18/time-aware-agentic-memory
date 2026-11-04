# Vá V7, V8 (session chính đọc kiểm). Chạy từ dataset/eval/timeline_pilot: python3 -I tools/patch_bV78.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os
for b in ("batchV7","batchV8"):
    os.makedirs(f"{b}/rev",exist_ok=True)
    for f in glob.glob(f"{b}/sub/*.json"): shutil.copy(f,f"{b}/rev/"+os.path.basename(f))
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

A("batchV8","Harry_Holtzman",[
("1932","role",None,"Holtzman's remarks against the xenophobia of the League's director were instrumental in a membership vote that brought George Grosz and Hans Hofmann to teach at the Art Students League","2","both","At a membership meeting in early 1932 , Holtzman’s remarks against the xenophobia of the League’s director were instrumental")])
A("batchV8","Nico_H_lkenberg",[
("2006","other","racing","Finished fifth in the German Formula Three Championship (ATS Formel 3 Cup)","9","both","Hülkenberg finished fifth in the German Formula Three Championship ( ATS Formel 3 Cup ) in 2006"),
("2006","affiliation","A1 Grand Prix","Joined the German A1 Grand Prix team for the 2006-07 season","8","both","Hülkenberg also joined the German A1 Grand Prix team for the 2006–07 season",AP),
("2008","other","GP2 Asia","Made GP2 Asia Series debut for ART Grand Prix at the Bahrain round of the 2008-09 series, taking pole at the first attempt","12","both","Hülkenberg made his GP2 Asia Series début for the ART Grand Prix team at the third round of the 2008–09 GP2 Asia Series in Bahrain",AP)])
A("batchV7","Max_Planck_Institute_for_Astronomy",[
("2005","education","IMPRS","International Max Planck Research School (IMPRS) English-language doctoral program started","21","both","The IMPRS is an English-language doctoral program that started in 2005"),
("2009","other","Haus der Astronomie","Haus der Astronomie, a center for astronomy education and outreach, founded on the MPIA campus","24","both","In 2009 , Haus der Astronomie , a center for astronomy education and outreach was founded on the MPIA campus"),
("2011-12","other","Haus der Astronomie","Haus der Astronomie's galaxy-shaped building, funded and constructed by the Klaus Tschira Foundation, opened","24","both","The centers galaxy-shaped building , funded and constructed by the Klaus Tschira Foundation , was opened in December 2011")])
A("batchV8","GCR_Class_11E",[
("1927-02-27","other","accident","No. 5437 Prince George, hauling an express passenger train, collided with a light engine in Yorkshire","6","both","On 27 February 1927 , locomotive No . 5437 Prince George was hauling an express passenger train that was involved in a collision with a light engine at Yorkshire")])
A("batchV7","Stord",[
("1997","other","town status","Leirvik declared a town","0","both","Leirvik was declared a town in 1997"),
("2006-10-10","other","air accident","Atlantic Airways Flight 670 skidded off the runway at Stord Airport; four people died","12","both","On 10 October 2006 , Atlantic Airways Flight 670 skidded off the runway at the airport")])
A("batchV7","Healy_Hall",[
("1873","role",None,"Patrick Francis Healy became president of Georgetown University","2","both","In 1873 , Patrick Francis Healy became the president of Georgetown University"),
("1967-05-28","other","landmark","Georgetown Historic District, of which Healy Hall is a contributing property, listed as a National Historic Landmark District","12","both","Georgetown Historic District , which was listed as a National Historic Landmark District on May 28 , 1967")])

A("batchV7","Han_dynasty",[
("-0138","other","diplomacy","Zhang Qian's travels (139 to 125 BC) established Chinese contacts with many surrounding civilizations","23","both","Zhang Qians travels from 139 to 125 BC",AP),
("0011","other","flood","Massive Yellow River floods contributed to the downfall of Wang Mang's regime","32","both","massive floods of AD and 11 AD"),
("0065","other","religion","Buddhism first mentioned in Imperial China during the Eastern Han","99","both","was first mentioned in 65 CE"),
("0200","other","battle","Cao Cao defeated Yuan Shao at the Battle of Guandu","67","both","Cao defeated him at the Battle of Guandu in 200 AD"),
("0208","other","battle","Cao Cao defeated at the naval Battle of Red Cliffs; China divided into three spheres of influence","68","both","After Caos defeat at the naval Battle of Red Cliffs in 208 AD")])

A("batchV8","Myanmar",[
("1437","other","Arakan","Mrauk U unified the Arakan coastline for the first time","27","both","Mrauk U unified the Arakan coastline for the first time in 1437"),
("1740","other","Hanthawaddy","The Mon of Lower Myanmar founded the Restored Hanthawaddy Kingdom","33","both","In 1740 , the Mon of Lower Myanmar founded the Restored Hanthawaddy Kingdom"),
("1940","other","Burma Independence Army","Aung San formed the Burma Independence Army in Japan","43","both","In 1940 , before Japan formally entered the war , Aung San formed the Burma Independence Army in Japan"),
("1961","role",None,"U Thant, Burma's permanent representative to the UN, elected UN Secretary-General","51","both","In 1961 , U Thant , the Union of Burmas Permanent Representative to the United Nations and former secretary to the prime minister , was elected Secretary-General of the United Nations")],
drop=("(period end)",))
