## 1. Telemetry boundary

- [x] 1.1 **Target:** new `src/omaha/myprofit/telemetry.py`, recorder/context and allowlists. **Change:** add context-local recorder keyed only by UUID-shaped `job_id`; emit fixed `myprofit_telemetry` events through existing `omaha` logger for `transition`, `stage`, `terminal`, and `ui_limit`; normalize event/domain/status/stage/code and clamp/reject non-finite or negative durations. **Preserve:** standard-library logger identity, JSON/text envelope, no exception propagation into job flow, no credentials/CSV/URL/path/filename. **Acceptance:** event messages have finite bounded fields, fixed `na` for irrelevant values, no arbitrary labels, and one job remains one run. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_telemetry_event_shape_and_sanitization` (new named scenario) with malicious stage/code/path/exception-like values. **Focused command:** `uv run task test-integration -- -k telemetry_event_shape_and_sanitization`. **Independent oracle:** parse captured `caplog` messages and assert exact allowlist, numeric bounds, same `job_id`, and forbidden-value absence.
- [x] 1.2 **Target:** `src/omaha/routes/imports.py`, `MyProfitSyncService.start`, `run_myprofit_sync_job`, `_mark_failed`, `_process_downloaded_csv`, `expire_myprofit_sync_job`, `status_for_profile`. **Change:** open recorder per job; collect queued/running/terminal transitions, preview/handoff and expiry stages, total duration, and best-effort log failures without changing return/status/cleanup behavior. **Preserve:** profile isolation, worker cap, expiry precedence, preview-only handoff, explicit commit boundary, existing sanitized API payload. **Acceptance:** success/failure/expired jobs each produce one terminal event and reconciled transitions/durations; no portfolio tables change. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py` success, connector failure, parser failure, late expiry, and no-mutation cases. **Focused command:** `uv run task test-integration -- -k "myprofit_sync_jobs or telemetry"`. **Independent oracle:** existing job row/status/preview/cleanup assertions plus captured event counts and `Asset`/`Position`/`DbMutation` before/after equality.
- [x] 1.3 **Target:** `src/omaha/routes/imports.py`, new authenticated observation route adjacent to `get_myprofit_sync_status`. **Change:** accept only fixed UI-limit notification for `{job_id}`, resolve active profile, validate job ownership, emit bounded `polling_ui` telemetry, and reject/ignore foreign/missing/repeated observations without DB mutation. **Preserve:** existing GET polling status, 404/409 boundaries, auth and Família guards, no free-form request body. **Acceptance:** owned signal logs one fixed event; foreign/missing signal is non-mutating and does not disclose job data. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py::test_ui_limit_signal_is_owned_and_non_mutating`. **Focused command:** `uv run task test-integration -- -k ui_limit_signal`. **Independent oracle:** TestClient status code/body, `caplog`, and DB row-count/status snapshot.

## 2. Connector and browser collection

- [x] 2.1 **Target:** `src/omaha/myprofit/connector.py`, `PlaywrightMyProfitConnector._download_from_page` and cleanup in `download_positions_csv`. **Change:** instrument existing navigation, login, 2FA, export, CSV-option, download, and cleanup boundaries through active recorder context with integer non-negative stage durations and sanitized failure code; do not log exception object or browser data. **Preserve:** exact external URLs/selectors, per-stage timeout values, fake/offline connector contract, cleanup and error precedence. **Acceptance:** fake connector tests see stage events for success and failure; timeout settings and connector error stage/code remain byte-for-byte behaviorally equivalent. **Test file/scenario:** existing `tests/test_myprofit_connector.py` fake browser success/timeout/cleanup scenarios plus backend telemetry capture. **Focused command:** `uv run task test-unit -- -k "myprofit_connector or telemetry"` and `uv run task test-integration -- -k telemetry`. **Independent oracle:** fake page call order, `MyProfitConnectorError(stage, code)`, temporary-artifact cleanup, and forbidden-token scan of all captured messages.

## 3. UI local-limit signal

- [x] 3.1 **Target:** `src/omaha/templates/_patrimonio_add_asset_modal.html`, `Alpine.store('patrimonioSync')` fields/methods `init`, `start`, `schedulePoll`, `poll`, `setError`. **Change:** add per-run one-shot guard and fixed keepalive signal when existing `pollCount >= maxPolls` branch fires, then retain current safe timeout message, state, and no-more-poll behavior. **Preserve:** `pollDelay = 500`, `maxPolls = 120`, request token cancellation, queued/running polling, success preview handoff, failed/expired notification, manual commit. **Acceptance:** local harness records exactly one signal at limit and zero signals on success; no extra poll or commit request occurs. **Test file/scenario:** `tests/e2e/test_patrimonio_sync_action.py` local intercepted store scenarios for success, failed/expired, bounded polling, and local limit. **Focused command:** `uv run task test-e2e -- -k "patrimonio_sync_action"`. **Independent oracle:** intercepted request list, store `state/pollCount`, notification text, modal visibility, and absence of `/api/import/commit` before explicit action.
- [x] 3.2 **Target:** `src/omaha/templates/_patrimonio_actions.html`, root action state and notification rendering. **Change:** verify/retain existing `data-sync-state`, button disabled/`aria-busy`, and safe notification attributes; change markup only if needed to expose existing observation boundary, with no new copy. **Preserve:** Família disabled surface, accessibility roles/live regions, focus/reset behavior, Import CSV and review controls. **Acceptance:** template remains compatible with store event path and all existing state markers render unchanged. **Test file/scenario:** `tests/e2e/test_patrimonio_sync_action.py::test_state_markers_render` and local notification lifecycle. **Focused command:** `uv run task test-e2e -- -k "state_markers_render or patrimonio_sync_action"`. **Independent oracle:** exact `data-testid`, `data-sync-state`, `aria-busy`, role/live attributes, and git diff allow-list.

## 4. Runbook and stable boundaries

- [x] 4.1 **Target:** new `docs/runbooks/myprofit-sync-telemetry.md`. **Change:** document stdout collection (no app storage), minimum four-week window, extension to eight weeks when volume/evidence is insufficient, target 4–8 real runs/week, bounded grouping by `domain/stage/code`, counts/rates/percentiles, missing/invalid event handling, and diagnosis thresholds. **Preserve:** no SLA, timeout, retry, external-service, F68, T36, or infrastructure claim. **Acceptance:** runbook gives executable commands/filters in terms of retained log lines, distinguishes connector/browser, polling/UI, preview/handoff, concurrency, and states `insufficient-evidence` when retention is absent. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py` runbook contract test or repository docs assertion covering required headings/tokens. **Focused command:** `uv run task test-integration -- -k myprofit_telemetry_runbook`. **Independent oracle:** read runbook text and assert required window, dimensions, thresholds, forbidden-scope terms, and no secret/URL examples.
- [x] 4.2 **Target:** `src/omaha/models.py` (`MyProfitSyncJob`), `src/omaha/config.py`, `src/omaha/logging_config.py`. **Change:** verify implementation reuses `normalize_error`, timestamps, existing `LOG_LEVEL`/`LOG_FORMAT`, and stdout formatter without model columns, migration, telemetry setting, timeout, or retention daemon. **Preserve:** stable status serializer, one-hour product job retention, JSON seven-key envelope, production/test DB boundaries. **Acceptance:** no schema/config/logging contract drift is needed for T38. **Test file/scenario:** `tests/test_myprofit_sync_jobs.py` serializer/retention tests and `tests/test_logging.py` JSON formatter tests. **Focused command:** `uv run task test-integration -- -k "status_serializer or expired_jobs"` and `uv run task test-unit -- -k logging`. **Independent oracle:** `alembic` migration inventory unchanged, exact serializer payload assertions, formatter parseability, and no telemetry table/file created.

