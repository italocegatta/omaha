## Context

F58 owns the synchronous, profile-guarded boundary
`omaha.myprofit.connector.MyProfitConnector.download_positions_csv(profile)`.
The current import flow is request-bound: `POST /api/import/preview` reads an
`UploadFile`, decodes UTF-8, calls `parse_positions`, stores an
`ImportPreview`, and returns `_build_preview_response`; the Alpine
`$store.importModal.uploadFile()` method consumes that response and advances to
review. `POST /api/import/commit` is a separate, explicit destructive action.

F59 adds only the server-side bridge between those two boundaries. F60 owns the
dashboard action and browser polling choreography. F59 must therefore expose a
stable job/status contract that F60 can consume without inventing another
preview shape or commit path.

## Owner-approved validation amendment

Production design is unchanged: runtime worker still consumes the F58 connector
contract, persists profile-scoped lifecycle state, reuses the internal import
preview path, and preserves manual commit safety. Apply validation is narrowed
to essential internal dependencies and high-value failure boundaries.

F59 tests SHALL cover only job state/concurrency, expiry and owned-path cleanup,
profile/Família authorization, direct internal CSV-to-existing-preview
handoff, normalized error-to-page/job state with `preview: null` and no-modal
behavior, and DB-mutation safety where affected. Tests use temporary DB/path
resources and synthetic internal inputs or persisted state transitions.

F59 tests SHALL NOT exercise, fake, mock, launch, log into, download from, or
otherwise involve `MyProfitConnector`, Playwright, browser/network navigation,
credentials, or MyProfit service behavior. F58 owns connector behavior;
connector integration validation remains outside this slice (F58/T31).

## Implementation Decisions

### R1 remediation: deterministic settlement, retention, and error boundaries

- Context: review R1 found that shutdown only removed in-memory directories,
  expired rows had no retention deadline or pruning path, serialized stages were
  not bounded, and connector failures could overwrite an expired lifecycle
  state.
- Decision: shutdown settles every currently reserved queued/running job as
  `expired`, assigns `finished_at`/`retention_until`, removes only its exact
  registered path, and clears reservations. Worker failure/preview paths refresh
  their job row before transition so a stale worker cannot publish or replace
  that terminal state. Add profile-scoped, bounded terminal-row pruning after
  `retention_until`. Normalize stage and code through explicit model allowlists
  both when persisting worker errors and when serializing status/page state.
- Impact: app restart/test lifecycle cannot inherit stale reservations; expired
  rows have bounded storage lifetime; arbitrary stage/code values cannot reach
  API or page context; deadline and shutdown expiry always outrank connector
  failure. F58 connector behavior and manual preview/commit boundaries remain
  unchanged.
- Evidence: R1-focused tests cover shutdown settlement and replacement start,
  retention-window preservation plus bounded pruning, secret/path stage-code
  fallback, and late failure retaining `expired` status.

### Apply preflight: preserve existing request and connector boundaries

- Context: the existing manual JSON route owns byte validation and
  `_build_preview_response`, while F58 exposes a synchronous
  `download_positions_csv(profile)` protocol and already sanitizes connector
  failures.
- Decision: extract `preview_from_blob` as the only shared byte-to-preview
  path; keep connector invocation synchronous inside FastAPI `BackgroundTasks`
  with an app-owned semaphore and independent `SessionLocal` session. Resolve
  the session-bound `Profile` directly for sync routes so the Família sentinel
  returns the existing 409 before service lookup or filesystem work.
- Impact: manual and sync previews remain wire-compatible; no HTTP self-call,
  `asyncio.create_task`, commit call, or connector alteration is introduced.
- Evidence: mapped `imports.py`, `auth.py`, `main.py`, and archived F58
  connector contract inspected before edits; `require_active_profile` maps
  Família to `None`, so the new sync dependency must inspect the sentinel row
  directly.

### Apply implementation decision: internal downloaded-blob seam

- Context: owner-approved F59 validation forbids connector doubles and all
  connector, browser, credential, network, and MyProfit service behavior, but
  production still needs to pass connector bytes through the same worker path.
- Decision: keep connector invocation exclusively in
  `run_myprofit_sync_job`, and factor the post-download file/parse/persist
  sequence into private `_process_downloaded_csv`. Focused tests call that
  internal seam with synthetic filename/bytes and persisted job state; they do
  not construct or invoke the F58 adapter.
- Impact: internal tests cover lifecycle, owned cleanup, expiry, preview shape,
  page-safe errors, and mutation safety without broadening F59 validation or
  changing F58. Runtime remains connector-compatible and uses
  `preview_from_blob` as its sole CSV-to-preview path.
- Evidence: F59 focused test module contains no connector/browser/network/
  credential setup; `uv run task test-file tests/test_myprofit_sync_jobs.py`
  passes with 15 tests.

