"""Vòng lặp agent (`tam.agents.loop`) với LLM giả có kịch bản. Không gọi API."""
import json
import time
from typing import Any

import pytest
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import Field

from tam.agents.loop import PROMPT_DIR, AgentLoop, load_system_prompt
from tam.llm.cache import SqliteCache
from tam.tools.text_corpus import Passage, TextCorpus
from tam.tools.text_tools import text_tools


class ScriptedChatModel(BaseChatModel):
    """Trả lần lượt các AIMessage trong `script`; hết kịch bản thì ném lỗi (giả lập lỗi nhà cung cấp). Lưu mọi tin nhắn nhận được."""

    script: list[Any]
    seen: list[Any] = Field(default_factory=list)
    bound: list[Any] = Field(default_factory=list)
    pos: int = 0
    kwargs_seen: list[Any] = Field(default_factory=list)

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        self.bound = list(tools)
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        self.seen.append(list(messages))
        self.kwargs_seen.append(kwargs)
        if self.pos >= len(self.script):
            raise RuntimeError("429 hết hạn mức")
        msg = self.script[self.pos]
        self.pos += 1
        return ChatResult(generations=[ChatGeneration(message=msg)])


class StreamingScriptedModel(ScriptedChatModel):
    """Như ScriptedChatModel nhưng trả lời bằng nhiều chunk (lời gọi công cụ, rồi từng từ, rồi chunk chứa usage) sau `delay` giây, để thử TTFT và TPOT."""

    delay: float = 0.03

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        self.seen.append(list(messages))
        msg = self.script[self.pos]
        self.pos += 1
        time.sleep(self.delay)
        for i, tc in enumerate(msg.tool_calls):
            args = json.dumps(tc["args"])
            yield ChatGenerationChunk(message=AIMessageChunk(content="", tool_call_chunks=[{"name": tc["name"], "args": args, "id": tc["id"], "index": i}]))
            time.sleep(0.01)
        for i, w in enumerate(str(msg.content).split()):
            yield ChatGenerationChunk(message=AIMessageChunk(content=w if i == 0 else " " + w))
            time.sleep(0.01)
        yield ChatGenerationChunk(message=AIMessageChunk(content="", usage_metadata=msg.usage_metadata))


def call(name, args, id="c1"):
    return {"name": name, "args": args, "id": id}


def ai(text="", calls=(), tin=100, tout=10):
    return AIMessage(content=text, tool_calls=list(calls), usage_metadata={"input_tokens": tin, "output_tokens": tout, "total_tokens": tin + tout})


@pytest.fixture()
def corpus():
    return TextCorpus({"Alpha": [Passage("Alpha", 0, "Alpha FC\nFounded in 1900."), Passage("Alpha", 1, "Alpha FC | Honours\nWon the league in 1950.")]})


def loop(corpus, script, **kw):
    llm = ScriptedChatModel(script=script)
    return llm, AgentLoop(llm, text_tools(corpus), load_system_prompt("2026-11-03"), **kw)


def test_answer_after_tool_call(corpus):
    llm, agent = loop(corpus, [ai(calls=[call("grep", {"pattern": "1950"})]), ai("1950")])
    run = agent.run("When did Alpha win the league?", query_id="q1")
    assert (run.answer, run.stop_reason, run.steps, run.tool_calls) == ("1950", "answer", 2, 1)
    assert (run.input_tokens, run.output_tokens) == (200, 20)
    assert run.chunk_ids == ["/wiki/Alpha#1"]
    assert [e["event"] for e in run.trace] == ["llm", "tool", "llm", "end"] and all(e["query_id"] == "q1" for e in run.trace)
    second = llm.seen[1]  # lượt 2 thấy kết quả công cụ
    assert isinstance(second[-1], ToolMessage) and "Alpha [#1]" in second[-1].content and second[-1].tool_call_id == "c1"
    assert "2026-11-03" in llm.seen[0][0].content and llm.seen[0][1].content == "When did Alpha win the league?"
    assert [t["function"]["name"] for t in llm.bound] == ["list_pages", "grep", "read_page"]


