# Implementation Log

This file is the durable timeline for OpsDesk spec work. Keep entries short, factual, and linked to specs, commits, validation, and review outcomes.

## How To Use

- Add one entry per meaningful spec-prep, implementation, review, or merge event.
- Newest entries go at the top of `Entries`.
- Reference spec IDs exactly, for example `SPEC-010`.
- Record commands that were run and their result. If a command was not run, record why.
- Record known gaps only when they matter after the current step.

## Entry Template

```text
### YYYY-MM-DD — SPEC-XXX — Short title

Role: Arquitecto de specs | Ingeniero de software | Review agent
Branch: branch-name
Commit/PR: commit sha or PR URL
Status: Planned | Ready | Implemented | Reviewed | Merged | Blocked

Summary:
- ...

Validation:
- command: PASS/FAIL/NOT RUN — notes

Review:
- decision: APPROVED/CHANGES_REQUESTED/BLOCKED_BY_SPEC_GAP/N/A

Known gaps:
- None, or list remaining work.
```

## Entries

### 2026-09-23 — SPEC-318 — Independent PR review approved

Role: Review agent
Branch: agent/spec-318-portfolio-landing
Commit/PR: PR #24 at reviewed head `a5bb425` (`https://github.com/RGAlvaro/opdesk/pull/24`)
Status: Reviewed

Summary:
- Compared AC-1 through AC-8 against the implementation, route and browser tests, desktop/mobile captures, factual ERP repository evidence, and the committed visual reference. The composition, responsive order, public navigation, accessibility coverage, and truthful current-versus-planned ERP copy meet the spec; no product changes are required.
- AC-9 remains a mandatory production-release checkpoint: visually inspect desktop/mobile deployment and record the deployed revision and any deviation.

Validation:
- command: `make memory-check SPEC=SPEC-318`: PASS — current memory shape checked by the reviewer.
- command: `make test-frontend`: PASS — 70 frontend tests checked by the reviewer.
- command: `make changelog-check`: PASS — release entry validated by the reviewer.
- command: `make release-workflow-check`: PASS — release workflow validated by the reviewer.
- command: `git diff --check`: PASS — no whitespace errors.
- command: GitHub Actions `Verify` run `35838529047`: PASS — `verify` and `e2e` on reviewed head `a5bb425`.

Review:
- decision: APPROVED — no product changes required; commit this review-memory checkpoint and recheck CI before merge.

Known gaps:
- Merge PR #24 after CI on the review-memory commit, run the changelog-gated production release, and complete AC-9 with desktop/mobile visual verification and merge/deploy memory.

### 2026-09-23 — SPEC-318 — Portfolio landing release candidate prepared

Role: Ingeniero de software
Branch: agent/spec-318-portfolio-landing
Commit/PR: implementation commit `0865173`; PR #24 (`https://github.com/RGAlvaro/opdesk/pull/24`)
Status: Implemented

Summary:
- Audited the local changes against `SPEC-318`: the landing, scoped CSS, reference asset, factual ERP copy/repository link, frontend assertions, responsive and accessibility browser coverage, and project memory are in scope. The authenticated OpsDesk interface and backend are unchanged.
- Added the user-facing `2026-09-23 - Portfolio Landing Release` entry to `CHANGELOG.md` for the required production release gate.
- Published the implementation branch and opened PR #24 after the full verification and release checks. No production change has occurred yet.

Validation:
- command: `make verify`: PASS — lint, format, types, 124 selected backend tests, 70 frontend tests, technical docs, and Alembic upgrade/check with no new operations.
- command: `cd frontend && npm run build`: PASS — production Vite build with the new changelog entry.
- command: `make release-workflow-check`: PASS — changelog and release workflow validation.
- command: `make prod-config`: PASS — production Compose configuration rendered with placeholder values.
- command: `make test-e2e`: PASS — 14 browser tests passed and 1 skipped; includes SPEC-318 responsive widths, public accessibility, Firefox/WebKit smoke, and critical authenticated flow.
- command: GitHub Actions `Verify` run `35838116771` on PR #24 at `8b12bd3`: PASS — `verify` in 1m52s and `e2e` in 2m47s.
- command: GitHub Actions `Verify` run `35838529047` on PR #24 at `a5bb425`: PASS — final published head passed `verify` in 1m35s and `e2e` in 2m54s.

Review:
- decision: N/A — PR review has not yet happened.

Known gaps:
- Obtain an independent PR review approval before merge; then deploy with the specified changelog entry and verify the production desktop/mobile rendering.

### 2026-09-23 — SPEC-318 — ERP current foundation and future modules clarified

Role: Ingeniero de software
Branch: main
Commit/PR: uncommitted local implementation; no PR
Status: Implemented

Summary:
- Revised `SPEC-318` and its index to remove team-size attribution from the ERP card and distinguish its present authentication foundation and HR management module from planned finance, inventory, sales/invoicing, CRM, and production modules.
- Checked the public ERP authentication model and service: passwords are hashed with Werkzeug and checked against the stored hash, so the landing says `hashed passwords` rather than implying reversible encryption. Preserved the public repository link and no-live-demo wording.
- Updated the public landing, component assertions, and responsive browser assertions. The authenticated OpsDesk interface, backend, and persistence remain unchanged.

Validation:
- command: `make test-frontend`: PASS — 70 frontend tests.
- command: `make lint`: PASS — backend Ruff and frontend ESLint.
- command: `make format-check`: PASS — backend Ruff format and frontend Prettier.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript.
- command: `cd frontend && npm run build`: PASS — production Vite build.
- command: `docker compose up -d --build frontend`: PASS — local frontend rebuilt and running.
- command: focused Docker Chromium responsive E2E: PASS — 3/3 checks at 390/768/1440 px; mobile screenshot reviewed.
- command: `make test-e2e`: PASS — 14 browser tests passed and 1 skipped, including accessibility and Firefox/WebKit smoke.
- command: `make memory-check SPEC=SPEC-318`: PASS — project memory shape is current.
- command: `git diff --check`: PASS — no whitespace errors.
- command: `curl -fsSI --max-time 5 http://localhost:5173/`: PASS — local landing responds with HTTP 200.

Review:
- decision: N/A — independent review has not been requested or completed.

Known gaps:
- Independent review, merge, changelog-backed production release, and post-deploy desktop/mobile verification remain.

### 2026-09-23 — SPEC-318 — ERP attribution and landing copy corrected

Role: Ingeniero de software
Branch: main
Commit/PR: uncommitted local implementation; no PR
Status: Implemented

Summary:
- Revised `SPEC-318` after checking the public ERP repository's HR models, routes, and frontend modules. The project is now described as collaboratively built in a small team, not aimed at small teams; the panel names evidenced employee, department, salary, and job-offer interface work without claiming unsupported features or a live deployment.
- Removed the decorative side slogan beside `Selected work`, added the ERP repository link and source-available status, updated its illustration and mobile spacing, and aligned frontend and browser assertions. OpsDesk's authenticated design is unchanged.
- Updated the spec index and current project state; the prior mockup's side slogan and ERP placeholder are explicitly superseded by the revised spec.

Validation:
- command: `make test-frontend`: PASS — 70 frontend tests.
- command: `make lint`: PASS — backend Ruff and frontend ESLint.
- command: `make format-check`: PASS — backend Ruff format and frontend Prettier.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript.
- command: `cd frontend && npm run build`: PASS — production Vite build.
- command: `make test-e2e`: PASS — 14 browser tests passed and 1 skipped, including 390/768/1440 px responsive checks, accessibility, and Firefox/WebKit smoke.
- command: `docker compose run --rm -e PLAYWRIGHT_OUTPUT_DIR=/work/test-results e2e sh -c 'npm ci --silent && npx playwright test e2e/portfolio-landing.spec.ts --project=chromium-desktop'`: PASS — final 3/3 responsive checks and mobile screenshot after art-spacing adjustment.
- command: `make memory-check SPEC=SPEC-318`: PASS — spec and implementation memory shape is current.
- command: `git diff --check`: PASS — no whitespace errors.
- command: `curl -I --max-time 5 http://localhost:5173/`: PASS — local app responds with HTTP 200.

Review:
- decision: N/A — independent review has not been requested or completed.

Known gaps:
- Independent review, merge, changelog-backed production release, and post-deploy desktop/mobile verification remain.

### 2026-09-23 — SPEC-318 — Public portfolio landing implemented locally

Role: Ingeniero de software
Branch: main
Commit/PR: uncommitted local implementation; no PR
Status: Implemented

Summary:
- Replaced the public `/` composition in `frontend/src/app/LandingPage.tsx` and added scoped `LandingPage.css`: dark header, editorial hero, dominant OpsDesk panel, four-step process, ERP coming-soon panel, and public footer following the versioned reference.
- Built the project illustrations in semantic frontend code and retained real `/login`, `/signup`, `/changelog`, `/terms`, `/copyright`, and `/cookies` destinations. No authenticated OpsDesk styling, backend API, data model, or migration changed.
- Updated route assertions and public-route E2E expectations; added 390/768/1440 px browser checks and desktop/mobile review captures. Compared both captures with the reference: hierarchy, section order, blue palette, and dominant OpsDesk panel match; illustrative controls, mockup copy, and erroneous copyright date were intentionally omitted.

Validation:
- command: `make test-frontend`: PASS — 70 frontend tests.
- command: `make lint`: PASS — backend Ruff and frontend ESLint.
- command: `make format-check`: PASS — backend Ruff format and frontend Prettier.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript.
- command: `cd frontend && npm run build`: PASS — production Vite build.
- command: `make test-e2e`: PASS — 14 browser tests passed and 1 project-specific test skipped; includes SPEC-318 widths, public accessibility, and Firefox/WebKit smoke.
- command: `docker compose run --rm -e PLAYWRIGHT_OUTPUT_DIR=/work/test-results e2e sh -c 'npm ci --silent && npx playwright test e2e/portfolio-landing.spec.ts --project=chromium-desktop'`: PASS — 3 responsive checks with ignored desktop/mobile screenshot artifacts for visual review.
- command: `make verify`: PASS — lint, format, types, 124 selected backend tests, 70 frontend tests, technical docs check, Alembic upgrade/check with no new operations.
- command: `make memory-check SPEC=SPEC-318`: PASS — implementation and project-state memory shape is current.
- command: `git diff --check`: PASS — no whitespace errors.
- command: local host `playwright test e2e/portfolio-landing.spec.ts`: UNAVAILABLE — Chromium could not launch because host `libnspr4.so` is absent; the Docker Playwright runs above passed.

Review:
- decision: N/A — review has not been requested or completed.

Known gaps:
- Independent review, merge, changelog-backed production release, and post-deploy desktop/mobile visual verification remain.
- The existing privacy-policy and Resend-key rotation operational gaps are separate from SPEC-318.

### 2026-09-23 — SPEC-318 — Portfolio landing visual spec ready

Role: Arquitecto de specs
Branch: main
Commit/PR: uncommitted spec-preparation changes; no PR
Status: Ready

Summary:
- Created `SPEC-318` for the selected public portfolio landing composition and stored its generated mockup as `specs/assets/spec-318-portfolio-landing-reference.png` so the design target survives a production release cycle.
- Defined desktop and responsive section hierarchy, existing project and legal-link preservation, accessible presentation, truthful-copy constraints, and pre/post-release visual checks. The authenticated OpsDesk interface is outside scope.
- Updated the spec index and project state. No product code or production deployment was changed.

Validation:
- command: `git diff --check`: PASS — no whitespace errors in planning changes.
- command: `make memory-check SPEC=SPEC-318`: PASS — spec memory shape is current.
- command: `file specs/assets/spec-318-portfolio-landing-reference.png`: PASS — versioned PNG reference is 1024 × 1536.
- command: implementation/test/release checks: NOT RUN — specification preparation only.

Review:
- decision: N/A — implementation and review have not begun.

Known gaps:
- `SPEC-318` implementation, browser comparison with the reference, review, and production deployment remain outstanding.
- The existing privacy-policy and Resend-key rotation operational gaps remain separate from this spec.

### 2026-09-16 — Operations Readiness production release

Role: Ingeniero de software
Branch: main
Commit/PR: Production Release run `35080510017`, deployed `a22dce9`
Status: Merged

Summary:
- Updated the VPS `/srv/opdesk/.env.production` with the required `SPEC-314` production email settings for Resend-backed delivery and created backup `.env.production.backup.20260916-093729`.
- Ran the manual Production Release workflow with `target_ref=a22dce9dc67cb52f01e012b4ac763799bd1d122e`, `deploy_to_production=true`, and changelog entry `2026-09-16 - Operations Readiness Release`.
- Deployed the Operations Readiness release to production with migration head `0014`, scheduler service running, and release manifest written at `/srv/opdesk/releases/latest-release.txt`.

Validation:
- command: `ssh opdesk-vps` env presence check: PASS — `PROD_PUBLIC_APP_URL`, `PROD_EMAIL_DELIVERY_PROVIDER`, `PROD_RESEND_API_KEY`, `PROD_RESEND_FROM_EMAIL`, `EMAIL_NOTIFICATIONS_ENABLED`, and `EMAIL_PROVIDER_TIMEOUT_SECONDS` are present in `/srv/opdesk/.env.production`.
- command: `ssh opdesk-vps 'cd /srv/opdesk/current && docker compose --project-name opdesk-prod --env-file /srv/opdesk/.env.production -f docker-compose.prod.yml config >/dev/null'`: PASS.
- command: `gh workflow run production-release.yml --repo RGAlvaro/opdesk --ref main ...`: PASS — triggered Production Release run `35080510017`.
- command: `gh run watch 35080510017 --repo RGAlvaro/opdesk --exit-status`: PASS — release job completed in 4m3s.
- command: `ssh opdesk-vps 'cat /srv/opdesk/releases/latest-release.txt'`: PASS — backup `/srv/opdesk/backups/opdesk-20260916-094007-a22dce9dc67cb52f01e012b4ac763799.dump`, `migrations=PASS`, `migration_drift_check=PASS`, `alembic_current=0014 (head)`, `compose_update=PASS`, `backend_health=PASS`, `frontend=PASS`, `redis=PASS`, `worker=PASS`, and `scheduler=PASS`.
- command: `ssh opdesk-vps 'curl --fail --silent --show-error --retry 5 --retry-delay 2 --retry-all-errors https://rgalvaro.es/health && curl --fail --silent --show-error --retry 5 --retry-delay 2 --retry-all-errors https://rgalvaro.es/ | head -c 120'`: PASS.
- command: local `curl --fail --silent --show-error https://rgalvaro.es/health`: PASS once with `{"status":"ok"}`; later local DNS resolution for `rgalvaro.es` and `www.rgalvaro.es` failed from this workstation, while VPS-side public checks and workflow public checks passed.

Review:
- decision: APPROVED by release workflow and post-deploy checks.

Known gaps:
- A full privacy policy remains needed before production use that relies on real user account/profile data beyond portfolio evaluation.
- The Resend API key was exposed during operator setup and should be rotated in Resend, then updated in `/srv/opdesk/.env.production`.

### 2026-09-16 — Production update preparation merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #23, merge `9319a2b`
Status: Merged

Summary:
- Merged the operations readiness changelog entry and production-release preparation memory through PR #23.
- The next production workflow should target current `main` and use changelog entry `2026-09-16 - Operations Readiness Release`.
- Local `main` was fast-forwarded to merge commit `9319a2b`.

Validation:
- command: `gh pr checks 23 --repo RGAlvaro/opdesk --watch`: PASS — `verify` passed in 1m30s and `e2e` passed in 3m3s on run `35071896950`.
- command: `gh pr view 23 --repo RGAlvaro/opdesk --json mergeStateStatus,isDraft,statusCheckRollup,headRefOid,baseRefName,headRefName,url`: PASS before merge — PR was not draft, merge state `CLEAN`, `verify` and `e2e` succeeded on head `d2e0e5d`.
- command: `gh pr merge 23 --repo RGAlvaro/opdesk --merge --delete-branch`: PASS.
- command: `git switch main && git pull --ff-only`: PASS — fast-forwarded local `main` to merge commit `9319a2b`.

Review:
- decision: APPROVED by passing CI and release-preparation validation.

Known gaps:
- Before production deployment, confirm the VPS `.env.production` has `PROD_PUBLIC_APP_URL`, `PROD_RESEND_API_KEY`, `PROD_RESEND_FROM_EMAIL`, and other `SPEC-314` email settings required by production Compose.
- A full privacy policy remains needed before production use that relies on real user account/profile data beyond portfolio evaluation.

### 2026-09-16 — Production update preparation started

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added the required production changelog heading `2026-09-16 - Operations Readiness Release` for the next release workflow run.
- The release entry summarizes changes merged since the 2026-08-18 production deployment: cross-browser/accessibility E2E hardening, external email notifications, real-time notification inbox, scheduler/operational audit, public legal pages, and technical documentation.

Validation:
- command: `make changelog-check`: PASS.
- command: `make prod-config`: PASS — production Compose renders backend, frontend, PostgreSQL, Redis, worker, scheduler, and Caddy with placeholder production env.
- command: `make technical-docs-check`: PASS.
- command: `make release-workflow-check`: PASS — changelog validation, workflow static validation, release script syntax, and missing-env failure guard passed.

Review:
- decision: N/A

Known gaps:
- A full privacy policy remains needed before production use that relies on real user account/profile data beyond portfolio evaluation.
- Before production deployment, confirm the VPS `.env.production` has the required Resend variables and production public app URL for `SPEC-314`.

### 2026-09-16 — SPEC-317 — Merged to main

Role: Ingeniero de software
Branch: main
Commit/PR: PR #22, merge `eab66a6`
Status: Merged

Summary:
- Published local documentation/legal commits through branch `agent/spec-317-legal-docs` and opened PR #22.
- Waited for GitHub Actions; `verify` and `e2e` passed on the PR head.
- Merged PR #22 into `main` with the merge strategy and deleted the remote feature branch through GitHub.
- Fast-forwarded local `main` to merge commit `eab66a6`.

Validation:
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `git push -u origin agent/spec-317-legal-docs`: PASS.
- command: `gh pr create --repo RGAlvaro/opdesk --base main --head agent/spec-317-legal-docs`: PASS — opened PR #22.
- command: `gh pr checks 22 --repo RGAlvaro/opdesk --watch`: PASS — `verify` passed in 1m57s and `e2e` passed in 2m48s on run `35070466769`.
- command: `gh pr view 22 --repo RGAlvaro/opdesk --json mergeStateStatus,isDraft,statusCheckRollup,headRefOid,baseRefName,headRefName,url`: PASS before merge — PR was not draft, merge state `CLEAN`, `verify` and `e2e` succeeded on head `91b0c90`.
- command: `gh pr merge 22 --repo RGAlvaro/opdesk --merge --delete-branch`: PASS.
- command: `git switch main`: PASS.
- command: `git pull --ff-only`: PASS — fast-forwarded local `main` to merge commit `eab66a6`.

Review:
- decision: APPROVED by passing CI and prior local validation; no separate review-agent pass was requested before merge.

Known gaps:
- A full privacy policy remains needed before production use that relies on real user account/profile data beyond portfolio evaluation.
- The public legal text is a conservative template and should be reviewed with final responsible-party/contact details before being relied on legally.

### 2026-09-16 — SPEC-317 — Public legal pages implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added `SPEC-317` for public terms, copyright, and cookie-policy pages before the next production deployment.
- Added public frontend routes `/terms`, `/copyright`, and `/cookies` with static legal text and production review caveats.
- Added landing footer links to the legal pages and frontend route coverage for the pages and footer links.
- Updated technical documentation route inventory and documented the remaining pre-production privacy-policy gap.

Validation:
- command: `cd frontend && ./node_modules/.bin/vitest run src/app/AppRouter.test.tsx --testNamePattern "public legal|portfolio home" --reporter verbose --maxWorkers 1`: PASS — legal route tests and landing footer link test passed.
- command: `cd frontend && ./node_modules/.bin/vitest run src/app/AppRouter.test.tsx --maxWorkers 1`: PASS — 28 router tests passed.
- command: `cd frontend && npm run format:check -- src/app/AppRouter.test.tsx src/app/AppRouter.tsx src/app/LandingPage.tsx src/app/LegalPages.tsx`: PASS.
- command: `cd frontend && npm run lint`: PASS.
- command: `cd frontend && npm run typecheck`: PASS.
- command: `make technical-docs-check`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- A full privacy policy remains needed before production use that relies on real user account/profile data beyond portfolio evaluation.
- The public legal text is a conservative template and should be reviewed with final responsible-party/contact details before being relied on legally.

### 2026-09-15 — Technical documentation maintenance harness added

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Added `docs/technical-documentation.md` as the canonical full internal technical documentation source for the current OpsDesk architecture.
- Added `scripts/check_technical_docs.py` and `make technical-docs-check` to validate required documentation sections, stack terms, current Alembic head, local/production Compose services, and ASCII-only PDF-friendly content.
- Added `make technical-docs-check` to `verify-no-db` so future architecture/runtime changes must keep the technical documentation current before review.
- Documented the new target in `specs/harness/local-validation.md` and in the technical documentation maintenance section.

Validation:
- command: `make technical-docs-check`: PASS.
- command: `python3 -m py_compile scripts/check_technical_docs.py`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- No PDF converter is installed in the current environment; the Markdown document remains the canonical source until a PDF conversion tool such as Pandoc is added.

### 2026-09-15 — SPEC-316 — Merged to main

Role: Ingeniero de software
Branch: main
Commit/PR: PR #21, merge `e0b1bea`
Status: Merged

Summary:
- Confirmed PR #21 was not draft, merge state was `CLEAN`, and required GitHub Actions checks passed.
- Merged PR #21 into `main` with the merge strategy and deleted the remote feature branch through GitHub.
- Switched local checkout to `main` and fast-forwarded to merge commit `e0b1bea`.

Validation:
- command: `gh pr view 21 --repo RGAlvaro/opdesk --json url,headRefOid,mergeStateStatus,statusCheckRollup,isDraft,baseRefName,headRefName`: PASS before merge — PR was not draft, merge state `CLEAN`, `verify` and `e2e` succeeded on head `dfaeac2`.
- command: `gh pr merge 21 --repo RGAlvaro/opdesk --merge --delete-branch`: PASS.
- command: `git switch main`: PASS.
- command: `git pull --ff-only`: PASS — fast-forwarded local `main` to merge commit `e0b1bea`.
- command: GitHub Actions `Verify` run `34958845792`: PASS before merge — `verify` passed in 1m49s and `e2e` passed in 2m44s.

Review:
- decision: APPROVED

Known gaps:
- No blocking `SPEC-316` gaps. Production must run exactly one scheduler instance; horizontal scheduler locking remains future scope if multiple scheduler replicas are ever needed.

### 2026-09-15 — SPEC-316 — PR opened

Role: Ingeniero de software
Branch: agent/spec-316-scheduled-audit
Commit/PR: PR #21, commit `6b1c6f5`
Status: Reviewed

Summary:
- Pushed the reviewed `SPEC-316` branch to `origin/agent/spec-316-scheduled-audit`.
- Opened PR #21 against `main` after review approval.

Validation:
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `git push -u origin agent/spec-316-scheduled-audit`: PASS.
- command: `gh pr create --repo RGAlvaro/opdesk --base main --head agent/spec-316-scheduled-audit`: PASS — opened PR #21.

Review:
- decision: APPROVED

Known gaps:
- No blocking `SPEC-316` gaps. Production must run exactly one scheduler instance; horizontal scheduler locking remains future scope if multiple scheduler replicas are ever needed.

### 2026-09-15 — SPEC-316 — Scheduled jobs audit review fixes approved

