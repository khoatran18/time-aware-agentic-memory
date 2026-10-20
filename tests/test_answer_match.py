from datetime import datetime, timezone

import pytest

from tam.evaluation.answer_match import answer_hits, contains_answer, is_valid_at, normalize
from tam.evaluation.metrics_temporal import EvalCase, evaluate_retrieval
from tam.retrieval.base import Retriever
from tam.schemas.chunk import Chunk
from tam.schemas.result import RetrievalResult, ScoredChunk


def utc(y, m=1, d=1):
    return datetime(y, m, d, tzinfo=timezone.utc)


def chunk(cid, text, start=None, end=None):
    return Chunk(chunk_id=cid, text=text, source="s", start_time=start, end_time=end)


def test_normalize_lowercases_and_drops_punctuation():
    assert normalize("Woman  Grandmaster ( WGM )") == "woman grandmaster wgm"
    assert normalize("Nicolas  Cage,") == "nicolas cage"


def test_contains_answer_needs_whole_words_and_any_accepted_answer():
    assert contains_answer(["Aston Villa"], "he became manager at Aston Villa .")
    assert contains_answer(["no match", "colonel"], "OKW colonel Meyer")
    assert not contains_answer(["colonel"], "two colonels were present")  # không dính vào chữ khác
    assert not contains_answer(["Aston Villa"], "he joined Villa .")  # không so gần đúng
    assert not contains_answer([""], "bất kỳ")


def test_is_valid_at_requires_start_and_covering_interval():
    t = utc(2012, 4, 1)
    assert is_valid_at(chunk("a", "x", utc(2011), utc(2013)), t)
    assert is_valid_at(chunk("b", "x", utc(2011)), t)  # còn hiệu lực
    assert not is_valid_at(chunk("c", "x", utc(2013)), t)  # bắt đầu sau
    assert not is_valid_at(chunk("d", "x", utc(2000), utc(2005)), t)  # đã hết hạn
    assert not is_valid_at(chunk("e", "x"), t)  # không mốc: coi là không hợp lệ (chặt)


def test_answer_hits_by_k_separates_plain_and_valid():
    chunks = [chunk("1", "Villa only", utc(2000), utc(2005)), chunk("2", "manager of Aston Villa", utc(2011), utc(2013))]
    plain, valid = answer_hits(["Aston Villa"], chunks, utc(2012, 4, 1), (1, 3))
    assert plain == {1: 0.0, 3: 1.0} and valid == {1: 0.0, 3: 1.0}
    plain, valid = answer_hits(["Aston Villa"], [chunk("3", "Aston Villa", utc(1990), utc(1991))], utc(2012), (1,))
    assert plain == {1: 1.0} and valid == {1: 0.0}  # có chuỗi nhưng sai thời kỳ


class _Fixed(Retriever):
    mechanism = "temporal"

    def __init__(self, chunks):
        self.chunks = chunks

    def retrieve(self, query):
        return RetrievalResult(mechanism="temporal", chunks=[ScoredChunk(chunk=c) for c in self.chunks])


def test_evaluate_reports_answer_metrics_and_keeps_hit_at_k():
    right = chunk("gold", "no answer here", utc(2011), utc(2013))
    other = chunk("other", "he managed Aston Villa", utc(2011), utc(2013))
    case = EvalCase(id="q", query="q", t_req=utc(2012, 4, 1), gold_ids=frozenset({"gold"}), answers=("Aston Villa",))
    out = evaluate_retrieval(_Fixed([other, right]), [case], ks=(1, 3))["summary"]
    assert out["hit@1"] == 0.0 and out["hit@3"] == 1.0  # hit@k theo chunk id giữ nguyên
    assert out["ans_hit@1"] == 1.0 and out["ans_valid_hit@1"] == 1.0
    no_answers = EvalCase(id="q2", query="q", t_req=utc(2012), gold_ids=frozenset({"gold"}))
    summary = evaluate_retrieval(_Fixed([right]), [no_answers], ks=(1,))["summary"]
    assert summary["ans_hit@1"] is None  # không có chuỗi đáp án: không tính
    assert summary["hit@1"] == pytest.approx(1.0)