## 5. Focused verification and acceptance evidence

- [x] 5.1 **Target:** changed-file boundary for exact T38 dossier plus listed runtime/tests/docs files. **Change:** run lint and inspect diff for only intended telemetry/runbook files; do not edit roadmap, stable specs, config, T36 archive, F68, T37, F67, D06, `.env`, or financial/browser artifacts. **Preserve:** all unrelated worktree changes, especially pre-existing `openspec/roadmap.md` modification. **Acceptance:** lint passes; no forbidden files or secrets changed; no DB mutation command, live connector, external URL, or browser-service access is used. **Test file/scenario:** no product scenario; changed-file allow-list and forbidden-token scan. **Focused command:** `uv run task lint`. **Independent oracle:** `rtk git status --short --untracked-files=all`, `rtk git diff --check`, and exact path allow-list.
- [x] 5.2 **Target:** T38 acceptance across `tests/test_myprofit_sync_jobs.py`, `tests/test_myprofit_connector.py`, `tests/e2e/test_patrimonio_sync_action.py`, runbook, and delta spec. **Change:** execute focused backend, connector, browser, docs/spec validation and record results in this `tasks.md`; do not run full canonical suite during proposal/apply planning unless lifecycle owner later requires it. **Preserve:** no skip/xfail/retry/masked failure, no persistent DB write. **Acceptance:** all focused scenarios green; evidence demonstrates success/failure/concurrency/polling/UI-limit coverage, bounded/sanitized fields, retained-source/insufficient-evidence rule, and zero timeout/retry/F68 change. **Test file/scenario:** all scenarios named in 1.1–4.2. **Focused command:** `uv run task test-integration -- -k "myprofit_sync_jobs or telemetry"`; `uv run task test-unit -- -k "myprofit_connector or logging"`; `uv run task test-e2e -- -k patrimonio_sync_action`; `uv run task lint`. **Independent oracle:** `openspec validate t38-telemetria-minima-e-runbook-de-analise-myprofit --type change --no-interactive`, `git diff --check`, focused command exit codes, and reviewer comparison against `design.md`/delta spec.

## Test Strategy

- Backend lifecycle and sanitization: integration tests in
  `tests/test_myprofit_sync_jobs.py`, using existing temporary DB fixtures and
  `caplog`; no `data/portfolio.db` mutation.
- Connector stage coverage: existing offline fake-browser tests in
  `tests/test_myprofit_connector.py`; no credentials, Playwright launch, or
  network access.
- UI/polling: local intercepted Playwright harness in
  `tests/e2e/test_patrimonio_sync_action.py`; assert request choreography and
  rendered safe state, not external service behavior.
