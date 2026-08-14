"""Invitation business rules for organization and project access grants."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.organization import (
    Invitation,
    InvitationScope,
    InvitationStatus,
    MembershipRole,
    Organization,
    OrganizationMembership,
)
from app.models.project import Project
from app.models.user import User
from app.repositories.invitations import InvitationRepository
from app.repositories.organizations import OrganizationRepository
from app.repositories.projects import ProjectRepository
from app.repositories.users import UserRepository
from app.services.organizations import OrganizationService
from app.services.projects import ProjectService
from app.services.users import normalize_email

INVITATION_TTL_DAYS = 7


def parse_invitation_status(value: str | None) -> InvitationStatus | None:
    """Convert optional public status text to the persisted enum."""
    if value is None:
        return None
    try:
        return InvitationStatus(value)
    except ValueError as exc:
        raise APIError(400, "invalid_invitation", "Invitation status is invalid.") from exc


class InvitationService:
    """Coordinate invitation state with tenant and project membership policies."""

    def __init__(self, db: Session) -> None:
        """Create invitation collaborators bound to the request transaction."""
        self.db = db
        self.invitations = InvitationRepository(db)
        self.organizations = OrganizationRepository(db)
        self.organization_service = OrganizationService(db)
        self.projects = ProjectRepository(db)
        self.project_service = ProjectService(db)
        self.users = UserRepository(db)

    def create_organization_invitation(
        self, actor: User, organization_id: uuid.UUID, *, email: str, role: MembershipRole
    ) -> Invitation:
        """Invite an existing user to join an organization after admin checks."""
        _, actor_membership = self.organization_service.get_organization(actor, organization_id)
        if actor_membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        if role == MembershipRole.OWNER:
            raise APIError(400, "invalid_invitation", "Owner role cannot be invited.")
        if role == MembershipRole.ADMIN and actor_membership.role != MembershipRole.OWNER:
            raise APIError(403, "insufficient_role", "Only owners can invite admins.")

        target_email = normalize_email(email)
        target = self.users.get_by_email(target_email)
        if target is None:
            raise APIError(404, "user_not_found", "User was not found.")
        if target.id == actor.id:
            raise APIError(400, "invalid_invitation", "You cannot invite yourself.")
        if self.organizations.get_membership(organization_id, target.id) is not None:
            raise APIError(409, "membership_exists", "User is already a member.")

        self._expire_pending_replacement(
            organization_id=organization_id,
            target_user_id=target.id,
            scope_type=InvitationScope.ORGANIZATION,
            project_id=None,
        )
        pending = self.invitations.get_pending_for_scope(
            organization_id=organization_id,
            target_user_id=target.id,
            scope_type=InvitationScope.ORGANIZATION,
            project_id=None,
        )
        if pending is not None:
            raise APIError(409, "invitation_exists", "Invitation already exists.")

        invitation = self.invitations.add(
            Invitation(
                organization_id=organization_id,
                target_email=target.email,
                target_user_id=target.id,
                role=role,
                scope_type=InvitationScope.ORGANIZATION,
                project_id=None,
                invited_by_id=actor.id,
                status=InvitationStatus.PENDING,
                expires_at=self._new_expiration(),
            )
        )
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def create_project_invitation(
        self, actor: User, project_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Invitation:
        """Invite an existing organization member to explicit project access."""
        project, actor_membership = self.project_service.get_project(actor, project_id)
        if actor_membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        if actor.id == user_id:
            raise APIError(400, "invalid_invitation", "You cannot invite yourself.")
        target_membership = self.organizations.get_membership(project.organization_id, user_id)
        if target_membership is None:
            raise APIError(404, "membership_not_found", "Membership was not found.")
        target = self.users.get_by_id(user_id)
        if target is None:
            raise APIError(404, "membership_not_found", "Membership was not found.")
        if self.projects.get_membership(project.id, user_id) is not None:
            raise APIError(
                409,
                "project_membership_exists",
                "User is already a project member.",
            )

        self._expire_pending_replacement(
            organization_id=project.organization_id,
            target_user_id=user_id,
            scope_type=InvitationScope.PROJECT,
            project_id=project.id,
        )
        pending = self.invitations.get_pending_for_scope(
            organization_id=project.organization_id,
            target_user_id=user_id,
            scope_type=InvitationScope.PROJECT,
            project_id=project.id,
        )
        if pending is not None:
            raise APIError(409, "invitation_exists", "Invitation already exists.")

        invitation = self.invitations.add(
            Invitation(
                organization_id=project.organization_id,
                target_email=target.email,
                target_user_id=target.id,
                role=None,
                scope_type=InvitationScope.PROJECT,
                project_id=project.id,
                invited_by_id=actor.id,
                status=InvitationStatus.PENDING,
                expires_at=self._new_expiration(),
            )
        )
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def list_my_invitations(
        self, actor: User, limit: int, offset: int, status: str | None
    ) -> tuple[list[Invitation], int]:
        """List invitations addressed to the current authenticated user."""
        return self.invitations.list_for_target(
            actor.id, limit, offset, parse_invitation_status(status)
        )

    def list_organization_invitations(
        self, actor: User, organization_id: uuid.UUID, limit: int, offset: int, status: str | None
    ) -> tuple[list[Invitation], int]:
        """List organization-owned invitations for owners and admins."""
        _, membership = self.organization_service.get_organization(actor, organization_id)
        if membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        return self.invitations.list_for_organization(
            organization_id, limit, offset, parse_invitation_status(status)
        )

    def accept_invitation(self, actor: User, invitation_id: uuid.UUID) -> Invitation:
        """Finalize a pending invitation and create the matching membership."""
        invitation = self._get_pending_target_invitation(actor, invitation_id)
        if self._is_expired(invitation):
            self._mark_expired(invitation)
            self.db.commit()
            raise APIError(400, "invalid_invitation", "Invitation is expired.")
        if invitation.scope_type == InvitationScope.ORGANIZATION:
            if self.organizations.get_membership(invitation.organization_id, actor.id) is not None:
                raise APIError(409, "membership_exists", "User is already a member.")
            if invitation.role is None or invitation.role == MembershipRole.OWNER:
                raise APIError(400, "invalid_invitation", "Invitation is no longer valid.")
            self.organizations.add_membership(self._organization_membership(invitation, actor.id))
        else:
            if invitation.project_id is None:
                raise APIError(400, "invalid_invitation", "Invitation is no longer valid.")
            if self.organizations.get_membership(invitation.organization_id, actor.id) is None:
                raise APIError(400, "invalid_invitation", "Invitation is no longer valid.")
            if self.projects.get_membership(invitation.project_id, actor.id) is not None:
                raise APIError(
                    409,
                    "membership_exists",
                    "User is already a project member.",
                )
            self.project_service.add_project_member(
                invitation.organization_id,
                invitation.project_id,
                actor.id,
                invitation.invited_by_id,
            )
        now = datetime.now(UTC)
        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = now
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def decline_invitation(self, actor: User, invitation_id: uuid.UUID) -> Invitation:
        """Decline a pending invitation without granting access."""
        invitation = self._get_pending_target_invitation(actor, invitation_id)
        if self._is_expired(invitation):
            self._mark_expired(invitation)
            self.db.commit()
            raise APIError(400, "invalid_invitation", "Invitation is expired.")
        invitation.status = InvitationStatus.DECLINED
        invitation.declined_at = datetime.now(UTC)
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def cancel_invitation(
        self, actor: User, organization_id: uuid.UUID, invitation_id: uuid.UUID
    ) -> None:
        """Cancel a pending organization-owned invitation."""
        _, membership = self.organization_service.get_organization(actor, organization_id)
        if membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
        invitation = self.invitations.get_by_id(invitation_id)
        if invitation is None or invitation.organization_id != organization_id:
            raise APIError(404, "invitation_not_found", "Invitation was not found.")
        if invitation.status != InvitationStatus.PENDING:
            raise APIError(409, "invitation_finalized", "Invitation is already finalized.")
        invitation.status = InvitationStatus.CANCELLED
        invitation.cancelled_at = datetime.now(UTC)
        self.db.add(invitation)
        self.db.commit()

    def enrich_invitation(
        self, invitation: Invitation
    ) -> tuple[Invitation, Organization | None, Project | None]:
        """Load safe display names for invitation responses."""
        organization = self.organizations.db.get(Organization, invitation.organization_id)
        project = None
        if invitation.project_id is not None:
            project = self.projects.db.get(Project, invitation.project_id)
        return invitation, organization, project

    def _get_pending_target_invitation(self, actor: User, invitation_id: uuid.UUID) -> Invitation:
        """Load a pending invitation addressed to the actor or raise 404/409."""
        invitation = self.invitations.get_for_target(invitation_id, actor.id)
        if invitation is None:
            raise APIError(404, "invitation_not_found", "Invitation was not found.")
        if invitation.status != InvitationStatus.PENDING:
            raise APIError(400, "invalid_invitation", "Invitation is no longer pending.")
        return invitation

    def _expire_pending_replacement(
        self,
        *,
        organization_id: uuid.UUID,
        target_user_id: uuid.UUID,
        scope_type: InvitationScope,
        project_id: uuid.UUID | None,
    ) -> None:
        """Mark an expired pending invitation before duplicate checks."""
        pending = self.invitations.get_pending_for_scope(
            organization_id=organization_id,
            target_user_id=target_user_id,
            scope_type=scope_type,
            project_id=project_id,
        )
        if pending is not None and self._is_expired(pending):
            self._mark_expired(pending)
            self.db.flush()

    @staticmethod
    def _organization_membership(
        invitation: Invitation, user_id: uuid.UUID
    ) -> OrganizationMembership:
        """Build the organization membership created by acceptance."""
        return OrganizationMembership(
            organization_id=invitation.organization_id,
            user_id=user_id,
            role=invitation.role,
        )

    @staticmethod
    def _new_expiration() -> datetime:
        """Return the standard pending invitation expiry timestamp."""
        return datetime.now(UTC) + timedelta(days=INVITATION_TTL_DAYS)

    @staticmethod
    def _is_expired(invitation: Invitation) -> bool:
        """Return whether a pending invitation is past its acceptance window."""
        expires_at = invitation.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        return expires_at <= datetime.now(UTC)

    @staticmethod
    def _mark_expired(invitation: Invitation) -> None:
        """Move a stale pending invitation to its terminal expired state."""
        invitation.status = InvitationStatus.EXPIRED
