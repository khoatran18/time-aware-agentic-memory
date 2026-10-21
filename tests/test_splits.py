"""Chia tune/valid: trang chỉ thuộc một tập, đủ hạn mức, ưu tiên nguồn D rồi bù C, tái lập theo seed."""
import pytest

from tam.evaluation.splits import assign_pages


def rows(prefix, pages, per_page):
    return [{"idx": f"{prefix}{p}#{i}", "page_id": f"/wiki/{prefix}{p}"} for p in range(pages) for i in range(per_page)]


def pool():
    return {"sports": {"D/train": rows("d", 6, 3), "C/dev": rows("c", 20, 3)}, "career": {"D/train": rows("e", 2, 3), "C/dev": rows("f", 20, 3)}}


def test_pages_disjoint_quota_and_fallback():
    out, owner = assign_pages(pool(), ["tune", "valid"], {"sports": 8, "career": 8}, ("D/train", "C/dev"), max_per_page=3, seed=1)
    pages = {s: {r["page_id"] for r in rows_} for s, rows_ in out.items()}
    assert not pages["tune"] & pages["valid"] and all(owner[p] == "tune" for p in pages["tune"])
    for s in out:
        assert len(out[s]) == 16
        assert sum(1 for r in out[s] if r["_source"] == "D/train") > 0
    career_c = [r for r in out["tune"] + out["valid"] if r["page_id"].startswith("/wiki/f")]
    assert career_c  # career chỉ có 6 câu D mỗi nguồn nên phải bù từ C


def test_sources_split_evenly_between_sets():
    out, _ = assign_pages(pool(), ["tune", "valid"], {"sports": 6, "career": 6}, ("D/train", "C/dev"), max_per_page=3, seed=3)
    d = {s: sum(r["_source"] == "D/train" for r in out[s]) for s in out}
    assert abs(d["tune"] - d["valid"]) <= 3  # xoay vòng theo trang nên lệch tối đa một trang


def test_deterministic_and_error_when_short():
    a, _ = assign_pages(pool(), ["tune", "valid"], {"sports": 5, "career": 5}, ("D/train", "C/dev"), max_per_page=2, seed=7)
    b, _ = assign_pages(pool(), ["tune", "valid"], {"sports": 5, "career": 5}, ("D/train", "C/dev"), max_per_page=2, seed=7)
    assert a == b
    with pytest.raises(ValueError):
        assign_pages(pool(), ["tune"], {"sports": 500, "career": 1}, ("D/train", "C/dev"), max_per_page=3, seed=1)


def test_match_distribution_covers_target_relations_and_prefers_used_pages():
    from tam.evaluation.splits import match_distribution
    rows = [{"idx": f"{r}{p}#{i}", "page_id": f"/wiki/{r}{p}", "relation": r} for r in ("P1", "P2", "P3") for p in range(6) for i in range(2)]
    out = match_distribution(rows, {"P1": 6, "P2": 3, "P3": 1}, 10, max_per_page=2, seed=1)
    rel = {r: sum(x["relation"] == r for x in out) for r in ("P1", "P2", "P3")}
    assert len(out) == 10 and rel["P3"] >= 2 and rel["P1"] > rel["P2"] >= rel["P3"]
    assert len({x["idx"] for x in out}) == 10 and all(sum(x["page_id"] == p for x in out) <= 2 for p in {x["page_id"] for x in out})
    only = match_distribution(rows[:2], {"P1": 1, "PX": 1}, 10, max_per_page=2, seed=1)
    assert len(only) == 2  # hết câu thì trả ít hơn, không báo lỗi
