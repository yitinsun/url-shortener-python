---
name: url-shortener-sdlc
description: >-
  Runs the gated spec-first Python SDLC for this repo (PRD, design, stack,
  tests, Gate 2 HITL, pytest-cov, audit log). Use when implementing the URL
  shortener API from specs/greenfield, or when the user mentions AGENTS.md,
  Gate 2, or the backend SDLC.
disable-model-invocation: true
---

# URL shortener API SDLC

Cursor loads this file when the skill is attached. Product behavior lives in `specs/greenfield/`. Do not invent APIs, `pyproject.toml` dependencies, or coverage.

## Instructions

1. Read `AGENTS.md`.
2. Read `specs/greenfield/INSTRUCTIONS.md` and `specs/greenfield/ORCHESTRATION_MANIFEST.md`.
3. Read `PRD.md`, `SYSTEM_DESIGN.md`, `TECH_STACK.md`, and `TESTING_PLAN.md` in `specs/greenfield/` for their roles only.
4. Keep `specs/contracts/openapi.yaml` aligned with `PRD.md`.
5. Honor Gate 2: no `backend/pyproject.toml` or `backend/src/**` until `GATE2_APPROVAL.txt` contains `[APPROVED: …]`.
6. After approval, run 3A schema, 3B Base62, and 3C FastAPI together, then the Gate 4 pytest command from `backend/`.
7. Brownfield playbooks in `specs/brownfield/` start only after Gate 4. `specs/scenarios/` records evaluation; it does not generate code.
8. Do not create `frontend/src/**` in this skill. The Python UI specs live in `specs/frontend/` and are a separate pass.
