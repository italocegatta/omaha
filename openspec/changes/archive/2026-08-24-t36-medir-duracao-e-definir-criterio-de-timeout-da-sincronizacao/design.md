## Scope

Quality/measurement slice. No runtime timeout change. No external network or
credentials. No production DB. No destructive reset. Current working-tree
changes in `tests/visual/artifacts/f60-atualizar-posicao-*.png` are pre-existing
and must remain untouched.

## Owner scope decision — 2026-08-24

Owner changed T36 measurement sample from the previously proposed sample to
exactly **15 fake/mock connector repetitions per bounded measurement run**.
Rationale: align measurement workload with owner instruction before Apply while
keeping the harness bounded, offline, repeatable, and explicit about evidence
quality. This is a workload decision, not a claim that 15 repetitions establish
external-service performance or statistical equivalence to the former plan.
Every Apply procedure, acceptance check, and evidence record SHALL use
`sample_size = 15`; no measurement result exists at this proposal gate.

## Code map

| File | Symbols / region | Role in current flow |
|---|---|---|
| `src/omaha/routes/imports.py` | `PREVIEW_TTL`, `MyProfitSyncService.start` | Creates profile-scoped queued job, sets `expires_at` from `settings.PREVIEW_TTL_SECONDS`, and schedules background execution. |
| `src/omaha/routes/imports.py` | `MyProfitSyncService.run_myprofit_sync_job` | Acquires bounded worker slot, marks `running`, invokes connector, maps sanitized connector failures, and settles cleanup/reservation. |
| `src/omaha/routes/imports.py` | `_process_downloaded_csv` | Writes owned temporary CSV, parses through `preview_from_blob`, publishes `succeeded` preview or expires/fails; does not commit portfolio rows. |
| `src/omaha/routes/imports.py` | `status_for_profile`, `expire_myprofit_sync_job`, `prune_expired_jobs` | Defines polling-visible terminal behavior, job expiry, preview cleanup, and bounded retention. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `Alpine.store('patrimonioSync')`; `pollDelay`, `maxPolls`, `schedulePoll`, `poll`, `setError` | Starts browser action, polls status, stops at client polling boundary, keeps failed/expired modal closed, and opens valid success preview. |
| `src/omaha/templates/_patrimonio_actions.html` | `dashboard-sync-btn`, notification template | Exposes action and sanitized lifecycle presentation on real profiles; Família has no action. |
| `src/omaha/models.py` | `MyProfitSyncJob`, fields `started_at`, `finished_at`, `expires_at`, `retention_until`, `to_status_dict` | Persists lifecycle timestamps and exposes only sanitized status/preview/error fields. |
| `src/omaha/myprofit/connector.py` | `MyProfitConnector`, `PlaywrightMyProfitConnector`, `MyProfitConnectorTimeouts` | Separates connector boundary from route/DB and defines per-stage Playwright timeout values. Measurement uses fake connector, never concrete connector. |
| `tests/test_myprofit_sync_jobs.py` | existing lifecycle/preview/expiry tests | Existing temporary-DB boundary for service behavior, cleanup, expiry precedence, no portfolio mutation, and sanitized errors; future T36 harness belongs here. |
| `tests/test_myprofit_connector.py` | fake browser classes and timeout assertions | Offline oracle for connector stage timeout inventory; no browser/network execution. |
| `tests/e2e/test_import_modal.py` | review/preview modal assertions | Confirms F65 review payload/rendering remains an observation oracle only; T36 does not change this file. |
| `tests/e2e/test_patrimonio_sync_action.py` | intercepted sync polling choreography | Browser timeout inventory and behavior oracle: local fake responses, bounded waits, failed/expired modal closure, manual commit boundary. |
| `tests/conftest.py` | `_INTEGRATION_PREFIXES` | `tests/test_myprofit_sync_jobs.py` is already explicitly integration; no marker allow-list change is needed. |
| `tests/PERFORMANCE.md` | full-suite wall-clock contract | Canonical suite ceiling is `<=300s`; T36 evidence must not be confused with suite duration. |
| `openspec/specs/myprofit-sync-job/spec.md` | lifecycle, preview handoff, expiry, mutation guard requirements | Stable product contract to preserve; no delta. |
| `openspec/specs/myprofit-position-csv-connector/spec.md` | offline boundary and bounded per-stage timeout requirements | Stable connector contract to preserve; no delta. |
| `openspec/specs/import-modal/spec.md` | successful handoff, failed/expired no-modal, explicit commit requirements | Stable UI contract to preserve; no delta. |

