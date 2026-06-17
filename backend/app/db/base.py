"""Shared SQLAlchemy declarative base for all persistence models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class that collects model metadata for migrations and sessions."""

    pass
