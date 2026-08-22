## 1. Persist job identity and lifecycle

- [x] 1.1 `src/omaha/models.py::MyProfitSyncJob` and new Alembic head
  `alembic/versions/<new-head>_myprofit_sync_jobs.py`: add profile-scoped job
  row with unique id, `queued|running|succeeded|failed|expired` status,
  `preview_id`, sanitized filename/error stage/error code, private owned-file
  metadata, UTC timestamps, and expiry; add only required indexes/FKs and a
  reversible downgrade. Preserve `ImportPreview`, Asset, Position, and seed
  schemas. Acceptance: temporary DB upgrade creates job table and downgrade
  removes only F59 schema; no production DB command is run. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py::test_job_model_and_migration_round_trip`.
  Focused taskipy command: `uv run task test-one
  tests/test_myprofit_sync_jobs.py::test_job_model_and_migration_round_trip`.
  Independent oracle: temporary DB history/model inspection proves columns/FKs
  match design and `data/portfolio.db` mtime/content is unchanged.

- [x] 1.2 `src/omaha/models.py::MyProfitSyncJob` serialization/query helpers:
  expose only documented public status fields; keep path, credentials, raw
  exceptions, CSV bytes, and private filenames out of API serialization;
  preserve profile ownership checks and existing preview TTL semantics.
  Acceptance: serializer contains only stable documented keys and no synthetic
  secret, raw exception, absolute path, or CSV marker. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py::test_status_serializer_is_sanitized`.
  Focused taskipy command: `uv run task test-one
  tests/test_myprofit_sync_jobs.py::test_status_serializer_is_sanitized`.
  Independent oracle: JSON scan against credential/path/CSV sentinels plus
  direct inspection of `MyProfitSyncJob` fields.

## 2. Build bounded background execution

- [x] 2.1 `src/omaha/routes/imports.py::MyProfitSyncService` and
  `src/omaha/main.py::create_app`: add app-owned service wiring with one active
  reservation per real profile, global two-worker cap, BackgroundTasks handoff,
  independent `SessionLocal` worker sessions, and shutdown cleanup limited to
  owned futures/directories. Preserve quote-service startup/shutdown and
  TestClient compatibility; do not use direct `asyncio.create_task`.
  Acceptance: duplicate starts create one active job row; Italo and Ana retain
  separate reservations and can overlap; active workers never exceed two;
  shutdown releases owned reservations without killing foreign processes.
  Test file/scenario: `tests/test_myprofit_sync_jobs.py::test_duplicate_profile_start_is_rejected`,
  `::test_profiles_run_independently`, `::test_worker_cap_is_two`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: internal reservation/barrier counters and temporary DB
  rows prove exact active-job count, profile ownership, and cap; no connector
  object, browser, network, credential, or MyProfit call is created.

- [x] 2.2 `src/omaha/routes/imports.py::start_myprofit_sync` and
  `::get_myprofit_sync_status`: add authenticated start/poll endpoints with
  exact 202/200/404/409 contracts, active-profile ownership filtering, and
  stable lifecycle values. Preserve existing manual import routes and response
  shapes. Acceptance: start returns `202`; queued/running return
  `preview:null`; unknown/foreign jobs return 404; same-profile active
  duplicate returns 409 with original id. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py::test_start_returns_202`,
  `::test_poll_states`, `::test_foreign_job_is_404`,
  `::test_duplicate_profile_start_is_rejected`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: TestClient status/body assertions against pre-created
  internal job rows and scheduler state; no connector invocation or connector
  double.

- [x] 2.3 `src/omaha/routes/imports.py::run_myprofit_sync_job` and its internal
  failure/cleanup helpers: preserve the F58 connector seam and production
  mapping of normalized failures, create unique private job paths, sanitize
  basename/error fields, and release profile reservation in `finally`.
  Acceptance: an internally recorded bounded failure becomes `failed` with
  `preview:null`; success/failure cleanup removes only paths recorded as owned;
  raw exception, secret, and path never reach status/log response. Test
  file/scenario: `tests/test_myprofit_sync_jobs.py::test_job_failure_state_is_sanitized`,
  `::test_job_file_cleanup_success`, `::test_job_file_cleanup_failure`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: synthetic normalized error plus owned-path ledger proves
  state/error mapping and exact cleanup; test never invokes, fakes, mocks,
  launches, logs into, or downloads from the F58/MyProfit connector.

## 3. Reuse import preview and page error boundary

- [x] 3.1 `src/omaha/routes/imports.py::preview_from_blob` plus
  `::preview_import`: factor existing size/UTF-8/`parse_positions`/
  `ImportPreview`/`_build_preview_response` flow into one helper and call it
  from manual upload and sync worker. Preserve `RawPosition` totals,
  auto-match/suggested-class fields, profile isolation, and existing error
  statuses. Do not add `qty * price` fallback or HTTP self-calls. Acceptance:
  manual and sync previews have byte/key-compatible documented payloads, and
  malformed/empty/oversized/non-UTF-8 input creates no usable preview. Test
  file/scenario: `tests/test_import_preview.py::test_preview_response_shape`,
  `tests/test_myprofit_sync_jobs.py::test_success_reuses_existing_preview_shape`,
  `::test_invalid_csv_fails_before_preview`.
  Focused taskipy command: `uv run task test-file tests/test_import_preview.py`.
  Independent oracle: direct synthetic CSV bytes produce identical response
  key sets and preserve broker totals; no connector or commit route is called.

- [x] 3.2 `src/omaha/routes/imports.py::run_myprofit_sync_job` success path:
  persist preview under the job's active profile, return `succeeded` with
  `preview_id`, `auto_matched`, `unmatched`, and `asset_classes` under
  `preview`, and never call `commit_import`. Preserve manual class assignment,
  explicit confirmation, snapshot, and audit guards. Acceptance: synthetic
  valid CSV bytes yield review payload, unmatched rows still need assignment,
  and Asset/Position counts plus `db_mutations` stay unchanged. Test
  file/scenario: `tests/test_myprofit_sync_jobs.py::test_success_reuses_existing_preview_shape`,
  `::test_sync_does_not_commit_or_audit`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: temporary DB counts and mutation rows remain unchanged;
  direct internal helper path proves preview handoff without any connector
  object or invocation.

- [x] 3.3 `src/omaha/routes/pages.py::_common_context`,
  `::_render_patrimonio`, `::index`, and `::get_patrimonio`: expose only latest
  active-profile failed/expired job status and safe error as page context;
  preserve profile/Família view resolution and ensure GET never schedules a
  job, polls externally, or opens `$store.importModal`. Acceptance: failure
  context contains fixed PT-BR error and no secret/path; Família page has no
  real-profile job detail. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py::test_failed_sync_is_page_safe_error`,
  `::test_family_view_has_no_sync_leak`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: rendered response/context from persisted normalized job
  state contains safe status only, with zero scheduler/filesystem side effect.

