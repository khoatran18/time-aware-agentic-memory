from tam.evaluation.subset import gold_paragraph_indices, paragraph_spans, sample_cases


def _page():
    paragraphs = [{"title": "A", "text": "Alpha one."}, {"title": "B", "text": "Beta two."}, {"title": "C", "text": "Gamma three."}]
    context = "Title . Alpha one. Early . Beta two. Gamma three."
    return context, paragraphs


def test_gold_in_paragraph_heading_and_span():
    context, paragraphs = _page()
    spans = paragraph_spans(context, paragraphs)
    assert all(spans)
    s = context.index("two")
    assert gold_paragraph_indices(spans, [s], [s + 3]) == ([1], [])
    h = context.index("Early")
    assert gold_paragraph_indices(spans, [h], [h + 5]) == ([1], ["answer_in_heading"])
    s2 = context.index("one")
    e2 = context.index("two") + 3
    assert gold_paragraph_indices(spans, [s2], [e2]) == ([0, 1], ["answer_spans_paragraphs"])


def test_sample_is_deterministic_and_balanced():
    rows = [{"idx": f"{r}#{i}", "relation": r} for r in ("P1", "P2") for i in range(10)]
    a = sample_cases(rows, ["P1", "P2"], 3, seed=7)
    assert a == sample_cases(list(reversed(rows)), ["P1", "P2"], 3, seed=7)
    assert [r["relation"] for r in a].count("P1") == 3


def test_sample_by_domain():
    rows = [{"idx": f"{r}#{i}", "relation": r} for r in ("P54", "P39", "P26") for i in range(6)]  # sports, politics, person
    a = sample_cases(rows, ["sports", "politics"], 4, seed=1, group_by="domain")
    assert [r["relation"] for r in a].count("P54") == 4 and [r["relation"] for r in a].count("P39") == 4
    assert not any(r["relation"] == "P26" for r in a)
