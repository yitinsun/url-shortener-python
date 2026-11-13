# URL shortener

Pure Python URL shortener. The HTTP API is a FastAPI service in `backend/`. The browser UI is a Starlette and Jinja2 app in `frontend/`. Specs live in `specs/greenfield/`, `specs/brownfield/`, and `specs/frontend/`.

Gate 2 is approved. The signature file is `GATE2_APPROVAL.txt`.

## Prerequisites

- Python 3.13
- Docker is optional. The lab stack is `backend/Dockerfile` and the root `docker-compose.yml`.
- MySQL 8 for the dev profile on localhost. Database `shortener_dev`, user `root`. The lab default for `DB_PASSWORD` is `Tiger`. Compose uses that same lab password for `shortener_prod` and does not publish MySQL on host port 3306.

JDK, Maven, and Node.js are not used.

## Tests

From `backend/`:

```powershell
pytest --cov=urlshortener --cov-report=term-missing --cov-report=json:coverage.json --cov-fail-under=80
```

The run fails below 80% line coverage. Copy `covered_lines / num_statements` from `backend/coverage.json` into `SDLC_METRICS.json`.

From `frontend/`:

```powershell
pytest
```

That plan has no coverage percentage. Do not invent one.

## Run

From `backend/`, with MySQL 8 available:

```powershell
uvicorn urlshortener.main:app --host 0.0.0.0 --port 8080
```

`APP_ENV=dev` is the default. The lab container runs `APP_ENV=prod` with `DOCS_ENABLED=true` and listens on port **8080**.

From `frontend/`, with the API already on port 8080:

```powershell
uvicorn urlshortener_web.app:app --host 0.0.0.0 --port 5173
```

Open `http://localhost:5173`. The form posts to the UI process, which calls `POST /api/v1/shorten`. **Open short link** uses the absolute short URL from the API.

## URLs

- `POST /api/v1/shorten` — public JSON create, no token
- `GET /short/{code}` — **302**, or an HTML **404** when the code is missing or expired
- `http://localhost:8080/docs`
- `http://localhost:8080/openapi.json`

Any other path on the API returns the HTML 404. A `longUrl` that contains HTML returns **400** JSON.

## Specs and lineage

- `specs/greenfield/` — first build
- `specs/brownfield/` — OpenAPI docs, legal paths, HTML rejection, this docs pass
- `specs/contracts/openapi.yaml` — paths and status codes
- `GATE2_APPROVAL.txt`
- `SDLC_AUDIT_LOG.json`
- `SDLC_METRICS.json`

## Limits

- Lab password defaults belong in settings defaults and Compose `environment:` only.
- Short codes are sequential Base62 of the numeric id and can be guessed.
- The create API is public. There is no login.
- Click counts, a stats API, and a metrics exporter are not in this build.