- Documentation/spec health: required-token assertions plus OpenSpec
  validation; no stable spec synchronization in this gate.
- Canonical full suite: record `NOT RUN — maintenance-suspended` during
  Apply/Review per repository policy; focused lanes remain mandatory.

## Acceptance Evidence Required Before READY_FOR_REVIEW

Record in this file, after implementation only:

1. Exact changed-file list and clean `git diff --check` for owned files.
2. Focused command, timestamp, exit code, and test count for each applicable
   taskipy lane.
3. Captured event examples proving same `job_id`, finite durations,
   transition/stage/terminal/UI-limit coverage, and forbidden-value absence.
4. Success, connector/preview failure, expiry/late result, concurrent-profile,
   duplicate-start, polling, and UI local-limit oracle results.
5. Runbook/spec validation result and explicit statement that no timeout,
   retry, external service, DB schema, F68, T36, or stable spec changed.

## Execution Evidence

### Apply initial — 2026-08-24

Changed files owned by T38:

- `src/omaha/myprofit/telemetry.py`
- `src/omaha/routes/imports.py`
- `src/omaha/myprofit/connector.py`
- `src/omaha/templates/_patrimonio_add_asset_modal.html`
- `tests/test_myprofit_sync_jobs.py`
- `tests/test_myprofit_connector.py`
- `tests/e2e/test_patrimonio_sync_action.py`
- `docs/runbooks/myprofit-sync-telemetry.md`
- this change's `design.md` and `tasks.md`

Preserved pre-existing `openspec/roadmap.md` modification. No changes to
`_patrimonio_actions.html`, models, config, logging config, migrations, stable
specs, F68, T36, T37, F67, D06, `.env`, financial data, or visual artifacts.

Focused validation receipts:

| Command | Result |
|---|---|
| `uv run task test-integration -- -k "myprofit_sync_jobs or telemetry"` | 23 passed, 1128 deselected; exit 0 |
| `uv run task test-unit -- -k "myprofit_connector or telemetry"` | 32 passed, 1108 deselected; exit 0 |
| `uv run task test-integration -- -k "status_serializer or expired_jobs"` | 2 passed, 1149 deselected; exit 0 |
| `uv run task test-unit -- -k logging` | 5 passed, 1135 deselected; exit 0 |
| `uv run task test-e2e -- -k "patrimonio_sync_action"` | 10 passed, 55 deselected; exit 0 |
| `uv run task lint` | all hooks passed; exit 0 |
| `openspec validate t38-telemetria-minima-e-runbook-de-analise-myprofit --type change --no-interactive` | valid; exit 0 |
| `git diff --check` | clean; exit 0 |

Final post-edit smoke: `uv run task test-integration -- -k "telemetry_event_shape_and_sanitization or ui_limit_signal or myprofit_telemetry_runbook"` → 3 passed, 1148 deselected; exit 0. Final
`uv run task lint`, strict change validation, and `git diff --check` remained
green after this smoke.

Acceptance evidence: telemetry tests captured four events with one identical
UUID-shaped `job_id`, allowlisted dimensions, finite integer durations/fixed
`na`, and no secret/path/URL/exception-like token. Lifecycle tests cover
success, connector/parser failure, expiry/late result, duplicate start,
concurrent profiles, preview no-mutation, and one owned/non-mutating UI signal.
Connector fake-browser tests cover navigation, login, 2FA, export, CSV option,
download, cleanup, success, and timeout failure. Browser local-limit test shows
one `/ui-limit` request, no extra poll, no commit request, and existing error
state. Runbook contract passes required retention/grouping/threshold and
forbidden-scope assertions.

No canonical full suite was run: `NOT RUN — maintenance-suspended`.
No timeout, retry, external service, DB schema, F68, T36, or stable spec
changed. No DB mutation command or live connector was used by focused tests.

### Ownership ledger receipts

Validation runs created test child/process-group resources and browser/e2e
temporary artifacts. Current-run e2e visual artifact paths were exact known
outputs and restored to their pre-existing tracked bytes after each run. No
foreign process, listener, production DB, or unrecorded path was cleaned.

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-apply-focused-20260824` | child process | taskipy pytest children (PIDs varied per command) | T38 apply agent | exact taskipy command recorded above; pre-launch PID registration was not captured | command start/end in shell receipt | command exit | exited | owned-current-run | focused lanes exited 0 | fixtures completed bounded cleanup; no residue observed |
| `T38-apply-e2e-20260824` | temporary path | exact `tests/visual/artifacts/f60-atualizar-posicao-{error,family,loading,patrimonio}.png` | T38 apply agent | e2e command and exact output paths | e2e command start | cleanup attempt after each run | cleanup-attempted | owned-cleaned | only known test outputs changed | exact tracked bytes restored; no other visual files touched |
| `T38-preflight-8000-20260824` | process group / listener / port / log | PGID 121691 / PID 121695 / 8000 / `/tmp/omaha-uvicorn.log` | pre-existing Omaha process, not T38 | exact command, cwd `/home/juca/github/omaha`, user `juca`; pre-existing identity | `2026-08-24 11:57:47 -0300` | not ended | active | pre-existing | healthz reachable; current run did not launch it | preserved untouched; no kill/adoption |

### Refresh-for-test receipt

Mandatory refresh preflight reached existing server and read-only checks, but
restart was not performed: PID 121695/PGID 121691 and port 8000 predate this
apply run. Exact command/cwd identify Omaha, but protocol does not permit
adopting or terminating pre-existing resources. Therefore no claim is made
that current runtime bytes were loaded.

`bash scripts/print_lan_url.sh` → `http://192.168.1.8:8000`
`curl -fsS --max-time 5 "$URL/healthz"` → `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`
DB read-only verification: `11 classes / 89 assets / 88 positions` (existing
owner state; no DB task ran).
Dashboard read-only check: HTTP 200, `RF Din` count 5.
Server: pre-existing PID 121695 preserved.
Refresh result: `BLOCKED_FOR_IMPLEMENTATION_BRIEF` — owner decision required
to restart exact pre-existing Omaha listener or provide isolated delivery
runner. This blocks READY_FOR_REVIEW handoff under current ownership policy.

