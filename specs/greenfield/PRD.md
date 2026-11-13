# Product Requirement Document (PRD): URL Shortener Service

## 1. Executive Summary & Objective

Build a lightweight **URL Shortener microservice**. The service turns a long HTTP(S) URL into a short, shareable code and redirects that code back to the destination. v1 is a single FastAPI service plus MySQL 8.0 — not a multi-region platform. The Python UI is a later pass and is not part of this PRD.

**Out of v1 (re-plan if requested later):** user accounts, custom aliases, click-count APIs, rate limiting, Google Safe Browsing, Redis cache, sharding, the frontend app.

## 2. Functional Requirements

### 2.1 Core Link Shortening API

* **Endpoint:** `POST /api/v1/shorten`
* **Input payload:**
  ```json
  {
    "longUrl": "https://example.com/api-design/api-design-url-shortening-service/",
    "ttlInDays": 365
  }
  ```
  `ttlInDays` is optional. The example value `365` is **not** the default.

* **Behavior:**
  * Reject `longUrl` that is missing, not HTTP/HTTPS, longer than **2048** characters, contains script payloads, or whose host matches this service’s own public host (**self-loop**). Those cases return **400**.
  * **Idempotency:** If an **active** (not expired) row already exists for the exact same `longUrl` string, return that row. Do **not** insert a duplicate. If the client sends a different `ttlInDays` while the existing mapping is still active, **ignore the new TTL** and return the existing `shortCode` / `expiresAt`.
  * If a row exists for that `longUrl` but is **expired**, create a **new** mapping (new id, new short code, new expiry).
  * New codes are unique **5 to 7 character** Base62 strings derived from the numeric id.

* **Success (`201 Created`):**
  ```json
  {
    "longUrl": "https://example.com/api-design/api-design-url-shortening-service/",
    "shortUrl": "http://localhost:8080/short/b9K2x1",
    "shortCode": "b9K2x1",
    "expiresAt": "2027-11-12T09:25:00Z"
  }
  ```
  `shortUrl` is `{APP_BASE_URL}/short/{shortCode}`. Default `APP_BASE_URL` is `http://localhost:8080` (no trailing slash). `expiresAt` is ISO-8601 UTC.

### 2.2 Link Redirection

* **Endpoint:** `GET /short/{shortCode}`
* **Behavior:**
  * If the row exists and `expires_at` is in the future, return **302 Found** with `Location: <longUrl>`.
  * Do **not** use **301**. Analytics/click counting is **out of v1**, but 302 keeps a future counter possible.
  * If the code is missing or expired, return **404** with a friendly HTML page (not JSON, and not FastAPI’s default `{"detail": ...}` body).
  Expired reads return 404 immediately. A background cleanup job may delete stale rows later; cleanup is not required on the request path.

### 2.3 Expiration & TTL Management

* `expiresAt = createdAt + ttlInDays` days.
* If `ttlInDays` is omitted, default is **24 months** (730 days).
* `ttlInDays` must be an integer **1..3650** when present; otherwise **400**.

## 3. Non-Functional Requirements

### 3.1 Availability, Latency, & Performance

* Design for about **100 reads per 1 write**. Optimize `GET /short/{shortCode}`.
* Redirect **application overhead** (lookup + 302) target is **under 20 ms** under normal local load. v1 does not include a load-test gate; the unique index on `short_code` is the design control.

### 3.2 Data Consistency & Security

* Base62 must be deterministic: `decode(encode(id)) == id`. Alphabet is `[0-9a-zA-Z]` only — no `+` or `/`.
* v1 codes are **plain Base62(id)** (sequential, guessable). Obfuscation/salt is out of v1.
* No authentication in v1; the create API is open.

## 4. Technical Grounding

* **Runtime:** Python 3.13.
* **Module:** `backend/` (a `pyproject.toml` project). Do not generate `frontend/` from this PRD.
* **Persistence:** MySQL 8.0 InnoDB, **utf8mb4**.
* **Encoding:** Base62 as specified in `SYSTEM_DESIGN.md`.
* **Contract:** `specs/contracts/openapi.yaml` must name the same paths and status codes as this file.
