"""Lần trích sự kiện theo mục, bản 2: có end (3 trạng thái), thập niên -> period, kiểm ngày bằng mã. Không dàn ý.
Dùng: python pass3_v2.py <repo> <timeline_pilot_dir> <out_dir> <tên trang>..."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field

repo, pilot, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(repo / "src"))
from tam.config.loader import load_config
from tam.llm.factory import get_llm
from tam.llm.structured import invoke_structured
from tam.ingestion.time_extraction import ongoing_evidence_ok, _norm

PROMPT = """You extract dated events from ONE section of a Wikipedia page.

Page title: {title}
Section: {section}

You receive the numbered chunks of this section. Return the events of the page's subject that this section dates. For each event:
- `text`: one short sentence saying what happened.
- `chunk`: the number of the chunk that states it.
- `date`: when it STARTED or happened, as `YYYY`, `YYYY-MM` or `YYYY-MM-DD`, with exactly the precision the text gives (never invent a month or a day). Use null when the text gives no usable year, or only a decade or century ("the 1970s", "mid-1990s", "19th century").
- `approximate`: true when the text is vague about the date: "early/mid/late 2017", "spring of 1910", "circa 1920", "by 1928", "after 1916", "Q4 2017", a season "1999-2000" (then `date` is the year, e.g. 2017, 1999). Otherwise false.
- `period`: only when `date` is null because of a decade or century: copy the phrase as written ("the 1970s", "mid-1990s"). Otherwise null.
- `end`: when the situation STOPPED, same format, ONLY if the text says so ("until 2007", "left in 2007", "from 2001 to 2004"). For a one-moment event (birth, award, a match, a signing), `end` equals `date`. Otherwise null.
- `end_status`: "known" if `end` is set; "ongoing" ONLY if the text itself says the situation continues ("since 2010", "is still", "currently", "incumbent"); "unknown" otherwise. A missing end is NOT evidence that it continues. Never use the date of the next event as `end`.
- `ongoing_evidence`: only when `end_status` is "ongoing": the exact words copied from the text that show it continues. Otherwise empty.

Rules:
- Use only the text you receive. Do NOT add dates or facts from your own knowledge.
- A range "2012-2013" for one situation: `date` 2012, `end` 2013. Never put a range or a "Q" or an "s" inside `date` or `end`.
- Never turn a decade into a single year ("the 1970s" is NOT 1970).
- Events of the subject itself. Also events of other people or things that directly happen to the subject. Skip the biography of other people merely mentioned, appearances of the subject in films, books or advertising, and dates of cited works or of names that contain a year ("2017 Calendar").
- One item per event. If a chunk states several dated events, return each.
- Resolve "the following year" or "that year" from the text you receive; if it cannot be resolved use null.
"""

class Ev(BaseModel):
    text: str
    chunk: int
    date: str | None = None
    approximate: bool = False
    period: str | None = None
    end: str | None = None
    end_status: Literal["known", "ongoing", "unknown"] = "unknown"
    ongoing_evidence: str = ""

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

FMT = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
def year_token(y, text): return re.search(rf"(?<![\d]){y}(?![\d]|s)", text) is not None

cfg = load_config(); llm = get_llm(cfg, "google_31"); chain = llm.with_structured_output(Evs)

def call(args):
    page, k, title, sec = args
    body = "\n\n".join(f"[{i}] {x}" for i, x in sec["chunks"])
    msgs = [("system", PROMPT.format(title=title, section=sec["title"])), ("human", body)]
    r = invoke_structured(llm, chain, Evs, msgs, max_attempts=3, cache=None)
    print(page, "sec", k, "ok" if r else "FAIL", len(r.events) if r else None, flush=True)
    return page, k, [e.model_dump() for e in r.events] if r else None

jobs, meta = [], {}
for name in sys.argv[4:]:
    p = next(Path(pilot).glob(f"batch*/in/{name}.txt")); chunks, secs = parse(p); meta[name] = (chunks, secs)
    for k, s in enumerate(secs): jobs.append((name, k, chunks[0][1], s))
with ThreadPoolExecutor(3) as ex: res = list(ex.map(call, jobs))
out.mkdir(parents=True, exist_ok=True)
for name in sys.argv[4:]:
    chunks, secs = meta[name]; page = _norm(" ".join(c[2] for c in chunks)); raw = " ".join(c[2] for c in chunks)
    kept, dropped = [], []
    for page_, k, evs in res:
        if page_ != name: continue
        if evs is None: dropped.append({"section": k, "reason": "llm_fail"}); continue
        lo, hi = secs[k]["chunks"][0][0], secs[k]["chunks"][-1][0]
        for e in evs:
            e = dict(e, section=k, flags=[])
            if not (lo <= e["chunk"] <= hi): dropped.append(dict(e, reason="bad_chunk")); continue
            e["cid"] = chunks[e["chunk"]][0]; ctext = chunks[e["chunk"]][2]
            d = e["date"]
            if d is not None:
                if not FMT.match(d): dropped.append(dict(e, reason="bad_format")); continue
                if not year_token(d[:4], raw): dropped.append(dict(e, reason="year_not_in_page")); continue
                if not year_token(d[:4], ctext): e["flags"].append("derived_date")
            if e["approximate"]: e["flags"].append("approximate_date")
            en = e["end"]
            if en is not None:
                if not FMT.match(en) or not year_token(en[:4], raw) or (d and en < d):
                    e["flags"].append("end_dropped:" + en); e["end"] = None; e["end_status"] = "unknown"
            if e["end_status"] == "ongoing" and not ongoing_evidence_ok(e["ongoing_evidence"], page):
                e["flags"].append("ongoing_downgraded"); e["end_status"] = "unknown"
            if e["end"] is None and e["end_status"] == "known": e["end_status"] = "unknown"
            kept.append(e)
    (out / f"{name}.json").write_text(json.dumps({"events": kept, "dropped": dropped}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, "kept", len(kept), "dropped", len(dropped), flush=True)
print("DONE", flush=True)
