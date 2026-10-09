"""OpenAI (và API tương thích OpenAI, đặt `base_url`) qua langchain-openai."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id, require
from tam.llm.registry import register_llm


@register_llm("openai")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatOpenAI từ một profile trong `llm.profiles`."""
    from langchain_openai import ChatOpenAI

    return ChatOpenAI(
        model=model_id(profile),
        api_key=require(profile, "api_key", "đặt OPENAI_API_KEY trong .env"),
        temperature=profile.get("temperature", 0),
        base_url=profile.get("base_url"),
    )
