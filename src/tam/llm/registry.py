"""Sổ đăng ký provider LLM: tên trong yaml (`provider: "anthropic"`) -> hàm build tạo chat model.

Dùng:

    @register_llm("anthropic")
    def build(profile: dict) -> BaseChatModel: ...

Cơ chế giống embedding/registry.py. Khác ở chỗ: thứ đăng ký ở đây là một HÀM (không phải class), vì không cần lớp
riêng: kết quả của hàm đã là chat model của langchain-core (BaseChatModel), nên `with_structured_output`, `bind_tools`
dùng được bất kể provider.

"Đăng ký" = ghi hàm vào dict, lúc file provider được import. Chưa gọi hàm, chưa tạo chat model nào. Hàm chỉ chạy khi
factory gọi `get_llm(...)`. Vì vậy providers/__init__.py phải import từng file provider.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

# tên provider (khớp `provider:` trong yaml) -> hàm build(profile) tạo chat model
LLM_PROVIDERS: dict[str, Callable[[dict[str, Any]], BaseChatModel]] = {}


def register_llm(name: str):
    """Trả về decorator đăng ký hàm build dưới tên `name`.

    Python gọi `register_llm("anthropic")` -> ra `deco`; rồi gọi `deco(build)` với `build` là hàm nằm dưới dòng `@`.
    """

    def deco(build):
        if name in LLM_PROVIDERS:
            raise ValueError(f"Provider LLM {name!r} đã được đăng ký")
        LLM_PROVIDERS[name] = build  # chỉ ghi hàm vào dict, chưa gọi
        return build  # trả lại đúng hàm để tên `build` giữ nguyên nghĩa

    return deco
