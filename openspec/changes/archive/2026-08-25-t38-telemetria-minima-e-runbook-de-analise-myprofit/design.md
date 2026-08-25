## Context

T38 is one observability/documentation slice after archived T36. The current
MyProfit flow creates one profile-scoped `MyProfitSyncJob`, runs a bounded
worker, calls the connector, hands downloaded bytes to preview parsing, and
exposes sanitized status to Alpine polling. The browser stops after
`pollDelay = 500 ms` and `maxPolls = 120`; this is a local UI limit, not a
server timeout. T36 and deprecated F68 are context only: T38 must not change
their timeout decision or reopen either change.

The repository already configures `omaha` logging to stdout through
`configure_logging`, with JSON or text formatting selected by existing
`LOG_LEVEL`/`LOG_FORMAT` settings. No telemetry table, file sink, metrics
backend, collector, or retention service exists in inspected code.

## Code Map

| File | Exact symbols / region | Role in current flow |
|---|---|---|
| `src/omaha/routes/imports.py` | `MyProfitSyncService.start` | Creates one queued job per real profile and schedules worker execution. |
| `src/omaha/routes/imports.py` | `MyProfitSyncService.run_myprofit_sync_job` | Acquires bounded worker slot, transitions queued→running, invokes connector, maps failures, and settles cleanup. |
| `src/omaha/routes/imports.py` | `_mark_failed`, `_process_downloaded_csv` | Normalizes failure stage/code and publishes preview success or failure without portfolio commit. |
| `src/omaha/routes/imports.py` | `expire_myprofit_sync_job`, `status_for_profile`, `start_myprofit_sync`, `get_myprofit_sync_status` | Owns expiry precedence, sanitized API status, start/duplicate responses, and polling boundary. |
| `src/omaha/models.py` | `MyProfitSyncJob.normalize_error`, `safe_error_stage`, `safe_error_code`, `to_status_dict`; timestamp fields | Existing allowlists, terminal timestamps, retention metadata, and safe status serialization. No new telemetry persistence is present. |
| `src/omaha/config.py` | `Settings.LOG_LEVEL`, `LOG_FORMAT`, `effective_log_format` | Existing logger selection. No telemetry-specific setting or timeout is justified. |
| `src/omaha/myprofit/connector.py` | `MyProfitConnectorError`, `PlaywrightMyProfitConnector.download_positions_csv`, `_download_from_page`, `finally` cleanup | Existing sanitized stage/code boundary and connector/browser stages to time. Never expose credentials, URLs, page data, exceptions, or CSV bytes. |
| `src/omaha/logging_config.py` | `JsonFormatter`, `configure_logging` | Existing stdout sink and JSON/text envelope. T38 emits through this boundary; it does not add a sink or formatter. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `Alpine.store('patrimonioSync')`, `start`, `schedulePoll`, `poll`, `setError` | Starts a job, polls queued/running status, stops at local limit, opens only valid success preview, and renders safe errors. |
| `src/omaha/templates/_patrimonio_actions.html` | root `x-init`, `data-sync-state`, `dashboard-sync-btn` | Existing UI observation boundary for loading/terminal state and action availability. Preserve markup semantics; no new product copy is needed. |
| `tests/test_myprofit_sync_jobs.py` | lifecycle, serializer, duplicate/profile isolation, expiry, cleanup tests | Integration oracle for backend lifecycle, sanitized fields, concurrency, and no portfolio mutation. |
| `tests/e2e/test_patrimonio_sync_action.py` | local intercepted store harness and polling scenarios | Browser oracle for UI polling, local-limit signal, safe notification, and preview handoff without external service. |
| `docs/runbooks/myprofit-sync-telemetry.md` | new operator runbook | Defines collection window, bounded grouping, thresholds, interpretation, and cause-diagnosis gate. |

## Current Relevant Flow

1. **Input:** authenticated real-profile `POST /api/myprofit/sync` calls
   `start`, which creates `job_id`/`queued` and schedules the background job.
2. **Worker transformation:** `run_myprofit_sync_job` marks `running`, calls
   `download_positions_csv`, stores the returned file only in an owned temp
   path, and calls `_process_downloaded_csv`.
3. **Preview transformation:** parser errors become allowlisted `preview`
   failures; valid bytes create a short-lived preview and `succeeded`. No
   asset/position mutation occurs until explicit existing import commit.
4. **Terminal output:** failure, success, or expiry has `finished_at` and
   sanitized status. Cleanup removes only owned resources; expiry wins over a
   late result.
