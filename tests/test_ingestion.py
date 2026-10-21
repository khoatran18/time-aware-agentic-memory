import json
from datetime import datetime, timezone

import pytest
from tests.conftest import FakeVectorStore

from tam.ingestion.chunking import chunk_document, content_hash
from tam.ingestion.loaders.timeqa import load_pages, page_title
from tam.ingestion.pipeline import IngestionPipeline, Sink, VectorSink
from tam.ingestion.time_extraction import BatchTimes, ChunkTime, TimeExtractor, parse_partial_date, to_span
from tam.ingestion.types import RawDoc, Section


def utc(*a):
    return datetime(*a, tzinfo=timezone.utc)


def make_doc(sections, doc_id="/wiki/Knox_Cunningham"):
    return RawDoc(doc_id=doc_id, title=page_title(doc_id), source="Wikipedia", sections=tuple(Section(*s) for s in sections))


# ---- parse_partial_date / to_span ----
@pytest.mark.parametrize("raw,end,expected", [
    ("1985", False, utc(1985, 1, 1)),
    ("1985", True, utc(1985, 12, 31)),
    ("1985-06", False, utc(1985, 6, 1)),
    ("1985-02", True, utc(1985, 2, 28)),
    ("1984-02", True, utc(1984, 2, 29)),
    ("1136-05-04", False, utc(1136, 5, 4)),
    ("950", False, utc(950, 1, 1)),
])
def test_parse_partial_date(raw, end, expected):
    assert parse_partial_date(raw, end=end) == expected


@pytest.mark.parametrize("raw", ["", "abc", "0", "-44", "1985-13", "1985-02-30", "2005 BC"])
def test_parse_partial_date_rejects(raw):
    with pytest.raises(ValueError):
        parse_partial_date(raw, end=False)


def test_to_span_range_single_ongoing_and_invalid():
    r = to_span(ChunkTime(index=0, start="2004", end="2005")).span
    assert (r.start, r.end) == (utc(2004, 1, 1), utc(2005, 12, 31))
    r = to_span(ChunkTime(index=0, start="1909")).span  # mốc đơn: end = hết kỳ của chính nó
    assert (r.start, r.end) == (utc(1909, 1, 1), utc(1909, 12, 31))
    r = to_span(ChunkTime(index=0, start="2008", end="2012", ongoing=True)).span  # ongoing thắng end
    assert r.end is None
    assert to_span(ChunkTime(index=0)).reason == "no_time"
    assert to_span(ChunkTime(index=0, start="2010", end="2005")).reason == "invalid_time"
    assert to_span(ChunkTime(index=0, start="not a date")).reason == "invalid_time"


# ---- chunking ----
def test_chunk_per_section_with_header_and_stable_ids():
    doc = make_doc([("Knox Cunningham", "Intro text ."), ("Early career", "He was born ."), ("Empty", "   ")])
    chunks = chunk_document(doc)
    assert [c.chunk_id for c in chunks] == ["/wiki/Knox_Cunningham#0", "/wiki/Knox_Cunningham#1"]
    assert chunks[0].text == "Knox Cunningham\nIntro text ."
    assert chunks[1].text == "Knox Cunningham | Early career\nHe was born ."
    assert chunk_document(doc) == chunks  # tất định


def test_content_hash_ignores_case_and_whitespace_only():
    assert content_hash("A  b\n c") == content_hash("a b c")
    assert content_hash("a b c") != content_hash("a b d")