### Resume refresh registration — 2026-08-24

Owner explicitly authorized exact restart of PID `121695`, PGID `121691`,
listener port `8000`. Current run owns only these exact identities for bounded
restart/reconciliation plus new child/log resources created by refresh. No
other PID, PGID, port, process, or path is a target.

Registered before resource use:

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| process group | PGID `121691` / child PID `121695` | T38 resume apply | owner authorization in current handoff; exact prior receipt identity | 2026-08-24T16:49:14-03:00 | 2026-08-24T16:49:45-03:00 | exited | owned-cleaned | exact command/cwd/listener revalidated; TERM returned 0; exact group absent | bounded TERM only to exact PGID; no other process target |
| port | `8000` old listener | T38 resume apply | owner authorization for exact Omaha listener | 2026-08-24T16:49:14-03:00 | 2026-08-24T16:49:45-03:00 | absent | owned-cleaned | exact old listener absent after TERM | bounded release/rebind only |
| log | `/tmp/omaha-t38-refresh-20260824.log` | T38 resume apply | exact new path, verified absent before launch | 2026-08-24T16:50:06-03:00 | active | active | owned-current-run | refresh launch output; new PID `159577`, child `159581` | preserve while server active; no broad cleanup |
| process group | PGID `159577` / child PID `159581` | T38 resume apply | exact `setsid` launch command; cwd `/home/juca/github/omaha`; owner `juca` | 2026-08-24T16:50:06-03:00 | active | active | owned-current-run | exact current command and listener PID `159581`; startup log confirms ready | preserve as delivery listener; bounded cleanup only on authorized follow-up |
| port | `8000` new listener | T38 resume apply | exact refresh launch and listener inspection | 2026-08-24T16:50:07-03:00 | active | active | owned-current-run | `0.0.0.0:8000` owned by PID `159581`, PGID `159577` | preserve as delivery listener |
| temporary path | `/tmp/omaha-t38-healthz-20260824.txt` | T38 resume apply | exact refresh health command redirected curl output to path | 2026-08-24T16:50:18.960442581-03:00 | 2026-08-24T16:51:24-03:00 | absent | owned-cleaned | created by exact current-run health command; post-cleanup path absent | exact bounded removal succeeded |
| temporary path | `/tmp/omaha-t38-healthz-20260824.err` | T38 resume apply | exact refresh health command redirected curl stderr to path | 2026-08-24T16:50:18.948442581-03:00 | 2026-08-24T16:51:24-03:00 | absent | owned-cleaned | created by exact current-run health command; post-cleanup path absent | exact bounded removal succeeded |

### Final refresh-for-test receipt — 2026-08-24

Owner authorized exact listener restart: old PID `121695`, PGID `121691`, port
`8000`. Pre-restart inspection matched exact command
`uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`, cwd
`/home/juca/github/omaha`, user `juca`, and listener PID `121695`. Sent
`kill -TERM -- -121691` only; exit status 0. After bounded wait, old PGID/PIDs
and port listener were absent.

Fresh launch used only:
`setsid bash -c 'exec uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000'`
with exact owned log `/tmp/omaha-t38-refresh-20260824.log`.

