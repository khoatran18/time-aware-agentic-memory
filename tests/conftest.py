import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Test không phụ thuộc .env hay biến môi trường của máy."""
    for name in ("APP_ENV", "TAM_CONFIG_DIR", "TAM_PROJECT_ROOT", "TAM_OUTPUT_DIR"):
        monkeypatch.delenv(name, raising=False)
