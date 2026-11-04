# Bổ sung sau khi session chính đọc kiểm V11, V12 (chạy SAU patch_bV11.py và patch_bV12.py). Idempotent nhờ fin.
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
D="derived_date";AP="approximate_date";D="derived_date"
A("batchV11","Edward_Adolf_Sonnenschein",[
("1883","work","Plautus","Published Bentley's Plautine emendations from his copy of Gronovius (first of 6 editions, 1883-1963)","11","both","Bentleys Plautine emendations from his copy of Gronovius by Richard Bentley , 6 editions between 1883 and 1963"),
("1898","work","grammar","Published A Greek Grammar for Schools (first of 18 editions, 1898-1929)","12","both","A Greek Grammar for Schools ; based on the principles and requirements of the Grammatical Society , 18 editions between 1898 and 1929"),
("1902","work","Latin","Published Ora Maritima, a Latin story for beginners (first of 10 editions, 1902-1927)","12","both","Ora Maritima ; a Latin story for beginners , 10 editions between 1902 and 1927"),
("1912","work","grammar","Published A New Latin Grammar based on the Joint Committee recommendations (first of 11 editions, 1912-1925)","12","both","A New Latin Grammar : based on the recommendations of the Joint Committee on Grammatical Terminology , 11 editions between 1912 and 1925"),
("1912","work","Classical Association","Published Recommendations of the Classical Association on the teaching of Latin and Greek","13","both","Recommendations of the Classical Association on the teaching of Latin and Greek , 2 editions in 1912"),
("1914","work","German","Published Through German Eyes (first of 11 editions, 1914-1915)","10","both","Through German Eyes , 11 editions between 1914 and 1915"),
("1916","work","grammar","Published A new English Grammar based on the Joint Committee recommendations (first of 17 editions, 1916-1962)","10","both","A new English Grammar based on the recommendations of the Joint Committee on Grammatical Terminology , 17 editions between 1916 and 1962"),
("1924","work","Latin","Published The Gateway, a book of Latin composition for middle forms","14","both","The Gateway ; a book of Latin composition for middle forms , 4 editions in 1924"),
("1925","work","essay","Published the essay What is Rhythm?","14","both","What is Rhythm ? An essay , 2 editions in 1925"),
])
A("batchV12","Atl_tico_Madrid",drop=("Former home Vicente Calderón demolished",),items=[
("2000","other","Copa del Rey","Reached the Copa del Rey final but was relegated","39","both","Despite reaching the Copa del Rey final in 2000 , Atlético were relegated"),
("2014-05-24","other","Champions League","Lost the Champions League final 4-1 to Real Madrid after extra time (first CL final since 1974)","56","date","On 17 May 2014 , a 1–1 draw at the Camp Nou against Barcelona secured the La Liga title for Atlético",D,[("57","description","Real ultimately won 4–1")]),
("2015","other","Champions League","Lost on penalties to Real Madrid in the 2015-16 Champions League final","57","both","Atlético reached a second Champions League final in three seasons in 2015–16 , again facing Real Madrid , and lost on penalties after a 1–1 draw",AP),
])
