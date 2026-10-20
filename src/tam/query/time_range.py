"""Quy mốc thời gian một phần (`YYYY`, `YYYY-MM`, `YYYY-MM-DD`) thành khoảng ngày `[ngày đầu, ngày cuối]` (decisions/07 đề xuất 1).

Profiler chỉ ghi mốc ở độ mịn câu hỏi nêu; code (không phải LLM) mở rộng ra ngày đầu và ngày cuối của đơn vị đó, nên LLM không phải tự tính
ngày cuối tháng. Mọi mốc là ngày lúc 00:00 UTC, khoảng đóng hai đầu, cùng cách ingestion lưu `start_time`/`end_time`.
"""
from __future__ import annotations

import calendar
import re
from datetime import datetime, timezone
from typing import Literal

Bound = Literal["exact", "after", "before", "none"]
BEFORE_LOWER_MODES: tuple[str, ...] = ("point", "min")
MIN_DATE = datetime(1, 1, 1, tzinfo=timezone.utc)  # kho đã loại mốc trước Công nguyên (decisions/05)

_PARTIAL = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")


def expand_partial(raw: str) -> tuple[datetime, datetime]:
    """`(ngày đầu, ngày cuối)` của đơn vị mà `raw` nêu: "2026" thành cả năm, "2026-02" cả tháng, "2026-02-14" đúng một ngày."""
    m = _PARTIAL.match(raw.strip())
    if not m:
        raise ValueError(f"Mốc thời gian không phải YYYY, YYYY-MM hoặc YYYY-MM-DD: {raw!r}")
    year, month, day = int(m.group(1)), m.group(2), m.group(3)
    if day is not None:
        d = datetime(year, int(month), int(day), tzinfo=timezone.utc)
        return d, d
    if month is not None:
        last = calendar.monthrange(year, int(month))[1]
        return datetime(year, int(month), 1, tzinfo=timezone.utc), datetime(year, int(month), last, tzinfo=timezone.utc)
    return datetime(year, 1, 1, tzinfo=timezone.utc), datetime(year, 12, 31, tzinfo=timezone.utc)


def expand_range(
    t_start: str | None, t_end: str | None, bound: Bound, t_now: datetime, *, before_lower: str = "point"
) -> tuple[datetime, datetime]:
    """Khoảng hỏi `[qs, qe]` (ngày, đóng hai đầu) từ đầu ra của Profiler.

    - `exact`: một mốc thì cả đơn vị đó; hai mốc thì từ ngày đầu của `t_start` đến ngày cuối của `t_end`.
    - `after X`: `[ngày đầu của X, T_now]` (`qe` là T_now vì không có điểm cuối).
    - `before X`: `before_lower="point"` (mặc định) thì `[ngày đầu của X, ngày đầu của X]` (chunk gần nhất trước X được ưu tiên nhờ điểm
      lùi về quá khứ); `"min"` thì `[0001-01-01, ngày đầu của X]` (mở cận dưới).
    - `none` hoặc thiếu `t_start`: `[T_now, T_now]`.
    Không bao giờ để `qe` sau `T_now`, và `qs` không sau `qe`.
    """
    if before_lower not in BEFORE_LOWER_MODES:
        raise ValueError(f"before_lower không hợp lệ: {before_lower!r}; cho phép {BEFORE_LOWER_MODES}")
    today = datetime(t_now.year, t_now.month, t_now.day, tzinfo=timezone.utc)
    if bound == "none" or not t_start:
        return today, today
    first, last = expand_partial(t_start)
    if bound == "after":
        qs, qe = first, today
    elif bound == "before":
        qs, qe = (first, first) if before_lower == "point" else (MIN_DATE, first)
    else:
        qs, qe = first, (expand_partial(t_end)[1] if t_end else last)
    if qs > today:  # câu hỏi về tương lai: giữ nguyên khoảng, không ép về hôm nay
        return qs, qe
    return qs, min(qe, today)
