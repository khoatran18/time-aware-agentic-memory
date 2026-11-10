import json
import time
from uuid import uuid4

from pydantic import BaseModel

from tam.llm import metrics
from tam.llm.structured import invoke_structured


class Out(BaseModel):
    answer: str


class Llm:
    model_name = "fake-model"

    def with_structured_output(self, schema):
        return self

    def invoke(self, messages):
        return Out(answer="a")


def _rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_invoke_structured_writes_invoke_row(tmp_path, monkeypatch):
    f = tmp_path / "m.jsonl"
    monkeypatch.setenv("TAM_LLM_METRICS_FILE", str(f))
    llm = Llm()
    invoke_structured(llm, llm, Out, [("system", "s"), ("human", "q")])
    row = _rows(f)[0]
    assert row["kind"] == "invoke" and row["outcome"] == "ok" and row["attempts"] == 1 and row["e2e_s"] >= 0


def test_no_file_when_metrics_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("TAM_LLM_METRICS_FILE", raising=False)
    llm = Llm()
    assert invoke_structured(llm, llm, Out, [("human", "q")]).answer == "a"  # không lỗi dù không có nơi ghi


class _Gen:
    def __init__(self):
        class M:
            usage_metadata = {"input_tokens": 10, "output_tokens": 5}
        self.message = M()


class _Resp:
    generations = [[_Gen()]]
    llm_output = None


def test_callback_records_tokens_and_errors(tmp_path, monkeypatch):
    f = tmp_path / "m.jsonl"
    monkeypatch.setenv("TAM_LLM_METRICS_FILE", str(f))
    cb, rid = metrics.LlmMetrics("p"), uuid4()
    cb.on_chat_model_start({}, [[]], run_id=rid)
    time.sleep(0.01)
    cb.on_llm_end(_Resp(), run_id=rid)
    err = uuid4()
    cb.on_chat_model_start({}, [[]], run_id=err)

    class E(Exception):
        status_code = 429

    cb.on_llm_error(E(), run_id=err)
    ok, bad = _rows(f)
    assert ok["input_tokens"] == 10 and ok["output_tokens"] == 5 and ok["tokens_per_s"] > 0
    assert bad["ok"] is False and bad["status"] == 429


def test_summarize_percentiles_and_peak(tmp_path):
    f = tmp_path / "m.jsonl"
    rows = [{"kind": "llm_call", "ts": 100 + i, "ok": True, "e2e_s": float(i + 1), "input_tokens": 10, "output_tokens": 5,
             "tokens_per_s": 5.0} for i in range(10)]
    f.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    s = metrics.summarize(f)
    assert s["llm_calls"] == 10 and s["e2e_call_s"]["p50"] == 5.5 and s["RPM_peak"] == 10 and s["TPM_peak"] == 150


def test_measure_stream_ttft(tmp_path, monkeypatch):
    monkeypatch.setenv("TAM_LLM_METRICS_FILE", str(tmp_path / "m.jsonl"))

    class Chunk:
        def __init__(self, c, usage=None):
            self.content, self.usage_metadata = c, usage

    class S:
        def stream(self, messages):
            time.sleep(0.02)
            yield Chunk("a")
            yield Chunk("b")
            yield Chunk("", {"input_tokens": 3, "output_tokens": 2})

    row = metrics.measure_stream(S(), [("human", "q")])
    assert row["ttft_s"] >= 0.02 and row["output_tokens"] == 2 and row["tokens_exact"] and row["tpot_s"] is not None
