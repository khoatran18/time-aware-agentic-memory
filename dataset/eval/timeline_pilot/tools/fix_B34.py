# Bổ sung sau khi session chính đọc kiểm B3/B4: các mốc sót ở Counselor_to_the_President và Line_7_Beijing_Subway
import json
def ev(date,track,label,text,chunk,role,quote,flag=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date)],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if flag:e["flag"]=flag
    return e
def fin(base,n,d):
    d["events"]=sorted(d["events"],key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{base}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"

b="batchB4";n="Counselor_to_the_President";d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
d["events"]+=[
 ev("2016","role","","President-elect Trump announced intention to name Kellyanne Conway to the position and Steve Bannon senior counselor",c+"8","both","Soon after the 2016 election , President-elect Donald Trump announced his intention to name his campaign manager during the general election , Kellyanne Conway , to the position",flag="derived_date"),
 ev("2017-01","role","","Bannon named to the Principals Committee of the National Security Council by executive order",c+"8","both","Bannon was named to the Principals Committee of the National Security Council in a January 2017 executive order"),
 ev("2017-04","role","","Trump removed Bannon from the National Security Council after public opposition",c+"9","both","Trump removed Bannon from the council in April 2017")]
fin(b,n,d)

b="batchB4";n="Line_7_Beijing_Subway";d=json.load(open(f"{b}/rev/{n}.json"));c=pre(d)
d["events"]+=[
 ev("2008-01-08","work","","Plans for Line 7 reported in the media; construction scheduled to begin by end of year",c+"7","both","January 8 , 2008 : Plans for Line 7 reported in the media"),
 ev("2009-07-19","work","","Construction on Line 7 announced to begin in late August 2009",c+"7","both","July 19 , 2009 : Construction on Line 7 announced to begin in late August 2009")]
fin(b,n,d)
