"""Kiểm lại bộ câu hỏi đã giữ (questions.final.jsonl) của một tập: thống kê + kiểm offline bằng code + kiểm MƠ HỒ bằng LLM (hy4).
Mơ hồ = câu hỏi đứng một mình (KHÔNG kèm tên trang/đoạn) có chỉ rõ một thực thể/sự kiện và có đáp án duy nhất không.
Chạy: python scripts/audit_questions.py --split tune [--no-llm] [--workers 30]
Ra: <tập>/questions.audit.jsonl, <tập>/questions.audit.metrics.json. LLM: hy4-flash-free (thinking BẬT), cache data/llm_cache/pastamb_<model>/. Prompt tiếng Anh.
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


def load(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()] if p.exists() else []


def offline(R: list[dict]) -> dict:
    """Kiểm bằng code trên câu đã giữ: trùng câu, đáp án lộ trong câu, dấu vết token hóa, câu dài, thiếu tên riêng."""
    seen, dup = Counter(r["question"].strip().lower() for r in R), 0
    out = Counter()
    flags: dict[tuple, list] = defaultdict(list)
    for r in R:
        q, a = r["question"], r["answer"]
        key = (r["edit_id"], r["kind"])
        if seen[q.strip().lower()] > 1:
            flags[key].append("duplicate")
        if re.search(r"[A-Z]{2,}s\b(?=\s[A-Z])| ,| \.|\( | \)| ;|\w ' s\b", q):
            flags[key].append("tokenised")
        if len(q.split()) > 25:
            flags[key].append("long")
        names = re.findall(r"[A-Z][\w'’.-]{2,}", q)[1:]   # bỏ từ đầu câu
        if not names and not re.search(r"\b\d{4}\b", q):
            flags[key].append("no_proper_noun")
        if r["type"] in ("F", "C", "E") and r["kind"] not in ("verify_false", "current", "historical"):
            core = re.sub(r"^no[,;. ]*", "", a.strip().lower())
            if core and len(core) > 3 and core in q.lower():
                flags[key].append("answer_in_question")
    for k, v in flags.items():
        for f in set(v):
            out[f] += 1
    return dict(out), {f"{k[0]}/{k[1]}": sorted(set(v)) for k, v in flags.items()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--split", default="tune")
    ap.add_argument("--workers", type=int, default=30)
    ap.add_argument("--model", default="hy4-flash-free")
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--prefix", default="questions", help="tên gốc các file (vd questions_A2)")
    a = ap.parse_args()
    d = ORG / "past" / a.split
    raw = load(d / f"{a.prefix}.jsonl")
    val = load(d / f"{a.prefix}.validated.jsonl")
    fin = load(d / f"{a.prefix}.final.jsonl")
    ed = load(d / "edits.jsonl")
    print(f"== {a.split}: chỗ sửa {len(ed)} {dict(Counter(r['type'] for r in ed))} | câu sinh {len(raw)} | qua kiểm LLM-trả-lời {len(val) - sum(bool(r['validation_failed']) for r in val)} | câu giữ (final) {len(fin)}")
    if not fin:
        print("  (chưa có câu hỏi)")
        return
    print("  final theo loại/kind:", dict(Counter(f"{r['type']}/{r['kind']}" for r in fin)))
    print("  chỗ sửa còn ≥1 câu:", {t: len({r["edit_id"] for r in fin if r["type"] == t}) for t in "CEFA"})
    off, per = offline(fin)
    print("  kiểm offline (số câu dính cờ):", off or "không có")
    if a.no_llm:
        return

    from pydantic import BaseModel, model_validator
    from tam.config.loader import load_config
    from tam.llm.cache import SqliteCache
    from tam.llm.factory import get_llm
    from tam.llm.structured import invoke_structured

    class J(BaseModel):
        i: int
        self_contained: bool
        unique_answer: bool
        reason: str = ""

    class Out(BaseModel):
        @model_validator(mode="before")
        @classmethod
        def _unwrap(cls, v):
            if isinstance(v, dict) and "judgements" not in v and isinstance(v.get("properties"), dict):
                return v["properties"]
            return v

        judgements: list[J]

    cfg = load_config()
    P = cfg.llm.profiles["opencode_deepseek_flash"]
    P._data["model_id"] = a.model
    hd = dict(P.get("default_headers") or {})
    hd[P["session_header"]] = f"pastamb-{a.split}-{int(time.time())}"
    P._data["default_headers"] = hd
    llm = get_llm(cfg, "opencode_deepseek_flash")
    chain = llm.with_structured_output(Out)
    cache = SqliteCache(ROOT / "data" / "llm_cache" / f"pastamb_{a.model}" / "cache.sqlite", threadsafe=True)
    sysp = ("You audit evaluation questions that will be asked to a retrieval system over a large Wikipedia corpus, WITHOUT any page title or passage. "
            "For each numbered question decide two things using only the question text:\n"
            "- self_contained: true only if a reader who has seen nothing else can tell exactly which specific person/organisation/place/event the question is about "
            "(a generic phrase such as 'a diplomat', 'the club', 'the company' with no proper name makes it NOT self-contained).\n"
            "- unique_answer: true only if the question has one short correct answer (not several equally plausible answers, not a list, not dependent on an unstated date).\n"
            "Give a short reason when either is false. Return only JSON: {\"judgements\": [{\"i\": 1, \"self_contained\": true, \"unique_answer\": true, \"reason\": \"\"}, ...]}.")
    by = defaultdict(list)
    for r in fin:
        by[r["edit_id"]].append(r)
    t0 = time.time()

    def judge(eid: str):
        items = by[eid]
        human = "Questions:\n" + "\n".join(f"{i}. {q['question']}" for i, q in enumerate(items, 1))
        res = invoke_structured(llm, chain, Out, [("system", sysp), ("human", human)], max_attempts=3, cache=cache)
        got = {x.i: x for x in res.judgements} if res else {}
        return eid, got

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(a.workers) as ex:
        res = dict(ex.map(judge, list(by)))
    rows, st = [], Counter()
    for eid, items in by.items():
        for i, q in enumerate(items, 1):
            j = res[eid].get(i)
            sc, ua = (j.self_contained, j.unique_answer) if j else (None, None)
            rows.append(dict(edit_id=eid, type=q["type"], kind=q["kind"], question=q["question"], answer=q["answer"], self_contained=sc, unique_answer=ua,
                             reason=(j.reason if j else "judge_fail"), offline_flags=per.get(f"{eid}/{q['kind']}", [])))
            st["tổng"] += 1
            st["không_đánh_giá_được"] += j is None
            st["self_contained_false"] += sc is False
            st["unique_answer_false"] += ua is False
            st["ổn(cả hai true)"] += bool(sc and ua)
            st[f"mơ hồ:{q['type']}"] += not (sc and ua)
    # bộ sạch: bỏ câu mơ hồ. E/current luôn mang "still/now" (tương đối theo T_now, hệ thống truyền giờ hiện tại) nên chỉ đòi self_contained, không đòi unique_answer.
    ok = {(r["edit_id"], r["question"]) for r in rows if r["self_contained"] and (r["unique_answer"] or (r["type"], r["kind"]) == ("E", "current"))}
    clean = [r for r in fin if (r["edit_id"], r["question"]) in ok]
    (d / f"{a.prefix}.clean.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in clean) + "\n", encoding="utf-8")
    st["clean"] = len(clean)
    for t in "CEFA":
        st[f"clean:{t}"] = sum(r["type"] == t for r in clean)
        st[f"clean chỗ sửa:{t}"] = len({r["edit_id"] for r in clean if r["type"] == t})
    p = d / f"{a.prefix}.audit.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    m = dict(run="audit", model=a.model, thinking="BẬT", cache_dir=f"data/llm_cache/pastamb_{a.model}", calls=len(by), cache_hits=cache.hits,
             cache_misses=cache.misses, wall_s=round(time.time() - t0, 1), offline=off, stats=dict(st))
    p.with_suffix(".metrics.json").write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding="utf-8")
    print("  METRICS", json.dumps(m, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