## 4. Enforce Família, expiry, and cleanup contracts

- [x] 4.1 `src/omaha/routes/imports.py::start_myprofit_sync` and
  `::get_myprofit_sync_status`: reject Família before credential resolution,
  connector access, worker scheduling, file creation, or foreign-job lookup;
  preserve exact `409 {"reason":"household_read_only"}` semantics.
  Acceptance: start and poll under Família return stable read-only response,
  create no job row, schedule no worker, inspect no foreign job, and touch no
  path. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py::test_family_start_is_blocked_before_worker`,
  `::test_family_poll_is_blocked_before_foreign_lookup`.
  Focused taskipy command: `uv run task test-one
  tests/test_myprofit_sync_jobs.py::test_family_start_is_blocked_before_worker`.
  Independent oracle: ordered internal events prove sentinel check precedes
  scheduling, job lookup, and path access; no connector/browser/network spy or
  double is used.

- [x] 4.2 `src/omaha/routes/imports.py::expire_myprofit_sync_job` and cleanup
  helpers: use `settings.PREVIEW_TTL_SECONDS` for job/preview expiry; mark late
  jobs `expired`, return `preview:null`, delete linked preview and only owned
  temporary paths, and retain terminal row only for bounded status retention.
  Acceptance: clock-controlled transitions for queued/running/succeeded jobs
  remove linked preview/files, leave unrelated paths and production DB
  untouched, and prevent late publication. Test file/scenario:
  `tests/test_myprofit_sync_jobs.py::test_expiry_cleans_preview_and_files`,
  `::test_late_worker_cannot_publish_after_expiry`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: temporary DB/path inventory before/after plus status JSON;
  no broad `/tmp` traversal or delete.

## 5. Focused validation and scope proof

- [x] 5.1 `tests/test_myprofit_sync_jobs.py` and `tests/conftest.py` allow-list:
  add only internal fixtures/helpers for job state, temporary DB/path cleanup,
  synthetic CSV bytes, normalized errors, and profile authorization; explicitly
  classify any new DB/TestClient file. Preserve no production DB, no masked
  pass, no retry, and no marker drift. Acceptance: essential internal
  scenarios pass and collection emits no `UnknownTestPath`. Test files/scenarios:
  `tests/test_myprofit_sync_jobs.py`, `tests/test_imports_routes.py`,
  `tests/test_import_preview.py`, `tests/test_family_aggregate.py`.
  Focused taskipy command: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`.
  Independent oracle: temporary DB/path ownership is isolated, marker
  collection is allow-listed, and source contains no connector/Playwright test
  double or external-service setup.

- [x] 5.2 All F59 Python/model/migration changes: run minimal focused regression
  commands and lint; preserve F58 connector, external connector tests, and
  unrelated runner/harness work. Acceptance: these commands pass:
  `uv run task lint`, `uv run task test-file tests/test_myprofit_sync_jobs.py`,
  `uv run task test-file tests/test_import_preview.py`,
  `uv run task test-file tests/test_imports_routes.py`, and
  `uv run task test-file tests/test_family_aggregate.py`; changed-file audit
  contains only F59 mapped files/tests/migration/spec artifacts. Test files:
  commands above. Focused taskipy command: `uv run task lint`. Independent
  oracle: `git diff --check`, changed-file list, no `.env`, browser,
  financial, production-DB, seed, or external-service artifact.

