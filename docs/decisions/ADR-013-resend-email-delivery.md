# ADR-013 — Resend Email Delivery

Status: Accepted
Date: 2026-09-07
Related specs:
- SPEC-314
- SPEC-316

## Context

OpsDesk already persists in-app notifications and has Redis/Celery worker infrastructure, but external delivery is still log-only. The project needs transactional email for invitations, client tickets, ticket comments, assignment requests, and missed chat/unread conversation summaries without adding disproportionate operational complexity for a portfolio-scale VPS deployment.

## Decision

Use Resend as the production transactional email provider for `SPEC-314`.

Email notifications are enabled by default for eligible notification types in the first implementation. User-configurable notification preferences remain future scope.

Local and CI environments continue to use fake/console delivery by default and must not require provider credentials or outbound provider access.

Delivery audit rows are retained indefinitely until a later explicit manual deletion or retention feature removes them.

## Consequences

The implementation can focus on one production adapter instead of a generic provider matrix. Resend keeps setup smaller than AWS SES while still representing realistic production email delivery.

The app must document Resend environment variables, sender/domain prerequisites, and safe local fallback behavior. Tests must mock the Resend adapter and must not send real emails.

Default-on email is simpler for the first slice, but user preferences will need a later spec if the product grows beyond demo/portfolio usage.

## Alternatives Considered

- SMTP: portable, but provider behavior varies and template/API observability is weaker.
- Postmark: strong transactional email product, but less attractive for this portfolio slice because the free developer allowance is smaller.
- Amazon SES: inexpensive at scale, but AWS onboarding, sandbox/domain setup, and deliverability configuration add operational weight that is not needed for the first external-delivery slice.
