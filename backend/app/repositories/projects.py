"""Data access operations for tenant-scoped projects."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import OrganizationMembership
from app.models.project import Project


class ProjectRepository:
    """Keep project queries scoped to the owning organization."""

    def __init__(self, db: Session) -> None:
        """Store the active request transaction."""
        self.db = db

    def add(self, project: Project) -> Project:
        """Stage and flush a project so generated fields are available."""
        self.db.add(project)
        self.db.flush()
        return project

    def get_by_id(self, organization_id: uuid.UUID, project_id: uuid.UUID) -> Project | None:
        """Return a project only inside the supplied organization."""
        return self.db.scalar(
            select(Project).where(
                Project.id == project_id,
                Project.organization_id == organization_id,
            )
        )

    def get_for_member(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership] | None:
        """Load one project only when the actor belongs to its organization."""
        row = self.db.execute(
            select(Project, OrganizationMembership)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Project.organization_id,
            )
            .where(Project.id == project_id, OrganizationMembership.user_id == user_id)
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def list_by_organization(
        self, organization_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[Project], int]:
        """List and count projects for one organization tenant."""
        organization_filter = Project.organization_id == organization_id
        total = self.db.scalar(select(func.count(Project.id)).where(organization_filter)) or 0
        projects = list(
            self.db.scalars(
                select(Project)
                .where(organization_filter)
                .order_by(Project.created_at, Project.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return projects, total
