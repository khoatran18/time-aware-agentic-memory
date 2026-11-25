"""Tìm file prompt theo tên (không đuôi): thư mục `prompts/` (đang dùng), rồi `prompts/archive/` (bản cũ, giữ để chạy lại lệnh cũ).

Tên cũ hoặc tên theo số phiên bản (`agent_v5`, `ingestion_time_v3`...) ánh xạ sang file đang dùng qua `ALIASES` (xem prompts/README.md), nên `--prompt v5` hay `--prompt-version v3` vẫn chạy.
"""
from __future__ import annotations

from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent / "prompts"
ARCHIVE_DIR = PROMPT_DIR / "archive"
ALIASES = {  # tên cũ hoặc tên theo số phiên bản -> file đang dùng
    "agent_v5": "agent_m2", "agent_v6": "agent_m3",
    "ingestion_time_v3": "ingest_m1",    # bản đang dùng của prompt nạp kho vector (tune, valid, test_clean)
    "time_extractor_v2": "profiler_m1",  # bản đang dùng của Profiler (khoảng thời gian)
}


def prompt_path(stem: str) -> Path:
    """Đường dẫn `<stem>.md` trong prompts/ hoặc prompts/archive/; ném FileNotFoundError nếu không có."""
    stem = ALIASES.get(stem, stem)
    for folder in (PROMPT_DIR, ARCHIVE_DIR):
        path = folder / f"{stem}.md"
        if path.exists():
            return path
    raise FileNotFoundError(f"không có prompt {stem!r} trong {PROMPT_DIR} hoặc {ARCHIVE_DIR}")


def available_versions(prefix: str) -> list[str]:
    """Các hậu tố `v...` chọn được cho `<prefix>_<v>` (file trong prompts/, archive/ và tên trong ALIASES)."""
    stems = {p.stem for folder in (PROMPT_DIR, ARCHIVE_DIR) for p in folder.glob(f"{prefix}_v*.md")}
    stems |= {k for k in ALIASES if k.startswith(f"{prefix}_v")}
    return sorted(stem.removeprefix(f"{prefix}_") for stem in stems)
