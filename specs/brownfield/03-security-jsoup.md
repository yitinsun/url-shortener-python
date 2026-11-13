# 03 — Public routes and HTML rejection

Brownfield playbook. Run after `02-legal-paths.md`. This is a **demo of a public API**, not product login. No users, JWT, or login page.

`beautifulsoup4` is outside `TECH_STACK.md`. Wait for a new human signature before editing `backend/pyproject.toml`. Use the stdlib `html.parser` only. Do not add `lxml`.

The Java playbook this replaces added Spring Security (`permitAll`, CSRF off) and jsoup. Here the API already has no auth and no CSRF middleware. Keep it that way, and add the HTML check.

What it adds:

1. Confirmation that no authentication package is installed, so `POST /api/v1/shorten` needs no token and unknown paths still reach `LegalPathMiddleware` (HTML 404, not 401).
2. `SanitizeMiddleware` — Beautiful Soup rejects HTML or script in `longUrl`.
3. On a finding, raise `SanitizationError` and let the existing exception handler return the existing **400** JSON. Do not invent a second error shape.

`LegalPathMiddleware` stays the allowlist and runs **first**. This middleware runs after it, so illegal URLs still get HTML 404.

## Package

```toml
dependencies = [
  "beautifulsoup4>=4.12,<5",
]
```

Do not add an auth library, OAuth client, or JWT library.

## Public access

`urlshortener` has no `Security` middleware and no session cookie:

- `POST /api/v1/shorten` from `/docs` and from curl stays a plain JSON request.
- There is no form login, HTTP basic, or logout route.
- Documented routes and unknown paths are reachable without credentials.
- Unknown paths still hit `LegalPathMiddleware`.

Requiring a logged-in user is a later re-plan, not this demo.

## Beautiful Soup

Buffer `POST` JSON so the route can still read the body. Treat markup as unsafe. A plain `https://example.com/path` must pass.

Reject rather than silently clean. Apply only to `longUrl` on `POST /api/v1/shorten`.

Unsafe when `BeautifulSoup(value, "html.parser")` finds any tag, including `script` and `img`.

## Tests

- Existing API tests still pass (nothing challenges POST for a token).
- `longUrl` containing HTML or `<script>` → **400** JSON whose message mentions sanitization or HTML.
- `html_sanitizer` unit tests: clean URL vs `<script>` / `<img>`.

## Files

| File | Role |
|:-----|:-----|
| `backend/pyproject.toml` | `beautifulsoup4` |
| `web/html_sanitizer.py` | `looks_unsafe` |
| `web/errors.py` | `SanitizationError` mapped to 400 JSON |
| `web/sanitize_middleware.py` | middleware after the allowlist |
