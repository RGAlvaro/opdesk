"""Database session integration checks against local PostgreSQL."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.db.session import create_database_engine


@pytest.mark.db
def test_database_engine_can_connect_when_postgres_is_available() -> None:
    """The configured SQLAlchemy engine can execute a basic PostgreSQL query."""
    engine = create_database_engine()

    try:
        with engine.connect() as connection:
            result = connection.execute(text("select 1")).scalar_one()
    except OperationalError as exc:
        pytest.skip(f"PostgreSQL is not available: {exc}")

    assert result == 1
