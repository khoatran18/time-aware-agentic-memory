from datetime import datetime, timezone

import pytest

from tam.retrieval.temporal.filters import FACET_KEYS, passes_hard_filter, to_vector_filter
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.stores.vector.base import VectorFilter
from tam.stores.vector.qdrant_store import PAYLOAD_INDEXES


def mk(**kw):
    base = dict(chunk_id="c", text="t", source="s", start_time=datetime(2018, 1, 1), domain_features={"country": "VN"})
    base.update(kw)
    return Chunk(**base)


def flt(**kw):
    return VectorFilter(t_req=datetime(2020, 1, 1, tzinfo=timezone.utc), **kw)


def test_blocks_future_chunk_but_allows_equal_time():
    assert not passes_hard_filter(mk(start_time=datetime(2021, 1, 1)), flt())
    assert passes_hard_filter(mk(start_time=datetime(2020, 1, 1)), flt())


def test_blocks_invalidated_unless_asked():
    c = mk(invalidated_at=datetime(2019, 1, 1))
    assert not passes_hard_filter(c, flt())
    assert passes_hard_filter(c, flt(exclude_invalidated=False))


def test_facets_must_all_match():
    c = mk(domain_features={"country": "VN", "domain": "law"})
    assert passes_hard_filter(c, flt(facets={"country": "VN"}))
    assert passes_hard_filter(c, flt(facets={"country": "VN", "domain": "law"}))
    assert not passes_hard_filter(c, flt(facets={"country": "US"}))
    assert not passes_hard_filter(mk(domain_features={}), flt(facets={"country": "VN"}))


def test_to_vector_filter_copies_query_fields():
    q = ProfiledQuery(semantic_query="x", t_req=datetime(2020, 1, 1), filters={"country": "VN"})
    f = to_vector_filter(q)
    assert f.t_req == q.t_req and f.facets == {"country": "VN"} and f.exclude_invalidated


def test_to_vector_filter_rejects_unindexed_key():
    q = ProfiledQuery(semantic_query="x", t_req=datetime(2020, 1, 1), filters={"source": "báo A"})
    with pytest.raises(ValueError, match="source"):
        to_vector_filter(q)


def test_facet_keys_match_qdrant_payload_indexes():
    indexed = {k.removeprefix("domain_features.") for k in PAYLOAD_INDEXES if k.startswith("domain_features.")}
    assert FACET_KEYS == indexed
