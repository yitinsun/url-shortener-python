# Greenfield scenario

**Intent:** build the URL shortener API from specs. This file is an evaluation index. It does not generate code.

**Decomposition**

1. Requirements → `specs/greenfield/PRD.md` and `specs/contracts/openapi.yaml` (Gate 1: named APIs, Python 3.13, MySQL 8, Base62).
2. Architecture → `SYSTEM_DESIGN.md`, `TECH_STACK.md` (Gate 2: a human line `[APPROVED: …]` in `GATE2_APPROVAL.txt`).
3. Implementation in parallel, after approval (Gate 3 sync):
   - **3A** `backend/src/urlshortener/db/schema.sql`
   - **3B** `urlshortener.encoding.base62` + unit tests
   - **3C** `backend/pyproject.toml`, SQLAlchemy, routes, exception handlers
4. Tests / compliance (Gate 4): the pytest command in `TESTING_PLAN.md`, from `backend/`, line coverage ≥ 80%, bound parameters, no skipped tests.

**Orchestration path:** Stages 1→2→HITL→3A/3B/3C→4, as in `specs/greenfield/ORCHESTRATION_MANIFEST.md`.

**Validation (when Stage 4 runs):** `test_base62.py`, `test_url_shortener_service.py`, `test_expired_mapping_cleanup.py`, `test_url_shortener_api.py`. Command: the Gate 4 pytest command on Python 3.13 from `backend/`.

**Outputs present in the workspace:**

- `backend/pyproject.toml`, `backend/src/urlshortener/**` (including `db/schema.sql`, `encoding/base62.py`, `openapi.py`, `web/legal_paths.py`, `web/html_sanitizer.py`, `web/sanitize_middleware.py`), `backend/Dockerfile`, and root `docker-compose.yml`.
- Image `url-shortener-python-application:latest` exists. `docker image inspect` reports it created `2026-11-12T22:43:46Z` (`sha256:62bd1c28088ea6466e54e58af6a18495a231a1dff7dc672a55c614aed8c6c3b4`). `docker compose ps` shows MySQL 8.0 healthy with `3306/tcp` only inside the compose network, and the API on `0.0.0.0:8080`.
- The Stage 6 release `POST /api/v1/shorten` returned **201** with short code `3QkkP`. A live `GET /short/3QkkP` on 2026-11-12 still returns **302** to `https://example.com/api-design/api-design-url-shortening-service/`. `GET /docs` returns **200** HTML. `GET /` returns HTML **404**.
- pytest from `backend/` on 2026-11-12: 45 tests, 0 failures. `coverage.json` totals are 433 covered lines and 482 statements (433/482). `SDLC_METRICS.json` `coverage_line_ratio` is 0.8983402489626556. `stage7_epoch_ms` is 1794521641000, the audit-log RELEASE time `2026-11-12T22:14:01Z`. `stage1_epoch_ms` and `end_to_end_latency_ms` are null: the audit log has no Stage 1 timestamp. `retry_rollback_frequency` is 2. `mttr_ms` is null because those two repairs were not timed.
- `frontend/` is the Starlette client: `frontend/pyproject.toml` and `frontend/src/urlshortener_web/` (app, shorten, templates, styles, clipboard script, local fonts, and the four WebP photographs). pytest from `frontend/` on 2026-11-12: 15 tests, 0 failures. That plan has no coverage percentage.

Policy: `specs/greenfield/ORCHESTRATION_MANIFEST.md`. Stage 7 records this measured tree. The Python UI is not in this pass.
