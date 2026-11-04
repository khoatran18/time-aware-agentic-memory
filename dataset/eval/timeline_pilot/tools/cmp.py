import sys,json,re
base=sys.argv[1]
def words(s): return set(re.findall(r"\w+",s.lower()))
tot=dict(me=0,sub=0,match=0,track=0,badq=0,badc=0)
for name in sys.argv[2:]:
    txt=open(f"{base}/in/{name}.txt").read()
    ch={m.group(1):m.group(2) for m in re.finditer(r"=== CHUNK (\S+) ===\n(.*?)(?=\n=== CHUNK |\Z)",txt,re.S)}
    me=json.load(open(f"{base}/me/{name}.json")); sb=json.load(open(f"{base}/sub/{name}.json"))
    A=me["events"]; B=sb["events"]
    badq=badc=0
    for e in B:
        for ev in e.get("evidence",[]):
            if ev["chunk_id"] not in ch: badc+=1
            elif ev["quote"] not in ch[ev["chunk_id"]]: badq+=1
    def norm(d): return d
    pairs=[]
    for i,a in enumerate(A):
        ca={x["chunk_id"] for x in a["evidence"]}
        for j,b in enumerate(B):
            if a["date"]!=b["date"]: continue
            cb={x["chunk_id"] for x in b.get("evidence",[])}
            if not ca&cb: continue
            pairs.append((len(words(a["text"])&words(b["text"])),i,j))
    pairs.sort(reverse=True); ua=set();ub=set();m=[]
    for s,i,j in pairs:
        if i in ua or j in ub: continue
        ua.add(i);ub.add(j);m.append((i,j))
    tr=sum(A[i]["track"]==B[j]["track"] for i,j in m)
    print(f"\n## {name}: me={len(A)} sub={len(B)} matched={len(m)} recall_vs_me={len(m)/len(A):.2f} prec_vs_me={len(m)/len(B):.2f} track_agree={tr}/{len(m)} bad_chunk={badc} bad_quote={badq} undated me={len(me['undated_mentions'])} sub={len(sb.get('undated_mentions',[]))}")
    print(" only me:",[ (A[i]['date'],A[i]['text'][:40]) for i in range(len(A)) if i not in ua])
    print(" only sub:",[ (B[j]['date'],B[j]['text'][:40]) for j in range(len(B)) if j not in ub])
    for k,v in dict(me=len(A),sub=len(B),match=len(m),track=tr,badq=badq,badc=badc).items(): tot[k]+=v
print("\nTOTAL",tot)
