# SPEC-317 — Public Legal Pages

Status: Implemented
Owner: Arquitecto de specs
Last updated: 2026-09-16

## Scope And Required Context

This spec governs:

- Public legal-information pages for production: terms and conditions, copyright notice, and cookie policy.
- Public landing/footer navigation to those pages.
- Frontend route coverage and documentation memory for the legal surfaces.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/101-auth-and-users.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/311-public-portfolio-home.md`

Memory updates:

- `docs/project-state.md` when current state, next work, known gaps, or validation baseline changes
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change

## Problem

Before the next production deployment, the public site should expose basic legal pages for users and reviewers. The app currently has a public portfolio home and changelog, but it does not provide terms and conditions, a copyright notice, or a cookie policy.

## Goals

- Add public routes for terms and conditions, copyright, and cookie policy.
- Link those routes from the public landing footer.
- Keep text conservative and reviewable rather than presenting it as legal advice.
- Reflect the current cookie reality: OpsDesk uses necessary httpOnly session cookies for authentication and does not currently use analytics or marketing cookies.
- Avoid adding a cookie-consent banner while only necessary technical/authentication cookies are used.

## Non-Goals

- Legal advice or jurisdiction-specific legal certification.
- Full privacy policy.
- Cookie consent management UI for analytics, marketing, or third-party tracking cookies.
- Terms acceptance workflow during registration.
- Billing, subscription, SLA, or commercial contract terms.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous visitor | Reads legal pages | No login required |
| Authenticated user | Reads legal pages | Same public routes |
| Site owner/operator | Updates text before production | Must replace placeholder legal identity/contact details before relying on text legally |

## Business Rules

- BR-1: Legal pages must be public and must not require an authenticated session.
- BR-2: Footer links must expose the legal pages from the public landing page.
- BR-3: Cookie policy must describe only actual cookies currently used by the app.
- BR-4: The app must not add a cookie-consent banner unless non-essential cookies are introduced.
- BR-5: Text must avoid claiming lawyer review or formal legal compliance approval.
- BR-6: Text must include a clear "last updated" date.
- BR-7: The production owner/contact details must be treated as a required pre-production review item if the current placeholder text is not sufficient.
- BR-8: Public legal pages should be static frontend routes so production can serve them without backend state.

## Data Model Impact

None.

## API Contract

No API changes.

## Frontend Impact

New public routes:

- `/terms`
- `/copyright`
- `/cookies`

Landing-page footer links:

- Terms
- Copyright
- Cookies

The pages should use the existing public-page visual language and should remain readable on mobile and desktop.

## Acceptance Criteria

- AC-1: Given an anonymous visitor opens `/terms`, then terms and conditions content is visible without an API call.
- AC-2: Given an anonymous visitor opens `/copyright`, then copyright ownership/reservation text is visible without an API call.
- AC-3: Given an anonymous visitor opens `/cookies`, then the policy lists the necessary authentication cookies currently used by OpsDesk and states that no analytics/marketing cookies are currently used.
- AC-4: Given the public landing page is open, then footer links to terms, copyright, and cookies are visible.
- AC-5: Given the current app uses only necessary auth cookies, then no cookie-consent banner is shown.
- AC-6: Given future non-essential cookies are added, then this spec is insufficient and a consent-management spec must be prepared before deployment.

## Harness Requirements

Required tests/checks:

- Frontend route tests for the three pages.
- Frontend route test for public footer links.
- Technical documentation check if public route architecture documentation changes.

Required commands:

```bash
cd frontend && npm run test -- AppRouter.test.tsx
make technical-docs-check
git diff --check
```

## Observability And Failure Cases

- Legal pages are static and have no runtime observability beyond normal frontend availability.
- If production adds analytics, marketing pixels, embedded third-party trackers, or non-essential cookies, the cookie page becomes stale and a cookie consent workflow is required.
- A full privacy policy remains a separate pre-production legal gap because the app processes user account data such as email and profile fields.
