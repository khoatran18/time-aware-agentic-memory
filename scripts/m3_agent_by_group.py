"""Cơ chế 3: exact của agent theo nhóm câu (đích / cùng chunk / cùng trang) và theo loại chỗ sửa (C/E/F/A). KHÔNG gọi LLM.
Dùng: python3 scripts/m3_agent_by_group.py <tên thư mục output> [...]   (chấm bằng v9_agent_score --detail, đọc subset m3_state/<tập>/subset.json)
"""
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
cases = {c["idx"]: c for c in json.loads((ROOT / "dataset/organized" / __import__("os").environ.get("M3_STATE_NAME", "m3_state") / __import__("os").environ.get("M3_SET", "tune") / "subset.json").read_text(encoding="utf-8"))["cases"]}
for run in sys.argv[1:]:
    out = subprocess.run([sys.executable, "-I", str(ROOT / "scripts/v9_eval/v9_agent_score.py"), str(ROOT), run, "--detail"], capture_output=True, text=True, cwd=ROOT).stdout
    wrong = {l.split()[0] for l in out.splitlines() if l.startswith("   ") and "exact=0" in l}
    ran = {json.loads(l)["idx"] for l in (ROOT / "output" / run / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    for key in ("group", "edit_type"):
        tot, ok = defaultdict(int), defaultdict(int)
        for i in ran:
            tot[cases[i][key]] += 1
            ok[cases[i][key]] += i not in wrong
        print(run, key, " ".join(f"{k}={ok[k]}/{tot[k]}({ok[k] / tot[k]:.2f})" for k in sorted(tot)))
    print(run, "all", f"{len(ran) - len(wrong & ran)}/{len(ran)}", "sai:", sorted(wrong & ran))
