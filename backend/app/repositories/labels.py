"""Data access operations for project-scoped task labels."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import TaskLabel, TaskLabelAssignment


class TaskLabelRepository:
    """Keep label queries scoped through project and organization identifiers."""

    def __init__(self, db: Session) -> None:
        """Store the active request transaction."""
        self.db = db

    def add(self, label: TaskLabel) -> TaskLabel:
        """Stage and flush a task label so generated fields are available."""
        self.db.add(label)
        self.db.flush()
        return label

    def add_assignment(self, assignment: TaskLabelAssignment) -> TaskLabelAssignment:
        """Stage and flush one task label assignment."""
        self.db.add(assignment)
        self.db.flush()
        return assignment

    def get_by_id(
        self, organization_id: uuid.UUID, project_id: uuid.UUID, label_id: uuid.UUID
    ) -> TaskLabel | None:
        """Return a label only inside the supplied organization and project."""
        return self.db.scalar(
            select(TaskLabel).where(
                TaskLabel.id == label_id,
                TaskLabel.organization_id == organization_id,
                TaskLabel.project_id == project_id,
            )
        )

    def get_by_project_name(self, project_id: uuid.UUID, normalized_name: str) -> TaskLabel | None:
        """Find an active project label by its case-insensitive public name."""
        return self.db.scalar(
            select(TaskLabel).where(
                TaskLabel.project_id == project_id,
                TaskLabel.archived_at.is_(None),
                func.lower(TaskLabel.name) == normalized_name.lower(),
            )
        )

    def list_by_project(
        self,
        organization_id: uuid.UUID,
        project_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
        include_archived: bool,
    ) -> tuple[list[TaskLabel], int]:
        """List and count labels for one project with optional archived rows."""
        filters = [
            TaskLabel.organization_id == organization_id,
            TaskLabel.project_id == project_id,
        ]
        if not include_archived:
            filters.append(TaskLabel.archived_at.is_(None))
        total = self.db.scalar(select(func.count(TaskLabel.id)).where(*filters)) or 0
        labels = list(
            self.db.scalars(
                select(TaskLabel)
                .where(*filters)
                .order_by(TaskLabel.archived_at.is_not(None), TaskLabel.name, TaskLabel.id)
                .limit(limit)
                .offset(offset)
            )
        )
        return labels, total

    def get_assignment(self, task_id: uuid.UUID, label_id: uuid.UUID) -> TaskLabelAssignment | None:
        """Return one task-label assignment when it already exists."""
        return self.db.scalar(
            select(TaskLabelAssignment).where(
                TaskLabelAssignment.task_id == task_id,
                TaskLabelAssignment.label_id == label_id,
            )
        )

    def delete_assignment(self, assignment: TaskLabelAssignment) -> None:
        """Delete one task-label assignment from the current transaction."""
        self.db.delete(assignment)
        self.db.flush()

    def list_for_task(self, task_id: uuid.UUID) -> list[TaskLabel]:
        """Return labels assigned to one task in stable display order."""
        return list(
            self.db.scalars(
                select(TaskLabel)
                .join(TaskLabelAssignment, TaskLabelAssignment.label_id == TaskLabel.id)
                .where(TaskLabelAssignment.task_id == task_id)
                .order_by(TaskLabel.archived_at.is_not(None), TaskLabel.name, TaskLabel.id)
            )
        )

    def list_for_tasks(self, task_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[TaskLabel]]:
        """Return assigned labels grouped by task for task list responses."""
        if not task_ids:
            return {}
        rows = self.db.execute(
            select(TaskLabelAssignment.task_id, TaskLabel)
            .join(TaskLabel, TaskLabel.id == TaskLabelAssignment.label_id)
            .where(TaskLabelAssignment.task_id.in_(task_ids))
            .order_by(
                TaskLabelAssignment.task_id,
                TaskLabel.archived_at.is_not(None),
                TaskLabel.name,
                TaskLabel.id,
            )
        ).all()
        grouped: dict[uuid.UUID, list[TaskLabel]] = {task_id: [] for task_id in task_ids}
        for task_id, label in rows:
            grouped.setdefault(task_id, []).append(label)
        return grouped
