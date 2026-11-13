# 04 — Refine docs and measured lineage

Brownfield playbook. Run after `03-security-jsoup.md`. Documentation and metrics only, unless a line below says otherwise. Do not add Redis, Alembic, JWT, Safe Browsing, custom aliases, or a click-count column.

## README

Keep `README.md` accurate for the **Python** service and UI:

- Python 3.13, optional Docker.
- Tests: the pytest command from `TESTING_PLAN.md`, run in `backend/` (line coverage ≥ 80%).
- URLs: `POST /api/v1/shorten`, `GET /short/{code}`, `/docs`, `/openapi.json`.
- Pointers: `specs/greenfield/`, `specs/brownfield/`, `GATE2_APPROVAL.txt`, `SDLC_AUDIT_LOG.json`.
- Limits: lab passwords, sequential Base62, the create API is public.

## Metrics

Update `SDLC_METRICS.json` from real commands only:

- `coverage_line_ratio` is `covered_lines / num_statements` from `backend/coverage.json` after the Gate 4 pytest command.
- `stage1_epoch_ms`, `stage7_epoch_ms`, and `end_to_end_latency_ms` from the audit log, or leave them null and say Stage 7 is open.
- `retry_rollback_frequency` and `mttr_ms` only for repair loops that actually ran.

If Stage 6 has not been run, `docker compose up --build` once and append the result. If it was not run, do not claim an image.

## Lineage

New `SDLC_AUDIT_LOG.json` entries carry the SHA-256 of the governing file (`PRD.md`, `SYSTEM_DESIGN.md`, `TECH_STACK.md`, `TESTING_PLAN.md`, or the brownfield playbook). Do not write `"n/a"` when that file exists.

## Scenario index

Update Outputs in `specs/scenarios/01-greenfield.md` and `02-brownfield.md` so they list files that exist. Gate 6 fails when those sections claim coverage or Docker that the workspace does not have.

## Still halted

A `click_count` column, a stats API, and a metrics-exporter package need a new human signature. They are not part of this playbook.
