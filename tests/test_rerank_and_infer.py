"""Cross-encoder rerank, chunk liền kề của Plain RAG, suy luận mốc thời gian từ chunk liền kề, hệ số chunk suy luận."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from conftest import FakeVectorStore
from tam.ingestion.infer_time import group_pages, infer_page
from tam.retrieval.baseline import PlainRetriever
from tam.retrieval.temporal.rerank import minmax, mix_scores, rerank_text
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.retrieval.temporal.scoring import temporal_score
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery


def utc(y, m=1, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


def mk(cid, text, year, end=None):
    return Chunk(chunk_id=cid, text=text, source="s", start_time=utc(year), end_time=utc(end) if end else None)


class FakeReranker:
    """Điểm = số lần chunk chứa từ `gold` (tất định)."""

    def __init__(self, gold):
        self.gold, self.calls = gold, []

    def score(self, query, texts):
        self.calls.append(list(texts))
        return [float(t.count(self.gold)) for t in texts]


def _store():
    return FakeVectorStore([
        mk("a#0", "alpha beta common words here", 2000),
        mk("a#1", "alpha common words gamma", 2001),
        mk("a#2", "common words", 2002),
        mk("b#0", "alpha beta common", 2003),
    ])


def test_minmax_and_mix():
    assert minmax([1, 3, 2]) == [0.0, 1.0, 0.5] and minmax([2, 2]) == [1.0, 1.0] and minmax([]) == []
    assert mix_scores([1.0, 0.0], [0, 10], "replace", 0.5) == [0.0, 1.0]
    assert mix_scores([1.0, 0.0], [0, 10], "mix", 0.5) == [0.5, 0.5]
    with pytest.raises(ValueError):
        mix_scores([1.0], [1.0], "bad", 0.5)


def test_rerank_text_with_time():
    c = mk("x#0", "text", 1990, 1995)
    assert rerank_text(c, with_time=False) == "text" and rerank_text(c, with_time=True) == "[1990-1995] text"
    assert rerank_text(mk("x#1", "t", 2000), with_time=True) == "[2000-now] t"


def test_rerank_replace_changes_order_and_trace():
    q = ProfiledQuery(semantic_query="alpha beta common words", t_req="2010-01-01")
    base = TemporalRetriever(_store(), top_k=3).retrieve(q)
    fr = FakeReranker("gamma")
    res = TemporalRetriever(_store(), top_k=3, reranker=fr, rerank_top=4, rerank_mode="replace", w1=1.0, w2=0.0).retrieve(q)
    assert res.chunks[0].chunk.chunk_id == "a#1" != base.chunks[0].chunk.chunk_id  # CE đẩy chunk chứa 'gamma' lên đầu
    assert res.trace.ranked_ids[0] == "a#1" and set(res.trace.ranked_ids) == set(base.trace.ranked_ids)
    assert len(fr.calls) == 1 and len(fr.calls[0]) == 4


def test_rerank_pool_limit_keeps_tail_order():
    q = ProfiledQuery(semantic_query="alpha beta common words", t_req="2010-01-01")
    base = TemporalRetriever(_store(), top_k=4, w1=1.0, w2=0.0).retrieve(q)
    res = TemporalRetriever(_store(), top_k=4, reranker=FakeReranker("zzz"), rerank_top=2, rerank_mode="replace", w1=1.0, w2=0.0).retrieve(q)
    assert res.trace.ranked_ids[2:] == base.trace.ranked_ids[2:]  # ngoài nhóm rerank giữ nguyên thứ tự


def test_rerank_validation():
    with pytest.raises(ValueError):
        TemporalRetriever(_store(), reranker=FakeReranker("x"), rerank_mode="bad")
    with pytest.raises(ValueError):
        TemporalRetriever(_store(), reranker=FakeReranker("x"), rerank_top=0)
    with pytest.raises(ValueError):
        TemporalRetriever(_store(), reranker=FakeReranker("x"), rerank_pool="bad")


def test_plain_retriever_neighbors():
    q = ProfiledQuery(semantic_query="alpha beta common words", t_req="2010-01-01")
    assert PlainRetriever(_store(), method="dense", top_k=1).retrieve(q).neighbors == []
    res = PlainRetriever(_store(), method="dense", top_k=1, neighbor_window=1).retrieve(q)
    top = res.chunks[0].chunk.chunk_id
    assert top == "a#0" and [c.chunk_id for c in res.neighbors] == ["a#1"]
    with pytest.raises(ValueError):
        PlainRetriever(_store(), neighbor_window=-1)


def _rows():
    def r(i, start, end, status, undated=False):
        return {"chunk_id": f"/wiki/P#{i}", "start": start and f"{start}T00:00:00+00:00", "end": end and f"{end}T00:00:00+00:00",
                "end_status": status, "undated": undated, "skipped": None if start else "no_time"}
    return [
        r(0, "1950-01-01", "2000-12-31", "known"),      # đời người
        r(1, None, None, None, undated=True),            # không mốc
        r(2, "1970-01-01", "1970-12-31", "unknown"),     # chỉ biết bắt đầu
        r(3, "1980-01-01", None, "ongoing"),
        r(4, "1985-01-01", "1985-12-31", "unknown"),
    ]


def test_infer_start_rules():
    rows = _rows()
    a = infer_page(rows, start_rule="prev_end")["/wiki/P#1"]
    assert (a.start.year, a.inferred, a.end_status) == (2000, "start", "unknown")
    b = infer_page(rows, start_rule="prev_start")["/wiki/P#1"]
    assert b.start.year == 1950
    c = infer_page(rows, start_rule="prev_end_cap", cap_years=10)["/wiki/P#1"]
    assert c.start.year == 1950  # khoảng 1950-2000 dài hơn cap nên rơi về start
    assert "/wiki/P#2" not in infer_page(rows, start_rule="prev_end")  # đã có mốc thì không đụng


def test_infer_end_rule_and_ongoing_untouched():
    out = infer_page(_rows(), end_rule="next_start")
    assert (out["/wiki/P#2"].end.year, out["/wiki/P#2"].end_status, out["/wiki/P#2"].inferred) == (1980, "known", "end")
    assert "/wiki/P#3" not in out            # ongoing không suy
    assert "/wiki/P#4" not in out            # không còn chunk dated nào sau
    assert "/wiki/P#2" not in infer_page(_rows(), end_rule="next_start", max_gap_years=5)  # cách 10 năm > 5
    assert infer_page(_rows()) == {}
    with pytest.raises(ValueError):
        infer_page(_rows(), start_rule="bad")


def test_group_pages_orders_by_index():
    rows = [{"chunk_id": "/wiki/A#10"}, {"chunk_id": "/wiki/A#2"}, {"chunk_id": "/wiki/B#0"}]
    assert [r["chunk_id"] for r in group_pages(rows)["/wiki/A"]] == ["/wiki/A#2", "/wiki/A#10"]


def test_inferred_factor_scales_temporal_score_only_for_inferred():
    real = mk("x#0", "t", 2000, 2010)
    inf = real.model_copy(update={"time_inferred": "end"})
    t = utc(2005)
    assert temporal_score(inf, t, 0.5, inferred_factor=0.6) == pytest.approx(0.6)
    assert temporal_score(real, t, 0.5, inferred_factor=0.6) == 1.0
    assert temporal_score(inf, t, 0.5) == 1.0                      # mặc định 1.0 = giữ hành vi cũ


def test_cross_encoder_score_cache(tmp_path, monkeypatch):
    """Điểm đã chấm được đọc lại từ sqlite, không gọi model lần hai."""
    from tam.retrieval.temporal import rerank as mod

    calls = []

    class Fake:
        def __init__(self, **kw): ...

        def rerank(self, query, docs):
            calls.append(list(docs))
            return [float(len(d)) for d in docs]

    import sys
    import types
    fake_mod = types.ModuleType("fastembed.rerank.cross_encoder")
    fake_mod.TextCrossEncoder = Fake
    monkeypatch.setitem(sys.modules, "fastembed.rerank.cross_encoder", fake_mod)
    r = mod.CrossEncoderReranker("m", score_cache=tmp_path / "c.sqlite")
    assert r.score("q", ["aa", "bbb"]) == [2.0, 3.0]
    assert r.score("q", ["aa", "bbb", "c"]) == [2.0, 3.0, 1.0]
    assert calls == [["aa", "bbb"], ["c"]]
    assert mod.CrossEncoderReranker("m", score_cache=tmp_path / "c.sqlite").score("q", ["aa"]) == [2.0]  # tiến trình khác đọc lại được
    assert len(calls) == 2


def test_plain_retriever_rerank_changes_order():
    q = ProfiledQuery(semantic_query="alpha beta common words", t_req="2010-01-01")
    base = PlainRetriever(_store(), method="dense", top_k=4).retrieve(q)
    res = PlainRetriever(_store(), method="dense", top_k=4, reranker=FakeReranker("gamma"), rerank_top=4).retrieve(q)
    assert res.chunks[0].chunk.chunk_id == "a#1" != base.chunks[0].chunk.chunk_id
    assert res.trace.ranked_ids[0] == "a#1" and set(res.trace.ranked_ids) == set(base.trace.ranked_ids)


def test_normalize_kinds():
    from tam.retrieval.temporal.rerank import normalize
    xs = [-2.0, 0.0, 3.0]
    assert normalize(xs, "minmax") == [0.0, 0.4, 1.0]
    sg = normalize(xs, "sigmoid")
    assert sg == sorted(sg) and all(0 < v < 1 for v in sg) and normalize([100.0], "sigmoid") == [1.0]
    assert abs(sum(normalize(xs, "softmax")) - 1) < 1e-9
    z = normalize(xs, "zscore")
    assert z == sorted(z) and normalize([1.0, 1.0], "zscore") == [0.5, 0.5]
    with pytest.raises(ValueError):
        normalize(xs, "bad")
    with pytest.raises(ValueError):
        TemporalRetriever(_store(), reranker=FakeReranker("x"), rerank_norm="bad")


def test_rerank_without_temporal_orders_by_ce_only():
    store = FakeVectorStore([mk("a#0", "alpha beta gamma", 1990, 1995), mk("a#1", "alpha beta", 2005)])
    q = ProfiledQuery(semantic_query="alpha beta", t_req="2010-01-01")
    with_t = TemporalRetriever(store, top_k=2, reranker=FakeReranker("gamma"), rerank_top=2, w1=0.1, w2=0.9).retrieve(q)
    no_t = TemporalRetriever(store, top_k=2, reranker=FakeReranker("gamma"), rerank_top=2, w1=0.1, w2=0.9, rerank_temporal=False).retrieve(q)
    assert with_t.chunks[0].chunk.chunk_id == "a#1"   # chunk còn hiệu lực thắng khi Temporal nặng
    assert no_t.chunks[0].chunk.chunk_id == "a#0"     # bỏ Temporal ở lần hai: chỉ còn điểm cross-encoder
