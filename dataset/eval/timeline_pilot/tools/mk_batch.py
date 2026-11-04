# usage: python3 -I tools/mk_batch.py <batch_dir_name> <seed> <reserved_json>   (chạy từ dataset/eval/timeline_pilot)
# Chọn 10 trang tune chưa dùng nằm trong reserved_json, dựng <batch>/{in,sub,rev}, chép GUIDE_v6.md.
import json,re,glob,random,ast,sys,os,shutil
name,seed,resv=sys.argv[1],int(sys.argv[2]),sys.argv[3]
root="../../.."  # repo root
used=set()
for f in glob.glob("*/in/*.txt"):
    used|=set(re.findall(r"=== CHUNK (/wiki/.*?)#\d+ ===",open(f).read()))
reserved=set(json.load(open(resv)))
rem=sorted(reserved-used)
pages={}
for l in open(f"{root}/dataset/full_dataset/pages.jsonl"):
    d=json.loads(l); pid=d.get("page_id") or d.get("id")
    if pid in rem: pages[pid]=d
def paras(d):
    p=d["paragraphs"]; return ast.literal_eval(p) if isinstance(p,str) else p
cnt={pid:sum(1 for x in paras(d) if x.get("text","").strip()) for pid,d in pages.items()}
random.seed(seed)
a=sorted(p for p,c in cnt.items() if 8<=c<=45); b=sorted(p for p,c in cnt.items() if 46<=c<=72); c=sorted(p for p,x in cnt.items() if x>=73)
other=sorted(p for p,x in cnt.items() if x<8)
sel=random.sample(b,min(2,len(b)))+random.sample(c,min(1,len(c)))
left=[p for p in a+b+c if p not in sel]
sel+=random.sample(a,min(10-len(sel),len(a)))
if len(sel)<10: sel+=random.sample([p for p in left if p not in sel],min(10-len(sel),len([p for p in left if p not in sel])))
if len(sel)<10: sel+=random.sample([p for p in other if p not in sel],min(10-len(sel),len([p for p in other if p not in sel])))  # trang <8 chunk chỉ lấy khi hết trang dài
print("còn trong reserved:",len(rem),"chọn:",len(sel))
if os.path.exists(name): sys.exit("thư mục đã tồn tại: "+name)
for sub in ("in","sub","rev"): os.makedirs(f"{name}/{sub}")
G="GUIDE_v7.md" if os.path.exists("GUIDE_v7.md") else "batch8/GUIDE_v6.md"
shutil.copy(G,f"{name}/"+os.path.basename(G).replace("batch8/",""))
for pid in sel:
    d=pages[pid]; fn=re.sub(r"[^A-Za-z0-9]+","_",pid.replace("/wiki/","")).strip("_")
    out=[]
    for i,x in enumerate(paras(d)):
        t=x.get("text","")
        if not t.strip(): continue
        h=d.get("title",fn)
        if x.get("title"): h+=" | "+x["title"]
        out.append(f"=== CHUNK {pid}#{i} ===\n{h}\n{t}")
    open(f"{name}/in/{fn}.txt","w").write("\n".join(out)+"\n")
    print(fn,cnt[pid])
