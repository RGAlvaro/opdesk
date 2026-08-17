# ADR-012 — WebSocket Chat Transport

Status: Accepted
Date: 2026-08-17
Related specs:
- SPEC-304
- SPEC-306

## Context

Organization chat should feel like a real collaboration surface in the portfolio app. Polling would be simpler, but it would make chat feel less representative of production-minded real-time engineering. The app already has persistent notifications, Redis/Celery for background work, and a production reverse proxy.

## Decision

Use WebSockets for `SPEC-304` new-message delivery. REST endpoints still own conversation history, unread state, read markers, conversation creation, and reconnect recovery.

WebSocket connections authenticate through the existing browser session cookie and must reject unauthenticated users and restricted client accounts. Message sends must persist before fan-out. V1 may use in-process connection management for a single app instance; Redis pub/sub or another cross-process fan-out layer requires a later spec/ADR update before horizontal scaling.

Unread notifications are aggregate conversation-level notifications through `SPEC-306`, not one notification per message.

## Consequences

The backend needs WebSocket test coverage in addition to ordinary API tests. The frontend needs explicit connected, reconnecting, failed, and recovered states.

Production Caddy and Compose must continue to support WebSocket upgrades for the backend API path. Any future multi-replica backend deployment must revisit fan-out before scaling chat horizontally.

Separating REST history from WebSocket delivery makes reconnect recovery testable and prevents WebSocket delivery from being the source of truth.

## Alternatives Considered

- Polling only: simpler, but less compelling for the collaboration feature and not the selected product direction.
- Server-sent events: good for one-way delivery, but chat send/ack flows still need normal API calls and provide less symmetry than WebSockets.
- Redis pub/sub in V1: useful for multi-process fan-out, but unnecessary until the production topology introduces multiple backend replicas.
