"""Khởi tạo logging cho cả project. Nơi duy nhất cấu hình log; module khác chỉ cần:

    from tam.config.logging import get_logger
    logger = get_logger(__name__)

`setup_logging()` gọi một lần ở điểm vào (scripts/*.py). Nó tạo output/<YYYYMMDD_HHMMSS>/ cho lần chạy,
ghi run.log vào đó, và cho phép module khác ghi sản phẩm của lần chạy vào cùng thư mục qua get_run_dir().

Lưu ý: file này tên `logging.py` nhưng `import logging` bên dưới vẫn là thư viện chuẩn (import tuyệt đối của
Python 3). Đừng chạy trực tiếp file này và đừng thêm thư mục `config/` vào PYTHONPATH.
"""
from __future__ import annotations

import contextlib
import contextvars
import json
import logging
import os
import sys
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

import yaml

from tam.config.loader import Config, project_root

TEXT_FORMAT = "%(asctime)s | %(levelname)-8s | %(query_id)s | %(name)s | %(message)s"
_HANDLER_MARK = "_tam_handler"

_query_id: contextvars.ContextVar[str] = contextvars.ContextVar("tam_query_id", default="-")
_run_dir: Path | None = None


class _QueryIdFilter(logging.Filter):
    """Gắn query_id hiện tại vào mọi bản ghi log."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.query_id = _query_id.get()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "query_id": getattr(record, "query_id", "-"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Dùng được ở mọi nơi, kể cả khi chưa gọi setup_logging() (khi đó chưa có handler, không tạo thư mục)."""
    return logging.getLogger(name)


@contextlib.contextmanager
def query_context(query_id: str) -> Iterator[None]:
    """Mọi log trong khối này mang query_id, để lọc hành trình của một câu hỏi."""
    token = _query_id.set(query_id)
    try:
        yield
    finally:
        _query_id.reset(token)


def get_run_dir() -> Path:
    """Thư mục output của lần chạy hiện tại (đã được setup_logging tạo)."""
    if _run_dir is None:
        raise RuntimeError("Chưa gọi setup_logging(): chưa có thư mục output của lần chạy")
    return _run_dir


def _create_run_dir(base: Path) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    candidate, n = base / stamp, 1
    while True:
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:  # hai lần chạy trùng giây
            n += 1
            candidate = base / f"{stamp}_{n}"


def setup_logging(config: Config, *, force: bool = False) -> Path:
    """Tạo output/<timestamp>/, gắn handler console + file. Trả về thư mục của lần chạy.

    `config` là toàn bộ Config (đọc nhóm `logging`, thiếu khóa nào dùng mặc định). Gọi lại lần nữa sẽ trả về
    cùng thư mục (không tạo thư mục mới) trừ khi force=True. Ghi thêm config.resolved.yaml (bí mật đã bị che).
    """
    global _run_dir
    if _run_dir is not None and not force:
        return _run_dir

    cfg = config.get("logging") or Config({})
    level = str(cfg.get("level", "INFO")).upper()
    fmt = cfg.get("format", "text")
    file_name = cfg.get("file_name", "run.log")
    module_levels = cfg.get("module_levels") or {}
    module_levels = module_levels.to_dict(masked=False) if isinstance(module_levels, Config) else module_levels

    out_root = Path(os.getenv("TAM_OUTPUT_DIR") or cfg.get("log_dir", "output"))
    if not out_root.is_absolute():
        out_root = project_root() / out_root
    _run_dir = _create_run_dir(out_root)

    formatter: logging.Formatter = _JsonFormatter() if fmt == "json" else logging.Formatter(TEXT_FORMAT)
    handlers: list[logging.Handler] = [
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(_run_dir / file_name, encoding="utf-8"),
    ]

    root = logging.getLogger()
    for old in [h for h in root.handlers if getattr(h, _HANDLER_MARK, False)]:  # tránh nhân đôi khi force
        root.removeHandler(old)
        old.close()
    for handler in handlers:
        handler.setFormatter(formatter)
        handler.addFilter(_QueryIdFilter())
        setattr(handler, _HANDLER_MARK, True)
        root.addHandler(handler)
    root.setLevel(level)
    for module, module_level in module_levels.items():
        logging.getLogger(module).setLevel(str(module_level).upper())

    (_run_dir / "config.resolved.yaml").write_text(
        yaml.safe_dump(config.to_dict(masked=True), allow_unicode=True, sort_keys=False), encoding="utf-8"
    )

    get_logger(__name__).info("Thư mục output của lần chạy: %s", _run_dir)
    return _run_dir
