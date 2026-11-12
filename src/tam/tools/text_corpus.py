"""Kho text thuần và ba công cụ của agent search kiểu A: `list_pages`, `grep`, `read_page`. Không gọi LLM, không embed, không có mốc thời gian.

Mỗi trang là một file `<tên>.txt`; mỗi đoạn mở đầu bằng `[#i]` rồi đúng văn bản chunk mà ingestion tạo ra, nên `[#i]` khớp
`chunk_id = <page_id>#<i>` (page_id = `/wiki/` + tên, `%2F` đổi lại thành `/`). Agent chỉ thấy tên trang và `[#i]`; `ToolResult.chunk_ids`
dành cho vết (đối chiếu chunk gold với thứ agent đã đọc). Kho không biết trang thuộc tập nào (tune, valid, test_clean).
"""
from __future__ import annotations

import difflib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from tam.ingestion.chunking import chunk_document
from tam.ingestion.loaders.timeqa import load_pages
from tam.tools.base import ToolError, ToolResult

MAX_NAME = 180
MAX_PATTERN = 200
HARD_MAX_HITS = 100
HARD_MAX_PAGES = 200
HARD_MAX_CHARS = 20_000
_PART = re.compile(r"\n\n(?=\[#\d+\] )")
_HEAD = re.compile(r"\[#(\d+)\] ")


@dataclass(frozen=True)
class Passage:
    page: str
    idx: int
    text: str

    @property
    def chunk_id(self) -> str:
        return f"{page_id_of(self.page)}#{self.idx}"


def file_name(page_id: str) -> str:
    """'/wiki/Knox_Cunningham' -> 'Knox_Cunningham.txt'; dấu '/' trong tên trang đổi thành '%2F'."""
    return page_id.removeprefix("/wiki/").replace("/", "%2F").replace("\x00", "")[:MAX_NAME] + ".txt"


def page_id_of(name: str) -> str:
    """Tên trang (không đuôi) -> page_id."""
    return "/wiki/" + name.replace("%2F", "/")


def render_doc(doc) -> str:
    """Văn bản một trang: mỗi chunk là `[#i] <văn bản chunk>`, cách nhau một dòng trống."""
    return "\n\n".join(f"[#{c.chunk_id.rpartition('#')[2]}] {c.text}" for c in chunk_document(doc)) + "\n"