5. **Browser output:** `patrimonioSync` starts once, polls every 500 ms, and
   stops after 120 scheduled polls. `failed`/`expired` show safe notification;
   only valid `succeeded` opens the existing review modal.
6. **Existing logging boundary:** application logs are emitted to stdout by
   `omaha` logger. JSON mode wraps the message in fixed fields, but message
   fields are not independently typed; T38 therefore uses a fixed event name
   and allowlisted `key=value` tokens.

## Goals / Non-Goals

**Goals:**

- Correlate one run using only its `job_id`; one job is one run.
- Emit bounded events for state transitions, connector/preview stages,
  terminal result, total duration, per-stage duration, and UI local-limit
  signal.
- Preserve safe stage/code normalization and make invalid values observable as
  bounded fallback values, never raw input.
- Make success, failure, concurrency, polling, and UI-limit behavior
  testable offline and document analysis for real executions.
- Define storage/retention honestly: existing stdout is source; no DB/file
  persistence is added; collected lines must cover the runbook observation
  window.

**Non-Goals:**

- No change to `pollDelay`, `maxPolls`, `PREVIEW_TTL_SECONDS`, connector stage
  timeouts, retry policy, worker cap, expiry, status payload, or messages.
- No network/service-external telemetry, browser trace, screenshot, CSV,
  filename, URL, email, password, page content, or raw exception.
- No database model, migration, telemetry API for querying, dashboard, alert,
  metrics backend, log shipper, retention daemon, or automatic root-cause
  diagnosis.
- No reopening or implementation of F68, and no modification of T36, T37,
  F67, D06, or stable requirements of `myprofit-sync-job`, connector, or
  import modal.

## Decisions

### 1. Existing stdout logger is sole application storage boundary

**Decision:** emit `myprofit_telemetry` messages through the existing
`omaha` logger. Do not add DB rows, files, endpoints for querying, external
metrics, or a new collector. Operator retention means retaining those emitted
stdout lines for a minimum four-week observation window and, when volume is
insufficient, up to eight weeks; the application does not enforce retention.

**Why:** inspected repository has only stdout logging and existing JSON/text
formatters. Adding a sink or retention mechanism would invent infrastructure
and create an unrequested operational dependency. If deployment does not
retain stdout, runbook marks evidence unavailable rather than reconstructing
or fabricating it.

**Alternative rejected:** persist telemetry in `MyProfitSyncJob` or a new
table. This would mix operational history with one-hour product-job retention,
require migration/cleanup policy, and expose sensitive-data risk without an
owner-approved storage decision.

### 2. One job_id is run identity; event vocabulary is fixed

**Decision:** every event carries a UUID-shaped `job_id`; no profile name,
email, filename, request id, URL, or arbitrary label is emitted. Event name,
domain, status, stage, and code come from explicit finite allowlists. A run
is not assigned a second opaque id: `run_id` in the runbook means `job_id`.

**Why:** current job already guarantees one profile-owned execution identity,
and this bounds cardinality while preserving correlation across worker and UI
events.

### 3. Context-local recorder bridges service and connector

**Decision:** add a small internal recorder/context boundary. The service
opens a recorder for `job_id`; the real connector records named stage start/end
and failure duration through that context. Service records queue/run,
preview/handoff, terminal, expiry, and total duration. A connector fake that
does not know recorder context remains compatible and still yields service
boundary duration.

**Why:** changing `MyProfitConnector.download_positions_csv(profile)` to pass
telemetry would break existing one-argument fakes and widen the public
connector contract. A context-local recorder works within each bounded worker
and does not change connector input/output.

**Alternative rejected:** instrument only total job duration. It cannot
distinguish connector, browser, preview/handoff, and cleanup causes required by
the runbook.

### 4. UI limit uses one fire-and-forget, server-validated signal

**Decision:** when the Alpine store reaches its existing `maxPolls` boundary,
it emits at most one fixed `local_limit_reached` signal for current `job_id`
to a narrow authenticated job-owned route, then preserves current safe error
behavior. The route validates active profile/job ownership and logs a fixed
event; it never accepts a free-form body and never changes job status.

**Why:** browser-only console output cannot be correlated in the existing
stdout evidence stream. A one-way signal is the smallest source-collection
point and does not alter polling or terminal semantics. Client-side one-shot
guard plus fixed event vocabulary bounds normal event cardinality.

**Alternative rejected:** alter the polling response or add a server timeout.
Both would conflate UI observation with product behavior and reopen F68.

### 5. Sanitization happens before logging, not only at API serialization

