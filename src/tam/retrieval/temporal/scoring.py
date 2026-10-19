"""Temporal_Score: TH1 (đúng mốc) = 1.0, TH2 (lùi về quá khứ) = exp(-λ·Δyears); xem docs/design/02, bước 3-4.

Cách xử lý chunk có `end_status` `ongoing`/`unknown` (decisions/02), chọn bằng `end_mode`:
- `stored` (C, mặc định): theo `end_time` đã lưu (`ongoing` = rỗng, TH1 mãi; `unknown` = hết kỳ của `start`).
- `open` (A): `ongoing` và `unknown` đều coi là còn hiệu lực, TH1 = 1.0 mãi.
- `decay` (B): `ongoing` và `unknown` giảm nhẹ theo khoảng cách `start` tới `t_req`: `exp(-open_decay·Δyears)`.
Chunk `known` hoặc không có `end_status` luôn theo `end_time`.

Chunk không có mốc (`start_time` rỗng, decisions/04) nhận điểm cố định `t_unknown`, không có TH1 hay TH2.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Literal

from tam.schemas.chunk import Chunk

SECONDS_PER_YEAR = 365.25 * 24 * 3600  # năm Julian

EndMode = Literal["stored", "open", "decay"]
END_MODES: tuple[str, ...] = ("stored", "open", "decay")


def delta_years(t_req: datetime, start_time: datetime) -> float:
    """Khoảng cách `t_req - start_time` tính bằng năm; âm nghĩa là start_time nằm sau t_req (tương lai)."""
    return (t_req - start_time).total_seconds() / SECONDS_PER_YEAR


def is_exact_match(chunk: Chunk, t_req: datetime) -> bool:
    """TH1: chunk còn hiệu lực tại t_req, tức `end_time` rỗng (còn hiệu lực) hoặc `end_time >= t_req`."""
    return chunk.start_time is not None and (chunk.end_time is None or chunk.end_time >= t_req)


def temporal_score(
    chunk: Chunk, t_req: datetime, decay_lambda: float, *, end_mode: EndMode = "stored", open_decay: float = 0.1,
    t_unknown: float | None = None,
) -> float:
    """TH1 trả 1.0; TH2 trả `exp(-λ·Δyears)` với Δ tính từ `start_time`; `end_mode` xem docstring module.

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
    if chunk.start_time > t_req:
        raise ValueError(
            f"Rò rỉ tương lai: chunk {chunk.chunk_id} có start_time {chunk.start_time} > t_req {t_req}"
        )
    if end_mode != "stored" and chunk.end_status in ("ongoing", "unknown"):
        if end_mode == "open":
            return 1.0
        return math.exp(-open_decay * delta_years(t_req, chunk.start_time))
    if is_exact_match(chunk, t_req):
        return 1.0
    return math.exp(-decay_lambda * delta_years(t_req, chunk.start_time))


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
