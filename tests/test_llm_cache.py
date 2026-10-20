import json

import pytest
from pydantic import BaseModel

from tam.llm.cache import SqliteCache, open_cache
from tam.llm.structured import LlmUnavailable, invoke_structured


class Out(BaseModel):
    answer: str


class Llm:
    model_name = "fake-model"

    def __init__(self):
        self.calls = 0

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        self.calls += 1
        return Out(answer=f"a{self.calls}")


MSG = [("system", "s"), ("human", "q")]


def test_cache_hit_skips_llm_and_key_depends_on_messages(tmp_path):
    cache, llm = open_cache(tmp_path), Llm()
    assert invoke_structured(llm, llm, Out, MSG, cache=cache).answer == "a1"
    assert invoke_structured(llm, llm, Out, MSG, cache=cache).answer == "a1"  # lấy từ cache
    assert llm.calls == 1 and cache.hits == 1 and cache.misses == 1
    assert invoke_structured(llm, llm, Out, [("system", "s"), ("human", "khác")], cache=cache).answer == "a2"
    assert llm.calls == 2


def test_cache_refresh_recalls_and_overwrites(tmp_path):
    llm = Llm()
    invoke_structured(llm, llm, Out, MSG, cache=open_cache(tmp_path))
    fresh = open_cache(tmp_path, refresh=True)
    assert invoke_structured(llm, llm, Out, MSG, cache=fresh).answer == "a2"
    assert invoke_structured(llm, llm, Out, MSG, cache=open_cache(tmp_path)).answer == "a2"  # đã bị ghi đè


def test_failed_result_is_not_cached(tmp_path):
    class Bad(Llm):
        def invoke(self, messages):
            raise ValueError("bad json")

    cache, llm = open_cache(tmp_path), Bad()
    assert invoke_structured(llm, llm, Out, MSG, max_attempts=1, cache=cache) is None
    assert SqliteCache(tmp_path / "cache.sqlite").count() == 0


def test_corrupt_sqlite_value_is_ignored(tmp_path):
    cache = SqliteCache(tmp_path / "c.sqlite")
    key = cache.key("Out", "fake-model", "x")
    cache._db.execute("INSERT INTO cache (key, value) VALUES (?, ?)", (key, "{không phải json"))
    cache._db.commit()
    assert cache.get(key) is None and cache.misses == 1


def test_json_view_mirrors_sqlite_with_metadata(tmp_path):
    cache, llm = open_cache(tmp_path), Llm()
    invoke_structured(llm, llm, Out, MSG, cache=cache)
    cache.close()  # ghi nốt bản JSON
    view = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    (key, entry), = view.items()
    assert entry["schema"] == "Out" and entry["model"] == "fake-model" and entry["preview"] == "q"
    assert entry["value"] == {"answer": "a1"} and entry["created_at"]
    row = SqliteCache(tmp_path / "cache.sqlite").get(key)
    assert row == {"answer": "a1"}


def test_sqlite_is_source_of_truth_json_rebuilt(tmp_path):
    llm = Llm()
    cache = open_cache(tmp_path)
    invoke_structured(llm, llm, Out, MSG, cache=cache)
    cache.close()
    (tmp_path / "cache.json").write_text('{"giả": {"value": {"answer": "sai"}}}', encoding="utf-8")  # bản xem bị sửa tay
    again = open_cache(tmp_path)  # lệch khóa với SQLite nên dựng lại
    assert invoke_structured(llm, llm, Out, MSG, cache=again).answer == "a1"  # vẫn lấy từ SQLite
    again.close()
    view = json.loads((tmp_path / "cache.json").read_text(encoding="utf-8"))
    assert "giả" not in view and len(view) == 1


# ---- chờ khi LLM lỗi tạm thời ----
class _Flaky:
    """Chain giả: lỗi `failures` lần (mã `status`) rồi trả kết quả."""

    def __init__(self, failures, status):
        self.failures, self.status, self.calls = failures, status, 0

    def invoke(self, messages):
        self.calls += 1
        if self.calls <= self.failures:
            err = RuntimeError("down")
            err.status_code = self.status
            raise err
        return {"x": 1}


class _Schema(BaseModel):
    x: int


def test_backoff_waits_then_succeeds():
    waits = []
    chain = _Flaky(3, 503)
    out = invoke_structured(None, chain, _Schema, [("human", "q")], sleep=waits.append)
    assert out.x == 1 and waits == [1, 2, 4]


def test_backoff_gives_up_after_32s():
    waits = []
    with pytest.raises(LlmUnavailable):
        invoke_structured(None, _Flaky(99, 502), _Schema, [("human", "q")], sleep=waits.append)
    assert waits == [1, 2, 4, 8, 16, 32]


def test_auth_error_not_retried():
    waits = []
    chain = _Flaky(99, 401)
    with pytest.raises(RuntimeError):
        invoke_structured(None, chain, _Schema, [("human", "q")], sleep=waits.append)
    assert waits == [] and chain.calls == 1


def test_structured_output_false_skips_structured_call():
    class Plain(BaseModel):
        answer: str

    class Llm2:
        model_name = "fake"

        def __init__(self):
            self.metadata = {"structured_output": False}
            self.structured_calls = self.text_calls = 0

        def structured(self, messages):
            self.structured_calls += 1
            raise ValueError("không ép khuôn được")

        def invoke(self, messages):
            self.text_calls += 1
            return '```json\n{"Answer": "ok"}\n```'

    llm = Llm2()
    chain = type("C", (), {"invoke": lambda self, m: llm.structured(m)})()
    assert invoke_structured(llm, chain, Plain, MSG).answer == "ok"
    assert (llm.structured_calls, llm.text_calls) == (0, 1)  # không tốn request structured
    llm.metadata = {}
    assert invoke_structured(llm, chain, Plain, MSG).answer == "ok"
    assert (llm.structured_calls, llm.text_calls) == (1, 2)  # mặc định vẫn thử structured trước


def test_provider_rate_limit_error_without_status_code_is_transient():
    from tam.llm.structured import _is_transient

    class ModelRateLimitError(Exception):
        pass

    class GoogleRateLimitError(ModelRateLimitError):
        pass

    assert _is_transient(GoogleRateLimitError("429 RESOURCE_EXHAUSTED"))
    assert not _is_transient(ValueError("x")) and not _is_transient(RuntimeError("401"))
