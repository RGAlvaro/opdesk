"""Business rules for scheduled jobs and operational audit visibility."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.operational import OperationalAuditRun, OperationalAuditStatus
from app.models.organization import Invitation, InvitationStatus, MembershipRole
from app.models.project import Task, TicketAssignmentRequest, TicketAssignmentRequestStatus
from app.models.user import User, UserAccountType
from app.notifications.delivery import ExternalNotificationDeliveryService
from app.repositories.notifications import NotificationRepository
from app.repositories.operational_audit import OperationalAuditRepository
from app.repositories.organizations import OrganizationRepository
from app.services.notifications import NotificationService

logger = logging.getLogger(__name__)

heartbeat_job_name = "scheduler_heartbeat"
external_delivery_retry_job_name = "external_delivery_retry_sweep"
expired_invitations_job_name = "expired_invitation_maintenance"
ticket_assignment_reminders_job_name = "stale_ticket_assignment_request_reminders"
stale_assignment_request_age = timedelta(hours=24)


@dataclass(frozen=True)
class JobRunResult:
    """Safe count summary returned by a scheduled job implementation."""

    records_seen: int | None = None
    records_changed: int | None = None
    skipped: bool = False


def parse_audit_status(value: str | None) -> OperationalAuditStatus | None:
    """Convert optional public status text into an audit status enum."""
    if value is None:
        return None
    try:
        return OperationalAuditStatus(value)
    except ValueError as exc:
        raise APIError(400, "invalid_audit_filter", "Operational audit status is invalid.") from exc


class OperationalAuditService:
    """Coordinate audit rows, scheduled jobs, and owner/admin visibility."""

    def __init__(self, db: Session) -> None:
        """Create collaborators bound to the active transaction."""
        self.db = db
        self.audit = OperationalAuditRepository(db)
        self.organizations = OrganizationRepository(db)
        self.notifications = NotificationRepository(db)

    def list_runs(
        self,
        actor: User,
        *,
        limit: int,
        offset: int,
        job_name: str | None,
        status: str | None,
    ) -> tuple[list[OperationalAuditRun], int]:
        """List audit rows only for internal users with any owner/admin role."""
        self._require_owner_admin_context(actor)
        return self.audit.list_runs(
            limit=limit,
            offset=offset,
            job_name=job_name,
            status=parse_audit_status(status),
        )

    def run_job(
        self,
        job_name: str,
        job: Callable[[], JobRunResult],
        *,
        scheduled_for: datetime | None = None,
    ) -> OperationalAuditRun:
        """Run one scheduled job and persist a sanitized audit outcome."""
        now = datetime.now(UTC)
        audit_run = self.audit.add(
            OperationalAuditRun(
                job_name=job_name,
                scheduled_for=scheduled_for,
                started_at=now,
                status=OperationalAuditStatus.STARTED,
            )
        )
        self.db.commit()
        try:
            result = job()
        except Exception as exc:  # pragma: no cover - exercised through tests with explicit raises.
            self.db.rollback()
            audit_run = self.db.merge(audit_run)
            audit_run.status = OperationalAuditStatus.FAILED
            audit_run.finished_at = datetime.now(UTC)
            audit_run.error_code = exc.__class__.__name__
            audit_run.error_message = self._sanitize_error_message(str(exc))
            self.db.add(audit_run)
            self.db.commit()
            logger.exception(
                "scheduled_job failed job_name=%s audit_id=%s error_class=%s",
                job_name,
                audit_run.id,
                exc.__class__.__name__,
            )
            return audit_run

        audit_run = self.db.merge(audit_run)
        audit_run.finished_at = datetime.now(UTC)
        audit_run.status = (
            OperationalAuditStatus.SKIPPED if result.skipped else OperationalAuditStatus.SUCCEEDED
        )
        audit_run.records_seen = result.records_seen
        audit_run.records_changed = result.records_changed
        self.db.add(audit_run)
        self.db.commit()
        logger.info(
            "scheduled_job finished job_name=%s audit_id=%s status=%s "
            "records_seen=%s records_changed=%s",
            job_name,
            audit_run.id,
            audit_run.status.value,
            audit_run.records_seen,
            audit_run.records_changed,
        )
        return audit_run

    def scheduler_heartbeat(self) -> JobRunResult:
        """Record that the scheduler and worker can execute a trivial job."""
        return JobRunResult(records_seen=1, records_changed=1)

    def external_delivery_retry_sweep(self, limit: int = 100) -> JobRunResult:
        """Retry pending external notification deliveries that are currently due."""
        due_count = self.notifications.count_due_deliveries(limit)
        changed = ExternalNotificationDeliveryService(self.db).process_due_deliveries(limit)
        return JobRunResult(records_seen=due_count, records_changed=changed)

    def expire_pending_invitations(self) -> JobRunResult:
        """Move stale pending invitations to their terminal expired state."""
        now = datetime.now(UTC)
        invitations = list(
            self.db.scalars(
                select(Invitation).where(
                    Invitation.status == InvitationStatus.PENDING,
                    Invitation.expires_at <= now,
                )
            )
        )
        for invitation in invitations:
            invitation.status = InvitationStatus.EXPIRED
            self.db.add(invitation)
            NotificationService(self.db).mark_invitation_read(invitation)
        self.db.commit()
        return JobRunResult(records_seen=len(invitations), records_changed=len(invitations))

    def remind_stale_assignment_requests(self) -> JobRunResult:
        """Create safe aggregate reminders for old pending ticket handoff requests."""
        cutoff = datetime.now(UTC) - stale_assignment_request_age
        requests = list(
            self.db.scalars(
                select(TicketAssignmentRequest)
                .join(Task, Task.id == TicketAssignmentRequest.task_id)
                .where(
                    TicketAssignmentRequest.status == TicketAssignmentRequestStatus.PENDING,
                    TicketAssignmentRequest.created_at <= cutoff,
                )
            )
        )
        notifier = NotificationService(self.db)
        for request in requests:
            task = self.db.get(Task, request.task_id)
            if task is None:
                continue
            notifier.notify_ticket_assignment_requested(
                request.requested_by_id,
                task,
                request.target_user_id,
            )
        self.db.commit()
        return JobRunResult(records_seen=len(requests), records_changed=len(requests))

    def _require_owner_admin_context(self, actor: User) -> None:
        """Require an internal account with at least one owner/admin membership."""
        if actor.account_type == UserAccountType.CLIENT:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        organizations, _total = self.organizations.list_for_user(actor.id, limit=100, offset=0)
        if not any(
            membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}
            for _organization, membership in organizations
        ):
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")

    @staticmethod
    def _sanitize_error_message(message: str) -> str:
        """Bound stored error text so audit rows never contain raw payloads."""
        cleaned = " ".join(message.split())
        return cleaned[:255] if cleaned else "Scheduled job failed."
