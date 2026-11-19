"""Sinh bản quá khứ (mô phỏng) của một số chunk để thử Cơ chế 3. Thiết kế: docs/decisions/16_MECH3_PAST_VERSION_DESIGN.md.

Mỗi chỗ sửa = một câu trong một chunk của bản `real` (bản mới nhất). Chunk còn lại và các câu khác giữ nguyên.
  C: đổi một năm trong câu (code, không LLM)           E: viết lại thành "còn đang tiếp diễn" (LLM)
  F: đổi một giá trị/tên thành giá trị sai (LLM)         A: diễn đạt lại không đổi ý, đối chứng (LLM)
Kết quả: <out>/edits.jsonl (nhãn), <out>/chunks/<trang>.txt (chunk bản cũ, id có hậu tố @past).
Chạy: python scripts/make_past.py --split tune --workers 20 [--dry]   (--dry: chỉ chọn chỗ sửa, không gọi LLM)
LLM: OpenCode, model qua --model (mặc định hy4-flash-free); cache riêng data/llm_cache/pastgen_<model>/.
Thinking: profile gửi thinking=disabled nhưng hy4 BỎ QUA (đã kiểm: reasoning tokens vẫn 108); chỉ reasoning_effort:none tắt được, nhưng chất lượng giảm. Dùng thinking BẬT.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ORG = ROOT / "dataset" / "organized"
YEAR = re.compile(r"(?<!\d)\d{4}(?!\d)")
CAPS = re.compile(r"(?<=[a-z,0-9] )[A-Z][\w'’-]{2,}")
END_W = re.compile(r"\b(until|left|resigned|retired|stepped down|replaced|ended|succeeded|ceased)\b", re.I)
norm = lambda s: re.sub(r"\s+", "", s).lower()
QUOTA = {"C": 1, "E": 1, "F": 1, "A": 1}   # tỉ lệ; chỉnh theo ứng viên E hiếm hơn


def parse_chunks(path: Path) -> list[dict]:
    """Chunk của một trang: id, tiêu đề mục, thân (giữ nguyên khoảng trắng gốc)."""
    parts = re.split(r"^=== CHUNK (\S+) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    out = []
    for k in range(1, len(parts), 2):
        head, _, body = parts[k + 1].partition("\n")
        out.append({"id": parts[k], "head": head, "body": body})
    return out


ABBR = {"mr", "mrs", "ms", "dr", "st", "jr", "sr", "vs", "c", "b", "d", "ca", "no", "inc", "co", "ltd", "mt", "fr", "prof", "gen", "col", "lt", "rev", "hon", "gov", "sen", "rep", "capt", "cdr", "adm", "maj", "sgt", "cpl", "esq", "vol", "dept", "ft", "bros", "mme", "mlle", "sra"}


def sentences(body: str) -> list[str]:
    """Tách câu theo '. ' nhưng không tách sau viết tắt (B.S . / c . / Dr .): token trước dấu chấm có chấm bên trong hoặc nằm trong ABBR."""
    parts = re.split(r"(?<=\.) (?=\S)", body.strip())
    out: list[str] = []
    for x in parts:
        if out:
            tok = out[-1].rstrip(" .").split(" ")[-1] if out[-1].endswith(".") else ""
            if tok and ("." in tok or tok.lower() in ABBR or (len(tok) == 1 and tok.isupper())):
                out[-1] += " " + x
                continue
        out.append(x)
    return out


def frag_ok(s: str) -> bool:
    """Câu không phải mảnh cụt: mở bằng chữ hoa/số/'- ' và ngoặc không âm."""
    return (s[:1].isupper() or s[:1].isdigit() or s.startswith("- ")) and s.count(")") == s.count("(") and not re.match(r"\d[\d/]*\s[–-]", s)


def whole_sentence_ok(chunks: list[dict], ci: int, si: int, sents: list[str]) -> bool:
    """Câu trọn trong chunk: câu giữa luôn được; câu đầu chỉ khi chunk mở đầu một mục; câu cuối chỉ khi kết thúc bằng dấu chấm."""
    if si == 0 and ci > 0 and chunks[ci - 1]["head"] == chunks[ci]["head"]:
        return False
    return not (si == len(sents) - 1 and not sents[si].rstrip().endswith("."))


END_CTX = r"(?:until|till|to|through|death in|died in|left in|resigned in|retired in|stepped down in|ended in|ceased in)"


def strict_e(sentence: str, event: dict) -> bool:
    """Câu E hợp lệ: mốc phase=end, năm kết thúc của mốc đứng ngay sau until/to/through/... và chỉ xuất hiện một lần."""
    d = event.get("date")
    if event.get("phase") != "end" or not d or event.get("approximate"):
        return False
    y = d[:4]
    return YEAR.findall(sentence).count(y) == 1 and bool(re.search(rf"\b{END_CTX}\b[^.;,()]{{0,25}}?(?<!\d){y}(?!\d)", sentence, re.I))


ONGOING = re.compile(r"\b(is|are|has|have|remains?|remained|continues?|continued|currently|still|since|present|today|to date|ongoing|continuing|serving|serves|holds?|works?|lives?)\b", re.I)
MONTH = r"(January|February|March|April|May|June|July|August|September|October|November|December)"


def chunk_has_end(body: str, ev: dict) -> bool:
    """Năm kết thúc (hoặc tháng-năm nếu mốc có tháng) còn xuất hiện trong đoạn văn."""
    d = ev["date"]
    ye = d[:4]
    mon = re.search(MONTH, ev.get("text") or "")
    if len(d) > 4 and mon:
        return bool(re.search(rf"{mon.group(1)}\s+(?:\d{{1,2}},?\s+)?{ye}|{ye}[^.]{{0,12}}{mon.group(1)}", body))
    return ye in YEAR.findall(body)


def e_chunk_bad(chunk: dict, sentence_real: str, new: str, ev: dict) -> list[str]:
    """Kiểm mức chunk cho E: chunk bản cũ không còn năm kết thúc; câu mới có từ chỉ còn tiếp diễn."""
    bad = []
    if chunk_has_end(chunk["body"].replace(sentence_real, new, 1), ev):
        bad.append("end_in_chunk")
    if not ONGOING.search(new) and re.search(r"\b(was|were|had|\w{3,}ed)\b", new):   # không có từ chỉ tiếp diễn VÀ còn dấu hiệu thì quá khứ
        bad.append("no_ongoing_marker")
    return bad


def candidates(page: str, chunks: list[dict], events: list[dict]) -> dict[str, list[dict]]:
    by_id = {c["id"]: k for k, c in enumerate(chunks)}
    res: dict[str, list[dict]] = {t: [] for t in QUOTA}
    for e in events:
        ci = by_id.get(e.get("cid"))
        if ci is None or not e.get("quote") or not e.get("date"):
            continue
        sents = sentences(chunks[ci]["body"])
        hit = [i for i, s in enumerate(sents) if norm(e["quote"]) in norm(s)]
        if len(hit) != 1 or not whole_sentence_ok(chunks, ci, hit[0], sents) or not frag_ok(sents[hit[0]]):
            continue
        si, s = hit[0], sents[hit[0]]
        base = dict(page=page, ci=ci, si=si, sentence=s, event={k: e.get(k) for k in ("date", "text", "track", "phase", "kind", "quote")})
        yr = e["date"][:4]
        if not e.get("approximate") and len(YEAR.findall(s)) >= 1 and YEAR.findall(s).count(yr) == 1:
            res["C"].append(dict(base, year=yr))
        if strict_e(s, e) and not chunk_has_end(chunks[ci]["body"].replace(s, "", 1), e):
            res["E"].append(base)
        if e.get("track") in ("role", "affiliation", "ownership_structure") and CAPS.search(s):
            res["F"].append(base)
        if 8 <= len(s.split()) <= 45:
            res["A"].append(base)
    return res


def shift_year(c: dict, rng: random.Random) -> dict:
    s, y = c["sentence"], int(c["year"])
    others = set(YEAR.findall(s))
    d = next(x for x in rng.sample([-4, -3, -2, -1, 1, 2, 3, 4], 8) if str(y + x) not in others)
    new = re.sub(rf"(?<!\d){y}(?!\d)", str(y + d), s, count=1)
    return dict(sentence_past=new, old_value=str(y + d), new_value=str(y), note=f"year {y} -> {y + d} in the past version")


PROMPTS = {
    "E": ("Rewrite the TARGET sentence so that it clearly states the situation is STILL ONGOING at the time of writing (as if the passage were "
          "written before the situation ended). Remove the end date and any mention of a successor, departure or ending; keep the start. "
          "Use present or present-perfect wording (e.g. 'is', 'has ... since <start>', 'remains', 'continues to', 'currently'). Also drop clauses that "
          "only make sense after the end ('in protest', 'after N years', 'returning to ...'). Do NOT add any new year, number or name; keep every "
          "other year and name exactly. Change nothing else."),
    "F": ("Rewrite the TARGET sentence replacing exactly ONE factual value (a person's name, a place or an organisation) with a different, "
          "plausible but WRONG value of the same kind. Keep every other word. Report the replaced value and the new wrong value."),
    "A": ("Paraphrase the TARGET sentence without changing any fact: keep every name, number and date exactly, change only wording."),
}


def run_llm(kind: str, chunk: dict, c: dict, llm, chain, cache, Out, retry: int = 0) -> dict | None:
    from tam.llm.structured import invoke_structured

    marked = chunk["body"].replace(c["sentence"], f"<<TARGET>> {c['sentence']} <</TARGET>>", 1)
    sys_p = ("You edit one sentence of a Wikipedia passage to build a synthetic OLDER version of the page. " + PROMPTS[kind] +
             " The text is tokenised: keep spaces around punctuation exactly like the input. Return only the rewritten TARGET sentence "
             "(without the markers), plus old_value/new_value when you replaced a value (null otherwise)."
             + (" Retry: put the full rewritten sentence in the `sentence` field; keep every clause that is not part of the change; do not shorten the sentence beyond the change." if retry else "")
             + (f" (attempt {retry})" if retry > 1 else ""))
    hint = f"\n\nThe end to remove: {c['event']['date'][:4]}." if kind == "E" else ""
    msgs = [("system", sys_p), ("human", f"Section: {chunk['head']}\n\nPassage:\n{marked}{hint}")]
    r = invoke_structured(llm, chain, Out, msgs, max_attempts=3, cache=cache)
    if r is None:
        return None
    return dict(sentence_past=r.sentence.strip(), old_value=r.old_value, new_value=r.new_value, note=None)


def verify(kind: str, c: dict, r: dict) -> list[str]:
    """Lỗi kiểm bằng code (rỗng = đạt). Chỉ câu mục tiêu thay đổi vì ta ghép lại; ở đây kiểm nội dung câu mới."""
    old, new = c["sentence"], r["sentence_past"]
    bad = []
    if norm(old) == norm(new):
        bad.append("unchanged")
    if kind != "C" and len(new.split()) > len(old.split()) + 6:
        bad.append("length_grew")
    if (kind == "F" and len(new.split()) < len(old.split()) - 4) or (kind == "A" and len(new.split()) < 0.6 * len(old.split())):
        bad.append("length_shrunk")
    if kind == "C" and YEAR.findall(old).count(c["year"]) != 1:
        bad.append("year")
    if kind == "E":
        ye = c["event"]["date"][:4]
        d = c["event"]["date"]
        mon = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)", c["event"].get("text") or "")
        if len(d) > 4 and mon and mon.group(1) in old:   # mốc có tháng: kết thúc tính theo tháng-năm (From January to July 1982 -> From January 1982 là đạt)
            if re.search(rf"{mon.group(1)}\s+(?:\d{{1,2}},?\s+)?{ye}|{ye}[^.]{{0,12}}{mon.group(1)}", new):
                bad.append("end_still_present")
        elif ye in YEAR.findall(new):
            bad.append("end_still_present")
        if set(re.findall(r"\d+", new)) - set(re.findall(r"\d+", old)):
            bad.append("new_number")
        lost = set(YEAR.findall(old)) - {ye} - set(YEAR.findall(new))
        if any(int(y) <= int(ye) for y in lost):   # mất năm sau mốc kết thúc thì chấp nhận (cắt phần sau, hợp với bản cũ)
            bad.append("other_year_lost")
        if len(new.split()) < 0.3 * len(old.split()):
            bad.append("over_edit")
    if kind == "F":
        ov, nv = r.get("old_value"), r.get("new_value")
        if not ov or not nv or norm(ov) not in norm(old) or norm(new).count(norm(ov)) >= norm(old).count(norm(ov)) or norm(nv) not in norm(new) or norm(nv) in norm(old):
            bad.append("value_swap")
    if kind == "A":
        if sorted(YEAR.findall(old)) != sorted(YEAR.findall(new)) or any(w not in new for w in CAPS.findall(old)):
            bad.append("facts_changed")
    return bad


def write_metrics(a, out: Path, name: str, cache, t0: float, rows: list[dict], calls: int) -> None:
    """Ghi chỉ số lần chạy vào <out>/<name>.json và in ra log: cache trúng/trượt, số lần gọi, thời gian, thinking, kết quả kiểm theo loại."""
    from collections import Counter
    m = dict(run=name, model=a.model, thinking="BẬT (hy4 bỏ qua thinking:disabled; chỉ reasoning_effort:none mới tắt, đã kiểm 2026-11-18)", workers=a.workers,
             cache_dir=f"data/llm_cache/pastgen_{'e2_' if a.regen_e else ''}{a.model}", llm_calls_planned=calls,
             cache_hits=getattr(cache, "hits", None), cache_misses=getattr(cache, "misses", None), wall_s=round(time.time() - t0, 1),
             rows=len(rows), passed=sum(not r["checks_failed"] for r in rows),
             by_type={k: dict(total=sum(r["type"] == k for r in rows), passed=sum(r["type"] == k and not r["checks_failed"] for r in rows)) for k in "CEFA"},
             fails=dict(Counter(x for r in rows for x in r["checks_failed"])))
    (out / f"{name}.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print("METRICS", json.dumps(m, ensure_ascii=False), flush=True)


def redo(a, out: Path) -> None:
    """Kiểm lại edits.jsonl bằng luật hiện tại; chỗ hỏng: thử lại cùng câu (prompt retry) nếu câu còn hợp lệ, không thì thay bằng ứng viên cùng loại trên trang (rồi trang khác chưa dùng)."""
    import os
    import shutil
    from collections import Counter
    from concurrent.futures import ThreadPoolExecutor

    t0 = time.time()
    f = out / "edits.jsonl"
    src = out / "edits_v5.jsonl"
    if a.from_current:
        src = out / "edits_prev.jsonl"
        shutil.copy2(f, src)
    elif not src.exists():
        shutil.copy2(f, src)
    rows = [json.loads(x) for x in src.read_text(encoding="utf-8").splitlines() if x.strip()]
    gold = gold_chunks(a.split)
    pc: dict[str, list] = {}
    get = lambda p: pc.setdefault(p, parse_chunks(ORG / "source" / a.split / "chunks" / f"{p}.txt"))
    evs = lambda p: json.loads((ORG / "graph" / a.split / "ingest_10b" / f"{p}.json").read_text(encoding="utf-8"))["events"]

    def cand_of(r):
        ch = get(r["page"]); ci = next(k for k, c in enumerate(ch) if c["id"] == r["chunk_id"])
        return dict(page=r["page"], ci=ci, sentence=r["sentence_real"], event=r["event"], year=(r["event"].get("date") or "")[:4])

    def valid(r) -> list[str]:
        if r["type"] == "C":
            return list(r["checks_failed"])
        bad = ["llm_fail"] if r["sentence_past"] is None else verify(r["type"], cand_of(r), dict(sentence_past=r["sentence_past"], old_value=r["real_value"], new_value=r["past_value"]))
        if not frag_ok(r["sentence_real"]):
            bad.append("fragment")
        if r["type"] == "E" and not strict_e(r["sentence_real"], r["event"]):
            bad.append("not_end_sentence")
        if r["type"] == "E" and r["sentence_past"] is not None:
            bad += e_chunk_bad(get(r["page"])[cand_of(r)["ci"]], r["sentence_real"], r["sentence_past"], r["event"])
            if chunk_has_end(get(r["page"])[cand_of(r)["ci"]]["body"].replace(r["sentence_real"], "", 1), r["event"]):
                bad.append("not_end_sentence")   # năm kết thúc còn ở câu khác trong chunk: thay chỗ sửa
        return bad

    todo = []
    for n, r in enumerate(rows):
        r["checks_failed"] = valid(r)
        if a.regen_e and r["type"] == "E" and "regen" not in r:
            r["checks_failed"] = r["checks_failed"] or ["regen_e"]   # sinh lại mọi chỗ E bằng prompt mới
        if r["checks_failed"] or (r["edit_id"] in a.swap.split(",") and a.swap):
            todo.append(n)
    print("hỏng theo luật hiện tại (offline):", len(todo), "/", len(rows), Counter(x for n in todo for x in rows[n]["checks_failed"]))
    print("ids:", [rows[n]["edit_id"] for n in todo])
    if a.no_llm:
        return
    used = {}
    for r in rows:
        used.setdefault(r["page"], set()).add(r["chunk_id"])
    jobs = []
    rng_r = random.Random(7)
    info_pages = [q for q in (ORG / f"pages_{a.split}.txt").read_text().split() if (ORG / "graph" / a.split / "ingest_10b" / f"{q}.json").exists()]
    for n in todo:
        r = rows[n]
        ok_same = not set(r["checks_failed"]) & {"fragment", "not_end_sentence"} and r["edit_id"] not in a.swap.split(",")
        if ok_same:
            jobs.append((n, cand_of(r)))
            continue
        ch = get(r["page"])
        pool = [c for c in candidates(r["page"], ch, evs(r["page"]))[r["type"]] if ch[c["ci"]]["id"] not in used[r["page"]]]
        if pool:
            c = pool[0]
            used[r["page"]].add(ch[c["ci"]]["id"])
            r.update(chunk_id=ch[c["ci"]]["id"], chunk_id_past=ch[c["ci"]]["id"] + "@past", on_gold_chunk=ch[c["ci"]]["id"] in gold,
                     sentence_real=c["sentence"], event=c["event"], replaced=True)
            jobs.append((n, c))
        else:   # không còn ứng viên trên trang: lấy trang khác chưa có chỗ sửa
            other = [q for q in info_pages if len(used.get(q, ())) < a.per_page]
            rng_r.shuffle(other)
            hit = None
            for q in other + sorted([x for x in info_pages if x not in other], key=lambda x: len(used.get(x, ()))):   # hết trang còn chỗ: cho phép trang đã đủ per_page nhận thêm 1 (ngoại lệ, ghi vào log)
                chq = get(q)
                pl = [c for c in candidates(q, chq, evs(q))[r["type"]] if chq[c["ci"]]["id"] not in used.get(q, set())]
                if pl:
                    hit = (q, chq, pl[0])
                    if q not in other:
                        print("ngoại lệ: trang", q, "nhận chỗ sửa thứ", len(used.get(q, ())) + 1)
                    break
            if hit:
                q, chq, c = hit
                used.setdefault(q, set()).add(chq[c["ci"]]["id"])
                r.update(page=q, chunk_id=chq[c["ci"]]["id"], chunk_id_past=chq[c["ci"]]["id"] + "@past", on_gold_chunk=chq[c["ci"]]["id"] in gold,
                         sentence_real=c["sentence"], event=c["event"], replaced=True)
                jobs.append((n, c))
            else:
                r["checks_failed"] = ["no_valid_candidate"]
    print("gọi LLM:", len(jobs), "lần (prompt retry)", flush=True)
    llm, chain, cache, Out = setup_llm(a)

    def work(j):
        n, c = j
        r = run_llm(rows[n]["type"], get(c["page"])[c["ci"]], c, llm, chain, cache, Out, retry=2)
        print("xong", rows[n]["edit_id"], "OK" if r else "FAIL", flush=True)
        return r

    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(work, jobs))
    for (n, c), r in zip(jobs, res):
        k = rows[n]["type"]
        rows[n]["sentence_past"] = r["sentence_past"] if r else None
        if k == "F" and r:
            rows[n]["real_value"], rows[n]["past_value"] = r["old_value"], r["new_value"]
        rows[n]["checks_failed"] = ["llm_fail"] if r is None else verify(k, c, r)
        if k == "E" and r:
            rows[n]["checks_failed"] += e_chunk_bad(get(c["page"])[c["ci"]], c["sentence"], r["sentence_past"], c["event"])
            rows[n]["regen"] = "e2"
        if rows[n]["edit_id"] in a.accept.split(","):
            rows[n]["accepted_by_hand"] = [x for x in rows[n]["checks_failed"] if x in ("over_edit", "no_ongoing_marker")]
            rows[n]["checks_failed"] = [x for x in rows[n]["checks_failed"] if x not in ("over_edit", "no_ongoing_marker")]
        rows[n]["model"] = a.model

    for g in (out / "chunks").glob("*.txt"):
        os.remove(g)
    edited = {}
    for r in rows:
        if not r["checks_failed"]:
            ch = next(c for c in get(r["page"]) if c["id"] == r["chunk_id"])
            edited.setdefault(r["page"], []).append(f"=== CHUNK {ch['id']}@past ===\n{ch['head']}\n" + ch["body"].replace(r["sentence_real"], r["sentence_past"], 1))
    for pg, blocks in edited.items():
        (out / "chunks" / f"{pg}.txt").write_text("\n".join(blocks) + "\n", encoding="utf-8")
    with open(f, "w", encoding="utf-8") as o:
        for r in rows:
            o.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("đạt kiểm:", sum(not r["checks_failed"] for r in rows), "/", len(rows), "| lỗi", dict(Counter(x for r in rows for x in r["checks_failed"])))
    write_metrics(a, out, "metrics_redo2", cache, t0, rows, len(jobs))


def gold_chunks(split: str) -> set[str]:
    """Chunk là bằng chứng của câu hỏi có sẵn: Cơ chế 1 (gold_chunk_ids) và Cơ chế 2 (evidence của mốc vàng được câu v9 dùng)."""
    g: set[str] = set()
    for c in json.loads((ORG / "questions" / "mech1" / split / f"{split}_subset.json").read_text(encoding="utf-8"))["cases"]:
        g |= set(c["gold_chunk_ids"])
    for f in (ORG / "questions" / "mech2" / split).glob("*.jsonl"):
        gf = ORG / "timeline_gold" / split / f"{f.stem}.json"
        if not gf.exists():
            continue
        ev = {e["id"]: e for e in json.loads(gf.read_text(encoding="utf-8"))["events"]}
        for line in filter(str.strip, f.read_text(encoding="utf-8").splitlines()):
            for i in json.loads(line).get("gold_event_ids", []):
                g |= {x["chunk_id"] for x in ev.get(i, {}).get("evidence", [])}
    return g


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", default="tune")
    ap.add_argument("--n", type=int, default=202, help="tổng số chỗ sửa")
    ap.add_argument("--page-frac", type=float, default=0.5, help="tỉ lệ trang bị đổi")
    ap.add_argument("--per-page", type=int, default=2)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--model", default="hy4-flash-free")
    ap.add_argument("--out", default=None)
    ap.add_argument("--redo", action="store_true", help="kiểm lại offline edits.jsonl bằng luật mới, gọi lại LLM chỉ cho chỗ E hỏng")
    ap.add_argument("--swap", default="", help="với --redo: edit_id (phẩy) bắt buộc thay bằng ứng viên khác thay vì thử lại")
    ap.add_argument("--accept", default="", help="với --redo: edit_id (phẩy) đã đọc tay, miễn lỗi over_edit (cắt đúng phần sau mốc kết thúc)")
    ap.add_argument("--regen-e", action="store_true", help="với --redo: sinh lại mọi chỗ E bằng prompt E mới (nêu rõ còn tiếp diễn) + kiểm mức chunk; cache riêng pastgen_e2_<model>")
    ap.add_argument("--from-current", action="store_true", help="với --redo: lấy edits.jsonl hiện tại làm gốc (lưu bản sao edits_prev.jsonl) thay vì bản lượt đầu")
    ap.add_argument("--no-llm", action="store_true", help="với --redo: chỉ kiểm offline, không gọi LLM")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    out = Path(a.out or ORG / "past" / a.split)
    if a.redo:
        return redo(a, out)
    pages = (ORG / f"pages_{a.split}.txt").read_text().split()
    rng.shuffle(pages)
    quota = {k: round(v * a.n / sum(QUOTA.values())) for k, v in QUOTA.items()}   # đều nhau theo QUOTA; chỉnh ở đây nếu cần
    gold = gold_chunks(a.split)
    # chọn E trước (ít ứng viên nhất): mỗi trang tối đa 1 E; rồi C, F, A lấp chỗ trống (mỗi trang tối đa per_page chỗ, chunk khác nhau)
    info = {}
    for p in pages:
        f = ORG / "graph" / a.split / "ingest_10b" / f"{p}.json"
        if f.exists():
            chunks = parse_chunks(ORG / "source" / a.split / "chunks" / f"{p}.txt")
            info[p] = (chunks, candidates(p, chunks, json.loads(f.read_text(encoding="utf-8"))["events"]))
    picked, taken, cnt, gcnt = [], {}, {k: 0 for k in QUOTA}, {k: 0 for k in QUOTA}

    def take(k, p):
        chunks, cand = info[p]
        pool = [c for c in cand[k] if c["ci"] not in taken.setdefault(p, set())]
        if not pool or cnt[k] >= quota[k] or len(taken[p]) >= a.per_page:
            return False
        want = gcnt[k] * 2 < cnt[k] + 1
        pref = [c for c in pool if (chunks[c["ci"]]["id"] in gold) == want] or pool
        c = rng.choice(pref)
        c["on_gold"] = chunks[c["ci"]]["id"] in gold
        picked.append((k, c, chunks)); taken[p].add(c["ci"]); cnt[k] += 1; gcnt[k] += c["on_gold"]
        return True

    for p in [p for p in pages if p in info and info[p][1]["E"]]:
        take("E", p)
    e_pages = [p for p in pages if p in taken]
    rest = [p for p in pages if p in info and p not in taken]
    for p in e_pages + rest:
        order = [k for k in QUOTA if k != "E"]
        rng.shuffle(order)
        for k in order:
            take(k, p)
    n_gold, npg = sum(c["on_gold"] for _, c, _ in picked), len({c["page"] for _, c, _ in picked})
    quota = {k: quota[k] - cnt[k] for k in quota}
    print("trang", npg, "| chỗ sửa", len(picked), {k: sum(1 for x in picked if x[0] == k) for k in QUOTA}, "| trên gold chunk", n_gold,
          "| thiếu quota", {k: v for k, v in quota.items() if v})
    if a.dry:
        return

    llm = chain = cache = Out = None
    if any(k != "C" for k, _, _ in picked):
        llm, chain, cache, Out = setup_llm(a)

    return finish(a, picked, rng, llm, chain, cache, Out, out)


def setup_llm(a):
    if True:
        from pydantic import BaseModel
        from tam.config.loader import load_config
        from tam.llm.cache import SqliteCache
        from tam.llm.factory import get_llm

        from pydantic import model_validator

        class Out(BaseModel):  # noqa: F811
            @model_validator(mode="before")
            @classmethod
            def _unwrap(cls, v):   # hy4 hay bọc kết quả trong {"properties": {...}} (giống schema); mở ra thay vì coi là JSON hỏng
                if isinstance(v, dict) and "sentence" not in v and isinstance(v.get("properties"), dict):
                    return v["properties"]
                return v

            sentence: str
            old_value: str | None = None
            new_value: str | None = None

        cfg = load_config()
        P = cfg.llm.profiles["opencode_deepseek_flash"]
        P._data["model_id"] = a.model
        hd = dict(P.get("default_headers") or {})
        hd[P["session_header"]] = f"pastgen-{a.split}-{int(time.time())}"
        P._data["default_headers"] = hd
        llm = get_llm(cfg, "opencode_deepseek_flash")
        chain = llm.with_structured_output(Out)
        cache = SqliteCache(ROOT / "data" / "llm_cache" / (f"pastgen_e2_{a.model}" if a.regen_e else f"pastgen_{a.model}") / "cache.sqlite", threadsafe=True)
        print("model", a.model, "| extra_body gửi đi:", P.get("extra_body"), "(hy4 bỏ qua trường này: thinking vẫn BẬT) | luồng", a.workers, flush=True)
        return llm, chain, cache, Out


def finish(a, picked, rng, llm, chain, cache, Out, out):
    t0 = time.time()

    # loại C làm trước bằng code (rng tuần tự); các loại còn lại gọi LLM song song
    pre = {n: shift_year(c, rng) for n, (k, c, _) in enumerate(picked) if k == "C"}

    def work(n: int):
        kind, c, chunks = picked[n]
        r = pre.get(n) or run_llm(kind, chunks[c["ci"]], c, llm, chain, cache, Out)
        print("xong", n + 1, "/", len(picked), kind, c["page"], "OK" if r else "FAIL", flush=True)
        return r

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(work, range(len(picked))))

    out.mkdir(parents=True, exist_ok=True)
    (out / "chunks").mkdir(exist_ok=True)
    rows, edited = [], {}
    for n, ((kind, c, chunks), r) in enumerate(zip(picked, results), 1):
        ch = chunks[c["ci"]]
        bad = ["llm_fail"] if r is None else verify(kind, c, r)
        if r and kind == "F":     # LLM: old_value = giá trị real, new_value = giá trị sai của bản cũ
            real_v, past_v = r["old_value"], r["new_value"]
        else:                     # C: old_value = giá trị bản cũ, new_value = giá trị real
            real_v, past_v = (r and r["new_value"]) if kind == "C" else None, (r and r["old_value"]) if kind == "C" else None
        row = dict(edit_id=f"{a.split}-{n:03d}", type=kind, page=c["page"], chunk_id=ch["id"], chunk_id_past=ch["id"] + "@past",
                   on_gold_chunk=c["on_gold"], sentence_real=c["sentence"], sentence_past=r["sentence_past"] if r else None,
                   event=c["event"], real_value=real_v, past_value=past_v, checks_failed=bad, model="code" if kind == "C" else a.model)
        rows.append(row)
        if not bad:
            body = ch["body"].replace(c["sentence"], r["sentence_past"], 1)
            edited.setdefault(c["page"], []).append(f"=== CHUNK {ch['id']}@past ===\n{ch['head']}\n{body}")
    for pg, blocks in edited.items():
        (out / "chunks" / f"{pg}.txt").write_text("\n".join(blocks) + "\n", encoding="utf-8")
    with open(out / "edits.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    from collections import Counter
    fails = Counter(x for r in rows for x in r["checks_failed"])
    print("đạt kiểm:", sum(not r["checks_failed"] for r in rows), "/", len(rows), "| lỗi", dict(fails), "->", out)
    write_metrics(a, out, "metrics", cache, t0, rows, sum(k != "C" for k, _, _ in picked))


if __name__ == "__main__":
    main()
