# Ambiguous requirements — decisions

Intent: several product phrases were never given an API, schema, or SLA. This file records the options, the v1 pick, and the risk. It does not assign implementation tasks. Schema or new public APIs stay halted until a human signature.

Lifecycle: `REQUIREMENTS` / `REPLAN` → append `SDLC_AUDIT_LOG.json`. No silent table changes.

---

## Analytics

**Vague phrase:** “analytics” with no event, no API, no retention.

| Option | Risk |
|:-------|:-----|
| A. Click column + increment on 302; no read API | Schema change (high impact) |
| B. `GET /api/v1/stats/{code}` | New API + schema |
| C. Keep 302 only; no counters | Analytics stays future work |

**v1 pick: C.** Redirect stays **302** (not 301) so a later counter can still see every hop. No `click_count` column and no stats API in this pass.

---

## Reliability

**Vague phrase:** “reliability features” with no SLO.

**v1 pick:** TTL (default 730 days), batched expiry delete, **503** JSON when the database is down, SQLite `test` vs MySQL `dev`/`prod`, compose MySQL healthcheck. No multi-AZ, no Redis.

---

## Orchestration runtime

**Vague phrase:** lifecycle “layer” vs files on disk.

**v1 pick:** Cursor agent + `specs/greenfield/ORCHESTRATION_MANIFEST.md` + `GATE2_APPROVAL.txt` + append-only `SDLC_AUDIT_LOG.json` / `SDLC_METRICS.json`. Not LangGraph or an LLM inside the Python process.

---

## Greenfield vs brownfield

**v1 pick:** `specs/greenfield/` generates the first build. `specs/brownfield/` is OpenAPI docs, the legal-path fence, the public-route and Beautiful Soup demo, then docs. See `01-greenfield.md` and `02-brownfield.md`.

---

## Open API vs authentication

**v1 pick:** `POST /api/v1/shorten` stays public. Greenfield has no authentication library. If playbook `03-security-jsoup.md` is signed later, the API stays public (no login middleware) and Beautiful Soup plus `LegalPathMiddleware` bound abuse at the HTTP edge. Login and JWT stay out of band.

---

## Follow-through not taken

A click-count column on successful 302 was considered. It needs DDL after Gate 2 → **halt** until a new signature. Not part of greenfield or of `04-refine.md`.
