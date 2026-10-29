"""Graph lý tưởng, câu hỏi cấu trúc và chấm đầu ra của Cơ chế 2 (không cần Qdrant, không gọi LLM)."""
from tam.evaluation.metrics_timeline import event_coverage, parse_count, score_answer, score_list
from tam.evaluation.timeline_gold import build_cells, graph_context, make_questions, month_index, month_label

PAGE = {"page_id": "/wiki/X", "context": "intro A text. second B text. third C text.",
        "paragraphs": [{"title": "X", "text": "intro A text."}, {"title": "S", "text": "second B text."}, {"title": "S", "text": "third C text."}]}


def _row(q_index, value, start, end, frm, to):
    return {"idx": f"/wiki/X#P1#{q_index}", "page_id": "/wiki/X", "relation": "P1", "q_index": q_index, "time_start": start, "time_end": end,
            "answers": [{"answer": value, "from": frm, "end": to}]}


def _cell(rows=None):
    rows = rows or [_row(0, "Alpha", "Jan 2000", "Dec 2001", 6, 7), _row(1, "Beta", "Jan 2002", "2003", 20, 21), _row(2, "Gamma", "2004", "2005", 34, 35)]
    return build_cells({"/wiki/X": PAGE}, rows, {"P1": "role"})[0]


def test_month_index_and_label():
    assert month_index("May 1997") == 1997 * 12 + 5
    assert month_index("1997") < month_index("1997", end=True)
    assert month_index("bad") is None
    assert month_label(month_index("May 1997")) == "May 1997"


def test_build_cell_orders_events_and_flags_completeness():
    cell = _cell()
    assert [e["value"] for e in cell["events"]] == ["Alpha", "Beta", "Gamma"] and cell["complete"]
    assert cell["events"][0]["chunk_ids"] == ["/wiki/X#0"]
    gap = _cell([_row(0, "Alpha", "2000", "2001", 6, 7), _row(2, "Gamma", "2004", "2005", 34, 35)])
    assert not gap["complete"]


def test_questions_have_deterministic_answers():
    qs = {q["kind"]: q for q in make_questions(_cell())}
    assert qs["list"]["gold_answer"] == ["Alpha", "Beta", "Gamma"] and qs["count"]["gold_answer"] == 3
    assert qs["first"]["gold_answer"] == "Alpha" and qs["last"]["gold_answer"] == "Gamma"
    assert all(q["reliable"] for q in qs.values())
    assert make_questions(_cell([_row(0, "Alpha", "2000", "2001", 6, 7)])) == []


def test_incomplete_cell_has_no_last_or_successor_and_is_unreliable():
    kinds = {q["kind"] for q in make_questions(_cell([_row(0, "Alpha", "2000", "2001", 6, 7), _row(2, "Gamma", "2004", "2005", 34, 35)]))}
    assert "last" not in kinds and "successor" not in kinds


def test_graph_context_lists_events_in_order():
    assert graph_context(_cell(), [2, 0]).splitlines()[1:] == ["- Alpha (Jan 2000 to Dec 2001)", "- Gamma (Jan 2004 to Dec 2005)"]


def test_event_coverage_strict_vs_loose():
    events = [{"chunk_ids": ["a", "b"]}, {"chunk_ids": ["c"]}]
    assert event_coverage(["a", "c"], events) == {"strict": 0.5, "loose": 1.0}


def test_score_list_order_and_extras():
    assert score_list(["Alpha", "Beta", "Gamma"], ["Alpha", "Beta", "Gamma"])["exact"] == 1.0
    swapped = score_list(["Beta", "Alpha", "Gamma"], ["Alpha", "Beta", "Gamma"])
    assert swapped["f1"] == 1.0 and swapped["exact"] == 0.0 and swapped["order"] < 1.0
    extra = score_list(["Alpha", "Beta", "Gamma", "Zeta"], ["Alpha", "Beta", "Gamma"])
    assert extra["recall"] == 1.0 and extra["precision"] == 0.75
    assert score_list(None, ["Alpha"])["f1"] == 0.0


def test_score_answer_by_type():
    q = {c["kind"]: c for c in make_questions(_cell())}
    assert score_answer(q["count"], "3 roles")["exact"] == 1.0 and score_answer(q["count"], "four")["exact"] == 0.0
    assert score_answer(q["first"], "Alpha")["exact"] == 1.0 and score_answer(q["first"], None)["f1"] == 0.0
    assert parse_count("three") == 3 and parse_count(True) is None
