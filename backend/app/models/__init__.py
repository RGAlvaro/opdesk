"""Expose SQLAlchemy models so Alembic metadata discovery imports them."""

from app.models.user import User

__all__ = ["User"]
