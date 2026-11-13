# Agent governance (url-shortener-python)

This repo is a gated SDLC for a pure Python URL shortener. Specs in `specs/greenfield/` are binding. Do not invent APIs, dependencies, or coverage numbers.

The service is FastAPI. The UI is a separate Python process (Starlette and Jinja2). There is no Spring Boot module and no React app.

Cursor skill loader: `.cursor/skills/url-shortener-sdlc/SKILL.md` (opt-in). Scenario files under `specs/scenarios/` are evaluation indexes. They do not generate code.

## Before any work

1. Read `specs/greenfield/INSTRUCTIONS.md` and `specs/greenfield/ORCHESTRATION_MANIFEST.md`.
2. Use the other specs only for their role:
   - Product: `specs/greenfield/PRD.md`
   - Design: `specs/greenfield/SYSTEM_DESIGN.md`
   - Stack: `specs/greenfield/TECH_STACK.md`
   - Tests: `specs/greenfield/TESTING_PLAN.md`
   - Language: `specs/domain/glossary.md`
   - HTTP contract: `specs/contracts/openapi.yaml` (same paths and status codes as `PRD.md`)
   - Python UI: `specs/frontend/PRD.md`, `DESIGN.md`, `TECH_STACK.md`, `TESTING_PLAN.md`
3. Brownfield playbooks in `specs/brownfield/` apply only after Gate 4 is green. One playbook per change.

## Gate 2 lock (Stage 3)

Do not create or edit `backend/pyproject.toml`, `backend/src/**`, or other functional Python until the workspace root contains `GATE2_APPROVAL.txt` with a line `[APPROVED: HUMAN_ENGINEER_ID]`.

Allowed before approval: `specs/**`, `AGENTS.md`, `.cursor/rules/**`, `.cursor/skills/**`, `Dockerfile`, `docker-compose.yml`, `SDLC_AUDIT_LOG.json`, `SDLC_METRICS.json`.

If the approval file is missing, refuse to implement and tell the operator to write it (and optionally `git tag gate2-approved`).

## After approval

- Stage 3, all three before tests:
  - **3A** `backend/src/urlshortener/db/schema.sql`
  - **3B** `encode` / `decode` in `backend/src/urlshortener/encoding/base62.py`
  - **3C** FastAPI module (`backend/pyproject.toml`, `settings.py`, SQLAlchemy, routes, exception handlers)
- Stage 4–5: `TESTING_PLAN.md`. From `backend/`, `pytest` with line coverage ≥ 80%. No `pytest.mark.skip` or `pytest.mark.skipif` to force a green run. Max **3** repair retries, then Safe-Stop.
- Stage 6–7: containers, then measured entries in `SDLC_METRICS.json` and the Outputs section of `specs/scenarios/01-greenfield.md`.
- Log every mutation in `SDLC_AUDIT_LOG.json` (`INSTRUCTIONS.md`).

## High impact — stop and ask

Schema changes after Gate 2, `backend/pyproject.toml` dependencies not listed in `TECH_STACK.md`, or lowering the 80% / mandatory test bar.

## Out of the backend v1

Redis, Alembic, an authentication library, rate limiting, Safe Browsing, custom aliases, auth, click APIs.

## Frontend

Specs in `specs/frontend/` and `.cursor/rules/20-frontend-python.mdc` are binding when building the Python UI. That UI is not a backend dependency. Do not generate `frontend/src/**` or `frontend/pyproject.toml` during the API stages. The UI calls `POST /api/v1/shorten` only, and it does not add APIs.