Role: Review agent
Branch: agent/spec-316-scheduled-audit
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-316` fix commit `faf032f` against the prior review findings.
- Confirmed scheduled-job failure audit rows now persist a generic safe summary instead of raw exception text.
- Confirmed stale ticket assignment reminder reruns keep idempotent notification behavior and report `records_changed=0` when no new notification is created.

Validation:
- command: `cd backend && poetry run pytest tests/test_operational_audit.py`: PASS — 6 focused scheduled-job/audit tests passed.
- command: `cd backend && poetry run ruff check app/services/operational_audit.py tests/test_operational_audit.py`: PASS.
- command: `make test-backend`: PASS — 124 backend tests passed and 2 DB tests were deselected.
- command: `cd backend && poetry run mypy app`: PASS.
- command: `make memory-check SPEC=SPEC-316`: PASS.
- command: `git diff --check HEAD~1..HEAD`: PASS.

Review:
- decision: APPROVED

Known gaps:
- No blocking `SPEC-316` gaps. Production must run exactly one scheduler instance; horizontal scheduler locking remains future scope if multiple scheduler replicas are ever needed.

### 2026-09-15 — SPEC-316 — Scheduled jobs audit review fixes implemented

Role: Ingeniero de software
Branch: agent/spec-316-scheduled-audit
Commit/PR: Pending
Status: Implemented

Summary:
- Replaced persisted scheduled-job failure details with a generic safe summary based on the exception class so raw exception text, tokens, provider payloads, or message bodies are not stored in audit rows.
- Corrected stale ticket assignment reminder audit counts so idempotent reruns report `records_changed=0` when an unread reminder already exists.
- Added regression assertions for sensitive failure text redaction and idempotent reminder change counts.

Validation:
- command: `cd backend && poetry run pytest tests/test_operational_audit.py`: PASS — 6 focused scheduled-job/audit tests passed with the new regression assertions.
- command: `cd backend && poetry run ruff check app/services/operational_audit.py tests/test_operational_audit.py`: PASS.
- command: `cd backend && poetry run ruff format --check app/services/operational_audit.py tests/test_operational_audit.py`: PASS.
- command: `make test-backend`: PASS — 124 backend tests passed and 2 DB tests were deselected.
- command: `cd backend && poetry run mypy app`: PASS.

Review:
- decision: N/A — review fixes pending re-review.

Known gaps:
- No `SPEC-316` implementation gaps known after review fixes. Production must run exactly one scheduler instance; horizontal scheduler locking remains future scope if multiple scheduler replicas are ever needed.

### 2026-09-15 — SPEC-316 — Scheduled jobs and operational audit implemented

Role: Ingeniero de software
Branch: agent/spec-316-scheduled-audit
Commit/PR: Pending
Status: Implemented

Summary:
- Added persistent `operational_audit_runs` storage with Alembic migration `0014`, repository/service/schema layers, and owner/admin-only audit listing API.
- Added Celery beat scheduling for heartbeat, external notification delivery retry sweeps, expired invitation maintenance, and stale ticket assignment request reminders, with each run recorded as started, succeeded, failed, or skipped.
- Added an admin operational audit UI, navigation visibility for organization owners/admins, frontend API hooks, and regression coverage for authorization and filtering.
- Updated local/production Compose, smoke checks, production release script checks, deployment docs, README, and spec indexes so the scheduler service is part of the operational contract.

Validation:
- command: `cd backend && poetry run pytest tests/test_operational_audit.py`: PASS — 6 focused backend scheduled-job/audit tests passed.
- command: `cd frontend && npm run test -- AppRouter.test.tsx`: PASS — focused router/audit UI coverage passed.
- command: `make test-backend`: PASS — 124 backend tests passed and 2 DB tests were deselected.
- command: `make test-frontend`: PASS — 67 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make migrations-check`: PASS — Alembic upgraded through `0014` and reported no new upgrade operations.
- command: `make prod-config`: PASS — production Compose renders the private scheduler service.
- command: `make smoke`: PASS — Docker/local backend health, Redis `PONG`, worker, scheduler, Adminer, and Vite frontend checks passed.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- No `SPEC-316` implementation gaps known before review. Production must run exactly one scheduler instance; horizontal scheduler locking remains future scope if multiple scheduler replicas are ever needed.

### 2026-09-15 — SPEC-315 — Merged to main

Role: Ingeniero de software
Branch: main
Commit/PR: PR #20, merge `cac6268`
Status: Merged

Summary:
- Merged PR #20 into `main` with the merge strategy after final PR checks passed.
- Pulled `main` locally to merge commit `cac6268`.
- Updated project memory so the next handoff moves to `SPEC-316`.

Validation:
- command: `gh pr view 20 --repo RGAlvaro/opdesk --json mergeStateStatus,statusCheckRollup,headRefOid,baseRefName,headRefName,url`: PASS before merge — merge state `CLEAN`, `verify` and `e2e` successful on head `f3dca14`.
- command: `gh pr merge 20 --repo RGAlvaro/opdesk --merge --delete-branch`: PASS.
- command: `git switch main`: PASS.
- command: `git pull --ff-only`: PASS — fast-forwarded `main` to merge commit `cac6268`.
- command: GitHub Actions `Verify` run `34943597736`: PASS before merge — `verify` passed in 1m47s and `e2e` passed in 3m7s.

Review:
- decision: APPROVED before merge.

Known gaps:
- Multi-backend Redis pub/sub fan-out remains outside V1 by spec and must be added before horizontal backend scaling.

### 2026-09-15 — SPEC-315 — PR opened and GitHub Actions passed

Role: Ingeniero de software
Branch: agent/spec-315-realtime-notifications
Commit/PR: PR #20, commit `a9c12d9`, GitHub Actions run `34943274026`
Status: Reviewed

Summary:
- Pushed the reviewed `SPEC-315` branch and opened PR #20 against `main`.
- Confirmed GitHub CLI authentication for account `RGAlvaro` with `repo` and `workflow` scopes before PR operations.
- Waited for GitHub Actions on PR #20; both required jobs passed on run `34943274026`.

Validation:
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `git push -u origin agent/spec-315-realtime-notifications`: PASS.
- command: `gh pr create --repo RGAlvaro/opdesk --base main --head agent/spec-315-realtime-notifications`: PASS — opened PR #20.
- command: `gh pr checks 20 --repo RGAlvaro/opdesk --watch`: PASS — `verify` passed in 1m56s and `e2e` passed in 2m52s on run `34943274026`.

Review:
- decision: APPROVED before PR creation.

Known gaps:
- Multi-backend Redis pub/sub fan-out remains outside V1 by spec and must be added before horizontal backend scaling.

### 2026-09-15 — SPEC-315 — Real-time notification inbox reviewed

Role: Review agent
Branch: agent/spec-315-realtime-notifications
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-315` against authenticated notification WebSocket delivery, recipient isolation, post-commit fan-out, read-state events, frontend unread/list cache updates, reconnect behavior, REST polling fallback, tests, and project memory.
- Confirmed the branch includes the merged `SPEC-314` baseline after resolving the notification-service and memory conflicts from `main`.
- Kept the documented multi-backend fan-out limitation as future scope before horizontal backend scaling.

Validation:
- command: `make test-backend`: PASS — 118 selected backend tests passed and 2 DB tests were deselected.
- command: `make test-frontend`: PASS — 65 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make smoke`: PASS — Docker/local backend health, Redis `PONG`, worker, Adminer, and Vite frontend checks passed.
- command: `make memory-check SPEC=SPEC-315`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- Multi-backend Redis pub/sub fan-out remains outside V1 by spec and must be added before horizontal backend scaling.

### 2026-09-11 — SPEC-314 — Merged to main

Role: Ingeniero de software
Branch: main
Commit/PR: PR #19, merge `70fcbee`
Status: Merged

Summary:
- Merged PR #19 into `main` with the merge strategy after final PR checks passed.
- Pulled `main` locally to merge commit `70fcbee`.
- Updated project memory so the next handoff moves to `SPEC-315`.

Validation:
- command: `gh pr view 19 --repo RGAlvaro/opdesk --json mergeStateStatus,statusCheckRollup,url,headRefOid,baseRefName,headRefName`: PASS before merge — merge state `CLEAN`, `verify` and `e2e` successful on head `a05b2f6`.
- command: `gh pr merge 19 --repo RGAlvaro/opdesk --merge --delete-branch`: PASS.
- command: `git switch main`: PASS.
- command: `git pull --ff-only`: PASS — fast-forwarded `main` to merge commit `70fcbee`.
- command: GitHub Actions `Verify` run `34577119234`: PASS before merge — `verify` passed in 1m54s and `e2e` passed in 3m10s.

Review:
- decision: APPROVED before merge.

Known gaps:
- None for `SPEC-314` merge handoff. Scheduled retry sweeps through Celery beat remain in `SPEC-316`; manual delivery-audit cleanup remains future scope per `SPEC-314`.

### 2026-09-11 — SPEC-314 — PR opened and GitHub Actions passed

Role: Ingeniero de software
Branch: agent/spec-314-external-notifications
Commit/PR: PR #19, commit `7e4540b`, GitHub Actions run `34576823985`
Status: Reviewed

Summary:
- Committed reviewed `SPEC-314` implementation and opened PR #19 against `main`.
- Confirmed GitHub CLI authentication for account `RGAlvaro` with `repo` and `workflow` scopes before PR operations.
- Waited for GitHub Actions on PR #19; both required jobs passed on run `34576823985`.

Validation:
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `git push -u origin agent/spec-314-external-notifications`: PASS.
- command: `gh pr create --repo RGAlvaro/opdesk --base main --head agent/spec-314-external-notifications`: PASS — opened PR #19.
- command: `gh pr checks 19 --repo RGAlvaro/opdesk --watch`: PASS — `verify` passed in 2m1s and `e2e` passed in 2m41s on run `34576823985`.

Review:
- decision: APPROVED before PR creation.

Known gaps:
- None for PR validation. Scheduled retry sweeps through Celery beat remain in `SPEC-316`; manual delivery-audit cleanup remains future scope per `SPEC-314`.

### 2026-09-11 — SPEC-314 — External notification delivery reviewed

Role: Review agent
Branch: agent/spec-314-external-notifications
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-314` implementation against delivery eligibility, Resend/console provider behavior, audit persistence, retry/suppression states, idempotency, production configuration, and memory requirements.
- Tightened default delivery logging so worker diagnostics include safe ids/status/error fields without logging recipient email, subject, provider payloads, tokens, or message bodies.

Validation:
- command: `make test-backend`: PASS — 115 selected backend tests passed and 2 DB tests were deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make memory-check SPEC=SPEC-314`: PASS.
- command: `git diff --check`: PASS.
- command: `make migrations-check`: FAIL in current environment — elevated rerun could not connect to PostgreSQL at `127.0.0.1:5432`; prior implementation validation passed this command before the logging-only review adjustment.
- command: `make prod-config`: FAIL in current environment — elevated rerun could not find `docker` in this WSL distro; prior implementation validation passed this command before the logging-only review adjustment.

Review:
- decision: APPROVED

Known gaps:
- No blocking `SPEC-314` gaps. Scheduled retry sweeps through Celery beat remain in `SPEC-316`; manual delivery-audit cleanup remains future scope per `SPEC-314` retention decision.

### 2026-09-09 — SPEC-314 — External notification delivery implemented

Role: Ingeniero de software
Branch: agent/spec-314-external-notifications
Commit/PR: Pending
Status: Implemented

Summary:
- Added `notification_deliveries` audit persistence with migration `0013`, email channel/status enums, retry indexes, and notification/channel idempotency.
- Added console and Resend email providers, safe plain-text email composition, post-commit delivery job enqueueing, bounded retry state, suppression for inactive/missing recipients, and Celery tasks for one delivery plus due-delivery sweeps.
- Added `ticket.created` notification fan-out for client-created tickets, production/local email env wiring, deployment docs, and network-free backend tests for adapter, service, worker, retry, suppression, and idempotency behavior.
- Brief future-spec note: if OpsDesk runs multiple backend replicas, notification WebSocket fan-out should use Redis pub/sub or an equivalent shared broker so events from one backend reach sockets connected to another backend.

Validation:
- command: `make test-backend`: PASS — 115 selected backend tests passed and 2 DB tests were deselected.
- command: `make migrations-check`: PASS — Alembic upgraded PostgreSQL through `0013` and reported no new upgrade operations.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make prod-config`: PASS — production Compose renders backend/worker Resend env wiring with placeholders.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- No `SPEC-314` implementation gaps known before review. Scheduled retry sweeps through Celery beat remain in `SPEC-316`; manual delivery-audit cleanup remains future scope per `SPEC-314` retention decision.

### 2026-09-09 — SPEC-315 — Real-time notification inbox implemented

Role: Ingeniero de software
Branch: agent/spec-315-realtime-notifications
Commit/PR: commit `aa9896f`, PR pending
Status: Implemented

Summary:
- Added authenticated `WS /api/v1/notifications/ws` support with in-process recipient-scoped connection tracking.
- Registered a notification event publisher so persisted notification create/read/mark-all-read changes emit best-effort real-time events with REST-compatible payloads and unread counts.
- Connected the authenticated app shell to a notification WebSocket hook that patches React Query unread/list caches, avoids duplicate list entries, invalidates REST state for recovery, and keeps a 30s polling fallback.
- Updated chat frontend tests to account for the new app-wide notification socket.
- Marked `SPEC-315` Implemented in the spec and spec index.

Validation:
- command: `cd backend && poetry run pytest tests/test_in_app_notifications_api.py`: PASS — 6 notification API/WebSocket tests passed.
- command: `cd frontend && npm run test -- NotificationsPage.test.tsx`: PASS — 3 notification UI/WebSocket tests passed.
- command: `make test-backend`: PASS — 109 selected backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 65 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: elevated `make smoke`: PASS — Docker/local backend health, Redis `PONG`, worker, Adminer, and Vite frontend checks passed.

Review:
- decision: N/A

Known gaps:
- Multi-backend Redis pub/sub fan-out remains outside V1 by spec and must be added before horizontal backend scaling. Future spec note: when OpsDesk runs multiple backend replicas, publish notification events through Redis pub/sub or an equivalent shared broker so events created on one backend can reach sockets connected to another backend.

### 2026-09-09 — SPEC-313 — Merged to main

Role: Ingeniero de software
Branch: main
Commit/PR: PR #18, merge `8006844`
Status: Merged

Summary:
- Merged PR #18 into `main` with the merge strategy after final PR checks passed.
- Pulled `main` locally to merge commit `8006844`.
- Updated project memory so the next handoff moves to `SPEC-315`.

Validation:
- command: `gh pr view 18 --repo RGAlvaro/opdesk --json mergeStateStatus,statusCheckRollup,url,headRefOid`: PASS before merge — merge state `CLEAN`, `verify` and `e2e` successful on head `971da56`.
- command: `gh pr merge 18 --repo RGAlvaro/opdesk --merge --delete-branch`: PASS.
- command: `git switch main`: PASS.
- command: `git pull --ff-only`: PASS — fast-forwarded `main` to merge commit `8006844`.
- command: GitHub Actions `Verify` run `34325273247`: PASS before merge — `verify` passed in 1m57s and `e2e` passed in 2m52s.

Review:
- decision: APPROVED before merge

Known gaps:
- None for `SPEC-313` merge handoff. Visual snapshots remain outside `SPEC-313` by design.

### 2026-09-09 — SPEC-313 — PR opened and GitHub Actions passed

Role: Ingeniero de software
Branch: agent/spec-313-cross-browser-a11y
Commit/PR: PR #18, commit `971da56`, GitHub Actions runs `34324881133` and `34325273247`
Status: PR merged

Summary:
- Pushed `agent/spec-313-cross-browser-a11y` to GitHub and opened PR #18 against `main`.
- Confirmed GitHub CLI authentication for account `RGAlvaro` with `repo` and `workflow` scopes before PR operations.
- Waited for GitHub Actions `Verify` run `34324881133` on PR #18 after the initial push, then pushed PR evidence commit `971da56` and waited for final run `34325273247`.

Validation:
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `git push -u origin agent/spec-313-cross-browser-a11y`: PASS.
- command: `gh pr create --repo RGAlvaro/opdesk --base main --head agent/spec-313-cross-browser-a11y`: PASS — opened PR #18.
- command: `gh pr checks 18 --repo RGAlvaro/opdesk --watch`: PASS for run `34324881133` — `verify` passed in 1m52s and `e2e` passed in 2m49s before this PR evidence memory commit.
- command: `gh pr checks 18 --repo RGAlvaro/opdesk --watch`: PASS for final run `34325273247` — `verify` passed in 1m57s and `e2e` passed in 2m52s on PR head `971da56`.

Review:
- decision: APPROVED before PR creation; PR merged after final checks.

Known gaps:
- None for PR validation.

### 2026-09-07 — SPEC-313 — Cross-browser and accessibility E2E reviewed

Role: Review agent
Branch: agent/spec-313-cross-browser-a11y
Commit/PR: commit `66c3610`, PR #18
Status: Reviewed

Summary:
- Reviewed `SPEC-313` implementation against cross-browser Playwright project coverage, accessibility scan coverage, harness documentation, CI artifact behavior, dependency changes, and project memory.
- Confirmed Firefox/WebKit smoke coverage exercises public routes, protected-route redirect, signup/login/logout, app shell, organization creation, project visibility, and post-logout protection.
- Confirmed Chromium accessibility checks scan public home, changelog, login, authenticated app shell, notifications inbox, project task list, and client ticket shell with route-specific serious/critical violation output.
- Confirmed existing Chromium desktop full suite and Chromium mobile critical path remain configured.

Validation:
- command: `make memory-check SPEC=SPEC-313`: PASS.
- command: `git diff --check`: PASS.
- command: `cd frontend && npm run typecheck`: PASS.
- command: `cd frontend && npm run format:check`: PASS.
- command: `cd frontend && npm run lint`: PASS.
- command: prior implementation `make test-e2e`: PASS — reviewed evidence recorded 11 passed and 1 expected skip across Chromium desktop, Chromium mobile, Firefox smoke, WebKit smoke, and accessibility scans.
- command: prior implementation `make test-frontend`: PASS — 63 frontend tests passed.
- command: prior implementation elevated `make smoke`: PASS.

Review:
- decision: APPROVED

Known gaps:
- Visual snapshot testing remains outside `SPEC-313` by design.

### 2026-09-07 — SPEC-313 — Cross-browser and accessibility E2E implemented

Role: Ingeniero de software
Branch: agent/spec-313-cross-browser-a11y
Commit/PR: commit `66c3610`, PR #18
Status: Implemented

Summary:
- Added `@axe-core/playwright` as a frontend dev dependency for rendered-page accessibility scans.
- Extended Playwright projects with `firefox-smoke` and `webkit-smoke` while keeping Chromium desktop as the full-suite project and Chromium mobile on the critical path.
- Added Firefox/WebKit smoke coverage for public home, changelog, protected-route redirect, signup/logout/login, organization creation, project visibility, and post-logout route protection.
- Added Chromium accessibility coverage for public home, changelog, login, authenticated app shell, notifications inbox, project task list, and client ticket shell, failing on serious/critical WCAG 2 A/AA violations with route-specific context.
- Updated E2E helpers for project client setup and updated harness documentation for the expanded browser/accessibility behavior.

Validation:
- command: `make test-e2e`: PASS — Docker/local Compose build, backend Alembic upgrade/check, and Playwright completed with 11 passed and 1 expected skip across Chromium desktop, Chromium mobile, Firefox smoke, WebKit smoke, and accessibility scans.
- command: `make test-frontend`: PASS — 63 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make smoke`: PASS — backend health, Redis `PONG`, worker running, Adminer, and Vite frontend checks passed.
- command: `make memory-check SPEC=SPEC-313`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-313` implementation needs review approval. Visual snapshots remain outside this spec by design.

### 2026-09-07 — SPEC-314/SPEC-316 — Notification delivery and scheduler decisions resolved

Role: Arquitecto de specs
Branch: agent/spec-313-cross-browser-a11y
Commit/PR: commit `66c3610`, PR #18
Status: Ready

Summary:
- Moved `SPEC-314` to Ready with Resend as the production email provider, email notifications enabled by default, all enumerated first-slice events eligible for email, and delivery audit retained indefinitely until manual deletion.
- Moved `SPEC-316` to Ready with Celery beat as scheduler, first-job order set to scheduler heartbeat/health audit, external delivery retry sweep, expired invitation state maintenance, and stale ticket assignment request reminders.
- Added owner/admin operational audit UI and API requirements to `SPEC-316`.
- Added `ADR-013` for Resend email delivery and `ADR-014` for Celery beat plus operational audit decisions.
- Updated `specs/README.md` and `docs/project-state.md` so all four planned specs are Ready and dependency-aware next work is clear.

Validation:
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-314`: PASS.
- command: `make memory-check SPEC=SPEC-316`: PASS.

Review:
- decision: N/A

Known gaps:
- None for spec readiness; implementation remains pending.

### 2026-09-07 — SPEC-313/SPEC-314/SPEC-315/SPEC-316 — Known gaps converted into planned specs

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Planned

Summary:
- Added `SPEC-313` as Ready for cross-browser Playwright smoke coverage and automated accessibility checks.
- Added `SPEC-314` as Draft for external email notification delivery, provider adapter, delivery audit, and production configuration.
- Added `SPEC-315` as Ready for real-time notification inbox updates over WebSockets with REST recovery and polling fallback.
- Added `SPEC-316` as Draft for scheduled jobs, scheduler service topology, and persistent operational audit.
- Updated `specs/README.md` and `docs/project-state.md` with new spec routing, dependencies, readiness state, known gaps, and next likely work.

Validation:
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-313`: PASS.
- command: `make memory-check SPEC=SPEC-314`: PASS.
- command: `make memory-check SPEC=SPEC-315`: PASS.
- command: `make memory-check SPEC=SPEC-316`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-314` needs product/operations decisions for production email provider, user preference defaults, first emailed event types, and delivery audit retention.
- `SPEC-316` needs decisions for first scheduled jobs, notification/audit retention, audit UI scope, and final scheduler mechanism.

### 2026-08-18 — SPEC-307/SPEC-305/SPEC-304 — Collaboration release deployed to production

Role: Ingeniero de software
Branch: main
Commit/PR: commit `cc35414`, Production Release run `32133588953`
Status: Deployed

Summary:
- Added the `2026-08-18 - Collaboration Release` changelog entry for the production deploy containing merged `SPEC-305` and `SPEC-304`.
- Fixed the public changelog route test after the new release entry increased the rendered release count.
- Deployed app revision `cc354148dee2d1f69b3d99d34b3f0aaced3f06b6` to production through the manual `Production Release` workflow.
- Confirmed the production manifest recorded backup `/srv/opdesk/backups/opdesk-20260818-115050-cc354148dee2d1f69b3d99d34b3f0aac.dump`, `backend_image_build=PASS`, `migrations=PASS`, `migration_drift_check=PASS`, `alembic_current=0012 (head)`, `compose_update=PASS`, `backend_health=PASS`, `frontend=PASS`, `redis=PASS`, and `worker=PASS`.

Validation:
- command: `python3 scripts/validate_changelog.py --entry "2026-08-18 - Collaboration Release"`: PASS.
- command: `make changelog-check`: PASS.
- command: `make release-workflow-check`: PASS.
- command: `cd frontend && npm run test -- AppRouter.test.tsx --run`: PASS — 23 frontend route tests passed after the changelog test update.
- command: `make test-frontend`: PASS — 63 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: `git diff --check`: PASS.
- command: GitHub Actions `Verify` run `32127525357`: FAIL — release-note commit exposed stale changelog route assertion expecting 2 `Added` sections; `e2e` passed and no production deploy was attempted.
- command: GitHub Actions `Verify` run `32127831767`: PASS — `verify` passed in 1m47s and `e2e` passed in 2m48s after the test fix.
- command: GitHub Actions `Production Release` run `32128264461`: FAIL — checkout failed because an incorrect target SHA was supplied; no validation, backup, migration, or production update ran.
- command: GitHub Actions `Production Release` run `32133588953`: PASS — deployed `cc354148dee2d1f69b3d99d34b3f0aaced3f06b6` in 2m58s.
- command: `curl -fsS https://rgalvaro.es/health`: PASS — returned `{"status":"ok"}`.
- command: `curl -I -fsS https://rgalvaro.es/`: PASS — returned `HTTP/2 200`.
- command: `curl -I -fsS https://rgalvaro.es/changelog`: PASS — returned `HTTP/2 200`.
- command: `curl -i -sS https://rgalvaro.es/api/v1/users/me`: PASS — returned expected `401 not_authenticated` API envelope.
- command: `ssh opdesk-vps '... releases/latest-release.txt ... alembic current ... docker compose ps ...'`: PASS — manifest and direct Alembic check report `0012 (head)`; backend, frontend, Caddy, PostgreSQL, Redis, and worker are running with PostgreSQL/Redis private.

Review:
- decision: APPROVED — `SPEC-305` and `SPEC-304` were approved before merge; `SPEC-307` release automation was previously review approved.

Known gaps:
- None for this production deployment. Future notification integrations remain outside the deployed specs until specified.

### 2026-08-18 — SPEC-304 — Organization member chat merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #17 https://github.com/RGAlvaro/opdesk/pull/17, merge `6aea60e`
Status: Merged