# ---- loader ----
def test_load_pages_filters_and_skips_empty(tmp_path):
    p = tmp_path / "pages.jsonl"
    rows = [
        {"page_id": "/wiki/A_B", "context": "", "paragraphs": [{"title": "A B", "text": "x"}]},
        {"page_id": "/wiki/C", "context": "", "paragraphs": [{"title": "C", "text": "y"}]},
        {"page_id": "/wiki/Empty", "context": "", "paragraphs": []},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert [d.doc_id for d in load_pages(p)] == ["/wiki/A_B", "/wiki/C"]
    docs = list(load_pages(p, page_ids={"/wiki/A_B"}))
    assert len(docs) == 1 and docs[0].title == "A B" and docs[0].source == "Wikipedia" and docs[0].doc_id == "/wiki/A_B"
    assert all(d.source == "Báo A" for d in load_pages(p, source="Báo A"))  # không fix cứng Wikipedia


# ---- TimeExtractor ----
class FakeLLM:
    """with_structured_output trả runnable gọi `fn(messages)`; ghi lại mọi lần gọi."""

    def __init__(self, fn):
        self.fn, self.calls = fn, []

    def with_structured_output(self, schema):
        assert schema is BatchTimes
        outer = self

        class _Chain:
            def invoke(self, messages):
                outer.calls.append(messages)
                return outer.fn(messages)

        return _Chain()


def by_text(table):
    """Fake LLM: tra mốc theo từ khóa có trong từng chunk của lô."""
    def fn(messages):
        items = []
        for block in messages[1][1].split("\n\n"):
            idx = int(block[1:block.index("]")])
            for key, (s, e, on) in table.items():
                if key in block:
                    items.append(ChunkTime(index=idx, start=s, end=e, ongoing=on, ongoing_evidence=key if on else ""))
        return BatchTimes(items=items)
    return fn


def test_extractor_injects_title_numbers_chunks_and_batches():
    doc = make_doc([(f"S{i}", f"text {i}") for i in range(5)])
    chunks = chunk_document(doc)
    llm = FakeLLM(lambda m: BatchTimes(items=[]))
    res = TimeExtractor(llm, batch_size=2).extract(doc.title, chunks)
    assert len(res) == 5 and all(r.reason == "no_time" for r in res)  # LLM bỏ sót = không có mốc
    assert len(llm.calls) == 3
    role, system = llm.calls[0][0]
    assert role == "system" and "Knox Cunningham" in system and "{doc_title}" not in system
    assert llm.calls[2][1][1].startswith("[0] ")  # index lô bắt đầu lại từ 0


def test_extractor_ignores_out_of_range_index_and_accepts_dict():
    doc = make_doc([("A", "x")])
    llm = FakeLLM(lambda m: {"items": [{"index": 7, "start": "2000"}, {"index": 0, "start": "1999"}]})
    res = TimeExtractor(llm).extract(doc.title, chunk_document(doc))
    assert res[0].span.start == utc(1999, 1, 1)


# ---- pipeline ----
class ListSink(Sink):
    def __init__(self):
        self.written = []

    def write(self, chunks):
        self.written.extend(chunks)


def run(docs, table, sinks=None):
    sink = ListSink()
    stats = IngestionPipeline(TimeExtractor(FakeLLM(by_text(table))), sinks or [sink]).run(docs)
    return stats, sink.written


def test_pipeline_counts_drops_and_dedups():
    doc1 = make_doc([
        ("Knox Cunningham", "born 1909 died 1976"),
        ("Career", "no date here"),
        ("Bad", "garbage date"),
        ("Now", "chair since 2012"),
    ])
    doc2 = make_doc([("Knox Cunningham", "born 1909 died 1976")], doc_id="/wiki/Knox_Cunningham")  # trùng hash với doc1 #0
    table = {"born 1909": ("1909", "1976", False), "garbage": ("2010", "2005", False), "since 2012": ("2012", None, True)}
    stats, written = run([doc1, doc2], table)
    assert stats.to_dict() == {"docs": 2, "chunks_total": 5, "ingested": 2, "ingested_undated": 0, "skipped_no_time": 1,
                               "skipped_invalid_time": 1, "skipped_llm_error": 0, "skipped_duplicate": 1}
    by_id = {c.chunk_id: c for c in written}
    assert set(by_id) == {"/wiki/Knox_Cunningham#0", "/wiki/Knox_Cunningham#3"}
    assert by_id["/wiki/Knox_Cunningham#0"].end_time == utc(1976, 12, 31)
    assert by_id["/wiki/Knox_Cunningham#3"].end_time is None  # còn hiệu lực
    assert all(c.source == "Wikipedia" and c.doc_id == "/wiki/Knox_Cunningham" for c in written)


def test_pipeline_no_sink_write_when_nothing_survives():
    sink = ListSink()
    stats = IngestionPipeline(TimeExtractor(FakeLLM(by_text({}))), [sink]).run([make_doc([("A", "nothing")])])
    assert sink.written == [] and stats.ingested == 0 and stats.skipped_no_time == 1


def test_vector_sink_feeds_store_and_retrieval_sees_pre_1970():
    store = FakeVectorStore([])
    doc = make_doc([("Career", "He was prime minister 1955 to 1957")], doc_id="/wiki/Old_Pm")
    stats, _ = run([doc], {"prime minister": ("1955", "1957", False)}, sinks=[VectorSink(store)])
    assert stats.ingested == 1 and store.count() == 1
    assert store.chunks[0].start_time == utc(1955, 1, 1)


def test_domain_labels_are_normalized_and_stored():
    from tam.schemas.domains import normalize_domains

    assert normalize_domains(["Sports", "sports", "weird", "career", "person", "politics"]) == ["sports", "career", "person"]
    res = to_span(ChunkTime(index=0, start="2004", domain=["Politics", "x"]))
    assert res.domains == ("politics",)


def test_facet_matches_list_valued_domain():
    from datetime import datetime, timezone

    from tam.retrieval.temporal.filters import passes_hard_filter
    from tam.schemas.chunk import Chunk
    from tam.stores.vector.base import VectorFilter

    t = datetime(2020, 1, 1, tzinfo=timezone.utc)
    c = Chunk(chunk_id="a#0", text="x", source="s", start_time=t, domain_features={"domain": ["career", "person"]})
    assert passes_hard_filter(c, VectorFilter(t_req=t, facets={"domain": "person"}))
    assert not passes_hard_filter(c, VectorFilter(t_req=t, facets={"domain": "sports"}))


def test_extractor_falls_back_to_text_json_with_markdown_fence():
    class Msg:
        content = '```json\n{"items": [{"index": 0, "start": "1999", "domain": ["sports"], "end": "2001"}]}\n```'

    class BrokenChain:
        def invoke(self, messages):
            BatchTimes.model_validate_json("```json")  # ValidationError, như lỗi parse của proxy

    class Llm:
        def with_structured_output(self, schema):
            return BrokenChain()

        def invoke(self, messages):
            return Msg()

    doc = make_doc([("A", "x")])
    res = TimeExtractor(Llm()).extract(doc.title, chunk_document(doc))
    assert res[0].span is not None and res[0].domains == ("sports",)


def test_parse_text_lowercases_keys():
    from tam.llm.structured import parse_json_text

    out = parse_json_text('{"items": [{"Index": 0, "start": "2000"}]}', BatchTimes)
    assert out.items[0].index == 0


def test_extractor_retries_then_marks_llm_error():
    class Llm:
        calls = 0

        def with_structured_output(self, schema):
            return self

        def invoke(self, messages):
            Llm.calls += 1
            raise ValueError("bad json")

    doc = make_doc([("A", "x")])
    res = TimeExtractor(Llm(), max_attempts=2).extract(doc.title, chunk_document(doc))
    assert res[0].reason == "llm_error" and Llm.calls == 4  # mỗi lần thử: structured + văn bản


def test_ongoing_evidence_check():
    from tam.ingestion.time_extraction import _norm, ongoing_evidence_ok

    corpus = _norm("She has served as chair since 2012 , after joining in 2008 .")  # văn bản của chính chunk
    assert ongoing_evidence_ok("since 2012", corpus)
    assert ongoing_evidence_ok('"Since  2012"', corpus)          # khác hoa thường, khoảng trắng, dấu nháy
    assert not ongoing_evidence_ok("", corpus)                   # không có bằng chứng
    assert not ongoing_evidence_ok("until 2020", corpus)         # không nằm trong văn bản
    assert not ongoing_evidence_ok("joining in 2008", corpus)    # có trong văn bản nhưng không phải dấu hiệu còn hiệu lực


def test_extractor_downgrades_ongoing_without_evidence():
    doc = make_doc([("A", "He joined the club in 2001 ."), ("B", "He is still at the club .")])
    llm = FakeLLM(lambda m: BatchTimes(items=[
        ChunkTime(index=0, start="2001", ongoing=True, ongoing_evidence="", reason_end_date="No end date mentioned"),
        ChunkTime(index=1, start="2001", ongoing=True, ongoing_evidence="still at the club")]))
    r0, r1 = TimeExtractor(llm).extract(doc.title, chunk_document(doc))
    assert r0.ongoing_downgraded and not r0.ongoing
    assert r0.span.end is not None  # về trạng thái "không biết": cuối kỳ của start, không phải NULL
    assert r1.ongoing and not r1.ongoing_downgraded and r1.span.end is None
    # bằng chứng lấy từ chunk khác của cùng trang vẫn được chấp nhận
    llm2 = FakeLLM(lambda m: BatchTimes(items=[
        ChunkTime(index=0, start="2001", ongoing=True, ongoing_evidence="still at the club")]))
    assert not TimeExtractor(llm2).extract(doc.title, chunk_document(doc))[0].ongoing_downgraded
    # bằng chứng không có ở đâu trong trang thì bị hạ
    llm3 = FakeLLM(lambda m: BatchTimes(items=[
        ChunkTime(index=0, start="2001", ongoing=True, ongoing_evidence="since 1999")]))
    assert TimeExtractor(llm3).extract(doc.title, chunk_document(doc))[0].ongoing_downgraded


def test_prompt_version_selects_file():
    import pytest

    from tam.ingestion.time_extraction import prompt_path
    assert prompt_path("v1").name == "ingestion_time_v1.md" and prompt_path("v3").name == "ingestion_time_v3.md"
    for v in ("v1", "v2", "v3"):
        text = prompt_path(v).read_text(encoding="utf-8")
        assert text.count("{doc_title}") == 1 and text.count("{domains}") == 1
    with pytest.raises(ValueError, match="phiên bản"):
        prompt_path("v9")
    assert TimeExtractor(FakeLLM(by_text({})), prompt_version="v2").prompt_version == "v2"
