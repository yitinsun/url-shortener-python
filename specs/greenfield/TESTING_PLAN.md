# Automated Test Verification Suite Plan

Mandatory tests and the agent loop for Gate 4. From `backend/`, the suite must pass at **100%** and line coverage **>= 80%**. Never use `pytest.mark.skip`, `pytest.mark.skipif`, or a comment-out to make a suite pass.

Coverage is enforced by pytest-cov in `TECH_STACK.md`. Do not invent a percentage in `specs/scenarios/01-greenfield.md` or `SDLC_METRICS.json`.

Test sources live under `backend/tests/`. The import package is `urlshortener`.

Gate 4 command, from `backend/`:

```powershell
pytest --cov=urlshortener --cov-report=term-missing --cov-report=json:coverage.json --cov-fail-under=80
```

## 1. Unit Testing Matrix

### 1.1 `tests/encoding/test_base62.py`

No FastAPI app and no database. Assert:

* **Pivot:** `encode(56800235)` is alphanumeric `[0-9A-Za-z]+` and length **>= 5** (and **<= 7** for this pivot).
* **Alphabet:** encoded forms contain no `+` or `/`.
* **Max:** `encode` of the maximum signed 64-bit value completes; `decode(encode(that value))` returns the same value.
* **Round-trip:** for a set of random positive ints, `decode(encode(id)) == id`.

### 1.2 `tests/service/test_url_shortener_service.py`

Mock the repository. No listening socket.

| Case | Setup | Expect |
|:-----|:------|:-------|
| Missing resource | Repo empty for short code | `ResourceNotFoundError` |
| Expired mapping | `expires_at` in the past | `ResourceNotFoundError` |
| Idempotent create | Active row for same `longUrl` | No second insert; return existing code |
| Default TTL | `ttlInDays` omitted | `expires_at` ≈ now + **730** days |
| Self-loop | `longUrl` host equals `APP_BASE_URL` host | validation failure / 400-path exception |
| Oversize URL | length > 2048 | validation failure |

### 1.3 `tests/schedule/test_expired_mapping_cleanup.py`

The scheduled delete uses a parameterized SQLAlchemy statement. Assert a cutoff instant is passed and the statement is not built with an f-string or concatenated SQL.

## 2. Web Layer Integration Testing (`tests/web/test_url_shortener_api.py`)

Use FastAPI `TestClient` with **`APP_ENV=test`** so the datasource is **SQLite** from `TECH_STACK.md`, and the next id starts at **56800235**. Seed data with the repository or a real POST — **not** a mock of the service.

Exception handlers must serialize the error JSON from `PRD.md` / `SYSTEM_DESIGN.md` for `POST /api/v1/shorten`. Redirect misses use HTML.

### 2.1 `POST /api/v1/shorten`

| Case | Assert |
|:-----|:-------|
| Valid HTTP(S) URL | **201**; body has `shortUrl`, `shortCode`, `expiresAt`; `shortCode` length 5–7; `shortUrl` starts with `{APP_BASE_URL}/short/` |
| Second POST of the same `longUrl` | **201** with the identical `shortCode` |
| `"longUrl": "not-a-valid-url"` | **400** and error JSON `status`/`message` |
| Self-loop to `APP_BASE_URL` | **400** |

### 2.2 `GET /short/{shortCode}`

| Case | Setup | Assert |
|:-----|:------|:-------|
| Active mapping | Persist unexpired row (or create via POST) | **302** and `Location` equals `longUrl` |
| Unknown code | GET a code that was never inserted | **404** friendly HTML (not JSON, not `{"detail": ...}`) |
| Expired mapping | Persist row with `expires_at` in the past | **404** friendly HTML (HTTP layer, not only service unit) |

## 3. Automated Agent Workflow Cycle

Coverage fails inside the pytest command above. Do not pass `--no-cov` or skip tests except inside the Docker **image build** of a tree already verified at Gate 4.

```
[ Import check ] ──> [ pytest  (tests + line coverage 80%) ]
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
[ All tests pass + coverage ]   [ Failures or coverage < 80% ]
         │                         │
         ▼                         ▼
[ Gate 5: container phase ]   [ Read traceback ]
         (Stage 6)                 │
                                   ▼
                          [ Patch failing module ]
                                   │
                                   ▼
                          [ Retry; max 3 times ]
                                   │
                    exhausted ──> [ Safe-Stop / rollback to Gate 2 ]
```

This loop **is** the Bounded Retry in `ORCHESTRATION_MANIFEST.md`. Passing tests do **not** rewrite modules. Gate 4C (secrets / parameterized SQL) is a compliance review of the same tree, not a pytest case — still must pass before Stage 6.
