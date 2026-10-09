"""Temporal_Score: TH1 (đúng mốc) = 1.0, TH2 (lùi về quá khứ) = exp(-λ·Δyears); xem docs/design/02, bước 3-4."""
from __future__ import annotations

import math
from datetime import datetime

from tam.schemas.chunk import Chunk

SECONDS_PER_YEAR = 365.25 * 24 * 3600  # năm Julian


def delta_years(t_req: datetime, start_time: datetime) -> float:
    """Khoảng cách `t_req - start_time` tính bằng năm; âm nghĩa là start_time nằm sau t_req (tương lai)."""
    return (t_req - start_time).total_seconds() / SECONDS_PER_YEAR


def is_exact_match(chunk: Chunk, t_req: datetime) -> bool:
    """TH1: chunk còn hiệu lực tại t_req, tức `end_time` rỗng (còn hiệu lực) hoặc `end_time >= t_req`."""
    return chunk.end_time is None or chunk.end_time >= t_req


def temporal_score(chunk: Chunk, t_req: datetime, decay_lambda: float) -> float:
    """TH1 trả 1.0; TH2 trả `exp(-λ·Δyears)` với Δ tính từ `start_time`.

    Chunk có `start_time > t_req` là rò rỉ tương lai; hard filter đã loại, nên gặp ở đây là lỗi và báo ngay
    thay vì chấm điểm im lặng.
    """
    if decay_lambda < 0:
        raise ValueError(f"decay_lambda phải >= 0, nhận {decay_lambda}")
    if chunk.start_time > t_req:
        raise ValueError(
            f"Rò rỉ tương lai: chunk {chunk.chunk_id} có start_time {chunk.start_time} > t_req {t_req}"
        )
    if is_exact_match(chunk, t_req):
        return 1.0
    return math.exp(-decay_lambda * delta_years(t_req, chunk.start_time))


def final_score(semantic: float, temporal: float, w1: float, w2: float) -> float:
    """`W1·Semantic + W2·Temporal`; `semantic` phải là RRF đã min-max về [0,1] để cùng thang với temporal."""
    if w1 < 0 or w2 < 0:
        raise ValueError(f"Trọng số phải >= 0, nhận w1={w1}, w2={w2}")
    return w1 * semantic + w2 * temporal
