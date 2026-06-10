from app.core.config import Settings


def test_settings_load_database_url_from_environment(monkeypatch) -> None:
    database_url = "postgresql+psycopg://user:password@localhost:5432/test_db"
    monkeypatch.setenv("DATABASE_URL", database_url)

    settings = Settings()

    assert settings.database_url == database_url
