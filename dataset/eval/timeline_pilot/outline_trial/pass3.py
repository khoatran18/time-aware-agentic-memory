"""Lần gọi 3 (trích sự kiện theo mục), hai nhánh: A không dàn ý, B có dàn ý. Đo recall với timeline vàng.
Dùng: python pass3_test.py <repo> <timeline_pilot_dir> <outline_dir> <out_dir> <tên trang>..."""
import glob, json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, Field

repo, pilot, odir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, str(repo / "src"))
from tam.config.loader import load_config
from tam.llm.factory import get_llm
from tam.llm.structured import invoke_structured

PROMPT = """You extract dated events from ONE section of a Wikipedia page.

Page title: {title}
Section: {section}
{outline}
You receive the numbered chunks of this section. Return every event or state change of the page's subject that the text of THIS section dates. Each item:
- `date`: the date as the text gives it: `YYYY`, `YYYY-MM` or `YYYY-MM-DD`. Keep exactly the precision the text gives; never invent a month or day. null only if the event has no date at all in the text.
- `text`: one short sentence saying what happened.
- `chunk`: the number of the chunk that states it.

Rules:
- Use only the text you receive. Do NOT add dates or facts from your own knowledge.
- One item per event. If a chunk states several dated events, return each of them.
- Events of the subject only (births, jobs, moves, titles, results, marriages, deaths, foundings, renamings...). Skip dates of cited books or articles.
- Resolve "the following year", "that year" from the text you receive; if it cannot be resolved, use null.
"""

class Ev(BaseModel):
    date: str | None = None
    text: str
    chunk: int

class Evs(BaseModel):
    events: list[Ev] = Field(default_factory=list)

def parse(path):
    parts = re.split(r"^=== CHUNK (\S+) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    chunks = []
    for cid, body in zip(parts[1::2], parts[2::2]):
        head, _, text = body.partition("\n")
        chunks.append((cid, head.split(" | ", 1)[1].strip(), text.strip()))
    secs = []
    for i, (cid, t, x) in enumerate(chunks):
        if secs and secs[-1]["title"] == t: secs[-1]["chunks"].append((i, x))
        else: secs.append({"title": t, "chunks": [(i, x)]})
    return chunks, secs

def outline_text(o, k):
    lines = [f"Outline of the whole page (shared context): {o['subject']}"]
    if o["aliases"]: lines.append("Other names of the subject: " + "; ".join(o["aliases"]))
    lines.append("Sections: " + " | ".join(f"[{s['index']}] {s['title']}: {s['covers']}" for s in o["sections"]))
    return "\n".join(lines) + "\n"

cfg = load_config(); llm = get_llm(cfg, "google_31"); chain = llm.with_structured_output(Evs)

def call(args):
    page, arm, k, title, sec, o = args
    outl = outline_text(o, k) if arm == "B" else ""
    body = "\n\n".join(f"[{i}] {x}" for i, x in sec["chunks"])
    msgs = [("system", PROMPT.format(title=title, section=sec["title"], outline=outl)), ("human", body)]
    r = invoke_structured(llm, chain, Evs, msgs, max_attempts=3, cache=None)
    print(page, arm, "sec", k, "ok" if r else "FAIL", len(r.events) if r else None, flush=True)
    return page, arm, k, [e.model_dump() for e in r.events] if r else None

jobs, meta = [], {}
for name in sys.argv[5:]:
    p = next(Path(pilot).glob(f"batch*/in/{name}.txt")); chunks, secs = parse(p)
    o = json.loads((odir / f"{name}.json").read_text())["outline"]
    meta[name] = (chunks, secs)
    for arm in "AB":
        for k, s in enumerate(secs): jobs.append((name, arm, k, chunks[0][1], s, o))
with ThreadPoolExecutor(3) as ex: res = list(ex.map(call, jobs))
out.mkdir(parents=True, exist_ok=True)
by = {}
for page, arm, k, evs in res: by.setdefault((page, arm), {})[k] = evs
summary = {}
for name in sys.argv[5:]:
    chunks, secs = meta[name]
    gp = next(Path(pilot).glob(f"batch*/rev/{name}.json")); gold = json.loads(gp.read_text())["events"]
    for arm in "AB":
        got = [dict(e, section=k) for k, evs in by[(name, arm)].items() for e in (evs or [])]
        for e in got: e["cid"] = chunks[e["chunk"]][0] if 0 <= e["chunk"] < len(chunks) else None
        fails = sum(1 for evs in by[(name, arm)].values() if evs is None)
        def hit(g, strict):
            gcids = {ev["chunk_id"] for ev in g["evidence"]}
            for e in got:
                if not e["date"]: continue
                d_ok = e["date"] == g["date"] if strict else e["date"][:4] == g["date"].lstrip("-")[:4] or e["date"] == g["date"]
                if d_ok and e["cid"] in gcids: return True
            return False
        gs = [g for g in gold]; n = len(gs)
        r_strict = sum(hit(g, True) for g in gs); r_year = sum(hit(g, False) for g in gs)
        gkey = {(g["date"], ev["chunk_id"]) for g in gold for ev in g["evidence"]}
        pe = sum(1 for e in got if e["date"] and (e["date"], e["cid"]) in gkey)
        summary[f"{name}|{arm}"] = {"gold": n, "extracted": len(got), "undated_extracted": sum(1 for e in got if not e["date"]),
            "recall_exact_date": r_strict, "recall_year": r_year, "extracted_matching_gold": pe, "failed_sections": fails}
        (out / f"{name}_{arm}.json").write_text(json.dumps({"events": got, "summary": summary[f"{name}|{arm}"]}, ensure_ascii=False, indent=1), encoding="utf-8")
(out / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
print("DONE", flush=True)
