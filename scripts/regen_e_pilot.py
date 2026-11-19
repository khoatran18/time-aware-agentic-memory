"""Thử sinh lại E (siết): câu bản cũ phải NÊU RÕ còn tiếp diễn, và năm kết thúc không còn ở bất kỳ đâu trong chunk (kiểm mức chunk).
Thử trên N chỗ E của tập đã có; KHÔNG ghi đè edits.jsonl, kết quả ra <tập>/e2_pilot.jsonl + e2_pilot.metrics.json.
Chạy: python scripts/regen_e_pilot.py --split tune --n 20 --workers 20
LLM: hy4-flash-free (thinking BẬT), cache riêng data/llm_cache/pastgen_e2_<model>/. Prompt tiếng Anh.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from argparse import Namespace
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import make_past as mp  # noqa: E402

ONGOING = re.compile(r"\b(is|are|has|have|remains?|remained|continues?|continued|currently|still|since|present|today|to date|ongoing|serving|serves|holds?|works?|lives?)\b", re.I)
MONTH = r"(January|February|March|April|May|June|July|August|September|October|November|December)"

E2 = ("Rewrite the TARGET sentence so that it clearly states the situation is STILL ONGOING at the time of writing (as if the passage were "
      "written before the situation ended). Remove the end date and any mention of a successor, departure or ending; keep the start. "
      "Use present or present-perfect wording (e.g. 'is', 'has ... since <start>', 'remains', 'continues to', 'currently'). Also drop clauses that "
      "only make sense after the end ('in protest', 'after N years', 'returning to ...'). Do NOT add any new year, number or name; keep every "
      "other year and name exactly. Change nothing else.")


def chunk_has_end(body: str, ev: dict) -> bool:
    d = ev["date"]
    ye = d[:4]
    mon = re.search(MONTH, ev.get("text") or "")
    if len(d) > 4 and mon:
        return bool(re.search(rf"{mon.group(1)}\s+(?:\d{{1,2}},?\s+)?{ye}|{ye}[^.]{{0,12}}{mon.group(1)}", body))
    return ye in mp.YEAR.findall(body)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="tune")
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--model", default="hy4-flash-free")
    a = ap.parse_args()
    d = mp.ORG / "past" / a.split
    rows = [json.loads(x) for x in (d / "edits.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    E = [r for r in rows if r["type"] == "E"]
    pc: dict = {}
    get = lambda p: pc.setdefault(p, mp.parse_chunks(mp.ORG / "source" / a.split / "chunks" / f"{p}.txt"))
    pick, skipped = [], 0
    for r in E:
        ch = next(c for c in get(r["page"]) if c["id"] == r["chunk_id"])
        rest = ch["body"].replace(r["sentence_real"], "", 1)
        if chunk_has_end(rest, r["event"]):
            skipped += 1   # năm kết thúc còn ở câu khác: pilot bỏ qua (xử lý riêng sau)
            continue
        pick.append((r, ch))
        if len(pick) >= a.n:
            break
    print("chọn", len(pick), "chỗ E | bỏ vì năm kết thúc còn ở câu khác (trong số đã duyệt):", skipped, flush=True)

    ns = Namespace(model=a.model, split=a.split, workers=a.workers)
    llm, chain, _, Out = mp.setup_llm(ns)
    from tam.llm.cache import SqliteCache
    from tam.llm.structured import invoke_structured
    cache = SqliteCache(ROOT / "data" / "llm_cache" / f"pastgen_e2_{a.model}" / "cache.sqlite", threadsafe=True)
    t0 = time.time()

    def work(j):
        r, ch = j
        marked = ch["body"].replace(r["sentence_real"], f"<<TARGET>> {r['sentence_real']} <</TARGET>>", 1)
        sys_p = ("You edit one sentence of a Wikipedia passage to build a synthetic OLDER version of the page. " + E2 +
                 " The text is tokenised: keep spaces around punctuation exactly like the input. Return only the rewritten TARGET sentence "
                 "(without the markers) in the `sentence` field; old_value/new_value null."
                 f" The end to remove: {r['event']['date'][:4]}.")
        res = invoke_structured(llm, chain, Out, [("system", sys_p), ("human", f"Section: {ch['head']}\n\nPassage:\n{marked}")], max_attempts=3, cache=cache)
        print("xong", r["edit_id"], "OK" if res else "FAIL", flush=True)
        return res

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(work, pick))
    out, st = [], Counter()
    for (r, ch), x in zip(pick, res):
        new = x.sentence.strip() if x else None
        c = dict(sentence=r["sentence_real"], event=r["event"], year=r["event"]["date"][:4])
        bad = ["llm_fail"] if new is None else mp.verify("E", c, dict(sentence_past=new, old_value=None, new_value=None))
        if new:
            chunk_past = ch["body"].replace(r["sentence_real"], new, 1)
            if chunk_has_end(chunk_past, r["event"]):
                bad.append("end_in_chunk")
            if not ONGOING.search(new):
                bad.append("no_ongoing_marker")
        out.append(dict(edit_id=r["edit_id"], page=r["page"], sentence_real=r["sentence_real"], sentence_past_old=r["sentence_past"], sentence_past_new=new, checks_failed=bad))
        st["tổng"] += 1
        st["đạt"] += not bad
        for b in bad:
            st[b] += 1
    p = d / "e2_pilot.jsonl"
    p.write_text("\n".join(json.dumps(o, ensure_ascii=False) for o in out) + "\n", encoding="utf-8")
    m = dict(run="e2_pilot", model=a.model, thinking="BẬT", workers=a.workers, cache_dir=f"data/llm_cache/pastgen_e2_{a.model}", calls=len(pick),
             cache_hits=cache.hits, cache_misses=cache.misses, wall_s=round(time.time() - t0, 1), stats=dict(st))
    p.with_suffix(".metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print("METRICS", json.dumps(m, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
