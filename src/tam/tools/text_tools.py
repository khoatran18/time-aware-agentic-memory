"""Bộ công cụ kiểu A (kho text thuần) cho agent: mô tả công cụ là một phần cố định của harness, giữ trung tính."""
from __future__ import annotations

from pydantic import BaseModel, Field

from tam.tools.base import AgentTool
from tam.tools.text_corpus import TextCorpus


class ListPagesArgs(BaseModel):
    contains: str | None = Field(default=None, description="Only list page names containing this text (case-insensitive).")
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=50, ge=1)


class GrepArgs(BaseModel):
    pattern: str = Field(description="Regular expression (Python syntax).")
    page: str | None = Field(default=None, description="Restrict the search to this page name; omit to search every page.")
    ignore_case: bool = True
    max_hits: int = Field(default=20, ge=1)
    offset: int = Field(default=0, ge=0)
    context: int = Field(default=100, ge=0, description="Characters of text shown on each side of the first match.")


class ReadPageArgs(BaseModel):
    page: str = Field(description="Page name, as returned by list_pages or grep.")
    start: int = Field(default=0, ge=0, description="First passage number ([#n]) to read.")
    end: int | None = Field(default=None, description="Last passage number to read; omit to read to the end of the page.")
    max_chars: int = Field(default=8000, ge=1)


def text_tools(corpus: TextCorpus) -> list[AgentTool]:
    """`list_pages`, `grep`, `read_page` trên `corpus`."""
    return [
        AgentTool("list_pages", "List the names of the pages in the collection. Each page is a Wikipedia article split into numbered passages [#n].",
                  ListPagesArgs, corpus.list_pages),
        AgentTool("grep", "Search the passages with a regular expression. Returns one line per matching passage: page name, passage number, "
                  "number of matches and a short excerpt around the first match, not the whole passage; use read_page to read a whole passage.", GrepArgs, corpus.grep),
        AgentTool("read_page", "Read the full text of the passages [#n] of a page.", ReadPageArgs, corpus.read_page),
    ]