- [x] 5.3 F59 proposal gate evidence: run exact-change OpenSpec validation and
  stable-spec validation after dossier revision; record command/result in the
  handoff. Acceptance: exact change and all delta specs validate; no unrelated
  files changed. Test file: N/A (artifact gate). Focused taskipy command: N/A;
  this proposal gate runs no product tests or runtime refresh. Independent
  oracle: `openspec status --change
  f59-executar-sincronizacao-background-e-entregar-preview --json`,
  `openspec validate f59-executar-sincronizacao-background-e-entregar-preview
  --type change --strict --json`, and `openspec validate --specs --strict
  --json`.

## Test strategy

- Minimal F59 focused plan covers only: job state/concurrency; expiry and
  owned-path cleanup; profile/Família authorization; direct synthetic CSV to
  existing preview handoff; normalized error-to-page/job state and no-modal /
  no-commit behavior; and DB-mutation safety where affected.
- Focused test files: `tests/test_myprofit_sync_jobs.py`,
  `tests/test_import_preview.py`, `tests/test_imports_routes.py`, and the
  directly affected `tests/test_family_aggregate.py` regression boundary.
- Explicit exclusions: no test exercises, fakes, mocks, launches, logs into,
  downloads from, or otherwise involves MyProfit/Playwright connector behavior;
  no browser, network, credentials, external service, or live connector setup.
  F58/T31 retain connector coverage.
- Explicit marker rule: new DB/TestClient file is added to
  `tests/conftest.py::_INTEGRATION_PREFIXES`; no pattern-based marker shortcut.
- Minimal focused commands: `uv run task test-file
  tests/test_myprofit_sync_jobs.py`, `uv run task test-file
  tests/test_import_preview.py`, `uv run task test-file
  tests/test_imports_routes.py`, `uv run task test-file
  tests/test_family_aggregate.py`, and `uv run task lint`.
- Existing repository quality rules remain active. Canonical `uv run task test`
  remains an Apply/Review delivery gate under current
  `maintenance-suspended` policy; Review records `NOT RUN —
  maintenance-suspended` when policy suspends it, never falsely green. This
  proposal gate runs no product tests and no `refresh-for-test`.

## Acceptance evidence

- Internal tests prove start/status contracts, all five lifecycle states,
  per-profile active-job rule, two-worker cap, and no foreign-profile detail
  without connector doubles.
- Synthetic internal inputs prove Família-first authorization,
  normalized failure sanitization, owned-path cleanup, expiry, page-safe error,
  no-modal/no-commit behavior, and existing preview key compatibility.
- Preview creation leaves Asset/Position and `db_mutations` unchanged before
  explicit existing commit; snapshot/audit guards remain owned by commit.
- Exact F59 OpenSpec and stable-spec validation are green; changed-file audit
  is F59-only; no production DB, browser, connector, or runtime refresh is
  touched during propose.

## Execution Evidence

### Proposal revision preflight

- Change: `f59-executar-sincronizacao-background-e-entregar-preview`.
- Owner amendment: lean internal-boundary validation only; connector/MyProfit/
  Playwright behavior excluded from F59 tests.
- Pre-existing worktree boundary: `openspec/roadmap.md` was already modified;
  unrelated prior changes include root agent/docs, config, F58 connector/config,
  test harness/support, seed fixtures, and visual baselines. This slice did not
  edit those files. The pre-existing untracked
  `openspec/changes/f59-executar-sincronizacao-background-e-entregar-preview/.env`
  file remains untouched.

### Validation evidence

- Initial exact-change validation before amendment: passed (`1/1`).
- Initial stable-spec validation before amendment: passed (`71/71`; existing
  INFO length advisories only).
- Final exact-change and stable-spec commands are required after this revision;
  results are reported at proposal handoff.

### Apply execution evidence

- Implementation pass completed against mapped F59 symbols only:
  `MyProfitSyncJob`, migration `0020_myprofit_sync_jobs`,
  `MyProfitSyncService`, `preview_from_blob`, sync start/status routes,
  page-safe context, app shutdown wiring, and the explicit integration
  allow-list entry for `tests/test_myprofit_sync_jobs.py`.
- Internal validation seam: `_process_downloaded_csv` receives synthetic
  filename/bytes and reuses `preview_from_blob`; no connector adapter,
  browser, network, credential, or external-service setup appears in the F59
  focused test module.
- `uv run task test-file tests/test_myprofit_sync_jobs.py` -> **15 passed**.
  Covers migration round-trip on temporary SQLite, sanitized status,
  202/scheduling, duplicate/profile isolation, two-worker semaphore, poll
  states/foreign 404, synthetic preview handoff/no mutation, invalid-input
  failure, owned cleanup, expiry/late worker, page-safe error, Família guard,
  and family context isolation.