- LAN URL: `bash scripts/print_lan_url.sh` → `http://192.168.1.8:8000`.
- Health: `GET /healthz` → HTTP 200,
  `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
- Readiness: log confirms application startup complete and Uvicorn on
  `0.0.0.0:8000`.
- New ownership: launcher PID/PGID `159577`; listener child PID `159581`,
  PGID `159577`; `0.0.0.0:8000` maps exactly to PID `159581`.
- Runtime bytes: authenticated `GET /patrimonio` → HTTP 200; page contains
  `reportUiLimit`, `/ui-limit`, and `data-sync-state`. Missing authenticated
  job status returns expected 404.
- DB read-only state: `11 classes / 89 assets / 88 positions`; no DB task ran.
- Dashboard read-only check: HTTP 200, `RF Din` count 5.
- Reconciliation: exact old process group exited; exact healthz temporary files
  were removed and verified absent. New server/log remain active delivery
  resources. No broad cleanup ran.
- No foreign process, listener, test DB, or resource was adopted or killed.
  No process other than authorized PGID `121691` was targeted.

Final refresh result: `READY_FOR_REVIEW`. Canonical full suite remains
`NOT RUN — maintenance-suspended`.

## Review Findings

### Review R1
Scope audit: proposal, design, delta requirements/scenarios, all 10 tasks,
changed runtime symbols, connector/browser boundaries, UI polling and preview
handoff, stable MyProfit job/connector/import contracts, runbook, sanitization,
cardinality, no-mutation behavior, test markers, scope allow-list, and PRD
§4.1–§4.14: pass except bounded terminal deduplication and best-effort
exception handling, recorded below as findings. No area is not assessable.

Full suite: `uv run task test` -> `NOT RUN — maintenance-suspended`; no
canonical elapsed duration, six-lane result, coverage/skips, fail-fast, or
`<=300s` classification applies. Focused evidence remains green: 23
integration, 32 connector unit, 10 E2E, 7 logging/status; lint, OpenSpec
validation, and diff-check green.

Preflight: per-run ledger in this file inspected. Exact delivery resources
were owner-authorized and classified `owned-current-run`: process group
PGID `159577` / listener PID `159581`, port `8000`, log
`/tmp/omaha-t38-refresh-20260824.log`. Old PGID `121691` / PID `121695` was
classified `owned-cleaned`; exact health temp paths were `owned-cleaned` and
absent. No canonical test process, test DB, or declared test-temp path was
launched by this review; no foreign or unknown relevant resource observed.
Product DB remained protected. Decision: runner isolation sufficient for
focused audit; canonical launch prohibited by maintenance suspension.

Postflight: no review test process or lane resource existed. Delivery listener
and log remain active `owned-current-run` resources by explicit handoff and were
preserved. Exact health temp paths remain absent. No cleanup was performed and
no foreign resource was adopted, killed, deleted, or masked.

Runner isolation: relevant process/listener state had trusted owner evidence;
no canonical runner resource was started. No baseline or allowlist exception
used.

Verification: `openspec validate t38-telemetria-minima-e-runbook-de-analise-myprofit --type change --no-interactive` -> valid, exit 0. `git diff --check` -> clean, exit 0. Changed-file audit passes: T38 runtime/test/runbook files only, with pre-existing `openspec/roadmap.md` preserved; no stable spec, model, config, migration, F68, T36, T37, F67, D06, `.env`, financial data, external-service call, DB mutation command, test deletion, skip, xfail, retry, or coverage reduction.

Verdict: CHANGES_REQUESTED

#### R1-F01 — Terminal telemetry stops permanently after 4096 job identities
Status: resolved in Remediation 1/2
Severity: high
Requirement/task: Delta `Telemetry SHALL expose transitions, stages, and durations`, scenario `Successful run emits bounded lifecycle evidence`; tasks 1.1, 1.2, 5.2; design decisions 2 and 5.
Evidence: `src/omaha/routes/imports.py:560-565` adds job IDs to `_terminal_observed` until length reaches 4096, then returns without emitting. Set never evicts. Every later terminal job can finish successfully while producing no terminal event, contradicting one terminal event per run and run correlation.
Required change: retain bounded duplicate protection while allowing every new terminal job to emit exactly one terminal event; use bounded eviction/active-run lifecycle tracking or equivalent keyed mechanism. Do not add DB columns, telemetry persistence, retention infrastructure, unbounded state, or change job status/cleanup behavior.
Acceptance: focused integration test creates more than 4096 distinct terminal job IDs (or injects a bounded recorder state) and asserts each terminal settlement emits one terminal event, duplicate settlement emits none, state remains bounded, and status/preview/cleanup/no-mutation assertions remain unchanged.

Resolution: changed `MyProfitSyncService._terminal_observed` from a rejecting
set to a bounded insertion-ordered deduplication window with
`TERMINAL_DEDUP_LIMIT = 4096`; new IDs evict oldest entries instead of being
dropped. Added `test_terminal_telemetry_emits_new_jobs_after_bounded_dedup_window`;
it emits 4097 distinct terminal events, suppresses repeated settlement for the
latest ID, and asserts state remains 4096 entries. Existing lifecycle and
no-mutation tests remain green.
Changed files/symbols: `src/omaha/routes/imports.py` — constant,
`MyProfitSyncService.__init__`, `_emit_terminal_once`; `tests/test_myprofit_sync_jobs.py`
— fixture cleanup and remediation test.

#### R1-F02 — Telemetry stage finalizer can alter synchronization exception behavior
Status: resolved in Remediation 1/2
Severity: medium
Requirement/task: Delta `Telemetry emission failure SHALL NOT change job status, preview handoff, cleanup, or manual commit behavior`; tasks 1.1, 2.1; design decision 5 and risk “Instrumentation changes functional flow”.
Evidence: `src/omaha/myprofit/telemetry.py:227-239` catches `BaseException`, then performs `getattr(failure, "stage", stage)` and `getattr(failure, "code", "unknown")` outside any protective boundary. Exception-like objects with raising `stage`/`code` properties can make the `finally` block raise a new exception and change the original connector/job flow. This path is not covered by focused tests.
Required change: make stage failure extraction itself best-effort and non-throwing; preserve original exception and job cleanup/status behavior even when exception metadata access or telemetry logging fails. Keep allowlists and raw-data exclusion; do not broaden exception logging or alter connector timeout/error mapping.
Acceptance: unit test raises an exception whose `stage` or `code` accessor raises, verifies original failure identity/error mapping and cleanup remain unchanged, and verifies no raw exception/property text enters captured telemetry; existing success/timeout/fake-browser tests remain green.

Resolution: added `_failure_metadata` best-effort accessor and guarded the
complete `stage_span` finalizer with a `BaseException` boundary. Raising
metadata accessors now fall back to fixed `stage`/`unknown` values, while the
original exception is re-raised unchanged and raw accessor/error text is not
logged. Added `test_stage_telemetry_metadata_failure_preserves_original_exception`;
existing connector timeout, cleanup, lifecycle, and no-mutation tests remain
green.
Changed files/symbols: `src/omaha/myprofit/telemetry.py` —
`_failure_metadata`, `stage_span`; `tests/test_myprofit_sync_jobs.py` —
remediation test.

Focused validation for both resolutions: remediation integration tests 2
passed; related integration lane 25 passed; connector/unit lane 32 passed;
lint final rerun passed. No timeout, retry, status, preview, cleanup, manual
commit, schema, persistence, retention, external service, F68, T36, or stable
spec behavior changed.

### Remediation 1 execution evidence

#### Ownership ledger — focused remediation tests

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-focused-20260824T170035-0300` | child process / process group / test DB resource | taskipy pytest children and isolated integration test DB resources created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:00:35-03:00` | `2026-08-24T17:01:17-03:00` | exited | owned-cleaned | bounded focused integration lane exited 0; 2 passed, 1151 deselected; product DB untouched | pytest/taskipy children exited; isolated fixture resources completed bounded cleanup; no residue observed |

Focused command registration before launch:
`uv run task test-integration -- -k "terminal_telemetry_emits_new_jobs_after_bounded_dedup_window or stage_telemetry_metadata_failure_preserves_original_exception"`

Result: exit 0, 2 passed, 1151 deselected in 6.43s.

#### Ownership ledger — focused lifecycle regression lane

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-lifecycle-20260824T170130-0300` | child process / process group / test DB resource | taskipy pytest children and isolated integration test DB resources created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:01:30-03:00` | `2026-08-24T17:01:54-03:00` | exited | owned-cleaned | related MyProfit lifecycle and telemetry integration lane exited 0; 25 passed, 1128 deselected; product DB untouched | pytest/taskipy children exited; isolated fixture resources completed bounded cleanup; no residue observed |

Focused command registration before launch:
`uv run task test-integration -- -k "myprofit_sync_jobs or telemetry"`

Result: exit 0, 25 passed, 1128 deselected in 9.58s.

#### Ownership ledger — connector telemetry regression lane

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-connector-20260824T170205-0300` | child process / process group / test DB resource | taskipy pytest children and isolated unit test resources created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:02:05-03:00` | `2026-08-24T17:02:33-03:00` | exited | owned-cleaned | related connector and telemetry unit lane exited 0; 32 passed, 1110 deselected; no product DB target | pytest/taskipy children exited; unit resources completed bounded cleanup; no residue observed |

Focused command registration before launch:
`uv run task test-unit -- -k "myprofit_connector or telemetry"`

Result: exit 0, 32 passed, 1110 deselected in 5.87s.

#### Ownership ledger — remediation lint

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-lint-20260824T170245-0300` | child process / process group | taskipy lint hooks and their children created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:02:45-03:00` | `2026-08-24T17:03:26-03:00` | exited | owned-cleaned | lint exited 1 because Ruff SIM117 remained after formatter hook modified files; no runtime/test failure | hooks exited; formatter changes retained as current-run owned edits; no process residue |

Focused command registration before launch:
`uv run task lint`

Result: exit 1; Ruff reported SIM117 in new nested test contexts. Formatter hook modified files; failure diagnosed and fixed before rerun.

#### Ownership ledger — remediation lint rerun

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-lint-rerun-20260824T170335-0300` | child process / process group | taskipy lint hooks and their children created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:03:35-03:00` | `2026-08-24T17:04:35-03:00` | exited | owned-cleaned | lint exited 1 because Ruff SIM117 also required combining pytest.raises and stage_span contexts; no runtime/test failure | hooks exited; formatter changes retained as current-run owned edits; no process residue |

Focused command registration before launch:
`uv run task lint`

Result: exit 1; Ruff SIM117 diagnosed and fixed by combining all three test contexts.

#### Ownership ledger — remediation lint final rerun

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-lint-final-20260824T170445-0300` | child process / process group | taskipy lint hooks and their children created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:04:45-03:00` | `2026-08-24T17:05:26-03:00` | exited | owned-cleaned | lint exited 0; all hooks passed including Ruff and pytest-unit hook | hooks exited; no process residue observed |

Focused command registration before launch:
`uv run task lint`

Result: exit 0; all hooks passed.

#### Ownership ledger — final focused integration validation

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-final-integration-20260824T171535-0300` | child process / process group / test DB resource | taskipy pytest children and isolated integration test DB resources created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:15:35-03:00` | `2026-08-24T17:15:57-03:00` | exited | owned-cleaned | final related integration validation exited 0; 25 passed, 1128 deselected; product DB untouched | pytest/taskipy children exited; isolated fixture resources completed bounded cleanup; no residue observed |

Focused command registration before launch:
`uv run task test-integration -- -k "myprofit_sync_jobs or telemetry"`

Result: exit 0, 25 passed, 1128 deselected in 9.62s.

#### Ownership ledger — final focused unit validation

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-final-unit-20260824T171620-0300` | child process / process group / test DB resource | taskipy pytest children and isolated unit test resources created by exact command below | T38 apply agent, remediation 1/2 | current change id plus exact taskipy command registered before launch; no PID adopted | `2026-08-24T17:16:20-03:00` | `2026-08-24T17:16:34-03:00` | exited | owned-cleaned | final connector and telemetry unit validation exited 0; 32 passed, 1110 deselected; no product DB target | pytest/taskipy children exited; unit resources completed bounded cleanup; no residue observed |