def test_first_step_showing_checks_tool_text_not_chunk_ids(corpus):
    """grep chỉ trả đoạn trích: chunk có trong danh sách chưa chắc chuỗi đáp án đã hiện; read_page thì hiện đủ."""
    long_text = "Beta FC\n" + "filler " * 200 + "Won the cup in 1987."
    big = TextCorpus({"Beta": [Passage("Beta", 0, long_text)]})
    _, agent = loop(big, [ai(calls=[call("grep", {"pattern": "Beta"})]), ai(calls=[call("read_page", {"page": "Beta"}, id="c2")]), ai("1987")])
    run = agent.run("When did Beta win the cup?")
    assert run.chunk_ids and run.chunk_ids[0] == "/wiki/Beta#0"  # chunk đã được liệt kê ở lượt 1...
    assert run.first_step_showing(["1987"]) == 2  # ...nhưng chuỗi đáp án chỉ hiện khi đọc cả trang ở lượt 2
    assert run.first_step_showing(["1999"]) is None and run.first_step_showing([]) is None


def test_bad_tool_use_is_returned_to_agent_not_raised(corpus):
    script = [ai(calls=[call("grep", {"pattern": "("}, "a"), call("nope", {}, "b"), call("read_page", {"page": "Alpha", "start": -1}, "c")]), ai("done")]
    llm, agent = loop(corpus, script)
    run = agent.run("q")
    assert run.stop_reason == "answer" and run.tool_calls == 3
    msgs = [m for m in llm.seen[1] if isinstance(m, ToolMessage)]
    assert [m.tool_call_id for m in msgs] == ["a", "b", "c"] and all(m.content.startswith("Error:") for m in msgs)
    assert "không có công cụ 'nope'" in msgs[1].content
    tools = [e for e in run.trace if e["event"] == "tool"]
    assert [e["ok"] for e in tools] == [False, False, False] and run.chunk_ids == []


def test_parallel_tool_calls_all_answered(corpus):
    _, agent = loop(corpus, [ai(calls=[call("list_pages", {}, "a"), call("read_page", {"page": "Alpha"}, "b")]), ai("ok")])
    run = agent.run("q")
    assert run.tool_calls == 2 and run.chunk_ids == ["/wiki/Alpha#0", "/wiki/Alpha#1"]


def test_max_steps_stops_without_answer(corpus):
    _, agent = loop(corpus, [ai(calls=[call("list_pages", {}, f"c{i}")]) for i in range(5)], max_steps=2)
    run = agent.run("q")
    assert (run.answer, run.stop_reason, run.steps, run.tool_calls) == (None, "max_steps", 2, 2)
    assert run.trace[-1]["event"] == "end" and run.trace[-1]["stop_reason"] == "max_steps"


def test_max_tokens_stops_before_running_tool(corpus):
    _, agent = loop(corpus, [ai(calls=[call("list_pages", {}, f"c{i}")], tin=600) for i in range(5)], max_total_tokens=1000)
    run = agent.run("q")
    assert (run.stop_reason, run.steps, run.tool_calls) == ("max_tokens", 2, 1)


def test_llm_error_ends_run_and_is_traced(corpus):
    _, agent = loop(corpus, [ai(calls=[call("list_pages", {})])])  # lượt 2: hết kịch bản -> lỗi
    run = agent.run("q")
    assert run.stop_reason == "llm_error" and run.answer is None
    bad = [e for e in run.trace if e["event"] == "llm" and not e["ok"]]
    assert len(bad) == 1 and "429" in bad[0]["error"]


def test_trace_file_is_jsonl_and_appends(corpus, tmp_path):
    path = tmp_path / "sub" / "agent_trace.jsonl"
    for q in ("q1", "q2"):
        _, agent = loop(corpus, [ai(calls=[call("grep", {"pattern": "1900"})]), ai("1900")], trace_path=path)
        agent.run("when", query_id=q)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [r["query_id"] for r in rows] == ["q1"] * 4 + ["q2"] * 4
    tool = rows[1]
    assert tool["tool"] == "grep" and tool["args"] == {"pattern": "1900"} and tool["chunk_ids"] == ["/wiki/Alpha#0"] and tool["n_chars"] > 0


def test_constructor_validation(corpus):
    llm = ScriptedChatModel(script=[])
    tools = text_tools(corpus)
    with pytest.raises(ValueError, match="trùng"):
        AgentLoop(llm, tools + tools, "p")
    with pytest.raises(ValueError):
        AgentLoop(llm, tools, "p", max_steps=0)


def test_system_prompt_is_neutral():
    """Prompt chung của A và B không được dặn cách xử lý thời gian hay công cụ (nếu không, thiết kế bị nhúng vào agent)."""
    text = (PROMPT_DIR / "agent_v1.md").read_text(encoding="utf-8").lower()
    assert "{t_now}" in text
    for word in ("filter", "future", "before", "after", "start_time", "latest", "most recent", "grep", "vector"):
        assert word not in text
    assert "{t_now}" not in load_system_prompt("2026-11-03")


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def streaming_loop(corpus, script, **kw):
    llm = StreamingScriptedModel(script=script)
    return llm, AgentLoop(llm, text_tools(corpus), load_system_prompt("2026-11-12"), **kw)