## Current relevant flow

1. **Input:** authenticated real-profile `POST /api/myprofit/sync` calls
   `MyProfitSyncService.start`. It creates one `queued` job, sets
   `expires_at = now + PREVIEW_TTL_SECONDS`, and schedules
   `run_myprofit_sync_job`.
2. **Transformation:** worker marks job `running`, calls injected
   `MyProfitConnector.download_positions_csv(profile)`, stores returned bytes
   only in an owned temporary directory, and routes bytes through
   `preview_from_blob` / `_process_downloaded_csv`.
3. **Output:** valid bytes produce `succeeded`, `finished_at`, retention, and a
   preview payload. Portfolio assets/positions remain unchanged until existing
   explicit `/api/import/commit`. Connector/parser failures become sanitized
   `failed`; expiry wins over late success/failure.
4. **Browser boundary:** `patrimonioSync.start` waits for `queued`, then polls
   every `pollDelay = 500 ms`; `maxPolls = 120` gives nominal
   `500 × 120 = 60,000 ms` of scheduled polling delay. A request/response can
   add wall time; this is not a server deadline. `failed`/`expired` call
   `setError`, while only valid `succeeded` opens review.
5. **Other boundaries:** default `PREVIEW_TTL_SECONDS = 3600 s` controls job
   expiry and preview freshness; terminal retention uses the same TTL. The
   connector has independent per-stage Playwright values: navigation 45,000 ms,
   login settle 5,000 ms, optional 2FA probe 30,000 ms, export control 30,000
   ms, CSV option 10,000 ms, and download capture 45,000 ms. These are stage
   timeouts, not a single end-to-end deadline. E2E waits (for example 8 s and
   3 s in `test_patrimonio_sync_action.py`, and 15 s review waits in
   `test_import_modal.py`) are test-harness limits, not runtime limits.

Boundary cases for measurement/oracles: queued/running, success with valid
preview, connector failure, parser failure, expiry before publish, late worker
after expiry, foreign/Família access, preview without commit, and cleanup of
only owned temporary paths.

## Measurement design

### Harness boundary

Add one explicitly named, test-only measurement scenario to
`tests/test_myprofit_sync_jobs.py` only if implementation is authorized after
this proposal. Reuse existing integration classification and fixtures. The
harness SHALL:

- inject a deterministic fake implementing `MyProfitConnector`; fake returns a
  small valid CSV fixture or raises an allowlisted `MyProfitConnectorError`;
- use a temporary DB already supplied by test isolation and a `tmp_path`
  `temp_root`; never import live `SessionLocal` against `data/portfolio.db`,
  launch Playwright, load `.env`, or call `myprofitweb.com`;
- create and run jobs through `MyProfitSyncService` and the same
  `_process_downloaded_csv`/`run_myprofit_sync_job` boundary, not by timing a
  parser-only function;
- collect `time.perf_counter()` around each complete fake job and also record
  persisted `started_at → finished_at` when available;
- run exactly 15 fake/mock connector repetitions per measurement run, with deterministic
  success/failure schedule. Success percentiles use successful samples only;
  failures are separately counted and classified by terminal status/stage/code;
- write no portfolio mutation and assert before/after counts for
  `Asset`, `Position`, and `DbMutation` are equal;
