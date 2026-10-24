"""Crawl lịch sử chỉnh sửa Wikipedia (từ 2021) của các trang trong real_subset. Dùng: python scripts/crawl_wiki_revisions.py <thư_mục_ra>; kết quả: <thư_mục_ra>/revs/*.json."""
import json, sys, time, urllib.parse, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(sys.argv[1]) / "revs"
UA = "tam-thesis-research/0.1 (HUST student thesis; tranminhkhoa2k42k5@gmail.com)"
API = "https://en.wikipedia.org/w/api.php"

def get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=30) as r:
                return json.load(r)
        except Exception as e:
            time.sleep(2 * (i + 1))
    raise RuntimeError(url)

pids = json.load(open(ROOT / "dataset/eval/real_subset.json"))["page_ids"]
for pid in pids:
    title = urllib.parse.unquote(pid.removeprefix("/wiki/")).replace("_", " ")
    f = OUT / (urllib.parse.quote(pid, safe="") + ".json")
    if f.exists():
        continue
    revs, cont = [], {}
    while True:
        r = get({"action": "query", "prop": "revisions", "titles": title, "rvlimit": 500, "rvdir": "newer",
                 "rvstart": "2021-01-01T00:00:00Z", "rvprop": "ids|timestamp|comment|tags|size|user", "format": "json",
                 "formatversion": 2, **cont})
        pg = r["query"]["pages"][0]
        revs += pg.get("revisions", [])
        if "continue" not in r:
            break
        cont = r["continue"]
    json.dump({"page_id": pid, "title": title, "revs": revs}, open(f, "w"), ensure_ascii=False)
    print(pid, len(revs), flush=True)
    time.sleep(0.2)
