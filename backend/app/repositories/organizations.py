"""Data access operations for organizations and tenant memberships."""

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models.organization import Organization, OrganizationMembership
from app.models.user import User


class OrganizationRepository:
    """Keep organization and membership queries tenant-scoped by construction."""

    def __init__(self, db: Session) -> None:
        """Store the request transaction used for all repository operations."""
        self.db = db

    def get_by_slug(self, slug: str) -> Organization | None:
        """Find an organization by its globally unique display slug."""
        return self.db.scalar(select(Organization).where(Organization.slug == slug))

    def add_organization(self, organization: Organization) -> Organization:
        """Stage and flush an organization so generated values are available."""
        self.db.add(organization)
        self.db.flush()
        return organization

    def add_membership(self, membership: OrganizationMembership) -> OrganizationMembership:
        """Stage and flush a tenant membership in the current transaction."""
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_membership(
        self, organization_id: uuid.UUID, user_id: uuid.UUID, *, refresh: bool = False
    ) -> OrganizationMembership | None:
        """Return a user's membership only within the requested organization."""
        statement = select(OrganizationMembership).where(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.user_id == user_id,
        )
        if refresh:
            statement = statement.execution_options(populate_existing=True)
        return self.db.scalar(statement)

    def lock_organization(self, organization_id: uuid.UUID) -> Organization | None:
        """Serialize ownership transfer and deletion on the organization row."""
        return self.db.scalar(
            select(Organization)
            .where(Organization.id == organization_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def get_organization_for_member(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Organization, OrganizationMembership] | None:
        """Load an organization only when the supplied user belongs to it."""
        row = self.db.execute(
            select(Organization, OrganizationMembership)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.id,
            )
            .where(
                Organization.id == organization_id,
                OrganizationMembership.user_id == user_id,
            )
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def list_for_user(
        self, user_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[tuple[Organization, OrganizationMembership]], int]:
        """List and count only organizations where the user has membership."""
        membership_filter = OrganizationMembership.user_id == user_id
        total = (
            self.db.scalar(select(func.count(OrganizationMembership.id)).where(membership_filter))
            or 0
        )
        rows = self.db.execute(
            select(Organization, OrganizationMembership)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Organization.id,
            )
            .where(membership_filter)
            .order_by(Organization.created_at, Organization.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return [(row[0], row[1]) for row in rows], total

    def list_members(
        self, organization_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[tuple[OrganizationMembership, User]], int]:
        """List memberships and safe user sources for one organization."""
        organization_filter = OrganizationMembership.organization_id == organization_id
        total = (
            self.db.scalar(select(func.count(OrganizationMembership.id)).where(organization_filter))
            or 0
        )
        rows = self.db.execute(
            select(OrganizationMembership, User)
            .join(User, User.id == OrganizationMembership.user_id)
            .where(organization_filter)
            .order_by(OrganizationMembership.created_at, OrganizationMembership.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return [(row[0], row[1]) for row in rows], total

    def delete_membership(self, membership: OrganizationMembership) -> None:
        """Delete only the supplied association and leave its user account intact."""
        self.db.delete(membership)

    def delete_organization(self, organization: Organization) -> None:
        """Delete all memberships and their organization without deleting users."""
        self.db.execute(
            delete(OrganizationMembership).where(
                OrganizationMembership.organization_id == organization.id
            )
        )
        self.db.delete(organization)