- `uv run task test-file tests/test_import_preview.py` -> **12 passed**.
- `uv run task test-file tests/test_imports_routes.py` -> **12 passed**.
- `uv run task test-file tests/test_family_aggregate.py` -> **16 passed**.
- `uv run task lint` -> **passed** (prek hooks, Ruff, unit hook, secret/hygiene
  checks). Initial SIM102 finding in `imports.py` was fixed and lint rerun.
- `uv run openspec validate
  f59-executar-sincronizacao-background-e-entregar-preview --type change
  --strict --json` -> **1/1 passed**.
- `uv run openspec validate --specs --strict --json` -> **71/71 passed**;
  existing INFO length advisories only.
- `git diff --check` -> **passed**. No full suite, connector/browser test,
  seed/reset, production DB, auto-commit, or F60 surface was run.
- Initial focused test failures were test-only drift (duplicate fixture job
  IDs and attempted ORM serialization), not product failures; fixed tests,
  then reran to 15 passed. No tests were weakened, skipped, xfailed, retried,
  or deleted.

### Apply ownership ledger receipts

Each focused command registered its wrapper PID/PGID before launch. All listed
processes exited; cleanup was idempotent no-op after exit. Test-only SQLite and
`tmp_path` resources were created by current pytest fixtures, never pointed at
production, and were bounded to that run; no unrecorded path was deleted.

| resource_kind | resource_id | owner | owner_evidence | started_at / ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|
| process + process group | PID/PGID 69524 | F59 initial test-file apply | wrapper printed identity before command | 2026-08-22T02:51:24-03:00 / 02:51:30-03:00 | exited | owned-cleaned | focused test failed on test fixture drift | idempotent no-op; already exited |
| process + process group | PID/PGID 69611 | F59 remediation 1 apply | wrapper printed identity before command | 02:51:44-03:00 / 02:51:49-03:00 | exited | owned-cleaned | one sanitizer assertion exposed raw synthetic code | idempotent no-op; already exited |
| process + process group | PID/PGID 69721 | F59 remediation 2 apply | wrapper printed identity before command | 02:52:11-03:00 / 02:52:17-03:00 | exited | owned-cleaned | 15 focused tests passed | idempotent no-op; already exited |
| process + process group | PID/PGID 69799 | F59 import-preview validation | wrapper printed identity before command | 02:52:29-03:00 / 02:52:35-03:00 | exited | owned-cleaned | 12 focused tests passed | idempotent no-op; already exited |
| process + process group | PID/PGID 69870 | F59 imports-routes validation | wrapper printed identity before command | 02:52:41-03:00 / 02:52:48-03:00 | exited | owned-cleaned | 12 focused tests passed | idempotent no-op; already exited |
| process + process group | PID/PGID 69963 | F59 family validation | wrapper printed identity before command | 02:52:53-03:00 / 02:53:01-03:00 | exited | owned-cleaned | 16 focused tests passed | idempotent no-op; already exited |
| process + process group | PID/PGID 70066 | F59 initial lint | wrapper printed identity before command | 02:53:08-03:00 / 02:53:29-03:00 | exited | owned-cleaned | SIM102 only | idempotent no-op; already exited |
| process + process group | PID/PGID 71310 | F59 remediation 3 test-file | wrapper printed identity before command | 02:53:42-03:00 / 02:53:47-03:00 | exited | owned-cleaned | 15 focused tests passed after code fix | idempotent no-op; already exited |
| process + process group | PID/PGID 71386 | F59 remediation 3 lint | wrapper printed identity before command | 02:53:53-03:00 / 02:54:15-03:00 | exited | owned-cleaned | lint passed | idempotent no-op; already exited |
| process + process group | PID/PGID 72571 | F59 exact/stable spec validation | wrapper printed identity before command | 02:54:23-03:00 / 02:54:25-03:00 | exited | owned-cleaned | exact 1/1 and stable 71/71 passed | idempotent no-op; already exited |
| process + process group | PID/PGID 72802 | F59 final test-file receipt | wrapper printed identity before command | 02:55:48-03:00 / 02:55:53-03:00 | exited | owned-cleaned | 15 focused tests passed | idempotent no-op; already exited |
| test DB / temporary path | pytest-managed test-only resources per listed run | F59 apply / pytest fixture | fixture creates session DB and `tmp_path` under test-only boundary | each listed run / each listed run | absent after fixture cleanup | owned-cleaned | no production path or listener used | bounded fixture cleanup; no broad discovery/deletion |

### Apply scope boundary

- Owned changes: F59 runtime files, migration, focused test, marker allow-list,
  and F59 dossier evidence/design decisions.
- Pre-existing worktree changes not owned: `openspec/roadmap.md` and any
  unrelated root agent/docs/config, F58 connector/config, test harness/support,
  seed, or visual-baseline changes recorded by proposal preflight.
- No open implementation task remains.

### Runtime refresh receipt

- Refresh run `f59-refresh-20260822T025902-0300` used isolated test-only
  SQLite `/tmp/opencode/f59-refresh-20260822.db`; no production DB access and
  no destructive reset. `db-migrate`, `db-seed`, and CSV-path `upsert` populated
  isolated Italo/Ana data.