def test_streaming_merges_tool_calls_and_measures_ttft_tpot(corpus):
    _, agent = streaming_loop(corpus, [ai(calls=[call("grep", {"pattern": "1950"})]), ai("it was in 1950")])
    run = agent.run("When?")
    assert (run.answer, run.stop_reason, run.tool_calls, run.chunk_ids) == ("it was in 1950", "answer", 1, ["/wiki/Alpha#1"])
    llm_events = [e for e in run.trace if e["event"] == "llm"]
    assert len(llm_events) == 2 and all(e["ttft_s"] >= 0.03 and e["e2e_s"] >= e["ttft_s"] for e in llm_events)
    last = llm_events[-1]  # lượt trả lời: 10 token ra, có thời gian sinh giữa token đầu và cuối
    assert last["tpot_s"] > 0 and last["tokens_per_s"] > 0 and last["tokens_exact"] and last["output_tokens"] == 10
    assert len(run.ttft_s) == 2 and run.llm_time_s >= 0.06 and run.wall_s >= run.llm_time_s + run.tool_time_s - 1e-6
    end = run.trace[-1]
    assert end["event"] == "end" and end["llm_time_s"] > 0 and "tool_time_s" in end and end["input_tokens"] == 200


def test_non_streaming_has_no_ttft(corpus):
    _, agent = loop(corpus, [ai("x")], stream=False)
    run = agent.run("q")
    e = run.trace[0]
    assert e["ttft_s"] is None and e["tpot_s"] is None and e["e2e_s"] >= 0 and e["input_tokens"] == 100 and run.ttft_s == []


def test_calls_log_has_prompt_answer_and_metrics(corpus, tmp_path):
    path = tmp_path / "calls.jsonl"
    _, agent = streaming_loop(corpus, [ai(calls=[call("grep", {"pattern": "1950"})]), ai("1950")], calls_path=path, model_name="opencode_deepseek_flash")
    agent.run("When did Alpha win the league?", query_id="q9")
    r1, r2 = read_jsonl(path)
    assert (r1["query_id"], r1["step"], r1["model"], r1["ok"], r1["prompt_mode"]) == ("q9", 1, "opencode_deepseek_flash", True, "full")
    assert [m["role"] for m in r1["prompt"]] == ["system", "human"] and "2026-11-12" in r1["prompt"][0]["content"]
    assert r1["prompt"][1]["content"] == "When did Alpha win the league?"
    assert r1["output"]["tool_calls"] == [{"id": "c1", "name": "grep", "args": {"pattern": "1950"}}]
    assert r1["metrics"]["input_tokens"] == 100 and r1["metrics"]["ttft_s"] >= 0.03
    assert [m["role"] for m in r2["prompt"]] == ["system", "human", "ai", "tool"]  # prompt đầy đủ mọi lượt
    assert r2["prompt"][2]["tool_calls"][0]["name"] == "grep" and "Alpha [#1]" in r2["prompt"][3]["content"] and r2["prompt"][3]["tool_call_id"] == "c1"
    assert r2["output"]["text"] == "1950"


def test_calls_log_delta_and_off(corpus, tmp_path):
    script = lambda: [ai(calls=[call("list_pages", {})]), ai("done")]
    _, a = loop(corpus, script(), calls_path=tmp_path / "d.jsonl", log_prompts="delta")
    a.run("q")
    r1, r2 = read_jsonl(tmp_path / "d.jsonl")
    assert [m["role"] for m in r1["prompt"]] == ["system", "human"] and [m["role"] for m in r2["prompt"]] == ["ai", "tool"]  # chỉ phần mới
    _, b = loop(corpus, script(), calls_path=tmp_path / "off.jsonl", trace_path=tmp_path / "t.jsonl", log_prompts="off")
    b.run("q")
    assert not (tmp_path / "off.jsonl").exists() and (tmp_path / "t.jsonl").exists()
    with pytest.raises(ValueError, match="log_prompts"):
        loop(corpus, [], log_prompts="all")


