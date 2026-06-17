"""Settings loading tests for environment-backed backend configuration."""

from app.core.config import Settings


def test_settings_load_database_url_from_environment(monkeypatch) -> None:
    """DATABASE_URL from the environment overrides the local default."""
    database_url = "postgresql+psycopg://user:password@localhost:5432/test_db"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()

    assert settings.database_url == database_url
