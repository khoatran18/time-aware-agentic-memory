"""Đo tỉ lệ chunk giữ nguyên hash sau chỉnh sửa (chunk theo đoạn và chunk cố định 100 từ). Dùng: python scripts/measure_chunk_stability.py <thư_mục_crawl> <số_cặp> <số_trang_khoảng_dài>."""
import json, re, sys, time, random, hashlib, pathlib, statistics, urllib.parse, urllib.request
SP = pathlib.Path(sys.argv[1]); D = SP / "revs"
UA = "tam-thesis-research/0.1 (HUST student thesis; tranminhkhoa2k42k5@gmail.com)"
API = "https://en.wikipedia.org/w/api.php"
BOT = re.compile(r"\bbot\b|\bAWB\b|WAWB|Bots/Requests", re.I)

def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError(url)

CACHE = SP / "wikitext.json"
cache = json.load(open(CACHE)) if CACHE.exists() else {}
def fetch(revids):
    need = [str(r) for r in revids if str(r) not in cache]
    for i in range(0, len(need), 20):
        b = need[i:i + 20]
        r = get({"action": "query", "prop": "revisions", "revids": "|".join(b), "rvslots": "main", "rvprop": "ids|content",
                 "format": "json", "formatversion": 2})
        for p in r["query"]["pages"]:
            for rv in p.get("revisions", []):
                cache[str(rv["revid"])] = rv["slots"]["main"].get("content", "")
        time.sleep(0.3)
    json.dump(cache, open(CACHE, "w"), ensure_ascii=False)

def strip_templates(s):
    prev = None
    while prev != s:
        prev = s; s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    return s
def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<ref[^>/]*/>", "", s); s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = strip_templates(s); s = re.sub(r"\{\|.*?\|\}", "", s, flags=re.S)
    s = re.sub(r"\[\[(?:File|Image|Category):[^\]]*\]\]", "", s, flags=re.I)
    s = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", s); s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"'{2,}", "", s); s = re.sub(r"<[^>]+>", "", s)
    return s

def paras(text):
    out = []
    for blk in re.split(r"\n\s*\n", clean(text)):
        blk = " ".join(blk.split())
        if not blk or re.fullmatch(r"=+[^=]*=+", blk) or blk.startswith(("*", "#", ":", ";")) and len(blk.split()) < 5: continue
        out.append(blk)
    return out
def chunk_para(text, cap=100):
    out = []
    for p in paras(text):
        w = p.split()
        for i in range(0, len(w), cap): out.append(" ".join(w[i:i + cap]))
    return out
def chunk_fixed(text, cap=100):
    w = " ".join(paras(text)).split()
    return [" ".join(w[i:i + cap]) for i in range(0, len(w), cap)]
H = lambda t: hashlib.md5(t.lower().encode()).hexdigest()
def stable(a, b):
    sa = {H(x) for x in a}; return sum(H(x) in sa for x in b) / len(b) if b else None

# --- chọn cặp sửa nhỏ liên tiếp (người, không phải bot, thay đổi nội dung vừa phải)
random.seed(7); pairs = []
for f in sorted(D.glob("*.json")):
    j = json.load(open(f)); revs = j["revs"]
    for k in range(1, len(revs)):
        r, p = revs[k], revs[k - 1]
        if r["parentid"] != p["revid"]: continue
        d = abs(r["size"] - p["size"]); c = r.get("comment", "") or ""
        if 20 <= d <= 3000 and not BOT.search(c) and "mw-reverted" not in r.get("tags", []) and not re.search(r"\brevert|undid|rv\b", c, re.I):
            pairs.append((j["page_id"], p["revid"], r["revid"], d))
random.shuffle(pairs); pairs = pairs[:int(sys.argv[2])]
fetch([x for _, a, b, _ in pairs for x in (a, b)])
res = {"para": [], "fixed": []}; chg = []
for pid, a, b, d in pairs:
    ta, tb = cache.get(str(a), ""), cache.get(str(b), "")
    pa, pb, fa, fb = chunk_para(ta), chunk_para(tb), chunk_fixed(ta), chunk_fixed(tb)
    if len(pa) < 5 or len(pb) < 5: continue
    res["para"].append(stable(pa, pb)); res["fixed"].append(stable(fa, fb))
    chg.append((len(pb), sum(H(x) not in {H(y) for y in pa} for x in pb), d))
def summ(name, xs):
    xs = [x for x in xs if x is not None]
    print(f"{name}: n={len(xs)} mean_unchanged={statistics.mean(xs):.3f} median={statistics.median(xs):.3f} "
          f">=0.9:{sum(x>=0.9 for x in xs)/len(xs):.2f} <0.5:{sum(x<0.5 for x in xs)/len(xs):.2f}")
print("== cặp sửa liên tiếp (1 lần sửa nhỏ)")
summ("chunk theo đoạn (như TimeQA)", res["para"]); summ("chunk cố định 100 từ", res["fixed"])
print("chunk đổi trung bình mỗi lần sửa (đoạn):", round(statistics.mean(c for _, c, _ in chg), 2), "/", round(statistics.mean(n for n, _, _ in chg), 1), "chunk")
# --- khoảng cách dài: bản đầu 2021 vs bản mới nhất
long = {"para": [], "fixed": []}; sel = []
for f in sorted(D.glob("*.json"))[:int(sys.argv[3])]:
    j = json.load(open(f)); revs = j["revs"]
    if len(revs) > 5: sel.append((revs[0]["revid"], revs[-1]["revid"]))
fetch([x for ab in sel for x in ab])
for a, b in sel:
    ta, tb = cache.get(str(a), ""), cache.get(str(b), "")
    pa, pb, fa, fb = chunk_para(ta), chunk_para(tb), chunk_fixed(ta), chunk_fixed(tb)
    if len(pa) < 5 or len(pb) < 5: continue
    long["para"].append(stable(pa, pb)); long["fixed"].append(stable(fa, fb))
print("== bản 2021 so với bản mới nhất")
summ("chunk theo đoạn", long["para"]); summ("chunk cố định 100 từ", long["fixed"])
