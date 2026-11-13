# Brownfield scenario

**Intent:** change the running API after Gate 4 without skipping the dependency allow-list, tests, or error pages. This file is an evaluation index. The playbooks generate the changes.

**Decomposition:** one playbook → impact → code and tests → the Gate 4 pytest command from `backend/`. A new `pyproject.toml` dependency or a table change waits for a human signature.

| Order | Change | Playbook | Modules | API / data |
|:------|:-------|:---------|:--------|:-----------|
| 1 | OpenAPI UI | `01-add-swagger.md` | FastAPI docs flags, `urlshortener.openapi`, Pydantic models already on the route | `/docs`, `/openapi.json` |
| 2 | Allowlist and HTML 404 for illegal paths | `02-legal-paths.md` | `LegalPathMiddleware`, `legal_paths`, error page | Fence around the greenfield routes. Redirect stays `GET /short/{code}` |
| 3 | Public routes + HTML rejection | `03-security-jsoup.md` | `html_sanitizer`, `SanitizeMiddleware` | 400 JSON if `longUrl` contains HTML. Routes stay public; no auth package |
| 4 | Docs and measured metrics | `04-refine.md` | README, audit log, scenario outputs | No schema |

**Orchestration path:** post–Gate 4, one playbook at a time. Greenfield already specifies `GET /short/{shortCode}`. Do not reopen that path as a second design.

**Validation:** after each playbook, the greenfield API tests still pass, plus the cases named in that playbook. Command remains the Gate 4 pytest command.

**Outputs:**

Playbooks 01, 02, 03, and 04 are applied.

- Docs: `backend/src/urlshortener/openapi.py`, `docs_url=/docs`, `openapi_url=/openapi.json`, redirect route `include_in_schema=False`. Prod leaves both URLs off unless `DOCS_ENABLED=true`. The lab Compose file sets that variable. `GET /docs` on the running API returned **200** HTML.
- Allowlist: `backend/src/urlshortener/web/legal_paths.py` (`is_legal`, `LegalPathMiddleware`) registered in `create_app` before routing. `GET /short/{code}` is unchanged. Illegal paths, including `GET /api/v1/shorten`, `/`, and `/metrics`, return the friendly HTML 404. `/docs` and `/openapi.json` are legal only while docs are enabled. A live `GET /` returned HTML **404**.
- HTML rejection: `beautifulsoup4` with the stdlib `html.parser`. `web/html_sanitizer.py` (`looks_unsafe`), `web/sanitize_middleware.py` (`SanitizeMiddleware`) after the allowlist, and `SanitizationError` mapped to the existing 400 JSON. No auth library. A plain `https://example.com/path` still returns 201. `longUrl` containing `<script>` or `<img>` returns 400 whose message says HTML sanitization. Illegal paths stay HTML 404.
- Docs pass: `README.md`, `SDLC_AUDIT_LOG.json`, `SDLC_METRICS.json`, and the Outputs sections of `01-greenfield.md` and this file. pytest from `backend/` on this pass: 45 tests, 0 failures. `coverage.json` totals are 433 covered lines and 482 statements (433/482). `coverage_line_ratio` is 0.8983402489626556. `stage7_epoch_ms` is 1794521641000. `stage1_epoch_ms`, `end_to_end_latency_ms`, and `mttr_ms` are null. `retry_rollback_frequency` is 2.
- No schema change. No metrics exporter. No click-count column.
- `frontend/` is the Starlette client in `frontend/src/urlshortener_web/`. It calls `POST /api/v1/shorten` only. pytest from `frontend/` on 2026-11-12: 15 tests, 0 failures. No frontend coverage percentage.
