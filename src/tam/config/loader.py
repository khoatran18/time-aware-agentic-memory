"""Nạp cấu hình: .env -> configs/config.{APP_ENV}.yaml -> thay ${VAR} -> Config (truy cập bằng dấu chấm)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

if __name__ == "__main__":
    # Chạy thẳng file này thì Python đặt thư mục config/ lên đầu sys.path, khiến `import logging`
    # (thư viện chuẩn, mà yaml/dotenv cũng dùng) nhận nhầm config/logging.py. Gỡ thư mục đó khỏi sys.path.
    _here = Path(__file__).resolve().parent
    sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != _here]

import logging
import re
from collections.abc import Iterator
from functools import lru_cache
from typing import Any

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

DEFAULT_ENV = "dev"
CONFIG_DIR_NAME = "configs"

# ${VAR} (bắt buộc) hoặc ${VAR:-mặc_định}
_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
# khóa có tên chứa các từ này sẽ bị che khi in / ghi ra file
_SECRET_KEY = re.compile(r"(key|secret|token|password)", re.IGNORECASE)


class ConfigError(Exception):
    """Lỗi nạp cấu hình, thông điệp nêu rõ file và khóa sai."""


class Config:
    """Bọc dict lồng nhau, đọc bằng cfg.retrieval.top_k hoặc cfg["retrieval"]["top_k"]."""

    def __init__(self, data: dict[str, Any], path: str = "") -> None:
        """`data`: dict đã thay biến; `path`: đường dẫn khóa hiện tại, dùng để báo lỗi."""
        self._data = data
        self._path = path

    def _wrap(self, name: str, value: Any) -> Any:
        """Bọc dict con thành Config để đọc tiếp bằng dấu chấm; giá trị khác giữ nguyên."""
        if isinstance(value, dict):
            return Config(value, f"{self._path}.{name}" if self._path else name)
        return value

    def __getattr__(self, name: str) -> Any:
        """`cfg.a.b`; thiếu khóa thì báo lỗi kèm đường dẫn và các khóa hiện có."""
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._wrap(name, self._data[name])
        except KeyError:
            where = f"{self._path}.{name}" if self._path else name
            raise AttributeError(f"Thiếu khóa cấu hình '{where}'; khóa hiện có: {sorted(self._data)}") from None

    def __getitem__(self, name: str) -> Any:
        """`cfg["a"]["b"]`; thiếu khóa thì KeyError."""
        return self._wrap(name, self._data[name])

    def get(self, name: str, default: Any = None) -> Any:
        """Giống dict.get."""
        return self._wrap(name, self._data[name]) if name in self._data else default

    def __contains__(self, name: object) -> bool:
        """`'a' in cfg`."""
        return name in self._data

    def __iter__(self) -> Iterator[str]:
        """Duyệt các khóa ở cấp này."""
        return iter(self._data)

    def keys(self):
        """Các khóa ở cấp này."""
        return self._data.keys()

    def items(self):
        """Cặp (khóa, giá trị); giá trị là dict thì được bọc thành Config."""
        return ((k, self._wrap(k, v)) for k, v in self._data.items())

    def to_dict(self, masked: bool = True) -> dict[str, Any]:
        """Bản dict thường; masked=True che giá trị của khóa có tên key/secret/token/password."""
        return _mask(self._data) if masked else _copy(self._data)

    def __repr__(self) -> str:
        """In cấu hình đã che bí mật."""
        return f"Config({self.to_dict(masked=True)!r})"


def _copy(node: Any) -> Any:
    """Sao chép sâu dict/list, không che gì."""
    if isinstance(node, dict):
        return {k: _copy(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_copy(v) for v in node]
    return node


def _mask(node: Any, key: str = "") -> Any:
    """Sao chép sâu, thay giá trị của khóa tên key/secret/token/password bằng '********'."""
    if isinstance(node, dict):
        return {k: _mask(v, str(k)) for k, v in node.items()}
    if isinstance(node, list):
        return [_mask(v, key) for v in node]
    if node and isinstance(node, str) and _SECRET_KEY.search(key):
        return "********"
    return node


def project_root() -> Path:
    """Gốc project = thư mục tổ tiên đầu tiên có chứa `configs/` (đổi được bằng TAM_PROJECT_ROOT)."""
    override = os.getenv("TAM_PROJECT_ROOT")
    if override:
        return Path(override).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / CONFIG_DIR_NAME).is_dir():
            return parent
    return Path.cwd()


def _expand_env(node: Any, path: str, missing: list[str]) -> Any:
    """Thay ${VAR} / ${VAR:-default} trong mọi chuỗi; ghi lại biến thiếu. Chuỗi chỉ có ${...} mà rỗng -> None."""
    if isinstance(node, dict):
        return {k: _expand_env(v, f"{path}.{k}" if path else str(k), missing) for k, v in node.items()}
    if isinstance(node, list):
        return [_expand_env(v, f"{path}[{i}]", missing) for i, v in enumerate(node)]
    if isinstance(node, str) and _ENV_PATTERN.search(node):

        def _sub(match: re.Match[str]) -> str:
            """Thay một `${VAR}` hoặc `${VAR:-mặc_định}`; biến bắt buộc mà thiếu thì ghi vào `missing`."""
            name, default = match.group(1), match.group(2)
            value = os.getenv(name)
            if value is not None and value != "":
                return value
            if default is not None:
                return default
            missing.append(f"{path}: thiếu biến môi trường {name}")
            return ""

        result = _ENV_PATTERN.sub(_sub, node)
        return result if result.strip() else None
    return node


def load_config(env: str | None = None, config_dir: Path | str | None = None) -> Config:
    """Nạp cấu hình cho môi trường `env` (mặc định: biến APP_ENV, rồi 'dev')."""
    root = project_root()
    load_dotenv(root / ".env", override=False)  # biến đã có sẵn trong môi trường được ưu tiên hơn .env

    env = env or os.getenv("APP_ENV") or DEFAULT_ENV
    directory = Path(config_dir or os.getenv("TAM_CONFIG_DIR") or root / CONFIG_DIR_NAME)
    path = directory / f"config.{env}.yaml"
    if not path.is_file():
        available = sorted(p.name for p in directory.glob("config.*.yaml")) if directory.is_dir() else []
        raise ConfigError(f"Không tìm thấy {path} (APP_ENV={env!r}); file hiện có: {available}")

    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} không phải YAML hợp lệ: {exc}") from exc
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} phải là một mapping ở cấp cao nhất")

    missing: list[str] = []
    expanded = _expand_env(raw, "", missing)
    if missing:
        raise ConfigError(f"{path} có biến môi trường chưa đặt:\n  " + "\n  ".join(missing))

    declared = (expanded.get("app") or {}).get("env")
    if declared is not None and declared != env:
        logger.warning("app.env=%r trong %s không khớp APP_ENV=%r", declared, path.name, env)
    return Config(expanded)


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Bản dùng chung cho cả tiến trình (nạp một lần)."""
    return load_config()


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        cfg = load_config(target)
    except ConfigError as exc:
        print(f"[LỖI] {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"[OK] Đã nạp cấu hình: env={cfg.app.env}, root={project_root()}")
    print("(!) In nguyên giá trị, KHÔNG che key, chỉ để kiểm tra; đừng dán output này lên nơi công khai")
    print(yaml.safe_dump(cfg.to_dict(masked=False), allow_unicode=True, sort_keys=False))
    print("Ví dụ truy cập:")
    print(f"  cfg.retrieval.top_k                  = {cfg.retrieval.top_k}")
    print(f"  cfg.llm.roles.generation             = {cfg.llm.roles.generation}")
    profile = cfg.llm.profiles[cfg.llm.roles.generation]
    print(f"  profile của role generation          = {profile.provider} / {profile.model_id}")