def test_calls_log_records_llm_error_with_prompt(corpus, tmp_path):
    _, agent = loop(corpus, [], calls_path=tmp_path / "c.jsonl")  # kịch bản rỗng: lượt 1 lỗi
    run = agent.run("q")
    (row,) = read_jsonl(tmp_path / "c.jsonl")
    assert run.stop_reason == "llm_error" and row["ok"] is False and "429" in row["error"] and row["output"] is None and row["prompt"][1]["content"] == "q"


def test_default_log_paths_use_run_dir(corpus, tmp_path, monkeypatch):
    monkeypatch.setattr("tam.config.logging._run_dir", tmp_path)
    _, agent = loop(corpus, [ai("x")])
    agent.run("q", query_id="r1")
    assert [r["event"] for r in read_jsonl(tmp_path / "agent_trace.jsonl")] == ["llm", "end"]
    assert len(read_jsonl(tmp_path / "agent_calls.jsonl")) == 1
    monkeypatch.setattr("tam.config.logging._run_dir", None)
    _, agent = loop(corpus, [ai("x")])  # chưa setup_logging: không ghi file, vẫn chạy
    assert agent.run("q").answer == "x"


def test_request_headers_are_per_question_and_sent_on_every_call(corpus):
    llm, agent = loop(corpus, [ai(calls=[call("list_pages", {})]), ai("a"), ai("b")], request_headers=lambda qid: {"x-session": f"run-{qid}"})
    agent.run("q1", query_id="q001")
    agent.run("q2", query_id="q002")
    assert [k["extra_headers"] for k in llm.kwargs_seen] == [{"x-session": "run-q001"}, {"x-session": "run-q001"}, {"x-session": "run-q002"}]


class ToolAwareModel(ScriptedChatModel):
    """`bind_tools` trả về bản gắn `tools=` vào kwargs, để biết lượt nào được phép gọi công cụ (kwargs_seen[i] có khóa `tools` hay không)."""

    def bind_tools(self, tools, **kwargs):
        self.bound = list(tools)
        return self.bind(tools=list(tools))


def _tool_texts(messages):
    return [m.content for m in messages if isinstance(m, ToolMessage)]


def test_budget_notice_counts_down_and_last_call_has_no_tools(corpus):
    llm = ToolAwareModel(script=[ai(calls=[call("grep", {"pattern": "Founded"})]), ai(calls=[call("read_page", {"page": "Alpha"}, "c2")]), ai("1900 [Alpha#0]")])
    agent = AgentLoop(llm, text_tools(corpus), load_system_prompt("2026-11-03", "v2"), max_steps=3, budget_notice=True)
    run = agent.run("When was Alpha founded?")
    assert run.stop_reason == "answer" and run.answer == "1900 [Alpha#0]" and run.steps == 3
    assert "tools" in llm.kwargs_seen[0] and "tools" in llm.kwargs_seen[1] and "tools" not in llm.kwargs_seen[2]
    texts = _tool_texts(llm.seen[1])
    assert texts and texts[-1].endswith("[2 of 3 model calls left. Stop searching as soon as you can answer.]")
    last_texts = _tool_texts(llm.seen[2])
    assert "last call and tools are no longer available" in last_texts[-1]
    assert "model calls left" in last_texts[0]  # tin báo cũ nằm yên trong lịch sử (giữ tiền tố cache)


def test_budget_notice_last_call_empty_text_is_not_an_answer(corpus):
    llm = ToolAwareModel(script=[ai(calls=[call("grep", {"pattern": "Founded"})]), ai("")])
    run = AgentLoop(llm, text_tools(corpus), "sys", max_steps=2, budget_notice=True).run("q")
    assert run.answer is None and run.stop_reason == "max_steps" and run.steps == 2


def test_no_budget_notice_by_default(corpus):
    llm = ToolAwareModel(script=[ai(calls=[call("grep", {"pattern": "Founded"})]), ai("done")])
    run = AgentLoop(llm, text_tools(corpus), "sys", max_steps=2).run("q")
    assert run.answer == "done"
    assert all("model calls left" not in t for t in _tool_texts(llm.seen[1]))
    assert "tools" in llm.kwargs_seen[1]


def test_prompt_v2_has_time_reasoning_and_grounding_rules():
    text = (PROMPT_DIR / "agent_v2.md").read_text(encoding="utf-8")
    assert "{t_now}" in text and "{t_now}" not in load_system_prompt("2026-11-03", "v2")
    for phrase in ("whole year or month", "never guess", "do not re-read"):
        assert phrase in text
    assert len(text.split()) < 140  # đã rút gọn, đừng để phình


