"""Data access operations for invitation lifecycle state."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import Invitation, InvitationScope, InvitationStatus


class InvitationRepository:
    """Keep invitation queries scoped by recipient or owning organization."""

    def __init__(self, db: Session) -> None:
        """Store the active request transaction."""
        self.db = db

    def add(self, invitation: Invitation) -> Invitation:
        """Stage and flush a new invitation row."""
        self.db.add(invitation)
        self.db.flush()
        return invitation

    def get_by_id(self, invitation_id: uuid.UUID) -> Invitation | None:
        """Load one invitation by primary key."""
        return self.db.get(Invitation, invitation_id)

    def get_for_target(
        self, invitation_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> Invitation | None:
        """Load an invitation only when addressed to the supplied user."""
        return self.db.scalar(
            select(Invitation).where(
                Invitation.id == invitation_id,
                Invitation.target_user_id == target_user_id,
            )
        )

    def get_pending_for_scope(
        self,
        *,
        organization_id: uuid.UUID,
        target_user_id: uuid.UUID,
        scope_type: InvitationScope,
        project_id: uuid.UUID | None,
    ) -> Invitation | None:
        """Return one active pending invitation for the same recipient and scope."""
        filters = [
            Invitation.organization_id == organization_id,
            Invitation.target_user_id == target_user_id,
            Invitation.scope_type == scope_type,
            Invitation.status == InvitationStatus.PENDING,
        ]
        if scope_type == InvitationScope.PROJECT:
            filters.append(Invitation.project_id == project_id)
        return self.db.scalar(select(Invitation).where(*filters))

    def list_for_target(
        self, target_user_id: uuid.UUID, limit: int, offset: int, status: InvitationStatus | None
    ) -> tuple[list[Invitation], int]:
        """List invitations addressed to one user with optional status filtering."""
        filters = [Invitation.target_user_id == target_user_id]
        if status is not None:
            filters.append(Invitation.status == status)
        total = self.db.scalar(select(func.count(Invitation.id)).where(*filters)) or 0
        items = list(
            self.db.scalars(
                select(Invitation)
                .where(*filters)
                .order_by(Invitation.created_at.desc(), Invitation.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total

    def list_for_organization(
        self, organization_id: uuid.UUID, limit: int, offset: int, status: InvitationStatus | None
    ) -> tuple[list[Invitation], int]:
        """List all invitations owned by one organization for administrators."""
        filters = [Invitation.organization_id == organization_id]
        if status is not None:
            filters.append(Invitation.status == status)
        total = self.db.scalar(select(func.count(Invitation.id)).where(*filters)) or 0
        items = list(
            self.db.scalars(
                select(Invitation)
                .where(*filters)
                .order_by(Invitation.created_at.desc(), Invitation.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return items, total
