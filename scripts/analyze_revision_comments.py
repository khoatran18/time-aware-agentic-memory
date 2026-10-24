"""Đếm comment chỉnh sửa theo nhóm revert / fix nhiễu / fix ứng viên. Dùng: python scripts/analyze_revision_comments.py <thư_mục_crawl>."""
import json, re, sys, pathlib, collections, random
D = pathlib.Path(sys.argv[1]) / "revs"
files = sorted(D.glob("*.json"))
FIX = re.compile(r"\b(fix(ed|es|ing)?|correct(ed|s|ion|ing)?|incorrect|wrong|error|mistake|inaccura\w+|actually|erroneous|not \w+ but)\b", re.I)
NOISE = re.compile(r"\b(typo|spelling|grammar|bot|cleanup|clean up|format\w*|citation|ref(erence)?s?|link|template|infobox param|deprecated|wikidata|dab|disambig|lint|category|categories|image|caption|whitespace|punctuation|wording)\b", re.I)
VAND = re.compile(r"\b(revert\w*|rv|rvv|undid|undo|vandal\w*|reverted)\b", re.I)
tot = collections.Counter(); pages_with = collections.Counter(); cands = []
for f in files:
    j = json.load(open(f)); revs = j["revs"]
    tot["pages"] += 1; tot["revs"] += len(revs)
    hit = set()
    for r in revs:
        c = r.get("comment", "") or ""
        tags = r.get("tags", [])
        if VAND.search(c) or any("revert" in t or "undo" in t for t in tags):
            tot["revert"] += 1; hit.add("revert"); continue
        if FIX.search(c):
            if NOISE.search(c): tot["fix_noise"] += 1
            else:
                tot["fix_candidate"] += 1; hit.add("cand"); cands.append((j["page_id"], r["revid"], r["parentid"], r["timestamp"][:10], c[:140]))
    for h in hit: pages_with[h] += 1
print(dict(tot)); print("pages with:", dict(pages_with))
random.seed(1); json.dump(cands, open(pathlib.Path(sys.argv[1]) / "cands.json", "w"), ensure_ascii=False)
for c in random.sample(cands, min(40, len(cands))): print(c)
