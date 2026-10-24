"""So ba cách nhận biết phần văn bản đã đổi giữa hai phiên bản trang (dữ liệu đã crawl bằng crawl_wiki_revisions + measure_chunk_stability):
A) hash chunk (chuẩn hóa) | B) hash câu (độc lập ranh giới chunk) | C) ghép mờ (Jaccard 3-gram từ) cho chunk còn câu mới.
Dùng: python scripts/measure_chunk_matching.py <thư_mục_crawl> <số_cặp> <số_trang_khoảng_dài>."""
import json, re, sys, random, hashlib, pathlib, statistics, unicodedata

D = pathlib.Path(sys.argv[1]); cache = json.load(open(D / "wikitext.json"))
BOT = re.compile(r"\bbot\b|\bAWB\b|WAWB|Bots/Requests", re.I)

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
    s = re.sub(r"'{2,}", "", s); return re.sub(r"<[^>]+>", "", s)
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
def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())
def sents(chunk): return [x for x in (norm(t) for t in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", chunk)) if x]
def shingles(c, k=3):
    w = norm(c).split(); return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}
def jac(a, b): return len(a & b) / len(a | b) if a | b else 0.0

def evaluate(pairs):
    R = dict(n=0, chunks=0, A=0, B=0, C_hi=0, C_mid=0, C_new=0, wordsB_changed=0, wordsB_total=0)
    per = []
    for ta, tb in pairs:
        ca, cb = chunk_para(ta), chunk_para(tb)
        if len(ca) < 5 or len(cb) < 5: continue
        hash_a = {norm(x) for x in ca}; sent_a = {s for x in ca for s in sents(x)}; sh_a = [shingles(x) for x in ca]
        a_need = b_need = 0
        for ch in cb:
            R["chunks"] += 1
            if norm(ch) in hash_a: continue
            a_need += 1
            ss = sents(ch); new = [s for s in ss if s not in sent_a]
            if not new: continue  # chỉ lệch ranh giới chunk
            b_need += 1
            R["wordsB_changed"] += sum(len(s.split()) for s in new); R["wordsB_total"] += sum(len(s.split()) for s in ss)
            sh = shingles(ch); best = max(jac(sh, x) for x in sh_a)
            R["C_hi" if best >= 0.8 else "C_mid" if best >= 0.5 else "C_new"] += 1
        R["n"] += 1; R["A"] += a_need; R["B"] += b_need
        per.append((len(cb), a_need, b_need))
    return R, per

def show(name, R, per):
    n = R["chunks"]
    print(f"== {name}: {R['n']} cặp, {n} chunk bản sau")
    print(f"A) hash chunk: phải xử lý {R['A']/n:.3f} chunk ({R['A']/R['n']:.2f}/cặp)")
    print(f"B) hash câu:   phải xử lý {R['B']/n:.3f} chunk ({R['B']/R['n']:.2f}/cặp); trong chunk đó chỉ {R['wordsB_changed']/max(1,R['wordsB_total']):.3f} số từ là câu mới")
    tot = R["C_hi"] + R["C_mid"] + R["C_new"]
    if tot: print(f"C) ghép mờ trên {tot} chunk có câu mới: sim>=0.8 (sửa nhỏ, ghép được) {R['C_hi']/tot:.3f} | 0.5-0.8 (sửa lớn) {R['C_mid']/tot:.3f} | <0.5 (đoạn mới) {R['C_new']/tot:.3f}")
    fx = [a / c for c, a, _ in per]; fy = [b / c for c, _, b in per]
    print(f"   theo cặp: tỉ lệ chunk phải xử lý, trung vị A={statistics.median(fx):.3f}, B={statistics.median(fy):.3f}; cặp có >50% chunk phải xử lý: A={sum(x>0.5 for x in fx)/len(fx):.2f}, B={sum(y>0.5 for y in fy)/len(fy):.2f}")

random.seed(7); pairs = []
for f in sorted((D / "revs").glob("*.json")):
    j = json.load(open(f)); revs = j["revs"]
    for k in range(1, len(revs)):
        r, p = revs[k], revs[k - 1]
        if r["parentid"] != p["revid"]: continue
        d = abs(r["size"] - p["size"]); c = r.get("comment", "") or ""
        if 20 <= d <= 3000 and not BOT.search(c) and "mw-reverted" not in r.get("tags", []) and not re.search(r"\brevert|undid|rv\b", c, re.I):
            pairs.append((j["page_id"], p["revid"], r["revid"], d))
random.shuffle(pairs); pairs = pairs[:int(sys.argv[2])]
show("một lần sửa nhỏ (revision liên tiếp)", *evaluate([(cache.get(str(a), ""), cache.get(str(b), "")) for _, a, b, _ in pairs]))
sel = []
for f in sorted((D / "revs").glob("*.json"))[:int(sys.argv[3])]:
    revs = json.load(open(f))["revs"]
    if len(revs) > 5: sel.append((cache.get(str(revs[0]["revid"]), ""), cache.get(str(revs[-1]["revid"]), "")))
show("bản 2021 so với bản mới nhất", *evaluate(sel))

# ---- Đo lại hash câu cho đúng: tách câu trên ĐOẠN đầy đủ (chưa cắt cửa sổ 100 từ), rồi đánh dấu cửa sổ nào chứa câu mới.
SPLIT = r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])"
def windows(text, cap=100):
    """Trả về [(chunk, {từ nằm trong câu mới} ...)] cần tập câu cũ; ở đây trả (chunk_text, danh_sách_id_câu_của_từng_từ)."""
    out = []
    for p in paras(text):
        toks, sid = [], []
        for si, s in enumerate(re.split(SPLIT, p)):
            w = s.split(); toks += w; sid += [(si, norm(s))] * len(w)
        for i in range(0, len(toks), cap): out.append((" ".join(toks[i:i + cap]), sid[i:i + cap]))
    return out
def evaluate2(pairs):
    R = dict(n=0, chunks=0, A=0, B=0, wn=0, wt=0); per = []
    for ta, tb in pairs:
        wa, wb = windows(ta), windows(tb)
        if len(wa) < 5 or len(wb) < 5: continue
        ha = {norm(c) for c, _ in wa}; sa = {n for _, sid in wa for _, n in sid if n}
        a_need = b_need = 0
        for c, sid in wb:
            R["chunks"] += 1
            if norm(c) not in ha: a_need += 1
            newtok = sum(1 for _, n in sid if n and n not in sa)
            if newtok: b_need += 1; R["wn"] += newtok; R["wt"] += len(sid)
        R["n"] += 1; R["A"] += a_need; R["B"] += b_need; per.append((len(wb), a_need, b_need))
    return R, per
def show2(name, R, per):
    n = R["chunks"]
    print(f"== (đo lại, tách câu trên đoạn đầy đủ) {name}: {R['n']} cặp, {n} chunk bản sau")
    print(f"A) hash chunk: {R['A']/n:.3f} | B) hash câu trên đoạn đầy đủ: {R['B']/n:.3f} | từ mới trong chunk phải xử lý (B): {R['wn']/max(1,R['wt']):.3f}")
show2("một lần sửa nhỏ", *evaluate2([(cache.get(str(a), ""), cache.get(str(b), "")) for _, a, b, _ in pairs]))
show2("bản 2021 so với nay", *evaluate2(sel))
