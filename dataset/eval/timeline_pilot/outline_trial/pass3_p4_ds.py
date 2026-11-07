"""Trích sự kiện theo mục, bản 3: chỉ date (không end), date_text, cửa sổ <=8 chunk, kiểm chống bịa bằng mã.
Dùng: python pass3_v3.py <repo> <timeline_pilot_dir> <out_dir> <tên trang>..."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, Field

repo, pilot, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(repo / "src"))
from tam.config.loader import load_config
from tam.llm.factory import get_llm
from tam.llm.structured import invoke_structured

WINDOW = 8
PROMPT = """You extract dated events from part of ONE section of a Wikipedia page.

Page title: {title}
Section: {section}

You receive numbered chunks. Chunks marked "(context only)" are given to help you understand; do NOT extract events from them. Go through the other chunks one by one, and for each chunk return EVERY event of the page's subject that the text dates. Each item:
- `text`: one short sentence saying what happened. Use only words and numbers that appear in the chunk.
- `chunk`: the number of the chunk that states it.
- `date_text`: the time expression exactly as written in the chunk, copied word for word ("24 March 1946", "in 1999", "early 2017", "Q4 2017", "circa 1920", "the 1970s", "June"). null if the event has no time expression at all.
- `date`: `YYYY`, `YYYY-MM` or `YYYY-MM-DD` with exactly the precision the text gives; never invent a month or a day. Fill it only if one specific year can be found. Take it from `date_text` itself, or, when `date_text` has only a month, a day or a phrase such as "in March", "later that year", "the following year", "at the end of the year", take it from the nearest earlier year in the chunks you received (earlier chunks of this section and the context chunk). Still copy `date_text` word for word. Use null when there is only a decade or century ("the 1970s", "mid-1990s", "19th century") or when no year appears before it in the chunks you received.
- `approximate`: true when the time is vague: "early/mid/late 2017", "spring of 1910", "circa 1920", "by 1928", "after 1916", "Q4 2017", a season "1999-2000" (then `date` is the single year, e.g. 2017, 1999). Otherwise false.

Rules:
- Use only the text you receive. Do NOT add dates, numbers or facts from your own knowledge. Every number in `text` must appear in the chunk.
- Never turn a decade into a single year ("the 1970s" is NOT 1970). Never put a range, a "Q" or an "s" inside `date`.
- A situation that lasted from X to Y ("from 2003 to 2007", "until 2001"): give one item for the start (`date` X). If the end date is stated, give a second item for the end ("... ended", `date` Y). If only the end is stated, give only that end item.
- One item per event. If a chunk states several dated events, return each of them. Do not skip events in long chunks.
- Only events and changes: skip specifications, measurements, statistics, descriptions and states without a change ("had a displacement of", "population decreased by", "was spelled").
- Events of the subject itself. Also events of other people or things that directly happen to the subject. Skip the biography of other people merely mentioned, appearances of the subject in films, books, advertising or lists of famous people, and dates of cited works or of names that contain a year ("2017 Calendar", "chart of 1782").
- Resolve "the following year", "that year", "later that year" and a bare month ("In September") with the nearest earlier year in the chunks you received (read the chunks in order, and use the context chunk too). Use null only if no earlier year can be found.
"""

class Ev(BaseModel):
    text: str
    chunk: int
    date_text: str | None = None
    date: str | None = None
    approximate: bool = False

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
norm = lambda s: re.sub(r"\s+", " ", s).strip().lower()
def year_token(y, text): return re.search(rf"(?<!\d){y}(?!\d|s)", text) is not None

cfg = load_config(); llm = get_llm(cfg, "deepseek_flash"); chain = llm.with_structured_output(Evs)

def call(args):
    page, k, w, title, section, ctx, items = args
    lines = ([f"[{ctx[0]}] (context only) {ctx[1]}"] if ctx else []) + [f"[{i}] {x}" for i, x in items]
    msgs = [("system", PROMPT.format(title=title, section=section)), ("human", "\n\n".join(lines))]
    r = invoke_structured(llm, chain, Evs, msgs, max_attempts=3, cache=None)
    print(page, "sec", k, "win", w, "ok" if r else "FAIL", len(r.events) if r else None, flush=True)
    return page, k, w, [e.model_dump() for e in r.events] if r else None

jobs, meta = [], {}
for name in sys.argv[4:]:
    p = next(Path(pilot).glob(f"batch*/in/{name}.txt")); chunks, secs = parse(p); meta[name] = (chunks, secs)
    for k, s in enumerate(secs):
        ch = s["chunks"]
        for w, lo in enumerate(range(0, len(ch), WINDOW)):
            ctx = ch[lo - 1] if lo > 0 else None
            jobs.append((name, k, w, chunks[0][1], s["title"], ctx, ch[lo:lo + WINDOW]))
with ThreadPoolExecutor(3) as ex: res = list(ex.map(call, jobs))
out.mkdir(parents=True, exist_ok=True)
for name in sys.argv[4:]:
    chunks, secs = meta[name]; raw = " ".join(c[2] for c in chunks); pagen = norm(raw)
    kept, dropped, seen = [], [], set()
    for page_, k, w, evs in res:
        if page_ != name: continue
        if evs is None: dropped.append({"section": k, "reason": "llm_fail"}); continue
        allowed = {i for i, _ in secs[k]["chunks"]}
        for e in evs:
            e = dict(e, section=k, flags=[])
            if e["chunk"] not in allowed: dropped.append(dict(e, reason="bad_chunk")); continue
            e["cid"] = chunks[e["chunk"]][0]; ct = chunks[e["chunk"]][2]; cn = norm(ct)
            dt, d = e["date_text"], e["date"]
            if dt:
                if norm(dt) not in cn:
                    if norm(dt) not in pagen: dropped.append(dict(e, reason="date_text_not_in_page")); continue
                    e["flags"].append("date_text_not_in_chunk")
                ym = re.findall(r"(?<!\d)\d{4}(?!\d)", dt)
                if d and ym and d[:4] not in ym: dropped.append(dict(e, reason="date_text_year_mismatch")); continue
                if re.search(r"\d{3}0s|century|decade", dt, re.I) and d: e["flags"].append("decade_date_cleared"); e["date"] = d = None
            if d is not None:
                if not FMT.match(d): dropped.append(dict(e, reason="bad_format")); continue
                if not year_token(d[:4], raw): dropped.append(dict(e, reason="year_not_in_page")); continue
                if not year_token(d[:4], ct): e["flags"].append("derived_date")
            if e["approximate"]: e["flags"].append("approximate_date")
            nums = [n.replace(",", "") for n in re.findall(r"\d[\d,\.]*\d|\d", e["text"])]
            ctn = ct.replace(",", "")
            bad = [n for n in nums if n not in ctn and not (d and n == d[:4]) and n.rstrip(".") not in ctn]
            if bad: dropped.append(dict(e, reason="number_not_in_chunk:" + ",".join(bad))); continue
            words = re.findall(r"(?<=[a-z,] )[A-Z][\w'’-]{2,}", e["text"])
            missing = [wd for wd in words if wd not in raw]
            if missing: e["flags"].append("name_not_in_page:" + ",".join(missing))
            key = (e["date"], e["cid"], norm(e["text"])[:40])
            if key in seen: dropped.append(dict(e, reason="duplicate")); continue
            seen.add(key); kept.append(e)
    (out / f"{name}.json").write_text(json.dumps({"events": kept, "dropped": dropped}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, "kept", len(kept), "dropped", len(dropped), flush=True)
print("DONE", flush=True)