### Code map

- `src/omaha/routes/imports.py`
  - `_raw_to_dict`, `_dict_to_raw`: serialize/rehydrate parser output already
    stored by `ImportPreview`.
  - `_load_preview`, `_is_expired`: existing profile/TTL guards to preserve for
    sync-created previews.
  - `_build_preview_response`: canonical response shape consumed by
    `$store.importModal`; must remain the single preview serializer.
  - `preview_import`: current manual upload boundary. Extract a shared internal
    blob-to-preview helper; do not make the background job call HTTP or duplicate
    this logic.
  - `commit_import`: existing explicit confirmation, snapshot, audit, and
    profile-writable boundary. F59 never calls it.
  - New `MyProfitSyncService`/route helpers: create, schedule, execute, poll,
    expire, and clean profile-scoped jobs.
- `src/omaha/routes/pages.py`
  - `_common_context`, `_render_patrimonio`, `index`, and `get_patrimonio`:
    current authenticated page context and Família/profile view resolution.
    Add only sanitized latest sync status/error context needed for a page error;
    do not start work or open the modal from a page GET.
- `src/omaha/main.py`
  - `create_app`, startup/shutdown registration, and `app.state` wiring:
    construct one bounded sync service per app, inject the F58 connector seam,
    and stop/clean owned workers on shutdown. Preserve quote-service lifecycle.
- `src/omaha/csv_import.py`
  - `parse_positions`: pure parser used by both manual upload and successful
    downloaded CSV. Preserve UTF-8/BR-number parsing, broker totals, malformed
    row behavior, and no `qty * price` recomputation.
- `src/omaha/models.py`
  - `Profile.is_family_sentinel`: real-profile/Família boundary.
  - `ImportPreview`: existing short-lived parsed preview and profile FK.
  - New `MyProfitSyncJob`: job id, profile id, lifecycle state, preview link,
    sanitized error fields, filename/file-work metadata, and timestamps/expiry.
- `src/omaha/myprofit/connector.py`
  - F58 `MyProfitConnector`, `MyProfitCsvDownload`, and sanitized stage/code
    errors are consumed unchanged. No connector implementation changes belong
    here.
- `alembic/versions/<new-head>_myprofit_sync_jobs.py`
  - New migration for the job table, profile/preview indexes or constraints,
    and rollback. Exact revision filename is created by the apply agent from
    the current Alembic head; no existing migration is edited.
- `tests/test_imports_routes.py`, `tests/test_import_preview.py`,
  `tests/test_import_get_preview.py`, and a new focused integration test module:
  current TestClient/import preview contracts plus internal job lifecycle,
  authorization, cleanup, page-state, and mutation-boundary scenarios only.
  `tests/conftest.py` must explicitly classify any new DB/TestClient file.

### Current relevant flow

1. Manual input arrives as multipart CSV at `POST /api/import/preview`.
2. Route enforces authenticated active writable real profile, upload size and
   UTF-8 boundaries, then transforms text → `RawPosition[]` via
   `parse_positions` → profile-scoped `ImportPreview.raw_json`.
3. `_build_preview_response` re-matches rows against active-profile assets and
   emits `preview_id`, `auto_matched`, `unmatched`, and `asset_classes`.
4. `$store.importModal` owns review assignments. It can later call
   `POST /api/import/commit`; that route captures snapshot/audit and requires
   explicit user confirmation through its existing contract.
5. F58 connector input is a real profile and output is in-memory filename + CSV
   bytes. It rejects Família before credential resolution/browser launch and
   sanitizes login/download failures. F59 consumes this production boundary;
   its focused tests do not invoke or double the connector.

Boundary conditions to preserve: stale/foreign preview is invisible; preview
   TTL is enforced; malformed/empty/oversized/non-UTF-8 CSV does not create a
   usable preview; Família is read-only; no asset/position row changes happen
    during sync; no production DB is used by tests; no connector, browser,
    credential, network, or external MyProfit behavior is involved by tests.

## Goals / Non-Goals

**Goals:**

- Start an authenticated background sync with `202 Accepted` and a job id.
- Expose profile-safe polling with states `queued`, `running`, `succeeded`,
  `failed`, and `expired`.
- Permit at most one active job per real profile; permit Italo and Ana jobs to
  overlap, bounded by a two-worker global cap matching the two real profiles.
- Keep job rows, temporary directories, downloaded CSV files, and generated
  previews isolated by profile and job id.
- Reuse existing parser and preview response shape, returning preview data only
  after successful download/parse/persistence.
- Surface only sanitized PT-BR page-safe error text plus stable stage/code;
  failed jobs return no preview and cannot trigger modal opening.
