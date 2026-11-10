"""Đo hiệu năng cuộc gọi LLM: E2E, token vào/ra, lỗi 429/5xx, thử lại; TTFT/TPOT/tokens-s qua streaming.

Cách dùng:
    - `factory.get_llm` gắn `LlmMetrics` vào model, nên mọi lần gọi (kể cả qua `invoke_structured`, `with_structured_output`)
      được ghi một dòng `kind="llm_call"` vào `llm_calls.jsonl`. Không đổi chữ ký hàm nào.
    - `invoke_structured` ghi thêm `kind="invoke"` cho cả lần gọi hàm (gồm thử lại, chờ backoff, cache hit).
    - `measure_stream(llm, messages)` đo TTFT/TPOT bằng streaming (đường riêng cho bài đo, không dùng cho pipeline).
    - `summarize(path)` tính p50/p90/p99, throughput, TPM/RPM đo được, số lỗi từ file.

File ghi vào `get_run_dir()/llm_calls.jsonl` nếu đã `setup_logging()`; nếu không thì vào đường dẫn của biến môi trường
`TAM_LLM_METRICS_FILE`; không có cả hai thì bỏ qua (không lỗi). Mỗi dòng một JSON; ghi có khóa nên an toàn khi nhiều luồng.
"""
from __future__ import annotations

import json
import os
import threading
import time
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from tam.config.logging import _query_id, get_logger, get_run_dir

logger = get_logger(__name__)

_LOCK = threading.Lock()
FILE_NAME = "llm_calls.jsonl"


def metrics_path() -> Path | None:
    """Nơi ghi: thư mục của lần chạy nếu đã setup_logging, không thì `TAM_LLM_METRICS_FILE`, không thì None (tắt)."""
    env = os.getenv("TAM_LLM_METRICS_FILE")
    if env:
        return Path(env)
    try:
        return get_run_dir() / FILE_NAME
    except RuntimeError:
        return None


def record(entry: dict[str, Any]) -> None:
    """Ghi một dòng JSON (kèm `ts`, `query_id`). Không bao giờ ném lỗi ra ngoài: đo đạc không được làm hỏng lần chạy."""
    path = metrics_path()
    if path is None:
        return
    try:
        row = {"ts": time.time(), "query_id": _query_id.get(), **entry}
        line = json.dumps(row, ensure_ascii=False)
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Không ghi được llm_calls.jsonl: %s", exc)


def _usage_from(response: Any) -> tuple[int | None, int | None]:
    """(token vào, token ra) từ kết quả của langchain, hoặc (None, None) nếu API không trả usage."""
    try:
        for gens in response.generations:
            for gen in gens:
                usage = getattr(getattr(gen, "message", None), "usage_metadata", None)
                if usage:
                    return usage.get("input_tokens"), usage.get("output_tokens")
        out = (response.llm_output or {}).get("token_usage") or {}
        if out:
            return out.get("prompt_tokens"), out.get("completion_tokens")
    except Exception:  # noqa: BLE001
        pass
    return None, None