def build_corpus(pages_path: str | Path, split_of: Mapping[str, str], out_dir: str | Path) -> dict[str, dict[str, str]]:
    """Ghi mỗi trang trong `split_of` (page_id -> tên tập) thành một file `.txt` trong `out_dir`; trả bảng `{page_id: {file, split}}`.

    Bảng này không nằm trong `out_dir` (người gọi tự ghi), để công cụ của agent không thấy tên tập."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    index: dict[str, dict[str, str]] = {}
    names: dict[str, str] = {}
    for doc in load_pages(pages_path, set(split_of)):
        name = file_name(doc.doc_id)
        if name in names:
            raise ValueError(f"trùng tên file {name!r}: {names[name]} và {doc.doc_id}")
        names[name] = doc.doc_id
        (out / name).write_text(render_doc(doc), encoding="utf-8")
        index[doc.doc_id] = {"file": name, "split": split_of[doc.doc_id]}
    return index


def _parse(content: str) -> list[tuple[int, str]]:
    """Tách nội dung file thành [(chỉ số đoạn, văn bản chunk)]."""
    out = []
    for part in _PART.split(content.rstrip("\n")):
        m = _HEAD.match(part)
        if m:
            out.append((int(m.group(1)), part[m.end():]))
    return out


@dataclass
class TextCorpus:
    """Kho text trong bộ nhớ và ba công cụ. Tạo bằng `TextCorpus.load(thư_mục)`."""

    pages: dict[str, list[Passage]] = field(default_factory=dict)

    @classmethod
    def load(cls, root: str | Path) -> TextCorpus:
        pages: dict[str, list[Passage]] = {}
        for path in sorted(Path(root).glob("*.txt")):
            name = path.stem
            pages[name] = [Passage(name, i, t) for i, t in _parse(path.read_text(encoding="utf-8"))]
        return cls(pages)

    # ---- công cụ ----
    def list_pages(self, contains: str | None = None, offset: int = 0, limit: int = 50) -> ToolResult:
        """Tên các trang (lọc theo chuỗi con không phân biệt hoa thường); có phân trang."""
        limit = max(1, min(limit, HARD_MAX_PAGES))
        names = [n for n in self.pages if contains is None or contains.lower() in n.lower()]
        part = names[max(0, offset):max(0, offset) + limit]
        more = max(0, offset) + limit < len(names)
        head = f"{len(names)} trang khớp; hiển thị {len(part)} từ vị trí {max(0, offset)}" + (f"; còn nữa (offset={max(0, offset) + limit})" if more else "")
        return ToolResult("\n".join([head, *part]), truncated=more)

    def grep(self, pattern: str, page: str | None = None, ignore_case: bool = True, max_hits: int = 20, offset: int = 0,
             context: int = 100) -> ToolResult:
        """Tìm regex trong các đoạn (một kết quả mỗi đoạn, kèm số lần khớp và đoạn trích quanh lần khớp đầu). Có phân trang."""
        if not pattern or len(pattern) > MAX_PATTERN:
            raise ToolError(f"pattern rỗng hoặc dài quá {MAX_PATTERN} ký tự")
        try:
            rx = re.compile(pattern, re.IGNORECASE if ignore_case else 0)
        except re.error as exc:
            raise ToolError(f"regex không hợp lệ: {exc}") from exc
        max_hits = max(1, min(max_hits, HARD_MAX_HITS))
        context = max(0, min(context, 500))
        hits: list[tuple[Passage, int, re.Match[str]]] = []
        for name in ([self._require(page)] if page else self.pages):
            for p in self.pages[name]:
                ms = list(rx.finditer(p.text))
                if ms:
                    hits.append((p, len(ms), ms[0]))
        off = max(0, offset)
        shown = hits[off:off + max_hits]
        lines = [f"{len(hits)} đoạn khớp; hiển thị {len(shown)} từ vị trí {off}" + (f"; còn nữa (offset={off + max_hits})" if off + max_hits < len(hits) else "")]
        for p, n, m in shown:
            a, b = max(0, m.start() - context), min(len(p.text), m.end() + context)
            snippet = ("…" if a else "") + p.text[a:b].replace("\n", " ") + ("…" if b < len(p.text) else "")
            lines.append(f"{p.page} [#{p.idx}] ({n} lần): {snippet}")
        return ToolResult("\n".join(lines), tuple(p.chunk_id for p, _, _ in shown), off + max_hits < len(hits))

    def read_page(self, page: str, start: int = 0, end: int | None = None, max_chars: int = 8000) -> ToolResult:
        """Đọc các đoạn có chỉ số trong [start, end] (end rỗng = hết trang). Dừng ở ranh giới đoạn khi chạm `max_chars` và nói `next_start`."""
        name = self._require(page)
        max_chars = max(200, min(max_chars, HARD_MAX_CHARS))
        todo = [p for p in self.pages[name] if p.idx >= start and (end is None or p.idx <= end)]
        out, used, ids = [], 0, []
        for k, p in enumerate(todo):
            body = f"[#{p.idx}] {p.text}"
            if out and used + len(body) > max_chars:
                out.append(f"(đã cắt theo giới hạn ký tự; đọc tiếp bằng start={p.idx})")
                return ToolResult("\n\n".join(out), tuple(ids), True)
            if not out and len(body) > max_chars:
                body = body[:max_chars] + " …(đoạn bị cắt)"
            out.append(body)
            used += len(body)
            ids.append(p.chunk_id)
        if not out:
            last = self.pages[name][-1].idx if self.pages[name] else None
            raise ToolError(f"{name} không có đoạn nào trong khoảng đã chọn (chỉ số đoạn lớn nhất: {last})")
        return ToolResult("\n\n".join(out), tuple(ids), False)

    def _require(self, page: str) -> str:
        """Tên trang hợp lệ (nhận cả đuôi .txt); sai thì báo lỗi kèm gợi ý tên gần giống."""
        name = page.removesuffix(".txt")
        if name not in self.pages:
            near = difflib.get_close_matches(name, list(self.pages), n=3, cutoff=0.6)
            raise ToolError(f"không có trang {page!r}" + (f"; có thể là: {', '.join(near)}" if near else "; dùng list_pages để xem tên trang"))
        return name


def write_index(index: Mapping[str, object], path: str | Path) -> None:
    """Ghi bảng `{page_id: {file, split}}` (ngoài thư mục corpus)."""
    Path(path).write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
