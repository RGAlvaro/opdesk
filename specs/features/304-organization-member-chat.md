# SPEC-304 — Organization Member Chat

Status: Draft
Owner: Arquitecto de specs
Last updated: 2026-07-15

## Scope And Required Context

This spec governs:

- Organization-scoped member chat.
- Slack-like channels and group conversations for organization and project contexts.
- Chat member list ordering that prioritizes users who share a project with the current user.
- Backend message persistence, APIs, permissions, and frontend chat UI.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/102-organizations-and-rbac.md`
- `specs/features/103-projects-and-tasks.md`
- `specs/features/303-member-invitations-and-project-access.md` if project-level membership becomes authoritative
- `specs/features/306-in-app-notifications.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs if real-time transport, retention, or notification policy becomes a durable cross-cutting decision

## Problem

OpsDesk lacks a way for organization members to discuss operational work inside the app. A chat surface would make the product feel more complete, but it must stay scoped to organization membership and avoid exposing users across tenants.

## Goals

- Provide an organization chat UI with a left-side list of all organization members.
- Order the member list so people who share at least one project with the current user appear first.
- Let organization members exchange messages in direct conversations, groups, organization channels, and project channels.
- Persist chat messages with tenant isolation.
- Create missed-message in-app notifications through `SPEC-306`.
- Keep the first implementation simple enough for portfolio review.

## Non-Goals

- End-to-end encryption.
- External guest chat before client access is specified in `SPEC-305`.
- File attachments, voice/video calls, read receipts, reactions, typing indicators, or message search.
- Full real-time infrastructure unless explicitly selected before implementation.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Organization owner/admin/member | See organization member chat list and send messages to allowed chat targets | Must be organization member |
| Non-member | No chat access | Receives tenant-safe `404` |
| Client user | No access unless a later spec explicitly adds client chat | Covered by `SPEC-305` questions |

## Business Rules

- BR-1: Chat member lists include only users who are members of the current organization.
- BR-2: Members who share at least one non-archived project with the current user appear before other organization members.
- BR-3: Ordering within shared-project and non-shared groups must be deterministic.
- BR-4: Users cannot send direct or group messages to users outside the organization.
- BR-5: Project channel participants must be users who can access that project under the final project membership policy.
- BR-6: Message body must have a bounded length and be stored as user-generated content.
- BR-7: Deleted organization behavior must remove or make inaccessible its chat records consistently with organization deletion.
- BR-8: Conversation types are `direct`, `group`, `organization_channel`, and `project_channel`.
- BR-9: Missed messages create in-app notifications for recipients who are disconnected or not viewing the conversation.

## Data Model Impact

Expected new tables:

- `chat_conversations`
- `chat_conversation_participants`
- `chat_messages`

Candidate fields include organization ID, participant IDs, sender ID, message body, created timestamp, and updated timestamp where needed.

Migration required if implemented.

## API Contract

Exact endpoints remain Draft. Candidate endpoints:

- `GET /api/v1/organizations/{organization_id}/chat/members`
- `GET /api/v1/organizations/{organization_id}/chat/conversations`
- `POST /api/v1/organizations/{organization_id}/chat/groups`
- `POST /api/v1/projects/{project_id}/chat/channel`
- `GET /api/v1/chat/conversations/{conversation_id}/messages`
- `POST /api/v1/chat/conversations/{conversation_id}/messages`
- `POST /api/v1/organizations/{organization_id}/chat/conversations`

Polling is acceptable for the first implementation unless an ADR selects WebSockets or server-sent events.

## Frontend Impact

- Add a chat route under authenticated organization context.
- Support organization channel, project channel, group, and direct-message conversation types.
- Left panel lists organization members, prioritizing shared-project members.
- Main panel shows the selected conversation and message composer.
- Loading, empty, error, and permission states must be explicit.
- Chat UI must not crowd or destabilize the existing app shell navigation.

## Acceptance Criteria

- AC-1: Given an organization member opens chat, then the left list shows only members of that organization.
- AC-2: Given some members share a project with the current user, then those members appear before other organization members.
- AC-3: Given a user sends a valid message to an allowed target, then the message is persisted and appears in the conversation.
- AC-4: Given a user attempts to message a non-member, then the API rejects the request without leaking tenant data.
- AC-5: Given no conversation is selected, then the UI shows a safe empty state.
- AC-6: Given a user creates a group with valid organization members, then the group appears in the chat conversation list for its participants.
- AC-7: Given a project channel exists, then only users allowed for that project can participate.
- AC-8: Given a user receives a message while disconnected or away from the conversation, then `SPEC-306` creates an in-app notification.

## Harness Requirements

Required tests/checks:

- Backend API tests for member-list ordering, tenant isolation, send/read permissions, and validation errors.
- Frontend tests for member list ordering, empty/error states, and message send success/failure.
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

- [x] Chat should support a Slack-like combination of direct messages, groups, organization channels, and project channels.
- [ ] Should clients from `SPEC-305` appear in chat?
- [ ] Is polling acceptable for the portfolio MVP, or should this introduce WebSockets/SSE?
- [ ] What retention/deletion policy should apply to chat messages?
