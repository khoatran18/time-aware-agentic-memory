"""Temporal_Score: TH1 (đúng mốc) = 1.0, TH2 (lùi về quá khứ) = exp(-λ·Δyears); xem docs/design/02, bước 3-4.

Cách xử lý chunk có `end_status` `ongoing`/`unknown` (decisions/02), chọn bằng `end_mode`:
- `stored` (C, mặc định): theo `end_time` đã lưu (`ongoing` = rỗng, TH1 mãi; `unknown` = hết kỳ của `start`).
- `open` (A): `ongoing` và `unknown` đều coi là còn hiệu lực, TH1 = 1.0 mãi.
- `decay` (B): `ongoing` và `unknown` giảm nhẹ theo khoảng cách `start` tới `t_req`: `exp(-open_decay·Δyears)`.
- `unknown_decay` (mới, decisions/06): chỉ `unknown` giảm theo `exp(-open_decay·Δyears)`; `ongoing` giữ như `stored` (TH1 = 1.0 mãi,
  vì có câu trích làm bằng chứng). Ba chế độ trên giữ nguyên hành vi.
Chunk `known` hoặc không có `end_status` luôn theo `end_time`.

Chunk không có mốc (`start_time` rỗng, decisions/04) nhận điểm cố định `t_unknown`, không có TH1 hay TH2.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from tam.schemas.chunk import Chunk

SECONDS_PER_YEAR = 365.25 * 24 * 3600  # năm Julian

EndMode = Literal["stored", "open", "decay", "unknown_decay"]
END_MODES: tuple[str, ...] = ("stored", "open", "decay", "unknown_decay")
DecayFrom = Literal["start", "end"]
DECAY_FROMS: tuple[str, ...] = ("start", "end")
TimeMode = Literal["point", "range"]  # point: một điểm t_req (design 02); range: khoảng [qs, qe] (decisions/07 đề xuất 1)
TIME_MODES: tuple[str, ...] = ("point", "range")
Overlap = Literal["binary", "coverage"]  # chế độ range: giao nhau = 1.0, hay độ phủ |C ∩ Q| / |Q|
OVERLAPS: tuple[str, ...] = ("binary", "coverage")


def delta_years(t_req: datetime, start_time: datetime) -> float:
    """Khoảng cách `t_req - start_time` tính bằng năm; âm nghĩa là start_time nằm sau t_req (tương lai)."""
    return (t_req - start_time).total_seconds() / SECONDS_PER_YEAR


def is_exact_match(chunk: Chunk, t_req: datetime) -> bool:
    """TH1: chunk còn hiệu lực tại t_req, tức `end_time` rỗng (còn hiệu lực) hoặc `end_time >= t_req`."""
    return chunk.start_time is not None and (chunk.end_time is None or chunk.end_time >= t_req)


def temporal_score(
    chunk: Chunk, t_req: datetime, decay_lambda: float, *, end_mode: EndMode = "stored", open_decay: float = 0.1,
    t_unknown: float | None = None, decay_from: DecayFrom = "start",
) -> float:
    """TH1 trả 1.0; TH2 trả `exp(-λ·Δyears)` với Δ tính từ `start_time` (mặc định) hoặc từ `end_time` (`decay_from="end"`,
    decisions/07 đề xuất 3: chunk sống lâu vừa hết hạn không bị phạt như chunk cổ); `end_mode` xem docstring module.

    Chunk có `start_time > t_req` là rò rỉ tương lai; hard filter đã loại, nên gặp ở đây là lỗi và báo ngay
    thay vì chấm điểm im lặng.
    """
    if chunk.start_time is None:
        if t_unknown is None:
            raise ValueError(f"Chunk {chunk.chunk_id} không có mốc nhưng t_unknown chưa được đặt")
        return t_unknown
    if decay_lambda < 0 or open_decay < 0:
        raise ValueError(f"decay_lambda và open_decay phải >= 0, nhận {decay_lambda}, {open_decay}")
    if end_mode not in END_MODES:
        raise ValueError(f"end_mode không hợp lệ: {end_mode!r}; cho phép {END_MODES}")
    if decay_from not in DECAY_FROMS:
        raise ValueError(f"decay_from không hợp lệ: {decay_from!r}; cho phép {DECAY_FROMS}")
    if chunk.start_time > t_req:
        raise ValueError(
            f"Rò rỉ tương lai: chunk {chunk.chunk_id} có start_time {chunk.start_time} > t_req {t_req}"
        )
    if end_mode == "unknown_decay":
        if chunk.end_status == "unknown":
            return math.exp(-open_decay * delta_years(t_req, chunk.start_time))
    elif end_mode != "stored" and chunk.end_status in ("ongoing", "unknown"):
        if end_mode == "open":
            return 1.0
        return math.exp(-open_decay * delta_years(t_req, chunk.start_time))
    if is_exact_match(chunk, t_req):
        return 1.0
    anchor = chunk.end_time if decay_from == "end" and chunk.end_time is not None else chunk.start_time
    return math.exp(-decay_lambda * delta_years(t_req, anchor))


def temporal_score_range(
    chunk: Chunk, qs: datetime, qe: datetime, decay_lambda: float, *, end_mode: EndMode = "stored", open_decay: float = 0.1,
    t_unknown: float | None = None, decay_from: DecayFrom = "start", overlap: Overlap = "binary",
) -> float:
    """Điểm thời gian của chunk với KHOẢNG hỏi `[qs, qe]` (decisions/07 đề xuất 1); `qs == qe` thì giống `temporal_score`.

    - Chunk giao khoảng hỏi (`start <= qe` do hard filter, và `end` rỗng hoặc `end >= qs`): 1.0 (`overlap="binary"`), hoặc độ phủ
      `|C ∩ Q| / |Q|` tính theo ngày đóng hai đầu (`overlap="coverage"`, ít nhất một ngày nên luôn > 0).
    - Chunk đã hết hạn trước `qs`: `exp(-λ·Δyears)`, Δ từ `start` (mặc định) hoặc từ `end` (`decay_from="end"`) đến `qs`.
    - `ongoing`/`unknown` theo `end_mode` như `temporal_score`, Δ tính đến `qs` và không âm (chunk bắt đầu trong khoảng hỏi: Δ = 0).
    - Chunk không mốc: `t_unknown`.
    Chunk có `start_time > qe` là rò rỉ tương lai (hard filter đã loại): báo lỗi thay vì chấm im lặng.
    """
    if qe < qs:
        raise ValueError(f"Khoảng hỏi ngược: qs {qs} > qe {qe}")
    if chunk.start_time is None:
        if t_unknown is None:
            raise ValueError(f"Chunk {chunk.chunk_id} không có mốc nhưng t_unknown chưa được đặt")
        return t_unknown
    if decay_lambda < 0 or open_decay < 0:
        raise ValueError(f"decay_lambda và open_decay phải >= 0, nhận {decay_lambda}, {open_decay}")
    if end_mode not in END_MODES:
        raise ValueError(f"end_mode không hợp lệ: {end_mode!r}; cho phép {END_MODES}")
    if decay_from not in DECAY_FROMS:
        raise ValueError(f"decay_from không hợp lệ: {decay_from!r}; cho phép {DECAY_FROMS}")
    if overlap not in OVERLAPS:
        raise ValueError(f"overlap không hợp lệ: {overlap!r}; cho phép {OVERLAPS}")
    if chunk.start_time > qe:
        raise ValueError(f"Rò rỉ tương lai: chunk {chunk.chunk_id} có start_time {chunk.start_time} > qe {qe}")

    def years_to_qs(anchor: datetime) -> float:
        return max(0.0, delta_years(qs, anchor))

    if end_mode == "unknown_decay":
        if chunk.end_status == "unknown":
            return math.exp(-open_decay * years_to_qs(chunk.start_time))
    elif end_mode != "stored" and chunk.end_status in ("ongoing", "unknown"):
        if end_mode == "open":
            return 1.0
        return math.exp(-open_decay * years_to_qs(chunk.start_time))
    if chunk.end_time is None or chunk.end_time >= qs:
        if overlap == "coverage":
            lo, hi = max(chunk.start_time, qs), min(chunk.end_time or qe, qe)
            return max(0.0, ((hi - lo).days + 1) / ((qe - qs).days + 1))
        return 1.0
    anchor = chunk.end_time if decay_from == "end" else chunk.start_time
    return math.exp(-decay_lambda * years_to_qs(anchor))


def domain_score(chunk: Chunk, query_domains: list[str]) -> float:
    """1.0 nếu chunk có ít nhất một nhãn domain trùng domain của câu hỏi (chunk có tới 3 nhãn), ngược lại 0.0."""
    have = chunk.domain_features.get("domain")
    labels = set(have) if isinstance(have, list) else ({have} if have else set())
    return 1.0 if labels & set(query_domains) else 0.0


def final_score(semantic: float, temporal: float, w1: float, w2: float, domain: float = 0.0, w3: float = 0.0) -> float:
    """`W1·Semantic + W2·Temporal + W3·Domain`; `semantic` phải là RRF đã min-max về [0,1] để cùng thang với temporal."""
    if w1 < 0 or w2 < 0 or w3 < 0:
        raise ValueError(f"Trọng số phải >= 0, nhận w1={w1}, w2={w2}, w3={w3}")
    return w1 * semantic + w2 * temporal + w3 * domain
