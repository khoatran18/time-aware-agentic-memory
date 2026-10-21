"""Suy luận mốc thời gian từ chunk liền kề (decisions/07 đề xuất 11), không gọi LLM.

Trang Wikipedia thường viết theo thứ tự thời gian, nên chunk không có mốc thường xảy ra sau chunk dated đứng trước, và
chunk chỉ biết lúc bắt đầu thường kết thúc khi sự việc dated kế tiếp bắt đầu. Hai suy luận, đều tùy chọn:

- `start` rỗng: lấy mốc của chunk dated gần nhất đứng TRƯỚC (`start_rule`: `prev_end` | `prev_start` | `prev_end_cap`).
- `end` không rõ (`unknown`): lấy `start` của chunk dated gần nhất đứng SAU và muộn hơn `start` của chính nó (`end_rule`: `next_start`),
  bỏ nếu cách xa hơn `max_gap_years`.

`ongoing` không bao giờ suy (giữ chính sách cần cụm nguyên văn, decisions/02). Chunk được suy mang cờ `time_inferred` để
điểm thời gian thấp hơn mốc thật (`inferred_factor` trong scoring). Chỉ dùng nhãn GỐC của LLM để suy, không suy dây chuyền.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

START_RULES = ("none", "prev_end", "prev_start", "prev_end_cap")
END_RULES = ("none", "next_start")
SECONDS_PER_YEAR = 365.25 * 24 * 3600


@dataclass(frozen=True)
class Inferred:
    """Nhãn thời gian mới của một chunk."""

    start: datetime | None
    end: datetime | None
    end_status: str | None
    inferred: str | None  # "start" | "end" | None


def _parse(value: str | None) -> datetime | None:
    return None if not value else datetime.fromisoformat(value).astimezone(timezone.utc)


def _year_end(t: datetime) -> datetime:
    return datetime(t.year, 12, 31, tzinfo=timezone.utc)


def infer_page(
    rows: list[Mapping[str, Any]], *, start_rule: str = "none", end_rule: str = "none",
    max_gap_years: float | None = None, cap_years: float = 10.0,
) -> dict[str, Inferred]:
    """`rows`: các dòng `extractions.jsonl` CỦA MỘT TRANG, theo thứ tự đoạn. Trả chunk_id -> nhãn mới (chỉ chunk được suy)."""
    if start_rule not in START_RULES or end_rule not in END_RULES:
        raise ValueError(f"start_rule {START_RULES}, end_rule {END_RULES}; nhận {start_rule!r}, {end_rule!r}")
    s = [_parse(r["start"]) for r in rows]
    e = [_parse(r["end"]) for r in rows]
    status = [r.get("end_status") for r in rows]
    out: dict[str, Inferred] = {}
    for i, row in enumerate(rows):
        if s[i] is None and start_rule != "none" and row.get("undated"):  # chỉ chunk đang nằm trong kho dưới dạng không mốc
            j = next((k for k in range(i - 1, -1, -1) if s[k] is not None), None)
            if j is None:
                continue
            ref = s[j]
            use_end = start_rule == "prev_end" or (start_rule == "prev_end_cap" and e[j] is not None
                                                   and (e[j] - s[j]).total_seconds() / SECONDS_PER_YEAR <= cap_years)
            if use_end and status[j] == "known" and e[j] is not None:
                ref = e[j]
            out[row["chunk_id"]] = Inferred(ref, _year_end(ref), "unknown", "start")
        elif s[i] is not None and end_rule == "next_start" and status[i] == "unknown":
            k = next((k for k in range(i + 1, len(rows)) if s[k] is not None and s[k] > s[i]), None)
            if k is None:
                continue
            gap = (s[k] - s[i]).total_seconds() / SECONDS_PER_YEAR
            if max_gap_years is not None and gap > max_gap_years:
                continue
            out[row["chunk_id"]] = Inferred(s[i], s[k], "known", "end")
    return out


def page_of(chunk_id: str) -> tuple[str, int]:
    """`('/wiki/X', 12)` từ `/wiki/X#12`."""
    doc, _, idx = chunk_id.rpartition("#")
    return doc, int(idx)


def group_pages(rows: Iterable[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    """Gom dòng extractions theo trang, mỗi trang sắp theo chỉ số đoạn."""
    pages: dict[str, list[Mapping[str, Any]]] = {}
    for r in rows:
        pages.setdefault(page_of(r["chunk_id"])[0], []).append(r)
    for rs in pages.values():
        rs.sort(key=lambda r: page_of(r["chunk_id"])[1])
    return pages