- Existing listener on canonical port 8000 was observed and preserved; no
  foreign process was adopted or killed. Isolated server used port 18000,
  bound `0.0.0.0`.
- URL: `http://192.168.1.4:18000` (LAN host from
  `bash scripts/print_lan_url.sh`, port isolated because 8000 was occupied).
- Healthz: `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- Isolated DB: **11 classes / 89 assets / 88 positions**.
- Dashboard seeded: `RF Dinâmica` count **5** in authenticated GET `/`.
- Server PID: **73357**, PGID **73357**; exact owned server terminated and
  verified absent. Exact owned DB/log/cookie/launcher paths cleaned.

Refresh ownership receipt:

| resource_kind | resource_id | owner | owner_evidence | started_at / ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|
| test DB resource | `/tmp/opencode/f59-refresh-20260822.db` | F59 refresh | exact absent path checked before migration; env registered before use | 02:59:02-03:00 / 03:00:00-03:00 | absent | owned-cleaned | migrations/seeding targeted exact temp DB | removed exact path; idempotent bounded cleanup |
| log | `/tmp/opencode/f59-refresh-20260822.log` | F59 refresh | launcher declared exact path before server start | 02:59:11-03:00 / 03:00:00-03:00 | absent | owned-cleaned | server log contained PID 73357 and health request | removed exact path |
| child process + process group | PID/PGID 73357 | F59 refresh | launcher printed PID/PGID before health use | 02:59:11-03:00 / 03:00:00-03:00 | exited | owned-cleaned | exact uvicorn command and port 18000 matched | SIGTERM exact owned PID; absent after bounded wait |
| port | 18000 | F59 refresh | launcher declared port before bind; `ss` matched PID 73357 | 02:59:11-03:00 / 03:00:00-03:00 | absent | owned-cleaned | listener identity matched current-run server | closed with exact owned process |
| temporary path | `/tmp/opencode/f59-refresh-cookie` | F59 refresh | exact absent path checked before curl | 02:59:23-03:00 / 03:00:00-03:00 | absent | owned-cleaned | curl session cookie only | removed exact path |
| port | 8000 | pre-existing/foreign unknown | listener observed before refresh; no owner proof for current run | preflight 02:58:xx / unchanged | active | foreign/unknown | `ss` showed 0.0.0.0:8000; no PID ownership evidence | preserved; no action |

## Review Findings

### Review R1

Scope audit: dossier/artifact completeness **pass** (13/13 tasks; proposal,
design, delta specs, and apply handoff read); job model/migration **finding**;
bounded execution/profile isolation **findings**; polling/error serialization
**finding**; expiry/cleanup/retention **finding**; preview reuse and manual
commit/snapshot/audit boundary **pass**; Família guard **pass**; page-safe
failure/no-modal contract **pass** within F59 server boundary; focused test
scope/no connector-browser-network-credential behavior **pass**; migration
rollback/diff hygiene/OpenSpec validation **pass**; canonical full-suite result
**not assessable by policy** (`maintenance-suspended`, explicitly non-blocking).
No scope-breach implementation file found. Pre-existing `openspec/roadmap.md`,
ignored/untracked `.env` noted in apply receipt, and unrelated host resources
were not adopted or modified.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**. Owner
policy receipt is in PRD §4.13 and apply dossier. Focused product evidence:
`uv run task test-file tests/test_myprofit_sync_jobs.py` -> **15 passed in
3.12s**; apply handoff records import preview 12, import routes 12, family
aggregate 16, total 55 passed. No connector/MyProfit/Playwright/browser,
network, credential, login, download, mock, or fake test was run. No F59 test
was deleted, skipped, xfailed, retried, or masked.

Preflight: ledger
`/tmp/opencode/f59-review-20260822-ledger.jsonl`; owner evidence recorded
before focused launch. Review-owned wrapper and exact focused-test resources
classified `owned-current-run`/`owned-cleaned`; declared canonical test DB/log
paths were `absent`. Pre-existing listeners `8000/tcp` and `5443/tcp`, and
foreign `4096/tcp` owned by host `opencode` PID 58503, were preserved. No
canonical suite or app server launched; therefore no isolated canonical-runner
launch was attempted and no baseline/allowlist exception was used.

Postflight: same ledger records focused pytest process exit, fixture-owned
temporary DB/path cleanup, and no child residue. Pre-existing/foreign ports
remain active and untouched. Ledger receipt path retained; no broad cleanup.

Runner isolation: canonical runner precondition **not exercised** because
owner-authorized maintenance suspension forbids launching `uv run task test`;
relevant observed listeners were classified and preserved, with no suite
resource created.

Verification: `uv run openspec validate
f59-executar-sincronizacao-background-e-entregar-preview --type change
--strict --json` -> **1/1 passed**; `uv run openspec validate --specs --strict
--json` -> **71/71 passed**, INFO-only length advisories. `git diff --check` ->
**passed**. Verdict: **CHANGES_REQUESTED**.

#### R1-F01 — Shutdown leaves profile reservations and permits stale lifecycle
Status: resolved in remediation 1
Severity: high
Requirement/task: `myprofit-sync-job` bounded execution; design Decision 2;
task 2.1 acceptance (shutdown releases owned reservations).
Evidence: `src/omaha/routes/imports.py:544-556` `shutdown()` sets
`_stopping`, removes `_owned_dirs`, but never clears `_reservations`, marks
queued/running rows terminal, or waits/coordinates active workers. At
`src/omaha/routes/imports.py:259-264`, a later `start()` resets `_stopping` to
false, so shutdown can leave stale reservation state and block or race a new
job.
Required change: make app-owned shutdown deterministically release/settle its
owned reservations and lifecycle rows, while retaining bounded, exact-path
cleanup; do not kill/adopt foreign processes or alter F58 connector behavior.
Excluded scope: no distributed queue, browser/connector changes, broad process
cleanup, or F60 UI.
Acceptance: internal lifecycle test starts owned queued/running work, invokes
shutdown, proves no stale reservation remains, owned job reaches documented
terminal safe state, exact owned paths are cleaned, and a subsequent start
cannot race prior work.

#### R1-F02 — Expired rows never receive bounded retention metadata or pruning
Status: resolved in remediation 1
Severity: high
Requirement/task: `myprofit-sync-job` job-files/previews expiry; design Decision
4; task 4.2.
Evidence: `src/omaha/routes/imports.py:474-501` sets `status="expired"` and
`finished_at`, but never sets `retention_until`; repository search finds
`retention_until` assigned only in `_mark_failed` and success path
(`imports.py:333,397`) and no expired-row pruning implementation. Thus expired
terminal rows are retained indefinitely, contradicting “bounded status
retention” and the separate retention-window contract.
Required change: set expiry retention deadline and add bounded, profile-safe
pruning after that deadline, limited to F59 terminal rows and without deleting
unrelated previews, portfolio rows, or production data.
Excluded scope: no global DB cleanup, seed/reset changes, or changes to manual
preview TTL semantics.
Acceptance: clock-controlled test expires queued/running/succeeded jobs,
asserts `retention_until`, confirms rows remain during retention, then confirms
only expired F59 rows past retention are pruned and unrelated rows/paths stay.

#### R1-F03 — Arbitrary persisted error stage can leak through status/page state
Status: resolved in remediation 1
Severity: high
Requirement/task: `myprofit-sync-job` sanitized lifecycle errors; task 1.2 and
2.3.
Evidence: `src/omaha/models.py:498-507` allowlists `error_code` but returns
`self.error_stage` verbatim. `src/omaha/routes/imports.py:443-455` persists
connector stage values and broad failures; `pages.py:203-207` then exposes that
stage in page context. A bounded-code guarantee without a bounded-stage
allowlist permits an injected/raw stage to reach API/page output, contrary to
stable stage/error sanitization.
Required change: normalize both stage and code at the serialization/persistence
boundary to explicit F58/parser allowlists, mapping unknown values to safe
fallbacks; retain fixed PT-BR messages and omit raw exception/path/secret data.
Do not expose diagnostic strings or alter connector contract.
Excluded scope: no connector test coverage, browser/network behavior, or F60
modal implementation.
Acceptance: synthetic jobs with secret/path/URL values in both stage and code
produce only allowlisted stage/code and fixed message in status and page
context; existing normalized stages remain unchanged.

#### R1-F04 — Connector failure after deadline is reported failed, not expired
Status: resolved in remediation 1
Severity: medium
Requirement/task: `myprofit-sync-job` expiry late-publication contract; task
2.3 and 4.2.
Evidence: `src/omaha/routes/imports.py:429-445` catches
`MyProfitConnectorError` and calls `_mark_failed()` without checking
`job.expires_at`. If connector operation returns an error after the deadline,
polling reports `failed`, while the contract requires an owned late job to be
`expired` with `preview:null`; current pre/post deadline checks only surround
CSV processing at `imports.py:358-380,388-393`.
Required change: classify deadline-expired connector completion/failure as
`expired`, perform linked-preview/path cleanup, and prevent any terminal
`failed` transition after expiry. Preserve sanitized failure mapping for
in-deadline connector errors.
Excluded scope: no connector implementation or external-service test; use
internal persisted-state/time-controlled evidence only.
Acceptance: internal boundary test simulates completion after expiry with a
normalized connector failure and asserts status `expired`, null preview,
cleanup, and no late publication; in-deadline failure remains `failed` with
 safe error payload.

### Review R1 remediation 1 evidence

- `R1-F01` resolved: `MyProfitSyncService.shutdown` now settles every current
  queued/running reservation as `expired`, assigns terminal retention metadata,
  deletes only exact owned directories, clears reservations, and allows a new
  profile start only against the settled lifecycle. `_mark_failed` and
  `_process_downloaded_csv` refresh persisted state before transitions, so a
  late worker cannot publish or replace that terminal state. Test:
  `test_shutdown_settles_owned_jobs_and_releases_reservations`.
- `R1-F02` resolved: expiry now sets `retention_until`; bounded
  `prune_expired_jobs(profile_id, now, limit=100)` deletes only F59 terminal
  rows past retention and any linked preview owned by the same profile. Start
  invokes profile-scoped pruning; retention-window and limit behavior plus an
  unrelated preview are covered by
  `test_expired_jobs_are_retained_then_pruned_with_bound`.
- `R1-F03` resolved: `MyProfitSyncJob` defines explicit F58/parser stage and
  code allowlists, normalizes worker persistence, and normalizes again at
  status serialization/page context. Unknown secret/path values fall back to
  `connector`/`failed` with fixed PT-BR copy in
  `test_error_stage_and_code_are_allowlisted`.
- `R1-F04` resolved: `_mark_failed` refreshes current lifecycle state and
  delegates deadline/terminal jobs to expiry, preventing connector failure
  from replacing `expired`; `test_late_connector_failure_keeps_expired_precedence`
  proves `expired`, null error, retention metadata, while existing in-window
  failure coverage remains green.

Changed remediation symbols: `src/omaha/routes/imports.py::MyProfitSyncService`
(`_mark_failed`, `_process_downloaded_csv`, `expire_myprofit_sync_job`,
`prune_expired_jobs`, `shutdown`, `_safe_error_message`),
`src/omaha/models.py::MyProfitSyncJob` error allowlists/normalization,
`src/omaha/routes/pages.py::_common_context`, and focused internal tests in
`tests/test_myprofit_sync_jobs.py`.

Focused validation:

- `uv run task test-file tests/test_myprofit_sync_jobs.py` → **19 passed**
  (remediation run 1 and rerun after stale-worker refresh guard).
- `uv run task test-file tests/test_import_preview.py` → **12 passed**;
  `uv run task test-file tests/test_imports_routes.py` → **12 passed**;
  `uv run task test-file tests/test_family_aggregate.py` → **16 passed**.
- `uv run task lint` → **passed** (prek, Ruff, unit hook, secret/hygiene
  checks).
- `uv run openspec validate
  f59-executar-sincronizacao-background-e-entregar-preview --type change
  --strict --json` → **1/1 passed**.
- `uv run openspec validate --specs --strict --json` → **71/71 passed**;
  existing INFO-only length advisories unchanged.
- `git diff --check` → **passed**.

Runtime refresh receipt:

- Isolated test-only SQLite `/tmp/opencode/f59-r1-refresh-20260822.db` was
  migrated and populated through `uv run task db-migrate`, `uv run task
  db-seed`, and non-destructive `uv run task db-seed-upsert` for Italo/Ana;
  no production DB and no destructive reset. Read-only count: Italo 6
  classes, 46 assets, 46 positions.
- Isolated server bound `0.0.0.0:18001`; LAN base from
  `bash scripts/print_lan_url.sh` was `http://192.168.1.4:8000`, adjusted only
  to isolated port `http://192.168.1.4:18001`. `/healthz` returned `status=ok`,
  `db=ok`; authenticated dashboard smoke found `RF Dinâmica` 3 times.
