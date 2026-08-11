"""Project business rules, tenant isolation, and RBAC policy."""

import logging
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project, ProjectStatus, ProjectVisibility
from app.models.user import User
from app.repositories.projects import ProjectRepository
from app.services.metadata import currency_code, non_negative_decimal
from app.services.organizations import OrganizationService

logger = logging.getLogger(__name__)


def validate_project_name(name: str) -> str:
    """Normalize and validate a project name for persistence."""
    normalized = " ".join(name.strip().split())
    if not normalized or len(normalized) > 160:
        raise APIError(400, "invalid_project", "Name must be between 1 and 160 characters.")
    return normalized


def parse_project_status(
    value: str | None, *, default: ProjectStatus | None = None
) -> ProjectStatus | None:
    """Convert public project status text to the persisted enum."""
    if value is None:
        return default
    try:
        return ProjectStatus(value)
    except ValueError as exc:
        raise APIError(400, "invalid_project", "Project status is invalid.") from exc


def parse_project_visibility(
    value: str | None, *, default: ProjectVisibility | None = None
) -> ProjectVisibility | None:
    """Convert public project visibility text to the persisted enum."""
    if value is None:
        return default
    try:
        return ProjectVisibility(value)
    except ValueError as exc:
        raise APIError(400, "invalid_project", "Project visibility is invalid.") from exc


class ProjectService:
    """Coordinate project persistence with organization role checks."""

    def __init__(self, db: Session) -> None:
        """Create project collaborators bound to the request transaction."""
        self.db = db
        self.projects = ProjectRepository(db)
        self.organizations = OrganizationService(db)

    def create_project(
        self,
        actor: User,
        organization_id: uuid.UUID,
        *,
        name: str,
        description: str | None,
        status: str | None,
        start_date: date | None,
        end_date: date | None,
        budget_amount: Decimal | None,
        budget_currency: str | None,
        visibility: str | None,
        project_owner_id: uuid.UUID | None,
    ) -> Project:
        """Create a project when the actor can manage the organization."""
        _, membership = self.organizations.get_organization(actor, organization_id)
        self._require_role(membership, {MembershipRole.OWNER, MembershipRole.ADMIN})
        self._validate_dates(start_date, end_date)
        normalized_budget = non_negative_decimal(
            budget_amount, code="invalid_project", field="budget_amount"
        )
        normalized_currency = currency_code(budget_currency, required=normalized_budget is not None)
        if project_owner_id is not None:
            self._require_organization_member(organization_id, project_owner_id)
        project = Project(
            organization_id=organization_id,
            name=validate_project_name(name),
            description=description,
            status=parse_project_status(status, default=ProjectStatus.ACTIVE),
            start_date=start_date,
            end_date=end_date,
            budget_amount=normalized_budget,
            budget_currency=normalized_currency,
            visibility=parse_project_visibility(visibility, default=ProjectVisibility.ORGANIZATION),
            project_owner_id=project_owner_id,
        )
        self.projects.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def list_projects(
        self, actor: User, organization_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Project], int]:
        """List projects for an organization member with standard pagination."""
        self.organizations.get_organization(actor, organization_id)
        return self.projects.list_by_organization(organization_id, limit, offset)

    def get_project(
        self, actor: User, project_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership]:
        """Return project details or hide missing and cross-tenant resources."""
        result = self.projects.get_for_member(project_id, actor.id)
        if result is None:
            raise APIError(404, "project_not_found", "Project was not found.")
        return result

    def update_project(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        name: str | None,
        description: str | None,
        is_archived: bool | None,
        status: str | None,
        start_date: date | None,
        end_date: date | None,
        budget_amount: Decimal | None,
        budget_currency: str | None,
        visibility: str | None,
        project_owner_id: uuid.UUID | None,
        fields_set: set[str],
    ) -> Project:
        """Apply owner/admin project changes and log archive transitions."""
        project, membership = self.get_project(actor, project_id)
        self._require_role(membership, {MembershipRole.OWNER, MembershipRole.ADMIN})
        if not fields_set:
            raise APIError(400, "invalid_project", "At least one field must be updated.")
        if "name" in fields_set:
            if name is None:
                raise APIError(400, "invalid_project", "Name is required.")
            project.name = validate_project_name(name)
        if "description" in fields_set:
            project.description = description
        if "status" in fields_set:
            parsed_status = parse_project_status(status)
            if parsed_status is None:
                raise APIError(400, "invalid_project", "Project status is required.")
            project.status = parsed_status
        next_start_date = start_date if "start_date" in fields_set else project.start_date
        next_end_date = end_date if "end_date" in fields_set else project.end_date
        if "start_date" in fields_set or "end_date" in fields_set:
            self._validate_dates(next_start_date, next_end_date)
            project.start_date = next_start_date
            project.end_date = next_end_date
        if "budget_amount" in fields_set:
            project.budget_amount = non_negative_decimal(
                budget_amount, code="invalid_project", field="budget_amount"
            )
        if "budget_currency" in fields_set or "budget_amount" in fields_set:
            project.budget_currency = currency_code(
                budget_currency if "budget_currency" in fields_set else project.budget_currency,
                required=project.budget_amount is not None,
            )
        if "visibility" in fields_set:
            parsed_visibility = parse_project_visibility(visibility)
            if parsed_visibility is None:
                raise APIError(400, "invalid_project", "Project visibility is required.")
            previous_visibility = project.visibility
            project.visibility = parsed_visibility
            if previous_visibility != parsed_visibility:
                logger.info(
                    "project visibility changed actor_id=%s organization_id=%s "
                    "project_id=%s old_visibility=%s new_visibility=%s",
                    actor.id,
                    project.organization_id,
                    project.id,
                    previous_visibility.value,
                    parsed_visibility.value,
                )
        if "project_owner_id" in fields_set:
            if project_owner_id is not None:
                self._require_organization_member(project.organization_id, project_owner_id)
            previous_owner_id = project.project_owner_id
            project.project_owner_id = project_owner_id
            if previous_owner_id != project_owner_id:
                logger.info(
                    "project owner changed actor_id=%s organization_id=%s project_id=%s "
                    "old_owner_id=%s new_owner_id=%s",
                    actor.id,
                    project.organization_id,
                    project.id,
                    previous_owner_id,
                    project_owner_id,
                )
        if "is_archived" in fields_set and is_archived is not None:
            previous_archive_state = project.is_archived
            project.is_archived = is_archived
            if previous_archive_state != project.is_archived:
                logger.info(
                    "project archive state changed actor_id=%s organization_id=%s "
                    "project_id=%s is_archived=%s",
                    actor.id,
                    project.organization_id,
                    project.id,
                    project.is_archived,
                )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    @staticmethod
    def _validate_dates(start_date: date | None, end_date: date | None) -> None:
        """Reject project end dates that precede the selected start date."""
        if start_date is not None and end_date is not None and end_date < start_date:
            raise APIError(400, "invalid_project", "End date cannot be before start date.")

    def _require_organization_member(
        self, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMembership:
        """Validate project owner membership inside the project organization."""
        membership = self.organizations.organizations.get_membership(organization_id, user_id)
        if membership is None:
            raise APIError(400, "invalid_project", "Project owner must be an organization member.")
        return membership

    @staticmethod
    def _require_role(
        membership: OrganizationMembership, allowed_roles: set[MembershipRole]
    ) -> None:
        """Raise the stable authorization error when a member lacks a required role."""
        if membership.role not in allowed_roles:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
