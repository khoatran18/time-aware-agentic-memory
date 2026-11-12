"""OpenAI (và API tương thích OpenAI, đặt `base_url`) qua langchain-openai."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id, require
from tam.llm.registry import register_llm


@register_llm("openai")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatOpenAI từ một profile.

    `profile` là MỘT KHỐI dưới `llm.profiles` trong configs/config.*.yaml, đã đổi sang dict, ví dụ:

        llm:
          profiles:
            9router:                            # <- tên profile
              provider: "openai"
              model_id: "..."
              api_key: "${NINE_ROUTER_API_KEY:-}"
              base_url: "${NINE_ROUTER_URL:-http://localhost:20128/v1}"
              temperature: 0

    Các khóa dùng ở đây: `model_id`, `api_key`, `temperature`, `base_url` (tùy chọn; đặt để dùng proxy tương thích OpenAI như 9router), `extra_body` (tùy chọn; dict gửi kèm mỗi yêu cầu), `default_headers` (tùy chọn; dict header gửi kèm mọi yêu cầu, vd `User-Agent` riêng khi nhà cung cấp đòi), `stream_usage` (tùy chọn, bool; true thì yêu cầu streaming trả kèm token vào/ra qua `stream_options.include_usage`. langchain-openai mặc định TẮT khi có `base_url` tùy chỉnh, nên không đặt thì streaming qua proxy không có `usage`; cần cho `tam/agents/loop.py` đo token và áp trần token). Tên profile không nằm trong dict; factory dùng nó để chọn khối.
    """
    from langchain_openai import ChatOpenAI

    extra = {"stream_usage": bool(profile["stream_usage"])} if profile.get("stream_usage") is not None else {}
    if profile.get("default_headers"):
        extra["default_headers"] = dict(profile["default_headers"])
    return ChatOpenAI(
        **extra,
        model=model_id(profile),
        api_key=require(profile, "api_key", "điền biến key của profile trong .env, vd OPENAI_API_KEY hoặc NINE_ROUTER_API_KEY"),
        temperature=profile.get("temperature", 0),
        base_url=profile.get("base_url"),
        extra_body=profile.get("extra_body"),   # tùy chọn: tham số riêng của API tương thích OpenAI, vd DeepSeek {"thinking": {"type": "disabled"}}
    )
