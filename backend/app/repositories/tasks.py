"""Data access operations for tenant-scoped tasks."""

import uuid
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.organization import OrganizationMembership
from app.models.project import (
    Task,
    TaskLabelAssignment,
    TaskPriority,
    TaskStatus,
    TaskType,
    TaskWatcher,
)


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

    def add_watcher(self, watcher: TaskWatcher) -> TaskWatcher:
        """Stage and flush one task watcher subscription."""
        self.db.add(watcher)
        self.db.flush()
        return watcher

    def get_by_id(self, organization_id: uuid.UUID, task_id: uuid.UUID) -> Task | None:
        """Return a task only inside the supplied organization."""
        return self.db.scalar(
            select(Task).where(
                Task.id == task_id,
                Task.organization_id == organization_id,
            )
        )

    def get_by_id_for_notification(self, task_id: uuid.UUID) -> Task | None:
        """Load a task for worker-side notification validation."""
        return self.db.get(Task, task_id)

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
        task_type: TaskType | None = None,
        watcher_id: uuid.UUID | None = None,
        external_reference: str | None = None,
        label_id: uuid.UUID | None = None,
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
        if task_type is not None:
            filters.append(Task.task_type == task_type)
        if external_reference is not None:
            filters.append(Task.external_reference == external_reference)

        total_statement = select(func.count(Task.id)).where(*filters)
        list_statement = select(Task).where(*filters)
        if watcher_id is not None:
            total_statement = total_statement.join(
                TaskWatcher, TaskWatcher.task_id == Task.id
            ).where(TaskWatcher.user_id == watcher_id)
            list_statement = list_statement.join(TaskWatcher, TaskWatcher.task_id == Task.id).where(
                TaskWatcher.user_id == watcher_id
            )
        if label_id is not None:
            total_statement = total_statement.join(
                TaskLabelAssignment, TaskLabelAssignment.task_id == Task.id
            ).where(TaskLabelAssignment.label_id == label_id)
            list_statement = list_statement.join(
                TaskLabelAssignment, TaskLabelAssignment.task_id == Task.id
            ).where(TaskLabelAssignment.label_id == label_id)
        total = self.db.scalar(total_statement) or 0
        tasks = list(
            self.db.scalars(
                list_statement.order_by(Task.created_at, Task.id).limit(limit).offset(offset)
            )
        )
        return tasks, total

    def list_watcher_user_ids(self, task_id: uuid.UUID) -> list[uuid.UUID]:
        """Return watcher user identifiers for one task in creation order."""
        return list(
            self.db.scalars(
                select(TaskWatcher.user_id)
                .where(TaskWatcher.task_id == task_id)
                .order_by(TaskWatcher.created_at, TaskWatcher.id)
            )
        )

    def replace_watchers(
        self, task: Task, watcher_ids: list[uuid.UUID], added_by_id: uuid.UUID
    ) -> None:
        """Replace task watcher rows with a validated set of users."""
        existing = list(self.db.scalars(select(TaskWatcher).where(TaskWatcher.task_id == task.id)))
        for watcher in existing:
            self.db.delete(watcher)
        for watcher_id in watcher_ids:
            self.add_watcher(
                TaskWatcher(
                    organization_id=task.organization_id,
                    project_id=task.project_id,
                    task_id=task.id,
                    user_id=watcher_id,
                    added_by_id=added_by_id,
                )
            )
