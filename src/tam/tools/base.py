"""Hợp đồng chung của công cụ agent: `AgentTool` (tên, mô tả, schema tham số, hàm chạy), `ToolResult`, `ToolError`. Không phụ thuộc langchain."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError


class ToolError(ValueError):
    """Lỗi do tham số của agent (trang không có, regex sai, ngày sai). Thông báo được trả lại cho agent đọc, không phải lỗi chương trình."""


@dataclass(frozen=True)
class ToolResult:
    """`text`: nội dung đưa cho agent; `chunk_ids`: các chunk đã lộ ra trong `text` (cho vết); `truncated`: kết quả bị cắt theo trần."""

    text: str
    chunk_ids: tuple[str, ...] = ()
    truncated: bool = False


@dataclass(frozen=True)
class AgentTool:
    """Một công cụ: `args_model` (pydantic) sinh JSON schema cho LLM và kiểm tham số; `fn` nhận các tham số đã kiểm."""

    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable[..., ToolResult]

    def schema(self) -> dict[str, Any]:
        """Định dạng function của OpenAI; `bind_tools` của langchain nhận dạng này cho mọi nhà cung cấp."""
        return {"type": "function", "function": {"name": self.name, "description": self.description,
                                                  "parameters": self.args_model.model_json_schema()}}

    def call(self, args: dict[str, Any]) -> ToolResult:
        """Kiểm tham số rồi chạy; tham số sai thì ném `ToolError` với thông báo đọc được."""
        try:
            parsed = self.args_model.model_validate(args)
        except ValidationError as exc:
            detail = "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors())
            raise ToolError(f"tham số không hợp lệ cho {self.name}: {detail}") from exc
        return self.fn(**parsed.model_dump())
