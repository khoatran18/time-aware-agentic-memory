"""Cơ chế 3, bước 1 (diff chunk): với mỗi chỗ sửa của pilot, lấy chunk bản cũ (@past) và bản mới, tách câu và so sánh.
Không gọi LLM, không đụng kho. Ghi dataset/organized/m3_state/<tập>/diff.json.
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "dataset" / "organized"
M3 = os.environ.get("M3_STATE_NAME", "m3_state")  # thư mục trạng thái (mặc định m3_state; m3_state_ext cho đợt mở rộng)


def chunk_texts(path: Path) -> dict[str, str]:
    parts = re.split(r"^=== CHUNK (.+?) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    return {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}


def sentences(body: str) -> list[str]:
    body = body.split("\n", 1)[1] if "\n" in body else body  # bỏ dòng "<trang> | <tiêu đề>"
    return [s.strip() for s in re.split(r"(?<= \.) ", body) if s.strip()]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set", default="tune")
    a = ap.parse_args()
    S = a.set
    pilot = json.loads((ORG / M3 / S / "pilot.json").read_text(encoding="utf-8"))
    edits = {e["edit_id"]: e for e in map(json.loads, (ORG / "past" / S / "edits.jsonl").read_text(encoding="utf-8").splitlines()) if e.get("edit_id")}
    out, bad = [], 0
    for c in pilot["edits"]:
        e = edits[c["edit_id"]]
        old = chunk_texts(ORG / "past" / S / "chunks" / f"{c['page']}.txt")[e["chunk_id_past"]]
        new = chunk_texts(ORG / "source" / S / "chunks" / f"{c['page']}.txt")[c["chunk_id"]]
        so, sn = sentences(old), sentences(new)
        ops = [{"op": t, "old": so[i1:i2], "new": sn[j1:j2]}
               for t, i1, i2, j1, j2 in difflib.SequenceMatcher(None, so, sn, autojunk=False).get_opcodes() if t != "equal"]
        ok = any(e["sentence_past"].strip() in " ".join(o["old"]) and e["sentence_real"].strip() in " ".join(o["new"]) for o in ops)
        bad += not ok
        out.append({"edit_id": c["edit_id"], "type": c["type"], "page": c["page"], "chunk_id": c["chunk_id"],
                    "chunk_id_past": e["chunk_id_past"], "changed": bool(ops), "matches_edit_record": ok,
                    "n_sent_old": len(so), "n_sent_new": len(sn), "ops": ops, "old_text": old, "new_text": new})
    p = ORG / M3 / S / "diff.json"
    p.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out)} chỗ sửa -> {p.relative_to(ROOT)}; không khớp bản ghi sửa: {bad}")
    for o in out:
        print(f"{o['edit_id']:10} {o['type']} {o['page'][:28]:28} chunk_đổi={o['changed']} khớp={o['matches_edit_record']} thao_tác={[(x['op'], len(x['old']), len(x['new'])) for x in o['ops']]}")


if __name__ == "__main__":
    main()
