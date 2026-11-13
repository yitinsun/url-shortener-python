# System Design Specification: URL Shortener Service (MySQL 8.0)

Architecture, data model, and Base62 design for a **single-instance**, read-heavy (about 100:1) URL shortener on MySQL 8.0 InnoDB. This is not a multi-region or Redis-backed deployment.

v1 **does not** include: HTTP rate limiting, Google Safe Browsing, code salting, Redis, replicas, an authentication library, or the Python UI. Those remain future re-plans. OpenAPI docs, the legal-path allowlist, and the Beautiful Soup check are brownfield playbooks in `specs/brownfield/`, not this design.

Python package root: `urlshortener` under `backend/src/`.

## 1. Component Data Flow

```
[ Client ]
    │
    ├── POST /api/v1/shorten ──> [ Route + Pydantic validation ]
    │                                  │
    │                                  ▼
    │                            [ Service write path ]
    │                             1. Reject invalid / self-loop URLs
    │                             2. Find active row by exact long_url
    │                             3. If found → return existing mapping
    │                             4. Else insert row (DB assigns id)
    │                             5. Encode id → Base62 short_code, persist code + expires_at
    │                                  │
    │                                  ▼
    │                            [ MySQL 8.0 url_mappings ]
    │
    └── GET /short/{shortCode} ──> [ Redirection route ]
                                  │
                                  ▼
                             [ Lookup by short_code ]
                                  │
                    active ──> 302 Location: long_url
                    missing or expired ──> 404 HTML page
```

The GET path stays thin: route → service → indexed lookup. No cache in v1.

## 2. Database Schema & Index Design

### 2.1 Table `url_mappings`

| Column | Data type | Constraints | Description |
|:-------|:----------|:------------|:------------|
| `id` | `BIGINT` | PRIMARY KEY, AUTO_INCREMENT | Sequence **starts at 56800235** so the first Base62 codes are at least 5 characters. |
| `long_url` | `VARCHAR(2048)` | NOT NULL | Destination URL (utf8mb4). |
| `short_code` | `VARCHAR(10)` | UNIQUE, NOT NULL | Public Base62 key (5–7 chars in normal range). |
| `created_at` | `TIMESTAMP` | NOT NULL DEFAULT CURRENT_TIMESTAMP | Creation time (UTC). |
| `expires_at` | `TIMESTAMP` | NOT NULL | `created_at + ttl` (default 730 days). |

Idempotency is **application logic** (lookup active row by full `long_url`). There is **no** UNIQUE on `long_url` because an expired URL may be shortened again with a new code.

The prefix index `idx_long_url (long_url(255))` speeds candidate lookup. The service must compare the **full** string in memory so URLs that differ after character 255 are not treated as the same link.

### 2.2 DDL (MySQL 8.0)

Ship as `backend/src/urlshortener/db/schema.sql`. SQLAlchemy must **not** be the source of `AUTO_INCREMENT=56800235`. Dev and prod must not call `create_all` or emit `ALTER`. Tests may call `create_all` only against the SQLite test database, and that database’s next id must still be **56800235** before the first insert.

```sql
CREATE DATABASE IF NOT EXISTS shortener_dev
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE url_mappings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    long_url VARCHAR(2048) NOT NULL,
    short_code VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    UNIQUE KEY idx_short_code (short_code),
    INDEX idx_long_url (long_url(255))
) ENGINE=InnoDB
  AUTO_INCREMENT=56800235
  DEFAULT CHARSET=utf8mb4
  COLLATE=utf8mb4_unicode_ci;
```

Production database name is `shortener_prod` with the same table definition.

### 2.3 Write-path expiry

`expires_at = now(UTC) + (ttlInDays or 730) days`. Persist after insert once `id` is known so `short_code = encode(id)`.

Recommended insert sequence: insert with a temporary unique placeholder **or** flush the session to obtain `id`, then set `short_code` and commit. Either approach must remain one transaction.

## 3. Base62 Conversion

### 3.1 Alphabet

```
0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
```

v1 public `short_code` **is** this encoding of `id`. Sequential guessing is an accepted v1 risk (see section 5).

### 3.2 Logic

* **Encode:** while id > 0: append `alphabet[id % 62]`, `id = id // 62`; reverse. `encode(0)` is `0` (not used as a live id).
* **Decode:** for each character, `total = total * 62 + alphabet.index(char)`.

Redirect looks up `short_code` as a string; decode is required for tests and symmetry, not for GET.

Module: `urlshortener.encoding.base62` with `encode(id: int) -> str` and `decode(code: str) -> int`.

## 4. Error Handling Matrix

Use FastAPI exception handlers. Error JSON for the create API must be this object, not `{"detail": ...}`:

```json
{
  "status": 400,
  "error": "Bad Request",
  "message": "<reason>",
  "shortCode": null
}
```

| Situation | HTTP | Body | Exception / trigger |
|:----------|:-----|:-----|:--------------------|
| Malformed URL, self-loop, oversize, bad `ttlInDays` | **400** | JSON | Validation / `ValueError` |
| Short code missing or expired | **404** | Friendly HTML | `ResourceNotFoundError` on the redirect path |
| Database timeout or lock failure | **503** | JSON | SQLAlchemy data-access / timeout mapped in the handler |

## 5. Security Guardrails & Failure Modes

| Risk | v1 mitigation |
|:-----|:--------------|
| 32-bit id exhaustion | `BIGINT` primary key. |
| Sequential code guessing | **Accepted in v1.** Documented limitation; salt/HMAC is a re-plan (high-impact). |
| Malicious destination | RFC 3986 HTTP(S) validation, max 2048 chars, reject javascript/data schemes, reject host equal to `APP_BASE_URL` host. **No** Safe Browsing API in v1. |
| Expired row bloat | Hourly task in the FastAPI lifespan. Delete with a parameterized SQLAlchemy statement (for example `delete(UrlMapping).where(UrlMapping.expires_at < bindparam("cutoff"))`), in batches. Do not build SQL with f-strings. Redirect still 404s on `expires_at < now` even if the row is not deleted yet. |

Self-loop: parse `longUrl` host and compare case-insensitively to the host of `APP_BASE_URL`.