**Decision:** recorder accepts only normalized stage/code/status and finite,
non-negative integer duration values within a documented upper bound. Unknown
values map to `connector`/`failed` or fixed `unknown` telemetry fallback;
messages are fixed templates. Logging code never receives exception objects,
CSV bytes, paths, URLs, credentials, filenames, or arbitrary strings.

**Why:** `to_status_dict` protects API output, but telemetry is a separate
boundary. Defense-in-depth prevents a future logger call from bypassing API
sanitization.

### 6. Runbook uses descriptive evidence, not an SLA or timeout rule

**Decision:** runbook collects real runs for at least four weeks with target
volume of 4–8 executions per week; extend to eight weeks when weekly volume is
below four or evidence is incomplete. It reports counts, rates, p50/p95/p99
durations, stage/code groups, UI-limit count, concurrency count, and missing or
invalid event count. Open a future cause-diagnosis slice only when a repeated
stage/code cluster has at least three runs across at least two weeks and is at
least 50% of failed runs, or when local-limit signals occur in at least two
runs; these are triage thresholds, not timeout changes.

**Why:** this gives owner-verifiable acceptance without treating T38 as an
external SLA or making a timeout decision from sparse data.

## Event Contract

Each emitted message uses this fixed shape inside the existing logger `msg`:

```text
myprofit_telemetry version=1 event=<event> job_id=<uuid> domain=<allowlisted> status=<allowlisted> stage=<allowlisted> code=<allowlisted> duration_ms=<integer> total_duration_ms=<integer-or-null>
```

Fields not relevant to an event use the fixed token `na`; they are never
omitted based on arbitrary input. The finite domains are:

- `event`: `transition`, `stage`, `terminal`, `ui_limit`;
- `domain`: `job`, `connector`, `browser`, `preview_handoff`,
  `polling_ui`, `concurrency`;
- `status`: `queued`, `running`, `succeeded`, `failed`, `expired`, `rejected`;
- `stage`: existing safe connector stages plus fixed `queue`, `poll`, `ui`,
  `handoff`, `terminal`, `concurrency`;
- `code`: existing `MyProfitSyncJob.SAFE_ERROR_CODES` after normalization plus
  fixed `started`, `transitioned`, `local_limit_reached`, `sync_in_progress`,
  `success`, `unknown`.

One `transition` event is emitted per actual job status transition, one
`stage` event per completed instrumented stage, one `terminal` event per
terminal settlement, and one `ui_limit` event per normal browser run. Duplicate
or foreign UI signals are rejected or ignored without changing status. Total
duration is emitted once at terminal settlement; stage duration is emitted at
stage completion. No event contains raw exception text or payload data.

