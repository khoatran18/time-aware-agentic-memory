"""Cơ chế 3: chỉ số trạng thái (không gọi LLM) cho các hệ cập nhật, theo từng chỗ sửa của pilot.

Với chỗ sửa có chunk X, câu bản cũ/mới (sentence_past/sentence_real trong past/<tập>/edits.jsonl), giá trị cũ/mới (C: năm, F: tên):
  stale_open   nút còn "mở" mang giá trị CŨ: chunk nguồn có X và (C: date bắt đầu bằng năm cũ; F: quote/text chứa giá trị cũ; E: quote chỉ có ở câu cũ
               mà không có ở câu mới; A: không đo). Nút đã có invalidated_at hoặc end_time đặt vì sửa thì tính vào stale_marked (cơ chế 3), không tính stale_open.
  new_present  có nút ở chunk X mang giá trị MỚI (C: date bắt đầu bằng năm mới; F: chứa giá trị mới; E: quote nằm trong câu mới mà không có trong câu cũ; A: tập (ngày, phase) của các nút ở chunk đổi không đổi so với bản cũ)
  lost_other   nút của bản cũ KHÔNG có chunk nguồn X mà biến mất (node_id) sau cập nhật  (đổi thừa)
  added_other  nút mới KHÔNG có chunk nguồn X mà bản cũ không có  (đổi thừa)
Dùng: m3_state_metrics.py [hệ ...] (mặc định old window_replace diff_replace); hệ = thư mục m3_state/<tập>/<hệ>/nodes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "dataset" / "organized"
M3 = os.environ.get("M3_STATE_NAME", "m3_state")  # thư mục trạng thái (mặc định m3_state; m3_state_ext cho đợt mở rộng)
norm = lambda s: re.sub(r"\s+", "", s or "").lower()


def load_nodes(S: str, system: str, page: str) -> list[dict]:
    return json.loads((ORG / M3 / S / system / "nodes" / f"{page}.json").read_text(encoding="utf-8"))


def judge(c: dict, e: dict, nodes: list[dict], old: list[dict]) -> dict:
    cid, t = c["chunk_id"], c["type"]
    sr, sp = norm(e["sentence_real"]), norm(e["sentence_past"])
    rv, pv = e.get("real_value"), e.get("past_value")
    at = [n for n in nodes if cid in n["cids"]]

    def is_old(n):
        if t == "C":
            return bool(pv) and n["date"].startswith(pv)
        if t == "F":
            return bool(pv) and norm(pv) in norm(n.get("quote") or "") + norm(n["text"]) and norm(pv) not in sr
        q = norm(n.get("quote"))
        return bool(q) and q in sp and q not in sr

    def is_new(n):
        if t == "C":
            return bool(rv) and n["date"].startswith(rv)
        if t == "F":
            return bool(rv) and norm(rv) in norm(n.get("quote") or "") + norm(n["text"])
        q = norm(n.get("quote"))
        return bool(q) and q in sr and q not in sp

    stale = [] if t == "A" else [n for n in at if is_old(n)]  # loại A (chỉ diễn đạt lại): không so quote, nút cũ vẫn đúng nghĩa
    marked = [n for n in stale if n.get("invalidated_at") or n.get("end_time")]
    other_old = {n["node_id"] for n in old if cid not in n["cids"]}
    other_new = {n["node_id"] for n in nodes if cid not in n["cids"]}
    if t == "A":  # new_present = các nút ở chunk đổi giữ nguyên tập (ngày, phase) như bản cũ (tên nút/diễn đạt có thể đổi khi trích lại)
        sig = lambda ns: sorted((n["date"], n["phase"]) for n in ns if cid in n["cids"] and not n.get("invalidated_at"))
        new_ok = int(sig(nodes) == sig(old))
    else:
        new_ok = int(any(is_new(n) for n in at))
    return {"stale_open": len(stale) - len(marked), "stale_marked": len(marked), "new_present": new_ok,
            "lost_other": len(other_old - other_new), "added_other": len(other_new - other_old)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("systems", nargs="*", default=["old", "window_replace", "diff_replace"])
    ap.add_argument("--set", default="tune")
    ap.add_argument("-v", action="store_true", help="in từng chỗ sửa")
    a = ap.parse_args()
    S = a.set
    P = json.loads((ORG / M3 / S / "pilot.json").read_text(encoding="utf-8"))["edits"]
    ed = {e.get("edit_id"): e for e in map(json.loads, (ORG / "past" / S / "edits.jsonl").read_text(encoding="utf-8").splitlines())}
    tot = {s: defaultdict(lambda: defaultdict(int)) for s in a.systems}
    for s in a.systems:
        for c in P:
            if not (ORG / M3 / S / s / "nodes" / f"{c['page']}.json").exists():
                continue  # hệ chưa chạy chỗ sửa này
            old = load_nodes(S, "old", c["page"])
            r = judge(c, ed[c["edit_id"]], load_nodes(S, s, c["page"]), old)
            if a.v:
                print(f"{s:<15}{c['edit_id']:<10}{c['type']} {c['page'][:26]:<27}", r)
            for k, v in r.items():
                tot[s][c["type"]][k] += v
            tot[s][c["type"]]["n"] += 1
    keys = ["stale_open", "stale_marked", "new_present", "lost_other", "added_other"]
    print(f"\n{'hệ':<15}{'loại':<5}{'n':>3}" + "".join(f"{k:>13}" for k in keys))
    for s in a.systems:
        for t in "CEFA":
            d = tot[s][t]
            print(f"{s:<15}{t:<5}{d['n']:>3}" + "".join(f"{d[k]:>13}" for k in keys))
        allv = {k: sum(tot[s][t][k] for t in "CEFA") for k in keys + ["n"]}
        print(f"{s:<15}{'all':<5}{allv['n']:>3}" + "".join(f"{allv[k]:>13}" for k in keys))


if __name__ == "__main__":
    main()
