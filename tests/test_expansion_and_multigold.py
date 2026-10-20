"""Chunk liền kề, W3·Domain_Match và metric cho câu cần nhiều chunk."""
from __future__ import annotations

from datetime import datetime, timezone

from conftest import FakeVectorStore
from tam.evaluation.metrics_temporal import EvalCase, all_hit_at_k, evaluate_retrieval, recall_at_k
from tam.ingestion.time_extraction import ChunkTime, to_span
from tam.retrieval.temporal.expansion import neighbor_ids, split_chunk_id
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery


def utc(y):
    return datetime(y, 1, 1, tzinfo=timezone.utc)


def mk(cid, text, year, domain=None):
    return Chunk(chunk_id=cid, text=text, source="s", start_time=utc(year), domain_features={"domain": domain} if domain else {})


def test_split_and_neighbor_ids():
    assert split_chunk_id("/wiki/A#12") == ("/wiki/A", 12) and split_chunk_id("noidx") is None
    assert neighbor_ids(["/wiki/A#0", "/wiki/A#1"], 1) == ["/wiki/A#2"]  # #-1 bị bỏ, #1 và #0 là chính chúng
    assert neighbor_ids(["/wiki/A#5"], 2) == ["/wiki/A#4", "/wiki/A#6", "/wiki/A#3", "/wiki/A#7"]


def _store():
    return FakeVectorStore([
        mk("p#0", "zebra rare unique keyword", 2000),
        mk("p#1", "other words only", 2005),
        mk("p#2", "different content again", 2030),   # tương lai so với t_req: không được làm ngữ cảnh
    ])


def test_neighbors_added_and_filtered():
    q = ProfiledQuery(semantic_query="zebra rare unique keyword", t_req="2010-01-01")
    plain = TemporalRetriever(_store(), top_k=1).retrieve(q)
    assert plain.neighbors == []
    res = TemporalRetriever(_store(), top_k=1, neighbor_window=2).retrieve(q)
    assert [s.chunk.chunk_id for s in res.chunks] == ["p#0"]
    assert [c.chunk_id for c in res.neighbors] == ["p#1"]   # p#2 start 2030 > t_req nên bị loại


def test_domain_boost_changes_order():
    store = FakeVectorStore([mk("a#0", "alpha beta gamma", 2000, ["sports"]), mk("b#0", "alpha beta gamma", 2000, ["media_arts"])])
    q = ProfiledQuery(semantic_query="alpha beta gamma", t_req="2010-01-01", domains=["media_arts"])
    assert TemporalRetriever(store, top_k=2).retrieve(q).chunks[0].chunk.chunk_id == "a#0"        # hòa điểm: theo chunk_id
    top = TemporalRetriever(store, top_k=2, w3=1.0).retrieve(q).chunks
    assert top[0].chunk.chunk_id == "b#0" and top[0].domain_score == 1.0 and top[1].domain_score == 0.0


def test_multi_gold_metrics():
    ranked = ["x", "g1", "y", "g2"]
    assert recall_at_k(ranked, {"g1", "g2"}, 2) == 0.5 and recall_at_k(ranked, {"g1", "g2"}, 4) == 1.0
    assert all_hit_at_k(ranked, {"g1", "g2"}, 2) == 0.0 and all_hit_at_k(ranked, {"g1", "g2"}, 4) == 1.0
    assert all_hit_at_k(ranked, set(), 4) == 0.0


def test_summary_has_multi_gold_and_context_keys():
    cases = [
        EvalCase(id="one", query="zebra rare unique keyword", t_req="2010-01-01", gold_ids=frozenset({"p#0"})),
        EvalCase(id="two", query="zebra rare unique keyword", t_req="2010-01-01", gold_ids=frozenset({"p#0", "p#1"})),
    ]
    s = evaluate_retrieval(TemporalRetriever(_store(), top_k=1, neighbor_window=1), cases, (1,))["summary"]
    assert s["n_multi_gold"] == 1
    assert s["multi_all_hit@1"] == 0.0 and s["multi_recall@1"] == 0.5   # top-1 chỉ có p#0
    assert s["ctx_multi_all_hit"] == 1.0                                # thêm p#1 từ chunk liền kề
    assert s["ctx_size_mean"] == 2.0


def test_to_span_end_status():
    assert to_span(ChunkTime(index=0, start="2000", end="2005")).end_status == "known"
    assert to_span(ChunkTime(index=0, start="2000", ongoing=True)).end_status == "ongoing"
    assert to_span(ChunkTime(index=0, start="2000")).end_status == "unknown"


# ---- baseline, vết từng bước, chunk không mốc ----
from tam.evaluation.funnel import best_rank, stage_ranks, summarize_stages
from tam.retrieval.baseline import PlainRetriever


def _timeline_store():
    return FakeVectorStore([
        mk("old#0", "zebra rare keyword", 2000),
        mk("new#0", "zebra rare keyword", 2030),   # tương lai so với t_req 2010
        Chunk(chunk_id="und#0", text="zebra rare keyword", source="s", domain_features={}),  # không mốc
    ])


def test_plain_retriever_ignores_time_and_leaks():
    q = ProfiledQuery(semantic_query="zebra rare keyword", t_req="2010-01-01")
    for method in ("dense", "bm25", "hybrid"):
        res = PlainRetriever(_timeline_store(), method=method, top_k=5).retrieve(q)
        assert {s.chunk.chunk_id for s in res.chunks} == {"old#0", "new#0", "und#0"}   # không lọc gì
        assert res.trace is not None and res.trace.ranked_ids == [s.chunk.chunk_id for s in res.chunks][: len(res.trace.ranked_ids)]


