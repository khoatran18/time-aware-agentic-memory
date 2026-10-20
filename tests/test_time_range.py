from datetime import datetime, timezone

import pytest

from tam.query.range_profiler import RangeExtraction, RangeProfiler
from tam.query.time_range import expand_partial, expand_range

T_NOW = datetime(2026, 10, 20, tzinfo=timezone.utc)


def utc(y, m, d):
    return datetime(y, m, d, tzinfo=timezone.utc)


def test_expand_partial_covers_whole_unit():
    assert expand_partial("1990") == (utc(1990, 1, 1), utc(1990, 12, 31))
    assert expand_partial("2024-02") == (utc(2024, 2, 1), utc(2024, 2, 29))  # năm nhuận do code tính, không phải LLM
    assert expand_partial("2019-05-12") == (utc(2019, 5, 12), utc(2019, 5, 12))
    with pytest.raises(ValueError, match="YYYY"):
        expand_partial("March 1990")


@pytest.mark.parametrize(
    "t_start, t_end, bound, expected",
    [
        ("1990", None, "exact", (utc(1990, 1, 1), utc(1990, 12, 31))),
        ("2010-04", "2010-11", "exact", (utc(2010, 4, 1), utc(2010, 11, 30))),
        ("1938-11", None, "after", (utc(1938, 11, 1), utc(2026, 10, 20))),  # không có điểm cuối: qe = T_now
        ("2006-09", None, "before", (utc(2006, 9, 1), utc(2006, 9, 1))),  # không có điểm đầu: qs = qe = X
        (None, None, "none", (utc(2026, 10, 20), utc(2026, 10, 20))),
        ("2026", None, "exact", (utc(2026, 1, 1), utc(2026, 10, 20))),  # qe không vượt T_now
    ],
)
def test_expand_range_rules(t_start, t_end, bound, expected):
    assert expand_range(t_start, t_end, bound, T_NOW) == expected


def test_before_can_open_lower_bound_and_unknown_mode_rejected():
    assert expand_range("2006-09", None, "before", T_NOW, before_lower="min")[0] == utc(1, 1, 1)
    with pytest.raises(ValueError, match="before_lower"):
        expand_range("2006-09", None, "before", T_NOW, before_lower="middle")


class _FakeLLM:
    def __init__(self, answer):
        self.answer = answer

    def with_structured_output(self, schema):
        assert schema is RangeExtraction
        outer = self

        class _Chain:
            def invoke(self, messages):
                return outer.answer

        return _Chain()


def test_range_profiler_sets_t_req_to_start_and_t_end_to_end():
    out = RangeExtraction(semantic_query="x", t_start="2005-08", t_end="2006-09", domain="politics")
    q = RangeProfiler(_FakeLLM(out)).profile("câu hỏi", T_NOW)
    assert q.t_req == utc(2005, 8, 1) and q.t_end == utc(2006, 9, 30) and q.filters == {"domain": "politics"}


def test_range_profiler_rejects_bad_partial_date():
    out = RangeExtraction(semantic_query="x", t_start="mid 1990")
    with pytest.raises(ValueError, match="không hợp lệ"):
        RangeProfiler(_FakeLLM(out)).profile("câu hỏi", T_NOW)