Summary:
- Published the approved `SPEC-304` implementation branch and opened PR #17 for organization member chat.
- GitHub Actions passed both required checks, then PR #17 was marked ready, squash-merged to `main`, and the remote feature branch was deleted.
- Confirmed `main` includes migration `0012`, chat persistence, REST/WebSocket chat APIs, aggregate `chat.unread` notifications, organization chat UI, backend/frontend tests, and project memory updates.

Validation:
- command: `gh pr checks 17 --repo RGAlvaro/opdesk --watch`: PASS — `verify` passed in 1m47s and `e2e` passed in 2m9s.
- command: `gh pr view 17 --repo RGAlvaro/opdesk --json number,url,state,mergedAt,mergeCommit,headRefName,baseRefName`: PASS — PR #17 is `MERGED` with merge commit `6aea60e`.
- command: `git pull --ff-only`: PASS — local `main` fast-forwarded to `6aea60e`.

Review:
- decision: APPROVED — review entry below approved `SPEC-304` before merge.

Known gaps:
- `SPEC-304` was not yet deployed at merge time; it was deployed later on 2026-08-18 through Production Release run `32133588953`.

### 2026-08-18 — SPEC-304 — Organization member chat approved

Role: Review agent
Branch: main
Commit/PR: PR #17 https://github.com/RGAlvaro/opdesk/pull/17, merge `6aea60e`
Status: Reviewed

Summary:
- Re-reviewed `SPEC-304` after the review fixes.
- Confirmed the previous blocking gaps are fixed: REST chat message body validation now returns the specified `400 invalid_message` envelope for empty and overlong bodies, and frontend chat tests cover unread state plus conversation clearing.
- Confirmed internal member chat, direct conversations, organization/project channels, WebSocket delivery, REST history/recovery, client exclusion, tenant-safe project-channel access, aggregate unread notifications, migration `0012`, and project memory align with the spec.

Validation:
- command: `make test-backend`: PASS — 106 selected backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 63 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgrade/check completed with no new upgrade operations.
- command: `make memory-check SPEC=SPEC-304`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-08-18 — SPEC-304 — Review fixes implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed the `SPEC-304` review gap where REST chat message body validation could return framework `422` by routing empty and overlong message bodies through service-owned `400 invalid_message` validation.
- Added backend regression coverage for empty and overlong REST message bodies.
- Expanded frontend chat tests to cover unread conversation badge rendering and the conversation clear action.

Validation:
- command: `cd backend && poetry run pytest tests/test_organization_chat_api.py -q`: PASS — 6 SPEC-304 backend tests passed.
- command: `cd frontend && npm run test -- ChatPage.test.tsx --run`: PASS — 5 SPEC-304 frontend chat tests passed.
- command: `make test-backend`: PASS — 106 selected backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 63 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: `make memory-check SPEC=SPEC-304`: PASS.
- command: `git diff --check`: PASS.
- command: `make migrations-check`: NOT RUN — review fix did not change migrations or SQLAlchemy models; prior `SPEC-304` elevated migration validation passed through `0012`.

Review:
- decision: N/A

Known gaps:
- `SPEC-304` review fixes are implemented and need re-review.

### 2026-08-18 — SPEC-304 — Organization member chat reviewed

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-304` implementation against REST/WebSocket contracts, tenant isolation, client exclusion, project-channel access, unread notifications, frontend route behavior, migration, and project memory.
- Confirmed the main chat surfaces exist: migration `0012`, chat persistence, REST endpoints, WebSocket endpoint, direct/project/organization conversation support, aggregate `chat.unread` notifications, frontend chat route, and app-shell navigation hidden from client users.
- Found blocking gaps in API validation error shape and required frontend test coverage.

Validation:
- command: `cd backend && poetry run pytest tests/test_organization_chat_api.py -q`: PASS — 5 SPEC-304 backend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: `make memory-check SPEC=SPEC-304`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Empty or overlong REST message bodies currently use Pydantic request validation and can return framework `422` instead of the specified `400 invalid_message`; add endpoint-level regression coverage.
- Frontend tests do not yet cover the required unread-state and conversation-clearing behavior.

### 2026-08-18 — SPEC-304 — Organization member chat implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Implemented internal organization chat with migration `0012`, chat conversation/message/read persistence, direct conversations, organization and project channels, member-list shared-project ordering, personal conversation clearing, read state, and aggregate `chat.unread` notifications.
- Added authenticated REST chat APIs plus an in-process WebSocket endpoint that authenticates existing session cookies, persists messages before fan-out, and supports reconnect recovery through REST history.
- Added a frontend organization chat route with internal-only app-shell navigation, member discovery, project-channel opening, conversation list, explicit connection state, WebSocket send path, REST fallback, refresh, clear, empty/error states, and route-query selected conversation state.
- Added backend API/WebSocket tests and frontend route tests for `SPEC-304`.

Validation:
- command: `make test-backend`: PASS — 105 selected backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 61 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through `0012` and check reported no new upgrade operations.

Review:
- decision: N/A

Known gaps:
- `SPEC-304` implementation needs review approval before merge/deploy handoff.

### 2026-08-18 — Repository workflow — Merge memory checkpoint required

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Confirmed the existing memory harness had review-time helpers, but no explicit post-merge checkpoint.
- Added `make merge-memory-check SPEC=SPEC-XXX` and documented that merge actors must update project memory after PR merges, direct merges, production deploys, or branch cleanup changes current state.
- Updated `AGENTS.md`, harness docs, workflow notes, and `ADR-005` so future agents treat stale post-merge memory as a workflow violation.

Validation:
- command: `make merge-memory-check SPEC=<latest merged spec>`: PASS — merge memory for the latest merged feature is structurally valid.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- The target validates required merge-memory shape; it does not automatically infer semantic truth from GitHub. Agents must still record factual PR, commit, validation, and known-gap details.

### 2026-08-17 — SPEC-305 — Project clients and tickets merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #16 https://github.com/RGAlvaro/opdesk/pull/16, merge `ba140d3`
Status: Merged

Summary:
- Merged `SPEC-305` into `main` through PR #16 after local review approval and GitHub Actions validation.
- Confirmed `main` includes migrations `0010` and `0011`, restricted client accounts, project client access, client ticket list/create/detail/comment flows, internal ticket management, target-accepted ticket handoff requests, notifications, frontend route coverage, ADRs, and project memory updates.
- Left `SPEC-304` as the next Ready implementation target; production remains on the previously deployed `SPEC-306` revision until a release workflow deploys the merged client-ticket work.

Validation:
- command: `gh pr checks 16`: PASS — `verify` passed in 1m49s and `e2e` passed in 2m29s.
- command: `gh pr view 16 --json number,state,mergedAt,mergeCommit,url`: PASS — PR #16 is `MERGED` with merge commit `ba140d3`.
- command: `git status -sb`: PASS — local `main` clean and aligned with `origin/main`.

Review:
- decision: APPROVED — review entry below approved `SPEC-305` before merge.

Known gaps:
- `SPEC-305` is merged but not yet deployed to production.

### 2026-08-17 — SPEC-305 — Project clients and tickets approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-reviewed `SPEC-305` after the accept-time assignment eligibility fix.
- Confirmed restricted client accounts, project client access, client-created ticket tasks, ticket comments, aggregate ticket-comment notifications, assignment requests, target-only accept/decline, tenant-safe pending assignment listing, project-settings client management, client shell, and ticket workflow UI align with the implemented spec.
- Confirmed both prior review gaps are fixed: pending handoff listing revalidates current access, and accept-time handoff resolution revalidates explicit assignment eligibility before changing `assignee_id`.

Validation:
- command: `make test-backend`: PASS — 100 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 58 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through head and check reported no new upgrade operations.
- command: `make memory-check SPEC=SPEC-305`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-08-17 — SPEC-305 — Accept-time assignment eligibility fixed

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed the remaining `SPEC-305` accept-time handoff gap by revalidating current explicit project assignment eligibility before accepting a pending assignment request and changing `ticket.assignee_id`.
- Added a regression test proving an organization admin target who loses explicit project membership before accepting cannot become the ticket assignee and leaves the request pending.

Validation:
- command: `cd backend && poetry run pytest tests/test_client_tickets_api.py -q`: PASS — 8 SPEC-305 backend tests passed.
- command: `make test-backend`: PASS — 100 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 58 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through head and check reported no new upgrade operations.

Review:
- decision: N/A

Known gaps:
- `SPEC-305` accept-time assignment eligibility fix is implemented and needs re-review.

### 2026-08-17 — SPEC-305 — Assignment isolation fix re-reviewed

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-305` assignment-request isolation fix.
- Confirmed pending assignment request listing now revalidates current project and organization membership before returning embedded ticket metadata.
- Found one remaining blocking gap: accepting a pending assignment request revalidates internal project visibility but does not revalidate current explicit assignment eligibility before setting `ticket.assignee_id = actor.id`.

Validation:
- command: `make test-backend`: PASS — 99 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 58 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through head and check reported no new upgrade operations.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- `accept_assignment_request` must call the same assignee eligibility policy used for direct assignment before changing `assignee_id`, and tests should cover a target who loses project assignment eligibility before accepting.

### 2026-08-17 — SPEC-305 — Assignment request listing isolation fixed

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed the remaining `SPEC-305` re-review gap by making pending ticket assignment request listing join through ticket tasks, project memberships, and organization memberships.
- Added a regression test proving a target user removed from the project no longer receives pending handoff ticket metadata in `/api/v1/ticket-assignment-requests`.

Validation:
- command: `cd backend && poetry run pytest tests/test_client_tickets_api.py -q`: PASS — 7 SPEC-305 backend tests passed.
- command: `make test-backend`: PASS — 99 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 58 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through head and check reported no new upgrade operations.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-305` assignment-request isolation fix is implemented and needs re-review.

### 2026-08-17 — SPEC-305 — Review fixes re-reviewed

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-reviewed `SPEC-305` after the assignment-request review fixes.
- Confirmed the previous review findings were addressed: assigned workers can update assigned ticket status/priority, client management moved to project settings, ticket detail shows assignment state, and frontend ticket workflow coverage was expanded.
- Found one remaining blocking gap: pending assignment request listing returns ticket metadata for any matching `target_user_id` without revalidating current organization/project membership, so a user removed after request creation can still see pending handoff ticket data.

Validation:
- command: `cd backend && poetry run pytest tests/test_client_tickets_api.py -q`: PASS — 6 SPEC-305 backend tests passed.
- command: `make memory-check SPEC=SPEC-305`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Revalidate project/organization access when listing pending ticket assignment requests, and add a regression test for revoked target membership.

### 2026-08-17 — SPEC-305 — Review fixes implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Updated `SPEC-305` to capture the clarified assignment rule: owner/admin users can assign directly, while the currently assigned worker must request reassignment and the target worker must accept before `assignee_id` changes.
- Added ticket assignment request persistence, notification type `ticket.assignment_requested`, API schemas/routes for create/list/accept/decline, and service/repository policy enforcing target-only resolution.
- Allowed assigned workers to update assigned ticket status/priority while requiring reassignment requests for worker-initiated handoffs.
- Moved project client management to project settings, added assignment state to ticket detail, added a pending assignment requests route, and expanded frontend tests for client management, client ticket creation/detail/comments, internal ticket visibility, and assignment requests.
- Added Alembic migration `0011` for ticket assignment requests because local migration `0010` had already been applied before this review-fix scope.

Validation:
- command: `make test-backend`: PASS — 98 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 58 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through `0011` and check reported no new upgrade operations.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-305` review fixes are implemented and need re-review before approval/deployment.

### 2026-08-17 — SPEC-305 — Project clients and tickets reviewed

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-305` implementation against restricted client-account behavior, ticket APIs, ticket comments, assignment/update permissions, frontend placement, required frontend coverage, migrations, and project memory.
- Found blocking gaps: assigned workers cannot update assigned ticket fields, client management is rendered on project detail instead of project settings, frontend ticket detail omits assignment state, and required frontend tests do not cover client management, ticket creation/detail/comments, or internal ticket visibility.

Validation:
- command: `make test-backend`: PASS — 96 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 53 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: elevated `make migrations-check`: PASS — Alembic upgrade/check reported no new upgrade operations.
- command: `make memory-check SPEC=SPEC-305`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Assigned worker ticket update permission and corresponding tests are missing.
- Project client management must move to project settings or the spec must be changed before approval.
- Frontend client-ticket workflows need the required coverage from `SPEC-305`.

### 2026-08-17 — SPEC-305 — Project clients and tickets implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added migration `0010` for `users.account_type`, `tasks.client_user_id`, `task_type=ticket`, `project_client_accesses`, `ticket_comments`, and `ticket.comment` notifications.
- Added backend client-ticket models, repository, schemas, service, and routes for owner/admin client grants/revocation, client project/ticket endpoints, internal ticket listing/update, ticket comments, assignment eligibility, revoked-access behavior, and aggregate unread ticket-comment notifications.
- Updated generic task handling so tickets cannot be created through normal task APIs.
- Added frontend client ticket hooks/pages, restricted client app-shell navigation, login redirect for client accounts, project client management, internal ticket lists/details, and ticket comment forms.
- Added backend SPEC-305 API tests and frontend route coverage for the client shell.

Validation:
- command: `make test-backend`: PASS — 96 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 53 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy and frontend `tsc -b` passed.
- command: elevated temporary PostgreSQL `alembic upgrade head`: PASS — created `opdesk_spec305_migration_check`, applied migrations `0001` through `0010`, and dropped the temporary database after validating enum additions from scratch.
- command: elevated local PostgreSQL enum alignment: PASS — applied non-destructive `ALTER TYPE ... ADD VALUE IF NOT EXISTS` for `task_type=ticket` and `notification_type=ticket.comment` because the local database had already run the first draft of migration `0010`.
- command: elevated `make migrations-check`: PASS — Alembic upgraded through `0010` and check reported no new upgrade operations.

Review:
- decision: N/A

Known gaps:
- `SPEC-305` is implemented but not reviewed; production deployment remains pending.

### 2026-08-17 — SPEC-304/SPEC-305 — Collaboration specs readied

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Readied `SPEC-305` around restricted OpsDesk client accounts, owner/admin project client grants, client-owned ticket tracking, assignment to internal project members, ticket status visibility, and ticket detail comments/feedback.
- Readied `SPEC-304` around internal-only organization chat with WebSocket delivery, direct messages, organization channels, project channels, shared-project member ordering, indefinite retention, per-user conversation clearing, and aggregate unread conversation notifications.
- Added `ADR-011` for client accounts and ticket access and `ADR-012` for WebSocket chat transport.
- Updated spec routing and project memory so `SPEC-305` is the next implementation target before `SPEC-304`.

Validation:
- command: `make memory-check SPEC=SPEC-305`: PASS.
- command: `make memory-check SPEC=SPEC-304`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- Product implementation has not started; `SPEC-305` should be implemented before `SPEC-304`.

### 2026-08-14 — SPEC-307 — SPEC-306 deployed to production

Role: Ingeniero de software
Branch: main
Commit/PR: commit `926c0c1`, Production Release run `31793554991`
Status: Merged

Summary:
- Deployed `SPEC-306` app revision `926c0c16dbbca07213085cf942c5f9f49fac1101` to the production VPS through the `Production Release` workflow.
- The workflow passed repository verification, frontend build, production Compose config validation, release workflow validation, changelog validation, SSH upload, and remote production update.
- The remote release manifest records backup creation, Alembic `0009 (head)`, Compose update, backend health, frontend, Redis, and worker checks as PASS.

Validation:
- command: `gh run watch 31793554991 --interval 20 --exit-status`: PASS — Production Release completed in 2m54s.
- command: `curl -fsS https://rgalvaro.es/health`: PASS — returned `{"status":"ok"}`.
- command: `curl -I -fsS https://rgalvaro.es/`: PASS — returned `HTTP/2 200` through Caddy/nginx.
- command: `ssh opdesk-vps 'cat /srv/opdesk/releases/latest-release.txt'`: PASS — manifest recorded `release_ref=926c0c16dbbca07213085cf942c5f9f49fac1101`, backup `/srv/opdesk/backups/opdesk-20260814-104816-926c0c16dbbca07213085cf942c5f9f4.dump`, `alembic_current=0009 (head)`, `compose_update=PASS`, `backend_health=PASS`, `frontend=PASS`, `redis=PASS`, and `worker=PASS`.

Review:
- decision: N/A

Known gaps:
- This post-deploy memory entry is documentation-only and does not require another app deploy.

### 2026-08-14 — SPEC-307 — Production frontend build context fix

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Production Release run `31792683181` passed validation, created a production backup, built the backend image, and applied migrations through Alembic `0009`.
- The remote production update then failed during `docker compose up -d --build` because `frontend/Dockerfile` copied `nginx.conf` from the production root build context while the file lives under `frontend/nginx.conf`.
- Updated the production Dockerfile copy path so the frontend image can build from the root context used by `docker-compose.prod.yml`.

Validation:
- command: `gh run watch 31792683181 --interval 20 --exit-status`: FAIL — remote update failed after migrations during frontend image build.
- command: elevated `docker compose --project-name opdesk-prod-smoke --env-file .env.example -f docker-compose.prod.yml build frontend`: PASS — production frontend image builds with `frontend/nginx.conf` copied from the root build context.
- command: `make memory-check SPEC=SPEC-307`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- Production database is at Alembic `0009`; production app update remains pending until the fixed frontend production image builds and the release workflow passes.

### 2026-08-14 — SPEC-307 — SPEC-306 production release validation fix

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Triggered `Production Release` for `main` after the `SPEC-306` release readiness commit.
- GitHub Actions run `31792406644` stopped before production deployment during `Run full verification`.
- Root cause was a frontend changelog test that assumed only one `Added` heading after the new `2026-08-14 - Notification Inbox Release` changelog entry.
- Updated the changelog route test to assert the new release entry and allow multiple `Added` section headings.

Validation:
- command: `gh run watch 31792406644 --interval 20 --exit-status`: FAIL — full verification failed before backup, migration, SSH, or remote production update.

Review:
- decision: N/A

Known gaps:
- Production deployment remains pending until the fixed `main` revision passes the release workflow.

### 2026-08-14 — SPEC-306 — In-app notifications merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #15 https://github.com/RGAlvaro/opdesk/pull/15, merge `7084fd5`
Status: Merged

Summary:
- Merged `SPEC-306` into `main` through PR #15 after local review approval and GitHub Actions validation.
- Confirmed `main` includes migration `0009`, notification APIs, invitation/project/task fan-out, frontend inbox, tests, and project memory updates.
- Added `CHANGELOG.md` entry `2026-08-14 - Notification Inbox Release` required by the production release workflow.

Validation:
- command: `gh pr checks 15`: PASS — `verify` passed in 1m45s and `e2e` passed in 2m12s.
- command: `git status -sb`: PASS — local `main` clean and aligned with `origin/main` before post-merge memory/changelog correction.

Review:
- decision: APPROVED — review entry below approved before merge.

Known gaps:
- Production deployment remains pending for the current `main` revision.

### 2026-08-14 — SPEC-306 — In-app notifications reviewed

Role: Review agent
Branch: agent/spec-306-in-app-notifications
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-306` implementation against the readied polling inbox scope, API conventions, migration requirements, permission isolation, invitation reuse, project/task recipient rules, frontend unread state, and required project memory.
- Confirmed chat missed-message notifications are explicitly deferred until `SPEC-304` defines chat persistence and recipient state.
- Confirmed no external notification delivery, preference, deletion, retention cleanup, or realtime transport decision was introduced outside the active spec.

Validation:
- command: `make test-backend`: PASS — 92 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 52 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `make typecheck`: PASS — backend mypy passed and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — migration `0009` applied and Alembic check reported no new upgrade operations.
- command: `docker compose up -d --build backend worker`: PASS — backend and worker images rebuilt so Compose included migration `0009`.
- command: elevated `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the backend container after rebuild.
- command: `python3 -m compileall backend/alembic/versions backend/app`: PASS.
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-306`: PASS.

Review:
- decision: APPROVED

Known gaps:
- Chat missed-message notifications remain deferred until `SPEC-304` defines chat persistence and recipient state.
- Notification preferences, deletion, external delivery, retention cleanup, and WebSockets/SSE remain future scope.

### 2026-08-14 — SPEC-306 — In-app notifications implemented

Role: Ingeniero de software
Branch: agent/spec-306-in-app-notifications
Commit/PR: Pending
Status: Implemented

Summary:
- Readied `SPEC-306` by resolving polling, retention, recipient, invitation-surface, and chat-deferral questions before implementation.
- Added migration `0009` and persistent `notifications` backend model/repository/schema/service/API for current-user listing, unread count, mark-read, mark-unread, and mark-all-read.
- Connected notification creation to `SPEC-303` organization/project invitations, project membership grants, project visible-state changes, task creation/assignment, and task status changes.
- Added authenticated notification inbox UI at `/app/notifications` with unread badge in the app shell, read toggles, mark-all-read, and action links to the existing invitation flow.
- Added backend API/service tests and frontend route tests for unread state, inbox list, mark-read, action navigation, invitation integration, project/task fan-out, and non-recipient isolation.

Validation:
- command: `make test-backend`: PASS — 92 selected tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 52 frontend tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed after formatting new files.
- command: `make typecheck`: PASS — backend mypy passed and frontend `tsc -b` passed.
- command: elevated `make migrations-check`: PASS — migration `0009` applied and Alembic check reported no new upgrade operations.
- command: `docker compose up -d --build backend worker`: PASS — backend and worker images rebuilt so Compose included migration `0009`.
- command: elevated `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the backend container after rebuild; the first attempt failed because the old backend image could not locate revision `0009`.
- command: `python3 -m compileall backend/alembic/versions backend/app`: PASS.
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-306`: PASS.

Review:
- decision: N/A

Known gaps:
- Chat missed-message notifications remain deferred until `SPEC-304` defines chat persistence and recipient state.
- Notification preferences, deletion, external delivery, retention cleanup, and WebSockets/SSE remain future scope.

### 2026-08-14 — SPEC-303 — Compose migration validation rerun

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Rebuilt and recreated the Docker Compose backend and worker images so the containers included migration `0008`.
- Reran Compose-based migration validation successfully after the old backend image initially could not locate revision `0008`.

Validation:
- command: `docker compose up -d --build backend worker`: PASS — backend and worker images rebuilt and containers recreated.
- command: elevated `make migrations-check-compose`: PASS — Alembic upgrade ran inside the backend container and `alembic check` reported no new upgrade operations.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-08-14 — SPEC-303 — Review fix for stale project membership assignment

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed review-found stale-access risk where removing an organization membership could leave explicit project membership rows usable for task assignment.
- Organization member removal now removes that user's explicit project memberships in the organization.
- Task assignee validation now requires both explicit project membership and current organization membership.
- Added a regression test for removing an organization member and rejecting later task assignment to that user.

Validation:
- command: `make test-backend`: PASS — 89 passed, 2 deselected.
- command: `make typecheck`: PASS — backend mypy passed and frontend `tsc -b` passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-08-14 — SPEC-303 — Member invitations and project access implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added migration `0008` plus SQLAlchemy models for `invitations` and `project_memberships`, including pending-invitation uniqueness and existing-project membership backfill.
- Added backend invitation APIs for organization invites, project invites, current-user invitation list, accept, decline, cancellation, project member listing, and project member removal.
- Restricted regular members to explicit project membership for project/task access and changed task assignee validation to require explicit project membership.
- Added frontend organization invite controls, organization invitation list/cancellation, project member/invite controls, primary-nav access to `/app/invitations`, and a minimal My invitations accept/decline page.
- Added backend SPEC-303 API tests and frontend invitation UI tests, and updated older project/task notification tests to seed explicit project memberships where the new contract requires them.

Validation:
- command: `make test-backend`: PASS — 88 passed, 2 deselected.
- command: `make test-frontend`: PASS — 51 passed.
- command: `make typecheck`: PASS — backend mypy passed and frontend `tsc -b` passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed after migration import ordering fix.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier check passed.
- command: `python3 -m compileall backend/alembic/versions backend/app`: PASS.
- command: elevated `make migrations-check`: PASS — migration `0008` applied and Alembic check reported no new upgrade operations after replacing the reused `membership_role` column type with `postgresql.ENUM(..., create_type=False)`.
- command: elevated `make migrations-check-compose`: PASS on rerun after rebuilding backend/worker images; the initial failure came from the old backend image not knowing revision `0008`.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-08-14 — SPEC-303 — Member invitations and project access readied

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Refined `SPEC-303` from Draft to Ready for existing-user organization invitations, project invitations, explicit project memberships, and regular-member project visibility restrictions.
- Resolved admin invite permissions: owners may invite admins or members; admins may invite only members.
- Removed task invitations from `SPEC-303`; task assignment now depends on explicit project membership.
- Added migration backfill requirements so existing organization members retain access to existing projects.
- Defined a minimal “My invitations” flow owned by `SPEC-303` and updated `SPEC-306` to integrate those invitations later in the full notification inbox.

Validation:
- command: `make memory-check SPEC=SPEC-303`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-303` implementation remains pending.
- `SPEC-306` still needs future notification inbox decisions and must later reuse the `SPEC-303` invitation state.

