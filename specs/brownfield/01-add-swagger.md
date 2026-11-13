# 01 — OpenAPI docs (FastAPI)

Brownfield playbook. Run only after Gate 4 is green. This playbook turns on documentation routes that greenfield left off. It does not add a dependency: FastAPI already serves the schema. It does not change status codes, the schema, or redirect behavior. The written contract stays `specs/contracts/openapi.yaml`.

This is the Python replacement for a springdoc Swagger UI. Paths are `/docs` and `/openapi.json`.

| Item | Value |
|:-----|:------|
| Module | `backend/` |
| Runtime | Python 3.13, FastAPI |
| Package | `urlshortener` |
| JSON API | `POST /api/v1/shorten` |
| Redirect | `GET /short/{shortCode}` → **302** (hide from the schema) |

After enablement: `http://localhost:8080/docs` and `http://localhost:8080/openapi.json`.

## 1. App flags

In `dev` and `test`, set:

* `docs_url="/docs"`
* `redoc_url=None`
* `openapi_url="/openapi.json"`

Both doc routes honor `DOCS_ENABLED` (default `true` in dev, `false` in prod). When the flag is false, set `docs_url` and `openapi_url` back to `None`.

`urlshortener.openapi` supplies title **URL Shortener API**, version `0.1.0`, and a server URL from `APP_BASE_URL`. That module is documentation only.

Do not add a Bearer or JWT security scheme. The create API stays public.

## 2. Schema contents

`POST /api/v1/shorten` is in the schema with **201**, **400**, and **503**, matching `openapi.yaml`. The response models are the frozen Pydantic types in `urlshortener.web.dto` (`ShortenRequest`, `ShortenResponse`, `ErrorResponse`).

`GET /short/{shortCode}` is registered with `include_in_schema=False`.

Do not add a second OpenAPI package.

## 3. What this playbook does not do

- No authentication library in this change (`03-security-jsoup.md` is separate).
- No schema change.
- No replacement for `tests/web/test_url_shortener_api.py`.

## 4. Smoke check

1. Start the API on port 8080 with docs enabled.
2. `GET /docs` shows **URL Shortener API** `0.1.0`.
3. The catalog lists `POST /api/v1/shorten` and omits `GET /short/{shortCode}`.
4. Try-it-out with a valid `https://…` URL returns **201**.
5. `GET /openapi.json` is OpenAPI 3 JSON.
6. The pytest command from `TESTING_PLAN.md`, run in `backend/`, stays green.