- append one machine-readable JSON evidence block to this change's `tasks.md`.
  No evidence file is created during proposal. Planned schema:

```json
{
  "change_id": "t36-medir-duracao-e-definir-criterio-de-timeout-da-sincronizacao",
  "run_id": "<timestamp-or-run-stamp>",
  "environment": {"python": "", "platform": "", "pytest": ""},
  "sample_size": 15,
  "successes": 0,
  "failures": 0,
  "failure_rate": 0.0,
  "success_duration_ms": {"mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "min": 0.0, "max": 0.0, "stdev": 0.0, "iqr": 0.0, "mad": 0.0},
  "failure_statuses": {},
  "boundaries_ms": {"poll_delay_x_max_polls": 60000, "job_expiry": 3600000, "preview_ttl": 3600000},
  "playwright_stage_timeouts_ms": {"navigation": 45000, "login_settle": 5000, "two_factor_probe": 30000, "export_button": 30000, "csv_option": 10000, "download": 45000},
  "candidate_timeout_ms": null,
  "decision": "<covered|increase-justified|insufficient-evidence>"
}
```

The JSON is evidence, not a runtime configuration source.

### Metrics and decision rule

- `n` is total attempts; report successes and failures separately. A valid
  decision run requires `n = 15`, at least one successful sample, zero
  unclassified failures, and no external access. A run with no successful
  samples, or with insufficient repeatability/quality for the metrics, is
  `insufficient-evidence` and F68 stays blocked.
- Report arithmetic mean, p50/p95/p99 using one documented percentile method,
  min/max, sample standard deviation, IQR (`p75 - p25`), and MAD. Report
  terminal status plus sanitized stage/code for every failure class.
- Define candidate safe margin as
  `p99_success + max(2 × IQR, 5,000 ms)`, rounded up to the next 5,000 ms.
  This margin is explicit, bounded, and separate from connector stage
  timeouts. It SHALL never exceed `job_expiry` or `preview_ttl`.
- If candidate ≤ current nominal polling boundary (60,000 ms), record
  `covered`; no F68 increase is justified by this run.
- If candidate > 60,000 ms and candidate < both TTL/expiry boundaries, record
  `increase-justified` and hand candidate to F68 as a review target; F68 must
  still preserve failed/expired status, manual commit, sanitized errors, and
  no infinite retry.
- If candidate violates a TTL/expiry boundary, failure rate is non-zero in a
  way not explained by the declared fake schedule, or timing is unstable
  (`p99`/IQR cannot be reproduced in a second bounded run), record
  `insufficient-evidence`; do not infer a timeout.

The fake schedule is a system-boundary calibration, not evidence of MyProfit
network latency. No T36 result may claim real-service performance or authorize
external credentials. F68 must treat any real connector latency evidence as a
separate owner-approved input.

## Implementation decisions

- **Behavior:** measurement only; no `pollDelay`, `maxPolls`, TTL, expiry,
  Playwright timeout, status, message, or API change.
- **Validation:** exact sample count, success/failure reconciliation, finite
  non-negative durations, required percentile fields, boundary inventory, and
  before/after mutation counts.
- **Error handling:** fake failures use existing sanitized connector error
  types; harness fails on unexpected exceptions, leaked paths, foreign status,
  or unclassified failure. No retry/skip/xfail masking.
- **Compatibility:** preserve D06 surface decisions, F65 triage payload and
  ordering, explicit manual review/commit, Família guard, profile isolation,
  bounded worker count, cleanup ownership, and stable specs.
- **Non-goals:** F67 ordering, F68 timeout implementation, connector redesign,
  credentials, network probes, browser rendering changes, production DB
  inspection/mutation, destructive reset, runtime telemetry, and full-suite
  performance optimization.

## Change map

