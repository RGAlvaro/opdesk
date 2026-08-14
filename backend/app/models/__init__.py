"""Expose SQLAlchemy models so Alembic metadata discovery imports them."""

from app.models.organization import (
    Invitation,
    InvitationScope,
    InvitationStatus,
    MembershipRole,
    Organization,
    OrganizationMembership,
)
from app.models.project import (
    Project,
    ProjectMembership,
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
    "Invitation",
    "InvitationScope",
    "InvitationStatus",
    "Organization",
    "OrganizationMembership",
    "Project",
    "ProjectMembership",
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