def test_prompt_variants_v3_v4_differ_only_where_intended():
    v2, v3, v4 = (( PROMPT_DIR / f"agent_v{n}.md").read_text(encoding="utf-8") for n in (2, 3, 4))
    for t in (v3, v4):
        assert "{t_now}" in t and "Answer: <the value(s)>" in t and "Type: stated" in t and "spans a change" in t
    assert "spans a change" not in v2 and "Type:" not in v2
    assert "never guess." in v3 and "partly cover" not in v3
    assert "partly cover" in v4 and "never guess a value that no passage names" in v4


# ---------------- cache từng lần gọi LLM ----------------
def _cached_agent(corpus, llm, cache, salt=""):
    return AgentLoop(llm, text_tools(corpus), "sys", max_steps=4, cache=cache, cache_model="m1", cache_salt=salt, budget_notice=True)


def test_agent_cache_replays_identical_run_without_calling_llm(corpus, tmp_path):
    cache = SqliteCache(tmp_path / "c.sqlite", threadsafe=True)
    script = [ai(calls=[call("grep", {"pattern": "Founded"})], tin=111, tout=7), ai("1900 [Alpha#0]", tin=222, tout=9)]
    llm1 = ToolAwareModel(script=script)
    first = _cached_agent(corpus, llm1, cache).run("When?")
    assert llm1.pos == 2 and first.cache_hits == 0 and first.answer == "1900 [Alpha#0]"
    llm2 = ToolAwareModel(script=[])  # hết kịch bản: mà gọi LLM sẽ ném lỗi
    second = _cached_agent(corpus, llm2, cache).run("When?")
    assert llm2.pos == 0 and not llm2.seen
    assert second.cache_hits == 2 and second.stop_reason == "answer" and second.answer == first.answer
    assert (second.input_tokens, second.output_tokens) == (first.input_tokens, first.output_tokens) == (333, 16)  # số đo lấy từ lần gọi thật
    assert [e.get("cache_hit") for e in second.trace if e["event"] == "llm"] == [True, True]
    assert [e.get("cache_hit") for e in first.trace if e["event"] == "llm"] == [False, False]
    assert cache.count() == 2


def test_agent_cache_salt_or_model_or_prompt_change_misses(corpus, tmp_path):
    cache = SqliteCache(tmp_path / "c.sqlite", threadsafe=True)
    script = [ai("a1")]
    _cached_agent(corpus, ToolAwareModel(script=list(script)), cache, salt="0").run("Q")
    for variant in (lambda: _cached_agent(corpus, ToolAwareModel(script=list(script)), cache, salt="1"),  # đổi salt
                    lambda: AgentLoop(ToolAwareModel(script=list(script)), text_tools(corpus), "other prompt", cache=cache, cache_model="m1", cache_salt="0"),
                    lambda: AgentLoop(ToolAwareModel(script=list(script)), text_tools(corpus), "sys", cache=cache, cache_model="m2", cache_salt="0")):
        assert variant().run("Q").cache_hits == 0


def test_agent_cache_does_not_store_errors_or_empty(corpus, tmp_path):
    cache = SqliteCache(tmp_path / "c.sqlite", threadsafe=True)
    run = _cached_agent(corpus, ToolAwareModel(script=[]), cache).run("Q")  # LLM lỗi ngay
    assert run.stop_reason == "llm_error" and cache.count() == 0
    run = _cached_agent(corpus, ToolAwareModel(script=[ai("")]), cache).run("Q")  # trả rỗng
    assert cache.count() == 0 and run.stop_reason == "answer"


def test_agent_cache_refresh_overwrites(corpus, tmp_path):
    path = tmp_path / "c.sqlite"
    _cached_agent(corpus, ToolAwareModel(script=[ai("old")]), SqliteCache(path, threadsafe=True)).run("Q")
    llm = ToolAwareModel(script=[ai("new")])
    run = _cached_agent(corpus, llm, SqliteCache(path, refresh=True, threadsafe=True)).run("Q")
    assert llm.pos == 1 and run.answer == "new" and run.cache_hits == 0
    run = _cached_agent(corpus, ToolAwareModel(script=[]), SqliteCache(path, threadsafe=True)).run("Q")
    assert run.answer == "new" and run.cache_hits == 1


def test_sqlite_cache_threadsafe_from_threads(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    cache = SqliteCache(tmp_path / "t.sqlite", threadsafe=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda i: cache.put(str(i), {"v": i}), range(50)))
        got = list(pool.map(lambda i: cache.get(str(i)), range(50)))
    assert got == [{"v": i} for i in range(50)] and cache.count() == 50
