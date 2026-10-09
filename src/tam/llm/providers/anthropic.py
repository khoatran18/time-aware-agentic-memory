"""Anthropic (Claude) qua langchain-anthropic."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id, require
from tam.llm.registry import register_llm


@register_llm("anthropic")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatAnthropic từ một profile trong `llm.profiles`."""
    from langchain_anthropic import ChatAnthropic  # import trễ: nặng

    return ChatAnthropic(
        model=model_id(profile),
        api_key=require(profile, "api_key", "đặt ANTHROPIC_API_KEY trong .env"),
        temperature=profile.get("temperature", 0),
    )
