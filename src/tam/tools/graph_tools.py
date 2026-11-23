"""Công cụ graph cho agent kiểu B (Cơ chế 2): `timeline`, `events_of_chunk`. Không gọi LLM.

Graph là dòng thời gian sự kiện theo trang (`Neo4jStore`): mỗi sự kiện có ngày, track, loại, câu mô tả và `chunk_id` trỏ về VectorDB.
Công cụ chỉ đọc; chọn trang, track, khoảng năm là việc của agent (không suy hộ `track` hay khoảng năm từ câu hỏi như `TimelineRetriever`).
Mô tả công cụ là một phần cố định của harness, giữ trung tính.
"""
from __future__ import annotations

import re
from typing import Protocol

from pydantic import BaseModel, Field

from tam.tools.base import AgentTool, ToolError, ToolResult

DEFAULT_MAX_EVENTS = 40
EVENTS_CAP = 50


class GraphReader(Protocol):
    """Phần của `Neo4jStore` mà công cụ cần (để test bằng kho giả)."""

    def cell_events(self, page: str, tracks: list[str] | None = None, date_from: str | None = None, date_to: str | None = None,
                    max_tier: int = 2) -> list[dict]: ...

    def events_of_chunks(self, chunk_ids: list[str]) -> list[dict]: ...


def page_name(page: str, normalize: bool = False) -> str:
    """`/wiki/Tên` hoặc `Tên` -> `Tên` (graph lưu tên trang không có tiền tố).
    `normalize`: nhận cả chunk id (`/wiki/Tên#12`) và tên viết tự do; áp luật đặt tên của graph (mọi dãy ký tự ngoài `0-9A-Za-z` thành một `_`, bỏ `_` hai đầu): khớp đủ 35 tên trang hiện có từ id trang trong kho text."""
    name = page.strip().removeprefix("/wiki/")
    if not normalize:
        return name
    return re.sub(r"[^0-9A-Za-z]+", "_", name.split("#", 1)[0]).strip("_")  # bỏ `#n` của chunk id rồi áp luật đặt tên


def _short_cid(cid: str) -> str:
    """`/wiki/Trang#12` -> `#12` (chunk của chính trang đang xem; id đầy đủ là `/wiki/<trang>#12`)."""
    return "#" + cid.rsplit("#", 1)[-1]


class TimelineArgs(BaseModel):
    page: str = Field(description="Page name, e.g. Bohemond_IV_of_Antioch (a chunk id's page part also works).")
    track: list[str] | None = Field(default=None, description="Only events of these tracks (e.g. role, location, naming). Omit for all tracks.")
    from_year: int | None = Field(default=None, description="Only events dated in or after this year.")
    to_year: int | None = Field(default=None, description="Only events dated in or before this year.")
    max_events: int = Field(default=DEFAULT_MAX_EVENTS, ge=1, description="Number of events to return.")
    offset: int = Field(default=0, ge=0, description="Skip this many events (to get the next page).")


class EventsOfChunkArgs(BaseModel):
    chunk_ids: list[str] = Field(min_length=1, description="Chunk ids as shown in search results.")


def _year(y: int | None) -> str | None:
    return None if y is None else f"{y:04d}"


