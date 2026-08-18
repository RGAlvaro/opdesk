"""Business rules for internal organization chat and WebSocket fan-out."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.api.errors import APIError
from app.models.chat import (
    ChatConversation,
    ChatConversationParticipant,
    ChatConversationType,
    ChatMessage,
)
from app.models.organization import MembershipRole, OrganizationMembership
from app.models.project import Project
from app.models.user import User, UserAccountType
from app.repositories.chat import ChatRepository
from app.services.notifications import NotificationService


def validate_chat_body(body: str) -> str:
    """Normalize and validate user-generated chat message text."""
    normalized = body.strip()
    if not normalized or len(normalized) > 4000:
        raise APIError(400, "invalid_message", "Message must be between 1 and 4000 characters.")
    return normalized


def direct_key(first_user_id: uuid.UUID, second_user_id: uuid.UUID) -> str:
    """Build a stable direct-conversation key from two participant IDs."""
    ordered = sorted([str(first_user_id), str(second_user_id)])
    return ":".join(ordered)


class ChatService:
    """Coordinate chat persistence, tenant checks, unread state, and notifications."""

    def __init__(self, db: Session) -> None:
        """Create collaborators bound to the active database session."""
        self.db = db
        self.chat = ChatRepository(db)

    def list_members(
        self, actor: User, organization_id: uuid.UUID
    ) -> list[tuple[OrganizationMembership, User, bool]]:
        """List internal organization members with shared-project ordering."""
        self._require_internal(actor)
        membership = self.chat.get_organization_membership(organization_id, actor.id)
        if membership is None:
            raise APIError(404, "organization_not_found", "Organization was not found.")
        return self.chat.list_internal_members(organization_id, actor.id)

    def list_conversations(
        self, actor: User, organization_id: uuid.UUID
    ) -> list[tuple[ChatConversation, ChatConversationParticipant, ChatMessage | None, int]]:
        """List current-user conversations inside an organization."""
        self._require_internal(actor)
        membership = self.chat.get_organization_membership(organization_id, actor.id)
        if membership is None:
            raise APIError(404, "organization_not_found", "Organization was not found.")
        self._ensure_organization_channel(actor, organization_id)
        return self.chat.list_conversations_for_user(organization_id, actor.id)

    def create_direct_conversation(
        self, actor: User, organization_id: uuid.UUID, target_user_id: uuid.UUID
    ) -> ChatConversation:
        """Create or return a direct conversation for two internal organization members."""
        self._require_internal(actor)
        actor_membership = self.chat.get_organization_membership(organization_id, actor.id)
        target_membership = self.chat.get_organization_membership(organization_id, target_user_id)
        if actor_membership is None:
            raise APIError(404, "organization_not_found", "Organization was not found.")
        if target_membership is None or target_user_id == actor.id:
            raise APIError(404, "conversation_not_found", "Conversation was not found.")
        key = direct_key(actor.id, target_user_id)
        conversation = self.chat.get_direct_conversation(organization_id, key)
        if conversation is None:
            conversation = self.chat.add_conversation(
                ChatConversation(
                    organization_id=organization_id,
                    conversation_type=ChatConversationType.DIRECT,
                    direct_key=key,
                    created_by_id=actor.id,
                )
            )
            self._ensure_participant(conversation, actor.id)
            self._ensure_participant(conversation, target_user_id)
            self.db.commit()
            self.db.refresh(conversation)
        else:
            self._ensure_participant(conversation, actor.id)
            self._ensure_participant(conversation, target_user_id)
            self.db.commit()
        return conversation

    def get_project_channel(self, actor: User, project_id: uuid.UUID) -> ChatConversation:
        """Create or return the project channel when the actor can access that project."""
        project, membership = self._get_project_for_internal_member(actor, project_id)
        conversation = self.chat.get_project_channel(project.id)
        if conversation is None:
            conversation = self.chat.add_conversation(
                ChatConversation(
                    organization_id=project.organization_id,
                    project_id=project.id,
                    conversation_type=ChatConversationType.PROJECT_CHANNEL,
                    created_by_id=actor.id,
                )
            )
        for user_id in self._project_participant_ids(project.id, membership.role, actor.id):
            self._ensure_participant(conversation, user_id)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def list_messages(
        self, actor: User, conversation_id: uuid.UUID, limit: int, offset: int
    ) -> tuple[list[ChatMessage], int]:
        """Return visible message history for a conversation participant."""
        conversation, participant = self._get_current_participant(actor, conversation_id)
        self._revalidate_conversation_access(actor, conversation)
        return self.chat.list_messages(conversation.id, limit, offset, participant.cleared_at)

    def send_message(self, actor: User, conversation_id: uuid.UUID, body: str) -> ChatMessage:
        """Persist one message, mark the sender read, and create aggregate unread notifications."""
        conversation, _ = self._get_current_participant(actor, conversation_id)
        self._revalidate_conversation_access(actor, conversation)
        message = self.chat.add_message(
            ChatMessage(
                conversation_id=conversation.id,
                organization_id=conversation.organization_id,
                sender_id=actor.id,
                body=validate_chat_body(body),
            )
        )
        conversation.updated_at = datetime.now(UTC)
        self.db.add(conversation)
        self.chat.mark_read(conversation, actor.id, message.created_at)
        recipient_ids = set(self.chat.list_participant_user_ids(conversation.id))
        recipient_ids.discard(actor.id)
        NotificationService(self.db).notify_chat_unread(
            actor.id, conversation.id, conversation.organization_id, recipient_ids
        )
        self.db.commit()
        self.db.refresh(message)
        return message

    def mark_read(self, actor: User, conversation_id: uuid.UUID) -> ChatConversation:
        """Mark one conversation read for the current participant."""
        conversation, _ = self._get_current_participant(actor, conversation_id)
        self._revalidate_conversation_access(actor, conversation)
        self.chat.mark_read(conversation, actor.id, datetime.now(UTC))
        self.db.commit()
        return conversation

    def clear_conversation(self, actor: User, conversation_id: uuid.UUID) -> ChatConversation:
        """Hide existing messages from one participant without deleting them for others."""
        conversation, participant = self._get_current_participant(actor, conversation_id)
        self._revalidate_conversation_access(actor, conversation)
        now = datetime.now(UTC)
        participant.cleared_at = now
        self.db.add(participant)
        self.chat.mark_read(conversation, actor.id, now)
        self.db.commit()
        return conversation

    def _ensure_organization_channel(
        self, actor: User, organization_id: uuid.UUID
    ) -> ChatConversation:
        """Create the organization-wide channel and sync current internal members."""
        conversation = self.chat.get_organization_channel(organization_id)
        if conversation is None:
            conversation = self.chat.add_conversation(
                ChatConversation(
                    organization_id=organization_id,
                    conversation_type=ChatConversationType.ORGANIZATION_CHANNEL,
                    created_by_id=actor.id,
                )
            )
        for user_id in self.chat.list_organization_participant_ids(organization_id):
            self._ensure_participant(conversation, user_id)
        self.db.flush()
        return conversation

    def _ensure_participant(
        self, conversation: ChatConversation, user_id: uuid.UUID
    ) -> ChatConversationParticipant:
        """Create a participant row if it is missing."""
        participant = self.chat.get_participant(conversation.id, user_id)
        if participant is not None:
            return participant
        return self.chat.add_participant(
            ChatConversationParticipant(
                conversation_id=conversation.id,
                organization_id=conversation.organization_id,
                user_id=user_id,
            )
        )

    def _get_current_participant(
        self, actor: User, conversation_id: uuid.UUID
    ) -> tuple[ChatConversation, ChatConversationParticipant]:
        """Load a conversation for an authenticated internal participant."""
        self._require_internal(actor)
        result = self.chat.get_conversation_for_participant(conversation_id, actor.id)
        if result is None:
            raise APIError(404, "conversation_not_found", "Conversation was not found.")
        return result

    def _get_project_for_internal_member(
        self, actor: User, project_id: uuid.UUID
    ) -> tuple[Project, OrganizationMembership]:
        """Load a project and enforce SPEC-303 visibility for chat."""
        self._require_internal(actor)
        result = self.chat.get_project_for_member(project_id, actor.id)
        if result is None:
            raise APIError(404, "project_not_found", "Project was not found.")
        project, membership = result
        if membership.role not in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            if self.chat.get_project_membership(project.id, actor.id) is None:
                raise APIError(404, "project_not_found", "Project was not found.")
        return project, membership

    def _revalidate_conversation_access(self, actor: User, conversation: ChatConversation) -> None:
        """Recheck current membership/project access before history or sends."""
        membership = self.chat.get_organization_membership(conversation.organization_id, actor.id)
        if membership is None:
            raise APIError(404, "conversation_not_found", "Conversation was not found.")
        if conversation.conversation_type == ChatConversationType.PROJECT_CHANNEL:
            if conversation.project_id is None:
                raise APIError(404, "conversation_not_found", "Conversation was not found.")
            if membership.role in {MembershipRole.OWNER, MembershipRole.ADMIN}:
                return
            if self.chat.get_project_membership(conversation.project_id, actor.id) is None:
                raise APIError(404, "conversation_not_found", "Conversation was not found.")

    def _project_participant_ids(
        self, project_id: uuid.UUID, actor_role: MembershipRole, actor_id: uuid.UUID
    ) -> list[uuid.UUID]:
        """Build project-channel participants from explicit access and managing actor context."""
        participant_ids = set(self.chat.list_project_participant_ids(project_id))
        project_result = self.chat.get_project_for_member(project_id, actor_id)
        if project_result is not None:
            project, _ = project_result
            participant_ids.update(self.chat.list_owner_admin_user_ids(project.organization_id))
        if actor_role in {MembershipRole.OWNER, MembershipRole.ADMIN}:
            participant_ids.add(actor_id)
        return sorted(participant_ids)

    @staticmethod
    def _require_internal(actor: User) -> None:
        """Reject restricted client accounts from organization chat."""
        if actor.account_type == UserAccountType.CLIENT:
            raise APIError(403, "internal_member_required", "Internal membership is required.")