Focused command registration before launch:
`uv run task test-unit -- -k "myprofit_connector or telemetry"`

Result: exit 0, 32 passed, 1110 deselected in 5.82s.

#### Ownership ledger — final change validation

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-final-change-validation-20260824T171700-0300` | child process / process group | OpenSpec validator and git diff-check child processes created by exact commands below | T38 apply agent, remediation 1/2 | current change id plus exact commands registered before launch; no PID adopted | `2026-08-24T17:17:00-03:00` | `2026-08-24T17:17:08-03:00` | exited | owned-cleaned | OpenSpec change valid; git diff check exited 0 | validator and diff-check processes exited; no residue observed |

Focused command registration before launch:
`openspec validate t38-telemetria-minima-e-runbook-de-analise-myprofit --type change --no-interactive && rtk git diff --check`

Result: valid; both commands exit 0.

#### Ownership ledger — remediation refresh

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-refresh-20260824T171730-0300` | process group / listener / port | exact current Omaha PGID `159577`, listener PID `159581`, port `8000` | T38 apply agent, remediation 1/2 | prior owner-authorized T38 receipt identifies exact command/cwd/user and current delivery resources; remediation uses no other PID/PGID/port | `2026-08-24T17:17:30-03:00` | `2026-08-24T17:17:39-03:00` | exited | owned-cleaned | exact old process group terminated with bounded TERM; old listener absent before rebind | exact PGID only targeted; port released; no broad kill or cleanup |
| `T38-remediation1-refresh-log-20260824T171730-0300` | log / temporary path | `/tmp/omaha-t38-remediation1-refresh-20260824.log` | T38 apply agent, remediation 1/2 | exact new log path declared and verified absent before launch | `2026-08-24T17:17:30-03:00` | active | active | owned-current-run | refresh log contains startup complete and exact new listener PID `166748` | preserve as active delivery log; bounded cleanup decision pending |
| `T38-remediation1-refresh-new-20260824T171841-0300` | process group / listener / port | PGID `166745` / listener PID `166748` / port `8000` | T38 apply agent, remediation 1/2 | exact launch command, cwd `/home/juca/github/omaha`, user `juca`; startup log and listener inspection match | `2026-08-24T17:18:41-03:00` | active | active | owned-current-run | `0.0.0.0:8000` maps exactly to PID `166748`; healthz HTTP 200 | preserve as active delivery listener; bounded cleanup only on authorized follow-up |
| `T38-remediation1-refresh-launcher-20260824T171841-0300` | child process | launcher PID `166743` | T38 apply agent, remediation 1/2 | exact launch command returned PID before shell timeout; server child continued with declared PGID/log | `2026-08-24T17:18:41-03:00` | `2026-08-24T17:18:41-03:00` | absent | absent | launcher shell absent after tool timeout; child server identity independently reconciled from exact log/listener | idempotent no-op; not retried or adopted as target |
| `T38-remediation1-refresh-cookie-20260824T172110-0300` | temporary path | `/tmp/omaha-t38-remediation1-cookie-20260824.txt` | T38 apply agent, remediation 1/2 | exact cookie path declared before read-only authenticated smoke; verified absent before use | `2026-08-24T17:21:10-03:00` | `2026-08-24T17:22:04-03:00` | absent | owned-cleaned | read-only login/profile/dashboard cookie; exact path absent after smoke | exact bounded removal succeeded; no other temporary path touched |
| `T38-remediation1-refresh-smoke-20260824T172110-0300` | child process / process group | exact curl and `uv run python` smoke children created by declared commands | T38 apply agent, remediation 1/2 | exact LAN URL, read-only GET/POST auth commands, and bounded output pipeline; no PID adopted | `2026-08-24T17:21:10-03:00` | `2026-08-24T17:22:26-03:00` | exited | owned-cleaned | first profile-select pipeline stopped at `python` unavailable after login/profile returned 303; corrected `uv run python` smoke returned `RF Din count 5`; final health 200 | all smoke children exited; cookie exact path cleaned; no DB mutation |

