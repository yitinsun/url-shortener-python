# Glossary

Shared names for the API and the Python UI. HTTP paths and status codes are defined in `specs/greenfield/PRD.md` and `specs/contracts/openapi.yaml`.

| Term | Meaning |
|:-----|:--------|
| Long URL | Destination `http` or `https` URL stored in `long_url`. Max 2048 characters. |
| Short code | Public Base62 encoding of `url_mappings.id`. Alphabet `[0-9a-zA-Z]`. Normal length 5–7. Column `short_code`, max 10. |
| Short URL | `{APP_BASE_URL}/short/{shortCode}`. `APP_BASE_URL` has no trailing slash. Default `http://localhost:8080`. |
| Mapping | One row in `url_mappings`: id, long URL, short code, `created_at`, `expires_at`. |
| Active mapping | A row whose `expires_at` is still in the future. |
| TTL | `ttlInDays` on create. Optional. Allowed range 1–3650. Omitted value means **730** days (24 months). |
| Expiry | `expires_at = created_at + TTL`. An expired row is not reused. A later create of the same long URL inserts a new id and code. |
| Idempotent create | If an active row already has the exact same `long_url`, return that row. Ignore a different `ttlInDays` on that request. |
| Redirect | `GET /short/{shortCode}` → **302 Found** and `Location: <longUrl>` when the mapping is active. Never **301**. |
| Self-loop | `longUrl` host equals the host of `APP_BASE_URL`, compared case-insensitively. Rejected with **400**. |
| Base62 | Deterministic encode/decode of the numeric id. `decode(encode(id)) == id`. No `+` or `/`. v1 codes are plain `Base62(id)` and are guessable. |
