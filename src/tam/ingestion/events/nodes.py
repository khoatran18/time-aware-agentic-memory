"""Từ mốc ingest (đầu ra prompt 10b) tới nút graph: gộp quy tắc, gộp cặp LLM có chặn, gán tier, node_id. Không gọi LLM.

Thứ tự (docs/pending/02, mục "Quy tắc nạp graph"): merge_keyed -> merge(tracks) -> gộp cặp LLM `same` (có chặn) -> tier.
Chặn không gộp cặp LLM: khác phase (start/end), khác track (trừ other), số năm trong text mâu thuẫn.
Giữ nút: ưu tiên mốc không thuộc Lead (section != 0), rồi mốc đến trước; ngày dài hơn; hợp cids; ghi merged_from.
"""
from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from tam.ingestion.events import post as ip

_YEAR = re.compile(r"(?<!\d)\d{4}(?!\d)")


def rule_merge(events: list[dict]) -> list[dict]:
    """Gộp quy tắc: giữ thứ tự và chỉ số mà so cặp LLM đã chấm (merge_keyed rồi merge có tracks)."""
    return ip.merge(ip.merge_keyed(events), tracks=True)


def pair_blocked(a: dict, b: dict) -> str | None:
    """Lý do không được gộp một cặp LLM `same`, hoặc None nếu được."""
    if {a.get("phase"), b.get("phase")} == {"start", "end"}:
        return "phase"
    ta, tb = a.get("track"), b.get("track")
    if ta and tb and "other" not in (ta, tb) and ta != tb:
        return "track"
    ya, yb = set(_YEAR.findall(a["text"])), set(_YEAR.findall(b["text"]))
    if ya and yb and ya != yb:
        return "year"
    return None


def merge_pairs(e: list[dict], same_pairs: list[tuple[int, int]]) -> tuple[list[dict], dict]:
    """Gộp các cặp (i, j) LLM gán `same` bằng union-find, có chặn. Trả (danh sách mới, thống kê)."""
    par = list(range(len(e)))

    def find(x: int) -> int:
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        return x

    stat = {"pairs": len(same_pairs), "blocked_phase": 0, "blocked_track": 0, "blocked_year": 0, "merged": 0}
    for i, j in same_pairs:
        if i >= len(e) or j >= len(e):
            continue
        why = pair_blocked(e[i], e[j])
        if why:
            stat[f"blocked_{why}"] += 1
            continue
        a, b = find(i), find(j)
        if a != b:
            par[b] = a
            stat["merged"] += 1
    groups: dict[int, list[int]] = defaultdict(list)
    for k in range(len(e)):
        groups[find(k)].append(k)
    out = []
    for ks in groups.values():
        rep = min(ks, key=lambda k: (e[k].get("section", 0) == 0, k))  # không-Lead trước, rồi đến trước
        m = dict(e[rep])
        m["cids"] = sorted({c for k in ks for c in e[k].get("cids", [e[k]["cid"]])})
        dates = [e[k]["date"] for k in ks if e[k].get("date")]
        m["date"] = max(dates, key=len) if dates else m.get("date")
        m["merged_from"] = ks
        out.append(m)
    return out, stat


def tier_of(e: dict) -> int:
    """Tier 1 = mốc chính (change/occurrence của chính chủ thể); tier 2 = ưu tiên thấp (lọc mềm)."""
    return 1 if e.get("kind") in ("change", "occurrence") and e.get("subject") in ("self", "part_of_self") else 2


def to_nodes(page: str, e: list[dict]) -> list[dict]:
    """Chuyển mốc đã gộp thành nút graph, bỏ mốc không ngày. node_id ổn định: băm (trang, track, ngày, phase, object/text)."""
    nodes, seen = [], defaultdict(int)
    for x in e:
        if not x.get("date"):
            continue
        key = f"{page}|{x.get('track')}|{x['date']}|{x.get('phase')}|{ip.norm(x.get('object') or x['text'])[:60]}"
        h = hashlib.sha1(key.encode()).hexdigest()[:16]
        seen[h] += 1
        nodes.append(dict(
            node_id=h if seen[h] == 1 else f"{h}-{seen[h]}", page=page, track=x.get("track") or "other", date=x["date"],
            phase=x.get("phase") or "point", kind=x.get("kind"), subject=x.get("subject"), object=x.get("object"),
            text=x["text"], quote=x.get("quote"), cids=x.get("cids", [x["cid"]]), tier=tier_of(x),
            is_lead=x.get("section", 0) == 0, approximate=bool(x.get("approximate")), flags=list(x.get("flags", [])),
            merged_from=x.get("merged_from", [])))
    return nodes