Refresh result: implementation bytes loaded by exact new listener PGID `166745`,
PID `166748`; LAN URL from `bash scripts/print_lan_url.sh` was
`http://192.168.1.8:8000`; `GET /healthz` returned HTTP 200; read-only DB state
remained `11 classes / 89 assets / 88 positions`; authenticated dashboard smoke
returned `RF Din count 5`. No destructive DB task ran. Exact delivery listener
and log remain active owned-current-run resources. No foreign process, listener,
test DB, or declared temporary resource was adopted or cleaned.

Canonical review isolation: no canonical full suite launched; state remains
`maintenance-suspended`. Focused runner resources exited and isolated fixture
resources were cleaned. No baseline or allowlist exception used.

### Remediation acceptance summary

- R1-F01 resolved: 4097 distinct terminal settlements all emitted; latest
  duplicate suppressed; in-memory dedup state stayed at 4096 entries.
- R1-F02 resolved: raising `stage`/`code` accessors fell back safely; original
  exception identity and propagation remained unchanged; raw accessor/error
  text absent from telemetry.
- Focused final validation: integration `25 passed`; unit `32 passed`; lint
  all hooks passed; OpenSpec validation valid; `git diff --check` clean.
- No timeout, retry, external service, DB schema, persistence, retention,
  status, preview, cleanup, manual commit, F68, T36, or stable spec behavior
  changed.

