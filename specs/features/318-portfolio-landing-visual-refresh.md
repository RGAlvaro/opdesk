# SPEC-318 — Portfolio Landing Visual Refresh

Status: Ready
Owner: Arquitecto de specs
Last updated: 2026-09-23

## Scope And Required Context

This spec governs the public portfolio home at `/`, which presents OpsDesk as the available app and the existing ERP project as source-available portfolio work. It supersedes `SPEC-311`'s visual layout and its former assumption that the ERP was a future product for small teams. Its truthful-content and no-fake-live-app rules remain in force.

Visual reference: [`../assets/spec-318-portfolio-landing-reference.png`](../assets/spec-318-portfolio-landing-reference.png). The reference is a design target for composition, hierarchy, spacing, color, and illustration style. Its generated copy, links, dates, and claims are not product requirements.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/000-product-vision.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/104-frontend-app-shell-and-auth-ui.md`
- `specs/features/307-release-automation-and-safe-updates.md`
- `specs/features/310-release-changelog.md`
- `specs/features/311-public-portfolio-home.md`
- `specs/features/313-cross-browser-accessibility-e2e.md`
- `specs/features/317-public-legal-pages.md`

Memory updates: record spec readiness, implementation, review, merge, and production release evidence in `docs/project-state.md` and `docs/implementation-log.md`; keep `specs/README.md` aligned. No new ADR is required for a visual change within the existing frontend and deployment architecture.

## Problem

The current portfolio home presents the right projects and links, but its generic hero and two-card layout do not express the selected design direction. The next production release should show the chosen composition consistently while preserving accurate project status and existing public routes.

## Goals

- Make the selected reference the layout target for the public portfolio home on desktop.
- Adapt the same section order and hierarchy to tablet and mobile without hiding required information.
- Present OpsDesk as the clear, available featured app and distinguish the ERP's current authentication and human-resources foundation from planned modules, with a public code repository but no published live demo.
- Remove the decorative `Ideas · tools · better days` text beside the `Selected work` heading.
- Keep the existing public and OpsDesk entry points discoverable and functional.
- Validate the rendered design before and after the production release.

## Non-Goals

- Redesigning authenticated OpsDesk screens, login, signup, or the application shell.
- Creating a separate OpsDesk marketing site, case-study route, CMS, contact form, blog, theme switcher, or ERP application.
- Publishing the generated full-page mockup as a raster replacement for semantic page content.
- Adding unverified metrics, customers, uptime claims, testimonials, or fictional projects.
- Changing backend APIs, data models, or deployment topology.

## Actors And Permissions

| Actor | Permission | Notes |
|---|---|---|
| Anonymous visitor | View and navigate the portfolio home | No session or API call required to render |
| Authenticated user | View the public home and enter OpsDesk | Existing auth routing remains authoritative |
| Recruiter/interviewer | Inspect available work, approach, and release history | Primary audience |
| Repository maintainer | Update static content and prepare a release | Existing review and release gates apply |

## Business And Design Rules

- BR-1: `/` remains the static public portfolio home. It must render without authentication or backend data.
- BR-2: At desktop widths, section order and relative prominence follow the reference: slim dark-navy header; spacious editorial `Selected work` hero; large pale-blue OpsDesk feature panel; four-part `Spec · Build · Validate · Release` process strip; smaller ERP project panel; public footer. The OpsDesk panel is the dominant content block. The hero has no decorative text block beside its main heading.
- BR-3: The OpsDesk panel places its project title, `Available` status, concise factual description, stack labels, and primary `Open OpsDesk` action together on the left or reading-start side. An abstract connected-work illustration occupies the other side. Illustration is decorative and must not resemble a purported product screenshot.
- BR-4: The visual language follows the reference: near-white page, navy text and header, cobalt primary actions, pale-blue feature surfaces, sparse orange accents, fine separators, generous spacing, and a contrasting display-serif headline with readable sans-serif body text. Exact pixels are not contractual; hierarchy and section arrangement are.
- BR-5: On tablet and mobile, the layout stacks in the same reading order, keeps the OpsDesk action visible with its description, keeps the four process steps readable, and avoids horizontal scrolling at 390 px, 768 px, and desktop 1440 px viewports.
- BR-6: OpsDesk remains `Available`; its primary action uses the existing `/login` entry flow and a visible secondary path to `/signup` remains available. Do not imply that `/app` is public.
- BR-7: The ERP panel describes only the current authentication foundation with hashed passwords and the human-resources management module as implemented. It may distinguish finance, inventory/stock management, sales and invoicing, CRM, and production as planned future modules, never as available features. Passwords use one-way hashing rather than reversible encryption, as evidenced by the [public authentication model](https://github.com/RGAlvaro/ERP-ASA-final-project/blob/develop/src/backend/models/auth/user.py). The panel does not describe the team's size, claim a published live demo, or claim unverified attendance, reporting, payroll, or customer outcomes. A `View repository` action links to the [public source](https://github.com/RGAlvaro/ERP-ASA-final-project), not an unavailable app.
- BR-8: Keep a visible `/changelog` link and the existing `/terms`, `/copyright`, and `/cookies` links. An in-page `Work` anchor may point to the featured project. Do not copy the mockup's `About`, `Notes`, `Contact`, or theme controls unless those destinations or functions are separately specified and implemented.
- BR-9: Copy and stack labels must describe the actual portfolio and implementation. Do not mention the ERP team's size or copy illustrative mockup claims or its incorrect `2024` copyright date. If a copyright year is shown, it must be current and consistent with the legal page.
- BR-10: Semantic headings, landmarks, link names, keyboard focus, color contrast, and reduced-motion behavior must remain accessible. Decorative graphics must not add redundant spoken content. The core content must remain legible without custom fonts or decorative assets.
- BR-11: Public legal and changelog routes may share the updated public visual tokens where useful, but their content, routing, and behavior remain governed by their existing specs; broad redesign of those pages is not required.

## Data Model Impact

None. No migration or environment-variable change is expected.

## API Contract

No backend API changes.

## Frontend Impact

- Primary implementation surface: `frontend/src/app/LandingPage.tsx` and its page-specific styles/assets. Shared styles may change only as needed without altering authenticated OpsDesk styling.
- Update the public-home assertions in `frontend/src/app/AppRouter.test.tsx` to cover the new semantic sections and retained links.
- Use CSS and/or a small project-local illustration asset for abstract decoration. Do not ship the reference image as the page itself.
- Preserve the existing static route and entry actions; avoid adding new navigation destinations from the mockup.

## Acceptance Criteria

- AC-1: Given a visitor opens `/` at a 1440 px desktop viewport, the page visibly follows the committed reference's section order and composition: dark header, oversized editorial hero without the side slogan, dominant OpsDesk feature, four-step process, smaller ERP panel, and footer.
- AC-2: Given a visitor opens `/` at 390 px and 768 px widths, all required sections remain in order, text and actions are readable, and the document has no horizontal overflow.
- AC-3: Given the page loads, OpsDesk is clearly marked `Available`, its primary action reaches `/login`, and a signup link reaches `/signup`.
- AC-4: Given the ERP panel renders, it identifies hashed-password authentication and the human-resources module as current, labels finance, inventory, sales and invoicing, CRM, and production as future plans, makes no team-size claim, identifies the code as available, and links only to the public repository rather than an unavailable live app.
- AC-5: Given a visitor navigates from the page, `/changelog`, `/terms`, `/copyright`, and `/cookies` remain reachable; existing `/login`, `/signup`, and protected `/app` behavior continues to work.
- AC-6: Given the page loads without a session or API response, its public content still renders. Decorative assets or font failure must not hide its headings, descriptions, statuses, or links.
- AC-7: Given a keyboard or screen-reader user visits the page, semantic section names, focus visibility, meaningful links, and decorative-image handling pass the existing public-home accessibility scan with no serious or critical WCAG 2 A/AA violations.
- AC-8: Given the implementation is reviewed, desktop and mobile browser captures are compared with the committed reference for hierarchy, major section proportions, palette, and spacing. Intentional deviations required for truthful copy, working links, accessibility, or responsive behavior are recorded in review notes.
- AC-9: Given the production release completes, the deployed public `/` is visually inspected at desktop and mobile widths and the same section order, OpsDesk action, ERP status, and public footer links are confirmed. The release record names the deployed revision, validation results, and any visual deviation.

## Harness Requirements

Required checks during implementation and review:

- Frontend route/component tests for public content, section order or landmarks, the absence of the side slogan, ERP current-versus-planned copy and repository destination, and all existing routes; retain the no-backend-call assertion.
- Browser checks at 390 px, 768 px, and 1440 px for overflow and functional navigation; capture desktop and mobile screenshots for human comparison with the reference. Screenshots are review artifacts, not committed runtime assets.
- Existing public-home accessibility scan and frontend cross-browser smoke from `SPEC-313`.
- A production build and the repository frontend validation baseline. Run the full pre-PR verification gate defined in the harness before approval; record any unavailable gate explicitly.

Required commands:

```bash
make test-frontend
make lint
make format-check
make typecheck
cd frontend && npm run build
make test-e2e
make memory-check SPEC=SPEC-318
git diff --check
```

Before a production deployment, use the existing `SPEC-307` workflow and `SPEC-310` release-note gate. Add a truthful `CHANGELOG.md` entry for the landing change, run `make changelog-check` and `make release-workflow-check`, and record the post-deploy visual inspection in project memory. Do not mark this spec deployed based only on an HTTP 200 smoke result.

## Observability And Failure Cases

- The page is static; no new server logs or telemetry are required.
- Broken entry/legal/changelog links, hidden or misleading project status, horizontal overflow, inaccessible contrast/focus, and a materially different production layout are release-blocking failures.
- If the visual comparison reveals a material mismatch, correct it before release or update this spec and reference through review; do not silently reinterpret the selected composition.

## Open Questions

None blocking. Final wording may be refined during implementation as long as it remains truthful and meets the section and navigation contract.

## Implementation Notes

- The reference file is retained as durable design evidence. Its ERP title/status, side slogan, 2024 footer date, and extra navigation controls are generated artifacts or superseded decisions and must not be copied.
- The process strip describes the repository's spec-driven workflow; keep those four labels and the specified order.
- Keep new visual styles scoped to the public portfolio surface so the authenticated OpsDesk design remains stable.
