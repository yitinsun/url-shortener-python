# Frontend test plan

From `frontend/`, `pytest` must finish with zero failures. Do not skip a case to go green. There is no coverage percentage in this plan; do not invent one.

Drive the app with Starlette `TestClient`. Mock `httpx`. Do not start FastAPI.

## 1. Create form

| Case | Expect |
|:-----|:-------|
| Submit a valid `https` URL with lifetime blank | Upstream `POST /api/v1/shorten`, JSON body has `longUrl` and **no** `ttlInDays` |
| Submit with lifetime `365` | Body includes `ttlInDays: 365` |
| Empty URL, `http://` missing, length over 2048, or TTL `0` | No `httpx` call; an inline error is visible |
| **201** body | “Short link ready”, the `shortUrl`, `shortCode`, and a formatted `expiresAt` |
| Second **201** for the same URL | Still “Short link ready” (the API does not flag reuse) |

## 2. Errors

| Case | Expect |
|:-----|:-------|
| **400** `{ status, error, message }` | `message` is shown; the typed URL remains |
| **503** with a `message` | That `message` is shown |
| `httpx` raises | “The link service could not be reached.” |

## 3. Pictures and actions

| Case | Expect |
|:-----|:-------|
| First paint | Hero `alt` “Stone table with an open sketchbook, a pencil, and a ceramic cup”, plus the three step alts from `DESIGN.md` |
| Copy control after success | The control’s `data-short-url` is `shortUrl` |
| Open control | An anchor whose `href` is `shortUrl` |

## 4. Command

`pytest` from `frontend/` on Python 3.13. When the app exists, importing `urlshortener_web.app` must succeed without calling the API.
