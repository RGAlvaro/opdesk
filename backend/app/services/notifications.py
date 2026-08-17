"""Business rules for persistent in-app notification inbox behavior."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.notification import Notification, NotificationType
from app.models.organization import Invitation, InvitationScope
from app.models.project import Project, Task
from app.models.user import User
from app.repositories.notifications import NotificationRepository
from app.repositories.projects import ProjectRepository
from app.repositories.tasks import TaskRepository


class NotificationService:
    """Coordinate recipient-scoped inbox state and domain event fan-out."""

    def __init__(self, db: Session) -> None:
        """Create notification collaborators bound to the request transaction."""
        self.db = db
        self.notifications = NotificationRepository(db)
        self.projects = ProjectRepository(db)
        self.tasks = TaskRepository(db)

    def list_notifications(
        self, actor: User, limit: int, offset: int, unread: bool | None
    ) -> tuple[list[Notification], int]:
        """List only notifications owned by the authenticated actor."""
        return self.notifications.list_for_recipient(actor.id, limit, offset, unread)

    def unread_count(self, actor: User) -> int:
        """Count unread notifications owned by the authenticated actor."""
        return self.notifications.unread_count(actor.id)

    def set_read_state(
        self, actor: User, notification_id: uuid.UUID, *, read: bool
    ) -> Notification:
        """Mark one current-user notification read or unread."""
        notification = self.notifications.get_for_recipient(notification_id, actor.id)
        if notification is None:
            raise APIError(404, "notification_not_found", "Notification was not found.")
        notification.read_at = datetime.now(UTC) if read else None
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_read(self, actor: User) -> None:
        """Mark every unread current-user notification read."""
        now = datetime.now(UTC)
        for notification in self.notifications.mark_all_read(actor.id):
            notification.read_at = now
            self.db.add(notification)
        self.db.commit()

    def notify_invitation_created(self, invitation: Invitation, organization_name: str) -> None:
        """Create an actionable notification for an invitation recipient."""
        if invitation.scope_type == InvitationScope.ORGANIZATION:
            notification_type = NotificationType.INVITATION_ORGANIZATION
            title = "Organization invitation"
            body = f"You were invited to {organization_name}."
        else:
            notification_type = NotificationType.INVITATION_PROJECT
            title = "Project invitation"
            body = f"You were invited to a project in {organization_name}."
        self._create_once(
            recipient_user_id=invitation.target_user_id,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url="/app/invitations",
            resource_type="invitation",
            resource_id=invitation.id,
        )

    def mark_invitation_read(self, invitation: Invitation) -> None:
        """Mark matching unread invitation notifications read after user action."""
        for notification_type in (
            NotificationType.INVITATION_ORGANIZATION,
            NotificationType.INVITATION_PROJECT,
        ):
            notification = self.notifications.find_unread_for_resource(
                recipient_user_id=invitation.target_user_id,
                notification_type=notification_type,
                resource_type="invitation",
                resource_id=invitation.id,
            )
            if notification is not None:
                notification.read_at = datetime.now(UTC)
                self.db.add(notification)

    def notify_project_membership(self, project: Project, user_id: uuid.UUID) -> None:
        """Notify a user that explicit project access was added."""
        self._create_once(
            recipient_user_id=user_id,
            notification_type=NotificationType.PROJECT_MEMBERSHIP,
            title="Project access added",
            body=f"You were added to {project.name}.",
            action_url=f"/app/projects/{project.id}",
            resource_type="project",
            resource_id=project.id,
        )

    def notify_project_updated(
        self, actor_id: uuid.UUID, project: Project, changes: set[str]
    ) -> None:
        """Notify explicit project members about visible project state changes."""
        relevant = changes & {"status", "is_archived", "visibility", "project_owner_id"}
        if not relevant:
            return
        for recipient_id in self.projects.list_member_user_ids(project.id):
            if recipient_id == actor_id:
                continue
            self._create_once(
                recipient_user_id=recipient_id,
                notification_type=NotificationType.PROJECT_UPDATED,
                title="Project updated",
                body=f"{project.name} changed.",
                action_url=f"/app/projects/{project.id}",
                resource_type="project",
                resource_id=project.id,
            )

    def notify_task_created_or_assigned(
        self, actor_id: uuid.UUID, task: Task, *, created: bool
    ) -> None:
        """Notify the task assignee about creation or assignment events."""
        if task.assignee_id is None or task.assignee_id == actor_id:
            return
        self._create_once(
            recipient_user_id=task.assignee_id,
            notification_type=NotificationType.TASK_CREATED
            if created
            else NotificationType.TASK_ASSIGNED,
            title="Task assigned",
            body=f"{task.title} is assigned to you.",
            action_url=f"/app/tasks/{task.id}",
            resource_type="task",
            resource_id=task.id,
        )

    def notify_task_status_changed(self, actor_id: uuid.UUID, task: Task) -> None:
        """Notify assignee and watchers about a task status transition."""
        recipients = set(self.tasks.list_watcher_user_ids(task.id))
        if task.assignee_id is not None:
            recipients.add(task.assignee_id)
        recipients.discard(actor_id)
        for recipient_id in recipients:
            self._create_once(
                recipient_user_id=recipient_id,
                notification_type=NotificationType.TASK_STATUS_CHANGED,
                title="Task status changed",
                body=f"{task.title} is now {task.status.value.replace('_', ' ')}.",
                action_url=f"/app/tasks/{task.id}",
                resource_type="task",
                resource_id=task.id,
            )

    def notify_ticket_comment(
        self, actor_id: uuid.UUID, task: Task, recipient_ids: set[uuid.UUID]
    ) -> None:
        """Create one aggregate unread notification per recipient and ticket."""
        recipient_ids.discard(actor_id)
        for recipient_id in recipient_ids:
            self._create_once(
                recipient_user_id=recipient_id,
                notification_type=NotificationType.TICKET_COMMENT,
                title="Unread ticket comments",
                body=f"{task.title} has unread ticket feedback.",
                action_url=f"/app/tickets/{task.id}"
                if task.client_user_id != recipient_id
                else f"/app/client/tickets/{task.id}",
                resource_type="ticket",
                resource_id=task.id,
            )

    def notify_ticket_assignment_requested(
        self, actor_id: uuid.UUID, task: Task, target_user_id: uuid.UUID
    ) -> None:
        """Notify the target worker that a ticket handoff needs acceptance."""
        if target_user_id == actor_id:
            return
        self._create_once(
            recipient_user_id=target_user_id,
            notification_type=NotificationType.TICKET_ASSIGNMENT_REQUESTED,
            title="Ticket assignment request",
            body=f"{task.title} needs your assignment response.",
            action_url="/app/ticket-assignment-requests",
            resource_type="ticket",
            resource_id=task.id,
        )

    def _create_once(
        self,
        *,
        recipient_user_id: uuid.UUID,
        notification_type: NotificationType,
        title: str,
        body: str | None,
        action_url: str | None,
        resource_type: str,
        resource_id: uuid.UUID,
    ) -> Notification:
        """Create a notification unless an equivalent unread one already exists."""
        existing = self.notifications.find_unread_for_resource(
            recipient_user_id=recipient_user_id,
            notification_type=notification_type,
            resource_type=resource_type,
            resource_id=resource_id,
        )
        if existing is not None:
            return existing
        return self.notifications.add(
            Notification(
                recipient_user_id=recipient_user_id,
                type=notification_type,
                title=title,
                body=body,
                action_url=action_url,
                resource_type=resource_type,
                resource_id=resource_id,
            )
        )