class GraphTools:
    """`store`: `Neo4jStore` hoặc kho giả có `cell_events`, `events_of_chunks`."""

    def __init__(self, store: GraphReader, *, events_cap: int = EVENTS_CAP, compact: bool = False, normalize_names: bool = False,
                 track_hint: bool = False, source_hint: bool = False, allowed_pages: set[str] | None = None, show_state: bool = False) -> None:
        """`compact`: dòng `số. ngày text <#chunk>` (bỏ phase, track/kind, tier; chunk id rút còn `#n`). `normalize_names`: chuẩn hóa tên trang theo luật của graph. `source_hint`: mô tả công cụ nói mỗi dòng có chunk nguồn mà `read_chunk` đọc được. `track_hint`: tiêu đề nêu số sự kiện mỗi track và mô tả công cụ nhắc có thể lọc theo track. `allowed_pages`: chỉ cho xem các trang này (tên đã chuẩn hóa; None = mọi trang). `show_state`: ẩn sự kiện có `invalidated_at`, ghi `(ended <end_time>)` cho sự kiện có `end_time` (cơ chế 3); mặc định tắt = hành vi cũ."""
        self._store, self._cap, self._compact, self._normalize, self._hint, self._src = store, events_cap, compact, normalize_names, track_hint, source_hint
        self._allowed, self._state = allowed_pages, show_state

    def timeline(self, page: str, track: list[str] | None = None, from_year: int | None = None, to_year: int | None = None,
                 max_events: int = DEFAULT_MAX_EVENTS, offset: int = 0) -> ToolResult:
        """Các sự kiện của một trang theo thứ tự ngày, kèm chunk nguồn; lọc track và khoảng năm do agent chọn."""
        name = page_name(page, self._normalize)
        if from_year is not None and to_year is not None and from_year > to_year:
            raise ToolError(f"from_year ({from_year}) lớn hơn to_year ({to_year})")
        rows = [] if self._allowed is not None and page_name(name, True) not in self._allowed else self._store.cell_events(name, tracks=track or None, date_from=_year(from_year), date_to=_year(to_year), max_tier=2)
        if self._state:
            rows = [r for r in rows if not r.get("invalidated_at")]
        if not rows:
            raise ToolError(f"không có sự kiện nào cho trang {name!r} với bộ lọc này (graph chỉ có một phần số trang)")
        k, off = min(max_events, self._cap), offset
        part = rows[off:off + k]
        if not part:
            raise ToolError(f"offset {off} vượt quá {len(rows)} sự kiện")
        counts = {t: sum(r["track"] == t for r in rows) for t in sorted({r["track"] for r in rows})}
        tracks = [f"{t} ({n})" for t, n in counts.items()] if self._hint else list(counts)
        head = f"{len(rows)} events on {name}{' (chunk ids are /wiki/' + name + '#n)' if self._compact else ''}; showing {len(part)} from #{off + 1}; tracks: {', '.join(tracks)}"
        more = off + k < len(rows)
        if more:
            head += f"; more available (offset={off + k})"
        lines = [head]
        ids: list[str] = []
        for i, r in enumerate(part, off + 1):
            cids = list(r.get("cids") or [])
            ids.extend(cids)
            if self._compact:
                lines.append(f"{i}. {r['date']} {r['text']}{self._ended(r)} <{', '.join(_short_cid(c) for c in cids)}>")
            else:
                lines.append(f"{i}. {r['date']} [{r['phase']}] {r['track']}/{r['kind']} (tier {r['tier']}) {r['text']}{self._ended(r)} <{', '.join(cids)}>")
        return ToolResult("\n".join(lines), tuple(dict.fromkeys(ids)), more)

    def _ended(self, r: dict) -> str:
        return f" (ended {r['end_time']})" if self._state and r.get("end_time") else ""

    def events_of_chunk(self, chunk_ids: list[str]) -> ToolResult:
        """Với mỗi chunk: trang và track của các sự kiện rút ra từ chunk đó (để nhảy sang `timeline`)."""
        lines = []
        for cid in chunk_ids:
            evs = self._store.events_of_chunks([cid])  # từng chunk một: `events_of_chunks` không trả chunk nào sinh ra sự kiện nào
            if not evs:
                lines.append(f"{cid}: no events in the graph")
                continue
            lines.append(f"{cid}: {len(evs)} events; page {', '.join(sorted({e['page'] for e in evs}))}; tracks {', '.join(sorted({e['track'] for e in evs}))}")
        return ToolResult("\n".join(lines), tuple(chunk_ids))

    def tools(self) -> list[AgentTool]:
        return [
            AgentTool("timeline", "List the dated events extracted for a page, in date order, with the chunk each came from. "
                      "Events can be filtered by track and by year range." + (" A page with many events is easier to read when narrowed to the relevant track." if self._hint else "")
                      + (" Each event line ends with the chunk it came from; read_chunk shows that chunk's full text." if self._src else ""), TimelineArgs, self.timeline),
            AgentTool("events_of_chunk", "For chunk ids, show which page and tracks have timeline events extracted from them.",
                      EventsOfChunkArgs, self.events_of_chunk),
        ]
