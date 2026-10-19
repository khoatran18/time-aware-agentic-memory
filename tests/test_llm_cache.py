from pydantic import BaseModel

from tam.llm.cache import JsonCache
from tam.llm.structured import invoke_structured


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
    cache, llm = JsonCache(tmp_path), Llm()
    assert invoke_structured(llm, llm, Out, MSG, cache=cache).answer == "a1"
    assert invoke_structured(llm, llm, Out, MSG, cache=cache).answer == "a1"  # lấy từ cache
    assert llm.calls == 1 and cache.hits == 1 and cache.misses == 1
    assert invoke_structured(llm, llm, Out, [("system", "s"), ("human", "khác")], cache=cache).answer == "a2"
    assert llm.calls == 2


def test_cache_refresh_recalls_and_overwrites(tmp_path):
    llm = Llm()
    invoke_structured(llm, llm, Out, MSG, cache=JsonCache(tmp_path))
    fresh = JsonCache(tmp_path, refresh=True)
    assert invoke_structured(llm, llm, Out, MSG, cache=fresh).answer == "a2"
    assert invoke_structured(llm, llm, Out, MSG, cache=JsonCache(tmp_path)).answer == "a2"  # đã bị ghi đè


def test_failed_result_is_not_cached(tmp_path):
    class Bad(Llm):
        def invoke(self, messages):
            raise ValueError("bad json")

    cache, llm = JsonCache(tmp_path), Bad()
    assert invoke_structured(llm, llm, Out, MSG, max_attempts=1, cache=cache) is None
    assert not list(tmp_path.rglob("*.json"))


def test_corrupt_cache_file_is_ignored(tmp_path):
    cache = JsonCache(tmp_path)
    key = cache.key("Out", "fake-model", "x")
    path = tmp_path / key[:2] / f"{key}.json"
    path.parent.mkdir(parents=True)
    path.write_text("{không phải json", encoding="utf-8")
    assert cache.get(key) is None
