# Vá V13, V14 (session chính đọc kiểm). Chạy: python3 -I tools/patch_bV1314.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os
for b in ("batchV13","batchV14"):
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

AP="approximate_date"
A("batchV13","Engels_Saratov_Oblast",[
("2011-08-26","other","monument","Monument to the Russian-German victims of repression unveiled in the city","5","both","On August 26 , 2011 , a monument in honor of the Russian-German victims of repression within the Soviet Union was unveiled in the city"),
("2015-08","other","factory","First Locomotive Company's factory inaugurated at Engels with a prototype Bombardier Traxx locomotive unveiled","9","both","In August 2015 a prototype 1520 mm gauge Bombardier Traxx F120MS locomotive was unveiled at a ceremony to mark the inauguration of First Locomotive Companys factory at Engels"),
])
A("batchV13","Max_Weber_artist",[
("1915","work","painting","Painted Chinese Restaurant, the finest canvas of his Cubist phase (Whitney Museum)","0","both","He is best known today for Chinese Restaurant ( 1915 )"),
])
A("batchV13","Guy_Whittingham",[
("1987","affiliation","Waterlooville","Joined Waterlooville for the start of the 1987-88 season","2","both","he joined Waterlooville for the start of the 1987–88 season",AP),
])
A("batchV13","Florida_Gators_women_s_lacrosse",[
("2017-10","other","conference","The American announced a women's lacrosse league for the 2019 season, with Florida joining","6","both","October 2017 , The American announced that it would start a womens lacrosse league in the 2019 season , with Florida and Vanderbilt joining"),
])
A("batchV14","GER_Class_S69",[
("1928","other","modification","Lenz poppet valves fitted to the 1928 batch from new","4","both","The first substantive change was the fitting of Lenz poppet valves to the 1928 batch"),
])
