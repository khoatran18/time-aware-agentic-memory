"""Google Gemini gọi thẳng API (không qua proxy) qua langchain-google-genai; structured output do phía Google ép khuôn."""
from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from tam.llm.providers._common import model_id, require
from tam.llm.registry import register_llm


@register_llm("google")
def build(profile: dict[str, Any]) -> BaseChatModel:
    """Tạo ChatGoogleGenerativeAI từ một profile.

    `profile` là MỘT KHỐI dưới `llm.profiles` trong configs/config.*.yaml, đã đổi sang dict, ví dụ:

        llm:
          profiles:
            gemini_flash_lite:                  # <- tên profile
              provider: "google"
              model_id: "gemini-3.5-flash-lite"
              api_key: "${GOOGLE_API_KEY:-}"    # key Google AI Studio
              temperature: 0
              cache_model: "basic-gemini-3.5-flash-lite"   # tùy chọn: dùng lại cache của profile khác, xem factory.get_llm

    Các khóa dùng ở đây: `model_id`, `api_key`, `temperature`. Tên profile không nằm trong dict; factory dùng nó để chọn khối.
    """
    from langchain_google_genai import ChatGoogleGenerativeAI  # import trễ: nặng

    return ChatGoogleGenerativeAI(
        model=model_id(profile),
        google_api_key=require(profile, "api_key", "đặt GOOGLE_API_KEY trong .env"),
        temperature=profile.get("temperature", 0),
    )
