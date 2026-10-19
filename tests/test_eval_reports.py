from datetime import datetime, timezone

from tam.evaluation.ingestion_report import alive_chunk_ids, ingestion_report, label_year
from tam.evaluation.profiler_report import profiler_report
from tam.evaluation.retrieval_eval import build_cases, oracle_t_req

SUBSET = {"cases": [
    {"idx": "a#P1#0", "domain": "sports", "time_start": "2004", "time_end": "Dec 2006", "question_hard": "q a",
     "gold_chunk_ids": ["a#1"]},
    {"idx": "b#P2#0", "domain": "politics", "time_start": "1990", "time_end": "1992", "question_hard": "q b",
     "gold_chunk_ids": ["b#0"]},
]}
ROWS = {
    "a#1": {"chunk_id": "a#1", "start": "2004-01-01T00:00:00+00:00", "end": "2006-12-31T00:00:00+00:00", "ongoing": False,
            "skipped": None, "domain": ["sports"]},
    "a#2": {"chunk_id": "a#2", "start": "2010-01-01T00:00:00+00:00", "end": None, "ongoing": True, "skipped": None,
            "domain": [], "ongoing_downgraded": False},
    "b#0": {"chunk_id": "b#0", "start": None, "end": None, "ongoing": False, "skipped": "no_time", "domain": []},
}


def test_label_year():
    assert label_year("Dec 1965") == 1965 and label_year("2005") == 2005


def test_ingestion_report_counts_gold_survival_and_time_accuracy():
    r = ingestion_report(SUBSET, ROWS)
    assert r["chunks_total"] == 3 and r["chunks_loaded"] == 2 and r["skipped"] == {"no_time": 1}
    assert r["gold_total"] == 2 and r["gold_alive"] == 1 and r["gold_dropped"] == [{"chunk_id": "b#0", "reason": "no_time"}]
    assert r["domain_match"] == 1 and r["start_year_equals_label"] == 1 and r["end_year_equals_label"] == 1
    assert r["span_covers_label"] == 1 and r["ongoing_loaded"] == 1
    assert alive_chunk_ids(ROWS) == {"a#1", "a#2"}


def test_profiler_report_domain_agreement():
    profiled = {
        "a#P1#0": {"idx": "a#P1#0", "t_req": "2005-06-01T00:00:00+00:00", "filters": {"domain": "politics"}, "error": None},
        "b#P2#0": {"idx": "b#P2#0", "error": "boom"},
    }
    p = profiler_report(SUBSET, profiled, ROWS)
    assert p["errors"] == 1 and p["t_req_in_label_range"] == 1
    assert p["domain_set"] == 1 and p["domain_filter_would_drop_gold"] == 1  # Profiler nói politics, chunk đúng là sports


def test_oracle_t_req_is_midpoint_of_label_years():
    t = oracle_t_req(SUBSET["cases"][0])
    assert datetime(2004, 1, 1, tzinfo=timezone.utc) < t < datetime(2006, 12, 31, tzinfo=timezone.utc)


def test_build_cases_alive_gold_and_modes():
    cases = build_cases(SUBSET, mode="oracle", alive_ids=alive_chunk_ids(ROWS))
    assert [c.gold_ids for c in cases] == [frozenset({"a#1"}), frozenset()]  # b#0 bị bỏ lúc ingestion
    profiled = {"a#P1#0": {"idx": "a#P1#0", "t_req": "2005-06-01T00:00:00+00:00", "semantic_query": "sq",
                           "filters": {"domain": "sports", "country": "MT"}, "error": None}}
    e2e = build_cases(SUBSET, mode="e2e", profiled=profiled, facets="domain")
    assert len(e2e) == 1 and e2e[0].query == "sq" and e2e[0].filters == {"domain": "sports"}  # country không bao giờ được dùng
    assert build_cases(SUBSET, mode="e2e", profiled=profiled)[0].filters == {}
    oracle_q = build_cases(SUBSET, mode="oracle", profiled=profiled)
    assert oracle_q[0].query == "sq" and oracle_q[1].query == "q b"
