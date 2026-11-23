"""Cơ chế 3: kiểm quyết định của LLM theo quy tắc hành động (không gọi LLM).
C: có invalidate và add | E: có mốc phase end hoặc close | F: có add | A: không invalidate/close/add.
Thêm: số edit theo loại, số edit sai (loại C/E/F có edit), phase của mốc add. Dùng: m3_action_check.py <hệ> [<hệ>...] (hệ = mech3, mech3_v1)."""
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

ORG = Path(__file__).resolve().parents[1] / "dataset" / "organized"
for sysname in sys.argv[1:]:
    tot = defaultdict(Counter)
    bad = []
    for state in ((os.environ["M3_STATE_NAME"],) if os.environ.get("M3_STATE_NAME") else ("m3_state", "m3_state_ext")):
        P = json.loads((ORG / state / os.environ.get("M3_SET", "tune") / "pilot.json").read_text(encoding="utf-8"))["edits"]
        for c in P:
            o = json.loads((ORG / state / os.environ.get("M3_SET", "tune") / sysname / "raw" / f"{c['edit_id']}.json").read_text(encoding="utf-8"))["output"]
            ops = Counter(x["op"] for x in o["changes"])
            na, ends = len(o["add"]), sum(a["phase"] == "end" for a in o["add"])
            t = c["type"]
            ok = {"C": ops["invalidate"] >= 1 and na >= 1, "E": ends >= 1 or ops["close"] >= 1, "F": na >= 1,
                  "A": ops["invalidate"] + ops["close"] == 0 and na == 0}[t]
            tot[t]["ok" if ok else "no"] += 1
            if not ok:
                bad.append((c["edit_id"], t, c["page"][:24]))
            if t != "A":
                tot[t]["edit"] += ops["edit"]
            tot[t]["adds"] += na
            tot[t]["add_end"] += ends
            tot[t]["add_point"] += sum(a["phase"] == "point" for a in o["add"])
    print(sysname, {t: dict(tot[t]) for t in "CEFA"})
    print("  hỏng:", bad)
