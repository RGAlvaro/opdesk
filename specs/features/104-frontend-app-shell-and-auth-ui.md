# SPEC-104 — Frontend App Shell and Auth UI

Status: Implemented  
Owner: Arquitecto de specs / Ingeniero de software  
Last updated: 2026-07-28

## Scope And Required Context

This spec governs:

- `frontend/`, React app shell, auth/profile UI, Vite dev proxy, frontend tests, frontend Make targets, frontend Docker Compose service, or auth UI documentation.

Required context:

- `AGENTS.md`
- `docs/project-state.md`
- `specs/README.md`
- `specs/001-api-conventions.md`
- `specs/harness/local-validation.md`
- `specs/features/101-auth-and-users.md`

Memory updates:

- `docs/project-state.md` if frontend auth shell state, validation baseline, next work, or known gaps change
- `docs/implementation-log.md` for meaningful implementation, review, or validation events
- `specs/README.md` if status, dependencies, order, or primary surfaces change
- ADRs if frontend package management, state architecture, routing, or deployment strategy changes

## Problem

OpsDesk has backend authentication and user profile APIs, but no frontend application for a recruiter or user to sign up, log in, maintain a session, log out, or manage their own profile.

The frontend must also establish the app shell that later specs can extend with organizations, projects, and tasks without redesigning navigation or session handling.

## Goals

- Create the initial React TypeScript frontend application under `frontend/`.
- Provide a public landing page that lets users understand OpsDesk and start login/signup.
- Provide login and signup flows backed by `SPEC-101` APIs.
- Bootstrap authenticated sessions using httpOnly cookie auth and `GET /api/v1/users/me`.
- Provide an authenticated app shell with user navigation, logout, and a profile page.
- Allow authenticated users to view and update their `full_name`.
- Reserve clear navigation structure for future organizations, projects, and tasks without showing fake data or unsupported CRUD.
- Extend local validation and smoke checks so the frontend is part of the project harness.

## Non-Goals

- Implement organization CRUD UI from `SPEC-102`.
- Implement project/task UI from `SPEC-103`.
- Implement password reset, SSO, OAuth, two-factor auth, or invitation flows.
- Build production deployment routing. Production integration belongs to `SPEC-301`.
- Add analytics, billing, notifications, or background job UI.
- Replace `/` with a static portfolio/app hub. That later public home belongs to `SPEC-311`.

## Dependencies

- Requires `SPEC-010` backend scaffold and local Docker harness.
- Requires `SPEC-101` backend authentication and user APIs.
- Must follow `specs/001-api-conventions.md` for API paths, error handling, and auth cookies.
- Must use the frontend stack from `AGENTS.md`: React, TypeScript, Vite, React Router, TanStack Query, React Hook Form, Zod, Tailwind CSS, and shadcn/ui or similar component primitives.
- Initial package manager is `npm`, matching `specs/harness/local-validation.md`, unless an ADR updates the project package-manager decision.

## Actors And Permissions

| Actor | Permission | UI Behavior |
|---|---|---|
| Anonymous visitor | View landing page, log in, sign up | Cannot access authenticated app routes |
| Authenticated user | View app shell, profile, update own `full_name`, log out | Cannot access other users |
| Future organization member | Later access organizations/projects/tasks | Navigation may reserve space, but actions remain unavailable until backend specs are implemented |

## Product UX Contract

### Public Landing Page

Route: `/`

Purpose:

- Present OpsDesk as an operational work management app.
- Provide clear login and signup entry points.
- Avoid fake metrics, fake customer logos, fake screenshots, or unsupported feature claims.
- Mention future organization/project/task capabilities only as near-term product scope, not as currently usable features.

Required elements:

- Product name: `OpsDesk`.
- Short positioning copy focused on operational work management.
- Primary login action.
- Secondary signup action.
- If the user is already authenticated, redirect to `/app`.

Design rules:

- The landing page may be concise, but it must look like a real product entry point, not a raw form dump.
- On mobile, login/signup actions must remain visible without horizontal scrolling.
- Auth form errors must be visible near the form fields or submit action.

