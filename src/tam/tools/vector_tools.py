"""Bộ công cụ kiểu B (kho đã xây) cho agent: `vector_search`, `temporal_search`, `read_chunk`. Không gọi LLM.

Mọi chức năng của pipeline (chọn nhánh dense/BM25/hybrid, `k`, bộ lọc thời gian, chấm điểm thời gian, mở rộng chunk liền kề) là tham số công cụ;
dùng hay không là do agent quyết. Bộ lọc mặc định TẮT. Mô tả công cụ là một phần cố định của harness, giữ trung tính (không dặn lọc theo ngày).
`show_time=False` ẩn khoảng hiệu lực của chunk khỏi kết quả (biến thể đối chứng: agent dựa vào metadata hay vào văn bản).
"""
from __future__ import annotations

import calendar
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from tam.generation.answerer import period_label
from tam.retrieval.temporal.expansion import neighbor_ids, split_chunk_id
from tam.retrieval.temporal.fusion import fuse
from tam.retrieval.temporal.retriever import TemporalRetriever
from tam.schemas.chunk import Chunk
from tam.schemas.query import ProfiledQuery
from tam.stores.vector.base import BranchHits, VectorFilter, VectorStore
from tam.tools.base import AgentTool, ToolError, ToolResult

DEFAULT_K_CAP = 50
MAX_NEIGHBORS = 5
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)


def parse_date(text: str) -> datetime:
    """`YYYY`, `YYYY-MM` hoặc `YYYY-MM-DD` -> datetime UTC; ngày thiếu nghĩa là **cuối** năm hoặc tháng đó (cận trên tính cả kỳ)."""
    parts = text.strip().split("-")
    try:
        nums = [int(p) for p in parts]
        if len(nums) == 1:
            return datetime(nums[0], 12, 31, tzinfo=timezone.utc)
        if len(nums) == 2:
            return datetime(nums[0], nums[1], calendar.monthrange(nums[0], nums[1])[1], tzinfo=timezone.utc)
        if len(nums) == 3:
            return datetime(nums[0], nums[1], nums[2], tzinfo=timezone.utc)
    except ValueError:
        pass
    raise ToolError(f"ngày không hợp lệ: {text!r}; dùng YYYY, YYYY-MM hoặc YYYY-MM-DD")


def _line(chunk: Chunk, show_time: bool, prefix: str = "") -> str:
    meta = ""
    if show_time:
        meta = f"({period_label(chunk)}{'; marked invalid' if chunk.invalidated_at is not None else ''}) "
    return f"{prefix}{chunk.chunk_id} {meta}{chunk.text.strip()}"


def _result(chunks: list[Chunk], head: str, show_time: bool, truncated: bool) -> ToolResult:
    lines = [head, *(_line(c, show_time, f"{i}. ") for i, c in enumerate(chunks, 1))]
    return ToolResult("\n\n".join(lines), tuple(c.chunk_id for c in chunks), truncated)


class VectorSearchArgs(BaseModel):
    query: str = Field(description="Text to search for.")
    mode: Literal["dense", "bm25", "hybrid"] = Field(default="hybrid", description="dense = embedding similarity, bm25 = keyword match, hybrid = both fused.")
    k: int = Field(default=5, ge=1, description="Number of results to return.")
    offset: int = Field(default=0, ge=0, description="Skip this many top results (to get the next page).")
    start_before: str | None = Field(default=None, description="Only return chunks whose start date is on or before this date (YYYY, YYYY-MM or "
                                     "YYYY-MM-DD; a partial date means the end of that year or month). Omit for no date filter.")
    include_invalidated: bool = Field(default=True, description="False excludes chunks marked as invalid.")


class TemporalSearchArgs(BaseModel):
    query: str = Field(description="Text to search for.")
    t_req: str = Field(description="Reference date (YYYY, YYYY-MM or YYYY-MM-DD).")
    k: int = Field(default=5, ge=1, description="Number of results to return.")


