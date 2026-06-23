"""Project business rules, tenant isolation, and RBAC policy."""

import logging
import uuid

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project
from app.models.user import User
from app.repositories.projects import ProjectRepository
from app.services.organizations import OrganizationService

logger = logging.getLogger(__name__)


def validate_project_name(name: str) -> str:
    """Normalize and validate a project name for persistence."""
    normalized = " ".join(name.strip().split())
    if not normalized or len(normalized) > 160:
        raise APIError(400, "invalid_project", "Name must be between 1 and 160 characters.")
    return normalized


class ProjectService:
    """Coordinate project persistence with organization role checks."""

    def __init__(self, db: Session) -> None:
        """Create project collaborators bound to the request transaction."""
        self.db = db
        self.projects = ProjectRepository(db)
        self.organizations = OrganizationService(db)

    def create_project(
        self, actor: User, organization_id: uuid.UUID, name: str, description: str | None
    ) -> Project:
        """Create a project when the actor can manage the organization."""
        _, membership = self.organizations.get_organization(actor, organization_id)
        self._require_role(membership, {MembershipRole.OWNER, MembershipRole.ADMIN})
        project = Project(
            organization_id=organization_id,
            name=validate_project_name(name),
            description=description,
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
    def _require_role(
        membership: OrganizationMembership, allowed_roles: set[MembershipRole]
    ) -> None:
        """Raise the stable authorization error when a member lacks a required role."""
        if membership.role not in allowed_roles:
            raise APIError(403, "insufficient_role", "Your organization role is insufficient.")
