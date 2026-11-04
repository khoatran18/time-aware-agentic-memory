# Bổ sung sau khi session chính đọc kiểm B6/B7 (chạy SAU patch_bB6.py / patch_bB7.py)
import json
def ev(date,track,label,text,chunk,role,quote,flag=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if flag:e["flag"]=flag
    return e
def fin(base,n,d):
    seen=set();ev2=[]
    for e in d["events"]:
        k=(e["date"],e["text"])
        if k not in seen: seen.add(k);ev2.append(e)
    d["events"]=ev2
    d["events"]=sorted(d["events"],key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def L(b,n): return json.load(open(f"{b}/rev/{n}.json"))

b="batchB7";n="Central_European_University";d=L(b,n);c=pre(d)
d["events"]+=[
 ev("2017-03-28","other","legislation","Hungarian minister submitted a bill amending the higher education law, with rules aimed at foreign universities such as CEU",c+"15","both","On 28 March 2017 , Hungarian Minister of Human Resources Zoltán Balog , also responsible for education , submitted a bill to Parliament"),
 ev("2017-04-02","other","protest","Protest walk in support of CEU, thousands of participants",c+"33","both","On 2 April 2017 , a protest was held in the form of a walk from Budapests Corvinus University to Parliament"),
 ev("2020-10-06","other","court ruling","European Court of Justice ruled the Lex CEU incompatible with EU law",c+"5","both","On 6 October 2020 , the European Court of Justice ruled that the Lex CEU was incompatible with European Union law")]
fin(b,n,d)

b="batchB7";n="Exxon_Valdez";d=L(b,n);c=pre(d)
d["events"]+=[
 ev("1994","other","litigation","Jury awarded plaintiffs US$287 million compensatory and US$5 billion punitive damages",c+"7","both","In 1994 , a jury awarded plaintiffs US$287 million in compensatory damages and US$5 billion in punitive damages"),
 ev("2008-06","other","litigation","Supreme Court capped the punitive damages at US$507.5 million",c+"7","both","capped the damages to US$507.5 million in June , 2008"),
 ev("2008-08-27","other","litigation","Exxon Mobil agreed to pay 75% of the US$507.5 million damages ruling to settle",c+"7","both","On August 27 , 2008 , Exxon Mobil agreed to pay 75% of the US$507.5 million damages ruling"),
 ev("2009-06","other","litigation","Federal ruling ordered Exxon to pay an additional US$480 million in interest on delayed punitive damages",c+"8","both","In June 2009 , a federal ruling ordered Exxon to pay an additional US$480 million in interest")]
fin(b,n,d)

b="batchB7";n="Pelican_Faberg_egg";d=L(b,n);c=pre(d)
d["events"]=[e for e in d["events"] if not (e["date"] in("1936","1938") and "Pratt" in e["text"])]
d["events"]+=[ev("1936","ownership_structure","","Lillian Thomas Pratt purchased the egg from Hammer Galleries (between 1936 and 1938)",c+"7","both","Between 1936 and 1938 it was purchased by Lillian Thomas Pratt",flag="approximate_date")]
fin(b,n,d)

b="batchB7";n="Mannheim_Observatory";d=L(b,n);c=pre(d)
d["events"]+=[ev("1863-08-28","other","founding","Astronomische Gesellschaft founded at a meeting in Heidelberg organised by Schönfeld; he was on the founding board",c+"16","both","At one such a meeting , 28 August 1863 in Heidelberg , the Astronomische")]
fin(b,n,d)

# Áp quy ước (I): khôi phục mốc mất tên của U-96 không trùng mốc đã có (e49, e70 trong sub/)
b="batchB6";n="German_submarine_U_96_1940";d=L(b,n)
sub=json.load(open(f"{b}/sub/{n}.json"))
for e in sub["events"]:
    if e["id"] in("e49","e70"): d["events"].append(e)
fin(b,n,d)

# Áp quy ước (J): bỏ các mốc "revised" riêng của Panufnik (giữ "revised năm X" trong text của mốc "composed")
import re
b="batchB7";n="Andrzej_Panufnik";d=L(b,n)
d["events"]=[e for e in d["events"] if not (re.search(r"\brevised\b",e["text"],re.I) and "composed" not in e["text"].lower())]
fin(b,n,d)
