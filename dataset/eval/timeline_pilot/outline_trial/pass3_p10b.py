"""Bản 10b (thử nghiệm): = bản 10a với định nghĩa hẹp của kind=result. Bản 10a = bản 9 + trường track/phase/kind/subject/object/quote; có cache (data/llm_cache/ingest/); sửa năm viết tắt bằng ingest_post.
Trích sự kiện theo mục, prompt bản 9 (= bản 8 + mở rộng năm hai chữ số của mốc kết thúc + không lấy khoảng năm tài liệu phủ làm ngày sự kiện + tiêu đề danh sách Runners-up) + norm bỏ khoảng trắng + mã ghép tháng/ngày + mã thêm mốc kết thúc khoảng; PROFILE=env: chỉ date (không end), date_text, cửa sổ <=8 chunk, kiểm chống bịa bằng mã.
Dùng: PROFILE=deepseek_flash python3 pass3_p10.py <repo> <timeline_pilot_dir> <out_dir> <tên trang>...   (DRY=1: chỉ đếm số lần gọi, không gọi LLM)"""
import json, os, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, Field

repo, pilot, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(repo / "src"))
from tam.config.loader import load_config
from tam.llm.factory import get_llm
from tam.llm.structured import invoke_structured
from tam.llm.cache import SqliteCache
sys.path.insert(0, str(Path(__file__).parent))
import ingest_post as ip

