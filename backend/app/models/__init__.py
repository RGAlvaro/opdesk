"""Expose SQLAlchemy models so Alembic metadata discovery imports them."""

from app.models.chat import (
    ChatConversation,
    ChatConversationParticipant,
    ChatConversationRead,
    ChatConversationType,
    ChatMessage,
)
from app.models.notification import (
    Notification,
    NotificationDelivery,
    NotificationDeliveryChannel,
    NotificationDeliveryStatus,
    NotificationType,
)
from app.models.operational import OperationalAuditRun, OperationalAuditStatus
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
    ProjectClientAccess,
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
    TicketComment,
)
from app.models.user import User

__all__ = [
    "MembershipRole",
    "ChatConversation",
    "ChatConversationParticipant",
    "ChatConversationRead",
    "ChatConversationType",
    "ChatMessage",
    "Invitation",
    "InvitationScope",
    "InvitationStatus",
    "Notification",
    "NotificationDelivery",
    "NotificationDeliveryChannel",
    "NotificationDeliveryStatus",
    "NotificationType",
    "Organization",
    "OrganizationMembership",
    "OperationalAuditRun",
    "OperationalAuditStatus",
    "Project",
    "ProjectClientAccess",
    "ProjectMembership",
    "ProjectStatus",
    "ProjectVisibility",
    "Task",
    "TicketComment",
    "TaskLabel",
    "TaskLabelAssignment",
    "TaskPriority",
    "TaskStatus",
    "TaskType",
    "TaskWatcher",
    "User",
]
