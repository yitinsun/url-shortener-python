# 02 — Legal paths and friendly HTML

Brownfield playbook. Run after `01-add-swagger.md`. Greenfield already specifies `GET /short/{shortCode}`, `shortUrl = {APP_BASE_URL}/short/{shortCode}`, and HTML **404** for a missing or expired code. This playbook adds the allowlist fence and returns that same HTML page for every other URL on the API. It does not rename spec folders and it does not change the redirect path.

No new packages. No authentication library (that is `03-security-jsoup.md`). No schema change.

## Legal URL allowlist

Host is `http://localhost:8080` in local `dev` / `test`.

| Legal pattern | Methods | Notes |
|:--------------|:--------|:------|
| `/api/v1/shorten` | **POST** | JSON create. Other methods are illegal. |
| `/short/{shortCode}` | **GET** | `{shortCode}` is Base62 `[0-9A-Za-z]{1,10}`. |
| `/docs` | GET | From playbook 01, and only while docs are enabled. |
| `/openapi.json` | GET | OpenAPI JSON, only while docs are enabled. |

**Illegal examples:** `/`, `/index.html`, `/foo`, `/b9K2x1` (no `/short/` prefix), `GET /api/v1/shorten`, `/short/` with no code.

A metrics exporter is **not** on the v1 dependency list. Do not allowlist `/metrics` or `/actuator/**` in this playbook.

Implement `legal_paths` plus ASGI middleware (`LegalPathMiddleware`) on the whole app, registered so it runs before routing:

1. Legal pattern → continue the chain.
2. Anything else → **404** friendly HTML. Do not fall through to a route that might 302 or return JSON.

Package: `urlshortener.web`.

## HTML vs JSON

| Request | Body |
|:--------|:-----|
| `POST /api/v1/shorten` 400 / 503 | JSON `ErrorResponse` |
| `GET /short/{shortCode}` missing or expired | HTML 404 |
| Illegal path | HTML 404 |

The page must include a visible title, a short explanation, the escaped request path, and links to `POST /api/v1/shorten`, `/docs`, and `/short/{code}`. It must not show a traceback, the words “Whitelabel Error Page”, or the JSON body `{"detail":"Not Found"}`. Escape `<`, `&`, and `"`.

`ERR_CONNECTION_REFUSED` means nothing is listening on 8080. That is not this 404.

## Tests

Keep the greenfield cases. Add:

| Case | Expect |
|:-----|:-------|
| `GET /short/{activeCode}` | 302 + `Location` |
| `GET /short/unknown` | 404, `text/html`, friendly heading, no “Whitelabel”, no `{"detail"` |
| `GET /b9K2x1` | 404 HTML |
| `GET /` and `GET /nope` | 404 HTML |
| `GET /api/v1/shorten` | 404 HTML |
| `POST /api/v1/shorten` valid | 201 JSON |
| `GET /openapi.json` with docs enabled | 200 JSON containing `/api/v1/shorten` and not a bare `/{shortCode}` path |

The pytest command from `TESTING_PLAN.md`, run in `backend/`, must stay green. No skipped tests.
