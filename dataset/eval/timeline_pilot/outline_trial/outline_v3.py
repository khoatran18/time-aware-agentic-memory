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
- `subject`: who or what the page is about, in one sentence, with no dates.
- `aliases`: other NAMES of the subject (full name, birth name, former name, nickname, spelling variant) that the text itself uses, copied exactly as written. Do NOT include titles, ranks, job names, abbreviations of titles, pronouns, or names of other people or things. Empty list if none.
- `sections`: EXACTLY one item per listed section, same order, same `index` and `title` as listed. For each:
  - `covers`: ONE sentence saying what that section is about, based only on that section's own text. Do not write years.

Rules:
- Use only the text of the page. Do NOT add facts from your own knowledge.
- Do NOT list events or dates: that is the next step's job.
- A section titled like the page itself is the lead of the page.
"""

class SectionOutline(BaseModel):
    index: int
    title: str
    covers: str

class PageOutline(BaseModel):
    subject: str
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
    chk = []
    norm = lambda x: re.sub(r"\s+", "", x)
    if res:
        ptxt = norm(" ".join(t for _, _, t in chunks))
        for sc in res.sections:
            if sc.index >= len(secs): chk.append(f"index {sc.index} ngoài khoảng"); continue
            if sc.title.strip() != secs[sc.index]["title"].strip(): chk.append(f"[{sc.index}] tiêu đề đổi: {sc.title!r}")
            if re.search(r"\d{4}", sc.covers): chk.append(f"[{sc.index}] covers có năm: {sc.covers!r}")
        if [x.index for x in res.sections] != list(range(len(secs))): chk.append("thứ tự/số mục lệch")
        for al in res.aliases:
            if norm(al) not in ptxt: chk.append(f"alias không có trong trang: {al!r}")
            if re.fullmatch(r"[A-Z]{2,5}", al.strip()): chk.append(f"alias là chữ viết tắt: {al!r}")
        if re.search(r"\d{4}", res.subject): chk.append(f"subject có năm: {res.subject!r}")
    rec = {"checks": chk, "page": p.stem, "n_chunks": len(chunks), "n_sections": len(secs), "chars_in": len(body),
           "outline": res.model_dump() if res else None}
    (out / f"{p.stem}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(p.stem, "chunks", len(chunks), "sections", len(secs), "chars_in", len(body), "ok" if res else "FAIL", "checks_fail", len(chk),
          "n_out_sections", len(res.sections) if res else None, flush=True)
