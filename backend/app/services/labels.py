"""Task label business rules, tenant isolation, and assignment policy."""

import logging
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.organization import OrganizationMembership
from app.models.project import Task, TaskLabel, TaskLabelAssignment
from app.models.user import User
from app.repositories.labels import TaskLabelRepository
from app.services.metadata import optional_string
from app.services.tasks import TaskService

logger = logging.getLogger(__name__)

hex_color_pattern = re.compile(r"^#[0-9A-Fa-f]{6}$")


def validate_label_name(name: str | None) -> str:
    """Normalize and validate a project label name."""
    if name is None:
        raise APIError(400, "invalid_label", "Label name is required.")
    normalized = " ".join(name.strip().split())
    if not normalized or len(normalized) > 60:
        raise APIError(400, "invalid_label", "Label name must be between 1 and 60 characters.")
    return normalized


def validate_label_color(color: str | None) -> str:
    """Normalize and validate an explicit hex label color."""
    if color is None:
        raise APIError(400, "invalid_label", "Label color is required.")
    normalized = color.strip().upper()
    if not hex_color_pattern.fullmatch(normalized):
        raise APIError(400, "invalid_label", "Label color must use #RRGGBB format.")
    return normalized


class TaskLabelService:
    """Coordinate project label persistence with task update permissions."""

    def __init__(self, db: Session) -> None:
        """Create label collaborators bound to the request transaction."""
        self.db = db
        self.labels = TaskLabelRepository(db)
        self.tasks = TaskService(db)

    def list_labels(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        limit: int,
        offset: int,
        include_archived: bool,
    ) -> tuple[list[TaskLabel], int]:
        """List labels for a project visible to the actor."""
        project, _ = self.tasks._get_project_for_member(project_id, actor.id)
        return self.labels.list_by_project(
            project.organization_id,
            project.id,
            limit=limit,
            offset=offset,
            include_archived=include_archived,
        )

    def create_label(
        self,
        actor: User,
        project_id: uuid.UUID,
        *,
        name: str,
        color: str,
        description: str | None,
    ) -> TaskLabel:
        """Create an active label for a project visible to the actor."""
        project, _ = self.tasks._get_project_for_member(project_id, actor.id)
        normalized_name = validate_label_name(name)
        self._ensure_name_available(project.id, normalized_name)
        label = TaskLabel(
            organization_id=project.organization_id,
            project_id=project.id,
            name=normalized_name,
            color=validate_label_color(color),
            description=optional_string(
                description, max_length=500, code="invalid_label", field="description"
            ),
            created_by_id=actor.id,
        )
        try:
            self.labels.add(label)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise APIError(
                409, "label_name_taken", "An active label already uses that name."
            ) from exc
        self.db.refresh(label)
        logger.info(
            "task label created actor_id=%s organization_id=%s project_id=%s label_id=%s",
            actor.id,
            label.organization_id,
            label.project_id,
            label.id,
        )
        return label

    def update_label(
        self,
        actor: User,
        project_id: uuid.UUID,
        label_id: uuid.UUID,
        *,
        name: str | None,
        color: str | None,
        description: str | None,
        is_archived: bool | None,
        fields_set: set[str],
    ) -> TaskLabel:
        """Update label metadata or archive state for a project member."""
        project, _ = self.tasks._get_project_for_member(project_id, actor.id)
        label = self.labels.get_by_id(project.organization_id, project.id, label_id)
        if label is None:
            raise APIError(404, "label_not_found", "Label was not found.")
        if not fields_set:
            raise APIError(400, "invalid_label", "At least one field must be updated.")
        if "name" in fields_set:
            normalized_name = validate_label_name(name)
            if normalized_name.lower() != label.name.lower():
                self._ensure_name_available(project.id, normalized_name, ignored_label_id=label.id)
            label.name = normalized_name
        if "color" in fields_set:
            label.color = validate_label_color(color)
        if "description" in fields_set:
            label.description = optional_string(
                description, max_length=500, code="invalid_label", field="description"
            )
        if "is_archived" in fields_set:
            was_archived = label.archived_at is not None
            if is_archived and not was_archived:
                label.archived_at = datetime.now(UTC)
            elif is_archived is False and was_archived:
                self._ensure_name_available(project.id, label.name, ignored_label_id=label.id)
                label.archived_at = None
            if was_archived != (label.archived_at is not None):
                logger.info(
                    "task label archive state changed actor_id=%s organization_id=%s "
                    "project_id=%s label_id=%s is_archived=%s",
                    actor.id,
                    label.organization_id,
                    label.project_id,
                    label.id,
                    label.archived_at is not None,
                )
        try:
            self.db.add(label)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise APIError(
                409, "label_name_taken", "An active label already uses that name."
            ) from exc
        self.db.refresh(label)
        return label

    def apply_label(self, actor: User, task_id: uuid.UUID, label_id: uuid.UUID) -> Task:
        """Apply an active same-project label to a task the actor may update."""
        task, membership = self.tasks.get_task(actor, task_id)
        self.tasks._validate_update_permission(actor, membership, task, {"labels"})
        label = self.labels.get_by_id(task.organization_id, task.project_id, label_id)
        if label is None:
            hidden = self._label_exists_for_actor(actor, label_id)
            if hidden:
                raise APIError(
                    400,
                    "invalid_label_assignment",
                    "Label must belong to the task project.",
                )
            raise APIError(404, "label_not_found", "Label was not found.")
        if label.archived_at is not None:
            raise APIError(
                400,
                "invalid_label_assignment",
                "Archived labels cannot be applied to tasks.",
            )
        if self.labels.get_assignment(task.id, label.id) is not None:
            raise APIError(409, "label_already_applied", "Task already has that label.")
        self.labels.add_assignment(
            TaskLabelAssignment(
                organization_id=task.organization_id,
                project_id=task.project_id,
                task_id=task.id,
                label_id=label.id,
                applied_by_id=actor.id,
            )
        )
        self.db.commit()
        self.db.refresh(task)
        logger.info(
            "task label assigned actor_id=%s organization_id=%s project_id=%s "
            "task_id=%s label_id=%s",
            actor.id,
            task.organization_id,
            task.project_id,
            task.id,
            label.id,
        )
        return task

    def remove_label(self, actor: User, task_id: uuid.UUID, label_id: uuid.UUID) -> None:
        """Remove one label from a task the actor may update."""
        task, membership = self.tasks.get_task(actor, task_id)
        self.tasks._validate_update_permission(actor, membership, task, {"labels"})
        label = self.labels.get_by_id(task.organization_id, task.project_id, label_id)
        if label is None:
            raise APIError(404, "label_not_found", "Label was not found.")
        assignment = self.labels.get_assignment(task.id, label.id)
        if assignment is None:
            raise APIError(404, "label_not_found", "Label was not found.")
        self.labels.delete_assignment(assignment)
        self.db.commit()

    def list_task_labels(self, task_id: uuid.UUID) -> list[TaskLabel]:
        """Expose assigned labels for one task API response."""
        return self.labels.list_for_task(task_id)

    def list_labels_for_tasks(self, task_ids: list[uuid.UUID]) -> dict[uuid.UUID, list[TaskLabel]]:
        """Expose assigned labels for many task API responses."""
        return self.labels.list_for_tasks(task_ids)

    def _ensure_name_available(
        self,
        project_id: uuid.UUID,
        normalized_name: str,
        *,
        ignored_label_id: uuid.UUID | None = None,
    ) -> None:
        """Reject duplicate active label names inside one project."""
        existing = self.labels.get_by_project_name(project_id, normalized_name)
        if existing is not None and existing.id != ignored_label_id:
            raise APIError(409, "label_name_taken", "An active label already uses that name.")

    def _label_exists_for_actor(self, actor: User, label_id: uuid.UUID) -> bool:
        """Return whether the actor can see the label in any of their organizations."""
        row = self.db.execute(
            select(TaskLabel.id)
            .join(
                OrganizationMembership,
                OrganizationMembership.organization_id == TaskLabel.organization_id,
            )
            .where(TaskLabel.id == label_id, OrganizationMembership.user_id == actor.id)
        ).one_or_none()
        return row is not None