WINDOW = 8
PROMPT = """You extract dated events from part of ONE section of a Wikipedia page.

Page title: {title}
Section: {section}

You receive numbered chunks. Chunks marked "(context only)" are given to help you understand; do NOT extract events from them. Go through the other chunks one by one, and for each chunk return EVERY event of the page's subject that the text dates. Each item:
- `text`: one short sentence saying what happened. Use only words and numbers that appear in the chunk.
- `chunk`: the number of the chunk that states it.
- `date_text`: the time expression exactly as written in the chunk, copied word for word ("24 March 1946", "in 1999", "early 2017", "Q4 2017", "circa 1920", "the 1970s", "June"). null if the event has no time expression at all.
- `date`: `YYYY`, `YYYY-MM` or `YYYY-MM-DD` with exactly the precision the text gives; never invent a month or a day. Fill it only if one specific year can be found. Take it from `date_text` itself, or, when `date_text` has only a month, a day or a phrase such as "in March", "later that year", "the following year", "at the end of the year", take it from the nearest earlier year in the chunks you received (earlier chunks of this section and the context chunk). Still copy `date_text` word for word. Use null when there is only a decade or century ("the 1970s", "mid-1990s", "19th century") or when no year appears before it in the chunks you received. When the end of a range is written with only two digits or one digit ("1823–27", "1854–5", "1855–70", "1976-77"), `date_text` stays exactly as written ("27", "5", "70", "77") but `date` must be the full year: take the century and the decade of the start year of the same range (1823–27 gives 1827; 1854–5 gives 1855; 1855–70 gives 1870; 1976-77 gives 1977).
- `approximate`: true when the time is vague: "early/mid/late 2017", "spring of 1910", "circa 1920", "by 1928", "after 1916", "Q4 2017", a season "1999-2000" (then `date` is the single year, e.g. 2017, 1999). Otherwise false.

Rules:
- Use only the text you receive. Do NOT add dates, numbers or facts from your own knowledge. Every number in `text` must appear in the chunk.
- Never turn a decade into a single year ("the 1970s" is NOT 1970). Never put a range, a "Q" or an "s" inside `date`.
- A period with a start and an end ("from 2003 to 2007", "between 1772 and 1774", "1938-01-07 – 1942-06-30: X" in a list, "(Director 1813–1815)", "during the 1935–1977 period", "served until 2001", "term ends 2003") is ALWAYS two separate items, never one. Item 1 is the start: its `date` is the start and its `text` describes only the start ("X became commander"). Item 2 is the end: write it right after item 1, its `date` is the end and its `text` describes only the end ("X's command ended"). Do not put both dates in one item. If only the end is stated (for example "until 2001"), give only the end item.
- A `date` is when the event HAPPENED. A range of years that only says which years a document, index, volume, list, catalogue or external link COVERS ("indexes of the journal for 1846–1900", "Archive: 1846–1899", "Vol. 1–147") is not an event of the subject: skip it, and do not give it a start item and an end item.
- Read the heading of a list or table before you read its entries. Results listed under "Runners-up", "Finalists", "Nominations" or "Losses" are not wins: write "was runner-up in …", never "won …". Results under "Wins" or "Champion" are wins.
- One item per event. If a chunk states several dated events, return each of them. Do not skip events in long chunks.
- Only events and changes: skip specifications, measurements, statistics, descriptions and states without a change ("had a displacement of", "population decreased by", "was spelled").
- Events of the subject itself. Also events of other people or things that directly happen to the subject. Skip the biography of other people merely mentioned, appearances of the subject in films, books, advertising or lists of famous people, and years that are only part of the title of a cited work ("2017 Calendar", "chart of 1782"). Keep an event when the text says the subject won, played, published or took part in something whose name contains a year ("winning the 2008 Russian PriFR event" is an event of 2008).
- Dates inside parentheses, lists, tables and image captions count too: "(1862 and 1875)", "(Director 1813–1815)", "restored in November 2013" in a caption. When one phrase gives several dates, return one item per date.
- Resolve "the following year", "that year", "later that year" and a bare month ("In September") with the nearest earlier year in the chunks you received (read the chunks in order, and use the context chunk too). Use null only if no earlier year can be found.

Extra labels (add them to EVERY item; they do not change which events you extract: still return every dated event as above):
- `track`: the kind of change, one of: role (office, term, rank, command, directorship) | affiliation (employer, team, party, organisation, league, joining or leaving an organisation) | location (residence, headquarters, country, moving) | ownership_structure (ownership, operator, parent company, publisher, label, transfer of management) | work (product, building, programme or work made by the subject: release, performance, construction, completion) | naming (official name, renaming) | family (marriage, family) | education (studied at, graduated) | other (everything else: birth, death, award, honour, founding, competition result, event). If unsure prefer role, then affiliation, then work.
- `phase`: "start" for the first item of a period, "end" for the second item of a period, "point" for a one-off event.
- `kind`: "change" (a state, role, name, place, owner or membership changes), "occurrence" (a one-off happening or achievement: born, died, won, published, built), "state" (a dated state without a change: "had the rank of"), "result" (the score or outcome of ONE match, race, game or a season standing; winning a title, medal, award or championship is NOT a result: use "occurrence"), "statement" (something said, written or proposed).
- `subject`: "self" when the event is about the page's subject; "part_of_self" when it is about a member, leader, unit or product of the subject; "other" for another person or thing.
- `object`: the main named thing of the event copied word for word from the chunk (a name, title or place: "Soviet Square", "Euromaidan", "Hewlett-Packard"), or null if there is none.
- `quote`: a short verbatim excerpt (under 25 words) from the chunk that states the event, copied exactly. It must contain `date_text` when `date_text` is not null.
Say each real event ONCE: if the chunks you received state the same event twice, return one item (the one with the most complete date).
"""

class Ev(BaseModel):
    text: str
    chunk: int
    date_text: str | None = None
    date: str | None = None
    approximate: bool = False
    track: str = "other"
    phase: str = "point"
    kind: str = "occurrence"
    subject: str = "self"
    object: str | None = None
    quote: str | None = None

class Evs(BaseModel):
    events: list[Ev] = Field(default_factory=list)

