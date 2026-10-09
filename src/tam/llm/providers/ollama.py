"""Ollama (model chạy local, không cần API key) qua langchain-ollama."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id
from tam.llm.registry import register_llm


@register_llm("ollama")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatOllama từ một profile.

    `profile` là MỘT KHỐI dưới `llm.profiles` trong configs/config.*.yaml, đã đổi sang dict, ví dụ:

        llm:
          profiles:
            local_llama:                        # <- tên profile
              provider: "ollama"
              model_id: "..."
              base_url: "${OLLAMA_URL:-http://localhost:11434}"

    Các khóa dùng ở đây: `model_id`, `base_url` (tùy chọn), `temperature`; không cần `api_key`. Tên profile không nằm trong dict; factory dùng nó để chọn khối.
    """
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model_id(profile),
        base_url=profile.get("base_url") or "http://localhost:11434",
        temperature=profile.get("temperature", 0),
    )