### 2026-08-13 — SPEC-312 — Playwright E2E expansion merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #13 https://github.com/RGAlvaro/opdesk/pull/13, merge `9b020cc`
Status: Merged

Summary:
- Pushed `agent/spec-312-playwright-e2e-expansion`, opened PR #13, marked it ready after checks passed, and merged it into `main`.
- Confirmed GitHub Actions `Verify` run `31686532597` passed both the existing `verify` job and the new separate `e2e` job.
- Fast-forwarded local `main` to the merge commit.

Validation:
- command: `gh pr checks 13 --watch --interval 20`: PASS — `e2e` passed in 2m17s and `verify` passed in 1m49s.
- command: `git pull --ff-only`: PASS — local `main` updated to `9b020cc`.
- command: `gh run watch 31687118950 --interval 20 --exit-status`: PASS after rerun — initial post-memory-push `e2e` failed because Docker Hub returned `500 Internal Server Error` while fetching image auth tokens; rerun passed with `e2e` in 2m15s and `verify` in 1m50s on `5c1dac0`.
- command: `gh run watch 31691528101 --interval 20 --exit-status`: PASS — latest `main` memory commit `6422080` passed with `e2e` in 2m18s and `verify` in 1m40s.

Review:
- decision: APPROVED — review entry below approved before merge.

Known gaps:
- Firefox/WebKit, visual snapshots, and dedicated accessibility audits remain future E2E scope.

### 2026-08-13 — SPEC-312 — Playwright E2E expansion reviewed

Role: Review agent
Branch: agent/spec-312-playwright-e2e-expansion
Commit/PR: `d088295`, PR #13 https://github.com/RGAlvaro/opdesk/pull/13, merge `9b020cc`
Status: Reviewed

Summary:
- Reviewed the expanded Playwright suite against `SPEC-312` acceptance criteria for auth route protection, login/logout, profile persistence, task filter URL persistence, label filtering, desktop Chromium, mobile Chromium critical path, CI artifact handling, and Docker/local harness behavior.
- Confirmed E2E setup uses unique test data through public product APIs and browser UI behavior without direct database mutation or destructive cleanup.
- Confirmed `make verify` remains separate from E2E, while the new GitHub Actions `e2e` job runs `make test-e2e` and uploads Playwright artifacts only on failure.
- Confirmed project memory, spec index, and harness docs reflect the implemented state and residual E2E gaps.

Validation:
- command: `make memory-check SPEC=SPEC-312`: PASS.
- command: `git diff --check`: PASS.
- command: implementation evidence reviewed: `make test-e2e`, `make lint`, `make format-check`, `make typecheck`, `make test-frontend`, `make smoke`, `make prod-config`, and `cd frontend && npm run build` all recorded as PASS in the implementation entry.

Review:
- decision: APPROVED

Known gaps:
- Firefox/WebKit, visual snapshots, and dedicated accessibility audits remain future E2E scope.

### 2026-08-13 — SPEC-312 — Playwright E2E expansion implemented

Role: Ingeniero de software
Branch: agent/spec-312-playwright-e2e-expansion
Commit/PR: `d088295`, PR #13 https://github.com/RGAlvaro/opdesk/pull/13, merge `9b020cc`
Status: Implemented

Summary:
- Added shared Playwright E2E helpers for unique users, API-backed setup, authenticated sessions, organizations, projects, tasks, labels, and app-shell assertions.
- Added desktop Chromium E2E coverage for anonymous protected-route redirects, login/logout/post-logout protection, profile update persistence, task filter URL persistence, and label filtering.
- Expanded the critical signup-to-completed-task flow to run on both desktop Chromium and a mobile Chromium viewport.
- Added a separate GitHub Actions `e2e` job that runs `make test-e2e` and uploads Playwright failure artifacts from `frontend/test-results`.
- Updated Playwright harness docs to describe the expanded suite, CI split, and artifact behavior.

Validation:
- command: `make test-e2e`: PASS — Compose stack built, backend Alembic upgrade/check passed, and 6 Playwright tests passed across desktop Chromium plus mobile Chromium critical path.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make test-frontend`: PASS — 47 frontend tests passed.
- command: `make smoke`: PASS — Docker/local backend health, Redis, worker, Adminer, and Vite frontend checks passed.
- command: `make prod-config`: PASS.
- command: `cd frontend && npm run build`: PASS.

Review:
- decision: APPROVED — reviewed on 2026-08-13.

Known gaps:
- Firefox/WebKit browser projects, visual snapshot testing, and accessibility audits remain outside `SPEC-312`.

### 2026-08-13 — SPEC-312 — Playwright E2E expansion specified

Role: Arquitecto de specs
Branch: agent/spec-312-playwright-e2e-expansion
Commit/PR: `d088295`, PR #13 https://github.com/RGAlvaro/opdesk/pull/13, merge `9b020cc`
Status: Ready

Summary:
- Added Ready `SPEC-312` for expanding Playwright E2E coverage after the initial critical path.
- Scoped the next E2E phase to auth protection, login/logout, profile update persistence, task filter URL persistence, label filtering, desktop Chromium, mobile Chromium viewport, and optional CI artifacts.
- Kept E2E separate from `make verify` for this phase and specified unique product-API-created test data rather than direct database cleanup.
- Updated the spec index, dependency order, touch-to-spec routing, and project memory handoff.

Validation:
- command: `make memory-check SPEC=SPEC-312`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — spec prepared for implementation.

Known gaps:
- Implementation has not started.

### 2026-08-12 — SPEC-104/SPEC-106 — Playwright critical E2E harness

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added Playwright browser coverage for the critical authenticated workflow from signup through organization creation, project creation, task creation, and marking the task done.
- Added `make test-e2e`, `frontend/playwright.config.ts`, and `frontend/e2e/critical-workflow.spec.ts`.
- Added a Compose `e2e` runner using the official Playwright Docker image so browser system libraries are not required on the host.
- Updated frontend Docker builds to use the repository root context with a narrow root `.dockerignore`, allowing Docker dev/production frontend images to include root `CHANGELOG.md` for the public changelog route without sending local `node_modules` into the build context.
- Added `frontend/test-results/` and `frontend/playwright-report/` to `.gitignore`.

Validation:
- command: `make test-e2e`: PASS — Compose stack built, backend Alembic upgrade/check passed, and 1 Playwright Chromium critical-path test passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make test-frontend`: PASS — 47 frontend tests passed.
- command: `make smoke`: PASS — Docker/local backend health, Redis, worker, Adminer, and Vite frontend checks passed.
- command: `make prod-config`: PASS.
- command: `cd frontend && npm run build`: PASS.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- Full cross-browser/mobile E2E coverage remains outside this hardening pass.

### 2026-08-12 — SPEC-301 — Production hostname cleanup and VPS reboot

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Removed the temporary `opdesk.51.255.202.88.sslip.io` Caddy fallback from the VPS-side `/srv/opdesk/.env.production` after confirming `rgalvaro.es` and `www.rgalvaro.es` were healthy.
- Backed up the server-side env file to `/srv/opdesk/.env.production.pre-hostname-cleanup-20260812-093900` before editing.
- Recreated only the production Caddy container from the active release directory so the hostname change applied without rebuilding app services.
- Completed the controlled VPS reboot for the pending Ubuntu kernel upgrade.

Validation:
- command: pre-change `curl -fsS https://rgalvaro.es/health`, `curl -I -fsS https://rgalvaro.es/`, `curl -fsS https://www.rgalvaro.es/health`, and `curl -I -fsS https://www.rgalvaro.es/`: PASS.
- command: pre-change `ssh opdesk-vps`: PASS — confirmed `REBOOT_REQUIRED=yes` and `CADDY_SITE_ADDRESS=rgalvaro.es, www.rgalvaro.es, opdesk.51.255.202.88.sslip.io`.
- command: remote Caddy hostname cleanup: PASS — `.env.production` backup created, `CADDY_SITE_ADDRESS=rgalvaro.es, www.rgalvaro.es`, and `docker compose ... up -d --no-deps caddy` recreated Caddy.
- command: post-cleanup `curl -fsS https://rgalvaro.es/health`, `curl -I -fsS https://rgalvaro.es/`, `curl -fsS https://www.rgalvaro.es/health`, and `curl -I -fsS https://www.rgalvaro.es/`: PASS.
- command: post-cleanup `curl -fsS --max-time 15 https://opdesk.51.255.202.88.sslip.io/health`: EXPECTED FAIL — TLS internal alert confirms Caddy no longer serves that hostname.
- command: `ssh opdesk-vps 'sudo reboot'`: PASS.
- command: post-reboot public smoke: PASS — `https://rgalvaro.es/health` and `https://www.rgalvaro.es/health` returned `{"status":"ok"}`, both frontend routes returned `HTTP/2 200`, and unauthenticated `/api/v1/users/me` returned the expected `401 not_authenticated` envelope.
- command: post-reboot `ssh opdesk-vps`: PASS — uptime since `2026-08-12 09:39:36`, `REBOOT_REQUIRED=no`, `CADDY_SITE_ADDRESS=rgalvaro.es, www.rgalvaro.es`, production Compose services running, backend/PostgreSQL/Redis healthy, Redis `PONG`, and worker running.
- command: `make memory-check SPEC=SPEC-301`: PASS.
- command: `make prod-config`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — operational cleanup completed for already implemented `SPEC-301`.

Known gaps:
- None.

### 2026-08-12 — SPEC-311 — Public portfolio home merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #12 https://github.com/RGAlvaro/opdesk/pull/12, merge commit af9535e
Status: Merged

Summary:
- Marked PR #12 ready after the `SPEC-311` review approval, retargeted it from the merged `SPEC-310` branch to `main`, and merged it with a clean GitHub merge state.
- Fast-forwarded local `main` to `af9535e`.
- Deleted the merged local and remote `agent/spec-311-public-portfolio-home` branches.

Validation:
- command: GitHub PR #12 merge-state check: PASS — merge state `CLEAN` before merge.
- command: GitHub Actions `Verify` run `31581961980`: PASS — merge commit `af9535e23e9a46d01332dda0eadd07a917a40e5b`.
- command: `git pull --ff-only origin main`: PASS — local `main` fast-forwarded through `af9535e`.
- command: `git branch -d agent/spec-311-public-portfolio-home`: PASS.
- command: `git push origin --delete agent/spec-311-public-portfolio-home`: PASS.

Review:
- decision: APPROVED — merged after approved review.

Known gaps:
- None.

### 2026-08-12 — SPEC-310 — Release changelog merged

Role: Ingeniero de software
Branch: main
Commit/PR: PR #11 https://github.com/RGAlvaro/opdesk/pull/11, merge commit f0849fe
Status: Merged

Summary:
- Marked PR #11 ready after the `SPEC-310` review approval and merged it to `main` with a clean GitHub merge state.
- Fast-forwarded local `main` through the merge commit before the dependent `SPEC-311` merge.
- Deleted the merged local and remote `agent/spec-310-release-changelog` branches.

Validation:
- command: GitHub PR #11 merge-state check: PASS — merge state `CLEAN` before merge.
- command: GitHub Actions `Verify` run `31581706174`: PASS — merge commit `f0849fe2c16c4c6ee07c39d4d6aaaf3d967a0a4a`.
- command: `git pull --ff-only origin main`: PASS — local `main` fast-forwarded through `f0849fe`.
- command: `git branch -d agent/spec-310-release-changelog`: PASS.
- command: `git push origin --delete agent/spec-310-release-changelog`: PASS.

Review:
- decision: APPROVED — merged after approved review.

Known gaps:
- None.

### 2026-08-12 — SPEC-311 — Public portfolio home reviewed

Role: Review agent
Branch: agent/spec-311-public-portfolio-home
Commit/PR: 86f03ed
Status: Reviewed

Summary:
- Reviewed the `SPEC-311` implementation against the public portfolio home, OpsDesk available card, ERP coming-soon card, changelog navigation, static/no-backend rendering, existing auth route behavior, generated visual asset, tests, and project memory.
- Confirmed `/` is now public without session bootstrap, while `/login`, `/signup`, and `/app` keep the existing auth guard behavior.
- Confirmed the ERP card is clearly marked `Coming soon` and exposes no fake app navigation.
- Confirmed the generated portfolio bitmap has no legible text, logos, or fake product claims and builds into the frontend production bundle.

Validation:
- command: `make test-frontend`: PASS — 47 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make memory-check SPEC=SPEC-311`: PASS.
- command: `make smoke`: PASS — Docker/local backend health, Redis, worker, Adminer, and Vite frontend checks passed.
- command: `cd frontend && npm run build`: PASS.
- command: `git diff --check agent/spec-310-release-changelog...HEAD`: PASS.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-08-12 — SPEC-311 — Public portfolio home implemented

Role: Ingeniero de software
Branch: agent/spec-311-public-portfolio-home
Commit/PR: Pending
Status: Implemented

Summary:
- Resolved the `SPEC-311` Draft questions in the spec with recruiter-facing software-engineer copy and OpsDesk primary action to `/login` with `/signup` secondary.
- Replaced the OpsDesk-only public landing page with a static portfolio/app hub that does not require session bootstrap to render.
- Added an OpsDesk available app card, a Small-team ERP `Coming soon` card with no fake app navigation, and public changelog links.
- Added a generated portfolio hub bitmap asset at `frontend/src/assets/portfolio-hub.png` and wired it into the first viewport.
- Updated frontend route tests for portfolio copy, app cards, changelog link, ERP no-link behavior, and logout returning to the new home.

Validation:
- command: `make test-frontend`: PASS — 47 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS after Prettier fixed route files.
- command: `make typecheck`: PASS.
- command: `make smoke`: PASS — Docker/local backend health, Redis, worker, Adminer, and Vite frontend checks passed.
- command: `cd frontend && npm run build`: PASS.
- command: `make memory-check SPEC=SPEC-311`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- None.

### 2026-08-12 — SPEC-310 — Release changelog reviewed

Role: Review agent
Branch: agent/spec-310-release-changelog
Commit/PR: 1fe6784
Status: Reviewed

Summary:
- Reviewed the `SPEC-310` implementation against changelog format, public unauthenticated rendering, production workflow changelog enforcement, docs, tests, and project memory.
- Confirmed `CHANGELOG.md` is root-scoped, newest-first, uses only populated `Added`, `Changed`, and `Fixed` sections, and contains no secret-like content.
- Confirmed the manual production workflow validates the requested `changelog_entry` before production secrets, SSH configuration, archive upload, or remote deploy steps.
- Confirmed `/changelog` renders the repository changelog content as bundled static frontend content and is covered by a public route/link test.

Validation:
- command: `make release-workflow-check`: PASS.
- command: `make test-frontend`: PASS — 46 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make memory-check SPEC=SPEC-310`: PASS.
- command: `git diff --check main...HEAD`: PASS.
- command: `cd frontend && npm run build`: PASS.
- command: `python3 scripts/validate_changelog.py --entry "2099-01-01 - Missing Release"`: EXPECTED FAIL — missing changelog entry exits non-zero before deploy use.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-08-12 — SPEC-310 — Release changelog implemented

Role: Ingeniero de software
Branch: agent/spec-310-release-changelog
Commit/PR: Pending
Status: Implemented

Summary:
- Added root `CHANGELOG.md` with newest-first production release notes in `Added`, `Changed`, and `Fixed` sections.
- Added deterministic changelog validation for heading format, allowed sections, required bullets, newest-first order, and secret-like content guards.
- Updated the manual production release workflow so real deploys require a `changelog_entry` matching `CHANGELOG.md` before production secrets, SSH setup, archive upload, or remote update steps run.
- Added public `/changelog` frontend route backed by the repository changelog, linked it from the public landing page, and covered the route/link with frontend tests.
- Documented changelog validation in the local harness and production release docs.

Validation:
- command: `make release-workflow-check`: PASS.
- command: `python3 scripts/validate_changelog.py --entry "2026-08-12 - Production Release"`: PASS.
- command: `make test-frontend`: PASS — 46 frontend tests passed.
- command: `make typecheck`: PASS.
- command: `make lint`: PASS.
- command: `make format-check`: PASS after Prettier fixed two frontend files.
- command: `make memory-check SPEC=SPEC-310`: PASS.
- command: `git diff --check`: PASS.
- command: `cd frontend && npm run build`: PASS.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- None.

### 2026-08-12 — SPEC-309 — Project task labels merged

Role: Ingeniero de software
Branch: main
Commit/PR: 5d94836
Status: Merged

Summary:
- Merged `agent/spec-309-task-labels` into `main` by fast-forward after review approval and pushed `main` to `origin`.
- Deleted the merged local and remote `agent/spec-309-task-labels` branches.

Validation:
- command: `make test-frontend`: PASS — 45 frontend tests passed before merge.
- command: `make test-backend`: PASS — 83 selected backend tests passed, 2 DB tests deselected before merge.
- command: `make lint`: PASS before merge.
- command: `make format-check`: PASS before merge.
- command: `make typecheck`: PASS before merge.
- command: `make memory-check SPEC=SPEC-309`: PASS before merge.
- command: `git diff --check`: PASS before merge.

Review:
- decision: APPROVED — merged after approved re-review.

Known gaps:
- None.

### 2026-08-12 — SPEC-309 — Project task labels re-reviewed

Role: Review agent
Branch: agent/spec-309-task-labels
Commit/PR: 5d94836
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-309` review fixes against the frontend label permissions, task label assignment, archived-label visibility, test coverage, and project memory requirements.
- Confirmed project label management is reachable from project detail for regular project-visible members while owner/admin-only project settings remain restricted.
- Confirmed the added frontend tests cover regular-member label creation, local color validation, task label assignment, archived-label display, and existing label filter URL state.
- Marked `SPEC-309` implemented in the spec index and feature spec after approval.

Validation:
- command: `make test-frontend`: PASS — 45 frontend tests passed.
- command: `make test-backend`: PASS — 83 selected backend tests passed, 2 DB tests deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make memory-check SPEC=SPEC-309`: PASS.
- command: `git diff --check`: PASS.
- command: `make migrations-check`: NOT RUN — no backend model or Alembic changes in this frontend-only review fix; latest `SPEC-309` migration validation remains the 2026-08-11 PASS.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-08-12 — SPEC-309 — Project task labels review fixes

Role: Ingeniero de software
Branch: agent/spec-309-task-labels
Commit/PR: Pending
Status: Implemented

Summary:
- Moved frontend project label management from owner/admin-only project settings to the project detail page so regular project-visible team members can reach label creation and archive controls.
- Added local `#RRGGBB` label color validation with a visible color swatch before project label creation.
- Added frontend route coverage for regular-member label creation, label color validation, task label assignment, archived-label display, and the existing label filter URL state.

Validation:
- command: `make test-frontend`: PASS — 45 frontend tests passed.
- command: `make test-backend`: PASS — 83 selected backend tests passed, 2 DB tests deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.

Review:
- decision: N/A — review fixes pending re-review.

Known gaps:
- `SPEC-309` still needs re-review approval.
- Migration validation was not rerun for this frontend-only review fix; the latest `SPEC-309` migration validation remains the 2026-08-11 passing `make migrations-check` run.

### 2026-08-11 — SPEC-309 — Project task labels review

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the local `SPEC-309` implementation against backend API, migration, frontend UI, tests, and project memory.
- Backend label persistence, API behavior, task label assignment, task filtering, migration drift check, and backend tests are broadly aligned.
- Requested changes because the frontend label management UI is only reachable for owner/admin project settings users, while `SPEC-309` requires project team members to create/manage labels, and required frontend coverage is missing for label management, color validation, task label assignment, and archived-label display.

Validation:
- command: `make test-backend`: PASS — 83 selected backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 41 frontend tests passed.
- command: `make migrations-check`: PASS — Alembic upgraded to head and reported no new upgrade operations.
- command: `make memory-check SPEC=SPEC-309`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Frontend label management must be available to project team members, not only owner/admin project-settings users.
- Frontend tests must cover label management UI, color validation, task label assignment, archived-label display, and label filter URL state.

### 2026-08-11 — SPEC-309 — Project task labels implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added project-scoped task label persistence with migration `0007`, active-label case-insensitive uniqueness per project, archived-label state, and task-label assignment rows.
- Added label APIs for project label list/create/update/archive and task label apply/remove, plus task responses and project task filtering by `label_id`.
- Added backend API coverage for label metadata validation, duplicate handling, cross-project and archived-label assignment rejection, task update permissions, tenant isolation, and label filtering.
- Added frontend label management in project settings, task label chips in list/detail, task label assignment controls, and URL-backed task filtering by label.

Validation:
- command: `make test-backend`: PASS — 83 selected backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 41 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make migrations-check`: FAIL then PASS — first elevated run applied `0007` and exposed Alembic metadata drift for the partial label-name index; model metadata was updated and the elevated rerun reported no new upgrade operations.

Review:
- decision: N/A — implementation pending review.

Known gaps:
- Review approval is still pending.

### 2026-08-11 — Harness — GitHub Actions Node 24 action updates

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Updated GitHub official actions in `verify.yml` and `production-release.yml` to Node 24-compatible major versions.
- Replaced `actions/checkout@v4`, `actions/setup-python@v5`, and `actions/setup-node@v4` with their `@v6` releases in both workflows.

Validation:
- command: `make release-workflow-check`: PASS.
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-307`: PASS.
- command: GitHub Actions `Verify` run `31516781996`: PASS — validated `b21024f` without the prior Node 20 deprecation annotation.

Review:
- decision: N/A — CI harness warning cleanup.

Known gaps:
- None.

### 2026-08-11 — SPEC-307 — Production migration drift guard added

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Hardened `scripts/prod_release.sh` so production releases run `alembic check` after `alembic upgrade head` and before replacing app containers.
- Added release-manifest evidence for `migration_drift_check=PASS` and `alembic_current=...`.
- Hardened `scripts/validate_release_workflow.py` so static release validation enforces upgrade, drift check, current revision capture, and Compose update order.

Validation:
- command: `make release-workflow-check`: PASS.
- command: `make prod-config`: PASS.
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-307`: PASS.
- command: GitHub Actions `Verify` run `31501963103`: PASS — validated commit `5a36d8e`.
- command: GitHub Actions `Production Release` run `31502139076`: PASS — deployed commit `5a36d8e10d9469c2b1d505b1f4da90a54c0add0f`.
- command: production release manifest check: PASS — recorded `backend_image_build=PASS`, `migrations=PASS`, `migration_drift_check=PASS`, `alembic_current=0006 (head)`, and `compose_update=PASS`.
- command: post-release production smoke: PASS — `https://rgalvaro.es/health` returned `{"status":"ok"}` and frontend returned `HTTP/2 200`.

Review:
- decision: N/A — release harness hardening deployed.

Known gaps:
- None.

### 2026-08-11 — SPEC-307/SPEC-308 — Production migration recovery and release-order fix

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Investigated authenticated production smoke failure after `POST /api/v1/auth/register` returned `500`.
- Confirmed production backend logs showed `users.job_title` was missing and production `alembic_version` was still `0005`.
- Applied pending production migration `0006` manually through the already-built backend image, restoring schema compatibility for SPEC-308.
- Root-caused the release automation bug: `scripts/prod_release.sh` ran Alembic before building the new backend image, so migrations from the new release were unavailable during the migration step.
- Updated `scripts/prod_release.sh` to build the backend image after backup and before Alembic, without recreating application containers before migrations.
- Hardened `scripts/validate_release_workflow.py` so release validation checks the safety-critical order: backup, backend build, migrations, Compose update.
- Ran authenticated production smoke for profile, organization, project, task metadata, task watchers, and task metadata filters.
- Deleted the smoke organizations and all smoke users created during validation.

