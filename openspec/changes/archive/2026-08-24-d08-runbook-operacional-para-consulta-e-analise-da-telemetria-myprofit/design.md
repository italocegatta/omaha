## Context

D08 is a documentation-only follow-up to Applied T38. T38 already emits
bounded telemetry through the existing `omaha` logger and records no telemetry
in the database. The operator gap is procedural: current documentation starts
with a retained log file, but does not explain how to prove which stdout
surface is authoritative, how to account for rotation, how to correlate one
`job_id` with the short-lived product row, or how to keep missing UI-limit
evidence separate from a completed/failed/expired run.

The runbook must remain honest about two independent retention boundaries:
stdout retention is external to the application, while `myprofit_sync_jobs`
rows are product lifecycle data and are pruned after their existing retention
deadline (default preview TTL is one hour). Neither boundary can support a
retroactive 4–8 week reconstruction when records are absent.

## Code Map

| File / symbol | Role in current flow | D08 use |
|---|---|---|
| `docs/runbooks/myprofit-sync-telemetry.md` | Existing operator guide with basic `rg` extraction, bounded grouping, and T38 diagnosis thresholds | Sole implementation target; expand into executable discovery, collection, correlation, rotation, classification, and weekly-analysis procedure. |
| `src/omaha/myprofit/telemetry.py` — `TELEMETRY_EVENT`, `TELEMETRY_VERSION`, `EVENTS`, `DOMAINS`, `STATUSES`, `STAGES`, `CODES`, `TelemetryRecorder._emit` | Defines fixed message prefix, field order, finite dimensions, UUID-shaped `job_id`, and bounded integer durations | Source of truth for exact event line, envelope location, allowlists, and validation rules. |
| `src/omaha/logging_config.py` — `JsonFormatter`, `configure_logging` | Sends `omaha` records to stdout; JSON puts formatted telemetry in `msg`, text keeps message after the standard prefix | Source of truth for JSON/text discovery; no sink or formatter change. |
| `src/omaha/config.py` — `Settings.LOG_LEVEL`, `LOG_FORMAT`, `effective_log_format` | Selects JSON in production by default and text in development unless explicitly overridden | Documents format inspection without adding settings or assuming a file path. |
| `src/omaha/routes/imports.py` — `MyProfitSyncService.status_for_profile`, `observe_ui_limit`, `expire_myprofit_sync_job`, `prune_expired_jobs`; `/api/myprofit/sync/{job_id}` and `/ui-limit` routes | Owns profile-safe status lookup, UI-limit observation, expiry precedence, and product-row pruning | Defines what DB correlation can confirm and what missing rows/events cannot prove. |
| `src/omaha/models.py` — `MyProfitSyncJob`, `to_status_dict`, `normalize_error`, lifecycle fields | Defines `job_id`, `profile_id`, status allowlist, error fields, lifecycle timestamps, `expires_at`, and `retention_until` | Defines read-only correlation columns and `failed` versus `expired` classification. |
| `alembic/versions/0020_myprofit_sync_jobs.py` — `myprofit_sync_jobs` schema | Confirms columns, status check, profile FK, and indexes | Schema anchor for the SQLite read-only query; no migration is added. |
| `openspec/changes/t38-telemetria-minima-e-runbook-de-analise-myprofit/design.md` and `tasks.md` | T38 contract, event shape, retention decision, thresholds, execution and review evidence | Upstream contract and review findings; D08 must not mutate either artifact. |

## Current Relevant Flow

1. A real profile starts one profile-owned job. T38 emits a `queued` event and
   then a `running` transition; connector/browser and preview/handoff stages
   emit bounded stage records; terminal settlement emits `succeeded`,
   `failed`, or `expired` with total duration.
2. Each telemetry message is emitted by logger `omaha` to stdout. In JSON mode
   the exact message is the `msg` value inside the existing seven-key JSON
   record. In text mode the same message follows the configured timestamp,
   level, and logger prefix. No application log file, telemetry table, query
   endpoint, shipper, or retention daemon exists.
