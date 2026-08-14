"""Organization lifecycle, tenant isolation, and RBAC business rules."""

import logging
import re
import unicodedata
import uuid
from typing import Any

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.organization import MembershipRole, Organization, OrganizationMembership
from app.models.user import User
from app.repositories.organizations import OrganizationRepository
from app.repositories.projects import ProjectRepository
from app.repositories.users import UserRepository
from app.services.metadata import optional_email, optional_string, optional_url

logger = logging.getLogger(__name__)
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def normalize_organization_name(name: str) -> str:
    """Collapse name whitespace and enforce the documented length boundary."""
    normalized = " ".join(name.strip().split())
    if not normalized or len(normalized) > 120:
        raise APIError(400, "invalid_organization", "Name must be between 1 and 120 characters.")
    return normalized


def generate_slug(name: str) -> str:
    """Generate a lowercase ASCII URL slug from a validated organization name."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return validate_slug(slug)


def validate_slug(slug: str) -> str:
    """Accept only non-empty lowercase URL-safe slugs up to 120 characters."""
    if len(slug) > 120 or SLUG_PATTERN.fullmatch(slug) is None:
        raise APIError(
            400,
            "invalid_organization",
            "Slug must be lowercase, URL-safe, and between 1 and 120 characters.",
        )
    return slug


class OrganizationService:
    """Coordinate organization persistence with tenant and role policies."""

    def __init__(self, db: Session) -> None:
        """Create organization collaborators bound to the request transaction."""
        self.db = db
        self.organizations = OrganizationRepository(db)
        self.projects = ProjectRepository(db)
        self.users = UserRepository(db)

    def create_organization(
        self,
        actor: User,
        *,
        name: str,
        fields_set: set[str],
        metadata: dict[str, Any],
    ) -> tuple[Organization, OrganizationMembership]:
        """Create an organization and its owner membership atomically."""
        if "slug" in fields_set:
            raise APIError(400, "invalid_organization", "Organization slug is backend-generated.")
        normalized_name = normalize_organization_name(name)
        normalized_slug = self._generate_unique_slug(normalized_name)

        organization = Organization(name=normalized_name, slug=normalized_slug)
        self._apply_metadata(organization, metadata, fields_set)
        try:
            self.organizations.add_organization(organization)
            membership = self.organizations.add_membership(
                OrganizationMembership(
                    user_id=actor.id,
                    organization_id=organization.id,
                    role=MembershipRole.OWNER,
                )
            )
            self.db.commit()
            self.db.refresh(organization)
            self.db.refresh(membership)
        except IntegrityError as exc:
            self.db.rollback()
            raise APIError(
                400, "invalid_organization", "Organization could not be created."
            ) from exc
        return organization, membership

    def list_organizations(
        self, actor: User, limit: int, offset: int
    ) -> tuple[list[tuple[Organization, OrganizationMembership]], int]:
        """Return only organizations where the actor has a membership."""
        return self.organizations.list_for_user(actor.id, limit, offset)

    def get_organization(
        self, actor: User, organization_id: uuid.UUID
    ) -> tuple[Organization, OrganizationMembership]:
        """Return organization details or hide missing and cross-tenant resources."""
        result = self.organizations.get_organization_for_member(organization_id, actor.id)
        if result is None:
            raise APIError(404, "organization_not_found", "Organization was not found.")
        return result

    def update_organization(
        self,
        actor: User,
        organization_id: uuid.UUID,
        name: str | None,
        fields_set: set[str],
        metadata: dict[str, Any],
    ) -> tuple[Organization, OrganizationMembership]:
        """Apply valid owner-only organization name or slug changes."""
        organization, membership = self.get_organization(actor, organization_id)
        self._require_role(membership, {MembershipRole.OWNER})
        if "slug" in fields_set:
            raise APIError(400, "invalid_organization", "Organization slug is backend-generated.")
        if not fields_set:
            raise APIError(400, "invalid_organization", "At least one field must be updated.")

        if name is not None:
            organization.name = normalize_organization_name(name)
        if "name" in fields_set and name is None:
            raise APIError(400, "invalid_organization", "Name is required.")
        self._apply_metadata(organization, metadata, fields_set)

        try:
            self.db.add(organization)
            self.db.commit()
            self.db.refresh(organization)
        except IntegrityError as exc:
            self.db.rollback()
            raise APIError(
                409, "organization_slug_taken", "Organization slug is already in use."
            ) from exc
        if fields_set - {"name"}:
            logger.info(
                "organization metadata updated actor_id=%s organization_id=%s",
                actor.id,
                organization.id,
            )
        return organization, membership

    def _generate_unique_slug(self, name: str) -> str:
        """Generate a slug with numeric suffixes until it is globally available."""
        base_slug = generate_slug(name)
        candidate = base_slug
        suffix = 2
        while self.organizations.get_by_slug(candidate) is not None:
            suffix_text = f"-{suffix}"
            candidate = f"{base_slug[: 120 - len(suffix_text)]}{suffix_text}"
            suffix += 1
        return candidate

    @staticmethod
    def _apply_metadata(
        organization: Organization, metadata: dict[str, Any], fields_set: set[str]
    ) -> None:
        """Normalize optional organization metadata fields onto the model."""
        if "employee_count" in fields_set:
            employee_count = metadata["employee_count"]
            if employee_count is not None and int(employee_count) < 0:
                raise APIError(400, "invalid_organization", "Employee count must be non-negative.")
            organization.employee_count = employee_count
        text_fields = {
            "industry": 120,
            "phone": 40,
            "address_line1": 160,
            "address_line2": 160,
            "city": 120,
            "region": 120,
            "postal_code": 40,
            "country": 120,
            "tax_id": 80,
            "description": 2000,
        }
        for field, max_length in text_fields.items():
            if field in fields_set:
                setattr(
                    organization,
                    field,
                    optional_string(
                        metadata[field],
                        max_length=max_length,
                        code="invalid_organization",
                        field=field,
                    ),
                )
        if "website" in fields_set:
            organization.website = optional_url(
                metadata["website"], code="invalid_organization", field="website"
            )
        if "logo_url" in fields_set:
            organization.logo_url = optional_url(
                metadata["logo_url"], code="invalid_organization", field="logo_url"
            )
        if "contact_email" in fields_set:
            organization.contact_email = optional_email(
                metadata["contact_email"], code="invalid_organization", field="contact_email"
            )

    def list_members(
        self, actor: User, organization_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[tuple[OrganizationMembership, User]], int]:
        """List memberships for owners and admins without exposing cross-tenant data."""
        _, actor_membership = self.get_organization(actor, organization_id)
        self._require_role(actor_membership, {MembershipRole.OWNER, MembershipRole.ADMIN})
        return self.organizations.list_members(organization_id, limit, offset)

    def change_member_role(
        self,
        actor: User,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        role: MembershipRole,
    ) -> tuple[OrganizationMembership, User]:
        """Change a non-owner role without bypassing the ownership transfer flow."""
        _, actor_membership = self.get_organization(actor, organization_id)
        self._require_role(actor_membership, {MembershipRole.OWNER})
        target = self._get_target_membership(organization_id, user_id)
        if target.role == MembershipRole.OWNER or role == MembershipRole.OWNER:
            self._raise_ownership_transfer_required()

        previous_role = target.role
        target.role = role
        self.db.add(target)
        self.db.commit()
        self.db.refresh(target)
        if previous_role != role:
            logger.info(
                "organization membership role changed actor_id=%s organization_id=%s "
                "user_id=%s old_role=%s new_role=%s",
                actor.id,
                organization_id,
                user_id,
                previous_role.value,
                role.value,
            )
        user = self.users.get_by_id(target.user_id)
        if user is None:
            raise RuntimeError("Membership user disappeared during role update.")
        return target, user

    def remove_member(self, actor: User, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Remove a membership without deleting the associated user account."""
        _, actor_membership = self.get_organization(actor, organization_id)
        self._require_role(actor_membership, {MembershipRole.OWNER})
        target = self._get_target_membership(organization_id, user_id)
        if target.role == MembershipRole.OWNER:
            self._raise_ownership_transfer_required()

        self.projects.delete_memberships_for_user(organization_id, user_id)
        self.organizations.delete_membership(target)
        self.db.commit()

    def transfer_ownership(
        self, actor: User, organization_id: uuid.UUID, new_owner_user_id: uuid.UUID
    ) -> None:
        """Atomically transfer the single owner role to an existing member."""
        _, previous_owner = self._lock_and_revalidate_owner(actor, organization_id)
        target = self.organizations.get_membership(organization_id, new_owner_user_id, refresh=True)
        if target is None:
            raise APIError(404, "membership_not_found", "Membership was not found.")
        if target.role == MembershipRole.OWNER:
            raise APIError(
                409,
                "ownership_transfer_not_required",
                "Target user already owns the organization.",
            )

        try:
            previous_owner.role = MembershipRole.ADMIN
            self.db.add(previous_owner)
            self.db.flush()
            target.role = MembershipRole.OWNER
            self.db.add(target)
            self.db.commit()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        logger.info(
            "organization ownership transferred actor_id=%s organization_id=%s "
            "new_owner_user_id=%s",
            actor.id,
            organization_id,
            new_owner_user_id,
        )

    def delete_organization(self, actor: User, organization_id: uuid.UUID) -> None:
        """Permanently delete an organization and its memberships as its owner."""
        organization, _ = self._lock_and_revalidate_owner(actor, organization_id)
        self.organizations.delete_organization(organization)
        self.db.commit()
        logger.info(
            "organization deleted actor_id=%s organization_id=%s",
            actor.id,
            organization_id,
        )

    def _lock_and_revalidate_owner(
        self, actor: User, organization_id: uuid.UUID
    ) -> tuple[Organization, OrganizationMembership]:
        """Lock one organization and recheck that the actor still owns it."""
        _, initial_membership = self.get_organization(actor, organization_id)
        self._require_role(initial_membership, {MembershipRole.OWNER})
        organization = self.organizations.lock_organization(organization_id)
        if organization is None:
            raise APIError(404, "organization_not_found", "Organization was not found.")
        membership = self.organizations.get_membership(organization_id, actor.id, refresh=True)
        if membership is None:
            raise APIError(404, "organization_not_found", "Organization was not found.")
        self._require_role(membership, {MembershipRole.OWNER})
        return organization, membership

    def _get_target_membership(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMembership:
        """Load a target membership inside the actor's already-authorized tenant."""
        membership = self.organizations.get_membership(organization_id, user_id)
        if membership is None:
            raise APIError(404, "membership_not_found", "Membership was not found.")
        return membership

    @staticmethod
    def _require_role(
        membership: OrganizationMembership, allowed_roles: set[MembershipRole]
    ) -> None:
        """Raise the stable authorization error when a member lacks a required role."""
        if membership.role not in allowed_roles:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")

    @staticmethod
    def _raise_slug_conflict() -> None:
        """Raise the public conflict response for duplicate organization slugs."""
        raise APIError(409, "organization_slug_taken", "Organization slug is already in use.")

    @staticmethod
    def _raise_ownership_transfer_required() -> None:
        """Require the dedicated transfer flow for every owner role change."""
        raise APIError(
            409,
            "ownership_transfer_required",
            "Use ownership transfer to change the organization owner.",
        )
