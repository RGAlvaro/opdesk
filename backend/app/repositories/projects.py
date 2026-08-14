"""Data access operations for tenant-scoped projects."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project, ProjectMembership


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

    def add_membership(self, membership: ProjectMembership) -> ProjectMembership:
        """Stage and flush explicit project access for one organization member."""
        self.db.add(membership)
        self.db.flush()
        return membership

    def get_membership(self, project_id: uuid.UUID, user_id: uuid.UUID) -> ProjectMembership | None:
        """Return a user's explicit project membership when present."""
        return self.db.scalar(
            select(ProjectMembership).where(
                ProjectMembership.project_id == project_id,
                ProjectMembership.user_id == user_id,
            )
        )

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
        self,
        organization_id: uuid.UUID,
        limit: int,
        offset: int,
        *,
        actor_user_id: uuid.UUID | None = None,
        actor_role: MembershipRole | None = None,
    ) -> tuple[list[Project], int]:
        """List and count projects for one organization tenant."""
        filters = [Project.organization_id == organization_id]
        total_statement = select(func.count(Project.id)).where(*filters)
        list_statement = select(Project).where(*filters)
        if actor_role == MembershipRole.MEMBER and actor_user_id is not None:
            total_statement = total_statement.join(
                ProjectMembership, ProjectMembership.project_id == Project.id
            ).where(ProjectMembership.user_id == actor_user_id)
            list_statement = list_statement.join(
                ProjectMembership, ProjectMembership.project_id == Project.id
            ).where(ProjectMembership.user_id == actor_user_id)
        total = self.db.scalar(total_statement) or 0
        projects = list(
            self.db.scalars(
                list_statement.order_by(Project.created_at, Project.id).limit(limit).offset(offset)
            )
        )
        return projects, total

    def list_members(
        self, project_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[tuple[ProjectMembership, OrganizationMembership]], int]:
        """List explicit project members with their organization role."""
        project_filter = ProjectMembership.project_id == project_id
        total = self.db.scalar(select(func.count(ProjectMembership.id)).where(project_filter)) or 0
        rows = self.db.execute(
            select(ProjectMembership, OrganizationMembership)
            .join(
                OrganizationMembership,
                (OrganizationMembership.organization_id == ProjectMembership.organization_id)
                & (OrganizationMembership.user_id == ProjectMembership.user_id),
            )
            .where(project_filter)
            .order_by(ProjectMembership.created_at, ProjectMembership.id)
            .limit(limit)
            .offset(offset)
        ).all()
        return [(row[0], row[1]) for row in rows], total

    def list_member_user_ids(self, project_id: uuid.UUID) -> list[uuid.UUID]:
        """Return explicit project member user IDs for notification fan-out."""
        return list(
            self.db.scalars(
                select(ProjectMembership.user_id)
                .where(ProjectMembership.project_id == project_id)
                .order_by(ProjectMembership.created_at, ProjectMembership.id)
            )
        )

    def delete_membership(self, membership: ProjectMembership) -> None:
        """Remove only explicit project access."""
        self.db.delete(membership)

    def delete_memberships_for_user(self, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Remove all explicit project access for a user leaving an organization."""
        memberships = list(
            self.db.scalars(
                select(ProjectMembership).where(
                    ProjectMembership.organization_id == organization_id,
                    ProjectMembership.user_id == user_id,
                )
            )
        )
        for membership in memberships:
            self.db.delete(membership)