3. `$store.patrimonioSync` polls with existing `500 ms × 120` bounds. If the
   browser reaches that local boundary, one `ui_limit` event with
   `polling_ui/ui/local_limit_reached` is attempted and the existing safe UI
   error remains. This is an observation that terminal status was not seen by
   the browser; it is not a server timeout, failure, or expiry classification.
4. `myprofit_sync_jobs` stores one row per job with `profile_id`, status,
   normalized error fields, and created/started/finished/expiry/retention
   timestamps. Exact `job_id` is the only join key. Product rows can disappear
   after `retention_until`; stdout and DB retention are not interchangeable.
5. Collection therefore starts from retained stdout/log output, validates and
   groups only bounded fields by `job_id` and `domain/stage/code`, then uses a
   read-only DB query only when the matching product row still exists. Missing
   segments, invalid events, absent terminal records, and pruned rows remain
   explicit evidence gaps.

## Goals / Non-Goals

**Goals:**

- Make `docs/runbooks/myprofit-sync-telemetry.md` sufficient for an operator
  to discover the active stdout source without guessing a log filename.
- Give exact commands for bounded extraction from the existing development
  stdout and production Compose `web` stdout surfaces, with JSON/text handling.
- Define the exact telemetry message shape, finite dimensions, accepted
  numeric values, duplicate handling, and safe evidence artifact boundary.
- Provide a repeatable 4–8 week procedure targeting 4–8 real runs per week,
  including observed-run, terminal-run, failure, expiry, missing, invalid,
  local-limit, and top-factor measures.
- Provide a read-only `myprofit_sync_jobs` query keyed by exact `job_id`, with
  profile ownership and lifecycle comparison, while documenting row pruning.
- Make `insufficient-evidence` mandatory whenever retention, volume,
  terminal coverage, or field validity prevents a defensible conclusion.

**Non-Goals:**

- No edits to `src/`, `data/portfolio.db`, Alembic schema, stable specs,
  T38 artifacts, roadmap, config, logging behavior, routes, UI, API, or tests.
- No telemetry persistence, log collector, rotation policy, alert, dashboard,
  SLA, timeout, retry, F68 decision, external-service diagnosis, or root-cause
  implementation.
- No writes through SQLite, SQLAlchemy, API routes, Docker, or taskipy DB
  tasks; no restart, live connector, credential use, CSV retrieval, or
  sensitive URL/path/filename extraction.

## Decisions

### 1. Revise one existing runbook, not create a new capability

**Decision:** edit only the authoritative runbook as implementation target and
add the minimum required `myprofit-sync-observability` delta under this D08
dossier. The delta records clarified operator requirements; it does not alter
T38 runtime or stable capability behavior.

**Why:** T38 already owns the normative telemetry contract and its runbook
file. A second guide would split source-of-truth instructions. OpenSpec's
`spec-driven` validator requires a delta for a valid change, so the delta is
limited to the existing runbook requirement and remains documentation-only.

**Alternative rejected:** add a telemetry query API, database history, or new
runbook capability. Existing implementation explicitly has no such storage or
API, and adding one violates D08 scope.

### 2. Discover source from configured stdout boundary

**Decision:** runbook identifies source by deployment mode: inspect the
existing dev process/launcher and its stdout capture, or retrieve the existing
production Compose `web` stdout. It must not assume `/tmp`, journald, a host
file, or a log shipper. It records source identity, format, time bounds, and
rotation segments before filtering.

**Why:** `configure_logging` proves stdout is authoritative, but repository
code does not define an application-owned file or host-level retention.

**Alternative rejected:** prescribe one universal file path or claim Docker,
journald, or supervisor retention beyond the existing Compose surface.

### 3. Parse the fixed message, not arbitrary log text

**Decision:** the runbook treats this exact message shape as the telemetry
  payload:

```text
myprofit_telemetry version=1 event=<event> job_id=<uuid> domain=<domain> status=<status> stage=<stage> code=<code> duration_ms=<integer-or-na> total_duration_ms=<integer-or-na>
```

In JSON mode, extraction reads only `.msg` from the existing seven-key record;
in text mode, extraction removes only the known logging prefix. Every event
must have the fixed field order, UUID-shaped lower-case-equivalent `job_id`,
allowlisted dimensions, non-negative bounded integer durations or `na`, and no
extra payload. Exact repeated source lines may be deduplicated once; values
must never be repaired by guessing.

