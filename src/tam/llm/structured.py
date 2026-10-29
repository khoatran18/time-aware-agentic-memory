"""Gọi LLM lấy đầu ra có cấu trúc, chịu được proxy/model bỏ qua structured output (vd combo 9router `basic-llm`).

Thứ tự: structured output của langchain (bỏ qua nếu profile đặt `structured_output: false`, đi thẳng bước sau)
-> nếu lỗi định dạng thì gọi thường, kèm schema JSON, rồi đọc JSON từ văn bản
(bỏ hàng rào markdown, hạ chữ thường tên khóa) -> thử lại tối đa `max_attempts` lần. Chỉ bắt lỗi định dạng (ValueError,
gồm JSONDecodeError và ValidationError); lỗi xác thực ném ra ngay; lỗi tạm thời (mạng, 429, 5xx, 410) chờ 1 đến 32 giây rồi ném `LlmUnavailable`.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

from tam.config.logging import get_logger
from tam.llm.cache import PREVIEW_CHARS, CacheStore

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


BACKOFF_SECONDS = (1, 2, 4, 8, 16, 32)
_RETRYABLE_STATUS = frozenset({408, 409, 410, 425, 429})


class LlmUnavailable(RuntimeError):
    """LLM không phản hồi sau mọi lần chờ. Chạy lại sau; các lô đã xong nằm trong cache nên không gọi lại."""


def _is_transient(exc: Exception) -> bool:
    """Lỗi tạm thời đáng chờ: mạng, quá tải, 5xx, 429, model bị ngừng (410) ở combo. Không gồm 401/403/400."""
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status in _RETRYABLE_STATUS or status >= 500
    name = type(exc).__name__
    bases = {c.__name__ for c in type(exc).__mro__}  # lỗi của langchain-google-genai không có status_code: nhận qua tên lớp cha
    return (isinstance(exc, (ConnectionError, TimeoutError)) or "Connection" in name or "Timeout" in name
            or bool(bases & {"ModelRateLimitError", "ServerError", "TransportError"}))  # TransportError: gốc của lỗi mạng httpx (đứt kết nối, broken pipe)


class _SkipStructured(Exception):
    """Nội bộ: báo bỏ bước structured output (profile `structured_output: false`)."""


def _call_with_backoff(fn: Callable[[], Any], sleep: Callable[[float], None]) -> Any:
    """Gọi `fn`; lỗi tạm thời thì chờ 1, 2, 4, 8, 16, 32 giây rồi thử lại; hết lần thì ném `LlmUnavailable`."""
    for wait in (*BACKOFF_SECONDS, None):
        try:
            return fn()
        except ValueError:
            raise
        except Exception as exc:
            if not _is_transient(exc):
                raise
            if wait is None:
                raise LlmUnavailable(f"LLM lỗi sau {len(BACKOFF_SECONDS)} lần chờ: {exc}") from exc
            logger.warning("LLM lỗi tạm thời (%s), chờ %ds rồi thử lại", type(exc).__name__, wait)
            sleep(wait)


def _lower_keys(node: Any) -> Any:
    """Hạ chữ thường tên khóa ở mọi cấp (LLM yếu đôi khi viết "Index")."""
    if isinstance(node, dict):
        return {k.lower() if isinstance(k, str) else k: _lower_keys(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_lower_keys(v) for v in node]
    return node


def parse_json_text(reply: object, schema: type[T]) -> T:
    """Đọc `schema` từ văn bản thường: bỏ hàng rào markdown, lấy từ `{` đầu đến `}` cuối."""
    content = getattr(reply, "content", reply)
    if isinstance(content, list):  # nội dung dạng khối
        content = "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in content)
    text = str(content)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError(f"LLM không trả JSON: {text[:200]!r}")
    return schema.model_validate(_lower_keys(json.loads(text[start:end + 1])))


def _model_id(llm: Any) -> str:
    """Định danh model để làm khóa cache: `cache_model` của profile nếu có, không thì tên model trong config, không thì tên lớp."""
    alias = (getattr(llm, "metadata", None) or {}).get("cache_model")
    if alias:
        return str(alias)
    return str(getattr(llm, "model_name", None) or getattr(llm, "model", None) or type(llm).__name__)


def _uses_structured_output(llm: Any) -> bool:
    """False khi profile đặt `structured_output: false` (factory ghi vào `metadata`): bỏ bước structured output, đi thẳng đường văn bản."""
    return (getattr(llm, "metadata", None) or {}).get("structured_output", True) is not False


def _preview(messages: list[tuple[str, str]]) -> str:
    """Đầu nội dung người dùng gửi (không gồm prompt hệ thống), để nhận ra mục cache khi đọc file."""
    human = next((text for role, text in reversed(messages) if role == "human"), "")
    return human[:PREVIEW_CHARS].replace("\n", " ")


def invoke_structured(
    llm: BaseChatModel, chain: Any, schema: type[T], messages: list[tuple[str, str]], *, max_attempts: int = 3,
    cache: CacheStore | None = None, sleep: Callable[[float], None] = time.sleep,
    key_messages: list[tuple[str, str]] | None = None, cacheable: Callable[[T], bool] | None = None,
) -> T | None:
    """Trả `schema` hoặc None nếu mọi lần thử đều lỗi định dạng. `chain` = `llm.with_structured_output(schema)`.

    Có `cache` thì tra trước và chỉ gọi LLM khi chưa có; chỉ kết quả hợp lệ mới được ghi.
    `key_messages`: nội dung dùng để tính khóa thay cho `messages` (vd bỏ phần phụ thuộc ngày hiện tại).
    `cacheable`: nhận kết quả, trả False thì không ghi vào cache.
    """
    key = None
    if cache is not None:
        key = cache.key(schema.__name__, _model_id(llm), json.dumps(key_messages or messages, ensure_ascii=False))
        cached = cache.get(key)
        if cached is not None:
            return schema.model_validate(cached)
    schema_note = (
        "Reply with ONLY a JSON object (no markdown, no commentary) matching this JSON schema:\n"
        + json.dumps(schema.model_json_schema())
    )
    fallback_messages = [*messages, ("human", schema_note)]
    use_structured = _uses_structured_output(llm)
    for attempt in range(1, max_attempts + 1):
        try:
            try:
                if not use_structured:
                    raise _SkipStructured
                out = _call_with_backoff(lambda: chain.invoke(messages), sleep)
            except (ValueError, _SkipStructured) as exc:  # proxy bỏ qua structured output, trả văn bản/JSON trong khối markdown
                if use_structured:
                    logger.warning("Structured output lỗi (%s), thử đọc JSON từ văn bản", type(exc).__name__)
                out = parse_json_text(_call_with_backoff(lambda: llm.invoke(fallback_messages), sleep), schema)
            result = schema.model_validate(out) if isinstance(out, dict) else out
            if cache is not None and key is not None and (cacheable is None or cacheable(result)):
                cache.put(key, result.model_dump(mode="json"), meta={
                    "schema": schema.__name__, "model": _model_id(llm), "preview": _preview(messages)})
            return result
        except ValueError as exc:
            logger.warning("LLM trả JSON không hợp lệ (lần %d/%d): %s", attempt, max_attempts, str(exc)[:200])
    logger.error("Bỏ sau %d lần thử: LLM không trả JSON hợp lệ", max_attempts)
    return None