- Exact current-run server wrapper PID/PGID `77272`, uvicorn child `77279`,
  port `18001`, log, DB, launcher, and cookie paths were bounded-cleaned and
  verified absent. Pre-existing canonical listener `8000` remained untouched.

Ownership ledger receipts for remediation 1:

| resource_kind | resource_id | owner | owner_evidence | started_at / ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|
| process + process group | PID/PGID 75406 | F59 remediation 1 apply | wrapper identity printed before focused launch | 2026-08-22T06:10:21Z / 06:10:26Z | exited | owned-cleaned | 19 focused tests passed | idempotent no-op after exit |
| process + process group | PID/PGID 75578 | F59 remediation 1 apply | wrapper identity printed before focused launch | 2026-08-22T06:11:07Z / 06:11:13Z | exited | owned-cleaned | 19 focused tests passed after stale-state guard | idempotent no-op after exit |
| process + process group | PID/PGID 75634 | F59 remediation 1 apply | wrapper identity printed before lint launch | 2026-08-22T06:11:20Z / 06:11:42Z | exited | owned-cleaned | lint passed | idempotent no-op after exit |
| process + process group | PID/PGID 76788 | F59 remediation 1 apply | wrapper identity printed before related focused launches | 2026-08-22T06:11:55Z / 06:12:15Z | exited | owned-cleaned | 12 + 12 + 16 tests passed | idempotent no-op after exit |
| process + process group | PID/PGID 76967 | F59 remediation 1 apply | wrapper identity printed before artifact validation | 2026-08-22T06:12:23Z / 06:12:25Z | exited | owned-cleaned | exact 1/1, stable 71/71, diff check passed | idempotent no-op after exit |
| test DB | `/tmp/opencode/f59-r1-refresh-20260822.db` | F59 remediation 1 refresh | exact path registered before migration | 2026-08-22T06:13:09Z / 06:14:44Z | absent | owned-cleaned | isolated migration/seed/count smoke only | exact DB/WAL/SHM paths removed; idempotent absence verified |
| child process + process group | PID/PGID 77272; child 77279 | F59 remediation 1 refresh | exact launcher identity recorded before health checks; port matched child | 2026-08-22T06:13:30Z / 06:14:44Z | exited | owned-cleaned | healthz and dashboard smoke passed on port 18001 | exact owned group SIGTERM; absent after bounded wait |
| port | `18001/tcp` | F59 remediation 1 refresh | exact port preflight absent before bind; `ss` matched PID 77279 | 2026-08-22T06:13:30Z / 06:14:44Z | absent | owned-cleaned | isolated uvicorn listener only | closed with exact owned process group |
| log | `/tmp/opencode/f59-r1-refresh-20260822.log` | F59 remediation 1 refresh | launcher declared exact path before start | 2026-08-22T06:13:30Z / 06:14:44Z | absent | owned-cleaned | log contained exact uvicorn child and health request | exact path removed |
| temporary path | `/tmp/opencode/f59-r1-refresh-cookie-20260822`, `/tmp/opencode/f59-r1-refresh-cookie-20260822b`, launcher path | F59 remediation 1 refresh | each exact path checked/declared before use | 2026-08-22T06:14:03Z / 06:14:44Z | absent | owned-cleaned | first smoke attempt bounded failure; second dashboard smoke passed | exact paths removed; idempotent absence verified |

