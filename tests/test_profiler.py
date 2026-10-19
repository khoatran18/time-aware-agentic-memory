from datetime import datetime, timezone

import pytest

from tam.query.profiler import Extraction, Profiler, parse_t_req

T_NOW = datetime(2023, 10, 10, tzinfo=timezone.utc)


class FakeLLM:
    """Chat model giả: with_structured_output trả runnable luôn trả `answer`, và ghi lại prompt nhận được."""

    def __init__(self, answer):
        self.answer = answer
        self.messages = None

    def with_structured_output(self, schema):
        assert schema is Extraction
        outer = self

        class _Chain:
            def invoke(self, messages):
                outer.messages = messages
                return outer.answer

        return _Chain()


def profile(answer, question="câu hỏi", t_now=T_NOW):
    llm = FakeLLM(answer)
    return Profiler(llm).profile(question, t_now), llm


def test_t_now_is_injected_into_system_prompt():
    _, llm = profile(Extraction(semantic_query="x", t_req="2023-10-03"), t_now=datetime(2031, 2, 5))
    role, system = llm.messages[0]
    assert role == "system" and "2031-02-05" in system and "{t_now}" not in system
    assert llm.messages[1] == ("human", "câu hỏi")


def test_relative_time_result_becomes_absolute_utc():
    q, _ = profile(Extraction(semantic_query="ông A làm gì", t_req="2023-10-03"))
    assert q.t_req == datetime(2023, 10, 3, tzinfo=timezone.utc) and q.mechanism == "temporal"


@pytest.mark.parametrize("raw,expected", [
    ("2020", datetime(2020, 1, 1, tzinfo=timezone.utc)),
    ("2020-03", datetime(2020, 3, 1, tzinfo=timezone.utc)),
    ("1955-06-15", datetime(1955, 6, 15, tzinfo=timezone.utc)),
    ("2020-03-01T10:00:00+07:00", datetime(2020, 3, 1, 3, tzinfo=timezone.utc)),
])
def test_parse_t_req(raw, expected):
    assert parse_t_req(raw) == expected


def test_no_time_mentioned_means_now():
    q, _ = profile(Extraction(semantic_query="CEO of Acme Corp", t_req=None))
    assert q.t_req == T_NOW


def test_filters_normalized_and_limited_to_indexed_facets():
    q, _ = profile(Extraction(semantic_query="x", t_req="2020", domain=" Law ", country="vn"))
    assert q.filters == {"domain": "law", "country": "VN"}
    q, _ = profile(Extraction(semantic_query="x", t_req="2020", domain="  ", country=None))
    assert q.filters == {}


def test_dict_output_is_accepted():
    q, _ = profile({"semantic_query": "x", "t_req": "2020", "domain": None, "country": None})
    assert q.t_req.year == 2020


def test_empty_semantic_query_falls_back_to_question():
    q, _ = profile(Extraction(semantic_query="  ", t_req="2020"), question="  giữ nguyên tên Acme Corp ")
    assert q.semantic_query == "giữ nguyên tên Acme Corp"


def test_garbage_t_req_raises_with_context():
    with pytest.raises(ValueError, match="không phải ISO"):
        profile(Extraction(semantic_query="x", t_req="tuần trước"), question="Q?")


def test_future_t_req_warns_but_passes(caplog):
    with caplog.at_level("WARNING"):
        q, _ = profile(Extraction(semantic_query="x", t_req="2030-01-01"))
    assert q.t_req.year == 2030 and "sau T_now" in caplog.text


def test_cache_skips_use_t_now_and_empty_t_req(tmp_path):
    from tam.llm.cache import open_cache
    cache = open_cache(tmp_path)
    fixed = Extraction(semantic_query="x", t_req="1968-08-01", use_t_now=False)
    Profiler(FakeLLM(fixed), cache=cache).profile("Who ran it in Aug 1968?", T_NOW)
    assert cache._primary.count() == 1
    relative = Extraction(semantic_query="x", t_req="2022-10-10", use_t_now=True)
    Profiler(FakeLLM(relative), cache=cache).profile("Who ran it last year?", T_NOW)
    Profiler(FakeLLM(Extraction(semantic_query="x", t_req=None)), cache=cache).profile("Who ran it?", T_NOW)  # t_req rỗng
    assert cache._primary.count() == 1
    # khóa không chứa ngày: ngày khác vẫn trúng
    llm2 = FakeLLM(fixed)
    Profiler(llm2, cache=cache).profile("Who ran it in Aug 1968?", datetime(2031, 1, 1, tzinfo=timezone.utc))
    assert llm2.messages is None
    cache.close()
