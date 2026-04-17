import pytest
from school_mcp.config import Config


def test_from_env_with_all_required(monkeypatch):
    monkeypatch.setenv("SCHOOL_API_BASE", "http://localhost:8080/")
    monkeypatch.setenv("SCHOOL_USERNAME", "admin")
    monkeypatch.setenv("SCHOOL_PASSWORD", "pwd123")

    cfg = Config.from_env()

    assert cfg.api_base == "http://localhost:8080"
    assert cfg.username == "admin"
    assert cfg.password == "pwd123"
    assert cfg.timeout == 30.0
    assert cfg.log_level == "INFO"
    assert cfg.openapi_ttl == 300


def test_from_env_with_optional_overrides(monkeypatch):
    monkeypatch.setenv("SCHOOL_API_BASE", "http://x:8080")
    monkeypatch.setenv("SCHOOL_USERNAME", "u")
    monkeypatch.setenv("SCHOOL_PASSWORD", "p")
    monkeypatch.setenv("SCHOOL_TIMEOUT", "10.5")
    monkeypatch.setenv("SCHOOL_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SCHOOL_OPENAPI_TTL", "60")

    cfg = Config.from_env()

    assert cfg.timeout == 10.5
    assert cfg.log_level == "DEBUG"
    assert cfg.openapi_ttl == 60


def test_from_env_missing_required_exits(monkeypatch):
    monkeypatch.delenv("SCHOOL_API_BASE", raising=False)
    monkeypatch.delenv("SCHOOL_USERNAME", raising=False)
    monkeypatch.delenv("SCHOOL_PASSWORD", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        Config.from_env()
    assert "SCHOOL_API_BASE" in str(exc_info.value)
    assert "SCHOOL_USERNAME" in str(exc_info.value)
    assert "SCHOOL_PASSWORD" in str(exc_info.value)