class ReadChunkArgs(BaseModel):
    chunk_id: str = Field(description="Chunk id as shown in search results.")
    neighbors: int = Field(default=0, ge=0, description="Also return this many chunks before and after it in the same page.")


class VectorTools:
    """Cài đặt ba công cụ trên `store`; `retriever` (tùy chọn) là `TemporalRetriever` dựng với `top_k` = `k_cap`, dùng cho `temporal_search`."""

    def __init__(self, store: VectorStore, retriever: TemporalRetriever | None = None, *, k_cap: int = DEFAULT_K_CAP, rrf_k: int = 60,
                 show_time: bool = True) -> None:
        self._store, self._retriever, self._cap, self._rrf_k, self._show_time = store, retriever, k_cap, rrf_k, show_time

    def vector_search(self, query: str, mode: str = "hybrid", k: int = 5, offset: int = 0, start_before: str | None = None,
                      include_invalidated: bool = True) -> ToolResult:
        """Hybrid/dense/BM25, không lọc trừ khi agent truyền `start_before` hoặc `include_invalidated=False`."""
        k, off = min(k, self._cap), min(offset, 10 * self._cap)
        flt = VectorFilter(t_req=parse_date(start_before) if start_before else _EPOCH, exclude_invalidated=not include_invalidated,
                           apply_time=start_before is not None)
        top_n = max(self._cap, off + k)
        hits = self._store.search(query, flt, top_n)
        if mode == "dense":
            ranked = [h.chunk for h in hits.dense]
        elif mode == "bm25":
            ranked = [h.chunk for h in hits.sparse]
        else:
            ranked = [c for c, _ in fuse(BranchHits(dense=hits.dense, sparse=hits.sparse), self._rrf_k, top_n)]
        part = ranked[off:off + k]
        head = f"{len(ranked)} candidate chunks; showing {len(part)} from rank {off + 1}" + (f"; more available (offset={off + k})" if off + k < len(ranked) else "")
        return _result(part, head, self._show_time, off + k < len(ranked))

    def temporal_search(self, query: str, t_req: str, k: int = 5) -> ToolResult:
        """Pipeline Cơ chế 1 nguyên vẹn (lọc cứng, RRF, W1·Sem + W2·Temp); cắt xuống `k` của agent."""
        if self._retriever is None:
            raise ToolError("temporal_search không khả dụng")
        res = self._retriever.retrieve(ProfiledQuery(semantic_query=query, t_req=parse_date(t_req)))
        chunks = [s.chunk for s in res.chunks[:min(k, self._cap)]]
        return _result(chunks, f"{len(chunks)} chunks ranked by relevance and closeness to {t_req}", self._show_time, False)

    def read_chunk(self, chunk_id: str, neighbors: int = 0) -> ToolResult:
        """Chunk theo id, kèm tối đa `MAX_NEIGHBORS` chunk liền kề mỗi phía (cùng trang), xếp theo chỉ số đoạn."""
        ids = [chunk_id, *neighbor_ids([chunk_id], min(neighbors, MAX_NEIGHBORS))]
        got = self._store.get_chunks(ids)
        if not any(c.chunk_id == chunk_id for c in got):
            raise ToolError(f"không có chunk {chunk_id!r}")
        got.sort(key=lambda c: (split_chunk_id(c.chunk_id) or (c.chunk_id, 0)))
        return _result(got, f"{len(got)} chunk(s)", self._show_time, False)

    def tools(self) -> list[AgentTool]:
        """Các công cụ dùng được (`temporal_search` chỉ khi có retriever)."""
        out = [
            AgentTool("vector_search", "Search the indexed chunks by text similarity. Results show the chunk id, its validity period when known, "
                      "and its text.", VectorSearchArgs, self.vector_search),
            AgentTool("read_chunk", "Read a chunk by id, optionally with the chunks around it in the same page.", ReadChunkArgs, self.read_chunk),
        ]
        if self._retriever is not None:
            out.insert(1, AgentTool("temporal_search", "Search the indexed chunks, ranking them by relevance and by how well their validity period "
                                    "matches a reference date.", TemporalSearchArgs, self.temporal_search))
        return out
