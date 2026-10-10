from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.schemas.result import RetrievalResult, ScoredChunk


def mk(**kw):
    base = {"chunk_id": "c1", "text": "t", "source": "s", "start_time": datetime(1985, 1, 1)}
    base.update(kw)
    return Chunk(**base)


def test_naive_datetime_becomes_utc():
    assert mk().start_time.tzinfo == timezone.utc


def test_pre_1970_supported():
    c = mk(start_time=datetime(1850, 1, 1))
    assert c.start_time.year == 1850
    assert Chunk.model_validate(c.model_dump(mode="json")).start_time == c.start_time


def test_end_before_start_rejected():
    with pytest.raises(ValidationError):
        mk(end_time=datetime(1980, 1, 1))


def test_defaults_open_and_valid():
    c = mk()
    assert c.end_time is None and c.invalidated_at is None and c.domain_features == {}


def test_profiled_query_utc_and_default_mechanism():
    q = ProfiledQuery(semantic_query="x", t_req=datetime(2020, 1, 1))
    assert q.t_req.tzinfo == timezone.utc and q.mechanism == "temporal"


def test_result_roundtrip():
    r = RetrievalResult(mechanism="temporal", chunks=[ScoredChunk(chunk=mk(), final_score=0.5)])
    assert RetrievalResult.model_validate(r.model_dump(mode="json")) == r


def test_chunk_doc_id_is_optional_and_independent_of_source():
    assert Chunk(chunk_id="c", text="t", source="Wikipedia", start_time=datetime(2020, 1, 1)).doc_id is None
    c = Chunk(chunk_id="/wiki/A#1", text="t", source="Wikipedia", doc_id="/wiki/A", start_time=datetime(2020, 1, 1))
    assert c.source == "Wikipedia" and c.doc_id == "/wiki/A"
