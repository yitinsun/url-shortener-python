# Frontend PRD: URL shortener client

The Python UI is the human client for the API in `specs/greenfield/PRD.md`. It demonstrates create, copy, and open. It does not add product behavior the API does not have.

Binding contract: `specs/contracts/openapi.yaml`. Vocabulary: `specs/domain/glossary.md`. Visual rules: `DESIGN.md`.

The browser posts the form to the UI process. `urlshortener_web.shorten` validates the fields and performs `POST /api/v1/shorten` with `httpx`. The page is Jinja2. A few lines of script handle clipboard copy only.

## 1. What the user can do

1. Paste a long HTTP(S) URL and optionally set a lifetime in days.
2. Receive a short URL, short code, and expiry.
3. Copy the short URL.
4. Open the short URL in the browser, which follows `GET /short/{shortCode}` on the API host (**302** to the long URL).

There is no account, no custom back-half, and no click chart. Analytics stays decision **C** in `specs/scenarios/03-ambiguous.md`.

## 2. Screens

One route, `/`, is the product (`GET` renders the form, `POST` submits it). Unknown client routes render a quiet “page not found” inside the app shell. That page is not the API HTML 404. The API 404 is what a browser sees when a short code is missing or expired on the API host.

### 2.1 Create

| Control | Sends |
|:--------|:------|
| Long URL, required | `longUrl` |
| Lifetime in days, optional | `ttlInDays` only when the field has a number |

The UI server submits `POST /api/v1/shorten` with `Content-Type: application/json`.

* Blank lifetime omits `ttlInDays`. The server default is **730** days. Do not send `730` or `365` as a stand-in for “blank”.
* `365` may appear as placeholder text. It is an example, not the submitted default.
* Client checks, before the request: non-empty, `http` or `https`, length ≤ 2048, integer TTL in **1..3650** when filled. The API decision still wins. Show the JSON `message` on **400**.

### 2.2 Result

On **201**, replace the idle result area with:

| Shown | Source |
|:------|:-------|
| “Short link ready” | Fixed label. **201** is also returned when an active mapping already exists, and the body does not say which. |
| Short URL | `shortUrl` |
| Short code | `shortCode` |
| Expiry | `expiresAt`, formatted in the user’s locale with the timezone visible |
| Long URL | `longUrl`, as secondary text |

Actions: **Copy short link** (clipboard, then “Copied”), and **Open short link** (`shortUrl` in a new tab). Opening is a navigation so the API can answer **302**. Do not follow the redirect with `httpx` or `fetch`.

### 2.3 Failures

| Situation | UI |
|:----------|:---|
| **400** | `message` from `ErrorResponse`. Keep the typed URL in the form. |
| **503** | `message` when present, otherwise “The link service is unavailable. Try again in a moment.” |
| Network or non-JSON | “The link service could not be reached.” |
| HTML body | Do not dump HTML into the page. Use the network sentence above. |

## 3. How the pictures teach the API

Under the form, three steps match the three pictures in `DESIGN.md`:

1. **Paste** — the long URL is the request body.
2. **Code** — the service stores a mapping and returns a Base62 short code.
3. **Open** — the short URL hits `GET /short/{shortCode}` and the browser is sent to the long URL with **302**.

A one-line note under the steps: codes are plain Base62. Lifetime defaults to two years when omitted.

## 4. Out of the client

OpenAPI docs, the legal-path filter, and HTML rejection stay on the API. The form does not need to reimplement the self-loop host check beyond showing the **400** message. Do not call `/openapi.json` or `/docs` from the page.
