"""Anthropic (Claude) qua langchain-anthropic."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id, require
from tam.llm.registry import register_llm


@register_llm("anthropic")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatAnthropic từ một profile.

    `profile` là MỘT KHỐI dưới `llm.profiles` trong configs/config.*.yaml, đã đổi sang dict, ví dụ:

        llm:
          profiles:
            claude_haiku:                       # <- tên profile
              provider: "anthropic"
              model_id: "claude-haiku-5-5"
              api_key: "${ANTHROPIC_API_KEY:-}"
              temperature: 0

    Các khóa dùng ở đây: `model_id`, `api_key`, `temperature`. Tên profile không nằm trong dict; factory dùng nó để chọn khối.
    """
    from langchain_anthropic import ChatAnthropic  # import trễ: nặng

    return ChatAnthropic(
        model=model_id(profile),
        api_key=require(profile, "api_key", "đặt ANTHROPIC_API_KEY trong .env"),
        temperature=profile.get("temperature", 0),
    )