Validation:
- command: production `alembic upgrade head` through `docker compose run --rm backend`: PASS — upgraded production from `0005` to `0006`.
- command: production authenticated API smoke: PASS — register, login, profile metadata update, organization metadata create/delete, project metadata create, task metadata/watchers create, blocked reason update, and task metadata filters passed.
- command: production smoke cleanup: PASS — deleted smoke organization slugs and smoke users created during validation.
- command: `make release-workflow-check`: PASS.
- command: `make prod-config`: PASS.
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-307`: PASS.
- command: `make memory-check SPEC=SPEC-308`: PASS.
- command: GitHub Actions `Verify` run `31500412344`: PASS — validated commit `94dbb54`.
- command: GitHub Actions `Production Release` run `31500572299`: PASS — deployed commit `94dbb542e0fe71bcf223d0f576e8b5d4e52a4252` with corrected release script.
- command: production release manifest check: PASS — recorded `backend_image_build=PASS`, `migrations=PASS`, and `compose_update=PASS`.
- command: post-release production smoke: PASS — `https://rgalvaro.es/health` returned `{"status":"ok"}`, frontend returned `HTTP/2 200`, and production Alembic remained at `0006`.

Review:
- decision: N/A — production recovery and release automation fix deployed.

Known gaps:
- None.

### 2026-08-11 — SPEC-308 — Production release executed

Role: Ingeniero de software
Branch: main
Commit/PR: `cb7692e`
Status: Implemented

Summary:
- Confirmed the latest `main` CI passed after the SPEC-308 implementation and harness clarification commits.
- Ran the manual `Production Release` workflow for `main` with production deploy enabled.
- Confirmed the workflow deployed commit `cb7692e0d69f94f97e9883d6576c8719bfbbe8f5` successfully.
- Ran public production smoke checks for backend health, frontend delivery, and unauthenticated API error shape.

Validation:
- command: `gh run list --repo RGAlvaro/opdesk --branch main --limit 10`: PASS — latest `Verify` run `31475622515` for `cb7692e` completed successfully.
- command: `gh workflow run production-release.yml --repo RGAlvaro/opdesk --ref main -f target_ref=main -f deploy_to_production=true`: PASS — production release run `31476539204` completed successfully.
- command: `curl -fsS https://rgalvaro.es/health`: PASS — returned `{"status":"ok"}`.
- command: `curl -I -fsS https://rgalvaro.es/`: PASS — returned `HTTP/2 200`.
- command: `curl -i -sS https://rgalvaro.es/api/v1/users/me`: PASS — returned `401 not_authenticated` with the expected API error envelope.

Review:
- decision: N/A — production deployment and smoke checkpoint after approved SPEC-308.

Known gaps:
- Authenticated browser smoke for profile, organization, project, and task metadata was not run because no production test credentials were available in this session.

### 2026-08-11 — Harness — Managed sandbox migration validation clarified

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Updated `specs/harness/local-validation.md` so managed-sandbox agents treat host PostgreSQL and Docker Compose migration checks as outside-sandbox validation from the first attempt.
- Documented that sandboxed psycopg TCP failures or Docker socket permission errors are environment access constraints, not migration evidence.
- Clarified that either elevated `make migrations-check` or elevated `make migrations-check-compose` satisfies Alembic upgrade/drift coverage, with both preferred when available.

Validation:
- command: `make memory-check SPEC=SPEC-308`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — harness documentation clarification.

Known gaps:
- None.

### 2026-08-11 — SPEC-308 — Enriched metadata implemented and review-fixed

Role: Ingeniero de software / Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Added nullable backend metadata fields for users, organizations, projects, and tasks plus `task_watchers` persistence in migration `0006`.
- Extended current-user profile APIs for profile metadata and password-confirmed email changes with duplicate-email protection.
- Changed organization create/update behavior so public clients cannot submit `slug`; backend-generated slugs now use numeric collision suffixes.
- Extended project/task APIs for metadata validation, project owner checks, task blocker clearing, task watchers, and `task_type`/`watcher_id`/`external_reference` task filters.
- Added backend API tests for the new profile, organization, project, and task metadata behavior.
- Review found and fixed the missing frontend slice: profile, organization, project, and task forms now expose the new metadata fields, organization slug is display-only, project owner/watchers use visible organization members, and route tests cover the updated contracts.

Validation:
- command: `python3 -m compileall backend/app`: PASS.
- command: `make test-backend`: PASS — 80 non-DB backend tests passed, 2 DB tests deselected.
- command: `make test-frontend`: PASS — 41 frontend tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `git diff --check`: PASS.
- command: `make migrations-check`: PASS outside sandbox — Alembic upgraded through `0006` against host-local PostgreSQL and reported no new upgrade operations.
- command: `make migrations-check-compose`: PASS — Alembic upgraded through `0006` inside the Compose backend container and reported no new upgrade operations.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-08-11 — SPEC-307 — First production release workflow executed

Role: Ingeniero de software
Branch: main
Commit/PR: `a2dea58`
Status: Implemented

Summary:
- Ran the first manual `Production Release` workflow for `RGAlvaro/opdesk` against `main`.
- Ran validation-only first, then ran the production deploy after validation passed.
- Confirmed the production deploy executed remote SSH release steps, rebuilt/recreated the application services, and passed backend, frontend, Redis, and worker checks.
- Confirmed the public production domain still responds after deployment.

Validation:
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `gh workflow run production-release.yml --repo RGAlvaro/opdesk --ref main -f target_ref=main -f deploy_to_production=false`: PASS — run `31471833191` completed successfully; remote deploy was skipped.
- command: `gh workflow run production-release.yml --repo RGAlvaro/opdesk --ref main -f target_ref=main -f deploy_to_production=true`: PASS — run `31472041900` completed successfully at `a2dea58a70bef2aec98ef318ea6acc796099230f`; remote production update step passed.
- command: `curl -fsS https://rgalvaro.es/health`: PASS — returned `{"status":"ok"}`.
- command: `curl -I -fsS https://rgalvaro.es/`: PASS — returned `HTTP/2 200`.

Review:
- decision: N/A

Known gaps:
- The temporary `opdesk.51.255.202.88.sslip.io` hostname remains configured as a fallback.
- The VPS still needs a controlled reboot for the pending Ubuntu kernel upgrade.

### 2026-08-03 — SPEC-307 — Production release secrets configured

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Configured GitHub Actions repository secrets required by the manual `Production Release` workflow for `RGAlvaro/opdesk`.
- Set `PROD_SSH_HOST`, `PROD_SSH_USER`, `PROD_SSH_PORT`, `PROD_SSH_PRIVATE_KEY`, `PROD_PUBLIC_URL`, and `PROD_DEPLOY_ROOT`.
- Verified only secret names and update timestamps through GitHub CLI; secret values were not printed or committed.

Validation:
- command: `ssh -G opdesk-vps | rg '^(hostname|user|port|identityfile) '`: PASS — resolved deploy host metadata without printing private key contents.
- command: `gh auth status`: PASS — authenticated as `RGAlvaro` with `repo` and `workflow` scopes.
- command: `gh secret list --repo RGAlvaro/opdesk`: PASS — all six production release secrets are present.

Review:
- decision: N/A

Known gaps:
- First manual `Production Release` workflow run remains pending; run validation-only first with `deploy_to_production=false`, then deploy with `deploy_to_production=true` if validation passes.
- The temporary `opdesk.51.255.202.88.sslip.io` hostname remains configured as a fallback.
- The VPS still needs a controlled reboot for the pending Ubuntu kernel upgrade.

### 2026-07-30 — SPEC-307 — Release automation re-reviewed

Role: Review agent
Branch: main
Commit/PR: `dec820c`
Status: Reviewed

Summary:
- Re-reviewed the manual production release workflow, VPS release script, release validation target, deployment docs, spec status, and project memory against `SPEC-307`.
- Confirmed the previous blocking issue is fixed: production PostgreSQL and Redis are started only through `start_existing_service`, which requires existing containers and uses `docker compose start` before the pre-migration backup.
- Confirmed release automation remains manual, validates before production SSH, archives the selected Git revision, creates a pre-migration PostgreSQL custom-format backup, runs Alembic, updates the production Compose stack, checks backend/frontend through Caddy, verifies Redis and worker state, and documents app rollback separately from database restore.

Validation:
- command: `make release-workflow-check`: PASS — release script syntax, workflow static guardrails, missing `PROD_PUBLIC_URL` failure guard, and pre-backup no-recreate guard passed.
- command: `make memory-check SPEC=SPEC-307`: PASS — project memory mentions the active spec and required handoff sections.
- command: `git diff --check`: PASS.
- command: `make prod-config`: PASS — production Compose rendered with only Caddy host ports; PostgreSQL and Redis remain private.
- command: `make verify-no-db`: PASS — backend/frontend lint, format, typecheck, 71 backend non-DB tests, and 41 frontend tests passed.
- command: `make prod-data-smoke`: FAIL then PASS — sandboxed Docker socket access failed; elevated rerun passed isolated production migrations and backup/restore smoke for `opdesk-prod-smoke`.
- command: `make prod-smoke`: PASS — elevated isolated production stack build/start and Caddy backend/frontend, Redis, and worker checks passed.
- command: `make prod-down`: PASS — elevated isolated production-smoke stack stopped cleanly.

Review:
- decision: APPROVED

Known gaps:
- First real production workflow run remains pending until GitHub Actions secrets are configured.
- The temporary `opdesk.51.255.202.88.sslip.io` hostname remains configured as a fallback.
- The VPS still needs a controlled reboot for the pending Ubuntu kernel upgrade.

### 2026-07-29 — SPEC-307 — Release pre-backup recreation fix

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed the review-blocking release-order issue in `scripts/prod_release.sh`.
- Replaced the pre-backup `docker compose up -d postgres redis` path with `start_existing_service`, which requires existing production data-service containers and uses `docker compose start` so Compose cannot create or recreate PostgreSQL or Redis before the backup.
- Extended `scripts/validate_release_workflow.py` to require the safe data-service start guard and reject the unsafe `up -d postgres redis` fragment.

Validation:
- command: `make release-workflow-check`: PASS — release script syntax, workflow static guardrails, missing `PROD_PUBLIC_URL` failure guard, and pre-backup no-recreate guard passed.
- command: `make prod-config`: PASS — production Compose rendered with only Caddy host ports; PostgreSQL and Redis remain private.
- command: `git diff --check`: PASS.
- command: `make prod-data-smoke`: PASS — elevated isolated production migrations and backup/restore smoke passed for `opdesk-prod-smoke`.
- command: `make prod-smoke`: PASS — elevated isolated production stack build/start and Caddy backend/frontend, Redis, and worker checks passed.
- command: `make prod-down`: PASS — elevated isolated production-smoke stack stopped cleanly.

Review:
- decision: N/A — review fix ready for re-review.

Known gaps:
- Re-review is pending.
- First real production workflow run remains pending until review approval, merge, and GitHub Actions secrets are configured.

### 2026-07-29 — SPEC-307 — Release automation reviewed

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the manual production release workflow, VPS release script, release validation target, deployment docs, spec status, and project memory against `SPEC-307`.
- Confirmed the workflow is manual, records the selected revision, runs validation before SSH deployment, uses GitHub Actions secrets for production access, uploads a `git archive`, and documents rollback behavior.
- Found one blocking release-order issue: the remote script can recreate PostgreSQL or Redis via `docker compose up -d postgres redis` before the required pre-deploy backup.

Validation:
- command: `make release-workflow-check`: PASS — release script syntax, workflow static guardrails, and missing `PROD_PUBLIC_URL` failure guard passed.
- command: `make memory-check SPEC=SPEC-307`: PASS — project memory mentions the active spec and required handoff sections.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Change `scripts/prod_release.sh` so required data services are checked or started before backup without recreating/replacing existing production containers.
- First real production workflow run remains pending until review approval, merge, and GitHub Actions secrets are configured.

### 2026-07-29 — SPEC-307 — Release automation consolidation check

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Re-read `SPEC-307`, `SPEC-301`, release deployment docs, and deployment ADRs against the implemented manual release workflow and VPS release script.
- Confirmed the workflow remains manually triggered, records the selected target revision, runs validation before SSH deployment, uploads a `git archive` of the selected revision, and delegates production backup/migration/update/checks to `scripts/prod_release.sh`.
- Confirmed the release script validates production Compose config, starts data services before backup, writes a PostgreSQL custom-format backup before migrations, runs Alembic, rebuilds/starts the production stack, checks Caddy `/health`, frontend, Redis, and worker state, and writes a non-secret release manifest.

Validation:
- command: `make release-workflow-check`: PASS — release script syntax, workflow static guardrails, and missing `PROD_PUBLIC_URL` failure guard passed.
- command: `make memory-check SPEC=SPEC-307`: PASS — project memory mentions the active spec and required handoff sections.
- command: `git diff --check`: PASS.
- command: `make verify-no-db`: PASS — lint, format, typecheck, 71 backend non-DB tests, and 41 frontend tests passed.
- command: `make prod-config`: PASS — production Compose rendered with only Caddy host ports; PostgreSQL and Redis remain private.
- command: `make smoke`: PASS — local Compose stack built/started; backend `/health`, Redis, worker, Adminer, and frontend checks passed.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the Compose backend container with no new operations detected.
- command: `make verify`: FAIL — lint, format, typecheck, backend non-DB tests, and frontend tests passed; host-local `migrations-check` failed because WSL could not connect to PostgreSQL on `localhost`/`127.0.0.1:5432`.
- command: `make prod-data-smoke`: FAIL then PASS — sandboxed Docker socket access failed; elevated rerun passed isolated production migrations and backup/restore smoke for `opdesk-prod-smoke`.
- command: `make prod-smoke`: PASS — elevated isolated production stack build/start and Caddy backend/frontend, Redis, and worker checks passed.
- command: `make prod-down`: PASS — elevated isolated production-smoke stack stopped cleanly.

Review:
- decision: N/A — consolidation and validation checkpoint; review still pending.

Known gaps:
- Host-local `make verify` still cannot complete `migrations-check` from WSL, but equivalent Compose migration validation passed with `make migrations-check-compose`.
- First real production workflow run is pending until review/merge and GitHub Actions secrets are configured.

### 2026-07-28 — SPEC-308/SPEC-309/SPEC-310/SPEC-311 — Product follow-up specs prepared

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Updated `SPEC-102`, `SPEC-105`, and `SPEC-001` so organization slugs are backend-generated, non-editable, and collision-safe with numeric suffixes.
- Added Ready `SPEC-308` for enriched user profile metadata, password-confirmed email change, company metadata, project metadata, task metadata, task watchers, and non-editable organization slug behavior.
- Added Ready `SPEC-309` for project-scoped task labels with name, color, description, creator, archived state, task assignment, and label filtering.
- Added Ready `SPEC-310` for production-release-only `CHANGELOG.md` entries, `Added`/`Changed`/`Fixed` format, public changelog access, and release validation.
- Added Draft `SPEC-311` for a static public portfolio home linking OpsDesk and a coming-soon ERP app; personal/developer copy remains an implementation-time question.
- Updated the spec index, product vision, frontend landing/page notes, project/task UI routing notes, and project state with the new implementation order.

Validation:
- command: NOT RUN — spec/documentation-only change.
- command: `make memory-check SPEC=SPEC-308`: PASS — project memory mentions the next Ready spec and implementation-log handoff sections.

Review:
- decision: N/A

Known gaps:
- `SPEC-311` remains Draft pending personal/developer description inputs and the final primary OpsDesk action route.
- `SPEC-308`, `SPEC-309`, and `SPEC-310` are Ready but not implemented.

### 2026-07-23 — SPEC-307 — Release automation implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added the manual GitHub Actions `Production Release` workflow with `target_ref` and `deploy_to_production` inputs so maintainers can run validation-only dry runs or explicit production updates.
- Added `scripts/prod_release.sh` for the VPS-side update path: production Compose config validation, PostgreSQL custom-format backup before migrations, Alembic upgrade, Compose rebuild/start, Caddy `/health` and frontend checks, Redis `PING`, worker running-state check, release manifest, and rollback guidance on failure.
- Added `scripts/validate_release_workflow.py` plus `make release-workflow-check` to validate workflow guardrails and missing required environment handling without production secrets.
- Updated deployment docs, harness docs, spec index, and `SPEC-307` status for the implemented release automation path.

Validation:
- command: `make release-workflow-check`: PASS — shell syntax, workflow guardrail fragments, and missing `PROD_PUBLIC_URL` failure guard passed.
- command: `make prod-config`: PASS — release script syntax and production Compose config rendered; PostgreSQL and Redis still have no public host ports.
- command: `make verify`: FAIL — lint, format, typecheck, backend non-DB tests, and frontend tests passed; host-local `migrations-check` failed because PostgreSQL was not reachable from the host.
- command: `make smoke`: PASS — local Compose stack built/started and health, Redis, worker, Adminer, and frontend checks passed.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the Compose backend container.
- command: `make prod-data-smoke`: FAIL then PASS — sandboxed Docker socket access failed; elevated rerun passed isolated production migrations and backup/restore smoke for `opdesk-prod-smoke`.
- command: `make prod-smoke`: PASS — elevated isolated production stack build/start and Caddy backend/frontend, Redis, and worker checks passed.
- command: `make prod-down`: PASS — elevated isolated production-smoke stack stopped cleanly.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — implementation complete; review pending.

Known gaps:
- First real production workflow run is pending until the PR is reviewed/merged and GitHub Actions secrets are configured.
- The temporary `opdesk.51.255.202.88.sslip.io` hostname remains configured as a fallback.
- The VPS still needs a controlled reboot for the pending Ubuntu kernel upgrade.

### 2026-07-22 — SPEC-301 — Production domain configured

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Confirmed public DNS for `rgalvaro.es` and `www.rgalvaro.es` points to the VPS IPv4 `51.255.202.88` and IPv6 `2001:41d0:305:2100::1:1f66`.
- Updated server-side `/srv/opdesk/.env.production` so Caddy serves `rgalvaro.es`, `www.rgalvaro.es`, and the temporary `opdesk.51.255.202.88.sslip.io` hostname.
- Recreated the production Caddy container and confirmed Caddy obtained Let's Encrypt certificates for `rgalvaro.es` and `www.rgalvaro.es`.

Validation:
- command: `dig @1.1.1.1 +short rgalvaro.es A`: PASS — `51.255.202.88`.
- command: `dig @1.1.1.1 +short rgalvaro.es AAAA`: PASS — `2001:41d0:305:2100::1:1f66`.
- command: `curl -I https://rgalvaro.es/`: PASS — `HTTP/2 200`.
- command: `curl https://rgalvaro.es/health`: PASS — `{"status":"ok"}`.
- command: `curl -I https://www.rgalvaro.es/`: PASS — `HTTP/2 200`.
- command: `curl https://www.rgalvaro.es/health`: PASS — `{"status":"ok"}`.
- command: VPS stack check: PASS — backend, Caddy, frontend, PostgreSQL, Redis, and worker running.

Review:
- decision: N/A — production domain configuration for already approved `SPEC-301`.

Known gaps:
- `SPEC-307` release automation is still the next deployment-hardening implementation.
- The temporary `opdesk.51.255.202.88.sslip.io` hostname remains configured as a fallback and can be removed later.
- The VPS still needs a controlled reboot for the pending Ubuntu kernel upgrade.

### 2026-07-22 — SPEC-301 — Initial public VPS deployment executed

Role: Ingeniero de software
Branch: main
Commit/PR: deployed `a664414` / PR #9 already merged
Status: Implemented

Summary:
- Executed the documented initial `SPEC-301` production deployment on VPS host `opdesk-vps` as user `ubuntu`.
- Installed Docker Engine and Docker Compose plugin on Ubuntu 24.04 because the VPS did not yet have Docker available.
- Deployed source commit `a6644146fdda33ec592024fbdf16ff23e9a9f75a` to `/srv/opdesk` from a local `git archive`, avoiding persistent GitHub credentials on the VPS.
- Created server-side `/srv/opdesk/.env.production` with generated secrets, mode `600`, stable Compose project `opdesk-prod`, and public site `opdesk.51.255.202.88.sslip.io`.
- Created the initial PostgreSQL custom-format backup before migrations: `/srv/opdesk/backups/opdesk-initial-20260722-182637.dump`.
- Ran production Alembic migrations through revision `0005`, built backend/frontend/worker images, and started PostgreSQL, Redis, backend, worker, frontend, and Caddy.
- Confirmed Caddy obtained a Let's Encrypt certificate and serves the backend health endpoint and frontend through HTTPS.

Validation:
- command: `make prod-config`: PASS.
- command: `make verify`: FAIL — lint, format, typecheck, backend non-DB tests, and frontend tests passed; host-local `migrations-check` failed to connect to localhost PostgreSQL.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside Docker Compose.
- command: `make prod-data-smoke`: FAIL then PASS — sandboxed Docker socket access failed; elevated rerun passed production migrations plus backup/restore smoke for `opdesk-prod-smoke`.
- command: `ssh opdesk-vps 'docker compose --project-name opdesk-prod --env-file .env.production -f docker-compose.prod.yml config'`: PASS.
- command: production backup before migrations: PASS — custom-format dump created at `/srv/opdesk/backups/opdesk-initial-20260722-182637.dump`.
- command: production `alembic upgrade head`: PASS — migrations applied through `0005`.
- command: production `docker compose up -d --build`: PASS — backend healthy, frontend running, Caddy running, PostgreSQL/Redis healthy, worker running.
- command: production HTTPS `/health`: PASS — `{"status":"ok"}` from `https://opdesk.51.255.202.88.sslip.io/health`.
- command: production HTTPS `/`: PASS — `HTTP/2 200` from `https://opdesk.51.255.202.88.sslip.io/`.
- command: production Redis/worker/private-port checks: PASS — Redis `PONG`, worker running, PostgreSQL and Redis expose only container ports in Compose.

Review:
- decision: N/A — deployment execution for already approved `SPEC-301`.

Known gaps:
- `SPEC-307` release automation is now the next deployment-hardening implementation; routine post-launch updates remain manual until it is implemented.
- The deployment currently uses `opdesk.51.255.202.88.sslip.io`; replace with a durable custom domain if/when one is selected.
- The VPS has a pending Ubuntu kernel upgrade; schedule a controlled reboot outside this deployment window.

### 2026-07-22 — SPEC-302 — PR merged and obsolete branch cleaned

Role: Ingeniero de software
Branch: main
Commit/PR: merge `6f0a49b` / PR #9
Status: Merged

Summary:
- Merged the review-approved `SPEC-302` navigation stabilization PR #9 into `main`.
- Confirmed GitHub Actions `Verify / verify` passed before merge.
- Deleted the remote `codex/spec-302-navigation-stabilization` branch through the PR merge flow.
- Pruned remote refs and removed local obsolete merged branches whose upstreams were already gone.

Validation:
- command: GitHub Actions `Verify / verify`: PASS — PR #9 check completed successfully before merge.
- command: `git branch -r --format='%(refname:short)'`: PASS — remote now lists only `origin/main`.

Review:
- decision: APPROVED — prior review entry approved `SPEC-302`; PR #9 CI passed before merge.

Known gaps:
- Public VPS/domain deployment remains an external launch step.
- No Playwright E2E coverage was added; this remains a documented later frontend stabilization gap.

### 2026-07-22 — SPEC-302 — Navigation stabilization reviewed

Role: Review agent
Branch: codex/spec-302-navigation-stabilization
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the app-shell navigation implementation against `SPEC-302` and confirmed the frontend-only scope matches the spec.
- Confirmed Organizations, Projects, and Tasks now use deterministic route-derived active state and context-dependent links rather than all pointing to Organizations.
- Confirmed Projects and Tasks are disabled when their required organization/project context is unavailable.
- Confirmed project memory reflects the implementation, validation evidence, known gaps, and next work.

