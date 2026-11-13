# AI Agent Instructions: Autonomous Python URL Shortener with Lifecycle Governance

You are an advanced, context-aware AI software engineering node operating inside a stateful orchestration graph. You will build, test, and containerize the URL shortener **backend** under strict compliance and observability standards matching Python 3.13 and MySQL 8.0.

Governing documents (do not contradict them):

* Product: `specs/greenfield/PRD.md`
* Architecture: `specs/greenfield/SYSTEM_DESIGN.md`
* Toolchain: `specs/greenfield/TECH_STACK.md`
* Tests: `specs/greenfield/TESTING_PLAN.md`
* Lifecycle gates: `specs/greenfield/ORCHESTRATION_MANIFEST.md`
* Halt rules: `AGENTS.md`

Do not generate `frontend/**` from these instructions.

## 1. Observability, Lineage & Decision Logging

Maintain a continuous file named `SDLC_AUDIT_LOG.json` in the **workspace root**. The file is a JSON array. Append one object for every file generation, module modification, test execution, or self-correction run:

```json
{
  "timestamp": "2026-11-12T16:00:00Z",
  "stage": "IMPLEMENTATION",
  "action_taken": "Created encoding/base62.py to implement SYSTEM_DESIGN.md section 3.",
  "upstream_dependency": "specs/greenfield/SYSTEM_DESIGN.md",
  "upstream_dependency_hash": "<SHA-256 of the governing markdown file>",
  "rationale": "Deterministic ID-to-Base62 encoding avoids hash-collision retries on insert."
}
```

Allowed `stage` values: `REQUIREMENTS`, `ARCHITECTURE`, `IMPLEMENTATION`, `TESTING`, `COMPLIANCE`, `OBSERVABILITY`, `RELEASE`, `REPAIR`, `REPLAN`.

Preserve historical entries. Never overwrite the log on re-plan; only append. Do not write `"n/a"` for `upstream_dependency_hash` when a governing markdown file exists.

## 2. Reliability Metrics Tracking

Write aggregated telemetry to `SDLC_METRICS.json` in the workspace root after every execution loop. Do not leave metrics as unnamed context variables. Do not invent coverage ratios. After a real pytest run, copy the line fraction `covered_lines / num_statements` from `backend/coverage.json` (`totals`) into `coverage_line_ratio`.

```json
{
  "success_rate": {
    "compiled_ok": 0,
    "syntax_failures": 0
  },
  "retry_rollback_frequency": 0,
  "mttr_ms": null,
  "stage1_epoch_ms": null,
  "stage7_epoch_ms": null,
  "end_to_end_latency_ms": null,
  "coverage_line_ratio": null,
  "updated_at": "2026-11-12T16:00:00Z"
}
```

* **Success Rate:** modules that imported cleanly vs syntax failures generated.
* **Retry/Rollback Frequency:** increment on each Gate 4 fallback loop.
* **MTTR:** milliseconds from a failing pytest line to a successful re-run of that suite.
* **End-to-End Latency:** `stage7_epoch_ms - stage1_epoch_ms` when Stage 7 completes.
* Leave Stage 7 fields and `coverage_line_ratio` **null** until that stage or that pytest run actually finishes.

## 3. Hard Policy Compliance Guardrails

* **No concatenated SQL:** All MySQL access must use SQLAlchemy with bound parameters. `text()` is allowed only when `TECH_STACK.md` allows it, and every value is a bind parameter. An f-string or concatenated SQL string is a Gate 4C failure.
* **Secret isolation:** Do not hardcode credentials, production passwords, or API keys in Python modules. Read secrets through the environment as defined in `TECH_STACK.md`. Lab defaults are for local/dev only; production must inject real environment values.
* **No test bypass:** Never add `pytest.mark.skip` or `pytest.mark.skipif` to make a suite pass.

## 4. Work Execution Cycle (State Gate Constrained)

1. **Gate 2 lock:** Do not generate functional Python sources, `backend/pyproject.toml`, or `backend/src/**` until Gate 2 is approved. Approval is a workspace file `GATE2_APPROVAL.txt` containing a line of the form `[APPROVED: HUMAN_ENGINEER_ID]`. Documentation under `specs/`, `AGENTS.md`, `.cursor/rules/**`, `Dockerfile`, and `docker-compose.yml` may exist before Gate 2; they do not unlock Stage 3.
2. **Bounded retry:** If imports or tests fail, follow the 3-retry protocol in `ORCHESTRATION_MANIFEST.md`. Fix production or test code so assertions pass. Do not weaken coverage below 80%.
3. **Lineage:** After each mutation, append to `SDLC_AUDIT_LOG.json` with the SHA-256 of the markdown file that justified the change (`PRD.md`, `SYSTEM_DESIGN.md`, `TECH_STACK.md`, or `TESTING_PLAN.md`).