The runbook lists the current finite sets: events `transition`, `stage`,
`terminal`, `ui_limit`; domains `job`, `connector`, `browser`,
`preview_handoff`, `polling_ui`, `concurrency`; statuses `queued`, `running`,
`succeeded`, `failed`, `expired`, `rejected`; stages from
`MyProfitSyncJob.SAFE_ERROR_STAGES` plus `queue`, `poll`, `ui`, `handoff`,
`terminal`, `concurrency`, `unknown`; and codes from
`MyProfitSyncJob.SAFE_ERROR_CODES` plus `started`, `transitioned`,
`local_limit_reached`, `sync_in_progress`, `success`, `unknown`.

**Why:** the logger formatter does not type message fields. Fixed-token
validation preserves T38's cardinality and sanitization boundary.

### 4. Treat retention and rotation as evidence gates

**Decision:** collection inventories all retained segments/source pages and
their earliest/latest coverage, then copies only matching telemetry lines to
an operator-owned analysis artifact. Rotation is not a recovery mechanism.
Missing segments, truncation, source gaps, or retention shorter than the
requested window are recorded; no line or event is reconstructed.

The minimum window is four complete weeks with target 4–8 real runs per week.
Extend through eight weeks when any week has fewer than four runs or evidence
is incomplete. If the window remains incomplete, report the literal status
`insufficient-evidence` and stop causal interpretation.

**Why:** application has no retention enforcement, and `myprofit_sync_jobs`
rows are short-lived product records rather than telemetry history.

### 5. Separate observed telemetry, terminal classification, and UI limit

**Decision:** report these measures separately:

- `observed_runs`: unique valid `job_id` in at least one accepted event;
- `terminal_runs`: unique `job_id` with accepted terminal event;
- `succeeded`, `failed`, and `expired`: terminal status counts;
- `incomplete_runs`: observed jobs without a terminal event;
- `invalid_event_count` and `missing_event_count`: rejected records and
  expected runs with no accepted telemetry, respectively;
- `ui_limit_count`: accepted `ui_limit` events, regardless of later terminal
  outcome.

`failed` means terminal status `failed`; `expired` means terminal status
`expired` and is not counted as connector/preview failure. A missing terminal
event is not relabeled as either. Failure rate is `failed / terminal_runs`
only when terminal coverage is complete enough to support the report; the
report also prints the observed and terminal denominators. A UI-limit event
means the browser exhausted its local polling observation boundary before it
saw terminal status. Its absence does not prove polling completed, and its
presence does not change server status.

**Why:** these are the only classifications supported by T38 event/status
contracts and existing lifecycle code. They prevent a browser observation or
log loss from becoming an invented product failure.

### 6. Correlate DB rows by exact `job_id`, read-only

**Decision:** runbook supplies a read-only SQLite `SELECT` against
`data/portfolio.db` for explicitly selected job IDs, returning only existing
`myprofit_sync_jobs` lifecycle/error columns and `profile_id`. If ownership
verification needs `profiles`, it uses only the declared `profile_id` foreign
key and keeps profile labels out of shared telemetry evidence. Correlation is
valid only when log `job_id` equals DB `job_id`; no timestamp, status, filename,
or profile-name inference is allowed.

The procedure compares event terminal status with DB `status`, event terminal
duration with `created_at`/`finished_at` as descriptive context, and event
stage/code with normalized `error_stage`/`error_code` for failed rows. A missing
or pruned DB row is reported as `db-correlation-unavailable`, not recreated.
The query is explicitly read-only and must not use `task db-reset`, migration,
seed, commit, delete, update, or live mutation routes.

**Why:** model/migration evidence confirms exact fields and FK. It permits
safe verification while preserving product DB and profile isolation.

### 7. Weekly factors and escalation remain descriptive

**Decision:** group accepted events by bounded `domain/stage/code`, count
unique affected terminal runs and failed runs, and report weekly and aggregate
rates plus p50/p95/p99 total and stage durations. Top failure factors use
failed terminal runs only; expired and UI-limit counts are separate factors
of observation, not silently folded into failure.

