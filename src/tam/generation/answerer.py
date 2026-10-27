"""Sinh đáp án ngắn cho một lô câu hỏi (mỗi câu kèm các chunk đã truy xuất) bằng một request LLM.

Một request chứa `batch` câu độc lập; LLM trả `AnswerBatch` (mỗi câu một mục `n` = số thứ tự câu). Phiên bản prompt ở
`tam/llm/prompts/answer_<v>.md`: v1 chỉ đưa văn bản chunk; v2 thêm khoảng hiệu lực của chunk trước mỗi đoạn; v3, v4 = v1, v2 nới điều kiện từ chối (v1/v2 từ chối cả khi đáp án nằm trong ngữ cảnh). Xem decisions/03.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from tam.llm.cache import CacheStore
from tam.llm.structured import invoke_structured
from tam.schemas.chunk import Chunk

PROMPT_DIR = Path(__file__).resolve().parents[1] / "llm" / "prompts"
PROMPT_VERSIONS = ("v1", "v2", "v3", "v4")
REFUSALS = {"", "null", "none", "n/a", "unanswerable", "unknown", "not specified", "not mentioned"}


class AnswerItem(BaseModel):
    n: int = Field(description="Số thứ tự của câu hỏi trong tin nhắn (bắt đầu từ 1)")
    answer: str | None = Field(default=None, description="Cụm từ ngắn nhất trả lời câu hỏi; null nếu các đoạn không có đáp án")
    evidence: list[int] = Field(default_factory=list, description="Số thứ tự các đoạn đã dùng")


class AnswerBatch(BaseModel):
    answers: list[AnswerItem]


def is_refusal(answer: str | None) -> bool:
    return answer is None or answer.strip().lower().strip(".") in REFUSALS


def period_label(chunk: Chunk) -> str:
    """Khoảng hiệu lực của chunk, vd `2008 – 2009`, `2012 – present`, `no date`."""
    def fmt(d) -> str:
        return str(d.year) if (d.month, d.day) == (1, 1) else d.strftime("%Y-%m")
    if chunk.start_time is None:
        return "no date"
    return f"{fmt(chunk.start_time)} – {fmt(chunk.end_time) if chunk.end_time else 'present'}"


def build_user_message(questions: list[str], contexts: list[list[Chunk]], version: str) -> str:
    parts = []
    for i, (q, chunks) in enumerate(zip(questions, contexts), 1):
        lines = [f"[{j}] " + (f"({period_label(c)}) " if version in ("v2", "v4") else "") + c.text.strip().replace("\n", " ")
                 for j, c in enumerate(chunks, 1)]
        parts.append(f"### Question {i}\n{q}\n\nPassages:\n" + "\n".join(lines))
    return "\n\n".join(parts)


def valid_batch(batch: AnswerBatch, size: int) -> bool:
    """Đúng `size` mục, mỗi số thứ tự 1..size xuất hiện đúng một lần; `evidence` chỉ chứa số nguyên dương."""
    return sorted(a.n for a in batch.answers) == list(range(1, size + 1)) and all(e > 0 for a in batch.answers for e in a.evidence)


class Answerer:
    def __init__(self, llm: Any, *, version: str = "v1", cache: CacheStore | None = None, max_attempts: int = 2) -> None:
        if version not in PROMPT_VERSIONS:
            raise ValueError(f"version phải thuộc {PROMPT_VERSIONS}, nhận {version!r}")
        self.version, self._llm, self._cache, self._attempts = version, llm, cache, max_attempts
        self._chain = llm.with_structured_output(AnswerBatch)
        self._system = (PROMPT_DIR / f"answer_{version}.md").read_text(encoding="utf-8")

    def answer(self, questions: list[str], contexts: list[list[Chunk]]) -> AnswerBatch | None:
        """AnswerBatch hợp lệ (đủ mọi câu) hoặc None khi LLM trả sai định dạng; lỗi mạng/quota ném `LlmUnavailable`."""
        size = len(questions)
        messages = [("system", self._system), ("human", build_user_message(questions, contexts, self.version))]
        out = invoke_structured(self._llm, self._chain, AnswerBatch, messages, max_attempts=self._attempts, cache=self._cache,
                                cacheable=lambda r: valid_batch(r, size))
        return out if out is not None and valid_batch(out, size) else None
