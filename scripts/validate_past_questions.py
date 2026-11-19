"""Kiểm độc lập câu hỏi của chỗ sửa bằng cách cho LLM (hy4) TRẢ LỜI chúng, đáp án so với gold bằng code.
Mỗi chỗ sửa 3 lần gọi (tất cả câu hỏi của chỗ sửa gộp một lần):
  real   : chỉ kèm chunk bản real     -> phải khớp gold (câu rõ, đáp án đúng)
  past   : chỉ kèm chunk bản quá khứ  -> E current/when, F/C phải SAI (phân biệt được); E historical, A phải ĐÚNG
  closed : không kèm chunk            -> câu kiểu giá trị (không phải có/không) mà vẫn đúng = trả lời được bằng kiến thức sẵn, không đo bộ nhớ
Câu giữ lại: real_ok và past đúng kỳ vọng và không closed_leak.
Chạy: python scripts/validate_past_questions.py --split tune --in questions_pilot.jsonl --workers 20
LLM: hy4-flash-free (thinking BẬT), cache data/llm_cache/pastv_<model>/. Prompt tiếng Anh.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import make_past as mp  # noqa: E402

ORG = mp.ORG
POLAR = {("E", "current"), ("E", "historical"), ("F", "verify_false"), ("C", "verify_false")}


def match(q: dict, ans: str) -> bool:
    """Đáp án mô hình khớp gold? Câu có/không: so cực tính; câu giá trị: phủ ≥70% từ của đáp án gold (hoặc có năm kết thúc cho E when)."""
    a = (ans or "").strip().lower()
    g = q["answer"].lower()
    if a.startswith("unknown") or not a:
        return False
    if (q["type"], q["kind"]) in POLAR:
        return a.startswith(g.split(",")[0].split(".")[0].strip()[:3]) and (a.startswith("yes") == g.startswith("yes"))
    if q["type"] == "E" and q["kind"] == "when":
        return str(q["end_date"])[:4] in a
    w = [x for x in re.findall(r"\w+", g) if len(x) > 2 or x.isdigit()] or re.findall(r"\w+", g)   # số ngắn (52, 17) phải khớp
    return bool(w) and sum(x.rstrip("s") in a for x in w) / len(w) >= 0.7   # "NBCs" (token hóa) khớp "NBC"


def expected_past(q: dict) -> bool:
    """Với chunk bản quá khứ, đáp án gold có còn khớp không (True = phải khớp)."""
    return bool(q["expect"]["past_also_valid"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", default="tune")
    ap.add_argument("--in", dest="inp", default="questions_pilot.jsonl")
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--model", default="hy4-flash-free")
    a = ap.parse_args()
    d = ORG / "past" / a.split
    qs = [json.loads(x) for x in (d / a.inp).read_text(encoding="utf-8").splitlines() if x.strip()]
    ed = {json.loads(x)["edit_id"]: json.loads(x) for x in (d / "edits.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()}
    by = defaultdict(list)
    for q in qs:   # câu có evidence_chunk (chunk khác của cùng trang, A) tách nhóm riêng: dùng đúng chunk đó cho cả real và past (chunk không bị sửa)
        by[q["edit_id"] + ("#" + q["evidence_chunk"] if q.get("evidence_chunk") else "")].append(q)
    t0 = time.time()

    from pydantic import BaseModel, model_validator
    from tam.config.loader import load_config
    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured

    class A(BaseModel):
        i: int
        answer: str

    class Out(BaseModel):
        @model_validator(mode="before")
        @classmethod
        def _unwrap(cls, v):
            if isinstance(v, dict) and "answers" not in v and isinstance(v.get("properties"), dict):
                return v["properties"]
            return v

        answers: list[A]

    cfg = load_config()
    P = cfg.llm.profiles["opencode_deepseek_flash"]
    P._data["model_id"] = a.model
    hd = dict(P.get("default_headers") or {})
    hd[P["session_header"]] = f"pastv-{a.split}-{int(time.time())}"
    P._data["default_headers"] = hd
    llm = get_llm(cfg, "opencode_deepseek_flash")
    chain = llm.with_structured_output(Out)
    cache = SqliteCache(ROOT / "data" / "llm_cache" / f"pastv_{a.model}" / "cache.sqlite", threadsafe=True)
    print("model", a.model, "| thinking BẬT | luồng", a.workers, "| chỗ sửa", len(by), "| câu hỏi", len(qs), flush=True)

    import threading
    lock = threading.Lock()
    chunks: dict[str, list] = {}
    past_chunks: dict[str, dict] = {}

    def passage(eid: str, mode: str) -> str | None:
        eid, _, evc = eid.partition("#")
        r = ed[eid]
        if mode == "closed":
            return None
        with lock:
            if r["page"] not in past_chunks:
                pf = d / "chunks" / f"{r['page']}.txt"
                chunks[r["page"]] = mp.parse_chunks(ORG / "source" / a.split / "chunks" / f"{r['page']}.txt")
                past_chunks[r["page"]] = {c["id"]: c for c in mp.parse_chunks(pf)} if pf.exists() else {}
        if evc:
            c = next(c for c in chunks[r["page"]] if c["id"] == evc)
        elif mode == "real":
            c = next(c for c in chunks[r["page"]] if c["id"] == r["chunk_id"])
        else:
            c = past_chunks[r["page"]][r["chunk_id_past"]]
        return f"Section: {c['head']}\n{c['body']}"

    def ask(eid: str, mode: str):
        r = ed[eid.partition("#")[0]]
        items = by[eid]
        listing = "\n".join(f"{i}. {q['question']}" for i, q in enumerate(items, 1))
        page = r["page"].replace("_", " ")
        if mode == "closed":
            sys_p = ("Answer each question from your own knowledge only (no document is given). If you are not sure, answer UNKNOWN. "
                     "Short answers. Yes/no questions: begin with Yes or No.")
            human = f"Topic: {page}\n\nQuestions:\n{listing}"
        else:
            sys_p = ("Answer each question using ONLY the passage below. If the passage does not contain the answer, answer UNKNOWN. "
                     "Short answers. Yes/no questions: begin with Yes or No.")
            human = f"Topic: {page}\n\nPassage:\n{passage(eid, mode)}\n\nQuestions:\n{listing}"
        sys_p += " Return only a JSON object: {\"answers\": [{\"i\": 1, \"answer\": ...}, ...]}."
        res = invoke_structured(llm, chain, Out, [("system", sys_p), ("human", human)], max_attempts=3, cache=cache)
        got = {x.i: x.answer for x in res.answers} if res else {}
        print("xong", eid, mode, "OK" if res else "FAIL", flush=True)
        return eid, mode, got

    from concurrent.futures import ThreadPoolExecutor
    jobs = [(e, m) for e in by for m in ("real", "past", "closed")]
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(lambda j: ask(*j), jobs))
    ans = {(e, m): g for e, m, g in res}

    out_rows, st = [], Counter()
    for eid, items in by.items():
        for i, q in enumerate(items, 1):
            ar, ap_, ac = ans[(eid, "real")].get(i), ans[(eid, "past")].get(i), ans[(eid, "closed")].get(i)
            real_ok = match(q, ar)
            past_ok = match(q, ap_)
            polar = (q["type"], q["kind"]) in POLAR
            closed_ok = match(q, ac)
            flags = []
            if not real_ok:
                flags.append("real_wrong")
            unknown_past = (ap_ or "UNKNOWN").strip().lower().startswith("unknown")
            if past_ok != expected_past(q) and not (q["type"] == "E" and q["kind"] == "historical" and unknown_past):
                # E historical: bản cũ chỉ còn câu "đang tiếp diễn" (không còn năm) nên UNKNOWN là hợp lệ; chỉ sai khi trả lời trái gold
                flags.append("past_not_as_expected")
            if not polar and closed_ok:
                flags.append("closed_leak")
            out_rows.append(dict(q, answer_real_model=ar, answer_past_model=ap_, answer_closed_model=ac, real_ok=real_ok, past_ok=past_ok,
                                 closed_ok=closed_ok, validation_failed=flags))
            st["tổng"] += 1
            st["giữ"] += not flags
            for f in flags:
                st[f] += 1
                st[f"{f}:{q['type']}/{q['kind']}"] += 1
    out = d / (Path(a.inp).stem + ".validated.jsonl")
    DROP = {("E", "when")}   # mô hình trả lời được bằng kiến thức sẵn (closed_leak ~50%), không đo trí nhớ -> bỏ khỏi bộ chấm
    final = [r for r in out_rows if not r["validation_failed"] and (r["type"], r["kind"]) not in DROP]
    fin = d / (Path(a.inp).stem + ".final.jsonl")
    fin.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in final) + "\n", encoding="utf-8")
    cov = Counter(r["type"] for r in {x["edit_id"]: x for x in final}.values())
    st["final"] = len(final)
    for t in "CEFA":
        st[f"final:{t}"] = sum(r["type"] == t for r in final)
        st[f"chỗ sửa còn câu:{t}"] = cov[t]
    with open(out, "w", encoding="utf-8") as f:
        for r in out_rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    m = dict(run="validate", model=a.model, thinking="BẬT", workers=a.workers, cache_dir=f"data/llm_cache/pastv_{a.model}", calls=len(jobs),
             cache_hits=cache.hits, cache_misses=cache.misses, wall_s=round(time.time() - t0, 1), stats=dict(st))
    out.with_suffix(".metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print("METRICS", json.dumps(m, ensure_ascii=False), "->", out, flush=True)


if __name__ == "__main__":
    main()