Open a separate future diagnosis proposal only when one normalized
`stage/code` cluster occurs in at least three runs across at least two weeks
and is at least 50% of failed terminal runs, or UI-limit events occur in at
least two runs. These thresholds do not authorize timeout, retry, F68, or
external-service changes.

## Change Map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `docs/runbooks/myprofit-sync-telemetry.md` — source/retention and collection sections | Basic retained-file `rg` examples and a high-level retention warning | Authoritative stdout discovery, dev/Compose `web` retrieval, source/rotation inventory, JSON/text extraction, bounded copy, and explicit evidence gates | Let operator reproduce collection without inventing a sink or path. |
| `docs/runbooks/myprofit-sync-telemetry.md` — event contract and grouping sections | Shape and dimensions implied by T38 but not fully operationalized | Exact line/envelope shape, finite sets, `job_id` validation, duplicate/invalid handling, denominators, and `domain/stage/code` grouping | Make parsing and weekly counts independently reproducible. |
| `docs/runbooks/myprofit-sync-telemetry.md` — correlation/classification sections | No SQL procedure; UI-limit and terminal outcomes can be conflated | Read-only `myprofit_sync_jobs` query, profile ownership check, row-retention limitation, and separate succeeded/failed/expired/incomplete/UI-limit definitions | Correlate only supported records and prevent false failure/expiry claims. |
| `docs/runbooks/myprofit-sync-telemetry.md` — weekly analysis/diagnosis sections | Thresholds exist but no complete weekly worksheet/procedure | Four-to-eight-week repeatable report with observed/terminal denominators, error rates, missing/invalid counts, top factors, and escalation gate | Produce consistent evidence for future decisions. |
| No runtime symbols | T38 runtime behavior already Applied | No code/schema/config/API/test behavior changes | Preserve exact D08 documentation-only boundary. |
| `specs/myprofit-sync-observability/spec.md` — modified runbook requirement | T38 requirement states high-level weekly analysis but omits source discovery, exact extraction, DB correlation, and classification procedure | Full requirement block with documentation-only clarifications and scenarios | Satisfy spec-driven validation while keeping runtime and stable specs unchanged. |

## Risks / Trade-offs

- **[Stdout was never retained]** → report `insufficient-evidence`; never claim
  that no runs or UI-limit events occurred.
- **[Rotation removed part of requested window]** → list missing coverage and
  extend collection when possible; do not stitch inferred events or alter
  source lines.
- **[Product row was pruned before correlation]** → report
  `db-correlation-unavailable`; retain telemetry-only analysis with its
  limitation.
- **[JSON/text or Compose prefixes confuse extraction]** → extract only the
  exact `myprofit_telemetry` message/token set and reject nonconforming lines.
- **[Failure rate hides incomplete runs]** → print observed and terminal
  denominators, keep incomplete runs separate, and mark the report
  `insufficient-evidence` when completeness is inadequate.
- **[Evidence copy leaks sensitive operational data]** → retain only fixed
  telemetry lines and selected DB lifecycle columns; prohibit credentials,
  CSV/content, URL, path, filename, and exception payloads in artifacts.
- **[Operator mistakes a descriptive threshold for a remediation]** → repeat
  the explicit non-goals beside weekly results and diagnosis gate.

## Migration Plan

1. Apply edits only to the existing runbook file.
2. Validate required headings, exact event tokens, read-only command markers,
   classification rules, thresholds, and forbidden-scope boundaries with the
   existing focused runbook test plus documentation inspection.
3. No migration, seed/reset, server restart, connector execution, or refresh
   receipt is needed because no runtime code is touched.
4. Rollback is reverting the single runbook edit; telemetry and DB behavior
   remain unchanged.

## Open Questions

None. Existing T38 implementation, logger configuration, lifecycle route,
model/migration, and review findings provide enough evidence to specify every
requested runbook behavior without inventing runtime behavior or retention.

## Implementation Decisions

### 2026-08-24 — source procedure follows deployment-owned stdout surfaces

