from app.db.base import Base


def test_alembic_metadata_is_available() -> None:
    assert Base.metadata is not None