- Preserve manual class assignments, explicit commit confirmation,
  `db-mutation-safety` snapshot/audit guards, CSV totals, and existing preview
  expiration behavior.

**Non-Goals:**

- No F60 button, Alpine action, modal redesign, automatic polling UI, or visual
  state implementation. F60 consumes this contract.
- No automatic `/api/import/commit`, asset/class/position mutation, assignment
  inference beyond existing preview matching, or bypass of confirmation.
- No F58 connector changes, selector changes, credential/config changes, live
  MyProfit calls in tests, production DB access, seed changes, or broad runner/
  harness work.
- No distributed queue, multi-process job broker, retry loop, or automatic
  browser CAPTCHA/2FA bypass. One app process owns its bounded worker service.

## Decisions

### 1. Persist job lifecycle in an ORM row; keep payloads profile-scoped

Add `MyProfitSyncJob` with UUID/string `job_id`, `profile_id`, status,
`preview_id`, sanitized `error_stage`/`error_code`, sanitized filename,
non-public work-directory metadata, and UTC lifecycle/expiry timestamps. Add a
head migration and indexes on `(profile_id, created_at)` and active status.
Foreign keys enforce that a job and its generated preview belong to existing
portfolio identity. Status GET always compares job `profile_id` to the active
real profile; mismatch returns 404 without revealing status or filenames.

Alternative rejected: an in-memory-only dictionary. It loses poll state on
reload and cannot let `pages.py` render the latest page-safe error. A distributed
queue is unnecessary for one self-hosted process and would enlarge F59.

### 2. Use app-owned bounded `BackgroundTasks` with a service lock

`POST /api/myprofit/sync` creates the queued row, reserves the profile under a
thread lock, and schedules a synchronous worker through FastAPI
`BackgroundTasks`. The worker opens its own `SessionLocal` session and calls the
F58 connector in its own threadpool task. The service maintains a per-profile
active reservation and a global semaphore of two workers; duplicate starts for
one profile return `409` with stable `sync_in_progress` and the existing job id.
Different real profiles may run concurrently. Completion/failure always
releases the reservation in `finally`.

Alternative rejected: direct `asyncio.create_task`. Existing quote-service
notes document its sync `TestClient` failure mode; `BackgroundTasks` preserves
the repo's established request-boundary pattern and still returns the response
before the production client observes task completion. No retry is implicit.

### 3. Reuse preview transformation through an internal blob helper

Extract a helper in `imports.py` that accepts `(db, profile, bytes)` and owns
upload-size, UTF-8, parser, empty-result, `ImportPreview` persistence, and
`_build_preview_response` preparation. Manual `preview_import` calls it. The
worker writes connector bytes to a job-unique temporary file only long enough
to make cleanup auditable, reads the bytes through the helper, then removes the
file/directory. It never self-POSTs to the HTTP route and never calls commit.

On success, status JSON contains the same preview object as manual upload:
`preview_id`, `auto_matched`, `unmatched`, and `asset_classes`, plus job status
and sanitized filename. `$store.importModal` can assign that object directly;
the server does not mutate client state or commit data.

### 4. Define stable status/error/expiry contract

- Start: `POST /api/myprofit/sync` → `202` with `{job_id, status:"queued"}`.
- Poll: `GET /api/myprofit/sync/{job_id}` → `200` for an owned known job with
  status, timestamps, and `preview:null` until success. Unknown or foreign
  jobs → `404`.
- Success: `status:"succeeded"`, `preview` is the existing preview response;
  no commit result is returned.
- Failure: `status:"failed"`, `error:{stage, code, message}` where stage/code
  come from F58 or bounded parser stages and message is fixed PT-BR safe copy;
  `preview:null`. No raw exception, credentials, URL, CSV bytes, or path.
- Expiry: use existing `PREVIEW_TTL`/`settings.PREVIEW_TTL_SECONDS` as the
  bounded job/preview lifetime. A worker that outlives the deadline cannot
  publish a preview. Polling an owned expired job returns `200` with
  `status:"expired"`, `preview:null`; cleanup deletes any linked preview and
  all job files, then clears private path metadata. Expired terminal rows are
  pruned only after a separate bounded retention window, not during active
  polling.

This gives F60 a deterministic stop condition: only `succeeded` may hand off to
the review modal; `failed` and `expired` remain page/job errors and never open
the modal.

### 5. Preserve Família and mutation safety before any worker side effect

The start route resolves the active session row directly so Família is rejected
with existing `409 {"reason":"household_read_only"}` before credential
resolution, connector invocation, temp directory creation, or job scheduling.
Polling a Família session cannot access a real-profile job. Sync only creates an
`ImportPreview` and job metadata; it does not mutate `Asset`, `Position`, or
`AssetClass`. The existing manual review → explicit commit path remains the only
route that can trigger `snapshot_before_destructive` and
`record_mutation_audit`. F59 adds no bypass to `require_profile_writable` or
the production-DB guard.

