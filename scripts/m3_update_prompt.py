"""Cơ chế 3, hệ "LLM quyết định": prompt cập nhật, dựng đầu vào (nút cũ mức 2) và kiểm đầu ra bằng mã. KHÔNG gọi LLM trong file này.

  show <edit_id>   in đầu vào đầy đủ của một chỗ sửa (system + human)
  sizes            ký tự/ước token đầu vào của 20 chỗ sửa pilot, số nút cũ đưa vào
Nút cũ mức 2: nút có chunk nguồn là chunk đổi + nút kề trước/sau trong chuỗi TIẾP_THEO của cùng Cell (page, track; sắp theo ngày), tối đa MAX_NODES.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
ORG = ROOT / "dataset" / "organized"
M3 = os.environ.get("M3_STATE_NAME", "m3_state")  # thư mục trạng thái (mặc định m3_state; m3_state_ext cho đợt mở rộng)
MAX_NODES = 20
FMT = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")
norm = lambda s: re.sub(r"\s+", "", s or "").lower()

PROMPT = (ROOT / "src" / "tam" / "llm" / "prompts" / "update_m3.md").read_text(encoding="utf-8")  # nội dung prompt ở file này (đăng ký ở prompts/README.md)


class Change(BaseModel):
    node: str
    op: Literal["close", "invalidate"]
    evidence: str
    end_date: str | None = None  # close


class AddEv(BaseModel):
    text: str
    evidence: str
    date_text: str | None = None
    date: str | None = None
    approximate: bool = False
    track: str = "other"
    phase: str = "point"
    kind: str = "occurrence"
    subject: str = "self"
    object: str | None = None
    quote: str | None = None


class Update(BaseModel):
    changes: list[Change] = Field(default_factory=list)
    add: list[AddEv] = Field(default_factory=list)


def chunk_blocks(path: Path) -> list[tuple[str, str]]:
    parts = re.split(r"^=== CHUNK (.+?) ===\n", path.read_text(encoding="utf-8"), flags=re.M)
    return [(parts[i], parts[i + 1].strip()) for i in range(1, len(parts), 2)]


def body(text: str) -> str:
    return text.split("\n", 1)[1].strip() if "\n" in text else text


def select_nodes(nodes: list[dict], cid: str) -> list[dict]:
    """Mức 2: nút của chunk đổi + nút kề trước/sau trong chuỗi TIẾP_THEO (cùng track, sắp theo ngày) của từng nút đó; tối đa MAX_NODES."""
    by_track: dict[str, list[dict]] = {}
    for n in sorted(nodes, key=lambda n: (n["date"], n["node_id"])):
        by_track.setdefault(n["track"], []).append(n)
    chosen, seen = [], set()

    def take(n):
        if n["node_id"] not in seen:
            seen.add(n["node_id"])
            chosen.append(n)

    own = [n for n in sorted(nodes, key=lambda n: (n["date"], n["node_id"])) if cid in n["cids"]]
    for n in own:
        take(n)
    for n in own:
        chain = by_track[n["track"]]
        k = chain.index(n)
        for j in (k - 1, k + 1):
            if 0 <= j < len(chain):
                take(chain[j])
    return chosen[:MAX_NODES]


def render(c: dict, old_chunk: str, new_chunk: str, window_chunks: list[tuple[str, str]], nodes: list[dict], section_title: str) -> tuple[str, str, dict]:
    """(system, human, ánh xạ N<i> -> node_id). Số chunk = vị trí trong cửa sổ (1..k)."""
    cid = c["chunk_id"]
    num = {cd: i + 1 for i, (cd, _) in enumerate(window_chunks)}
    sel = select_nodes(nodes, cid)
    idmap = {f"N{i + 1}": n["node_id"] for i, n in enumerate(sel)}
    lines = [f"REVISED CHUNK: number {num[cid]}", "OLD text:", body(old_chunk), "NEW text:", body(new_chunk), "", "OTHER CHUNKS OF THE WINDOW:"]
    lines += [f"[{num[cd]}] (context only) {body(t)}" for cd, t in window_chunks if cd != cid] or ["(none)"]
    lines += ["", "EXISTING NODES:"]
    for (nid, _), n in zip(idmap.items(), sel):
        src = ", ".join(f"{num[x]}{' revised' if x == cid else ''}" if x in num else "other section" for x in n["cids"])
        lines.append(f"{nid} | date {n['date']} | phase {n['phase']} | track {n['track']} | kind {n['kind']} | chunks {src} | text: {n['text']} | quote: {n.get('quote')}")
    if not sel:
        lines.append("(none)")
    system = PROMPT.format(title=c["page"].replace("_", " "), section=section_title)
    return system, "\n".join(lines), idmap


def build(S: str, c: dict, nodes_system: str = "old") -> tuple[str, str, dict]:
    page = c["page"]
    src = dict(chunk_blocks(ORG / "source" / S / "chunks" / f"{page}.txt"))
    old = dict(chunk_blocks(ORG / "past" / S / "chunks" / f"{page}.txt"))[c["chunk_id"] + "@past"]
    win = [(cd, src[cd]) for cd in c["window"]["chunk_ids"]]
    nodes = json.loads((ORG / M3 / S / nodes_system / "nodes" / f"{page}.json").read_text(encoding="utf-8"))
    return render(c, old, src[c["chunk_id"]], win, nodes, c["window"]["section_title"])


def validate(upd: Update, new_chunk: str, page_text: str, idmap: dict) -> tuple[list, list, list]:
    """Kiểm bằng mã. Trả (thay đổi hợp lệ, mốc thêm hợp lệ, [(mục, lý do)] bị loại)."""
    nc, pg, rej = norm(new_chunk), norm(page_text), []
    yr = lambda d: bool(d) and re.search(rf"(?<!\d){d[:4].lstrip('0')}(?!\d)", new_chunk) is not None
    ok_c, seen = [], set()
    for ch in upd.changes:
        why = None
        if ch.node not in idmap:
            why = "node_id_unknown"
        elif ch.node in seen:
            why = "two_decisions_same_node"
        elif norm(ch.evidence) not in nc:
            why = "evidence_not_in_new_text"
        elif ch.op == "close" and not (ch.end_date and FMT.match(ch.end_date) and yr(ch.end_date)):
            why = "bad_end_date"
        (rej.append((ch, why)) if why else (ok_c.append(ch), seen.add(ch.node)))
    ok_a = []
    for ev in upd.add:
        why = None
        if norm(ev.evidence) not in nc:
            why = "evidence_not_in_new_text"
        elif ev.quote and norm(ev.quote) not in nc:
            why = "quote_not_in_new_text"
        elif ev.date and not (FMT.match(ev.date) and yr(ev.date)):
            why = "bad_date"
        elif any(n.replace(",", "") not in new_chunk.replace(",", "") for n in re.findall(r"\d[\d,\.]*\d|\d", ev.text) if not (ev.date and n == ev.date[:4])):
            why = "number_not_in_new_text"
        (rej.append((ev, why)) if why else ok_a.append(ev))
    return ok_c, ok_a, rej


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["show", "sizes"])
    ap.add_argument("edit_id", nargs="?")
    ap.add_argument("--set", default="tune")
    a = ap.parse_args()
    P = json.loads((ORG / M3 / a.set / "pilot.json").read_text(encoding="utf-8"))["edits"]
    if a.cmd == "show":
        c = next(x for x in P if x["edit_id"] == a.edit_id)
        s, h, m = build(a.set, c)
        print(s, "\n" + "=" * 20 + " HUMAN " + "=" * 20, h, sep="\n")
        return
    print(f"{'edit':<10}{'loại':<5}{'trang':<28}{'nút cũ':>7}{'ký tự':>7}{'~token':>7}")
    tot = 0
    for c in P:
        s, h, m = build(a.set, c)
        n = len(s) + len(h)
        tot += n
        print(f"{c['edit_id']:<10}{c['type']:<5}{c['page'][:27]:<28}{len(m):>7}{n:>7}{n // 4:>7}")
    print("tổng ~token vào:", tot // 4)


if __name__ == "__main__":
    main()
