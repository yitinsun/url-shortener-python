# Frontend technology stack

This is the only allowed toolchain for `frontend/`. It is not part of `backend/pyproject.toml`.

## 1. Versions

* **Runtime:** Python **3.13**
* **UI:** Starlette, Jinja2
* **Server:** Uvicorn, dev port **5173**
* **HTTP client:** httpx, used by the UI process to call the API
* **Tests:** pytest and Starlette `TestClient`

Module root: `frontend/` (`frontend/pyproject.toml`). Import package `urlshortener_web` from `frontend/src/`.

## 2. Dependency allow-list

Runtime:

* `starlette`
* `jinja2`
* `uvicorn`
* `httpx`

Test only:

* `pytest`

Do not add a component library, CSS framework, a JavaScript bundler, a chart package, an analytics SDK, or a second HTTP client. The browser does not run React. `static/app.js` is clipboard copy only.

Fonts are files in `static/fonts/` (Fraunces and Source Sans 3, woff2) so the page does not depend on a third-party stylesheet at runtime.

## 3. Dev server and the API

The browser talks to the UI origin on port **5173**. The UI process proxies `/api` to the FastAPI port so v1 does not need a CORS change in `backend/`.

* Dev server port **5173**.
* Proxy `/api` → `http://localhost:8080`.
* Server-side calls use `API_ORIGIN`, default `http://localhost:8080`.

`urlshortener_web.shorten` is the only module that knows the path, the JSON fields, and the status codes. Templates do not assemble the URL string themselves.

The short URL in the **201** body is absolute (`http://localhost:8080/short/...` by default). **Open short link** uses that absolute URL. Do not proxy `GET /short/**` through the UI; the redirect must be served by the API.

Do not hardcode a production secret. There is no auth header.

## 4. Layout when the app is generated

```text
frontend/
├── pyproject.toml
└── src/urlshortener_web/
    ├── app.py
    ├── shorten.py
    ├── templates/
    │   ├── index.html
    │   └── not_found.html
    └── static/
        ├── app.js
        ├── styles.css
        ├── fonts/
        └── assets/
            ├── hero-desk.webp
            ├── step-paste.webp
            ├── step-code.webp
            └── step-open.webp
```

## 5. Backend gate

Editing these frontend files does not unlock `backend/pyproject.toml` or `backend/src/**`. Gate 2 in `AGENTS.md` still applies to the API.
