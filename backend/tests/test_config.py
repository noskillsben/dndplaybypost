import pytest
from pydantic import ValidationError

from core.config import Settings


def test_missing_database_url_fails_fast(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings()


def test_cors_origins_parsed_into_list(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite://")
    monkeypatch.setenv("CORS_ORIGINS", "http://a.example, http://b.example,")
    settings = Settings()
    assert settings.cors_origins_list == ["http://a.example", "http://b.example"]


def test_debug_defaults_false(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite://")
    monkeypatch.delenv("DEBUG", raising=False)
    assert Settings().debug is False