def test_dated_branch_excludes_undated_unless_t_unknown_set():
    q = ProfiledQuery(semantic_query="zebra rare keyword", t_req="2010-01-01")
    base = TemporalRetriever(_timeline_store(), top_k=5).retrieve(q)
    assert {s.chunk.chunk_id for s in base.chunks} == {"old#0"}                     # không mốc và tương lai đều bị loại
    with_und = TemporalRetriever(_timeline_store(), top_k=5, t_unknown=0.5).retrieve(q)
    got = {s.chunk.chunk_id: s for s in with_und.chunks}
    assert set(got) == {"old#0", "und#0"} and got["und#0"].temporal_score == 0.5 and got["old#0"].temporal_score == 1.0


def test_trace_and_stage_summary():
    q = ProfiledQuery(semantic_query="zebra rare keyword", t_req="2010-01-01")
    res = TemporalRetriever(_timeline_store(), top_k=5, t_unknown=0.5).retrieve(q)
    ranks = stage_ranks(res.trace, {"old#0"})
    assert ranks["dense"] and ranks["fused"] and ranks["final"] == 1                # TH1 (1.0) đứng trên không mốc (0.5)
    rows = [{"has_gold": True, "stages": {"dense": 1, "sparse": 1, "fused": 3, "final": 1}},
            {"has_gold": True, "stages": {"dense": None, "sparse": 2, "fused": 2, "final": 4}}]
    s = summarize_stages(rows, (1, 3))
    assert s["temporal_helped"] == 1 and s["temporal_hurt"] == 1 and s["cand_recall_dense"] == 0.5
    assert s["hit@3_pre"] == 1.0 and s["hit@1_pre"] == 0.0
    assert best_rank(["a", "b"], {"b"}) == 2 and best_rank(["a"], {"z"}) is None


def test_pipeline_keeps_undated_only_with_content():
    from conftest import FakeVectorStore as _F  # noqa: F401  (đảm bảo import conftest hợp lệ)
    from tam.ingestion.pipeline import IngestionPipeline, Sink
    from tam.ingestion.time_extraction import BatchTimes, ChunkTime, TimeExtractor
    from tam.ingestion.types import RawDoc, Section

    class _Sink(Sink):
        def __init__(self):
            self.written = []

        def write(self, chunks):
            self.written.extend(chunks)

    class _Llm:
        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            return BatchTimes(items=[ChunkTime(index=0, domain=["place"]), ChunkTime(index=1)])  # chunk 1 không nhãn domain

    doc = RawDoc(doc_id="/wiki/X", title="X", source="Wikipedia", sections=(Section("A", "Pskov is a city."), Section("B", "References")))
    for keep, expect in ((False, 0), (True, 1)):
        sink = _Sink()
        stats = IngestionPipeline(TimeExtractor(_Llm()), [sink], keep_undated=keep).run([doc])
        assert stats.ingested_undated == expect and len(sink.written) == expect
        assert all(c.start_time is None for c in sink.written)


def test_top_pages_and_page_candidates():
    from tam.retrieval.temporal.expansion import page_candidate_ids, top_pages
    ranked = ["A#5", "B#0", "A#9", "C#1", "D#2"]
    assert top_pages(ranked, 3) == {"A": [5, 9], "B": [0], "C": [1]}  # D bị cắt; A#9 vẫn thuộc trang A
    ids = page_candidate_ids(["A#5", "A#9"], 1)["A"]
    assert len(ids) == 98 and "A#5" not in ids and "A#9" not in ids
    assert ids[:4] == ["A#4", "A#6", "A#8", "A#10"]  # gần chunk của Top-K trước, hòa thì chỉ số nhỏ trước


def _page_store():
    end = lambda c, y: c.model_copy(update={"end_time": utc(y)})
    return FakeVectorStore([
        mk("p#0", "zebra rare unique keyword", 2000),
        end(mk("p#1", "expired section", 1990), 1995),                # hết hạn trước t_req
        mk("p#2", "valid section later", 2005),                       # hợp lệ tại 2010
        mk("p#3", "future section", 2030),                            # tương lai
        Chunk(chunk_id="p#4", text="no date", source="s"),            # không mốc
        mk("q#0", "other page", 2001),
    ])


def test_page_expand_time_vs_page():
    q = ProfiledQuery(semantic_query="zebra rare unique keyword", t_req="2010-01-01")
    base = TemporalRetriever(_page_store(), top_k=1).retrieve(q)
    assert base.neighbors == []
    timed = TemporalRetriever(_page_store(), top_k=1, page_expand="time", page_per=5).retrieve(q)
    assert [c.chunk_id for c in timed.neighbors] == ["p#2"]   # p#1 hết hạn, p#3 tương lai, p#4 không mốc, q#0 khác trang
    page = TemporalRetriever(_page_store(), top_k=1, page_expand="page", page_per=5).retrieve(q)
    assert [c.chunk_id for c in page.neighbors] == ["p#1", "p#2"]  # đối chứng: chỉ hard filter (hết hạn vẫn lấy; tương lai, không mốc bị loại)
    capped = TemporalRetriever(_page_store(), top_k=1, page_expand="page", page_per=1).retrieve(q)
    assert [c.chunk_id for c in capped.neighbors] == ["p#1"]


def test_page_expand_validation():
    import pytest
    with pytest.raises(ValueError):
        TemporalRetriever(_page_store(), page_expand="bad")
    with pytest.raises(ValueError):
        TemporalRetriever(_page_store(), page_expand="time", page_per=0)
