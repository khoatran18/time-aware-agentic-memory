"""Thử lần gọi 2 (dàn ý cả trang) trên vài trang tune. Dùng: python outline_test.py <repo> <out_dir> <file1.txt> ..."""
import json, re, sys
from pathlib import Path
from pydantic import BaseModel, Field

repo, out = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo / "src"))
from tam.config.loader import load_config
from tam.llm.factory import get_llm
from tam.llm.structured import invoke_structured

PROMPT = """You read ONE Wikipedia page, already split into numbered sections by code, and write a short OUTLINE of it.
The outline is shared context for a later step that extracts dated events section by section. It is NOT a summary of the facts.

Page title: {title}

Return:
- `subject`: who or what the page is about, in one sentence (no dates).
- `page_type`: one of person, organization, place, work, event, vehicle_or_object, other.
- `aliases`: other names, titles, nicknames and spellings the text uses for the subject (copy them from the text; empty list if none).
- `sections`: EXACTLY one item per listed section, same order, same `index` and `title` as listed. For each:
  - `covers`: one or two sentences saying which period or topic of the subject's story the section covers.
  - `period`: the span of time the section covers, as the text states it (for example "1990s", "1914-1918"); null if the section gives none.
  - `entities`: up to 6 main people, organizations or places named in the section.
  - `links`: how the section continues or relates to another section (for example "continues 'Early life'"); null if not relevant.
  - `has_events`: false for sections with no events of the subject (references, notes, external links, pure lists of sources); otherwise true.

Rules:
- Use only the text. Do NOT add facts from your own knowledge.
- Do NOT list dates of individual events and do NOT list events: that is the next step's job. Keep each `covers` short.
- If the page title is the only heading of a section, that section is the lead of the page.
"""

class SectionOutline(BaseModel):
    index: int
    title: str
    covers: str
    period: str | None = None
    entities: list[str] = Field(default_factory=list)
    links: str | None = None
    has_events: bool = True

class PageOutline(BaseModel):
    subject: str
    page_type: str
    aliases: list[str] = Field(default_factory=list)
    sections: list[SectionOutline]

def parse(path: Path):
    chunks = []
    for blk in re.split(r"^=== CHUNK (\S+) ===\n", path.read_text(encoding="utf-8"), flags=re.M)[1:]:
        pass
    parts = re.split(r"^=== CHUNK (\S+) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    for cid, body in zip(parts[1::2], parts[2::2]):
        head, _, text = body.partition("\n")
        title = head.split(" | ", 1)[1].strip() if " | " in head else head.strip()
        chunks.append((cid, title, text.strip()))
    secs = []  # liên tiếp cùng tiêu đề = một mục
    for i, (cid, title, text) in enumerate(chunks):
        if secs and secs[-1]["title"] == title:
            secs[-1]["chunks"].append((i, text))
        else:
            secs.append({"title": title, "chunks": [(i, text)]})
    return chunks, secs

cfg = load_config()
llm = get_llm(cfg, "google_31")
chain = llm.with_structured_output(PageOutline)
out.mkdir(parents=True, exist_ok=True)
for f in sys.argv[3:]:
    p = Path(f); chunks, secs = parse(p)
    title = chunks[0][1]
    listing = "\n".join(f"[{k}] {s['title']}  (chunks {s['chunks'][0][0]}-{s['chunks'][-1][0]})" for k, s in enumerate(secs))
    body = "Sections:\n" + listing + "\n\n" + "\n\n".join(
        f"### [{k}] {s['title']}\n" + "\n".join(t for _, t in s["chunks"]) for k, s in enumerate(secs))
    msgs = [("system", PROMPT.format(title=title)), ("human", body)]
    res = invoke_structured(llm, chain, PageOutline, msgs, max_attempts=3, cache=None)
    rec = {"page": p.stem, "n_chunks": len(chunks), "n_sections": len(secs), "chars_in": len(body),
           "outline": res.model_dump() if res else None}
    (out / f"{p.stem}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(p.stem, "chunks", len(chunks), "sections", len(secs), "chars_in", len(body), "ok" if res else "FAIL",
          "n_out_sections", len(res.sections) if res else None, flush=True)
