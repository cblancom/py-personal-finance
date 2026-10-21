import pytest

from app.core.config import get_settings, load_settings


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_load_settings_reads_database_url():
    database_url = "postgresql+psycopg://user:password@localhost:5432/personal_finance"

    settings = load_settings({"DATABASE_URL": database_url})

    assert settings.database_url == database_url


def test_load_settings_requires_database_url():
    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is required"):
        load_settings({})


def test_load_settings_rejects_blank_database_url():
    with pytest.raises(RuntimeError, match="DATABASE_URL environment variable is required"):
        load_settings({"DATABASE_URL": "   "})


def test_error_message_does_not_include_other_environment_values():
    with pytest.raises(RuntimeError) as exc_info:
        load_settings({"SECRET_KEY": "super-secret"})

    assert "super-secret" not in str(exc_info.value)


def test_get_settings_is_cached(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:password@localhost:5432/personal_finance",
    )

    assert get_settings() is get_settings()
