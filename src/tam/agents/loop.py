"""Vòng lặp agent tối giản: gọi mô hình, chạy các công cụ nó yêu cầu, đưa kết quả lại, lặp đến khi nó trả lời hoặc hết ngân sách.

Cố ý không dùng LangGraph (docs/planning/00_OVERALL_PLAN.md mục 4.1): vòng lặp là một `for`, trần bước và trần token nằm ngay trong mã.
A và B dùng **cùng** vòng lặp, cùng system prompt; chỉ khác danh sách công cụ. Không có mốc thời gian hay thiết kế nào được nhúng vào prompt
(`agent_v1.md` trung tính).

Ghi log (mặc định vào `get_run_dir()` nếu đã `setup_logging()`, hoặc đường dẫn truyền vào; không có thì tắt file, vẫn ghi `logger`):
- `agent_trace.jsonl`: nhẹ, mỗi lượt một dòng `llm` (token vào/ra/cache, TTFT, TPOT, tokens/s, E2E, số lời gọi công cụ), `tool` (tên, tham số,
  chunk đã lộ ra, lỗi, số ký tự, thời gian) và `end` (lý do dừng, tổng token, thời gian LLM và công cụ, đáp án).
- `agent_calls.jsonl`: mỗi lần gọi LLM một dòng gồm **prompt** (toàn bộ tin nhắn đã gửi), **câu trả lời** (chữ, lời gọi công cụ, chuỗi suy luận nếu có)
  và các số đo trên. `log_prompts="delta"` chỉ ghi tin nhắn mới thêm từ lần gọi trước (prompt đầy đủ dựng lại được; đỡ phình vì mỗi lượt lặp lại
  toàn bộ lịch sử); `"off"` tắt file này.
`query_context` gắn `query_id` để nối với `llm_calls.jsonl` của `tam.llm.metrics` (callback ghi E2E, token, lỗi mỗi lần gọi thật).

Ngân sách lượt (`budget_notice=True`): sau mỗi lượt công cụ, kết quả cuối kèm dòng báo số lượt gọi LLM còn lại; ở lượt cuối **không gắn công cụ**
và dòng báo bảo trả lời ngay từ những đoạn đã đọc (không đủ căn cứ thì nói không xác định được), nên chạm trần không còn cho `answer=None` vì hết lượt.
Mặc định tắt (hành vi cũ, `agent_v1.md` làm đối chứng).

Cache từng lần gọi LLM (`cache=` một `CacheStore`): khóa = (model, `cache_salt`, có gắn công cụ hay không, toàn bộ tin nhắn, schema công cụ); chỉ lần gọi
thành công và không rỗng mới được ghi. Trúng cache thì không gọi API, số đo (token, TTFT, E2E) lấy **nguyên từ lần gọi thật** để chạy lại cho ra đúng bảng cũ,
và được đánh dấu `cache_hit=true` trong `agent_trace.jsonl`/`agent_calls.jsonl` để loại khỏi thống kê độ trễ. `llm_calls.jsonl` chỉ có lần gọi thật.
`cache_salt` (vd số lần chạy lặp) tách các lần chạy muốn lấy mẫu độc lập: cùng salt thì tái dùng, khác salt thì gọi mới.

Đo bằng streaming (`stream=True`, mặc định) để có TTFT và TPOT; `stream=False` gọi thường (TTFT và TPOT rỗng).
"""
from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    messages_from_dict,
    messages_to_dict,
)

from tam.config.logging import get_logger, get_run_dir, query_context
from tam.generation.scoring import normalize
from tam.llm.cache import PREVIEW_CHARS, CacheStore
from tam.llm.metrics import stream_collect
from tam.tools.base import AgentTool, ToolError

logger = get_logger(__name__)
PROMPT_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
StopReason = Literal["answer", "max_steps", "max_tokens", "llm_error"]
PromptLog = Literal["full", "delta", "off"]
_LOCK = threading.Lock()


BUDGET_LEFT = "[{left} of {total} model calls left. Stop searching as soon as you can answer.]"
BUDGET_LAST = ("[This is your last call and tools are no longer available. Answer now from the passages you have read, citing their ids and a short quote. "
               "If they do not support an answer, say it cannot be determined and state what you found; do not guess.]")


