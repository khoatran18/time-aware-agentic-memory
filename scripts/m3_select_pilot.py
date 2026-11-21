"""Cơ chế 3, pilot: chọn chỗ sửa của tune, dựng cửa sổ ingest và nhóm câu hỏi cơ chế 2. Không gọi LLM, không đụng kho.

Quy tắc chọn (cố định trước khi chạy): chỉ lấy chỗ sửa có ít nhất một câu cơ chế 2 "đích" (gold event có bằng chứng ở chunk sửa
và cùng ngày với sự kiện bị sửa); mỗi trang một chỗ sửa; N chỗ sửa mỗi loại C/E/F/A, ngẫu nhiên theo seed.
Cửa sổ: giống pass3_p10b.py (mục = các chunk liền nhau cùng tiêu đề; cắt từng khúc WINDOW chunk từ đầu mục).
Nhóm câu: dich (gold event ở chunk sửa, cùng ngày sự kiện sửa), cung_chunk (gold ở chunk sửa, ngày khác), cung_trang (còn lại).
Ghi: dataset/organized/m3_state/<tập>/pilot.json
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "dataset" / "organized"
WINDOW = 8  # pass3_p10b.py:18


def parse_chunks(path: Path) -> list[tuple[str, str]]:
    """[(chunk_id, tiêu đề mục)] theo thứ tự trong file (cùng cách pass3_p10b.parse)."""
    parts = re.split(r"^=== CHUNK (.+?) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    out = []
    for i in range(1, len(parts), 2):
        head = parts[i + 1].strip().split("\n", 1)[0]
        out.append((parts[i], (head.split(" | ", 1)[1] if " | " in head else "Lead").strip()))
    return out


def window_of(chunks: list[tuple[str, str]], cid: str) -> dict:
    secs: list[dict] = []
    for i, (c, t) in enumerate(chunks):
        if secs and secs[-1]["title"] == t:
            secs[-1]["idx"].append(i)
        else:
            secs.append({"title": t, "idx": [i]})
    for k, s in enumerate(secs):
        for w, lo in enumerate(range(0, len(s["idx"]), WINDOW)):
            ids = [chunks[i][0] for i in s["idx"][lo:lo + WINDOW]]
            if cid in ids:
                ctx = chunks[s["idx"][lo - 1]][0] if lo > 0 else None
                return {"section": k, "section_title": s["title"], "window": w, "chunk_ids": ids, "context_chunk": ctx}
    raise KeyError(cid)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", default="tune")
    ap.add_argument("--per-type", type=int, default=5)
    ap.add_argument("--seed", type=int, default=20261121)
    a = ap.parse_args()
    S = a.set

    edits = [json.loads(l) for l in (ORG / "past" / S / "edits.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    by_page = defaultdict(list)
    for e in edits:
        by_page[e["page"]].append(e)

    cand: dict[str, list[dict]] = defaultdict(list)
    for page, es in sorted(by_page.items()):
        gp, qp = ORG / "timeline_gold" / S / f"{page}.json", ORG / "questions" / "mech2" / S / f"{page}.jsonl"
        if not gp.exists() or not qp.exists():
            continue  # trang không có câu cơ chế 2
        gold = {ev["id"]: ev for ev in json.loads(gp.read_text(encoding="utf-8"))["events"]}
        qs = [json.loads(l) for l in qp.read_text(encoding="utf-8").splitlines() if l.strip()]
        for e in es:
            groups = {"dich": [], "cung_chunk": [], "cung_trang": []}
            edate = (e["event"] or {}).get("date") or ""
            for qi, q in enumerate(qs):
                hits = [gold[i] for i in q["gold_event_ids"] if i in gold and any(x["chunk_id"] == e["chunk_id"] for x in gold[i]["evidence"])]
                row = {"qi": qi, "type": q["type"], "question": q["question"]}
                if not hits:
                    groups["cung_trang"].append(row)
                elif any(h["date"][:4] == edate[:4] and edate for h in hits):
                    groups["dich"].append(row)
                else:
                    groups["cung_chunk"].append(row)
            if groups["dich"]:
                cand[e["type"]].append({"edit_id": e["edit_id"], "type": e["type"], "page": page, "chunk_id": e["chunk_id"],
                                        "event": e["event"], "groups": groups})

    rng = random.Random(a.seed)
    chosen, used = [], set()
    for t in "CEFA":
        pool = cand[t][:]
        rng.shuffle(pool)
        n = 0
        for c in pool:
            if c["page"] in used:
                continue
            used.add(c["page"])
            chosen.append(c)
            n += 1
            if n == a.per_type:
                break
    for c in chosen:
        ch = parse_chunks(ORG / "source" / S / "chunks" / f"{c['page']}.txt")
        c["window"] = window_of(ch, c["chunk_id"])
        c["n_chunks_page"] = len(ch)

    out = ORG / "m3_state" / S / "pilot.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"set": S, "seed": a.seed, "per_type": a.per_type, "window": WINDOW, "edits": chosen}, ensure_ascii=False, indent=1), encoding="utf-8")

    print("ứng viên (chỗ sửa có câu đích) theo loại:", {t: len(cand[t]) for t in "CEFA"})
    print("đã chọn:", len(chosen), "chỗ sửa trên", len({c['page'] for c in chosen}), "trang ->", out.relative_to(ROOT))
    tot = Counter()
    qt = Counter()
    for c in chosen:
        for g, rows in c["groups"].items():
            tot[g] += len(rows)
            if g == "dich":
                qt.update(r["type"] for r in rows)
    print("câu theo nhóm:", dict(tot), "| tổng", sum(tot.values()))
    print("câu đích theo loại câu:", dict(qt))
    print("cửa sổ (số chunk):", Counter(len(c["window"]["chunk_ids"]) for c in chosen))


if __name__ == "__main__":
    main()
