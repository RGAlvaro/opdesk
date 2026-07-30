# SPEC-311 — Public Portfolio Home

Status: Draft
Owner: Arquitecto de specs
Last updated: 2026-07-28

## Scope And Required Context

This spec governs:

- Replacing the current public `/` landing page with a static portfolio-style home.
- Linking to OpsDesk and future apps from the home page.
- Public navigation to changelog content from `SPEC-310`.
- Frontend routing, copy, layout, assets, and tests for the public unauthenticated home.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/harness/local-validation.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/301-deployment-and-ops.md`
- `specs/features/310-release-changelog.md`

Memory updates:

- `docs/project-state.md` when public presentation state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful spec-prep, implementation, review, validation, or merge events
- `specs/README.md` when status, dependencies, order, or primary surfaces change
- ADRs only if public site deployment topology changes

## Problem

The current public home is focused only on OpsDesk. The site should become a static portfolio entry point that introduces the developer, links to OpsDesk as the currently available app, and leaves room for future apps such as an easy-to-use ERP without implying that unfinished apps are already live.

## Goals

- Make `/` a static public home that links to OpsDesk and future apps.
- Present OpsDesk with a concise description and clear entry action.
- Show a future ERP app card as coming soon, with no fake app link.
- Include a short personal/developer description written from implementation-time answers.
- Link to the public changelog from `SPEC-310`.
- Preserve login/signup access for OpsDesk users.
- Keep the page static and simple, with no backend dependency.

## Non-Goals

- Building a marketing site with CMS editing.
- Creating the ERP app.
- Adding fake metrics, fake customer logos, or fake screenshots.
- Replacing the authenticated OpsDesk app shell.
- Adding analytics or contact forms.
- Requiring a separate repository or deployment target.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous visitor | View home, changelog, OpsDesk entry points, and coming-soon app cards | No authentication required |
| Authenticated user | May open home but should still be able to reach OpsDesk app | Existing auth behavior remains |
| Recruiter/interviewer | Inspect app links and project positioning | Primary public audience |
| Repository maintainer | Update static app cards and personal copy | No app role involved |

## Business Rules

- BR-1: `/` is the public portfolio home.
- BR-2: OpsDesk appears as the primary available app.
- BR-3: OpsDesk card links to the authenticated app entry or login/signup flow according to existing routing.
- BR-4: The future ERP card is marked `Coming soon` and must not link to a nonexistent production app.
- BR-5: The ERP description should position it as an easy-to-use ERP for small teams or businesses.
- BR-6: The page includes public access to `CHANGELOG.md` rendered through `/changelog` or an equivalent public route from `SPEC-310`.
- BR-7: Existing `/login`, `/signup`, `/app`, and authenticated route guard behavior from `SPEC-104` must continue to work.
- BR-8: The home page must not show unsupported OpsDesk features as currently available.
- BR-9: The page should be static and not require a backend API call to render initial content.

## Data Model Impact

No database changes are required.

Expected changed surfaces:

- frontend public route for `/`
- public navigation/header/footer components if present
- app-card data module or static content file
- frontend tests for public home links and coming-soon behavior

## API Contract

No backend API endpoints are added or changed.

## Frontend Impact

- Replace the existing OpsDesk-only landing page copy with a portfolio home.
- Keep visible actions for OpsDesk login/signup or app entry.
- Add an OpsDesk app card with status `Available`.
- Add an ERP app card with status `Coming soon`.
- Add a public changelog link once `SPEC-310` is implemented.
- The design must work on mobile and desktop without horizontal scrolling.
- The first viewport must communicate that the page is a portfolio/app hub, not only an OpsDesk login page.

## Acceptance Criteria

- AC-1: Given an anonymous visitor opens `/`, then they see a static portfolio home with a personal/developer description.
- AC-2: Given the home page renders, then OpsDesk is visible as the available app with a description and an action leading to the existing OpsDesk entry flow.
- AC-3: Given the home page renders, then the ERP card is visible as `Coming soon` and does not link to a nonexistent app.
- AC-4: Given a visitor wants release information, when they use the changelog link, then they can reach the public changelog from `SPEC-310`.
- AC-5: Given an authenticated user uses existing `/app`, `/login`, or `/signup` routes, then auth routing behavior remains consistent with `SPEC-104`.
- AC-6: Given the page is viewed on mobile and desktop, then app cards and actions remain readable and no text overflows its container.
- AC-7: Given unsupported future apps are displayed, then they are clearly marked as future work and not presented as live products.

## Harness Requirements

Required tests/checks:

- Frontend route test for `/` rendering portfolio copy, OpsDesk card, ERP coming-soon card, and changelog link.
- Frontend route test that ERP coming-soon card has no fake app navigation.
- Existing auth route tests from `SPEC-104` remain passing.

Required commands:

```bash
make test-frontend
make lint
make format-check
make typecheck
make smoke
make memory-check SPEC=SPEC-311
```

## Observability And Failure Cases

- No backend logs are expected because the home is static.
- Client-side development logs may include safe route names only.
- Broken links to unavailable future apps are blocking.
- The page must not depend on auth/session bootstrap to render public content.

## Open Questions

- [ ] What personal/developer description should appear on the home page? Ask during implementation for role, tone, target audience, and 2-3 strengths or project themes to highlight.
- [ ] Should the OpsDesk action point primarily to `/login`, `/signup`, or `/app` with auth-aware redirect behavior?

## Implementation Notes

- Keep app data in a small static structure so future apps can be added without changing layout code.
- Do not add fake screenshots or claims for the ERP before it exists.
- Coordinate with `SPEC-310` so the changelog link points to a real public route.