| File/symbol | From | To | Reason |
|---|---|---|---|
| `tests/test_myprofit_sync_jobs.py` — new named T36 measurement scenario | Existing lifecycle tests only; no repeated duration evidence | Optional test-only fake/mock harness with 15 bounded attempts, temporary state, metrics, and evidence append | Produce reproducible quality evidence without touching production flow. |
| Active change `tasks.md` — execution evidence section | Planning checklist only | JSON evidence record plus oracle results and decision | Make T36 result durable and handoff-ready for F68. |
| Production routes/templates/models/connector | Current behavior above | Unchanged | T36 must not implement timeout or alter D06/F65/F59/F60 behavior. |
| `specs/sync-duration-measurement/spec.md` | No durable T36 measurement contract | Added internal test/observability contract for bounded fake measurement and evidence schema | Make Apply procedure and F68 handoff testable without changing product specs. |
| Stable product specs | Current requirements | Unchanged | Measurement harness is internal quality evidence, not runtime product behavior. |

## Risks and preserved patterns

- **Fake evidence mistaken for external SLA:** label fake schedule and system
  overhead; prohibit real-service claim and require owner review before F68.
- **Timer noise:** fixed sample count, deterministic schedule, monotonic clock,
  second bounded repeatability run, and dispersion metrics; unstable result
  blocks decision.
- **DB contamination:** use existing temporary test isolation, assert mutation
  counts, never invoke reset/seed/commit route, and preserve pre-existing
  visual artifact changes.
- **Boundary conflation:** report polling, job/preview TTL, connector stage,
  and Playwright harness waits in separate fields; never sum unrelated limits
  into a runtime timeout.
- **Regression masking:** retain existing focused tests and explicit failure
  statuses; no skip, xfail, retry, or altered assertions to make measurement
  green.

## Implementation Decisions

### Apply preflight — 2026-08-24

- **Context:** `MyProfitSyncService` receives its connector, session factory,
  and temporary root as constructor dependencies. The repository integration
  fixture binds `SessionLocal` to a session-scoped temporary SQLite database
  before test collection; the active application service is separately
  shutdown by the existing sync-row fixture.
- **Decision:** construct a fresh service in the named T36 test with a fake
  connector, the fixture-safe `SessionLocal`, and an exact `tmp_path` child.
  Start each job through `start()` and execute it through
  `run_myprofit_sync_job()`; do not call production connector construction,
  alter global settings, or add a second DB bootstrap.
- **Impact:** timing covers connector schedule plus application job/file/parser
  overhead while preserving the real job boundary. Temporary CSV directories
  remain owned by this service and are asserted absent after every attempt.
- **Evidence:** inspected `MyProfitSyncService.__init__`, `start`,
  `run_myprofit_sync_job`, `_process_downloaded_csv`, and
  `tests/conftest.py` safe-database bootstrap; `git diff HEAD~1` showed only
  pre-existing F67/T36 dossier/worktree changes and no runtime timeout edit.

### Boundary inventory interpretation — 2026-08-24

- **Context:** current code exposes independent limits: Alpine polling
  (`500 ms × 120`), `PREVIEW_TTL_SECONDS` (`3600 s`) used for job expiry and
  preview freshness/retention, connector stage defaults, and Playwright test
  waits.
- **Decision:** record each family separately in evidence. Candidate timeout
  compares only with the nominal 60,000 ms polling boundary and the 3,600,000
  ms job/preview bounds; connector and browser harness values are inventory,
  not summed runtime deadlines.
- **Impact:** T36 can hand F68 a bounded review target without changing
  `pollDelay`, `maxPolls`, TTL, connector timeouts, or browser tests.
- **Evidence:** inspected template store at `pollDelay: 500` and
  `maxPolls: 120`, `Settings.PREVIEW_TTL_SECONDS = 3600`,
  `MyProfitConnectorTimeouts`, and focused E2E wait values in
  `test_patrimonio_sync_action.py` / `test_import_modal.py`.
