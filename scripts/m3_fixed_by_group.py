"""Tách kết quả f/f′/f″ (v9_fixed_eval) theo nhóm câu (đích/cùng chunk/cùng trang) và loại sửa (C/E/F/A).
Dùng: m3_fixed_by_group.py <tên>=<thư mục output> ...   (subset: m3_state/tune/subset.json)"""
import json, sys
from collections import defaultdict
S = json.load(open(f"dataset/organized/{__import__('os').environ.get('M3_STATE_NAME', 'm3_state')}/{__import__('os').environ.get('M3_SET', 'tune')}/subset.json"))["cases"]
meta = {c["idx"]: (c["group"], c["edit_type"]) for c in S}
tab = defaultdict(lambda: defaultdict(list))
for arg in sys.argv[1:]:
    name, d = arg.split("=")
    for line in open(f"{d}/results.jsonl"):
        r = json.loads(line); g, t = meta[r["qid"]]
        for key in (("ALL",), ("nhóm", g), ("loại sửa", t)):
            tab[(name, r["v"])][key].append(r["exact"])
keys = [("ALL",), ("nhóm", "dich"), ("nhóm", "cung_chunk"), ("nhóm", "cung_trang"), ("loại sửa", "C"), ("loại sửa", "E"), ("loại sửa", "F"), ("loại sửa", "A")]
print("hệ/cấu hình".ljust(22) + "".join(" ".join(k[1:] or k).ljust(12) for k in [("ALL",)] + keys[1:]))
for nv, d in tab.items():
    print(f"{nv[0]} {nv[1]}".ljust(22) + "".join((f"{sum(d[k])/len(d[k]):.2f} ({len(d[k])})" if d[k] else "-").ljust(12) for k in keys))
