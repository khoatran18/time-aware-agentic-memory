"""Sinh câu hỏi riêng cho các chỗ sửa của bản quá khứ (Cơ chế 3). Thiết kế: docs/decisions/16_MECH3_PAST_VERSION_DESIGN.md.

Mỗi chỗ sửa (edits.jsonl) -> 2-3 câu hỏi do LLM viết, đáp án bám nhãn của chỗ sửa, kiểm bằng code:
  E: current (X còn ... không? -> không, kết thúc năm D), historical (năm Y trước D: còn ... không? -> có), when (kết thúc khi nào? -> D)
  F: direct (hỏi giá trị đúng), verify_false ("có phải <giá trị sai> không?" -> không, là <giá trị đúng>)
  C: year (năm nào?), verify_false ("có phải năm <năm sai> không?" -> không)
  A: direct, direct2 (đối chứng: đáp án không đổi giữa bản cũ và real)
Chạy: python scripts/make_past_questions.py --split tune --n 20 --workers 20   (--n: số chỗ sửa thử, cân bằng theo loại; 0 = tất cả)
LLM: OpenCode hy4-flash-free (thinking BẬT, hy4 bỏ qua thinking:disabled); cache data/llm_cache/pastq_<model>/. Prompt bằng tiếng Anh.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import make_past as mp  # noqa: E402

ORG = mp.ORG
norm = mp.norm
KINDS = {"E": ["current", "historical", "when"], "F": ["direct", "verify_false"], "C": ["year", "verify_false"], "A": ["direct", "direct2", "direct3", "direct4"]}

SPEC = {
    "E": ("The edited fact is an ENDING: in the NEWEST version the situation ended (end date: {end}); an OLDER version still described it as ongoing. "
          "Write exactly 3 questions about the situation described by the TARGET sentence:\n"
          "- kind=current: ask whether the situation is still the case NOW (do not mention the end date). Answer: No, plus the end date.\n"
          "- kind=historical: ask whether it was the case in {asof} (mention that year in the question). Answer: Yes.\n"
          "- kind=when: ask when it ended (do not mention the end date). Answer: the end date ({end})."),
    "F": ("The TARGET sentence in the NEWEST version states '{real}'. An older version wrongly said '{past}'. Write exactly 2 questions:\n"
          "- kind=direct: ask a question whose answer is '{real}' (do NOT mention '{real}' or '{past}' in the question). Answer: {real}.\n"
          "- kind=verify_false: a yes/no question asserting the WRONG value '{past}' (it must contain '{past}'). Answer: No, followed by the right value '{real}'."),
    "C": ("The TARGET sentence in the NEWEST version has the year {real}. An older version wrongly said {past}. Write exactly 2 questions:\n"
          "- kind=year: ask in which year the event of the TARGET sentence happened (do NOT mention {real} or {past}). Answer: {real}.\n"
          "- kind=verify_false: a yes/no question asserting the WRONG year {past} (it must contain {past}). Answer: No, followed by the right year {real}."),
    "A": ("The TARGET sentence was only reworded in the older version (no fact changed). Write exactly 4 factual questions answerable from the TARGET sentence "
          "(kind=direct, direct2, direct3, direct4), each about a DIFFERENT detail. Prefer SPECIFIC, obscure details that a person could not guess without reading the "
          "passage: exact numbers, dates, quantities, minor names, places of minor events. Avoid the page's headline fact and anything a well-informed person already knows. "
          "Each question must name its subject with the full proper name (never 'a diplomat', 'the club', 'his suit', or a bare surname), must have ONE short answer "
          "(no lists, no 'which years/subjects'), and must not depend on an unstated date. Give the short answer exactly as it appears in the sentence."),
}


MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def nice_date(d: str) -> str:
    """2009-01 -> 'January 2009'; 2009-01-05 -> '5 January 2009'; 2009 -> '2009'."""
    p = d.split("-")
    if len(p) == 3:
        return f"{int(p[2])} {MONTHS[int(p[1]) - 1]} {p[0]}"
    return f"{MONTHS[int(p[1]) - 1]} {p[0]}" if len(p) == 2 else p[0]


def build_prompt(r: dict, chunk: dict) -> list[tuple[str, str]]:
    """Lời nhắc gửi LLM cho một chỗ sửa (tiếng Anh)."""
    t = r["type"]
    ev = r["event"]
    ctx = dict(end=nice_date(ev["date"]) if ev.get("date") else None, real=r.get("real_value"), past=r.get("past_value"), asof=asof_year(r))
    marked = chunk["body"].replace(r["sentence_real"], f"<<TARGET>> {r['sentence_real']} <</TARGET>>", 1)
    page = r["page"].replace("_", " ")
    sys_p = ("You write evaluation questions for a memory system about Wikipedia pages. " + SPEC[t].format(**ctx) +
             "\nQuestions must read like what a curious person would naturally ask (no contorted phrasing). Every question must be self-contained: name the person/organisation/place it is about (the page is '" + page +
             "'), never say 'the sentence', 'the passage' or 'this text', keep it under 25 words (short, plain wording; do not paraphrase the sentence, ask the way a reader who has not read it would) and end with '?'. Answers are short."
             "\nReturn only a JSON object: {\"questions\": [{\"kind\": ..., \"question\": ..., \"answer\": ...}, ...]}.")
    return [("system", sys_p), ("human", f"Page: {page}\nSection: {chunk['head']}\n\nPassage (newest version):\n{marked}")]


def asof_year(r: dict) -> str | None:
    """Năm mốc cho câu 'historical' của loại E: năm trước năm kết thúc (code tính, không để LLM tự chọn)."""
    if r["type"] != "E":
        return None
    return str(int(r["event"]["date"][:4]) - 1)


def check(r: dict, q: dict) -> list[str]:
    """Kiểm bằng code một câu hỏi: lộ đáp án, đáp án thiếu giá trị nhãn, câu hỏi tự thân..."""
    t, k = r["type"], q.get("kind")
    qs, ans = q.get("question", ""), q.get("answer", "")
    bad = []
    if k not in KINDS[t]:
        bad.append("kind")
    if not qs.strip().endswith("?") or not 4 <= len(qs.split()) <= 30:
        bad.append("form")
    caps = [w for w in re.findall(r"[A-Z][\w'’.-]{2,}", qs)[1:] if w.lower() not in {"yes", "no"}]
    pool = r["page"].replace("_", " ") + " " + r["sentence_real"]
    if not any(w.strip(".'’") in pool for w in caps) and not any(w in pool for w in re.findall(r"[A-Z][\w'’-]{2,}", qs)):
        bad.append("no_entity")
    if t == "E" and k == "current" and not re.search(r"\b(still|currently|now|today|anymore|present)\b", qs, re.I):
        bad.append("current_word")
    if not ans.strip():
        bad.append("no_answer")
    if re.search(r"\b(the|this) (sentence|passage|text)\b", qs, re.I):
        bad.append("not_self_contained")
    real, past = r.get("real_value"), r.get("past_value")
    end = r["event"]["date"][:4] if t == "E" else None
    n_q, n_a = norm(qs), norm(ans)
    if t == "F":
        if k == "direct" and (norm(real) in n_q or norm(past) in n_q):
            bad.append("leak")
        if k == "direct" and norm(real) not in n_a:
            bad.append("answer_missing_real")
        if k == "verify_false" and (norm(past) not in n_q or norm(real) not in n_a or not ans.strip().lower().startswith("no")):
            bad.append("verify_false")
    if t == "C":
        if k == "year" and (real in qs or past in qs):
            bad.append("leak")
        if k == "year" and real not in ans:
            bad.append("answer_missing_real")
        if k == "verify_false" and (past not in qs or real not in ans or not ans.strip().lower().startswith("no")):
            bad.append("verify_false")
    if t == "E":
        if k in ("current", "when") and end in qs:
            bad.append("leak")
        if k in ("current", "when") and end not in ans:
            bad.append("answer_missing_end")
        if k == "current" and not ans.strip().lower().startswith("no"):
            bad.append("answer_polarity")
        if k == "historical" and (asof_year(r) not in qs or not ans.strip().lower().startswith("yes")):
            bad.append("historical")
    if t == "A":
        def cov(txt: str) -> float:
            w = [x for x in re.findall(r"\w+", ans.lower()) if len(x) > 2]
            return sum(x in txt.lower() for x in w) / len(w) if w else 0.0
        if cov(r["sentence_real"]) < 0.7:
            bad.append("answer_not_in_real")
        if cov(r["sentence_past"]) < 0.7:
            bad.append("answer_not_in_past")
    return bad


# kỳ vọng trạng thái sau khi nạp real lên bản cũ: chunk nào phải còn hiệu lực, chunk nào là bản lỗi thời (không được trả như sự thật hiện tại)
def expect(r: dict, kind: str) -> dict:
    cur, past = r["chunk_id"], r["chunk_id_past"]
    if r["type"] == "E":
        return dict(valid_now=cur, stale_now=past, past_also_valid=(kind == "historical"), note="past chunk true until end_time, closed by real")
    if r["type"] in ("F", "C"):
        return dict(valid_now=cur, stale_now=past, past_also_valid=False, note="past chunk wrong from the start -> invalidated_at")
    return dict(valid_now=cur, stale_now=None, past_also_valid=True, note="reworded: neither version may be closed or invalidated")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", default="tune")
    ap.add_argument("--n", type=int, default=20, help="số chỗ sửa (cân bằng theo loại); 0 = tất cả")
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--model", default="hy4-flash-free")
    ap.add_argument("--out", default=None)
    ap.add_argument("--types", default="CEFA", help="chỉ sinh cho các loại này (vd A)")
    a = ap.parse_args()
    out = Path(a.out or ORG / "past" / a.split / ("questions.jsonl" if a.n == 0 else "questions_pilot.jsonl"))
    rows = [json.loads(x) for x in (ORG / "past" / a.split / "edits.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    rows = [r for r in rows if not r["checks_failed"] and r["type"] in a.types]
    if a.n:
        per = a.n // 4
        pick = []
        for t in "EFCA":
            pick += [r for r in rows if r["type"] == t][::max(1, len([r for r in rows if r["type"] == t]) // per)][:per]
        rows = pick
    t0 = time.time()

    from pydantic import BaseModel, model_validator
    from tam.config.loader import load_config
    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured

    class Q(BaseModel):
        kind: str
        question: str
        answer: str

    class Out(BaseModel):  # noqa: F811
        @model_validator(mode="before")
        @classmethod
        def _unwrap(cls, v):   # hy4 hay bọc kết quả trong {"properties": {...}}
            if isinstance(v, dict) and "questions" not in v and isinstance(v.get("properties"), dict):
                return v["properties"]
            return v

        questions: list[Q]

    cfg = load_config()
    P = cfg.llm.profiles["opencode_deepseek_flash"]
    P._data["model_id"] = a.model
    hd = dict(P.get("default_headers") or {})
    hd[P["session_header"]] = f"pastq-{a.split}-{int(time.time())}"
    P._data["default_headers"] = hd
    llm = get_llm(cfg, "opencode_deepseek_flash")
    chain = llm.with_structured_output(Out)
    cache = SqliteCache(ROOT / "data" / "llm_cache" / f"pastq_{a.model}" / "cache.sqlite", threadsafe=True)
    print("model", a.model, "| thinking BẬT (hy4 bỏ qua thinking:disabled) | luồng", a.workers, "| chỗ sửa", len(rows), flush=True)

    chunks_of: dict[str, list] = {}

    def work(r: dict):
        ch = chunks_of.setdefault(r["page"], mp.parse_chunks(ORG / "source" / a.split / "chunks" / f"{r['page']}.txt"))
        chunk = next(c for c in ch if c["id"] == r["chunk_id"])
        res = invoke_structured(llm, chain, Out, build_prompt(r, chunk), max_attempts=3, cache=cache)
        print("xong", r["edit_id"], r["type"], "OK" if res else "FAIL", flush=True)
        return res

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(work, rows))

    out.parent.mkdir(parents=True, exist_ok=True)
    n_q = n_ok = 0
    fails: Counter = Counter()
    with open(out, "w", encoding="utf-8") as f:
        for r, res in zip(rows, results):
            qs = [q.model_dump() for q in res.questions] if res else []
            kinds = Counter(q["kind"] for q in qs)
            for i, q in enumerate(qs, 1):
                bad = check(r, q)
                if res and kinds != Counter(KINDS[r["type"]]):
                    bad.append("kinds_set")
                n_q += 1
                n_ok += not bad
                fails.update(bad)
                f.write(json.dumps(dict(
                    qid=f"{r['edit_id']}-q{i}", edit_id=r["edit_id"], type=r["type"], page=r["page"], kind=q["kind"], question=q["question"],
                    answer=q["answer"], as_of=asof_year(r), real_value=r.get("real_value"), past_value=r.get("past_value"),
                    end_date=r["event"]["date"] if r["type"] == "E" else None, on_gold_chunk=r["on_gold_chunk"], expect=expect(r, q["kind"]), checks_failed=bad, model=a.model),
                    ensure_ascii=False) + "\n")
            if not res:
                fails["llm_fail"] += 1
    m = dict(run="questions", model=a.model, thinking="BẬT", workers=a.workers, cache_dir=f"data/llm_cache/pastq_{a.model}",
             edits=len(rows), llm_fail=sum(r is None for r in results), questions=n_q, passed=n_ok, fails=dict(fails),
             cache_hits=cache.hits, cache_misses=cache.misses, wall_s=round(time.time() - t0, 1))
    out.with_suffix(".metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print("METRICS", json.dumps(m, ensure_ascii=False), "->", out, flush=True)


if __name__ == "__main__":
    main()