def load_system_prompt(t_now: str, version: str = "v1") -> str:
    """Prompt của agent (`agent_<version>.md`; v1 trung tính, v2 có hướng dẫn suy luận thời gian) với `{t_now}` thay bằng ngày hiện tại của máy chủ (`str.replace`, vì prompt có thể chứa `{}`)."""
    return (PROMPT_DIR / f"agent_{version}.md").read_text(encoding="utf-8").replace("{t_now}", t_now)


def merge_chunks(chunks: list[Any]) -> AIMessage:
    """Ghép các chunk streaming thành một `AIMessage` (chữ, lời gọi công cụ, token); một tin nhắn nguyên vẹn thì trả lại chính nó."""
    if not chunks:
        raise ValueError("LLM không trả chunk nào")
    if all(isinstance(c, AIMessageChunk) for c in chunks):
        acc = chunks[0]
        for c in chunks[1:]:
            acc = acc + c
        return AIMessage(content=acc.content, tool_calls=acc.tool_calls, additional_kwargs=acc.additional_kwargs,
                         response_metadata=acc.response_metadata, usage_metadata=acc.usage_metadata, id=acc.id)
    last = chunks[-1]
    return last if isinstance(last, AIMessage) else AIMessage(content=str(getattr(last, "content", last)))


def dump_message(m: BaseMessage) -> dict[str, Any]:
    """Tin nhắn thành dict JSON được (vai trò, nội dung, lời gọi công cụ, id lời gọi)."""
    d: dict[str, Any] = {"role": m.type, "content": m.content}
    if getattr(m, "tool_calls", None):
        d["tool_calls"] = [{"id": c.get("id"), "name": c["name"], "args": c.get("args")} for c in m.tool_calls]
    if isinstance(m, ToolMessage):
        d["tool_call_id"] = m.tool_call_id
    return d


@dataclass
class AgentRun:
    """Kết quả một câu hỏi. `answer` rỗng khi hết ngân sách hoặc lỗi LLM (xem `stop_reason`)."""

    question: str
    answer: str | None
    stop_reason: StopReason
    steps: int = 0
    cache_hits: int = 0  # số lượt LLM trả từ cache (không gọi API)
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    llm_time_s: float = 0.0  # tổng thời gian các lượt gọi LLM (E2E, đo ở client)
    tool_time_s: float = 0.0  # tổng thời gian chạy công cụ
    wall_s: float = 0.0
    ttft_s: list[float] = field(default_factory=list)  # TTFT từng lượt (chỉ lượt có số đo)
    chunk_ids: list[str] = field(default_factory=list)  # mọi chunk đã lộ ra cho agent, theo thứ tự, có lặp
    tool_texts: list[tuple[int, str]] = field(default_factory=list)  # (lượt LLM, văn bản công cụ đã đưa cho agent), để kiểm đáp án có thật sự tới tay agent
    trace: list[dict[str, Any]] = field(default_factory=list)

    def first_step_showing(self, targets: list[str]) -> int | None:
        """Lượt LLM đầu tiên mà văn bản công cụ trả về chứa trọn một đáp án (theo từ, sau chuẩn hóa); None nếu chưa lần nào.
        Chính xác hơn `chunk_ids`: `grep` chỉ trả đoạn trích quanh chỗ khớp nên liệt kê chunk chưa có nghĩa là đáp án đã hiện ra."""
        golds = [g for g in map(normalize, targets) if g]
        for step, text in self.tool_texts:
            padded = f" {normalize(text)} "
            if any(f" {g} " in padded for g in golds):
                return step
        return None


def _run_path(name: str) -> Path | None:
    """`get_run_dir()/name` nếu đã `setup_logging()`, không thì None."""
    try:
        return get_run_dir() / name
    except RuntimeError:
        return None


def _append(path: Path | None, row: dict[str, Any]) -> None:
    """Thêm một dòng JSON vào `path` (có khóa, an toàn nhiều luồng). Không bao giờ ném lỗi: đo đạc không được làm hỏng lượt chạy."""
    if path is None:
        return
    try:
        line = json.dumps(row, ensure_ascii=False, default=str)
        with _LOCK:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
    except OSError as exc:
        logger.warning("Không ghi được %s: %s", path.name, exc)