Validation:
- command: `make test-frontend`: PASS — 3 frontend test files passed, 41 tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make memory-check SPEC=SPEC-302`: PASS.
- command: `git diff --check`: PASS.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, Redis, worker, PostgreSQL, and Adminer; backend `/health`, Redis `PONG`, worker running check, Adminer, and Vite frontend responded.

Review:
- decision: APPROVED

Known gaps:
- No Playwright E2E coverage was added; this remains a documented later frontend stabilization gap.

### 2026-07-22 — SPEC-307 — Post-launch release automation spec prepared

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Added `SPEC-307` for release automation and safe production updates after the initial `SPEC-301` public deployment.
- Scoped the first implementation toward an explicit manual release workflow, pre-deploy PostgreSQL backup, blocking production migrations, production Compose update, post-deploy health checks, rollback documentation, and release evidence.
- Updated the spec index and project state so automation is planned after the initial VPS/domain deployment rather than blocking it.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Initial public deployment is still an external launch step before `SPEC-307` should be implemented.
- Release automation implementation is pending.

### 2026-07-17 — SPEC-302 — Predeployment navigation stabilization implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Moved `SPEC-302` from Draft to Implemented by resolving the remaining navigation scope questions in favor of context-dependent project/task shortcuts.
- Updated the authenticated app shell so Organizations, Projects, and Tasks derive mutually exclusive active state from the current route.
- Routed Projects to the active organization projects page only when route context or loaded project/task data provides active organization context.
- Routed Tasks to the current project task list when a project route or task detail response provides project context, and disabled unsafe project/task shortcuts instead of routing to Organizations.
- Added frontend regression tests for no-context disabled navigation, Organizations active state, Projects click routing, and Tasks click routing.

Validation:
- command: `make test-frontend`: PASS — 3 frontend test files passed, 41 tests passed.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, Redis, worker, PostgreSQL, and Adminer; backend `/health`, Redis `PONG`, worker running check, Adminer, and Vite frontend responded.

Review:
- decision: N/A — implementation complete; review pending.

Known gaps:
- No Playwright E2E coverage was added; existing project memory already tracks Playwright as a later frontend stabilization gap.

### 2026-07-17 — SPEC-302/SPEC-303/SPEC-304/SPEC-305/SPEC-306 — Planning PR merged

Role: Arquitecto de specs
Branch: main
Commit/PR: merge `5c1a205` / PR #8
Status: Merged

Summary:
- Reconciled the predeployment planning branch with `main` after `SPEC-201` merged.
- Opened PR #8 from `codex/spec-predeployment-planning` to `main`.
- Confirmed GitHub Actions verification passed and the PR was mergeable.
- Merged Draft `SPEC-302`, `SPEC-303`, `SPEC-304`, `SPEC-305`, and `SPEC-306` into `main`, then deleted the remote planning branch.
- Updated project memory so predeployment planning is recorded as integrated into `main`.

Validation:
- command: `make memory-check SPEC=SPEC-302`: PASS.
- command: `git diff --check`: PASS.
- command: GitHub Actions `Verify / verify`: PASS — run `29564046240`, job `87832556220`.

Review:
- decision: N/A — spec-planning PR; specs remain Draft and need readiness decisions before implementation.

Known gaps:
- `SPEC-302` remains Draft pending final predeployment scope and Tasks/sidebar behavior decisions.
- `SPEC-303`, `SPEC-304`, `SPEC-305`, and `SPEC-306` remain Draft pending product and implementation-order decisions.

### 2026-07-15 — SPEC-303/SPEC-304/SPEC-305/SPEC-306 — Product decisions incorporated

Role: Arquitecto de specs
Branch: codex/spec-predeployment-planning
Commit/PR: Pending
Status: Planned

Summary:
- Updated `SPEC-303` so invite-by-email targets must be existing users, access is granted only after in-app invitation acceptance, and project membership restricts task assignment.
- Updated `SPEC-304` toward a Slack-like chat model with direct messages, groups, organization channels, and project channels.
- Updated `SPEC-305` so clients are lightweight project contacts, and client tickets are stored as differentiated task records with a visible ticket label/color.
- Added Draft `SPEC-306` for persistent in-app notifications, unread state, actionable invitations, project/task state notifications, and missed chat message notifications.
- Updated project memory and the spec index with the new notification spec and resolved product choices.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Specs remain Draft pending final decisions about admin invite permissions, project visibility restrictions, chat transport, client ticket form access, notification retention, and notification recipient rules.

### 2026-07-15 — SPEC-303/SPEC-304/SPEC-305 — Draft product additions captured

Role: Arquitecto de specs
Branch: codex/spec-predeployment-planning
Commit/PR: Pending
Status: Planned

Summary:
- Added Draft `SPEC-303` for adding organization members by email and assigning organization members to projects.
- Added Draft `SPEC-304` for organization chat with a left-side member list ordered by shared project participation.
- Added Draft `SPEC-305` for project clients and client-created tickets visible to project members.
- Updated `SPEC-302` to stay focused on predeployment UI stabilization and route larger product additions to separate specs.
- Updated the spec index and project memory with the new Draft specs and open scope decisions.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-303`, `SPEC-304`, and `SPEC-305` remain Draft pending product decisions about invite acceptance, email delivery, project-level access semantics, chat transport, client identity, and ticket data modeling.

### 2026-07-15 — SPEC-302 — Predeployment UI stabilization spec started

Role: Arquitecto de specs
Branch: codex/spec-predeployment-planning
Commit/PR: Pending
Status: Planned

Summary:
- Added Draft `SPEC-302` for predeployment UI stabilization and small corrections/additions.
- Captured the confirmed left-panel navigation defect: after creating an organization, clicking `Organizations`, `Projects`, or `Tasks` routes to organizations and highlights all three entries.
- Updated the spec index and project memory so the next work is completing `SPEC-302` scope before implementation.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Additional predeployment corrections/additions still need to be collected before `SPEC-302` can move to Ready.
- The intended `Tasks` left-panel target remains an open product/routing question.

### 2026-07-16 — SPEC-201 — PR #7 merged and branch closed

Role: Ingeniero de software
Branch: main
Commit/PR: merge `ad90534` / PR #7
Status: Merged

Summary:
- Opened PR #7 from `codex/spec-201-background-jobs` to `main`.
- Confirmed GitHub Actions verification passed and the PR was mergeable.
- Merged `SPEC-201` into `main` and deleted the remote `codex/spec-201-background-jobs` branch.
- Updated project memory so `SPEC-201` is recorded as integrated rather than awaiting PR/CI.

Validation:
- command: GitHub Actions `Verify / verify`: PASS — run `29481984511`, job `87567615091`.
- command: `make memory-check SPEC=SPEC-201`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED — prior review approved `SPEC-201`; PR #7 CI passed before merge.

Known gaps:
- Public VPS/domain deployment remains an external launch step.
- Notification delivery remains log-only; real email provider integration, notification inbox UI, scheduled jobs, and persistent job audit remain outside `SPEC-201`.

### 2026-07-08 — SPEC-201 — Review-approved branch published

Role: Ingeniero de software
Branch: codex/spec-201-background-jobs
Commit/PR: `4ccbd84`
Status: Implemented

Summary:
- Committed the review-approved `SPEC-201` implementation as `4ccbd84`.
- Pushed `codex/spec-201-background-jobs` to `origin/codex/spec-201-background-jobs`.
- Updated project memory so the next handoff is PR/CI integration rather than local publication.

Validation:
- command: `git diff --check`: PASS before commit.
- command: `make memory-check SPEC=SPEC-201`: PASS before commit.
- command: `git push -u origin codex/spec-201-background-jobs`: PASS.

Review:
- decision: APPROVED — previous review entry approved the implementation; this entry records publication.

Known gaps:
- PR creation, CI result, and merge remain pending.
- Public VPS/domain deployment remains an external launch step.
- Notification delivery remains log-only; real email provider integration, notification inbox UI, scheduled jobs, and persistent job audit remain outside `SPEC-201`.

### 2026-07-08 — SPEC-201 — Assignment-version review fix approved

