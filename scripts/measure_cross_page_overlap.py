"""Đo: sự kiện (chủ thể + đáp án) của mỗi câu trong real_subset có được trang khác trong pages.jsonl nhắc lại không.
Một trang khác 'nhắc lại' nếu chứa cả tên chủ thể và đáp án trong cửa sổ <= WINDOW ký tự (sau chuẩn hóa).
Dùng: python scripts/measure_cross_page_overlap.py [WINDOW]."""
import json, re, sys, unicodedata, pathlib, collections, random
ROOT = pathlib.Path(__file__).resolve().parents[1]
WINDOW = int(sys.argv[1]) if len(sys.argv) > 1 else 300
def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())
subset = json.load(open(ROOT / "dataset/eval/real_subset.json"))
eval_pages = set(subset["page_ids"])
texts = {}
for line in open(ROOT / "dataset/full_dataset/pages.jsonl"):
    p = json.loads(line); texts[p["page_id"]] = norm(" ".join(x["text"] for x in p["paragraphs"]))
print("tổng số trang trong dataset:", len(texts), "| trang trong bộ eval:", len(eval_pages))
def title(pid): return norm(pid.removeprefix("/wiki/").replace("_", " "))
def near(txt, a, b, w):
    i = txt.find(a)
    while i != -1:
        lo = max(0, i - w); hi = i + len(a) + w
        if b in txt[lo:hi]: return True
        i = txt.find(a, i + 1)
    return False
rows = []
for c in subset["cases"]:
    T = title(c["page_id"]); tg = [norm(t) for t in c["targets"] if len(norm(t)) >= 4]
    if len(T) < 4 or not tg: continue
    hits = []
    for pid, tx in texts.items():
        if pid == c["page_id"] or T not in tx: continue
        if any(near(tx, T, t, WINDOW) for t in tg): hits.append(pid)
    rows.append((c, hits))
n = len(rows); k = sum(1 for _, h in rows if h)
print(f"cửa sổ {WINDOW} ký tự: {k}/{n} câu ({k/n:.1%}) có ít nhất một trang khác nhắc lại cùng sự kiện")
print("số trang khác trung bình trong các câu đó:", round(sum(len(h) for _, h in rows if h) / max(1, k), 2))
inside = sum(1 for _, h in rows if any(p in eval_pages for p in h))
print(f"trong đó có trang nằm trong bộ eval (204 trang): {inside} câu")
by = collections.defaultdict(lambda: [0, 0])
for c, h in rows: by[c["relation"]][0] += 1; by[c["relation"]][1] += bool(h)
print("theo quan hệ (n, có nhắc lại):", sorted(((r, v[0], v[1]) for r, v in by.items()), key=lambda x: -x[1])[:8])
dom = collections.defaultdict(lambda: [0, 0])
for c, h in rows: dom[c["domain"]][0] += 1; dom[c["domain"]][1] += bool(h)
print("theo domain:", {d: f"{v[1]}/{v[0]}" for d, v in dom.items()})
random.seed(5)
for c, h in random.sample([x for x in rows if x[1]], min(10, k)):
    print(" -", c["page_id"], c["relation"], c["targets"][:1], "|", c["time_start"], "->", c["time_end"], "| nhắc lại ở:", h[:3])
json.dump([(c["idx"], h) for c, h in rows], open(ROOT / "local" / "wiki_revisions" / "cross_page_overlap.json", "w"))
