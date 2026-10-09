import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tam.config.loader import Config
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.retrieval.temporal.scoring import is_exact_match
from tam.schemas.query import ProfiledQuery
from tam.stores.vector.base import BranchHits, SearchHit, VectorStore

# Các case mà min-max trên Top-N (đúng như design 02) trả sai vì khuếch đại chênh lệch Semantic giữa các phiên bản
# gần như hòa nghĩa (xem test_minmax_turns_semantic_tie_into_gap). strict=True: sửa được fusion thì test này báo XPASS
# để nhớ gỡ dấu xfail.
MINMAX_TIE_BUG = {"housing_2020_exact", "housing_now_open_ended", "traffic_2020_fallback_th2", "acme_now"}


def _cases():
    data = json.loads((Path(__file__).parent / "fixtures" / "temporal_corpus.json").read_text(encoding="utf-8"))
    xfail = pytest.mark.xfail(strict=True, reason="min-max khuếch đại hòa nghĩa")
    marks = {i: xfail for i in MINMAX_TIE_BUG}
    return [pytest.param(c, id=c["id"], marks=marks.get(c["id"], ())) for c in data["cases"]]


@pytest.mark.parametrize("case", _cases())
def test_corpus_case(case, fake_store):
    q = ProfiledQuery(semantic_query=case["query"], t_req=case["t_req"], filters=case.get("filters", {}))
    res = TemporalRetriever(fake_store).retrieve(q)
    ids = [s.chunk.chunk_id for s in res.chunks]

    for absent in case["expect_absent"]:
        assert absent not in ids, f"{absent} lẽ ra bị lọc (tương lai/tin giả/facet), nhận {ids}"
    if case["expect_top"] is None:
        assert not any(i in ids for i in case["expect_absent"])
        return
    assert ids and ids[0] == case["expect_top"], f"top-1 mong đợi {case['expect_top']}, nhận {ids}"
    top = res.chunks[0]
    assert is_exact_match(top.chunk, q.t_req) == (case["expect_th"] == "TH1")


def test_scores_are_in_unit_interval_and_sorted(fake_store):
    q = ProfiledQuery(semantic_query="chief executive officer of Acme Corp", t_req="2026-10-09")
    res = TemporalRetriever(fake_store).retrieve(q)
    finals = [s.final_score for s in res.chunks]
    assert finals == sorted(finals, reverse=True)
    assert all(0 <= s.semantic_score <= 1 and 0 < s.temporal_score <= 1 for s in res.chunks)
    assert res.mechanism == "temporal"


def test_top_k_limits_result(fake_store):
    q = ProfiledQuery(semantic_query="chief executive officer of Acme Corp", t_req="2026-10-09")
    assert len(TemporalRetriever(fake_store, top_k=2).retrieve(q).chunks) == 2


def test_guard_drops_chunks_a_buggy_store_leaks(corpus_chunks):
    """Store lỗi trả cả chunk tương lai và tin giả: retriever vẫn không để chúng vào kết quả."""
    by_id = {c.chunk_id: c for c in corpus_chunks}
    leaky = [SearchHit(chunk=by_id[i], score=1.0) for i in ("housing_2021", "acme_ceo_false", "housing_2018")]

    class LeakyStore(VectorStore):
        def ensure_collection(self, *, recreate=False): ...

        def upsert(self, chunks):
            return 0

        def count(self):
            return 0

        def search(self, query_text, flt, top_n):
            return BranchHits(dense=leaky, sparse=leaky)

    q = ProfiledQuery(semantic_query="x", t_req=datetime(2013, 1, 1, tzinfo=timezone.utc))
    ids = [s.chunk.chunk_id for s in TemporalRetriever(LeakyStore()).retrieve(q).chunks]
    assert ids == []  # housing_2018 cũng bắt đầu sau 2013


def test_empty_store_result_is_empty(fake_store):
    q = ProfiledQuery(semantic_query="zzz không khớp gì", t_req="2020-01-01")
    assert TemporalRetriever(fake_store).retrieve(q).chunks == []


def test_invalid_top_params_rejected(fake_store):
    with pytest.raises(ValueError):
        TemporalRetriever(fake_store, top_k=0)
    with pytest.raises(ValueError):
        TemporalRetriever(fake_store, top_k=10, top_n=5)


def test_from_config(fake_store):
    cfg = Config({"retrieval": {"w1": 0.5, "w2": 0.5, "decay_lambda": 1.0, "rrf_k": 10, "top_n": 20, "top_k": 3}})
    r = TemporalRetriever.from_config(cfg, fake_store)
    q = ProfiledQuery(semantic_query="chief executive officer of Acme Corp", t_req="2026-10-09")
    assert len(r.retrieve(q).chunks) == 3


def test_minmax_turns_semantic_tie_into_gap(fake_store):
    """Hai phiên bản cùng nội dung chỉ khác con số: Semantic gần hòa, nhưng min-max kéo thành 1.0 vs 0.0."""
    q = ProfiledQuery(semantic_query="thời hạn cấp giấy chứng nhận quyền sở hữu nhà ở", t_req="2020-01-01")
    res = {s.chunk.chunk_id: s for s in TemporalRetriever(fake_store).retrieve(q).chunks}
    old, right = res["housing_2015"], res["housing_2018"]  # 2018 là bản đúng (TH1)
    assert right.temporal_score == 1.0 and old.temporal_score < 0.2
    assert abs(old.semantic_score - right.semantic_score) == 1.0  # chênh tối đa dù nội dung gần như y hệt