## Change Map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/myprofit/telemetry.py` — new recorder and allowlists | No runtime telemetry context | Context-local recorder with fixed event vocabulary, finite numeric bounds, sanitization, and logger emission | Centralize security/cardinality invariants. |
| `src/omaha/routes/imports.py` — service lifecycle and status routes | Job lifecycle changes state silently except ordinary app logs | Record transitions, stage boundaries, terminal/expiry, total duration; add ownership-checked fixed UI-limit signal route with no DB mutation | Correlate server execution and browser limit without changing behavior. |
| `src/omaha/myprofit/connector.py` — connector stage boundaries | Stage errors expose only safe stage/code; durations absent | Record bounded duration for navigation/login/2FA/export/download/cleanup through recorder context; preserve exceptions and external calls | Distinguish connector/browser stages without raw data. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` — `patrimonioSync` | Poll limit only sets safe UI error | At existing limit, send one fixed job-owned signal, then set same safe error; preserve 500 ms × 120 polling and handoff | Observe UI boundary without timeout change. |
| `src/omaha/templates/_patrimonio_actions.html` — sync action markup | Existing state/notification rendering | No semantic change; retain state and accessibility boundary used by UI oracle | Avoid unrelated UI rewrite/copy change. |
| `src/omaha/models.py` — `MyProfitSyncJob` | Existing normalization/timestamps/retention | Reuse unchanged; no telemetry columns or migration | Preserve product retention and API contract. |
| `src/omaha/config.py` / `logging_config.py` | Existing log settings and stdout sink | Reuse unchanged; no telemetry setting/sink | Avoid invented infrastructure and timeout knobs. |
| `tests/test_myprofit_sync_jobs.py` — focused scenarios | Lifecycle tests do not assert telemetry | Capture bounded transition/stage/terminal events for success, failure, concurrency, expiry, and sanitization | Backend oracle. |
| `tests/e2e/test_patrimonio_sync_action.py` — local browser scenarios | Polling tests do not assert local-limit signal | Assert one fixed signal at limit, no extra polling, unchanged safe UI error/success handoff | UI/polling oracle without external access. |
| `docs/runbooks/myprofit-sync-telemetry.md` — new | No operational analysis guide | PT-BR/English operator guide for retention window, queries/grouping, thresholds, and diagnosis gate | Make evidence usable over 4–8 weeks. |
| `openspec/changes/.../specs/myprofit-sync-observability/spec.md` — new delta | No T38 capability contract | Normative bounded telemetry and runbook requirements/scenarios | Make Apply and review verifiable. |

## Risks / Trade-offs

- **[Sensitive data leaks through logging]** → allowlists and fixed tokens are
  applied before logger call; tests assert password, CSV, URL, path, filename,
  and raw exception text never appear.
- **[Log volume/cardinality grows without bound]** → one job identity, finite
  dimensions, one event per actual transition/stage/terminal, and one client
  UI-limit signal; no payload values or arbitrary labels.
- **[stdout is not retained by deployment]** → runbook marks collection
  unavailable; T38 adds no fake persistence or retroactive reconstruction.
- **[UI signal races with expiry/foreign job]** → route validates profile/job
  ownership and treats missing/terminal jobs as non-mutating observation; UI
  keeps token and one-shot guard.
- **[Duration interpreted as timeout evidence]** → runbook labels metrics
  descriptive, separates polling/UI from connector/browser and preview, and
  explicitly does not authorize F68 or a timeout change.
- **[Instrumentation changes functional flow]** → recorder is best-effort;
  logging failure cannot fail or roll back job, preview, cleanup, or commit;
  existing lifecycle tests remain unchanged apart from observability asserts.

## Migration Plan

1. Implement recorder and collection points behind existing lifecycle and
   logger boundaries.
2. Add focused backend and local-browser tests; run only applicable taskipy
   commands during Apply, with no external service or persistent DB mutation.
3. Deploy/restart normally; no migration or seed/reset is required.
4. Retain emitted stdout lines for the runbook window and analyze them using
   the new document. Rollback is code rollback; absence of telemetry must not
   alter sync behavior.

## Open Questions

None for this slice. Storage was resolved from repository evidence: existing
stdout is source, application retention is deliberately absent, and the
runbook requires an externally retained observation window without naming or
inventing a collector.

## Implementation Decisions

### 2026-08-24 — bounded in-memory UI observation deduplication

**Context:** the UI-limit route must ignore repeated observations without a
database column, telemetry table, or new retention setting. Application stdout
is the only telemetry sink, and the browser already owns a one-shot guard.

**Decision:** keep a service-local set keyed only by validated job identity for
active UI-limit observations. Ignore repeated, missing, foreign, and terminal
jobs; clear the entry when job reaches terminal settlement. Keep terminal-event
deduplication bounded in the same service (maximum 4096 job identities) so
late expiry cannot emit a second terminal event for one run.

**Impact:** no schema/config/logging drift; route remains non-mutating for
portfolio/job rows; single-process service preserves bounded one-shot behavior.

**Evidence:** inspected `MyProfitSyncJob` model (no telemetry persistence),
existing profile ownership route boundary, and `logging_config.py` (stdout-only
sink). Focused UI-limit and lifecycle tests assert one event, unchanged row
status/count, and expiry precedence.

### 2026-08-24 — bounded rolling terminal deduplication and fail-safe metadata

**Context:** Review R1 found that the original fixed terminal-ID set stopped
emitting after 4096 distinct jobs, while `stage_span` read exception metadata
properties outside its best-effort boundary. Either behavior could violate the
telemetry contract or alter the original synchronization exception.

**Decision:** replace the terminal set with a 4096-entry insertion-ordered
deduplication window. Every new terminal settlement emits and enters the
window; duplicate settlements still return while their identity remains in
the bounded window. The existing job-status lifecycle guards remain the
authoritative protection for late worker/expiry races. Read `stage` and `code`
through a helper that catches `BaseException` and falls back to fixed
allowlisted values; guard the complete telemetry finalizer so telemetry cannot
replace the original exception.

**Impact:** terminal telemetry remains bounded without dropping new-job events;
no schema, persistence, retention, status, cleanup, or connector mapping
changes. Malformed exception metadata produces ordinary sanitized telemetry and
preserves exception identity and propagation.

**Evidence:** R1 remediation tests cover 4097 distinct terminal IDs with one
duplicate settlement, bounded state, and exception-like metadata accessors
that raise while the original exception remains identical. Existing lifecycle,
connector, cleanup, and no-mutation tests remain the behavioral oracle.
