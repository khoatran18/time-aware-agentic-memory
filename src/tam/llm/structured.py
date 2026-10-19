"""Gọi LLM lấy đầu ra có cấu trúc, chịu được proxy/model bỏ qua structured output (vd combo 9router `basic-llm`).

Thứ tự: structured output của langchain -> nếu lỗi định dạng thì gọi thường, kèm schema JSON, rồi đọc JSON từ văn bản
(bỏ hàng rào markdown, hạ chữ thường tên khóa) -> thử lại tối đa `max_attempts` lần. Chỉ bắt lỗi định dạng (ValueError,
gồm JSONDecodeError và ValidationError); lỗi mạng hay xác thực vẫn ném ra.
"""
from __future__ import annotations

import json
from typing import Any, TypeVar

from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel

from tam.config.logging import get_logger
from tam.llm.cache import JsonCache

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


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
    """Định danh model để làm khóa cache: tên model trong config nếu có, không thì tên lớp."""
    return str(getattr(llm, "model_name", None) or getattr(llm, "model", None) or type(llm).__name__)


def invoke_structured(
    llm: BaseChatModel, chain: Any, schema: type[T], messages: list[tuple[str, str]], *, max_attempts: int = 3,
    cache: JsonCache | None = None,
) -> T | None:
    """Trả `schema` hoặc None nếu mọi lần thử đều lỗi định dạng. `chain` = `llm.with_structured_output(schema)`.

    Có `cache` thì tra trước và chỉ gọi LLM khi chưa có; chỉ kết quả hợp lệ mới được ghi.
    """
    key = None
    if cache is not None:
        key = cache.key(schema.__name__, _model_id(llm), json.dumps(messages, ensure_ascii=False))
        cached = cache.get(key)
        if cached is not None:
            return schema.model_validate(cached)
    schema_note = (
        "Reply with ONLY a JSON object (no markdown, no commentary) matching this JSON schema:\n"
        + json.dumps(schema.model_json_schema())
    )
    fallback_messages = [*messages, ("human", schema_note)]
    for attempt in range(1, max_attempts + 1):
        try:
            try:
                out = chain.invoke(messages)
            except ValueError as exc:  # proxy bỏ qua structured output, trả văn bản/JSON trong khối markdown
                logger.warning("Structured output lỗi (%s), thử đọc JSON từ văn bản", type(exc).__name__)
                out = parse_json_text(llm.invoke(fallback_messages), schema)
            result = schema.model_validate(out) if isinstance(out, dict) else out
            if cache is not None and key is not None:
                cache.put(key, result.model_dump(mode="json"))
            return result
        except ValueError as exc:
            logger.warning("LLM trả JSON không hợp lệ (lần %d/%d): %s", attempt, max_attempts, str(exc)[:200])
    logger.error("Bỏ sau %d lần thử: LLM không trả JSON hợp lệ", max_attempts)
    return None