#### Ownership ledger — post-receipt change validation

| run id | resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|---|
| `T38-remediation1-post-receipt-validation-20260824T172305-0300` | child process / process group | OpenSpec validator and git diff-check child processes created by exact commands below | T38 apply agent, remediation 1/2 | current change id plus exact commands registered before launch; no PID adopted | `2026-08-24T17:23:05-03:00` | `2026-08-24T17:23:18-03:00` | exited | owned-cleaned | OpenSpec change valid; git diff check exited 0 | validator and diff-check processes exited; no residue observed |

Focused command registration before launch:
`openspec validate t38-telemetria-minima-e-runbook-de-analise-myprofit --type change --no-interactive && rtk git diff --check`

Refresh command registration before use: exact current listener identity above;
new launch command `setsid bash -c 'exec uv run uvicorn omaha.main:app --host
0.0.0.0 --port 8000'` with only declared log path. Read-only health, DB, and
dashboard checks only; no destructive DB task.

### Review R2 — remediation 1/2
Scope audit: pass. Rechecked complete dossier, all 10 tasks, all delta
requirements/scenarios, stable MyProfit job/connector/import contracts,
runtime symbols, connector/browser instrumentation, UI local-limit signal,
preview/manual-commit boundary, runbook 4–8 week analysis contract,
sanitization/cardinality, lifecycle/status/error preservation, test markers,
allow-list, PRD §4.1–§4.14, and unrelated-file boundary. No area is not
assessable.

R1-F01: resolved. `src/omaha/routes/imports.py:565-572` now uses a 4096-entry
insertion-ordered window. New terminal IDs evict oldest entries and still emit;
duplicate settlement remains suppressed while identity is retained. Remediation
test proves 4097 distinct terminal events, latest duplicate suppression, and
state size 4096. Lifecycle guards preserve normal late-result/expiry behavior.

R1-F02: resolved. `src/omaha/myprofit/telemetry.py:187-194,240-254` guards
metadata access and complete finalizer. Accessor failures use fixed fallback
values; original exception identity/propagation remains unchanged; raw
accessor/error text is absent. Remediation test proves behavior.

Focused evidence: green — remediation pair 2 passed; related integration 25
passed; connector/unit 32 passed; lint passed. Apply receipt records exact
commands, timestamps, ownership, isolated test resources, cleanup, and product
DB protection. Refresh receipt records health 200, DB `11/89/88`, exact old
PGID `159577` cleanup, fresh PGID `166745` / listener PID `166748` on
`0.0.0.0:8000`, and no foreign-resource adoption.

Verification: `openspec validate t38-telemetria-minima-e-runbook-de-analise-myprofit --type change --no-interactive` -> valid, exit 0. `git diff --check` -> clean, exit 0. No timeout, retry, external-service, F68, T36, schema, persistence, status, preview, cleanup, manual-commit, stable-spec, test-deletion, skip, xfail, retry, or coverage change. Runbook remains coherent: stdout-only source, 4–8 week evidence window, bounded grouping, insufficient-evidence rule, and diagnosis thresholds; rolling dedup prevents silent terminal suppression without adding retention infrastructure.

Full suite: `uv run task test` -> `NOT RUN — maintenance-suspended`; no
canonical duration, six-lane result, coverage/skips, fail-fast, or `<=300s`
classification applies. Suspension is non-blocking under `openspec/config.yaml`;
focused product evidence is green.

Preflight: per-run ledger and current exact resources inspected. PGID `166745`,
listener PID `166748`, port `8000`, and declared refresh log are
`owned-current-run` with owner evidence from remediation receipt. Old PGID
`159577` is `owned-cleaned`; exact cookie/health temp paths are absent and
`owned-cleaned`. Focused child/test-DB resources are `owned-cleaned`. No
foreign, unknown, contradictory, or incomplete relevant resource observed.
No canonical runner launched.

Postflight: focused resources exited and cleaned. Active delivery server/log
preserved as owner-authorized current-run resources. No broad cleanup or
foreign-resource action performed.

Runner isolation: pass for focused audit; canonical launch prohibited by
maintenance suspension. No baseline or allowlist exception used.

Verdict: APPROVED
