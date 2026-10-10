from datetime import datetime, timezone

import pytest

from tam.evaluation.metrics_temporal import (
    EvalCase,
    cases_from_corpus,
    evaluate_retrieval,
    hit_at_k,
    is_future_leak,
    is_invalidated,
    reciprocal_rank,
)
from tam.retrieval.base import Retriever
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.schemas.result import RetrievalResult, ScoredChunk


def test_hit_at_k():
    assert hit_at_k(["a", "b", "c"], {"b"}, 1) == 0.0
    assert hit_at_k(["a", "b", "c"], {"b"}, 2) == 1.0
    assert hit_at_k([], {"b"}, 5) == 0.0


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], {"c"}) == pytest.approx(1 / 3)
    assert reciprocal_rank(["a"], {"x"}) == 0.0


def test_leak_and_invalidated_flags(corpus_chunks):
    by_id = {c.chunk_id: c for c in corpus_chunks}
    t = datetime(2020, 1, 1, tzinfo=timezone.utc)
    assert is_future_leak(by_id["housing_2021"], t) and not is_future_leak(by_id["housing_2018"], t)
    assert is_invalidated(by_id["acme_ceo_false"]) and not is_invalidated(by_id["housing_2018"])


class _FixedRetriever(Retriever):
    """Retriever giả trả đúng danh sách chunk cho trước, để kiểm tra phép tính metric."""

    mechanism = "temporal"

    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query):
        return RetrievalResult(mechanism="temporal", chunks=[ScoredChunk(chunk=c) for c in self.chunks])


def test_evaluate_detects_leak_invalid_and_forbidden(corpus_chunks):
    by_id = {c.chunk_id: c for c in corpus_chunks}
    case = EvalCase(id="c", query="q", t_req="2020-01-01", gold_ids=frozenset({"housing_2018"}),
                    forbidden_ids=frozenset({"housing_2021"}))
    out = evaluate_retrieval(_FixedRetriever([by_id["housing_2021"], by_id["housing_2018"], by_id["acme_ceo_false"]]), [case])
    s = out["summary"]
    assert s["hit@1"] == 0.0 and s["hit@3"] == 1.0 and s["mrr"] == 0.5
    assert s["leakage_rate"] == s["invalidated_rate"] == s["forbidden_rate"] == 1.0


def test_no_answer_case_is_excluded_from_hit_and_mrr(corpus_chunks):
    case = EvalCase(id="none", query="q", t_req="2014-01-01")
    s = evaluate_retrieval(_FixedRetriever([]), [case])["summary"]
    assert s["n_answerable"] == 0 and s["hit@1"] is None and s["mrr"] is None and s["leakage_rate"] == 0.0


def test_corpus_never_leaks_future_or_invalid(fake_store, corpus_data):
    """Bất biến: trên toàn bộ 11 case corpus, leakage và invalidated luôn 0%, kể cả case min-max đang xfail."""
    out = evaluate_retrieval(TemporalRetriever(fake_store), cases_from_corpus(corpus_data))
    s = out["summary"]
    assert s["n_cases"] == len(corpus_data["cases"])
    assert s["leakage_rate"] == 0.0 and s["invalidated_rate"] == 0.0 and s["forbidden_rate"] == 0.0