No foreign process, listener, production DB, or unrelated path was adopted,
killed, or deleted. Canonical full suite was not launched under the existing
`maintenance-suspended` policy; no baseline or allowlist exception was used.

### Review R2
Scope audit: exact change/dossier **pass** (`openspec status` complete; proposal,
design, tasks, three delta specs, apply handoff, and R1 evidence re-read);
requirements/scenarios **pass**; R1 remediation symbols and changed files
**pass**; model/migration/FK/index/rollback **pass**; lifecycle, shutdown
settlement, reservation release, concurrency, and profile isolation **pass**;
preview/parser/no-commit/mutation guards **pass**; expiry, cleanup, retention,
and bounded pruning **pass**; stage/code sanitization and expiry precedence
**pass**; Família authorization/page-safe state **pass**; focused-test scope
and no-test-deletion evidence **pass**; diff/scope hygiene **pass**; exact and
stable spec validation **pass**; canonical full-suite enforcement **not
assessable by policy, non-blocking under owner-authorized
`maintenance-suspended`**.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**. No
canonical lane was launched. Focused product evidence: remediation receipt
retains 19 job tests + 12 preview + 12 imports routes + 16 family aggregate =
59 passed; R2 rerun `uv run task test-file tests/test_myprofit_sync_jobs.py` ->
**19 passed**, pytest 3.18s, external wall-clock 5.601s, rc=0. Excluded
MyProfit/Playwright/browser/network/credential/login/download/connector
mock/fake tests were not run. No F59 test was deleted, skipped, xfailed,
retried, or masked.

