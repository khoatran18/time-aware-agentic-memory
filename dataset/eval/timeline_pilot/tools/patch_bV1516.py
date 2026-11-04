# Vá V15, V16 (session chính đọc kiểm). Chạy: python3 -I tools/patch_bV1516.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os
for b in ("batchV15","batchV16"):
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
A("batchV15","British_Rail_Class_15",[
("1971-10-04","other","station pilot","Last Class 15 used as Liverpool Street station pilot (8234) replaced by a Class 08","13","both","the last locomotive used being 8234 which was replaced by a Class 08 on 4 October 1971"),
("1986","location","D8233","Preserved D8233 moved from the South Yorkshire Railway to the East Lancashire Railway","23","both","moving in 1986 to the East Lancashire Railway"),
("1988","location","D8233","Preserved D8233 moved to the Mangapps Farm Railway","23","both","and in 1988 to the Mangapps Farm Railway"),
("2006-02","location","D8233","Preserved D8233 returned to the East Lancashire Railway for restoration to working order","24","both","the locomotive returned to the East Lancashire Railway in February 2006"),
])
A("batchV16","DSB_class_D",[
("1970","other","withdrawal","DSB abandoned steam; only D 825 and D 826 were still serviceable","1","both","Only two class D engines were serviceable when DSB abandoned steam in 1970"),
])
A("batchV16","Conrad_Theodor_van_Deventer",[
("1899","work","article","Wrote the influential article Een Ereschuld (a debt of honour) in De Gids","11","both","In 1899 Van Deventer wrote a very influential article , called Een Ereschuld ( a debt of honour ) in the Dutch magazine De Gids"),
])
A("batchV16","Villa_del_Balbianello",[
("1820","other","arrest","Silvio Pellico was arrested at the villa by the Austrian government","2","both","In 1820 , Pellico was arrested at the villa by the Austrian government"),
("2018-11","other","wedding","Wedding of Ranveer Singh and Deepika Padukone took place at the villa","9","both","In November 2018 Indian movie star and Bollywoods famous couple Ranveer Singh and Deepika Padukones wedding took place at the villa"),
])