class LlmMetrics(BaseCallbackHandler):
    """Callback của langchain: mỗi lần model được gọi thật (kể cả lần thử lại) ghi một dòng `llm_call`."""

    raise_error = False

    def __init__(self, profile: str = "") -> None:
        self.profile = profile
        self._start: dict[UUID, float] = {}

    def on_chat_model_start(self, serialized: Any, messages: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Ghi mốc gửi."""
        self._start[run_id] = time.perf_counter()

    def on_llm_start(self, serialized: Any, prompts: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Ghi mốc gửi (model không phải chat)."""
        self._start[run_id] = time.perf_counter()

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        """Ghi một lần gọi thành công."""
        t0 = self._start.pop(run_id, None)
        tin, tout = _usage_from(response)
        e2e = None if t0 is None else time.perf_counter() - t0
        record({"kind": "llm_call", "profile": self.profile, "ok": True, "e2e_s": e2e, "input_tokens": tin,
                "output_tokens": tout, "tokens_per_s": (tout / e2e if tout and e2e else None)})

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        """Ghi một lần gọi lỗi, kèm mã HTTP nếu có (429 = chạm giới hạn)."""
        t0 = self._start.pop(run_id, None)
        record({"kind": "llm_call", "profile": self.profile, "ok": False,
                "e2e_s": None if t0 is None else time.perf_counter() - t0,
                "status": getattr(error, "status_code", None), "error": type(error).__name__})


def attach(llm: Any, profile: str) -> Any:
    """Gắn `LlmMetrics` vào model (giữ callback sẵn có). Trả lại chính model."""
    existing = list(getattr(llm, "callbacks", None) or [])
    if not any(isinstance(c, LlmMetrics) for c in existing):
        llm.callbacks = [*existing, LlmMetrics(profile)]
    return llm


def measure_stream(llm: Any, messages: list[tuple[str, str]], *, label: str = "") -> dict[str, Any]:
    """Đo một lần gọi bằng streaming: TTFT, TPOT, tokens/s, E2E. Đường riêng cho bài đo hiệu năng.

    TTFT = t(chunk có nội dung đầu) - t_gửi. TPOT = (t_cuối - t_đầu) / (số token ra - 1); số token ra lấy từ
    `usage_metadata` nếu API trả, không thì đếm số chunk có nội dung (xấp xỉ, ghi `tokens_exact=False`).
    """
    t_send = time.perf_counter()
    t_first = t_last = None
    n_chunks, usage_out, usage_in = 0, None, None
    for chunk in llm.stream(messages):
        usage = getattr(chunk, "usage_metadata", None)
        if usage:
            usage_in, usage_out = usage.get("input_tokens", usage_in), usage.get("output_tokens", usage_out)
        if getattr(chunk, "content", ""):
            now = time.perf_counter()
            t_first = t_first or now
            t_last = now
            n_chunks += 1
    t_done = time.perf_counter()
    n_out = usage_out if usage_out else n_chunks
    ttft = None if t_first is None else t_first - t_send
    gen = None if t_first is None or t_last is None else t_last - t_first
    row = {"kind": "stream", "label": label, "ttft_s": ttft, "e2e_s": t_done - t_send, "output_tokens": n_out,
           "input_tokens": usage_in, "tokens_exact": bool(usage_out),
           "tpot_s": (gen / (n_out - 1) if gen is not None and n_out > 1 else None),
           "tokens_per_s": (n_out / gen if gen and n_out else None)}
    record(row)
    return row


def percentile(values: list[float], p: float) -> float | None:
    """Phân vị p (0-100) theo nội suy tuyến tính; None nếu không có mẫu."""
    xs = sorted(v for v in values if v is not None)
    if not xs:
        return None
    k = (len(xs) - 1) * p / 100
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def peak_per_minute(times: list[float], weights: list[float] | None = None) -> float | None:
    """Giá trị lớn nhất của tổng (số lần hoặc trọng số) trong một cửa sổ trượt 60 giây; để so với giới hạn RPM/TPM."""
    if not times:
        return None
    pairs = sorted(zip(times, weights or [1.0] * len(times)))
    best, acc, lo = 0.0, 0.0, 0
    for hi, (t, w) in enumerate(pairs):
        acc += w
        while pairs[lo][0] <= t - 60:
            acc -= pairs[lo][1]
            lo += 1
        best = max(best, acc)
    return best


def summarize(path: Path) -> dict[str, Any]:
    """Tóm tắt file `llm_calls.jsonl`: p50/p90/p99 của E2E và TTFT/TPOT/tokens-s, throughput, TPM/RPM, lỗi, thử lại."""
    rows = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    calls = [r for r in rows if r["kind"] == "llm_call"]
    invokes = [r for r in rows if r["kind"] == "invoke"]
    streams = [r for r in rows if r["kind"] == "stream"]

    def pcts(rs: list[dict[str, Any]], key: str) -> dict[str, float | None]:
        vals = [r[key] for r in rs if r.get(key) is not None]
        return {"n": len(vals), "p50": percentile(vals, 50), "p90": percentile(vals, 90), "p99": percentile(vals, 99)}

    ts = [r["ts"] for r in rows]
    span = (max(ts) - min(ts)) if len(ts) > 1 else None
    tin = sum(r.get("input_tokens") or 0 for r in calls)
    tout = sum(r.get("output_tokens") or 0 for r in calls)
    minutes = span / 60 if span else None
    return {
        "llm_calls": len(calls), "failed_calls": sum(not r["ok"] for r in calls),
        "status_counts": dict(Counter(r.get("status") for r in calls if not r["ok"])),
        "e2e_call_s": pcts(calls, "e2e_s"), "e2e_invoke_s": pcts(invokes, "e2e_s"),
        "tokens_per_s": pcts(calls, "tokens_per_s"),
        "ttft_s": pcts(streams, "ttft_s"), "tpot_s": pcts(streams, "tpot_s"),
        "input_tokens": tin, "output_tokens": tout, "wall_s": span,
        "throughput_calls_per_s": (len(calls) / span if span else None),
        "throughput_out_tokens_per_s": (tout / span if span else None),
        "RPM_avg": (len(calls) / minutes if minutes else None), "TPM_avg": ((tin + tout) / minutes if minutes else None),
        "RPM_peak": peak_per_minute([r["ts"] for r in calls]),
        "TPM_peak": peak_per_minute([r["ts"] for r in calls],
                                    [(r.get("input_tokens") or 0) + (r.get("output_tokens") or 0) for r in calls]),
        "retries": sum(max(0, (r.get("attempts") or 1) - 1) for r in invokes),
        "cache_hits": sum(bool(r.get("cache_hit")) for r in invokes),
    }
