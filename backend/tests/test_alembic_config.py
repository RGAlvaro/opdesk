"""Alembic configuration smoke tests for migration metadata."""

from app.db.base import Base


def test_alembic_metadata_is_available() -> None:
    """Migration autogeneration can see the shared SQLAlchemy metadata."""
    assert Base.metadata is not None