class AgentLoop:
    """`llm`: `BaseChatModel` có `bind_tools`. `tools`: công cụ của A hoặc B. `max_steps`: số lượt gọi LLM tối đa; `max_total_tokens`: tổng token vào và ra.

    `model_name`: tên profile hoặc mô hình, chỉ để ghi log. `request_headers`: hàm `query_id -> header` gửi kèm mọi lần gọi LLM của câu hỏi đó (vd mã phiên `x-opencode-session` mà OpenCode Go đòi; mỗi câu một cuộc hội thoại). `trace_path`, `calls_path`: nơi ghi (mặc định `get_run_dir()`); `log_prompts`: xem docstring module.
    """

    def __init__(self, llm: Any, tools: list[AgentTool], system_prompt: str, *, max_steps: int = 10, max_total_tokens: int = 200_000,
                 stream: bool = True, model_name: str = "", trace_path: str | Path | None = None, calls_path: str | Path | None = None,
                 log_prompts: PromptLog = "full", request_headers: Callable[[str], dict[str, str]] | None = None, budget_notice: bool = False,
                 cache: CacheStore | None = None, cache_model: str = "", cache_salt: str = "") -> None:
        if max_steps < 1 or max_total_tokens < 1:
            raise ValueError("max_steps và max_total_tokens phải >= 1")
        if len({t.name for t in tools}) != len(tools):
            raise ValueError("tên công cụ bị trùng")
        if log_prompts not in ("full", "delta", "off"):
            raise ValueError(f"log_prompts phải là full, delta hoặc off; nhận {log_prompts!r}")
        self._tools = {t.name: t for t in tools}
        self._llm = llm.bind_tools([t.schema() for t in tools])
        self._cache, self._cache_model, self._cache_salt = cache, cache_model or model_name, cache_salt
        self._tools_key = json.dumps([t.schema() for t in tools], sort_keys=True, default=str)
        self._llm_plain, self._budget_notice = llm, budget_notice  # llm_plain: không công cụ, dùng ở lượt cuối khi có budget_notice
        self._system, self._max_steps, self._max_tokens = system_prompt, max_steps, max_total_tokens
        self._stream, self._model, self._log_prompts, self._headers = stream, model_name, log_prompts, request_headers
        self._trace_path = Path(trace_path) if trace_path else _run_path("agent_trace.jsonl")
        self._calls_path = None if log_prompts == "off" else (Path(calls_path) if calls_path else _run_path("agent_calls.jsonl"))

    def run(self, question: str, *, query_id: str = "-") -> AgentRun:
        """Chạy một câu hỏi. Lỗi do tham số của agent quay lại cho nó đọc; lỗi gọi LLM dừng lượt chạy (`llm_error`), không ném ra ngoài."""
        run = AgentRun(question=question, answer=None, stop_reason="max_steps")
        messages: list[BaseMessage] = [SystemMessage(self._system), HumanMessage(question)]
        logged = 0  # số tin nhắn đã ghi vào agent_calls (cho chế độ delta)
        t_start = time.perf_counter()
        extra = {"extra_headers": self._headers(query_id)} if self._headers else None
        llm_tools = self._llm.bind(**extra) if extra else self._llm
        llm_plain = self._llm_plain.bind(**extra) if extra else self._llm_plain
        with query_context(query_id):
            while True:
                if run.steps >= self._max_steps:
                    run.stop_reason = "max_steps"
                    break
                run.steps += 1
                prompt, logged = self._prompt_view(messages, logged)
                last = self._budget_notice and run.steps == self._max_steps and len(messages) > 2
                try:
                    ai, m = self._call_cached(llm_plain if last else llm_tools, messages, last, run)
                except Exception as exc:  # noqa: BLE001  429, hết hạn mức, JSON hỏng... đều là một kết quả của lượt chạy, không làm sập cả loạt
                    err = f"{type(exc).__name__}: {exc}"[:300]
                    logger.warning("agent step=%d lỗi LLM: %s", run.steps, err)
                    self._emit(run, query_id, {"event": "llm", "step": run.steps, "ok": False, "error": err})
                    self._log_call(query_id, run.steps, prompt, None, None, err)
                    run.stop_reason = "llm_error"
                    break
                run.input_tokens += m.get("input_tokens") or 0
                run.output_tokens += m.get("output_tokens") or 0
                run.cached_input_tokens += m.get("cached_input_tokens") or 0
                run.llm_time_s += m["e2e_s"]
                if m.get("ttft_s") is not None:
                    run.ttft_s.append(m["ttft_s"])
                calls = list(ai.tool_calls or [])
                logger.info("agent step=%d llm in=%s out=%s cached=%s ttft=%s e2e=%.2fs tool_calls=%d", run.steps, m.get("input_tokens"),
                            m.get("output_tokens"), m.get("cached_input_tokens"), _fmt(m.get("ttft_s")), m["e2e_s"], len(calls))
                self._emit(run, query_id, {"event": "llm", "step": run.steps, "ok": True, **_rounded(m), "n_tool_calls": len(calls)})
                self._log_call(query_id, run.steps, prompt, ai, m, None)
                if not calls:
                    run.answer, run.stop_reason = ai.text, "answer"
                    if last and not ai.text.strip():
                        run.answer, run.stop_reason = None, "max_steps"
                    break
                if run.input_tokens + run.output_tokens >= self._max_tokens:
                    run.stop_reason = "max_tokens"
                    break
                messages.append(ai)
                for call in calls:
                    messages.append(ToolMessage(content=self._run_tool(run, query_id, call), tool_call_id=call["id"]))
                if self._budget_notice and run.steps < self._max_steps:
                    left = self._max_steps - run.steps
                    note = BUDGET_LAST if left == 1 else BUDGET_LEFT.format(left=left, total=self._max_steps)
                    messages[-1] = ToolMessage(content=f"{messages[-1].content}\n\n{note}", tool_call_id=messages[-1].tool_call_id)
            run.wall_s = time.perf_counter() - t_start
            logger.info("agent xong stop=%s steps=%d tools=%d tokens=%d/%d wall=%.2fs", run.stop_reason, run.steps, run.tool_calls,
                        run.input_tokens, run.output_tokens, run.wall_s)
            self._emit(run, query_id, {"event": "end", "stop_reason": run.stop_reason, "steps": run.steps, "tool_calls": run.tool_calls,
                                       "input_tokens": run.input_tokens, "output_tokens": run.output_tokens,
                                       "cached_input_tokens": run.cached_input_tokens, "cache_hits": run.cache_hits, "llm_time_s": round(run.llm_time_s, 4),
                                       "tool_time_s": round(run.tool_time_s, 4), "wall_s": round(run.wall_s, 4), "answer": run.answer})
        return run

    def _call_cached(self, llm: Any, messages: list[BaseMessage], plain: bool, run: AgentRun) -> tuple[AIMessage, dict[str, Any]]:
        """`_call_llm` có cache. Trúng: dựng lại `AIMessage` và số đo từ lần gọi thật (thêm `cache_hit=True`). Trượt: gọi thật rồi ghi."""
        if self._cache is None:
            ai, m = self._call_llm(llm, messages)
            return ai, {**m, "cache_hit": False}
        key = CacheStore.key("AgentStep", self._cache_model, self._cache_salt, "plain" if plain else self._tools_key,
                             json.dumps([dump_message(x) for x in messages], ensure_ascii=False, sort_keys=True, default=str))
        hit = self._cache.get(key)
        if hit is not None:
            try:
                run.cache_hits += 1
                return messages_from_dict([hit["message"]])[0], {**hit["metrics"], "cache_hit": True}
            except (KeyError, ValueError, TypeError):
                run.cache_hits -= 1
                logger.warning("Mục cache agent hỏng, gọi lại LLM: %s", key[:12])
        ai, m = self._call_llm(llm, messages)
        if ai.text.strip() or ai.tool_calls:
            try:
                self._cache.put(key, {"message": messages_to_dict([ai])[0], "metrics": json.loads(json.dumps(m, default=str))},
                                meta={"schema": "AgentStep", "model": self._cache_model, "preview": str(messages[-1].content)[:PREVIEW_CHARS].replace("\n", " ")})
            except (TypeError, ValueError, OSError) as exc:
                logger.warning("Không ghi được cache agent: %s", exc)
        return ai, {**m, "cache_hit": False}

    def _call_llm(self, llm: Any, messages: list[BaseMessage]) -> tuple[AIMessage, dict[str, Any]]:
        """Một lần gọi LLM: (tin nhắn trả lời, số đo). Streaming cho TTFT và TPOT; không thì chỉ E2E và token."""
        if self._stream:
            chunks, m = stream_collect(llm, messages)
            return merge_chunks(chunks), m
        t0 = time.perf_counter()
        ai = llm.invoke(messages)
        usage = getattr(ai, "usage_metadata", None) or {}
        return ai, {"ttft_s": None, "e2e_s": time.perf_counter() - t0, "output_tokens": usage.get("output_tokens"), "input_tokens": usage.get("input_tokens"),
                    "cached_input_tokens": (usage.get("input_token_details") or {}).get("cache_read"), "tokens_exact": bool(usage.get("output_tokens")),
                    "tpot_s": None, "tokens_per_s": None}

    def _prompt_view(self, messages: list[BaseMessage], logged: int) -> tuple[list[dict[str, Any]], int]:
        """Phần prompt cần ghi lần này: toàn bộ (`full`) hoặc chỉ tin nhắn mới từ lần gọi trước (`delta`); và số tin nhắn đã ghi."""
        start = logged if self._log_prompts == "delta" else 0
        return [dump_message(m) for m in messages[start:]], len(messages)

    def _log_call(self, query_id: str, step: int, prompt: list[dict[str, Any]], ai: AIMessage | None, metrics: dict[str, Any] | None,
                  error: str | None) -> None:
        """Một dòng `agent_calls.jsonl`: prompt, câu trả lời, số đo (hoặc lỗi)."""
        if self._calls_path is None:
            return
        out = None if ai is None else {"text": ai.text, "tool_calls": [{"id": c.get("id"), "name": c["name"], "args": c.get("args")} for c in ai.tool_calls or []],
                                       "reasoning": (ai.additional_kwargs or {}).get("reasoning_content")}
        _append(self._calls_path, {"ts": time.time(), "query_id": query_id, "step": step, "model": self._model, "prompt_mode": self._log_prompts,
                                   "prompt": prompt, "output": out, "metrics": None if metrics is None else _rounded(metrics), "ok": error is None, "error": error})

    def _run_tool(self, run: AgentRun, query_id: str, call: dict[str, Any]) -> str:
        """Chạy một lời gọi công cụ; mọi lỗi tham số trả về dạng văn bản cho agent. Ghi vết."""
        name, args = call["name"], call.get("args") or {}
        run.tool_calls += 1
        t0 = time.perf_counter()
        event: dict[str, Any] = {"event": "tool", "step": run.steps, "tool": name, "args": args, "ok": True, "chunk_ids": [], "truncated": False}
        try:
            tool = self._tools.get(name)
            if tool is None:
                raise ToolError(f"không có công cụ {name!r}; công cụ có: {', '.join(self._tools)}")
            res = tool.call(args)
            text = res.text
            event.update(chunk_ids=list(res.chunk_ids), truncated=res.truncated)
            run.chunk_ids.extend(res.chunk_ids)
            run.tool_texts.append((run.steps, text))
        except ToolError as exc:
            text = f"Error: {exc}"
            event.update(ok=False, error=str(exc))
        dt = time.perf_counter() - t0
        run.tool_time_s += dt
        event.update(n_chars=len(text), e2e_s=round(dt, 4))
        logger.info("agent step=%d tool=%s ok=%s chars=%d %.3fs", run.steps, name, event["ok"], len(text), dt)
        self._emit(run, query_id, event)
        return text

    def _emit(self, run: AgentRun, query_id: str, event: dict[str, Any]) -> None:
        """Thêm vào `run.trace` và ghi một dòng JSONL nếu có nơi ghi."""
        row = {"query_id": query_id, **event}
        run.trace.append(row)
        _append(self._trace_path, {"ts": time.time(), **row})


def _rounded(m: dict[str, Any]) -> dict[str, Any]:
    """Số đo với các số thực làm tròn cho gọn file."""
    return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in m.items()}


def _fmt(v: float | None) -> str:
    return "-" if v is None else f"{v:.2f}s"
