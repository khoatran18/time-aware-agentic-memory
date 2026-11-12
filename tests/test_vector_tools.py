"""Công cụ kiểu B (`tam.tools.vector_tools`) trên kho giả. Không cần LLM, Qdrant hay embedding."""
from datetime import datetime, timezone

import pytest

from conftest import FakeVectorStore
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import VectorFilter
from tam.tools.base import ToolError
from tam.tools.vector_tools import VectorTools, parse_date

ACME = "chief executive officer Acme Corp"


def ids(result):
    return list(result.chunk_ids)


def test_parse_date_partial_means_end_of_period():
    assert parse_date("2010") == datetime(2010, 12, 31, tzinfo=timezone.utc)
    assert parse_date("2010-02") == datetime(2010, 2, 28, tzinfo=timezone.utc)
    assert parse_date("2012-02") == datetime(2012, 2, 29, tzinfo=timezone.utc)
    assert parse_date("2010-03-07") == datetime(2010, 3, 7, tzinfo=timezone.utc)
    for bad in ("", "abc", "2010-13", "2010-02-30", "2010-1-1-1"):
        with pytest.raises(ToolError):
            parse_date(bad)


def test_default_search_applies_no_filter(fake_store):
    r = VectorTools(fake_store).vector_search(ACME, k=10)
    assert {"acme_ceo_a", "acme_ceo_c", "acme_ceo_false"} <= set(ids(r))  # cả chunk tương lai lẫn chunk đã vô hiệu


def test_filters_are_agent_choices(fake_store):
    t = VectorTools(fake_store)
    assert "acme_ceo_false" not in ids(t.vector_search(ACME, k=10, include_invalidated=False))
    early = ids(t.vector_search(ACME, k=10, start_before="2010"))
    assert "acme_ceo_a" in early and "acme_ceo_b" not in early and "acme_ceo_c" not in early
    assert "acme_ceo_a" not in ids(t.vector_search(ACME, k=10, start_before="2004"))


def test_mode_selects_branch(fake_store):
    t = VectorTools(fake_store)
    dense, bm25, hybrid = (ids(t.vector_search(ACME, mode=m, k=20)) for m in ("dense", "bm25", "hybrid"))
    assert dense and bm25 and set(hybrid) == set(dense) | set(bm25)  # hybrid gộp cả hai nhánh
    r = fake_store.search(ACME, VectorFilter(t_req=datetime(1970, 1, 1, tzinfo=timezone.utc), exclude_invalidated=False, apply_time=False), 50)
    assert dense == [h.chunk.chunk_id for h in r.dense][:20] and bm25 == [h.chunk.chunk_id for h in r.sparse][:20]


def test_k_offset_and_cap(fake_store):
    t = VectorTools(fake_store, k_cap=2)
    assert len(ids(t.vector_search(ACME, k=10))) == 2  # trần cứng
    full = ids(VectorTools(fake_store).vector_search(ACME, k=4))
    p1, p2 = ids(VectorTools(fake_store).vector_search(ACME, k=2)), ids(VectorTools(fake_store).vector_search(ACME, k=2, offset=2))
    assert p1 + p2 == full
    r = VectorTools(fake_store).vector_search(ACME, k=1)
    assert r.truncated and "offset=1" in r.text


def test_show_time_toggle(fake_store):
    shown = VectorTools(fake_store).vector_search(ACME, k=10).text
    assert "(2005 – 2010-12)" in shown and "marked invalid" in shown and "2019 – present" in shown
    hidden = VectorTools(fake_store, show_time=False).vector_search(ACME, k=10).text
    assert "2005 – 2010-12" not in hidden and "marked invalid" not in hidden and "acme_ceo_a" in hidden


def test_temporal_search_hard_filters_future_and_invalid(fake_store):
    tools = VectorTools(fake_store, TemporalRetriever(fake_store, top_k=10))
    r = tools.temporal_search(ACME, "2010-06-01", k=10)
    assert "acme_ceo_a" in ids(r)
    assert not {"acme_ceo_b", "acme_ceo_c", "acme_ceo_false"} & set(ids(r))
    assert len(ids(tools.temporal_search(ACME, "2020", k=1))) == 1


def test_temporal_search_only_listed_with_retriever(fake_store):
    assert [t.name for t in VectorTools(fake_store).tools()] == ["vector_search", "read_chunk"]
    full = VectorTools(fake_store, TemporalRetriever(fake_store)).tools()
    assert [t.name for t in full] == ["vector_search", "temporal_search", "read_chunk"]
    with pytest.raises(ToolError):
        VectorTools(fake_store).temporal_search("x", "2020")


def _paged_store():
    mk = lambda i: Chunk(chunk_id=f"/wiki/X#{i}", text=f"part {i} of X", source="Wikipedia", start_time=datetime(2000 + i, 1, 1))
    return FakeVectorStore([mk(i) for i in (3, 0, 1, 2, 4, 5)] + [Chunk(chunk_id="/wiki/Y#0", text="other", source="Wikipedia")])


def test_read_chunk_neighbors_in_page_order():
    t = VectorTools(_paged_store())
    assert ids(t.read_chunk("/wiki/X#2")) == ["/wiki/X#2"]
    assert ids(t.read_chunk("/wiki/X#2", neighbors=1)) == ["/wiki/X#1", "/wiki/X#2", "/wiki/X#3"]
    assert ids(t.read_chunk("/wiki/X#0", neighbors=2)) == ["/wiki/X#0", "/wiki/X#1", "/wiki/X#2"]  # đầu trang: không có chunk trước
    assert len(ids(t.read_chunk("/wiki/X#2", neighbors=99))) == 6  # tối đa 5 mỗi phía, trang chỉ có 6 chunk
    with pytest.raises(ToolError, match="không có chunk"):
        t.read_chunk("/wiki/X#9")


def test_tool_schema_and_argument_validation(fake_store):
    tool = VectorTools(fake_store).tools()[0]
    s = tool.schema()["function"]
    assert s["name"] == "vector_search" and "query" in s["parameters"]["properties"] and s["parameters"]["required"] == ["query"]
    with pytest.raises(ToolError, match="k"):
        tool.call({"query": "x", "k": 0})
    with pytest.raises(ToolError, match="mode"):
        tool.call({"query": "x", "mode": "magic"})
    assert tool.call({"query": ACME}).chunk_ids