Role: Review agent
Branch: codex/spec-201-background-jobs
Commit/PR: Uncommitted local changes
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-201` assignment-version stale job fix.
- Confirmed worker processing now compares payload `assignment_version` with current task `updated_at` before delivery.
- Confirmed stale-version payloads return a safe no-op and have focused backend coverage.
- Confirmed project memory reflects the review-fix validation and remaining known gaps.

Validation:
- command: `cd backend && poetry run pytest tests/test_background_jobs_notifications.py -q`: PASS — 6 tests passed.
- command: `make memory-check SPEC=SPEC-201`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- Public VPS/domain deployment remains an external launch step.
- Notification delivery remains log-only; real email provider integration, notification inbox UI, scheduled jobs, and persistent job audit remain outside `SPEC-201`.
- Playwright E2E coverage remains deferred.

### 2026-07-08 — SPEC-201 — Assignment-version stale job review fix

Role: Ingeniero de software
Branch: codex/spec-201-background-jobs
Commit/PR: Uncommitted local changes
Status: Implemented

Summary:
- Addressed review feedback that worker processing ignored `assignment_version`.
- Added stale-version detection so an assignment notification job is ignored when the task assignee still matches but the current `updated_at` version differs from the payload.
- Added backend coverage for stale assignment-version payloads returning a safe no-op.

Validation:
- command: `cd backend && poetry run pytest tests/test_background_jobs_notifications.py -q`: PASS — 6 tests passed.
- command: `make verify-no-db`: PASS — backend Ruff, frontend ESLint, format checks, backend mypy, frontend typecheck, 71 backend non-DB tests, and 38 frontend tests passed.
- command: elevated `make verify`: FAIL — no-DB checks passed, but Alembic could not connect to PostgreSQL on `127.0.0.1:5432` because the local Compose database was not running.
- command: `make smoke`: PASS — local Compose built/started backend, frontend, PostgreSQL, Redis, worker, and Adminer; backend health, Redis `PONG`, worker running check, Adminer, and frontend HTTP checks passed.
- command: elevated `make migrations-check`: PASS — Alembic upgrade and drift check passed against the Compose PostgreSQL database.

Review:
- decision: N/A — review fix awaits re-review.

Known gaps:
- Public VPS/domain deployment remains an external launch step.
- Notification delivery remains log-only; real email provider integration, notification inbox UI, scheduled jobs, and persistent job audit remain outside `SPEC-201`.
- Playwright E2E coverage remains deferred.

### 2026-07-07 — SPEC-201 — Background jobs and task assignment notifications implemented

Role: Ingeniero de software
Branch: codex/spec-201-background-jobs
Commit/PR: Uncommitted local changes
Status: Implemented

Summary:
- Closed `SPEC-201` implementation decisions for Redis/Celery, log-only local-safe delivery, no persistent notification tables, and limited worker retries; recorded the durable choice in `ADR-010`.
- Added Celery/Redis dependencies, backend settings, Celery app wiring, request-time enqueue helper, worker task, and task assignment notification payload/processing code.
- Enqueued assignment notification jobs after successful task creation with an assignee and after successful reassignment to a non-null assignee.
- Added local and production Redis/worker Compose services, documented production Redis/worker operations, and expanded smoke checks to verify Redis and worker runtime state.
- Added backend coverage for minimal payload creation, task create/reassign enqueue hooks, synchronous worker processing, and broker-free worker task execution.

Validation:
- command: elevated `make verify`: PASS — backend Ruff, frontend ESLint, format checks, backend mypy, frontend typecheck, 70 backend non-DB tests, 38 frontend tests, Alembic upgrade, and Alembic drift check passed.
- command: `make verify-no-db`: PASS — backend Ruff, frontend ESLint, format checks, backend mypy, frontend typecheck, 69 backend non-DB tests, and 38 frontend tests passed before the invalid-payload worker test was added.
- command: `make prod-config`: PASS — production Compose renders private Redis, worker, backend, frontend, PostgreSQL, and Caddy with safe placeholder secrets.
- command: `make smoke`: PASS — local Compose built/started backend, frontend, PostgreSQL, Redis, worker, and Adminer; backend health, Redis `PONG`, worker running check, Adminer, and frontend HTTP checks passed.
- command: `make migrations-check`: FAIL then PASS — sandboxed localhost PostgreSQL connection failed; elevated rerun passed Alembic upgrade and drift check with no new upgrade operations detected.
- command: `make prod-smoke`: FAIL then PASS — sandboxed Docker socket access failed; elevated rerun passed production migrations, backup/restore data smoke, production image builds, Caddy `/health`, Redis `PONG`, worker running check, and frontend `/`.
- command: `make prod-down`: FAIL then PASS — sandboxed Docker socket access failed; elevated rerun removed the isolated production-smoke containers and network.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- Public VPS/domain deployment remains an external launch step.
- Notification delivery is log-only; real email provider integration, notification inbox UI, scheduled jobs, and persistent job audit remain outside `SPEC-201`.
- Playwright E2E coverage remains deferred.

### 2026-07-06 — Repository integration — SPEC-301 and sandbox policy merged

Role: Ingeniero de software
Branch: main
Commit/PR: merge `8225e6f` / PR #5; merge `c1a730b` / PR #6
Status: Merged

Summary:
- Merged the review-approved `SPEC-301` production deployment work and its final memory checkpoint into `main`.
- Reconciled the managed-sandbox GitHub CLI policy with the new production workflow, reviewed it, and merged it into `main`.
- Removed obsolete handoff text and recorded that no integration branches remain.

Validation:
- command: PR #5 GitHub Actions `Verify`: PASS — final PR head `99ee74d`, merged as `8225e6f`.
- command: PR #6 GitHub Actions `Verify`: PASS — run `28802864739`, job `85410599193`, final PR head `fb1f5a6`, merged as `c1a730b`.
- command: `make memory-check SPEC=SPEC-301`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED — both integrated PRs were mergeable, review approved, and green before merge.

Known gaps:
- Playwright E2E coverage, public VPS/domain launch, and `SPEC-201` remain explicitly deferred for later prioritization.

### 2026-07-06 — Repository workflow — Managed sandbox GitHub CLI policy reconciled

Role: Arquitecto de specs
Branch: codex/gh-outside-sandbox-policy
Commit/PR: `62bfaa0` / PR #6
Status: Reviewed

Summary:
- Required network-backed `gh` commands to run outside managed sandboxes from the first attempt.
- Required narrowly scoped approvals and an outside-sandbox authentication check before publication.
- Added an explicit `workflow` token-scope check when publishing `.github/workflows/*`.
- Recorded the durable decision in `ADR-009`; no product spec status or behavior changed.
- Reconciled the policy branch with `main` after SPEC-301 and PR #5 were integrated.

Validation:
- command: `git diff --check`: PASS.
- command: policy reference check with `rg`: PASS — mandatory outside-sandbox execution and `workflow` scope guidance are present in agent instructions, workflow notes, ADR, and project memory.
- command: `make memory-check SPEC=SPEC-301`: PASS — latest implemented product memory remains structurally valid; this policy does not introduce a product spec.
- command: elevated `gh auth status`: PASS — authenticated account exposes `repo` and `workflow` scopes outside the sandbox.
- command: GitHub Actions `Verify` / `verify`: PASS — run `28802653587`, job `85409870201`, completed successfully on reconciled head `32abece`.

Review:
- decision: APPROVED — the policy is consistent across `AGENTS.md`, workflow guidance, ADR-009, and project memory; it does not weaken secret handling or validation requirements.

Known gaps:
- Runtime approval remains environment-specific; the repository can require elevation but cannot pre-authorize it.

### 2026-07-06 — SPEC-301 — Review fix published and CI passed

Role: Ingeniero de software
Branch: codex/spec-301-deployment
Commit/PR: `2a36558` / PR #5
Status: Reviewed

Summary:
- Published the review-approved production database URL and full-CI fixes to PR #5.
- Confirmed the pushed head matches commit `2a36558` and the GitHub Actions `Verify` workflow completed successfully.
- Reconciled project memory so it no longer describes the review fix as local or its CI as pending.

Validation:
- command: GitHub Actions `Verify` / `verify`: PASS — run `28778419569`, job `85327804130`, completed successfully on commit `2a36558`.
- command: `git status -sb`: PASS — local branch matched `origin/codex/spec-301-deployment` before this memory checkpoint.

Review:
- decision: APPROVED — the implementation review remains approved; this entry corrects its publication and CI evidence.

Known gaps:
- Public VPS/domain deployment remains an explicitly deferred external launch step.
- Redis and worker production services remain deferred until `SPEC-201`.

### 2026-07-06 — SPEC-301 — Production database URL and CI review approved

Role: Review agent
Branch: codex/spec-301-deployment
Commit/PR: `2a36558` / PR #5
Status: Reviewed

Summary:
- Re-reviewed the latest `SPEC-301` changes for explicit production database URL handling, CI full verification with PostgreSQL, deployment docs, ADR coverage, and project memory.
- Confirmed production Compose no longer interpolates raw `POSTGRES_PASSWORD` into `DATABASE_URL`; backend uses explicit `PROD_DATABASE_URL`.
- Confirmed docs and `.env.example` require URL-encoded production database credentials and no real secrets are committed.
- Confirmed CI now provisions PostgreSQL and runs `make verify`, including migration validation.

Validation:
- command: `make prod-config`: PASS — production Compose rendered with `PROD_DATABASE_URL`, Caddy as the only public entry point, private PostgreSQL, and namespaced smoke volumes.
- command: `make prod-config PROD_POSTGRES_PASSWORD='p@ss:word/with?x#y' PROD_DATABASE_URL='postgresql+psycopg://opdesk:p%40ss%3Aword%2Fwith%3Fx%23y@postgres:5432/opdesk'`: PASS — Compose rendered the encoded backend database URL and raw PostgreSQL password separately.
- command: `make prod-smoke`: PASS — production data smoke, image builds, Caddy `/health`, and frontend `/` checks passed.
- command: `make prod-down`: PASS — isolated production-smoke containers and network were removed without deleting the smoke database volume.
- command: `make smoke`: PASS — local Compose built/started backend, frontend dev server, PostgreSQL, and Adminer; HTTP checks passed.
- command: `make verify`: PARTIAL PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed; sandboxed host PostgreSQL connection failed during `migrations-check`.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the Compose backend container.
- command: `npm run build` from `frontend/`: PASS — TypeScript build and Vite production build passed.
- command: URL-encoded SQLAlchemy parse check: PASS — `p%40ss%3Aword%2Fwith%3Fx%23y` parsed as `p@ss:word/with?x#y`.
- command: `make memory-check SPEC=SPEC-301`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- PR #5 CI passed after these changes were committed and pushed as `2a36558`.
- Public VPS/domain deployment remains an external launch step.

### 2026-07-06 — SPEC-301 — Production database URL and CI review fix

Role: Ingeniero de software
Branch: codex/spec-301-deployment
Commit/PR: Uncommitted local changes / PR #5
Status: Implemented

Summary:
- Replaced the production backend `DATABASE_URL` interpolation of raw `POSTGRES_PASSWORD` with an explicit required `PROD_DATABASE_URL`.
- Documented that production database URL credentials must match PostgreSQL settings and URL-encode reserved password characters.
- Updated `SPEC-301` to require parser-safe production database URL handling and full CI verification including migration validation.
- Updated GitHub Actions to provide a PostgreSQL service and run `make verify` instead of the no-database subset.
- Recorded the explicit production database URL decision in `ADR-008`.

Validation:
- command: `make verify-no-db`: PASS — backend Ruff, frontend ESLint, format checks, backend mypy, frontend typecheck, 65 backend non-DB tests, and 38 frontend tests passed.
- command: `npm run build` from `frontend/`: PASS — TypeScript build and Vite production build passed.
- command: `cd backend && poetry run python -c "from sqlalchemy.engine import make_url; url=make_url('postgresql+psycopg://opdesk:p%40ss%3Aword@postgres:5432/opdesk'); assert url.password == 'p@ss:word'; print(url.host, url.password)"`: PASS — SQLAlchemy parsed the URL-encoded password as password text.
- command: `make memory-check SPEC=SPEC-301`: PASS.
- command: `git diff --check`: PASS.
- command: `make prod-config`: FAIL — Docker CLI is present through Docker Desktop but reports that WSL integration is unavailable in this distro, so production Compose rendering could not be rerun here.
- command: `make migrations-check`: FAIL — local PostgreSQL was not reachable from this environment.

Review:
- decision: N/A — implementation awaits Docker/CI revalidation and re-review.

Known gaps:
- Rerun `make prod-config`, `make prod-smoke`, `make prod-down`, and full `make verify` once Docker/PostgreSQL are reachable.
- Obtain fresh CI for PR #5 after committing/pushing the fix.
- Public VPS/domain deployment remains an external launch step.

### 2026-07-02 — SPEC-301 — Production smoke isolation and restore review fix

Role: Ingeniero de software
Branch: codex/spec-301-deployment
Commit/PR: `d413343`, memory checkpoint `5cb0017` / PR #5
Status: Implemented

Summary:
- Isolated production harness commands under the configurable `opdesk-prod-smoke` Compose project so they cannot reuse local-development containers, networks, or volumes by default.
- Added a production data smoke that applies migrations, creates a custom-format PostgreSQL backup, deletes a marker row, restores the backup transactionally, verifies the marker, removes the probe table, and checks Alembic drift.
- Replaced the unsafe plain-SQL restore documentation with stable project naming and custom-format `pg_dump`/`pg_restore` commands.
- Added production harness coverage to the local validation guide and ignored generated backup artifacts.

Validation:
- command: `make prod-config`: PASS — shell syntax and production Compose rendering passed; rendered resources use the `opdesk-prod-smoke_*` namespace.
- command: `make prod-data-smoke`: PASS — migrations, custom-format dump, destructive marker deletion, transactional restore, restored marker verification, probe cleanup, and final Alembic drift check passed in the isolated database.
- command: `make prod-smoke`: PASS — the complete data smoke passed, production images built, and `/health` plus `/` passed through Caddy on port 8081.
- command: `make prod-down`: PASS — isolated production-smoke containers and network stopped and were removed without affecting the local Compose project or deleting the smoke database volume.
- command: `make verify-no-db`: PASS — 65 backend tests and 38 frontend tests passed with lint, format, and type checks.
- command: `git diff --check`: PASS.
- command: `git push -u origin codex/spec-301-deployment`: PASS — implementation and memory commits were published to the branch used by PR #5.

Review:
- decision: N/A — fully validated review fix awaits re-review.

Known gaps:
- Obtain a fresh CI result for the updated PR #5 and re-review it.
- Public VPS/domain deployment remains an external launch step.

### 2026-06-30 — SPEC-301 — Production deployment implemented

Role: Ingeniero de software
Branch: codex/spec-301-deployment
Commit/PR: `3bb4882` / PR #5
Status: Implemented

Summary:
- Added production Compose with private PostgreSQL, backend, static frontend, and Caddy as the only public entry point.
- Added Caddy routing for `/api/*`, `/health`, and frontend routes, plus a production frontend image target served by nginx.
- Added production Make targets for Compose config validation, local production smoke, and production stack cleanup.
- Added GitHub Actions verification, deployment/backup/restore documentation, README updates, and `ADR-008` for the production topology.
- Marked `SPEC-301` implemented in the spec index and updated project memory for review handoff.

Validation:
- command: `make verify-no-db`: PASS — backend Ruff, frontend ESLint, format checks, backend mypy, frontend typecheck, 65 backend non-DB tests, and 38 frontend tests passed.
- command: `npm run build` from `frontend/`: PASS — TypeScript build and Vite production build passed.
- command: `make prod-config`: PASS — production Compose config rendered with safe placeholder secrets.
- command: `make prod-smoke`: PASS — production Compose built and started backend, frontend, PostgreSQL, and Caddy; `/health` and `/` passed through Caddy on local port 8081.
- command: `make prod-down`: PASS — production smoke containers were stopped and removed; shared Compose network remained because local Adminer was still running.
- command: `make smoke`: PASS — local Compose still starts backend, frontend dev server, PostgreSQL, and Adminer after frontend Dockerfile target changes.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the Compose backend container.
- command: `make verify`: PASS — full verification passed when rerun with elevated host PostgreSQL access; sandboxed host migration connection failed before elevation.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- GitHub Actions workflow `Verify` passed on PR #5 in 1m12s.
- Public production deployment is documented but not yet executed against a real VPS/domain.
- Redis and worker production services remain deferred until `SPEC-201`.

### 2026-06-30 — SPEC-106 — Pagination review fix approved

Role: Review agent
Branch: main
Commit/PR: `749c381`
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-106` pagination review fix.
- Confirmed project and task list hooks send `limit`/`offset` and include pagination in query keys.
- Confirmed project and task list screens expose URL-backed previous/next pagination controls.
- Confirmed task filters reset offset to the first page and preserve filters when paginating.
- Confirmed tests assert paginated requests, shared pagination URLs, and filtered task pagination.
- Updated project memory to mark `SPEC-106` review approved.

Validation:
- command: `make test-frontend`: PASS — 3 frontend test files, 38 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.
- command: `make memory-check SPEC=SPEC-106`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: APPROVED

Known gaps:
- No Playwright E2E critical path yet; `SPEC-106` explicitly recommends adding it after organization/project/task UI stabilizes.

### 2026-06-30 — SPEC-106 — Pagination review fix implemented

Role: Ingeniero de software
Branch: main
Commit/PR: `749c381`
Status: Implemented

Summary:
- Added `limit` and `offset` support to project and task list API hooks and query keys.
- Added URL-backed previous/next pagination controls to project and task list routes.
- Reset task pagination offset when filters change while preserving filter query parameters when paging.
- Added route tests that assert project/task list requests include `limit`/`offset`, that shared pagination URLs load the requested page, and that task filters are preserved while paginating.
- Updated project memory for re-review handoff.

Validation:
- command: `npm run test` from `frontend/`: PASS — 3 frontend test files, 38 tests passed.
- command: `npm run lint` from `frontend/`: PASS — frontend ESLint passed.
- command: `npm run format:check` from `frontend/`: PASS — frontend Prettier passed.
- command: `npm run typecheck` from `frontend/`: PASS — TypeScript project build passed.
- command: `make test-frontend`: PASS — 3 frontend test files, 38 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.

Review:
- decision: N/A — review fix awaits re-review.

Known gaps:
- No Playwright E2E critical path yet; `SPEC-106` recommends adding it after organization/project/task UI stabilizes.

### 2026-06-24 — SPEC-106 — Review changes requested

Role: Review agent
Branch: main
Commit/PR: `749c381`
Status: Reviewed

Summary:
- Reviewed the `SPEC-106` frontend projects/tasks implementation against routes, API usage, filters, role-aware controls, tests, validation, and project memory.
- Confirmed required frontend validation and smoke checks pass.
- Found that project and task list API hooks and screens do not expose `limit`/`offset` pagination controls or request parameters, leaving AC-1, AC-6, and the harness pagination requirement only partially implemented.
- Updated project memory to reflect the review decision and next work.

Validation:
- command: `make test-frontend`: PASS — 3 frontend test files, 37 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.
- command: `make memory-check SPEC=SPEC-106`: PASS.
- command: `git diff --check`: PASS.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Project and task list pagination controls/request parameters are missing and must be implemented before approval.

### 2026-06-24 — SPEC-106 — Frontend projects and tasks UI implemented

Role: Ingeniero de software
Branch: main
Commit/PR: `749c381`
Status: Implemented

Summary:
- Added project API hooks, types, list route, creation route, detail route, owner/admin settings, archive toggles, and organization-detail project navigation.
- Added task API hooks, types, URL-backed task filters, task list route, task creation route, role-aware assignee controls, task detail/update route, and safe `401`/`403`/`404`/`409` handling.
- Updated authenticated shell and dashboard navigation now that project/task routes are implemented.
- Added route-level frontend coverage for project list/create/update/archive, role-aware controls, task filters, assignment behavior, archived projects, task update completion state, safe API errors, and auth guard behavior.
- Marked `SPEC-106` implemented in the spec index and updated project memory for review handoff.

Validation:
- command: `npm run typecheck` from `frontend/`: PASS — TypeScript project build passed after initial implementation fixes.
- command: `npm run test -- --runInBand` from `frontend/`: FAIL — Vitest does not support the Jest-style `--runInBand` option in this project.
- command: `npm run test` from `frontend/`: PASS — 3 frontend test files, 37 tests passed.
- command: `npm run lint` from `frontend/`: PASS — frontend ESLint passed after removing a dead import and Fast Refresh helper exports.
- command: `npm run format:check` from `frontend/`: PASS — frontend Prettier check passed after formatting touched files.
- command: `make test-frontend`: PASS — 3 frontend test files, 37 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose rebuilt/started backend, frontend, PostgreSQL, and Adminer; backend health, Adminer, and frontend HTTP checks passed after backend startup retries.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- No Playwright E2E critical path yet; `SPEC-106` recommends adding it after organization/project/task UI stabilizes.

### 2026-06-24 — SPEC-106 — Memory harness review approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the review-gated memory workflow changes against the requested points: review approval as the canonical checkpoint, memory verification targets, and implementation-log scaffolding.
- Confirmed the changes avoid commit/push hooks as the source of truth and keep generated memory factual.
- Confirmed new scripts use standard-library Python, include required reader comments/docstrings, and are wired through Make targets.
- Confirmed project memory and `ADR-005` reflect the durable workflow policy.

Validation:
- command: `git diff --check`: PASS.
- command: `make memory-check SPEC=SPEC-106`: PASS — project-state and implementation-log mention the active spec and required handoff sections.
- command: `make review-ready SPEC=SPEC-106`: PASS — memory readiness alias passed.
- command: `python3 scripts/memory_check.py --spec SPEC-106 --reviewed`: PASS — strict reviewed/approved memory check passed.
- command: `python3 -m compileall scripts`: PASS — both memory helper scripts compiled.

Review:
- decision: APPROVED

Known gaps:
- `SPEC-106` product UI remains unimplemented; this review only covers the base workflow and memory harness preparation.

### 2026-06-24 — SPEC-106 — Review-gated memory harness prepared

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Updated the base workflow so Review agent `APPROVED` is the canonical point where `docs/project-state.md` and `docs/implementation-log.md` must be current.
- Added `make memory-check SPEC=SPEC-XXX`, `make review-ready SPEC=SPEC-XXX`, and `make memory-entry SPEC=SPEC-XXX` as harness helpers for memory verification and log-entry scaffolding.
- Documented the helpers in the local validation harness and captured the durable policy in `ADR-005`.
- Kept the helpers factual: they validate or print templates, but do not auto-write validation evidence or review decisions.

Validation:
- command: `make memory-entry SPEC=SPEC-106 ROLE='Review agent' STATUS=Reviewed TITLE='Review approved' BRANCH=main`: PASS — printed a paste-ready reviewed-entry template.
- command: `make memory-check SPEC=SPEC-106`: PASS — verified project-state and implementation-log memory shape for the active spec.
- command: `make review-ready SPEC=SPEC-106`: PASS — ran the memory readiness alias successfully.
- command: `git diff --check`: PASS.

Review:
- decision: N/A

Known gaps:
- `SPEC-106` remains unimplemented.

### 2026-06-24 — SPEC-106 — Readiness audit for frontend projects and tasks UI

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed project memory, spec index, product/API conventions, local validation harness, `SPEC-103`, `SPEC-104`, `SPEC-105`, and `ADR-007` before implementation handoff.
- Confirmed `SPEC-106` is the next dependency-valid implementation target after merged `SPEC-105`.
- Checked backend project/task API contracts and frontend organization helper surfaces for obvious mismatches; no spec gap found.
- Updated project memory so the active branch and active spec reflect the merged `main` state.

Validation:
- command: `git status -sb`: PASS — repository is on `main` tracking `origin/main` before documentation updates.
- command: implementation harness NOT RUN — readiness/documentation review only; product code was not changed.

Review:
- decision: N/A

Known gaps:
- `SPEC-106` remains unimplemented.
- Full implementation validation is deferred to the `SPEC-106` engineer.

### 2026-06-24 — SPEC-105 — Review approved after auth-loss fix

Role: Review agent
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-reviewed the `SPEC-105` organization `401 not_authenticated` fix.
- Confirmed organization query and mutation auth-loss handling clears cached session state and navigates to `/login`.
- Confirmed updated frontend tests cover cached-session query `401` and mutation `401` flows.
- Updated project memory to mark `SPEC-105` review approved and route next work to `SPEC-106`.

Validation:
- command: `make test-frontend`: PASS — 2 frontend test files, 24 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: prior `make verify-no-db`: PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed for the review fix.
- command: prior `make smoke`: PASS — Docker Compose built/started backend, frontend, PostgreSQL, and Adminer; health/Adminer/frontend checks passed for the review fix.

Review:
- decision: APPROVED

Known gaps:
- `SPEC-106` project/task UI remains unimplemented.

### 2026-06-24 — SPEC-105 — Review fix implemented

Role: Ingeniero de software
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Implemented

Summary:
- Added organization auth-loss handling that cancels/removes the cached session query and navigates to `/login` when organization queries or mutations return `401 not_authenticated`.
- Applied the handling to organization list/detail/member query error branches and create/update/delete/member role/member removal/ownership transfer mutation failures.
- Added frontend tests for cached-session query `401` and mutation `401` flows to ensure the login route remains visible after session cache is cleared.
- Updated project memory for re-review handoff.

Validation:
- command: `cd frontend && npm run test -- OrganizationPages.test.tsx`: PASS — 12 organization tests passed.
- command: `cd frontend && npm run typecheck`: PASS.
- command: `cd frontend && npm run lint`: PASS.
- command: `make test-frontend`: PASS — 2 frontend test files, 24 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make verify-no-db`: PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, frontend, PostgreSQL, and Adminer; health/Adminer/frontend checks passed.

Review:
- decision: N/A — review fix awaits re-review.

Known gaps:
- `SPEC-105` re-review approval remains pending.
- `SPEC-106` project/task UI remains unimplemented.

### 2026-06-24 — SPEC-105 — Review changes requested

Role: Review agent
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-105` implementation against frontend organization routes, API usage, permission states, error handling, tests, and project memory.
- Found that organization `401 not_authenticated` handling does not clear cached session state and mutation `401` responses do not redirect to login, contrary to the spec's API usage contract.
- Updated project memory to reflect review changes requested.

Validation:
- command: `make test-frontend`: PASS — 2 frontend test files, 22 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Fix organization query and mutation `401 not_authenticated` handling so session cache is cleared and the user reaches `/login`.

### 2026-06-24 — SPEC-105 — Frontend organizations UI implemented

Role: Ingeniero de software
Branch: codex/spec-105-frontend-organizations-ui
Commit/PR: Pending
Status: Implemented

Summary:
- Implemented frontend organization routes for list, create, detail, settings, and members under the authenticated app shell.
- Added organization API hooks and types for `SPEC-102` endpoints, including create/update/delete, member listing, role changes, member removal, and ownership transfer.
- Updated app navigation and dashboard entry points so Organizations is active while Projects/Tasks remain unavailable until `SPEC-106`.
- Added route-level frontend tests for empty/list states, creation errors, role-aware detail/settings/member controls, destructive confirmation, owner member actions, safe `403`/`404` handling, and auth redirects.
- Updated `SPEC-105` status and project memory for review handoff.

Validation:
- command: `cd frontend && npm run test`: PASS — 2 files, 22 tests passed.
- command: `cd frontend && npm run typecheck`: PASS.
- command: `cd frontend && npm run lint`: PASS.
- command: `cd frontend && npm run format:check`: PASS.
- command: `make test-frontend`: PASS — 2 frontend test files, 22 tests passed.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `make format-check`: PASS — backend Ruff format check and frontend Prettier passed.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, frontend, PostgreSQL, and Adminer; health/Adminer/frontend checks passed.
- command: `make verify-no-db`: PASS — lint, format, type checks, backend non-DB tests, and frontend tests passed.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- `SPEC-105` review approval remains pending.
- `SPEC-106` project/task UI remains unimplemented.

### 2026-06-24 — SPEC-105/SPEC-106 — Frontend work specs prepared

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Added `SPEC-105` for frontend organization/workspace UI, including routes, active organization context, owner/admin/member states, member management, API usage, acceptance criteria, and frontend validation requirements.
- Added `SPEC-106` for frontend projects and tasks UI, including routes, project/task forms, filters, assignment controls, archived-project behavior, API usage, acceptance criteria, and frontend validation requirements.
- Updated project memory and spec index so the next implementation order is `SPEC-105` then `SPEC-106`, with `SPEC-201` remaining Draft and `SPEC-301` still Ready but lower priority than the core UI.

Validation:
- command: `git diff --check`: PASS
- command: implementation harness NOT RUN — spec/documentation changes only; product code was not changed.

Review:
- decision: N/A

Known gaps:
- `SPEC-105` and `SPEC-106` are ready but not implemented.
- `SPEC-201` remains Draft until notification-worthy task events are finalized.

### 2026-06-23 — SPEC-103 — Docker validation retried

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Re-ran Docker-backed validation after Docker Desktop was started.
- Confirmed Docker Compose can build/start the stack and Alembic can validate migration `0005` from inside the backend container.
- Confirmed host-side Alembic access to `localhost:5432` still fails in this WSL environment, so `migrations-check-compose` remains the reliable DB validation path here.

Validation:
- command: `docker --version`: PASS — Docker CLI responded.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make migrations-check-compose`: PASS — Alembic upgrade/check passed inside the backend container.
- command: `make migrations-check`: FAIL — host process could not connect to PostgreSQL at `localhost:5432`.
- command: `LOCAL_DATABASE_URL=postgresql+psycopg://opdesk:opdesk_dev_password@127.0.0.1:5432/opdesk poetry run alembic current`: FAIL — same host-to-PostgreSQL connection issue.
- command: `make verify-no-db`: PASS — lint, format, backend/frontend type checks, backend tests, and frontend tests passed.

Review:
- decision: APPROVED on 2026-06-23

Known gaps:
- None for `SPEC-103`; host-side PostgreSQL connectivity remains an environment limitation, covered by `migrations-check-compose`.

### 2026-06-23 — SPEC-103 — Integrated locally

Role: Ingeniero de software
Branch: main
Commit/PR: `d897f6c`
Status: Merged

Summary:
- Committed the review-approved `SPEC-103` backend projects/tasks implementation and harness updates to local `main`.
- Included migration `0005`, project/task API surfaces, endpoint tests, project memory, and the sandbox-friendly validation targets.

Validation:
- command: `make verify-no-db`: PASS — lint, format, backend/frontend type checks, backend tests, and frontend tests passed before commit.
- command: `make migrations-check-compose`: NOT RUN in final integration session — Docker CLI is not available in this WSL environment; prior `SPEC-103` migration validation passed outside sandbox and is recorded below.
- command: `git diff --cached --check`: PASS before commit.

Review:
- decision: APPROVED on 2026-06-23

Known gaps:
- Commit is local only; push/PR publication remains pending.

### 2026-06-23 — SPEC-103 — Harness sandbox targets added

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added `make verify-no-db` for lint, format, type checks, and non-DB tests without Docker/PostgreSQL access.
- Kept `make verify` as the complete check by delegating to `verify-no-db` plus `migrations-check`.
- Added `make migrations-check-compose` to run Alembic upgrade/check from inside the backend container through Compose networking.
- Updated local validation docs to explain sandbox permission constraints for host PostgreSQL ports and Docker socket access.

Validation:
- command: `make verify-no-db`: PASS — lint, format, backend/frontend type checks, backend tests, and frontend tests passed.
- command: `make migrations-check-compose`: FAIL in sandbox — Docker socket access was denied before elevation.
- command: `make migrations-check-compose`: PASS outside sandbox — Alembic upgrade/check passed inside the backend container.
- command: `git diff --check`: PASS.

Review:
- decision: N/A — harness documentation/target refinement after `SPEC-103` review approval.

Known gaps:
- None.

### 2026-06-23 — SPEC-103 — Review approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-103` implementation against the feature spec, `SPEC-001`, `ADR-002`, `ADR-007`, project memory, migration `0005`, routes, services, repositories, schemas, and endpoint tests.
- Confirmed tenant-aware project/task lookups hide non-member resources with `404`, known members without action permission receive `403`, task assignees are organization members, archived projects reject new tasks, and `completed_at` follows `done` transitions.
- Verified project memory reflects `SPEC-103` implementation and validation evidence.

Validation:
- command: `make test-backend`: PASS — 65 passed, 2 DB tests deselected.
- command: `make lint`: PASS — backend Ruff and frontend ESLint passed.
- command: `git diff --check`: PASS.
- command: prior `make verify`: PASS outside sandbox — lint, format, backend/frontend type checks, backend/frontend tests, migration upgrade, and Alembic check passed.
- command: prior `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-103`; frontend organization/project/task UI remains future spec work.

### 2026-06-23 — SPEC-103 — Projects and tasks implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added project/task SQLAlchemy models, public enums, migration `0005`, schemas, repositories, services, and FastAPI routers.
- Registered project/task routes and implemented tenant-aware lookups that hide cross-tenant resources with `404` while returning `403` for known members without action permission.
- Enforced same-organization assignees, member self-assignment limits, owner/admin reassignment, archived-project task rejection, task filters, and `completed_at` transitions.
- Added endpoint-level tests for the `SPEC-103` acceptance criteria and updated project memory for review handoff.
- Fixed the initial PostgreSQL enum migration issue by creating enum types explicitly and reusing them with `create_type=False`.

Validation:
- command: `cd backend && poetry run ruff check .`: PASS.
- command: `cd backend && poetry run ruff format --check .`: PASS after formatting the new migration.
- command: `cd backend && poetry run pytest -m "not db"`: PASS — 65 passed, 2 DB tests deselected.
- command: `make typecheck`: PASS — backend mypy and frontend TypeScript checks passed.
- command: `make migrations-check`: PASS outside sandbox — migration `0005` applied and Alembic found no new upgrade operations.
- command: `docker compose exec backend poetry run alembic upgrade head`: PASS outside sandbox after rebuilding backend image with the corrected migration.
- command: `docker compose exec backend poetry run alembic check`: PASS outside sandbox — no new upgrade operations detected.
- command: `make verify`: PASS outside sandbox — lint, format, backend/frontend type checks, backend/frontend tests, migration upgrade, and Alembic check passed.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: N/A — implementation awaits review.

Known gaps:
- `SPEC-103` review approval remains pending.
- Frontend organization/project/task UI remains intentionally outside `SPEC-103`.

### 2026-06-23 — SPEC-103 — Implementation handoff refreshed

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed agent-facing repository instructions, `docs/agent-workflow.md`, `docs/project-state.md`, spec index, current validation baseline, and relevant ADRs after the previous Codex session ended.
- Updated project state to reflect that `main` is current, `SPEC-102` is published and review approved, and `SPEC-103` is the next implementation target.
- Added a SPEC-103 implementation handoff with likely backend files, first implementation slice, and key tenant/RBAC/archive/status-transition risks.

Validation:
- command: `git status -sb`: PASS — clean before documentation edits.
- command: `git log --oneline --decorate -5`: PASS — confirmed HEAD is `da852c0` on `main` with `origin/main`.
- command: `git diff --check`: PASS — documentation/spec handoff edits have no whitespace errors.
- command: implementation harness NOT RUN — documentation/spec handoff only; product code was not changed.

Review:
- decision: N/A

Known gaps:
- `SPEC-103` still needs implementation and validation by Ingeniero de software.

### 2026-06-18 — SPEC-102 — AC-15 review fix approved

Role: Ingeniero de software and Review agent
Branch: codex/spec-102-organizations-rbac
Commit/PR: `7d404fd` / draft PR `#3`
Status: Reviewed

Summary:
- Added the missing endpoint assertion that an organization `member` receives `403 insufficient_role` when attempting permanent organization deletion.
- Re-reviewed AC-15 alongside the existing admin `403`, non-member `404`, owner deletion, user retention, membership cascade, and slug-reuse assertions.
- Updated project memory to mark `SPEC-102` implemented and review approved.

Validation:
- command: `make test-backend`: PASS — 53 passed, 2 DB tests deselected.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make verify`: PASS outside sandbox — lint, format, backend/frontend type checks and tests, migration `0004`, and Alembic drift checks passed.
- command: `make test-backend-db`: PASS outside sandbox — 2 PostgreSQL tests passed, including concurrent ownership transfer.

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-102`; invitations remain explicitly outside its scope.

### 2026-06-18 — SPEC-102 — Single-owner revision changes requested

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the revised single-owner model, migration `0004`, generic role restrictions, ownership transfer, permanent deletion, tenant isolation, audit behavior, tests, and project memory against `SPEC-102`, `SPEC-001`, and `ADR-007`.
- Confirmed the implementation preserves one owner, serializes concurrent transfers/deletion, revalidates ownership after locking, rolls back failed transfers, retains users on deletion, and reuses deleted slugs.
- Found one acceptance-test gap: AC-15 requires both admin and member deletion attempts to return `403`, but the deletion test covers admin and non-member only.

Validation:
- command: `make test-backend`: PASS — 53 passed, 2 DB tests deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS — backend and frontend checks passed.
- command: `make smoke test-backend-db migrations-check`: PASS — services responded, 2 PostgreSQL tests passed, migration `0004` was current, and Alembic found no new operations.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Add endpoint-level coverage asserting a `member` receives `403 insufficient_role` from `DELETE /api/v1/organizations/{organization_id}`, then rerun the affected tests and request re-review.

### 2026-06-18 — SPEC-102 — Single-owner revision implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added migration `0004` and matching SQLAlchemy metadata for a unique partial owner index per organization.
- Restricted generic membership role/removal operations from assigning, demoting, or removing the owner role.
- Added atomic ownership transfer with organization-row locking, post-lock owner revalidation, ordered demotion flush, rollback on persistence failure, and audit logging.
- Added owner-only permanent organization deletion with serialized locking, membership cleanup, retained user accounts, slug reuse, and audit logging.
- Expanded endpoint coverage and added a PostgreSQL concurrency test forcing two transfers to authorize before competing for the same organization lock.

Validation:
- command: `make verify`: PASS — lint, format, strict backend/frontend types, 53 backend tests, 12 frontend tests, `alembic upgrade head`, and `alembic check` passed.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make test-backend-db`: PASS — 2 PostgreSQL tests passed, including concurrent ownership transfer.
- command: `make migrations-check`: PASS — migration `0004` applied and Alembic detected no new upgrade operations.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: N/A — revised implementation awaits review.

Known gaps:
- No implementation gaps identified; review approval remains pending.

### 2026-06-18 — SPEC-102 — Single-owner policy and organization deletion spec refresh

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Replaced multiple-owner/last-owner policy with exactly one owner per organization.
- Added a dedicated atomic ownership-transfer contract that promotes an existing member and demotes the previous owner to admin.
- Prevented generic membership role/removal endpoints from assigning, demoting, or removing the owner role.
- Added owner-only permanent organization deletion with membership cleanup, retained user accounts, and slug reuse.
- Added migration, PostgreSQL concurrency, audit, error, and acceptance requirements, and aligned `ADR-007` with the revised policy.

Validation:
- command: `git diff --check`: PASS.
- command: implementation harness NOT RUN — spec/ADR/project-memory-only change; implementation validation is required after code alignment.

Review:
- decision: N/A

Known gaps:
- Existing organization code, migration, and tests implement the superseded multiple-owner policy and must be updated before `SPEC-102` can return to review.

### 2026-06-18 — SPEC-102 — Review blocked by owner-removal policy gap

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Blocked

Summary:
- Reviewed the complete implementation against `SPEC-102`, `SPEC-001`, `ADR-007`, migration `0003`, tests, and project memory.
- Found conflicting source-of-truth rules for deleting owners: the permissions table and endpoint description allow removing only non-owner members, while BR-10 and the documented `last_owner_required` delete error imply that a non-final owner may be removed.
- Confirmed the implementation permits deleting an owner whenever another owner remains, but no acceptance test covers that policy choice.

Validation:
- command: `make test-backend`: PASS — 47 passed, 1 DB test deselected.
- command: `make lint`: PASS.
- command: `make format-check`: PASS.
- command: `make typecheck`: PASS — backend and frontend checks passed.
- command: `make smoke migrations-check`: PASS — services responded, migration `0003` was current, and Alembic detected no new upgrade operations.
- command: `git diff --check`: PASS before this memory update.

Review:
- decision: BLOCKED_BY_SPEC_GAP

Known gaps:
- An Arquitecto de specs must decide whether deleting a non-final owner is allowed and document the expected status/error when it is not. Implementation and endpoint tests must then match that decision before re-review.

### 2026-06-18 — SPEC-102 — Review approved

Role: Review agent
Branch: main
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed models, migration, repository scoping, service authorization, HTTP contracts, acceptance tests, project memory, and `ADR-007` against `SPEC-102` and `SPEC-001`.
- Confirmed all ten acceptance criteria have endpoint-level coverage and tenant access consistently returns `404` for non-members versus `403` for underprivileged members.
- Moved the final user lookup for role-change responses out of the route and behind the existing user repository boundary.

Validation:
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend built, started, and responded.
- command: `make verify`: PASS — lint, format, strict backend/frontend types, 47 backend tests, 12 frontend tests, live `alembic upgrade head`, and `alembic check` passed.
- command: `poetry run pytest tests/test_organizations_api.py -q`: PASS — 12 passed after the review adjustment.
- command: `poetry run ruff check . && poetry run ruff format --check .`: PASS.
- command: `poetry run mypy app`: PASS — no issues in 27 source files.
- command: `git diff --check`: PASS after removing modified Markdown trailing whitespace.

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-102`; invitations remain explicitly outside its scope.

### 2026-06-18 — SPEC-102 — Organizations and RBAC implemented

Role: Ingeniero de software
Branch: main
Commit/PR: Pending
Status: Implemented

Summary:
- Added organization and membership models with owner/admin/member roles, migration `0003`, uniqueness constraints, and tenant lookup indexes.
- Added organization schemas, tenant-scoped repository queries, service-owned isolation/RBAC policy, final-owner locking, role-change audit logging, and all specified organization/member routes.
- Added 12 endpoint-level tests covering creation, owner membership, slug behavior, tenant isolation, pagination, role permissions, final-owner protection, updates, safe member listing, and membership-only deletion.
- Added `ADR-007` to preserve the tenant isolation and RBAC enforcement pattern for `SPEC-103`.

Validation:
- command: `make test-backend`: PASS — 47 passed, 1 DB test deselected.
- command: `make typecheck`: PASS — backend strict mypy and frontend TypeScript checks passed.
- command: `poetry run alembic upgrade head --sql`: PASS — PostgreSQL DDL generated through migration `0003`.
- command: `make smoke`: PASS — PostgreSQL, backend, Adminer, and frontend started and responded.
- command: `make migrations-check`: PASS — migration `0003` applied to live PostgreSQL and Alembic detected no new upgrade operations.
- command: `make lint`: PASS after fixing one test import-order issue found by the initial run.
- command: `make format-check`: PASS after formatting migration `0003` following the initial run.
- command: `make verify`: PASS — all backend/frontend checks and live migration validation passed.

Review:
- decision: APPROVED on 2026-06-18.

Known gaps:
- None for `SPEC-102`; invitations remain explicitly outside its scope.

### 2026-06-17 — SPEC-002 — Review approved

Role: Review agent
Branch: main
Commit/PR: `86a1332`
Status: Reviewed

Summary:
- Reviewed `SPEC-002` implementation against the human-readable comment convention and source-of-truth caveat.
- Verified file-level comments/docstrings exist on source files under `backend/` and `frontend/` that are in scope.
- Verified representative function/class/component/hook/helper comments are concise and behavior-preserving.
- Updated project state to reflect successful Docker-backed validation and approval.

Validation:
- command: `make smoke`: PASS — Docker Compose built/started PostgreSQL, backend, Adminer, and frontend; health/Adminer/frontend checks succeeded.
- command: `make verify`: PASS outside sandbox — lint, format, typecheck, backend tests, frontend tests, `alembic upgrade head`, and `alembic check` passed.
- command: `git diff --check`: PASS

Review:
- decision: APPROVED

Known gaps:
- None for `SPEC-002`.

### 2026-06-17 — SPEC-002 — Human-readable code comments implemented

Role: Ingeniero de software
Branch: main
Commit/PR: `86a1332`
Status: Implemented

Summary:
- Added file-level comments/docstrings to existing backend, frontend, test, migration, and frontend configuration source files.
- Added concise explanatory comments/docstrings to backend functions/classes, test helpers/fixtures/cases, frontend components/hooks/helpers/types, and migration functions.
- Updated project memory and spec index so `SPEC-002` is implemented and awaiting review.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 12 passed.
- command: `make typecheck`: PASS
- command: `make verify`: FAIL — lint, format, typecheck, backend tests, and frontend tests passed; Alembic migration check failed because local PostgreSQL was not accepting connections.
- command: `make verify` outside sandbox: FAIL — same non-Docker checks passed; Alembic failed with connection refused to `127.0.0.1:5432`.
- command: `make smoke`: FAIL — Docker is not installed in this WSL distro, so PostgreSQL/local services could not be started.
- command: `git diff --check`: PASS

Review:
- decision: APPROVED on 2026-06-17

Known gaps:
- Resolved by the review entry above.

### 2026-06-17 — SPEC-002 — Human-readable code comments spec

Role: Arquitecto de specs
Branch: main
Commit/PR: `86a1332`
Status: Ready

Summary:
- Added `SPEC-002` for repository-wide human-readable file/function/class comments and the initial existing-code comment pass.
- Updated `AGENTS.md` to make the convention mandatory for future source code while clarifying comments are reader support, not source-of-truth material for agents.
- Added `ADR-006` to record the durable decision and updated spec routing/project state so `SPEC-002` is the next implementation target.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Resolved by the implementation entry above.

### 2026-06-16 — SPEC-104 — Merged locally to main

Role: Ingeniero de software
Branch: main
Commit/PR: `5d019bd`, merge commit pending push
Status: Merged

Summary:
- Committed `SPEC-104` implementation as `5d019bd`.
- Pushed branch `spec-104-frontend-auth-shell` to origin.
- Merged `spec-104-frontend-auth-shell` into local `main`.
- Updated project state so future agents start from `main` and treat `SPEC-102` as the next likely implementation target.

Validation:
- command: NOT RUN after merge — merge was clean; pre-merge `make smoke` and `make verify` passed and are recorded below.

Review:
- decision: APPROVED

Known gaps:
- `main` push and feature-branch deletion still pending in this publishing step.

### 2026-06-16 — SPEC-104 — Final review approved

Role: Review agent
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed the profile `401` review fix for `SPEC-104`.
- Verified `PATCH /api/v1/users/me` now clears session state and redirects to `/login` on `401 not_authenticated`.
- Verified test coverage for profile update losing authentication.
- Verified project memory reflects the fixed state and validation baseline.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run test`: PASS — 12 passed.
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run build`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 12 passed.
- command: `git diff --check`: PASS
- command: `make smoke`: PASS outside sandbox — recorded in the review-fix entry.
- command: `make verify`: PASS outside sandbox — recorded in the review-fix entry.

Review:
- decision: APPROVED

Known gaps:
- No E2E browser tests yet; `SPEC-104` recommends adding Playwright later after the frontend/local server harness stabilizes.

### 2026-06-16 — SPEC-104 — Profile 401 review fix

Role: Ingeniero de software
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Implemented

Summary:
- Fixed `PATCH /api/v1/users/me` profile update handling so `401 not_authenticated` clears the session query state and redirects to `/login`.
- Added frontend route test coverage for profile update losing authentication.
- Updated project memory to reflect the review fix and current validation baseline.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run format:check`: PASS
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run test`: PASS — 12 passed.
- command: `cd frontend && npm run build`: PASS
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 12 passed.
- command: `make smoke`: PASS outside sandbox — Docker Compose built/started backend, PostgreSQL, Adminer, and frontend; `/health`, Adminer, and `http://127.0.0.1:5173` responded.
- command: `make verify`: PASS outside sandbox — lint, format, typecheck, tests, Alembic upgrade, and Alembic check passed.

Review:
- decision: N/A

Known gaps:
- No E2E browser tests yet; `SPEC-104` recommends adding Playwright later after the frontend/local server harness stabilizes.

### 2026-06-16 — SPEC-104 — Review changes requested

Role: Review agent
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed `SPEC-104` frontend app shell/auth UI implementation against the spec, API conventions, project memory, and current diff.
- Verified the frontend app shell, public/auth routes, auth/profile forms, API client credential handling, future navigation unavailable state, Make/Compose integration, and memory updates.
- Found one required fix: profile update `401 not_authenticated` responses currently render an error instead of clearing session state and redirecting to `/login`, which conflicts with `SPEC-104` profile and failure-case requirements.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run format:check`: PASS
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run test`: PASS — 11 passed.
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 11 passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, PostgreSQL, Adminer, and frontend; `/health`, Adminer, and `http://127.0.0.1:5173` responded.
- command: `make migrations-check`: PASS outside sandbox — sandboxed process could not connect to local `localhost:5432`.
- command: `make verify`: PASS outside sandbox — lint, format, typecheck, tests, Alembic upgrade, and Alembic check passed.

Review:
- decision: CHANGES_REQUESTED

Known gaps:
- Add/fix profile-call `401` handling and test coverage before push.

### 2026-06-16 — Repository memory — Agent operational state and routing

Role: Arquitecto de specs
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Ready

Summary:
- Added `docs/project-state.md` as the compact current-state dashboard for active work, implemented specs, next likely work, known gaps, validation baseline, code map, and reading order.
- Expanded `specs/README.md` into a richer routing index with dependencies, primary implementation surfaces, and a central touch-to-spec routing table.
- Updated `docs/agent-workflow.md` so agents start from `docs/project-state.md` and follow the current implementation order.
- Added `Scope And Required Context` sections to the feature spec template and existing feature specs.
- Updated `AGENTS.md` to make `docs/project-state.md` part of required project memory.
- Added `ADR-005` to capture the durable decision to split current operational memory from historical implementation evidence.

Validation:
- command: NOT RUN — documentation/process-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-104` implementation remains locally implemented with uncommitted changes and still needs review/commit.

### 2026-06-15 — SPEC-104 — Frontend auth shell implemented

Role: Ingeniero de software
Branch: spec-104-frontend-auth-shell
Commit/PR: Pending
Status: Implemented

Summary:
- Created the initial React TypeScript frontend under `frontend/` with Vite, React Router, TanStack Query, React Hook Form, Zod, Tailwind CSS, Vitest, and Testing Library.
- Implemented the public landing page, login, signup, authenticated app shell, protected/public route guards, logout, and profile view/update flows against the `SPEC-101` API contract.
- Added disabled/unavailable future navigation for organizations, projects, and tasks without fake backend data or unsupported CRUD.
- Integrated the frontend into Docker Compose, `.env.example`, README setup, local validation docs, and Make targets.
- Updated frontend dev dependencies to Vite `8.0.16`, Vitest `4.1.9`, and `@vitejs/plugin-react` `6.0.2`; `npm audit` reports 0 vulnerabilities.

Validation:
- command: `cd frontend && npm run lint`: PASS
- command: `cd frontend && npm run format:check`: PASS
- command: `cd frontend && npm run typecheck`: PASS
- command: `cd frontend && npm run test`: PASS — 11 passed.
- command: `cd frontend && npm run build`: PASS
- command: `cd frontend && npm audit --omit=dev`: PASS — 0 vulnerabilities.
- command: `cd frontend && npm audit`: PASS — 0 vulnerabilities after Vite/Vitest update.
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS
- command: `make test`: PASS — backend 35 passed, 1 DB test deselected; frontend 11 passed.
- command: `make smoke`: PASS — Docker Compose built/started backend, PostgreSQL, Adminer, and frontend; `/health`, Adminer, and `http://127.0.0.1:5173` responded.
- command: `make verify`: PASS — required running outside the sandbox because the sandboxed process could not connect to local `localhost:5432`; lint, format, typecheck, tests, Alembic upgrade, and Alembic check passed.

Review:
- decision: N/A

Known gaps:
- No E2E browser tests yet; SPEC-104 recommends adding Playwright later after the frontend/local server harness stabilizes.
- Organization, project, and task UI remains intentionally unavailable until their frontend specs are active.

### 2026-06-15 — SPEC-104 — Frontend app shell and auth UI spec

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed current specs and completed backend `SPEC-101` work.
- Added `SPEC-104` for the initial React frontend, public landing page, login/signup flows, authenticated app shell, logout, and profile management.
- Reserved navigation/product structure for future organizations, projects, and tasks without allowing fake data or unsupported CRUD before `SPEC-102`/`SPEC-103` frontend work.
- Updated the spec index and dependency order so frontend auth shell follows backend auth and precedes future product UI expansion.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Frontend implementation pending.
- A frontend package-manager ADR may be needed during implementation if the project chooses anything other than npm.

### 2026-06-15 — SPEC-101 — Review approved after uvloop API tests

Role: Review agent
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Reviewed

Summary:
- Reviewed SPEC-101 endpoint-level API test changes after Docker was available.
- Verified the auth API tests now exercise public HTTP endpoints with FastAPI `TestClient` and `uvloop`.
- Verified logout now returns a real `204` response through the HTTP layer.
- Verified migrations, Docker smoke checks, DB test, lint, formatting, typecheck, and backend tests.

Validation:
- command: `make smoke`: PASS — Compose built/started backend, PostgreSQL, and Adminer; backend `/health` and Adminer HTTP checks passed.
- command: `make verify`: PASS — lint, format-check, backend tests, Alembic upgrade, and Alembic check passed.
- command: `make typecheck`: PASS — no issues in 22 source files.
- command: `make test-backend-db`: PASS — 1 passed, 35 deselected.
- command: `docker compose exec -T postgres pg_isready -U opdesk -d opdesk`: PASS — PostgreSQL accepting connections.

Review:
- decision: APPROVED

Known gaps:
- None for the SPEC-101 backend/API test scope. Frontend auth screens remain pending until frontend scaffold exists.

### 2026-06-15 — SPEC-101 — Endpoint-level auth API tests with uvloop

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Added endpoint-level SPEC-101 API tests using FastAPI `TestClient` with `backend_options={"use_uvloop": True}`.
- Added test dependency overrides for isolated SQLite DB sessions and auth settings.
- Covered register success, duplicate email, weak password, first-user superuser, later-user non-superuser, login success/failure/inactive user, refresh success/failure, logout cookie clearing, `/api/v1/users/me` unauthenticated/authenticated, profile update, and invalid profile through public HTTP endpoints.
- Fixed `POST /api/v1/auth/logout` to return an actual `204` status when returning the injected FastAPI `Response`.

Validation:
- command: `cd backend && poetry run pytest tests/test_auth_and_users.py`: PASS — 31 passed
- command: `make test-backend`: PASS — 35 passed, 1 DB test deselected
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make typecheck`: PASS — no issues in 22 source files
- command: `make verify`: FAIL/ENV — lint, format, and backend tests passed, then `migrations-check` failed because PostgreSQL/Docker was unavailable from this WSL session.
- command: `docker compose ps`: FAIL/ENV — Docker CLI not available in this WSL distro.

Review:
- decision: N/A

Known gaps:
- Docker-backed migration, DB, smoke, and full verify checks remain unverified in this session until Docker is available from WSL again.

### 2026-06-15 — SPEC-101 — uvloop added to API test harness specs

Role: Arquitecto de specs
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed API and validation specs after the ASGI client investigation.
- Added `uvloop` guidance to `specs/harness/local-validation.md` for in-process backend API tests using FastAPI `TestClient` or HTTPX `ASGITransport`.
- Updated `SPEC-101` to prefer `uvloop` for in-process ASGI tests when synchronous endpoints or dependencies hang under the default `asyncio` event loop.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- Implementation still needs to update SPEC-101 API tests to use endpoint-level HTTP coverage.

### 2026-06-15 — SPEC-101 — ASGI investigation readability update

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Rewrote `docs/spec-101-asgi-client-investigation.md` command examples as readable multiline shell heredocs.
- Preserved the investigation results and recommendation to use `uvloop` for in-process API tests, with Docker/local HTTP as fallback.

Validation:
- command: NOT RUN — documentation-only readability change.

Review:
- decision: N/A

Known gaps:
- SPEC-101 still needs automated API tests that exercise public HTTP endpoints.

### 2026-06-15 — SPEC-101 — API test clarification and ASGI client investigation

Role: Arquitecto de specs / Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Clarified in `SPEC-101` that API tests may use in-process ASGI clients or local Docker HTTP, but must exercise public HTTP endpoints and cookie/error behavior.
- Investigated why FastAPI `TestClient` and HTTPX `ASGITransport` hang in the local environment.
- Added `docs/spec-101-asgi-client-investigation.md` with reproduction steps, command evidence, likely causes, and recommended solutions.
- Found that the hang reproduces below FastAPI in AnyIO/asyncio thread wakeups, and that `uvloop` resolves the minimal reproductions.

Validation:
- command: minimal FastAPI `TestClient` without `uvloop`: FAIL/REPRODUCED — request hangs until timeout.
- command: minimal HTTPX `ASGITransport` with async endpoint: PASS.
- command: minimal HTTPX `ASGITransport` with sync endpoint: FAIL/REPRODUCED — request hangs until timeout.
- command: isolated `anyio.to_thread.run_sync`: FAIL/REPRODUCED — hangs until timeout.
- command: Python `threading` and `ThreadPoolExecutor`: PASS — native threads work.
- command: `asyncio.call_soon_threadsafe` with default event loop: FAIL/REPRODUCED — worker runs but loop does not wake without another timer.
- command: `asyncio.call_soon_threadsafe`, `anyio.to_thread.run_sync`, FastAPI `TestClient`, and HTTPX `ASGITransport` with `uvloop`: PASS.

Review:
- decision: N/A

Known gaps:
- SPEC-101 still needs automated API tests that exercise public HTTP endpoints. Recommended next step is FastAPI `TestClient(app, backend_options={"use_uvloop": True})`, with Docker/local HTTP as fallback.

### 2026-06-11 — SPEC-101 — Backend auth and users implemented

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Implemented

Summary:
- Implemented backend auth/user API endpoints for registration, login, refresh, logout, current user, and profile update.
- Added `users` SQLAlchemy model, repository/service layers, Pydantic schemas, API error shape, auth dependencies, Argon2 password hashing, and signed JWT cookies.
- Added Alembic migration `0002` for `users`.
- Added auth settings and safe local placeholders to `.env.example`.
- Added backend tests for password policy/hash, register/login/refresh/logout, current user, profile update, inactive user handling, duplicate email, and first-user superuser behavior.
- Updated README and spec index to reflect implemented backend auth scope.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 21 passed, 1 DB test deselected
- command: `make typecheck`: PASS — no issues in 22 source files
- command: `make migrations-check`: PASS — migration `0002` applied and Alembic check found no new upgrade operations
- command: `make test-backend-db`: PASS — 1 passed, 21 deselected
- command: `make smoke`: PASS — backend and Adminer responded after Docker rebuild
- command: `make verify`: PASS
- command: direct `curl` register/login against Docker backend: PASS — registration returned safe user payload and login set httpOnly `access_token`/`refresh_token` cookies.

Review:
- decision: N/A

Known gaps:
- Frontend auth screens remain pending because the frontend scaffold does not exist yet.
- In-process HTTP client tests using FastAPI `TestClient`/HTTPX ASGI transport hang in this environment, so backend tests exercise route functions directly and Docker `curl` smoke covers real HTTP register/login.

### 2026-06-11 — SPEC-101 — Auth spec refresh after scaffold/admin tooling

Role: Arquitecto de specs
Branch: spec-011-local-database-admin
Commit/PR: Pending
Status: Ready

Summary:
- Reviewed `SPEC-101` after `SPEC-010` scaffold and `SPEC-011` local DB admin work.
- Clarified that Adminer is inspection-only and not a functional dependency for auth behavior.
- Added auth configuration contract for token/cookie settings and updated harness expectations to current Make targets.
- Added test-state guidance for first-user superuser bootstrap.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-101` implementation still pending.

### 2026-06-11 — SPEC-011 — Review approved

Role: Review agent
Branch: spec-011-local-database-admin
Commit/PR: `269149c`, PR https://github.com/RGAlvaro/opdesk/pull/2
Status: Reviewed

Summary:
- Reviewed `SPEC-011` implementation after the Adminer port override fix.
- Verified local-only Adminer wiring, docs, ADR, harness updates, and implementation log evidence.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `docker compose config`: PASS — Adminer binds to localhost and uses the configured port.
- command: `make smoke`: PASS — verified both `.env` override path on `8081` during fix validation and default `8080` after removing temporary `.env`.

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-06-11 — SPEC-011 — Adminer port override review fix

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: `ff11f48`, PR https://github.com/RGAlvaro/opdesk/pull/2
Status: Implemented

Summary:
- Updated `Makefile` so Make includes `.env` when present and exports its variables to recipes.
- Added a default `ADMINER_PORT ?= 8080` and made `make smoke` curl `$(ADMINER_PORT)`, aligning smoke checks with Docker Compose `.env` resolution.

Validation:
- command: `make -n smoke` without `.env`: PASS — Adminer curl resolves to `http://127.0.0.1:8080`.
- command: temporary `.env` with `ADMINER_PORT=8081` plus `make -n smoke`: PASS — Adminer curl resolves to `http://127.0.0.1:8081`.
- command: temporary `.env` with `ADMINER_PORT=8081` plus `docker compose config`: PASS — Adminer publishes `127.0.0.1:8081`.
- command: temporary `.env` with `ADMINER_PORT=8081` plus `make smoke`: PASS — backend health returned `{"status":"ok"}` and Adminer returned the login page on port `8081`.
- command: `make smoke` after removing temporary `.env`: PASS — backend health returned `{"status":"ok"}` and Adminer returned the login page on default port `8080`.
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `docker compose ps`: PASS — `adminer`, `backend`, and healthy `postgres` services are running.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-06-10 — SPEC-011 — Local database admin implemented

Role: Ingeniero de software
Branch: spec-011-local-database-admin
Commit/PR: `d240330`, PR https://github.com/RGAlvaro/opdesk/pull/2
Status: Implemented

Summary:
- Added local-only Adminer service to Docker Compose with localhost host binding and default PostgreSQL server wiring.
- Documented Adminer URL, login values, local-only scope, and manual-edit caveat in README.
- Added `ADMINER_PORT` to `.env.example` and Adminer HTTP check to local smoke validation.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `rg -n "adminer|ADMINER" docker-compose.yml .env.example Makefile README.md specs/harness/local-validation.md specs/features/011-local-database-admin.md docs/decisions/ADR-004-local-database-admin-tool.md docs/implementation-log.md`: PASS — local Adminer wiring and docs present.
- command: `test -f docker-compose.prod.yml && rg -n "adminer|ADMINER" docker-compose.prod.yml || true`: PASS — no production Compose file exists yet, so Adminer is not present in production config.
- command: `docker compose config`: PASS — Adminer is configured on `127.0.0.1:8080` and depends on healthy PostgreSQL.
- command: `make smoke`: PASS — backend health returned `{"status":"ok"}` and Adminer returned the login page.
- command: `docker compose ps`: PASS — `adminer`, `backend`, and healthy `postgres` services are running.

Review:
- decision: N/A

Known gaps:
- None.

### 2026-06-10 — SPEC-011 — Local database admin spec

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Added `SPEC-011` for a local-only Adminer panel to inspect the Docker Compose PostgreSQL database.
- Updated the spec index and implementation order.
- Added ADR-004 to record the Adminer-over-pgAdmin local tooling decision and production exclusion.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-011` implementation still pending.

### 2026-06-09 — SPEC-010 — Backend scaffold implemented

Role: Ingeniero de software
Branch: spec-010-backend-scaffold
Commit/PR: `be18383`, `36f9757`, `d97031d`, `ea31737`, `3c84c46`, PR https://github.com/RGAlvaro/opdesk/pull/1, merge `ac242cd`
Status: Merged

Summary:
- Implemented FastAPI backend scaffold with `/health`, settings, SQLAlchemy session setup, Alembic baseline wiring, empty baseline revision, and backend tests.
- Added local PostgreSQL and backend services through Docker Compose with named PostgreSQL volume and health gating.
- Added `.env.example`, `Makefile`, `README.md`, `backend/Dockerfile`, backend `.dockerignore`, and Poetry lockfile.
- Added ADRs for package manager choice, backend module layout, and local/container database URL strategy.
- Tightened `AGENTS.md` memory rules so review-fix commits and validation reruns must update this log before review.

Validation:
- command: `make lint`: PASS
- command: `make format-check`: PASS
- command: `make test-backend`: PASS — 4 passed, 1 DB test deselected
- command: `make typecheck`: PASS
- command: `make migrations-check`: PASS — no new upgrade operations detected
- command: `make test-backend-db`: PASS — 1 DB test passed against Docker PostgreSQL
- command: `make smoke`: PASS — Docker Compose backend/PostgreSQL started and `/health` returned `{"status":"ok"}`
- command: `make verify`: PASS — includes `alembic upgrade head` and `alembic check`

Review:
- decision: APPROVED

Known gaps:
- None.

### 2026-06-09 — SPEC-010 — ADR requirement before implementation

Role: Arquitecto de specs
Branch: main
Commit/PR: Pending
Status: Ready

Summary:
- Clarified that `SPEC-010` implementation must create ADRs for durable scaffold choices.
- Required ADR coverage for package manager choice, backend module layout, and local/container database configuration strategy.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-010` implementation still pending.

### 2026-06-09 — SPEC-010 — Backend scaffold foundation spec

Role: Arquitecto de specs
Branch: main
Commit/PR: `fe4e493`
Status: Ready

Summary:
- Added `SPEC-010` for backend scaffold, local PostgreSQL, SQLAlchemy, Alembic, health checks, and harness.
- Updated dependency order so implementation starts with `SPEC-010` before auth, organizations, and tasks.
- Reframed `SPEC-301` as production deployment and operations built on top of the local scaffold.

Validation:
- command: NOT RUN — spec/documentation-only change.

Review:
- decision: N/A

Known gaps:
- `SPEC-201` remains Draft pending Redis/worker ownership and notification decisions.
- `SPEC-301` still needs final domain/DNS and VPS sizing decisions before production launch.
