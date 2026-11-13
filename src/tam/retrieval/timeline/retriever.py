"""Truy xuất Cơ chế 2 (docs/decisions/10): Vector tìm chunk -> chunk vào nút graph -> đi dọc ô (trang, track) theo thời gian -> timeline gọn.

`graph_timeline`: cấu hình đề xuất. `chunk_events`: baseline vector top-k (chỉ các nút của chunk tìm được, không đi dọc ô).
Quy tắc tier: mặc định tier 1; thêm tier 2 khi tier 1 rỗng hoặc nút tier 2 khớp từ khóa câu hỏi (>= 2 từ), trong phần ngân sách còn lại.
"""
from __future__ import annotations

import re
from collections import defaultdict

from tam.retrieval.timeline.track import infer_tracks
from tam.retrieval.timeline.window import parse_window
from tam.stores.graph.neo4j_store import Neo4jStore
from tam.stores.vector.base import VectorFilter, VectorStore
from datetime import datetime, timezone

RRF_K = 60
_TOK = re.compile(r"[A-Za-zÀ-ÿ]{3,}|\d{2,}")
_STOP = {"the", "and", "for", "that", "with", "from", "was", "were", "his", "her", "their", "among", "dated", "events", "timeline", "list", "summarize", "chronological", "order"}


def toks(t: str) -> set[str]:
    return {w.lower().rstrip("s") for w in _TOK.findall(t)} - _STOP


class TimelineRetriever:
    def __init__(self, vec: VectorStore, graph: Neo4jStore, top_n: int = 10, k_entry: int = 8, max_events: int = 40) -> None:
        self.vec, self.graph, self.top_n, self.k_entry, self.max_events = vec, graph, top_n, k_entry, max_events

    def search_chunks(self, query: str) -> list[str]:
        """Hybrid dense + BM25, gộp RRF; trả chunk_id theo thứ hạng (không lọc thời gian)."""
        flt = VectorFilter(t_req=datetime.now(timezone.utc), exclude_invalidated=False, apply_time=False)
        hits = self.vec.search(query, flt, self.top_n)
        score: dict[str, float] = defaultdict(float)
        for lst in (hits.dense, hits.sparse):
            for r, h in enumerate(lst):
                score[h.chunk.chunk_id] += 1.0 / (RRF_K + r + 1)
        return [c for c, _ in sorted(score.items(), key=lambda x: -x[1])]

    def _entries(self, chunks: list[str]) -> tuple[str | None, list[dict]]:
        """Nút vào từ top chunk; trang = trang có nhiều nút vào nhất (trọng số theo thứ hạng chunk)."""
        top = chunks[: self.k_entry]; rows = self.graph.events_of_chunks(top)
        by_chunk = {c: [] for c in top}
        for c in top:
            by_chunk[c] = [r for r in self.graph.events_of_chunks([c])]
        vote: dict[str, float] = defaultdict(float)
        for r, c in enumerate(top):
            for e in by_chunk[c]:
                vote[e["page"]] += 1.0 / (RRF_K + r + 1)
        if not vote:
            return None, []
        page = max(vote, key=vote.get)
        return page, [e for e in rows if e["page"] == page]

    def chunk_events(self, query: str) -> dict:
        """Baseline: chỉ các nút của chunk top-k thuộc trang được chọn (không đi dọc ô)."""
        chunks = self.search_chunks(query); page, entries = self._entries(chunks)
        if not page:
            return dict(page=None, events=[], chunks=chunks)
        ids = {e["node_id"] for e in entries}
        ev = [e for e in self.graph.cell_events(page) if e["node_id"] in ids]
        return dict(page=page, events=ev[: self.max_events], chunks=chunks)

    def graph_timeline(self, query: str, window: tuple[str | None, str | None] | None = None, question: str | None = None, track_mode: str = "filter") -> dict:
        """`window` = (từ năm, đến năm) tách từ câu hỏi (parse_window); None = không lọc thời gian. `question` (nếu có): suy track từ câu hỏi (infer_tracks) thay cho track của nút vào; không khớp thì dùng track của nút vào."""
        chunks = self.search_chunks(query); page, entries = self._entries(chunks)
        if not page:
            return dict(page=None, events=[], chunks=chunks, tier2=0)
        tracks = sorted({e["track"] for e in entries}) or None
        qt = infer_tracks(question) if question else set()
        if qt and track_mode == "filter":
            tracks = sorted(qt)  # lọc cứng theo track suy ra từ câu hỏi (đo: làm mất mốc đáp án)
        wf, wt = window or (None, None)
        t1 = self.graph.cell_events(page, tracks=tracks, date_from=wf, date_to=wt, max_tier=1)
        t2 = [e for e in self.graph.cell_events(page, tracks=tracks, date_from=wf, date_to=wt, max_tier=2) if e["tier"] == 2]
        q = toks(query); extra = [e for e in t2 if not t1 or len(toks(e["text"]) & q) >= 2]
        ev = t1 + extra
        if len(ev) > self.max_events:  # cắt theo độ khớp từ khóa câu hỏi, giữ tier 1 trước
            ev = sorted(ev, key=lambda e: (e["tier"], e["track"] not in qt, -len(toks(e["text"]) & q)))[: self.max_events]  # track suy ra chỉ dùng xếp hạng khi cắt
        ev.sort(key=lambda e: (e["date"], e["phase"]))
        return dict(page=page, events=ev, chunks=chunks, tier2=sum(1 for e in ev if e["tier"] == 2), tracks=tracks, window=window)