def parse(path):
    parts = re.split(r"^=== CHUNK (\S+) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    chunks = []
    for cid, body in zip(parts[1::2], parts[2::2]):
        head, _, text = body.partition("\n")
        chunks.append((cid, (head.split(" | ", 1)[1] if " | " in head else "Lead").strip(), text.strip()))
    secs = []
    for i, (cid, t, x) in enumerate(chunks):
        if secs and secs[-1]["title"] == t: secs[-1]["chunks"].append((i, x))
        else: secs.append({"title": t, "chunks": [(i, x)]})
    return chunks, secs

MONTHS = ['january','february','march','april','may','june','july','august','september','october','november','december']
FMT = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
TRACKS = {'role', 'affiliation', 'location', 'ownership_structure', 'work', 'naming', 'family', 'education', 'other'}
KINDS = {'change', 'occurrence', 'state', 'result', 'statement'}
norm = lambda s: re.sub(r"\s+", "", s).lower()  # bỏ mọi khoảng trắng: văn bản gốc tách "6 , 1959"
def year_token(y, text): return re.search(rf"(?<!\d){y}(?!\d|s)", text) is not None

DRY = os.environ.get("DRY") == "1"
if not DRY:
    cfg = load_config(); llm = get_llm(cfg, os.environ.get("PROFILE", "deepseek_flash")); chain = llm.with_structured_output(Evs)
    CACHE = SqliteCache(repo / "data" / "llm_cache" / "ingest" / "cache.sqlite", threadsafe=True)  # khóa = schema + model + toàn bộ prompt/đầu vào

def call(args):
    page, k, w, title, section, ctx, items = args
    lines = ([f"[{ctx[0]}] (context only) {ctx[1]}"] if ctx else []) + [f"[{i}] {x}" for i, x in items]
    msgs = [("system", PROMPT.format(title=title, section=section)), ("human", "\n\n".join(lines))]
    r = invoke_structured(llm, chain, Evs, msgs, max_attempts=3, cache=CACHE)
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
if DRY: print("DRY: số lần gọi tối đa (chưa trừ cache hit):", len(jobs)); sys.exit(0)
with ThreadPoolExecutor(3) as ex: res = list(ex.map(call, jobs))
print("cache: hit", CACHE.hits, "miss", CACHE.misses, flush=True)
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
                if not year_token(d[:4], raw):
                    if dt and ip.expands_to(raw, d[:4], dt): e["flags"].append("year_expanded_from_range")  # năm cuối khoảng viết tắt ("1855–70")
                    else: dropped.append(dict(e, reason="year_not_in_page")); continue
                if not year_token(d[:4], ct): e["flags"].append("derived_date")
            if d and len(d) == 4 and dt and not e["approximate"]:
                ms = {m: i + 1 for i, m in enumerate(MONTHS)}
                found = {ms[m.lower()] for m in re.findall(r"\b(" + "|".join(MONTHS) + r")\b", dt, re.I)}
                if len(found) == 1 and len(re.findall(r"(?<!\d)\d{4}(?!\d)", dt)) <= 1:
                    mo = found.pop(); d = e["date"] = f"{d}-{mo:02d}"; e["flags"].append("month_from_date_text")
                    dm = re.search(r"\b(\d{1,2})\s+(?:" + "|".join(MONTHS) + r")\b|\b(?:" + "|".join(MONTHS) + r")\s+(\d{1,2})\b", dt, re.I)
                    if dm: d = e["date"] = f"{d}-{int(dm.group(1) or dm.group(2)):02d}"
            if e["approximate"]: e["flags"].append("approximate_date")
            nums = [n.replace(",", "") for n in re.findall(r"\d[\d,\.]*\d|\d", e["text"])]
            ctn = ct.replace(",", "")
            bad = [n for n in nums if n not in ctn and not (d and n == d[:4]) and n.rstrip(".") not in ctn]
            if bad: dropped.append(dict(e, reason="number_not_in_chunk:" + ",".join(bad))); continue
            words = re.findall(r"(?<=[a-z,] )[A-Z][\w'’-]{2,}", e["text"])
            missing = [wd for wd in words if wd not in raw]
            if missing: e["flags"].append("name_not_in_page:" + ",".join(missing))
            if e["track"] not in TRACKS: e["flags"].append("bad_track:" + str(e["track"])); e["track"] = "other"
            if e["phase"] not in ("start", "end", "point"): e["flags"].append("bad_phase"); e["phase"] = "point"
            if e["kind"] not in KINDS: e["flags"].append("bad_kind"); e["kind"] = "occurrence"
            if e["subject"] not in ("self", "part_of_self", "other"): e["flags"].append("bad_subject"); e["subject"] = "self"
            if e.get("quote") and norm(e["quote"]) not in cn: e["flags"].append("quote_not_in_chunk")
            key = (e["date"], e["cid"], norm(e["text"])[:40])
            if key in seen: dropped.append(dict(e, reason="duplicate")); continue
            seen.add(key); kept.append(e)
    (out / f"{name}.json").write_text(json.dumps({"events": kept, "dropped": dropped}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(name, "kept", len(kept), "dropped", len(dropped), flush=True)
print("DONE", flush=True)
