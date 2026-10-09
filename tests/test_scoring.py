import math
from datetime import datetime, timedelta, timezone

import pytest

from tam.retrieval.temporal.scoring import (
    SECONDS_PER_YEAR,
    delta_years,
    final_score,
    is_exact_match,
    temporal_score,
)
from tam.schemas.chunk import Chunk


def utc(y, m=1, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


def mk(start, end=None, cid="c"):
    return Chunk(chunk_id=cid, text="t", source="s", start_time=start, end_time=end)


def test_th1_inside_range_is_one():
    assert temporal_score(mk(utc(2018), utc(2020, 12, 31)), utc(2020), 0.5) == 1.0


def test_th1_open_ended_is_one():
    assert temporal_score(mk(utc(2021)), utc(2026), 0.5) == 1.0


def test_th1_boundaries_inclusive():
    c = mk(utc(2018), utc(2020))
    assert temporal_score(c, utc(2018), 0.5) == 1.0  # t_req == start_time
    assert temporal_score(c, utc(2020), 0.5) == 1.0  # t_req == end_time


def test_th2_decay_values_match_design():
    # design 02: λ=0.5 -> 1 năm ≈ 0.61, 2 năm ≈ 0.37, 5 năm ≈ 0.08
    year = SECONDS_PER_YEAR
    base = datetime(2000, 1, 1, tzinfo=timezone.utc)
    for years, expected in [(1, 0.6065), (2, 0.3679), (5, 0.0821)]:
        t_req = base + timedelta(seconds=years * year)
        c = mk(base, base + timedelta(days=1))  # đã hết hiệu lực trước t_req
        assert temporal_score(c, t_req, 0.5) == pytest.approx(expected, abs=1e-3)


def test_th2_older_scores_lower_and_in_unit_interval():
    t_req = utc(2020)
    near = temporal_score(mk(utc(2018), utc(2019)), t_req, 0.5)
    far = temporal_score(mk(utc(2015), utc(2016)), t_req, 0.5)
    assert 0 < far < near < 1


def test_lambda_zero_means_no_decay():
    assert temporal_score(mk(utc(1990), utc(1991)), utc(2020), 0.0) == 1.0


def test_delta_uses_start_time_not_end_time():
    c = mk(utc(2010), utc(2019))
    assert temporal_score(c, utc(2020), 0.5) == pytest.approx(math.exp(-0.5 * delta_years(utc(2020), utc(2010))))


def test_pre_1970_supported():
    c = mk(utc(1955), utc(1960))
    assert is_exact_match(mk(utc(1955), utc(1960)), utc(1958))
    assert 0 < temporal_score(c, utc(1965), 0.5) < 1


def test_future_chunk_raises():
    with pytest.raises(ValueError, match="Rò rỉ tương lai"):
        temporal_score(mk(utc(2021)), utc(2020), 0.5)


def test_negative_lambda_rejected():
    with pytest.raises(ValueError):
        temporal_score(mk(utc(2018), utc(2019)), utc(2020), -0.1)


def test_final_score_weighted_sum_and_design_example():
    assert final_score(0.9, 0.37, 0.7, 0.3) == pytest.approx(0.741, abs=1e-3)  # luật 2018 trong design 02
    assert final_score(0.92, 0.08, 0.7, 0.3) == pytest.approx(0.668, abs=1e-3)  # luật 2015


def test_final_score_rejects_negative_weight():
    with pytest.raises(ValueError):
        final_score(1, 1, -0.1, 0.3)
