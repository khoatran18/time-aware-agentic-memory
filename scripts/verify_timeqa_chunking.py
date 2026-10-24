"""Kiểm chứng TimeQA chia chunk nội bộ trong đoạn: ghép chunk thành nhóm (nhóm = đoạn nếu quy tắc cắt 100 từ đúng),
rồi so với đoạn thật của bản Wikipedia đầu 2021 (đã crawl): nhóm khớp 1 đoạn, khớp 2 đoạn liền kề gộp lại, hay không khớp.
Dùng: python scripts/verify_timeqa_chunking.py <thư_mục_crawl> <số_trang>."""
import json, re, sys, pathlib, collections, unicodedata
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = pathlib.Path(sys.argv[1])
cache = json.load(open(D / "wikitext.json"))
def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())
def strip_t(s):
    prev = None
    while prev != s: prev = s; s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    return s
def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S); s = re.sub(r"<ref[^>/]*/>", "", s); s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = strip_t(s); s = re.sub(r"\{\|.*?\|\}", "", s, flags=re.S); s = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", s, flags=re.I)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s); s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s); s = re.sub(r"'{2,}", "", s); return re.sub(r"<[^>]+>", "", s)
def wiki_paras(t):
    out = []
    for blk in re.split(r"\n\s*\n|\n(?=[*#:;=])", clean(t)):
        blk = " ".join(blk.split())
        if len(blk.split()) >= 8 and not re.fullmatch(r"=+[^=]*=+", blk): out.append(norm(blk))
    return out
def sh(s, k=3):
    w = s.split(); return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}
def jac(a, b): return len(a & b) / len(a | b) if a | b else 0
pages = {}
for line in open(ROOT / "dataset/full_dataset/pages.jsonl"):
    p = json.loads(line); pages[p["page_id"]] = p["paragraphs"]
files = sorted((D / "revs").glob("*.json"))[:int(sys.argv[2])]
R = collections.Counter(); ex = []
for f in files:
    j = json.load(open(f))
    if len(j["revs"]) < 2 or j["page_id"] not in pages: continue
    wp = wiki_paras(cache.get(str(j["revs"][0]["revid"]), ""))
    if len(wp) < 5: continue
    wsh = [sh(x) for x in wp]
    ps = pages[j["page_id"]]; groups = []
    for k, x in enumerate(ps):
        prev = ps[k - 1] if k else None
        cont = prev and prev["title"] == x["title"] and len(prev["text"].split()) == 100 and not re.search(r"[.!?][\"')\]]*$", prev["text"].strip())
        if cont: groups[-1].append(x["text"])
        else: groups.append([x["text"]])
    for g in groups:
        gn = norm(" ".join(g))
        if len(gn.split()) < 12: continue
        gs = sh(gn); best = max((jac(gs, w) for w in wsh), default=0)
        best2 = max((jac(gs, wsh[i] | wsh[i + 1]) for i in range(len(wsh) - 1)), default=0)
        if best >= 0.8: R["khớp đúng 1 đoạn Wikipedia"] += 1
        elif best2 >= 0.8: R["khớp 2 đoạn Wikipedia gộp lại"] += 1; ex.append((j["page_id"], gn[:80]))
        else: R["không khớp (khác phiên bản/làm sạch)"] += 1
tot = sum(R.values()); print("nhóm chunk đã xét:", tot)
for k, v in R.items(): print(f"  {k}: {v} ({v/tot:.1%})")
for e in ex[:4]: print("  ví dụ gộp 2 đoạn:", e)
