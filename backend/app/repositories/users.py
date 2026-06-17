"""Data access helpers for user persistence operations."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    """Encapsulate user queries and writes behind a small repository boundary."""

    def __init__(self, db: Session) -> None:
        """Store the active database session used by repository methods."""
        self.db = db

    def count_users(self) -> int:
        """Return the number of registered users for first-user bootstrap logic."""
        return self.db.scalar(select(func.count(User.id))) or 0

    def get_by_email(self, email: str) -> User | None:
        """Find a user by normalized email address."""
        return self.db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: object) -> User | None:
        """Load a user by primary key for auth token resolution."""
        return self.db.get(User, user_id)

    def add(self, user: User) -> User:
        """Persist a new user and refresh generated database fields."""
        self.db.add(user)
        self.db.flush()
        self.db.refresh(user)
        return user