### Authentication Routes

Routes:

- `/login`
- `/signup`

Behavior:

- Login submits to `POST /api/v1/auth/login`.
- Signup submits to `POST /api/v1/auth/register`.
- After successful login or signup, the app must re-fetch `GET /api/v1/users/me` or otherwise update the session cache from a safe response.
- Authenticated users visiting `/login` or `/signup` redirect to `/app`.
- Failed auth requests render safe server errors from the API `error.message`.
- Token values must never be read from JSON, local storage, session storage, or JavaScript-managed cookies.

Validation:

- Login requires email and password.
- Signup requires email, password, and full name.
- Client validation may mirror backend password policy for UX, but backend remains authoritative.
- Signup password validation must include minimum 10 characters, at least one letter, and at least one number.

### Authenticated App Shell

Routes:

- `/app`
- `/app/profile`

Behavior:

- On app load, call `GET /api/v1/users/me`.
- If session bootstrap returns `401`, redirect to `/login`.
- While session bootstrap is pending, render a stable loading state.
- The shell must include user identity context: email and full name where available.
- Logout calls `POST /api/v1/auth/logout`, clears client query/session state, and redirects to `/`.
- Authenticated route protection must be client-side UX only; backend remains authoritative.

Future navigation:

- The shell must reserve navigation areas or route structure for future organizations, projects, and tasks.
- Future entries may be shown as disabled or unavailable states, but must not link to working CRUD pages until `SPEC-102` and `SPEC-103` frontend work exists.
- No placeholder data may be shown as if it came from the backend.

### Profile Page

Route: `/app/profile`

Behavior:

- Shows current user's safe profile fields from `GET /api/v1/users/me`.
- Allows editing `full_name` only.
- Saves changes with `PATCH /api/v1/users/me`.
- On success, updates displayed profile and session cache.
- On `400 invalid_profile`, shows the server error.
- On `401 not_authenticated`, redirects to `/login`.

Displayed fields:

- Email, read-only.
- Full name, editable.
- Account status, read-only if exposed by the API.
- Superuser flag may be hidden by default unless needed for local debugging; if shown, label it clearly as an internal/bootstrap flag.

## API Usage Contract

Frontend API calls must use relative paths by default so Vite dev proxy, Docker local setup, and future production reverse proxy can route consistently.

Required calls:

| UI Flow | Method | Path |
|---|---|---|
| Signup | `POST` | `/api/v1/auth/register` |
| Login | `POST` | `/api/v1/auth/login` |
| Session bootstrap | `GET` | `/api/v1/users/me` |
| Profile update | `PATCH` | `/api/v1/users/me` |
| Logout | `POST` | `/api/v1/auth/logout` |

HTTP requirements:

- Requests must include credentials so browser httpOnly cookies are sent.
- The app must not attempt to parse or store token values.
- API errors following `specs/001-api-conventions.md` must be converted into user-visible form or page errors.
- Unexpected errors must render a generic safe message.

## Frontend Structure

Implementation should group frontend feature code under:

```text
frontend/src/features/auth/
frontend/src/features/profile/
frontend/src/app/
frontend/src/shared/
```

Expected responsibilities:

- `features/auth`: login/signup forms, session query/mutations, auth route guards.
- `features/profile`: profile page and profile update form.
- `app`: router, shell layout, app providers.
- `shared`: API client, shared UI primitives, error helpers.

## Environment And Local Dev

`.env.example` must add any frontend variables required for local development.

Preferred local behavior:

- Vite dev server runs on `http://localhost:5173`.
- Vite proxies `/api` to the backend service in local development.
- Docker/local smoke checks include the frontend once it exists.

If Docker Compose is updated to run the frontend dev server, it must be documented in README and local validation specs.

## Accessibility And UX Requirements