Preflight: inspected per-run ledger
`/tmp/opencode/f59-review-20260822-ledger.jsonl`; prior declared process,
listener, test-DB, log, and temporary-path records contain owner/evidence,
timestamps, status, classification, and cleanup results. Relevant residue:
canonical test DB/log paths **absent**; ports `8000/tcp` and `5443/tcp`
**pre-existing** and preserved; `4096/tcp` **foreign** and preserved. R2
focused pytest process/test DB and temporary paths were current-run owned and
exited/fixture-cleaned (no child residue). No production DB or server was
launched. Suspension means canonical isolated-runner precondition was not
exercised; no baseline or allowlist exception was used.

Postflight: focused process exited rc=0; pytest-owned DB/temp resources were
fixture-cleaned; pre-existing/foreign listeners remained untouched. No broad
cleanup occurred. Canonical suite has no postflight because policy forbade
launch.

Runner isolation: **not exercised for canonical suite by maintenance policy**;
focused run used test-only fixture resources and preserved all foreign or
pre-existing resources.

Acceptance evidence: R1-F01 shutdown test proves queued/running settlement to
`expired`, retention metadata, exact owned-path cleanup, reservation clearing,
and replacement start. R1-F02 proves retention-window preservation, profile
scoping, and `limit=1` pruning without unrelated preview deletion. R1-F03
proves stage/code allowlist fallback and fixed PT-BR message in status/page
state. R1-F04 proves late connector failure cannot replace `expired`; late
preview publication remains blocked. R2 focused rerun preserves all 19 tests.
OpenSpec exact validation `1/1`, stable specs `71/71`, lint, and
`git diff --check` remain green from remediation evidence.

Changed files audited: `src/omaha/main.py`, `src/omaha/models.py`,
`src/omaha/routes/imports.py`, `src/omaha/routes/pages.py`,
`alembic/versions/0020_myprofit_sync_jobs.py`, `tests/conftest.py`,
`tests/test_myprofit_sync_jobs.py`, and F59 `proposal.md`, `design.md`,
`tasks.md`, and three delta specs. Pre-existing `openspec/roadmap.md` and
unrelated worktree resources remain outside F59 ownership.

Verdict: **APPROVED**

New findings: **none**. No stable R2 finding ID issued. All four prior findings
are resolved; owner validation may proceed. Canonical suite remains
policy-suspended and is not represented as green.
