"""Expose SQLAlchemy models so Alembic metadata discovery imports them."""

from app.models.organization import MembershipRole, Organization, OrganizationMembership
from app.models.project import (
    Project,
    ProjectStatus,
    ProjectVisibility,
    Task,
    TaskLabel,
    TaskLabelAssignment,
    TaskPriority,
    TaskStatus,
    TaskType,
    TaskWatcher,
)
from app.models.user import User

__all__ = [
    "MembershipRole",
    "Organization",
    "OrganizationMembership",
    "Project",
    "ProjectStatus",
    "ProjectVisibility",
    "Task",
    "TaskLabel",
    "TaskLabelAssignment",
    "TaskPriority",
    "TaskStatus",
    "TaskType",
    "TaskWatcher",
    "User",
]
