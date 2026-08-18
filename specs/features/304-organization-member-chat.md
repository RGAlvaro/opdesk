# SPEC-304 — Organization Member Chat

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-08-18

## Scope And Required Context

This spec governs:

- Organization-scoped internal member chat.
- Direct messages, organization channels, and project channels.
- Chat member list ordering that prioritizes users who share a project with the current user.
- Backend message persistence, WebSocket delivery, REST fallback/history APIs, permissions, and frontend chat UI.
- Aggregate unread conversation notifications through `SPEC-306`.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/303-member-invitations-and-project-access.md`
- `specs/features/305-project-clients-and-tickets.md`
- `specs/features/306-in-app-notifications.md`
- `docs/decisions/ADR-012-websocket-chat-transport.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if real-time transport, retention, or notification policy changes

## Problem

OpsDesk lacks a way for internal organization members to discuss operational work inside the app. A chat surface would make the product feel more complete, but it must stay scoped to organization membership and avoid exposing users across tenants or to client accounts.

## Goals

- Provide an internal organization chat UI with a left-side list of organization members.
- Order the member list so people who share at least one project with the current user appear first.
- Let organization members exchange messages through direct messages, organization channels, and project channels.
- Persist chat messages with tenant isolation.
- Deliver new chat messages over WebSockets for the portfolio MVP.
- Create aggregate unread in-app notifications through `SPEC-306` when conversations have unread activity.
- Keep clients out of chat; client-ticket discussion lives in `SPEC-305` ticket detail conversations.

## Non-Goals

- End-to-end encryption.
- Client chat or ticket-comment surfaces.
- Custom group conversations in V1.
- File attachments, voice/video calls, reactions, typing indicators, or message search.
- Full presence infrastructure beyond connection state needed for WebSocket delivery.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner/admin/member | See internal organization member chat list and send messages to allowed chat targets | Must be organization member |
| Project member | Participate in project channels for projects they can access | Project access follows `SPEC-303` |
| Client account | No organization chat access | Ticket discussion is handled by `SPEC-305` |
| Non-member | No chat access | Receives tenant-safe `404` |

## Business Rules

- BR-1: Chat member lists include only users who are members of the current organization.
- BR-2: Client accounts from `SPEC-305` do not appear in organization chat.
- BR-3: Members who share at least one non-archived project with the current user appear before other organization members.
- BR-4: Ordering within shared-project and non-shared groups must be deterministic.
- BR-5: Users cannot send direct messages to users outside the organization.
- BR-6: Project channel participants must be users who can access that project under `SPEC-303` project membership rules.
- BR-7: Message body must have a bounded length and be stored as user-generated content.
- BR-8: Deleted organization behavior must remove or make inaccessible its chat records consistently with organization deletion.
- BR-9: Conversation types in V1 are `direct`, `organization_channel`, and `project_channel`.
- BR-10: Chat messages are retained indefinitely while the organization/project exists.
- BR-11: A participant may clear or delete a conversation from their own chat view without deleting the underlying conversation for other participants.
- BR-12: Hard deletion of a message for all participants is not part of V1 unless required by organization deletion.
- BR-13: WebSocket delivery is required for new message fan-out; REST APIs still provide history, conversation creation, unread state, and reconnection recovery.
- BR-14: Unread notifications are conversation-level summaries, not one notification per individual message.

## Data Model Impact

Expected new tables:

- `chat_conversations`
- `chat_conversation_participants`
- `chat_messages`
- `chat_conversation_reads` or equivalent per-participant unread/last-read state

Candidate fields include organization ID, project ID for project channels, participant IDs, sender ID, message body, per-participant hidden/cleared timestamps, created timestamp, and updated timestamp where needed.

Migration required if implemented.

## API Contract

Exact schemas may be refined during implementation, but endpoint behavior must preserve the rules below.

REST endpoints:

- `GET /api/v1/organizations/{organization_id}/chat/members`
- `GET /api/v1/organizations/{organization_id}/chat/conversations`
- `POST /api/v1/organizations/{organization_id}/chat/direct-conversations`
- `GET /api/v1/projects/{project_id}/chat/channel`
- `GET /api/v1/chat/conversations/{conversation_id}/messages`
- `POST /api/v1/chat/conversations/{conversation_id}/messages`
- `POST /api/v1/chat/conversations/{conversation_id}/read`
- `POST /api/v1/chat/conversations/{conversation_id}/clear`

WebSocket endpoint:

- `WS /api/v1/chat/ws`

WebSocket requirements:

- Authenticate using the existing browser session cookie.
- Reject unauthenticated or client-account connections.
- Authorize each conversation subscription/send against organization and project access.
- Persist messages before fan-out.
- Support reconnect recovery through REST history endpoints.
- Do not require Redis pub/sub in V1 unless the implementation needs multi-process fan-out; a later ADR/spec update must define multi-instance behavior before horizontal scaling.

Errors must follow `specs/001-api-conventions.md`, including:

- `401 not_authenticated`
- `403 insufficient_role`
- `403 internal_member_required`
- `404 organization_not_found`
- `404 project_not_found`
- `404 conversation_not_found`
- `400 invalid_message`

## Frontend Impact

- Add a chat route under authenticated organization context.
- Support organization channel, project channel, and direct-message conversation types.
- Left panel lists organization members, prioritizing shared-project members.
- Main panel shows the selected conversation and message composer.
- WebSocket connection state, reconnecting state, loading, empty, error, and permission states must be explicit.
- Chat UI must not crowd or destabilize the existing app shell navigation.
- Client users must not see organization chat navigation.

## Acceptance Criteria

- AC-1: Given an organization member opens chat, then the left list shows only internal members of that organization.
- AC-2: Given some members share a project with the current user, then those members appear before other organization members.
- AC-3: Given a user sends a valid direct message to an allowed organization member, then the message is persisted, delivered over WebSocket when possible, and appears in conversation history.
- AC-4: Given a user attempts to message a non-member or client account, then the API rejects the request without leaking tenant data.
- AC-5: Given no conversation is selected, then the UI shows a safe empty state.
- AC-6: Given an organization channel exists, then organization members can view and send messages according to organization membership.
- AC-7: Given a project channel exists, then only users allowed for that project can participate.
- AC-8: Given a WebSocket connection drops, then the UI can recover missed messages through REST history after reconnect.
- AC-9: Given a participant clears a conversation, then it disappears or resets from that participant's view without deleting it for other participants.
- AC-10: Given a conversation has unread messages, then `SPEC-306` creates or updates an aggregate unread-conversation notification rather than one notification per message.

## Harness Requirements

Required tests/checks:

- Backend API tests for member-list ordering, tenant isolation, send/read permissions, project-channel permissions, unread state, conversation clearing, and validation errors.
- Backend WebSocket tests for authentication, client-account rejection, message persistence-before-fanout, authorized delivery, and reconnect/history recovery.
- Frontend tests for member list ordering, empty/error states, connection state, message send success/failure, unread state, and conversation clearing.
- Migration checks.

Required commands:

```bash
make test-backend
make test-frontend
make migrations-check
make lint
make format-check
make typecheck
make memory-check SPEC=SPEC-304
```

## Open Questions

- None. This spec is ready for implementation planning.
