import textwrap

import pytest
import yaml

from tam.config import logging as tam_logging
from tam.config.loader import ConfigError, load_config


def write_cfg(tmp_path, body: str, env: str = "dev"):
    (tmp_path / f"config.{env}.yaml").write_text(textwrap.dedent(body), encoding="utf-8")
    return tmp_path


def test_real_configs_load():
    for env in ("dev", "prod"):
        cfg = load_config(env)
        assert cfg.app.env == env
        assert cfg.retrieval.top_k > 0
        assert cfg.llm.roles.generation in cfg.llm.profiles


def test_default_and_env_substitution(tmp_path, monkeypatch):
    d = write_cfg(tmp_path, """
        a: {url: "${X_URL:-http://localhost:1}", key: "${X_KEY:-}", name: "${X_NAME}"}
    """)
    monkeypatch.setenv("X_NAME", "ok")
    cfg = load_config("dev", d)
    assert cfg.a.url == "http://localhost:1"
    assert cfg.a.key is None  # ${VAR:-} rỗng -> None
    assert cfg.a.name == "ok"
    monkeypatch.setenv("X_URL", "http://real")
    assert load_config("dev", d).a.url == "http://real"


def test_missing_required_var_names_key(tmp_path):
    d = write_cfg(tmp_path, 'a: {name: "${X_MUST_HAVE}"}')
    with pytest.raises(ConfigError, match="a.name.*X_MUST_HAVE"):
        load_config("dev", d)


def test_unknown_env_lists_files(tmp_path):
    write_cfg(tmp_path, "a: 1")
    with pytest.raises(ConfigError, match="config.dev.yaml"):
        load_config("nope", tmp_path)


def test_attribute_and_item_access_and_missing_key(tmp_path):
    cfg = load_config("dev", write_cfg(tmp_path, "retrieval: {top_k: 5}"))
    assert cfg.retrieval.top_k == cfg["retrieval"]["top_k"] == 5
    with pytest.raises(AttributeError, match="retrieval.top_kk"):
        cfg.retrieval.top_kk


def test_secrets_masked(tmp_path, monkeypatch):
    monkeypatch.setenv("X_KEY", "super-secret")
    cfg = load_config("dev", write_cfg(tmp_path, 'p: {api_key: "${X_KEY}", model: m}'))
    assert "super-secret" not in repr(cfg)
    assert cfg.to_dict()["p"]["api_key"] == "********"
    assert cfg.to_dict(masked=False)["p"]["api_key"] == "super-secret"


@pytest.fixture
def clean_logging():
    import logging

    yield
    root = logging.getLogger()
    for h in [h for h in root.handlers if getattr(h, tam_logging._HANDLER_MARK, False)]:
        root.removeHandler(h)
        h.close()
    tam_logging._run_dir = None


def test_setup_logging_creates_run_dir(tmp_path, monkeypatch, clean_logging):
    monkeypatch.setenv("TAM_OUTPUT_DIR", str(tmp_path / "out"))
    cfg = load_config("dev")
    run_dir = tam_logging.setup_logging(cfg, force=True)
    assert run_dir.parent == tmp_path / "out"
    assert (run_dir / "config.resolved.yaml").is_file()
    resolved = yaml.safe_load((run_dir / "config.resolved.yaml").read_text(encoding="utf-8"))
    assert resolved["llm"]["profiles"]["claude_haiku"]["api_key"] in (None, "********")
    assert tam_logging.get_run_dir() == run_dir
    # gọi lần hai không force -> cùng thư mục
    assert tam_logging.setup_logging(cfg) == run_dir
    with tam_logging.query_context("q-42"):
        tam_logging.get_logger("tam.test").warning("xin chào")
    log = (run_dir / cfg.logging.file_name).read_text(encoding="utf-8")
    assert "q-42" in log and "xin chào" in log