### 6. Page error is server context; F60 owns presentation

`pages.py` adds the latest owned failed/expired job's safe status/error to the
patrimonio context. It does not start jobs, poll, or open `$store.importModal`.
F60 may render this context alongside its action. The API status contract is
the authoritative state for no-modal behavior, keeping F59 independent of UI
action markup.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/models.py::ImportPreview` / new `MyProfitSyncJob` | Import previews only; no sync lifecycle row | Add profile-scoped job state, preview link, sanitized error, timestamps, expiry, and private cleanup metadata | Pollable durable contract and page-safe error lookup |
| `alembic/versions/<new-head>_myprofit_sync_jobs.py` | No job table | Add/drop `myprofit_sync_jobs` schema and indexes | Persist lifecycle without editing old migrations |
| `src/omaha/routes/imports.py::preview_import` | Owns upload decode/parse/persist inline | Delegate to shared bytes→preview helper; add authenticated start/status routes and worker helpers | Manual and MyProfit previews share one response contract |
| `src/omaha/routes/imports.py::commit_import` | Explicit guarded manual commit | No behavior change; remains sole commit path | Preserve confirmation, snapshot, audit, and no auto-commit |
| `src/omaha/routes/pages.py::_common_context` | Page context has no sync error | Include latest safe owned sync status/error | Keep failed sync visible as page state without modal side effect |
| `src/omaha/main.py::create_app` | Quote service is only background app service | Initialize/inject sync service and bounded shutdown cleanup | Make worker lifecycle app-owned and test-injectable |
| `src/omaha/csv_import.py::parse_positions` | Pure parser consumed by manual upload | Reused unchanged by shared helper | Preserve broker totals, BR parsing, and parser boundary |
| `src/omaha/myprofit/connector.py` | F58 returns sanitized bytes/errors | No functional change; inject protocol into service | Keep connector handoff stable and F58-owned |
| `tests/test_imports_routes.py` + new `tests/test_myprofit_sync_jobs.py` | Manual preview/import tests only | Add internal job state/polling/expiry/concurrency/Família, synthetic CSV preview, page-error/no-modal, and no-mutation tests; do not invoke or double connector | Prove material F59 behavior without external service, connector behavior, or prod DB |
| `tests/conftest.py::_INTEGRATION_PREFIXES` | New job test path absent | Explicitly classify DB/TestClient job tests | Preserve allow-list marker rule |

## Risks / Trade-offs

- **SQLite concurrent writers** → cap workers at two, use independent short
  sessions, commit job state in small transactions, and let SQLite serialize
  writes; tests assert no lost status or preview rows.
- **Background task outlives request/app reload** → app-owned shutdown marks
  owned running jobs failed/expired safely, releases reservations, and removes
  only recorded job directories; no broad process or `/tmp` cleanup.
- **Stale preview or late worker completion** → check job expiry before and
  after connector/parse, link preview only for the same job/profile, and delete
  preview on expiry.
- **Secret/financial data leakage** → persist only sanitized stage/code and
  basename; never log credentials, raw connector exceptions, CSV bytes, or
  private paths in API responses. Focused tests use synthetic internal inputs
  and persisted normalized errors, never connector doubles.
- **Duplicate sync clicks** → atomic service reservation plus active-row check
  returns stable conflict instead of starting a second profile job.
- **F60 client drift** → success payload is exactly `_build_preview_response`;
  failure/expiry payload explicitly has `preview:null`, and contract tests pin
  both shapes.
- **Migration rollback** → downgrade drops only F59 job schema and never
  deletes assets, positions, or existing import previews outside a linked
  expired F59 job cleanup.

## Migration Plan

1. Add model and Alembic head migration; run focused migration/model tests on
   temporary databases only.
2. Add service state wiring, start/status routes, shared preview helper, and
   page-safe context. Keep existing manual upload/commit tests green.
3. Add focused internal coverage for both profiles, Família authorization,
   duplicate/concurrent state, terminal states, expiry/file cleanup, synthetic
   CSV preview handoff, page-safe errors/no-modal behavior, and mutation safety.
   Run focused taskipy commands and lint; connector behavior remains outside
   F59 tests.
4. Apply migration through normal app migration path in deployment. No seed,
   reset, import commit, or live MyProfit operation is part of rollout.
5. Rollback removes only the F59 service/routes/model/migration; existing manual
   import previews and portfolio rows remain untouched. Expired F59 job rows and
   private files are cleaned before downgrade.

## Open Questions

None blocking. F60 must consume the exact start/status contract here; any change
to endpoint names, status values, preview shape, or error semantics requires an
owner-approved scope update before Apply.
