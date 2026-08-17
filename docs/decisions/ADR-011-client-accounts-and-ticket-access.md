# ADR-011 — Client Accounts And Ticket Access

Status: Accepted
Date: 2026-08-17
Related specs:
- SPEC-305
- SPEC-304

## Context

OpsDesk needs external clients to create tickets and follow their progress without exposing the internal organization workspace. A lightweight contact model would be simpler, but it would not support authenticated ticket history, status tracking, or ticket feedback from the client.

## Decision

Use restricted OpsDesk client accounts for project ticket access. Client accounts authenticate through the normal browser session mechanism but are not organization members and do not receive internal app navigation, organization chat, project settings, or internal task access.

Owner/admin users can grant and revoke project client access. Clients can create tickets only for projects where they have active access, see only tickets they created, view ticket status, and participate in the ticket-specific comment thread.

Tickets remain task records with a distinct ticket type/source so internal project members can handle them through the existing work model. Ticket comments are separate ticket-scoped conversation records, not organization chat.

## Consequences

The implementation must add account-type or equivalent authorization checks throughout auth bootstrap, route guards, and service policy code.

Client identity becomes reusable for later customer-facing features, but every future feature must explicitly opt client accounts into access rather than treating authenticated users as organization members.

Ticket comments can evolve independently from organization chat. Clients stay out of `SPEC-304` chat, which keeps internal collaboration and client support surfaces separate.

## Alternatives Considered

- Lightweight project contacts without login: simpler, but it does not satisfy client ticket history, status tracking, and feedback requirements.
- Public signed ticket links: avoids client accounts, but weakens the product's account-based access model and complicates revocation/auditing.
- Making clients ordinary organization members with limited roles: rejected because it risks leaking internal organization surfaces and blurs tenant membership semantics.