- Forms must use semantic labels.
- Buttons must expose loading/disabled states during submission.
- Keyboard users must be able to complete login, signup, logout, and profile update.
- Error messages must be associated with the relevant form or field where practical.
- Layout must work at mobile and desktop widths.
- Do not use visible instructional copy to explain implementation details, cookie behavior, keyboard shortcuts, or internal architecture.

## Acceptance Criteria

- AC-1: Given an anonymous visitor, when they open `/`, then they see the OpsDesk landing page with login and signup actions.
- AC-2: Given an authenticated user, when they open `/`, `/login`, or `/signup`, then they are redirected to `/app`.
- AC-3: Given invalid login credentials, when login is submitted, then the form displays the safe API error and does not expose whether the email exists.
- AC-4: Given valid login credentials, when login succeeds, then the app reaches `/app` and displays the current user's safe profile context.
- AC-5: Given valid signup details, when signup succeeds, then the user reaches the authenticated app experience without exposing tokens.
- AC-6: Given weak signup password input, when signup is submitted, then the UI prevents submission or displays the backend `weak_password` error.
- AC-7: Given no valid session, when `/app` or `/app/profile` is opened, then the app redirects to `/login`.
- AC-8: Given an authenticated user, when `/app/profile` is opened, then the page displays email and full name from `/api/v1/users/me`.
- AC-9: Given an authenticated user, when they update `full_name` with valid input, then the UI persists the change through `PATCH /api/v1/users/me` and updates displayed state.
- AC-10: Given an invalid profile update, when the API returns `400 invalid_profile`, then the UI displays the safe server error.
- AC-11: Given an authenticated user, when they log out, then the UI calls `POST /api/v1/auth/logout`, clears client session state, and returns to `/`.
- AC-12: Given future navigation entries for organizations/projects/tasks, when those backend/frontend features are not implemented, then the UI does not show fake data or active unsupported CRUD flows.

## Harness Requirements

Frontend tests:

- Landing page renders login/signup actions.
- Login form validation and failed-login error rendering.
- Signup form validation, including weak password UX.
- Successful login updates session state and navigates to `/app`.
- Protected route redirects unauthenticated users.
- Session bootstrap success renders authenticated app shell.
- Logout clears client session state and redirects to `/`.
- Profile page loads current user.
- Profile update success and `invalid_profile` error handling.
- Future navigation entries are absent, disabled, or explicitly unavailable until backing specs are implemented.

Recommended test approach:

- Use Vitest and React Testing Library for component/route behavior.
- Mock API calls at the HTTP boundary, preferably with MSW or an equivalent test server.
- Add Playwright only for critical E2E flows after the frontend and local server harness are stable.

Required commands once frontend exists:

```bash
make test-frontend
make lint
make format-check
make typecheck
make smoke
```

Harness updates required by implementation:

- `make test`, `make lint`, `make format-check`, `make typecheck`, and `make verify` must include frontend checks once the frontend scaffold exists.
- `make smoke` must verify the frontend URL once a frontend dev server or container is part of local setup.
- `specs/harness/local-validation.md` must be updated if frontend commands differ from the current npm-based expectations.

## Observability And Failure Cases

- Do not log passwords, token values, cookies, or raw auth headers.
- Client-side errors may log safe route/action names in development only.
- Network failures should show safe retry-oriented messages.
- API `401` during session bootstrap or profile calls must clear client session state and route to login.
- API `500` or malformed responses must not expose stack traces.

## Implementation Notes

- Prefer a small API client wrapper that consistently sends credentials and parses API convention errors.
- Prefer TanStack Query for session, profile, and mutation cache management.
- Prefer React Hook Form and Zod for form state and client validation.
- Use React Router route loaders or route guards only as UX; authorization remains backend-enforced.
- Keep the shell extensible: organization switcher area, primary navigation, and page content slot should be easy to connect to `SPEC-102` and `SPEC-103` later.
- Avoid adding mock organization/project/task datasets in production code.
- If `SPEC-311` is implemented, it supersedes this spec's original OpsDesk-only public landing page while preserving login, signup, and authenticated app routing behavior.
