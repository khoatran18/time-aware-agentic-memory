"""Đo: đáp án chuẩn của bộ eval (từ bản TimeQA ~2021) còn xuất hiện trong trang Wikipedia hiện tại không,
tức tải lại cả trang (replace-all) có giữ được thông tin cũ hay không.
Hai cách lấy văn bản hiện tại: extracts (bỏ bảng, nên là cận dưới) và wikitext thô (còn cả ref/template, nên là cận trên).
Dùng: python scripts/measure_old_info_retention.py <thư_mục_cache>; cache ở <thư_mục_cache>/current_extracts.json và current_wikitext.json."""
import json, re, sys, time, unicodedata, pathlib, urllib.parse, urllib.request, collections

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = pathlib.Path(sys.argv[1]) / "current_extracts.json"
UA = "tam-thesis-research/0.1 (HUST student thesis; tranminhkhoa2k42k5@gmail.com)"
API = "https://en.wikipedia.org/w/api.php"

def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (i + 1))
    raise RuntimeError(url)

def norm(s):
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())

subset = json.load(open(ROOT / "dataset/eval/real_subset.json"))
titles = {p: urllib.parse.unquote(p.removeprefix("/wiki/")).replace("_", " ") for p in subset["page_ids"]}
cur = json.load(open(CACHE)) if CACHE.exists() else {}
need = [p for p in titles if p not in cur]
for i in range(0, len(need), 1):  # extracts đầy đủ chỉ trả 1 trang mỗi request
    b = need[i:i + 1]
    r = get({"action": "query", "prop": "extracts", "explaintext": 1, "exlimit": 1, "redirects": 1,
             "titles": "|".join(titles[p] for p in b), "format": "json", "formatversion": 2})
    norm_t = {x["from"]: x["to"] for x in r["query"].get("normalized", [])}
    red = {x["from"]: x["to"] for x in r["query"].get("redirects", [])}
    by_title = {p["title"]: p.get("extract", "") for p in r["query"]["pages"]}
    for p in b:
        t = titles[p]; t = norm_t.get(t, t); t = red.get(t, t)
        cur[p] = by_title.get(t, "")
    time.sleep(0.15)
json.dump(cur, open(CACHE, "w"), ensure_ascii=False)

WCACHE = pathlib.Path(sys.argv[1]) / "current_wikitext.json"
wcur = json.load(open(WCACHE)) if WCACHE.exists() else {}
need = [p for p in titles if p not in wcur]
for i in range(0, len(need), 20):
    b = need[i:i + 20]
    r = get({"action": "query", "prop": "revisions", "rvslots": "main", "rvprop": "content", "redirects": 1,
             "titles": "|".join(titles[p] for p in b), "format": "json", "formatversion": 2})
    norm_t = {x["from"]: x["to"] for x in r["query"].get("normalized", [])}
    red = {x["from"]: x["to"] for x in r["query"].get("redirects", [])}
    by_title = {p["title"]: (p.get("revisions") or [{}])[0].get("slots", {}).get("main", {}).get("content", "") for p in r["query"]["pages"]}
    for p in b:
        t = titles[p]; t = norm_t.get(t, t); t = red.get(t, t)
        wcur[p] = by_title.get(t, "")
    time.sleep(0.3)
json.dump(wcur, open(WCACHE, "w"), ensure_ascii=False)

old = {}
for line in open(ROOT / "dataset/full_dataset/pages.jsonl"):
    pg = json.loads(line)
    if pg["page_id"] in titles:
        old[pg["page_id"]] = " ".join(x["text"] for x in pg["paragraphs"])

def year(s):
    m = re.search(r"\b(1\d{3}|20\d{2})\b", s or ""); return int(m.group(1)) if m else None

rows = []
for c in subset["cases"]:
    tg = [norm(t) for t in c["targets"] if norm(t)]
    po, pc, pw = norm(old[c["page_id"]]), norm(cur[c["page_id"]]), norm(wcur[c["page_id"]])
    if not tg or not pc: continue
    in_old = any(t in po for t in tg); in_ext = any(t in pc for t in tg); in_cur = in_ext or any(t in pw for t in tg)
    ye = year(c.get("time_end")) or year(c.get("time_start"))
    rows.append(dict(idx=c["idx"], rel=c["relation"], domain=c["domain"], in_old=in_old, in_ext=in_ext, in_cur=in_cur,
                     recent=bool(ye and ye >= 2019), targets=c["targets"], ts=c.get("time_start"), te=c.get("time_end")))

def rep(name, rs):
    rs = [r for r in rs if r["in_old"]]
    print(f"{name}: n={len(rs)} còn trong trang hiện tại: extracts (cận dưới) = {sum(r['in_ext'] for r in rs)/len(rs):.3f}, wikitext (cận trên) = {sum(r['in_cur'] for r in rs)/len(rs):.3f}" if rs else f"{name}: n=0")
print("tổng số câu:", len(rows), "| đáp án khớp trong bản 2021:", sum(r["in_old"] for r in rows))
rep("tất cả", rows)
rep("mốc hỏi < 2019 (lịch sử xa)", [r for r in rows if not r["recent"]])
rep("mốc hỏi >= 2019 (gần/đang diễn ra)", [r for r in rows if r["recent"]])
print("-- theo domain")
for d in sorted({r["domain"] for r in rows}): rep(d, [r for r in rows if r["domain"] == d])
lost = [r for r in rows if r["in_old"] and not r["in_cur"]]
print("-- mẫu đáp án không còn trong trang hiện tại:")
import random; random.seed(3)
for r in random.sample(lost, min(15, len(lost))): print(r["idx"], r["targets"], r["ts"], "->", r["te"])
json.dump(rows, open(pathlib.Path(sys.argv[1]) / "retention_rows.json", "w"), ensure_ascii=False)
