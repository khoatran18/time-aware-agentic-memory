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

    Các khóa dùng ở đây: `model_id`, `api_key`, `temperature`, `base_url` (tùy chọn; đặt để dùng proxy tương thích OpenAI như 9router). Tên profile không nằm trong dict; factory dùng nó để chọn khối.
    """
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model_id(profile),
        api_key=require(profile, "api_key", "điền biến key của profile trong .env, vd OPENAI_API_KEY hoặc NINE_ROUTER_API_KEY"),
        temperature=profile.get("temperature", 0),
        base_url=profile.get("base_url"),
    )
