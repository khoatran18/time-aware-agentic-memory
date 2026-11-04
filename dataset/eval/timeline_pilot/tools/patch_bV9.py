# Vá V9 (cloud đọc kiểm). Chạy từ dataset/eval/timeline_pilot: python3 -I tools/patch_bV9.py. Ghi đè rev/ từ sub/.
import json,glob,shutil,os
B="batchV9"
os.makedirs(f"{B}/rev",exist_ok=True)
for f in glob.glob(f"{B}/sub/*.json"): shutil.copy(f,f"{B}/rev/"+os.path.basename(f))
def ev(date,track,label,text,chunk,role,quote,flag=None,more=None):
    e={"date":date,"grain":{4:"year",7:"month",10:"day"}[len(date.lstrip("-"))],"track":track,"label":label,"text":text,
       "evidence":[{"chunk_id":chunk,"role":role,"quote":quote}]}
    if more: e["evidence"]+=[{"chunk_id":chunk.split("#")[0]+"#"+m[0],"role":m[1],"quote":m[2]} for m in more]
    if flag:e["flag"]=flag
    return e
def fin(n,d):
    seen=set();ev2=[]
    for e in d["events"]:
        k=(e["date"],e["text"])
        if k not in seen: seen.add(k);ev2.append(e)
    d["events"]=sorted(ev2,key=lambda e:(e["date"][:4],0 if len(e["date"])==4 else 1,e["date"]))
    for i,e in enumerate(d["events"],1): e["id"]=f"e{i}"
    json.dump(d,open(f"{B}/rev/{n}.json","w"),indent=1,ensure_ascii=False)
def load(n): return json.load(open(f"{B}/rev/{n}.json"))
def pre(d): return d["events"][0]["evidence"][0]["chunk_id"].split("#")[0]+"#"
def get(d,i): return next(e for e in d["events"] if e["id"]==i)
def A(n,items,d=None):
    d=d or load(n);c=pre(d)
    for it in items:
        date,track,label,text,ch,role,q=it[:7]
        d["events"].append(ev(date,track,label,text,c+ch,role,q,it[7] if len(it)>7 else None,it[8] if len(it)>8 else None))
    fin(n,d)
D="derived_date";AP="approximate_date"

# Florence: e30 chỉ có chunk 'date' -> cần 'both'; thêm mốc công trình/cơ quan có năm rõ.
n="Florence";d=load(n)
get(d,"e30")["evidence"][0]["role"]="both"
A(n,[
("1013","work",None,"Construction began on the Basilica di San Miniato al Monte","13","both","In 1013 , construction began on the Basilica di San Miniato al Monte"),
("1059","work",None,"Exterior of San Miniato al Monte reworked in Romanesque style (1059 to 1128)","13","both","The exterior of the church was reworked in Romanesque style between 1059 and 1128",AP),
("1296","work",None,"Construction of the Cathedral of Santa Maria del Fiore begun in Gothic style to a design of Arnolfo di Cambio","71","both","It was begun in 1296 in the Gothic style to a design of Arnolfo di Cambio"),
("1436","work",None,"Cathedral structurally completed, with the dome designed by Brunelleschi","71","both","was structurally completed by 1436 , with the dome designed by Filippo Brunelleschi",AP),
("1445","work",None,"Palazzo Medici Riccardi built for Cosimo il Vecchio (1445 to 1460)","57","both","was built between 1445 and 1460",AP),
("1563","work",None,"Ammannati's Fountain of Neptune built in Piazza della Signoria (1563 to 1565)","44","both","Fountain of Neptune ( 1563–1565 )"),
("1861","location",None,"Tuscany, including Florence, became a region of the Kingdom of Italy","27","both","Tuscany became a region of the Kingdom of Italy in 1861"),
("1862-05-17","work",None,"Politeama Fiorentino Vittorio Emanuele open-air theatre inaugurated","70","both","which was inaugurated on 17 May 1862 with a production of Donizettis Lucia di Lammermoor"),
("1920","work",None,"Cinema Teatro Savoia (later Odeon) established in a wing of the Palazzo dello Strozzino (1920 to 1922)","69","both","Established from 1920 to 1922 in a wing of the Palazzo dello Strozzino",AP)],d)

# Ty_Detmer: chấn thương 2000 (năm nêu rõ) ra khỏi undated.
n="Ty_Detmer";d=load(n)
d["undated_mentions"]=[u for u in d["undated_mentions"] if "Achilles" not in u]
A(n,[("2000","other","injury","Injured right Achilles and was inactive the entire season","19","both","Detmer injured his right Achilles and was inactive the entire 2000 season")],d)

# HJK: năm viết tắt ("1960–71") = derived_date; thêm chuyển nhượng mùa đông 2015.
n="Helsingin_Jalkapalloklubi";d=load(n)
for i in ("e54","e64","e65","e72","e83"): get(d,i)["flag"]=D
A(n,[("2015","affiliation",None,"Signed Mike Havenaar, Atomu Tanaka and Guy Moussi in the winter transfer window","18","both","HJK made several acquisitions during the winter of 2015 , including Córdoba forward Mike Havenaar",AP)],d)

# Không đổi: chỉ đánh số lại
for n in ["James_Parmentier","ACES_Colombia","Matthias_Platzeck","Carrier_Air_Wing_Seven","S_rgio_Concei_o","Anna_Karina","KF_Sk_nderbeu_Kor"]: fin(n,load(n))
