import pytest

from tam.retrieval.temporal.fusion import fuse, normalize_minmax, rrf
from tam.schemas.chunk import Chunk
from tam.stores.vector.base import BranchHits, SearchHit


def hit(cid, score=1.0):
    return SearchHit(chunk=Chunk(chunk_id=cid, text=cid, source="s", start_time="2020-01-01"), score=score)


def test_rrf_matches_design_table():
    # design 02: A (hạng 1, 3), C (hạng 5, 1), B (hạng 2, vắng)
    scores = rrf([["A", "B", "x", "y", "C"], ["C", "z", "A"]], k=60)
    assert scores["A"] == pytest.approx(1 / 61 + 1 / 63)
    assert scores["C"] == pytest.approx(1 / 65 + 1 / 61)
    assert scores["B"] == pytest.approx(1 / 62)
    assert scores["A"] > scores["C"] > scores["B"]


def test_rrf_k_zero_top_rank_dominates():
    s = rrf([["a", "b"]], k=0)
    assert s["a"] == 1.0 and s["b"] == 0.5


def test_rrf_ignores_duplicate_ids_within_branch():
    assert rrf([["a", "a", "b"]], k=60)["b"] == pytest.approx(1 / 62)  # b là hạng 2, không bị đẩy xuống 3


def test_rrf_empty_and_negative_k():
    assert rrf([[], []]) == {}
    with pytest.raises(ValueError):
        rrf([["a"]], k=-1)


def test_minmax_range_and_degenerate_cases():
    assert normalize_minmax([3.0, 1.0, 2.0]) == [1.0, 0.0, 0.5]
    assert normalize_minmax([0.5, 0.5]) == [1.0, 1.0]
    assert normalize_minmax([0.2]) == [1.0]
    assert normalize_minmax([]) == []


def test_fuse_design_example_scores():
    hits = BranchHits(
        dense=[hit("A"), hit("B"), hit("x"), hit("y"), hit("C")],
        sparse=[hit("C"), hit("z"), hit("A")],
    )
    out = {c.chunk_id: s for c, s in fuse(hits, k=60, top_n=50)}
    assert out["A"] == 1.0  # RRF cao nhất -> 1.0
    assert min(out.values()) == 0.0
    lo = 1 / 64  # nhỏ nhất: chunk "y" (hạng 4, chỉ ở dense)
    assert out["C"] == pytest.approx((1 / 65 + 1 / 61 - lo) / (1 / 61 + 1 / 63 - lo))


def test_fuse_keeps_single_branch_chunks_and_sorts_desc():
    hits = BranchHits(dense=[hit("a"), hit("b")], sparse=[hit("c")])
    out = fuse(hits, k=60, top_n=10)
    assert {c.chunk_id for c, _ in out} == {"a", "b", "c"}
    scores = [s for _, s in out]
    assert scores == sorted(scores, reverse=True) and all(0 <= s <= 1 for s in scores)


def test_fuse_truncates_to_top_n_then_normalizes_on_that_set():
    hits = BranchHits(dense=[hit(str(i)) for i in range(10)], sparse=[])
    out = fuse(hits, k=60, top_n=3)
    assert [c.chunk_id for c, _ in out] == ["0", "1", "2"]
    assert out[0][1] == 1.0 and out[-1][1] == 0.0


def test_fuse_empty_and_single():
    assert fuse(BranchHits(dense=[], sparse=[]), 60, 10) == []
    assert [s for _, s in fuse(BranchHits(dense=[hit("a")], sparse=[]), 60, 10)] == [1.0]
