# Technology Stack Profile: FastAPI URL Shortener (Python 3.13 & MySQL)

This document is the **only** allowed backend toolchain for v1. Packages not listed here are high-impact (see `ORCHESTRATION_MANIFEST.md` §5.1).

**Explicitly out of v1 (do not add):** Redis, an authentication library, a retry/circuit library, Safe Browsing clients, Alembic or any other migration tool, a third-party OpenAPI UI package, an HTML parser, a metrics exporter. FastAPI is constructed with `docs_url=None`, `redoc_url=None`, and `openapi_url=None` until playbook `01-add-swagger.md`. Schema is applied from `schema.sql` plus the DDL in `SYSTEM_DESIGN.md`. SQLAlchemy must not create or alter tables in `dev` or `prod`.

**Frontend:** the Python UI is specified in `specs/frontend/TECH_STACK.md`. It is not a dependency of `backend/pyproject.toml`.

## 1. Core Tooling Versions

* **Language Runtime:** Python 3.13
* **Framework:** FastAPI 0.115 or a later 0.x release that uses Pydantic v2
* **Server:** Uvicorn
* **Build / metadata:** `backend/pyproject.toml` (`requires-python >=3.13`). Install the project in editable mode with its `dev` extra.
* **Module root:** `backend/` (`backend/pyproject.toml`), import package `urlshortener` from `backend/src/`
* **Database driver:** PyMySQL, plus `cryptography` so MySQL 8 `caching_sha2_password` can authenticate
* **ORM:** SQLAlchemy 2.x
* **Settings:** pydantic-settings
* **Test DB:** SQLite in memory (test extra / test runs only)
* **Coverage:** pytest-cov, **minimum 80% line coverage**. The pytest command in `TESTING_PLAN.md` fails below that bar

## 2. Application Dependency Suite (`backend/pyproject.toml`)

Declare versions in this file only. Do not pin the same packages again in a second manifest.

Runtime:

* `fastapi`
* `uvicorn`
* `pydantic` (v2)
* `pydantic-settings`
* `sqlalchemy` (2.x)
* `pymysql`
* `cryptography`

Test extra:

* `pytest`
* `pytest-cov`
* `httpx` (FastAPI `TestClient`)

Configure coverage so the Gate 4 command runs on source package `urlshortener` and fails when line coverage is under 80%. Measure lines, not branches. Do not add other packages without Gate 2 / high-impact approval.

```toml
[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.coverage.run]
source = ["urlshortener"]
branch = false
```

## 3. Configuration (`backend/src/urlshortener/settings.py`)

All secrets and hosts come from the environment. Defaults below are **lab-only**. Never commit a literal production password that differs from these documented lab defaults.

`APP_BASE_URL` builds `shortUrl` in API responses. `APP_ENV` selects the profile: `dev` (default), `prod`, or `test`.

| Setting | Environment | Lab default |
|:--------|:------------|:------------|
| Profile | `APP_ENV` | `dev` |
| Public origin | `APP_BASE_URL` | `http://localhost:8080` |
| Database host | `DB_HOST` | `localhost` |
| Database port | `DB_PORT` | `3306` |
| Database name | `DB_NAME` | `shortener_dev` in dev, `shortener_prod` in prod |
| Database user | `DB_USER` | `root` |
| Database password | `DB_PASSWORD` | `Tiger` |

Dev connects with PyMySQL, UTC, `utf8mb4`. On startup, run `schema.sql` and continue when the database or table already exists. Do not call `create_all`.

Prod connects with TLS preferred (`use SSL` when the server offers it). Do not run `schema.sql` from the app. Do not call `create_all`. Refuse to serve if `url_mappings` is missing the columns in `SYSTEM_DESIGN.md`.

Test (`APP_ENV=test`) uses an in-memory SQLite URL. The fixture may call `create_all`, then set the next id to **56800235**. Integration tests use this profile. Do not point them at production MySQL unless an operator explicitly runs a local MySQL profile.

`docker-compose.yml` (workspace root) must pass `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, and `APP_BASE_URL` into the backend service. Compose may set lab passwords in `environment:`. Python still reads only the environment.

Prod schema (including `AUTO_INCREMENT=56800235`) is applied by DBA or a compose init mount of the same `schema.sql`, not by SQLAlchemy.

## 4. Development Constraints & Coding Standards

* **API types:** Request and response bodies on the HTTP boundary are frozen Pydantic models in `urlshortener.web.dto`. Do not use bare dicts as the public response model.
* **ORM models:** SQLAlchemy 2 mapped classes in `urlshortener.models`. They are not the HTTP models.
* **Database access:** SQLAlchemy queries with bound parameters only. f-strings, `%` formatting, and string concatenation that build SQL are banned. `text()` is allowed for batched expiry deletes only when every value is a bind parameter.
* **Scheduling:** one `asyncio` task started from the FastAPI lifespan for expiry cleanup. No Celery, no APScheduler, no extra scheduler library.
* **Layout:**

```text
backend/
├── pyproject.toml
├── Dockerfile
└── src/urlshortener/
    ├── main.py              # FastAPI app, lifespan, handlers
    ├── settings.py
    ├── encoding/base62.py
    ├── db/schema.sql
    ├── models/url_mapping.py
    ├── repositories/url_mapping_repository.py
    ├── service/url_shortener.py
    ├── schedule/cleanup.py
    └── web/
        ├── dto.py
        ├── routes.py
        ├── errors.py
        └── pages.py         # friendly HTML
```
