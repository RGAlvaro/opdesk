"""Data access operations for tenant-scoped tasks."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import OrganizationMembership
from app.models.project import Task, TaskPriority, TaskStatus


class TaskRepository:
    """Keep task queries scoped through organization and project identifiers."""

    def __init__(self, db: Session) -> None:
        """Store the active request transaction."""
        self.db = db

    def add(self, task: Task) -> Task:
        """Stage and flush a task so generated fields are available."""
        self.db.add(task)
        self.db.flush()
        return task

    def get_by_id(self, organization_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        """Return a task only inside the supplied organization."""
        return self.db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.organization_id == organization_id,
            )
        )

    def get_for_member(
        self, task_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[Task, OrganizationMembership] | None:
        """Load one task only when the actor belongs to its organization."""
        row = self.db.execute(
            select(Task, OrganizationMembership)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == Task.organization_id,
            )
            .where(Task.id == task_id, OrganizationMembership.user_id == user_id)
        ).one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    def list_by_project(
        self,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
        status: TaskStatus | None = None,
        assignee_id: uuid.UUID | None = None,
        priority: TaskPriority | None = None,
        due_before: date | None = None,
        due_after: date | None = None,
    ) -> tuple[list[Task], int]:
        """List and count tasks for one project with optional filters."""
        filters = [
            Task.organization_id == organization_id,
            Task.project_id == project_id,
        ]
        if status is not None:
            filters.append(Task.status == status)
        if assignee_id is not None:
            filters.append(Task.assignee_id == assignee_id)
        if priority is not None:
            filters.append(Task.priority == priority)
        if due_before is not None:
            filters.append(Task.due_date <= due_before)
        if due_after is not None:
            filters.append(Task.due_date >= due_after)

        total = self.db.scalar(select(func.count(Task.id)).where(*filters)) or 0
        tasks = list(
            self.db.scalars(
                select(Task)
                .where(*filters)
                .order_by(Task.created_at, Task.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return tasks, total
