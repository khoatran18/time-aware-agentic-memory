"""Ollama (model chạy local, không cần API key) qua langchain-ollama."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id
from tam.llm.registry import register_llm


@register_llm("ollama")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatOllama từ một profile trong `llm.profiles`."""
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model_id(profile),
        base_url=profile.get("base_url") or "http://localhost:11434",
        temperature=profile.get("temperature", 0),
    )