**Context:** implementation confirms `JsonFormatter` and text logging both
write through the `omaha` stdout handler. `docker-compose.yml` exposes the
development `web` process, while `prod.yml` exposes the existing production
Compose `web` service and documents `docker compose ... logs web`; neither
deployment declares an application-owned telemetry file or retention daemon.

**Decision:** the runbook names stdout as authoritative, gives bounded
Compose retrieval only for the existing `web` service, and requires operators
to declare any development capture or rotated segment before reading it. It
never claims a host path, journald, shipper, or guaranteed retention. Safe
analysis output contains only timestamp plus fixed `myprofit_telemetry` fields.

**Impact:** operators can reproduce JSON/text extraction and rotation
coverage checks without runtime changes or invented deployment behavior. A
missing or partial source remains `insufficient-evidence`.

**Evidence:** `src/omaha/logging_config.py:34-120`,
`src/omaha/config.py:165-206`, `docker-compose.yml:3-18`, and
`prod.yml:57-84`/`44-53`; source and retention sections in the D08 runbook.

### 2026-08-24 — read-only correlation uses FK scope, not inferred joins

**Context:** `MyProfitSyncJob.profile_id` is a foreign key and the model owns
the status, normalized error, lifecycle, expiry, and retention fields. Rows
are pruned after `retention_until`; telemetry is not persisted in the product
database.

**Decision:** the runbook uses an exact parameterized `SELECT` with
`-readonly`, exact `job_id`, explicit `profile_id`, and an FK existence check.
It omits filenames, work paths, and payload columns. Missing/pruned rows are
`db-correlation-unavailable`; timestamps provide context only.

**Impact:** profile isolation and product DB protection remain explicit, while
PostgreSQL is handled only through an already approved read-only client
without inventing credentials or connection details.

**Evidence:** `src/omaha/models.py:424-546`,
`alembic/versions/0020_myprofit_sync_jobs.py:15-56`, and
`src/omaha/routes/imports.py:746-768`.

### 2026-08-24 — Compose retrieval preserves application envelope

**Context:** Docker Compose can add its own display timestamp to `logs`
output. That prefix would make a JSON line no longer parse as the exact
application `JsonFormatter` object, and would add a second timestamp to text
mode. Application JSON already carries `ts`; text mode already carries the
configured timestamp prefix.

**Decision:** the runbook keeps Compose's bounded `--since`/`--until` window
and `--no-log-prefix`, but omits Compose `--timestamps`. Extraction therefore
receives the application line unchanged and derives coverage from the
application envelope/prefix. No Docker display metadata is treated as
telemetry evidence.

**Impact:** JSON/text extraction remains reproducible against the existing
Compose `web` stdout surface without inventing a second parser or retaining a
raw Compose capture.

**Evidence:** `prod.yml:44-53`, `src/omaha/logging_config.py:42-69`, and the
JSON/text Compose branches in the D08 runbook.

### 2026-08-24 — weekly report is run-anchored and terminal-gated

**Context:** Review R1 found two documentation-command defects. The report
calculated a Monday bucket independently for every event, so one job crossing
Monday appeared in multiple weekly buckets. Its factor loop also accepted any
failed stage without proving that the same `job_id` had a failed terminal
outcome.

**Decision:** retain earliest accepted event timestamp as the documented
run-level anchor. Build one record per `job_id`, assign exactly one UTC Monday
bucket, and route all events/measures through that bucket. Define
`terminal_failed_runs` as unique jobs with exactly one accepted terminal event
whose status is `failed`; extract factors only from failed stage events for
those jobs, counting each job once per normalized `stage/code` cluster.
Terminal conflicts are excluded from terminal arithmetic; incomplete jobs stay
in their anchor week but never enter failed factors. Successful, expired,
UI-limit-only, and incomplete jobs remain separate.

**Impact:** weekly observed/group/duration/factor counts cannot double-count a
cross-boundary job or treat a failed stage followed by terminal success as a
failed run. No runtime, telemetry, storage, DB, or stable contract changes.

**Evidence:** runbook §4.1 and §4.2 report command; D08 review findings
`R1-F01` and `R1-F02`; T38 event/status contract and existing terminal
settlement flow.
