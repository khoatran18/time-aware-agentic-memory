"""Chấm kết quả `run_agent_search.py` trên bộ v9 (`dataset/eval/v9_graph_subset.json`) bằng `local/v9_score.py`. KHÔNG gọi LLM.

    python3 -I local/v9_agent_score.py <repo> <tên thư mục output> [<tên thư mục output> ...] [--detail]
Đáp án của agent là JSON {kind, number, events[{date,text}], evidence}; hỏng JSON hoặc không có câu trả lời = 0 điểm (đếm riêng).
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import v9_score as V

FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def parse_answer(text):
    """JSON trong câu trả lời (có thể bọc ```json ... ```, hoặc kèm chữ); trả dict hoặc None."""
    if not text:
        return None
    for cand in [*FENCE.findall(text), text]:
        try:
            v = json.loads(cand.strip())
            if isinstance(v, dict):
                return v
        except ValueError:
            pass
        m = re.search(r"\{.*\}", cand, re.S)
        if m:
            try:
                v = json.loads(m.group())
                if isinstance(v, dict):
                    return v
            except ValueError:
                pass
    return None


TL_LINE = re.compile(r"^\s*\d+\. (\S+) \[[^\]]*\] \S+ \(tier \d\) (.*) <([^>]*)>\s*$")


TL_COMPACT = re.compile(r"^\s*\d+\. (\d{4}(?:-\d\d){0,2}) (.*) <([^>]*)>\s*$")
TL_HEAD = re.compile(r"chunk ids are (/wiki/\S+)#n\)")


def seen_timeline_rows(tool_texts):
    """Các dòng mốc của công cụ `timeline` trong văn bản công cụ (dạng đầy đủ hoặc gọn): [(date, text, {chunk_id})]."""
    rows = []
    for _, t in tool_texts:
        h = TL_HEAD.search(t.split("\n", 1)[0])
        for line in t.splitlines():
            m = TL_LINE.match(line)
            if m:
                rows.append((m.group(1), m.group(2), {c.strip() for c in m.group(3).split(",") if c.strip()}))
            elif h and (m := TL_COMPACT.match(line)):
                rows.append((m.group(1), m.group(2), {h.group(1) + c.strip() for c in m.group(3).split(",") if c.strip()}))
    return rows


def coverage(exp_ids, E, tool_texts):
    """'Đủ mốc' cho agent, không gọi LLM. Trả (đủ theo dòng timeline, đủ theo chunk, đủ theo cả hai cách).
    Theo dòng timeline: luật content_map của local/ingest_eval/graph_eval.py (ngày tương thích và (Jaccard >= 0.15, hoặc >= 0.05 khi chung chunk)).
    Theo chunk: mọi chunk bằng chứng của mốc gold đều xuất hiện (nguyên chuỗi id) trong văn bản công cụ; lạc quan với grep/read_page cắt đoạn."""
    from tam.ingestion.events import post as ip
    rows, blob = seen_timeline_rows(tool_texts), "\n".join(t for _, t in tool_texts)
    tl_ok = ch_ok = True
    for i in exp_ids:
        g = E[i]
        gc = {x["chunk_id"] for x in g["evidence"]}
        hit = any(ip.compat(g["date"], d) and ((gc & cs and ip.jacc_u(g["text"], tx) >= 0.05) or ip.jacc_u(g["text"], tx) >= 0.15) for d, tx, cs in rows)
        tl_ok &= hit
        ch_ok &= any(c in blob for c in gc)
    return tl_ok, ch_ok


def main():
    repo, runs = sys.argv[1], [a for a in sys.argv[2:] if not a.startswith("--")]
    detail = "--detail" in sys.argv
    sys.path.insert(0, str(Path(repo) / "src"))
    qs = {q["qid"]: q for q in V.load_questions(repo)}
    gold = {}
    print(f"{'run':<24}{'type':<17}{'n':>4}{'exact':>7}{'f1':>7}{'prec':>7}{'rec':>7}{'order':>7}{'noans':>6}{'badjson':>8}{'cov_tl':>7}{'cov_ch':>7}")
    for name in runs:
        rows = [json.loads(l) for l in open(Path(repo) / "output" / name / "results.jsonl", encoding="utf-8")]
        agg = defaultdict(list)
        tt_file = Path(repo) / "output" / name / "tool_texts.jsonl"
        tts = {j["idx"]: j["tool_texts"] for j in map(json.loads, open(tt_file, encoding="utf-8"))} if tt_file.exists() else {}
        for r in rows:
            q = qs[r["idx"]]
            E = gold.setdefault(q["page"], V.load_gold(repo, q["page"]))
            exp = V.expected(q, E)
            ans = parse_answer(r["answer"])
            if exp["kind"] == "number":
                pred = None if ans is None else ans.get("number")
            else:
                pred = None if ans is None else ans.get("events")
            s = V.score(exp, pred)
            if r["idx"] in tts:
                ids = q["answer_ids"] if q["type"] == "first_last_next" else q["gold_event_ids"]
                s["cov_tl"], s["cov_ch"] = (float(x) for x in coverage(ids, E, tts[r["idx"]]))
            s.update(noans=r["answer"] is None, badjson=r["answer"] is not None and ans is None, steps=r["steps"])
            agg[q["type"]].append(s)
            agg["ALL"].append(s)
            if detail and s["exact"] != 1.0:
                print(f"   {r['idx']:<34}{q['type']:<16}f1={s.get('f1', 0):.2f} exact={s['exact']:.0f} steps={r['steps']} stop={r['stop_reason']}")
        for t in ["first_last_next", "list", "order_gap", "summary", "ALL"]:
            v = agg.get(t)
            if not v:
                continue
            m = lambda k: (lambda xs: sum(xs) / len(xs) if xs else float('nan'))([x[k] for x in v if k in x])  # f1/prec/rec/order không có ở câu order_gap
            print(f"{name:<24}{t:<17}{len(v):>4}{m('exact'):>7.3f}{m('f1'):>7.3f}{m('precision'):>7.3f}{m('recall'):>7.3f}{m('order'):>7.3f}{sum(x['noans'] for x in v):>6}{sum(x['badjson'] for x in v):>8}{m('cov_tl'):>7.3f}{m('cov_ch'):>7.3f}")


if __name__ == "__main__":
    main()
