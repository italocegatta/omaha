## 1. Bounded diagnosis and ownership ledger

- [x] 1.1 Inspect `scripts/run_full_suite.py::_lane_metadata`, `launch`,
  `monitor`, `_stop`, `_reap`, `_final_exit_code`, and receipt finalization
  against F58 R6 integration evidence. Add no repair until one controlled
  observation records run ID, lane, parent PID, child PID, actual PGID,
  poll/signal/wait/exit timestamps, return code, and first-failure reason.
  Preserve six lanes, launch order, taskipy commands, fail-fast, and 300-second
  deadline. Acceptance: integration PID lineage is either fully attributable or
  explicitly `unknown`/blocked; no PID/PGID is inferred from name/port/path.
  Test file/scenario: `tests/scripts/test_t29_harness.py` controlled child
  lifecycle scenarios for launch, vanish, signal, wait, and exit. Focused
  taskipy command: `uv run task test-one tests/scripts/test_t29_harness.py -k "lineage or vanished_child or parent_sigterm"`.
  Independent oracle: receipt JSON contains same run/lane ID on every lineage
  event, actual PGID, explicit nulls for unavailable fields, and no signal call
  targets an unrecorded group.

- [x] 1.2 Diagnose `tests/support/server.py::run_test_server` and
  `tests/support/browser.py::wait_for_port`/`shutdown_uvicorn` using controlled
  dead-child, stale-listener, live-child-not-ready, and normal-ready cases.
  Record launch/readiness/port/log/exit/teardown evidence for requested
  `127.0.0.1:8768`; preserve current hosts, ports, env, browser scopes, and
  bounded timeout. Acceptance: one causal boundary is selected only when
  controlled evidence falsifies alternatives; ambiguous or contradictory state
  returns `BLOCKED_FOR_IMPLEMENTATION_BRIEF` and receives no speculative fix.
  Test file/scenario: existing stale-listener test plus focused server lifecycle
  cases in `tests/scripts/test_t29_harness.py`. Focused taskipy command:
  `uv run task test-one tests/scripts/test_t29_harness.py -k "server or listener or readiness"`.
  Independent oracle: dead child never yields URL, unrelated listener is never
  adopted, and failure includes return code plus flushed log evidence.

## 2. Implement confirmed runner/harness boundaries

- [x] 2.1 Update `scripts/run_full_suite.py` lifecycle symbols only for the
  confirmed PID-lineage defect: persist parent PID, child PID, actual PGID,
  phase events, poll/wait/exit values, and run/lane owner evidence; signal and
  reap only recorded current-run-owned groups. Preserve `_final_exit_code`
  precedence, fail-fast sibling attribution, signal exit semantics, bounded
  grace/KILL, six lane placeholders, and receipt persistence. Acceptance:
  controlled PID-not-found/ESRCH/EPIPE observations are recorded as bounded
  races, unexpected errors remain nonzero, and foreign/unknown resources are
  untouched. Test file/scenario: `tests/scripts/test_t29_harness.py` lineage,
  vanished-child, survivor, fail-fast, partial-launch, and timeout receipts.
  Focused taskipy command: `uv run task test-file tests/scripts/test_t29_harness.py`.
  Independent oracle: `git diff -- scripts/run_full_suite.py` changes no lane,
  task, port, DB allow-list, coverage, skip, or timeout topology.

- [x] 2.2 Update `tests/support/browser.py::wait_for_port` and
  `shutdown_uvicorn`, plus `tests/support/server.py::run_test_server`, only for
  the confirmed visual lifecycle defect. Bind readiness to spawned-child
  liveness and exact requested port, flush/read owned logs before raising, and
  publish run/lane parent/child/PGID/readiness/exit evidence. Preserve
  `127.0.0.1`, ports 8765/8766/8767/8768, existing env, browser args, bounded
  teardown, and no browser retry. Acceptance: visual startup failure is
  attributable; stale/dead listeners fail closed; normal visual server starts
  and reaps child. Test file/scenario: `tests/scripts/test_t29_harness.py`
  controlled lifecycle tests. Focused taskipy command:
  `uv run task test-one tests/scripts/test_t29_harness.py -k "server or listener or readiness"`.
  Independent oracle: no `page.goto` retry, no port scan/kill, and no changes
  to `tests/visual/conftest.py` unless direct evidence requires a declared
  boundary file.

- [x] 2.3 Update `scripts/run_full_suite.py::launch` lane environment and
  finalization, `tests/conftest.py::_omaha_test_env`/session setup, and
  `tests/support/db.py` receipt helpers to publish exact current-run pytest
  temp-root ownership. Use unique run/lane boundary, emit actual
  `tmp_path_factory.getbasetemp()`, reconcile only declared exact paths, and
  clean exact current-run-owned roots when safe. Preserve safe dynamic DB
  binding/import ordering, `T29_DB_TARGET`, production-DB guard, explicit
  marker allow-lists, all test fixtures, and no broad `/tmp` operation.
  Acceptance: every canonical lane has temp receipt and final state
  `absent`/`owned-cleaned`; missing/mismatched/pre-existing/foreign roots inside
  the runner-declared exact boundary remain untouched and force untrusted
  nonzero; out-of-bound temporary observations are preserved/non-target and do
  not block alone. Test file/scenario:
  `tests/scripts/test_t29_harness.py` temp ownership/reconciliation matrix and
  `tests/conftest.py` receipt path scenario. Focused taskipy command:
  `uv run task test-one tests/scripts/test_t29_harness.py -k "temp or receipt or ownership"`.
  Independent oracle: no recursive `/tmp/pytest-of-*` discovery, no deletion
  outside exact run/lane boundary, and no `data/portfolio.db` access.

- [x] 2.4 Do not edit `pyproject.toml` or other task/config files unless task
  or configuration causality is directly proven by task-boundary evidence. If
  required, change only named canonical task invocation while preserving six
  lane names/order, coverage/no-coverage flags, skips, fail-fast, and taskipy
  entrypoint. Acceptance: no task/config change is made for an unproven
  hypothesis; any necessary change has a focused harness regression scenario.
  Test file/scenario: `tests/scripts/test_t29_harness.py` command construction
  and lane topology tests. Focused taskipy command:
  `uv run task test-one tests/scripts/test_t29_harness.py -k "runtime_child_command or lane"`.
  Independent oracle: `git diff -- pyproject.toml` is empty unless design
  evidence names exact causal lines.

## 3. Focused verification and canonical acceptance

- [x] 3.1 Run complete focused harness verification after implementation:
  `tests/scripts/test_t29_harness.py` plus directly affected support tests if
  added. Preserve all pre-existing T29/T33/I08 contract tests and test markers;
  do not add skip/xfail/retry. Acceptance: focused task passes and receipt
  scenarios prove lineage, visual readiness, exact temp ownership,
  production-DB refusal, foreign-resource preservation, fail-fast, coverage,
  skips, and timeout behavior. Test file/scenario:
  `tests/scripts/test_t29_harness.py` entire module. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`.
  Independent oracle: `git diff --check`; changed-file audit lists only T34
  mapped implementation/tests plus T34 artifacts.

- [ ] 3.2 Review owns exactly one canonical `uv run task test` after focused
  repair; do not retry or run a second full suite. Acceptance evidence MUST
  include one run ID, six lane receipts exit 0, fail-fast semantics preserved,
  current node/coverage/skips reconciliation, DB targets isolated from
  production, trusted cleanup with every cleanup-relevant runner-declared exact
  temp path `absent` or `owned-cleaned`, no foreign/unknown residue action
  inside a declared boundary, out-of-bound temporary observations preserved as
  non-target without blocking alone, and elapsed wall-clock through cleanup
  <=300 seconds. Test file/scenario: canonical six-lane suite.
  Focused taskipy command: `uv run task test` (exactly once, review gate only).
  Independent oracle: run receipt plus postflight comparison by same run ID;
  any missing/contradictory evidence, red lane, reconciliation mismatch,
  untrusted cleanup, or duration over 300 seconds blocks acceptance.

- [x] 3.3 Perform final T34 scope/spec health audit without implementation or
  host mutation. Preserve F58 `Blocked` until canonical receipt passes; do not
  reopen T33/I08/D05 or touch F58 files. Acceptance: strict change/spec
  validation passes, no unrelated files appear, and dossier records focused
  results, one canonical result, acceptance evidence, and blockers. Test
  file/scenario: OpenSpec validation and mapped diff audit. Focused taskipy
  command: `uv run task test-one tests/scripts/test_t29_harness.py` only if a
  final focused smoke is needed; no additional canonical run. Independent
   oracle: `openspec validate t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 --type change --strict --json`,
   `openspec validate --specs --strict --json`, and `git status --short`.

## Review Findings

### Review R1

Scope audit: proposal pass; design pass; delta specs `dev-tasks` and
`shared-test-support` pass; tasks/evidence pass except review task 3.2 remains
open by design; PID/PGID/descendant lifecycle implementation pass by static
audit; visual `127.0.0.1:8768` child/readiness/log lifecycle pass by static
audit; exact pytest-temp reconciliation not assessable without canonical run;
full six-lane acceptance, coverage/skips, postflight receipt reconciliation,
and <=300s gate not assessable because trusted preflight blocked. Scope boundary
pass: T34 mapped files only in T34 diff; pre-existing `pyproject.toml`, F58,
product, archive, and unrelated worktree changes excluded.

Full suite: `uv run task test` -> **not run**, 0s, cleanup not applicable.
Canonical command was not launched after preflight block. Six lane receipt:
unit not run; integration not run; audit integration not run; e2e not run; bdd
not run; visual not run. Coverage/skips/node reconciliation unavailable;
fail-fast disposition unavailable. No red test classification exists because
no suite process started. Duration limit 300s; no duration classification.

Preflight: review ledger inspection at `2026-08-21T09:19:08-03:00` found no
`run_full_suite`, pytest, Playwright, BDD, or task-test process; ports 8765,
8766, 8767, and 8768 had no listener. Exact known path
`/tmp/pytest-of-juca` exists as directory, owner `juca:juca`, mode 700, mtime
`2026-08-21 09:16:18 -0300`; owner evidence belongs to prior focused apply run,
not current review. Classification: `pre-existing`; it is relevant pytest-temp
residue, therefore runner isolation failed. No adoption, deletion, kill, port
free, or broad scan performed. Per-run ledger fields: `resource_kind=temporary
path`, `resource_id=/tmp/pytest-of-juca`, `owner=T34 apply focused run`
(`t34-apply-focused-20260821T090935-0300`), `owner_evidence=prior tasks.md
receipt and mtime`, `started_at=prior apply session`, `ended_at=prior apply
session`, `status=present`, `classification=pre-existing`,
`evidence=exact stat above; no current-review identity`,
`cleanup_result=untouched; review blocked`.

Postflight: no canonical child cleanup occurred. Repeated inventory after
authorized LAN-service restoration at `2026-08-21T09:19:08-03:00` still showed
no suite processes and no 8765-8768 listeners. `/tmp/pytest-of-juca` remained
present and untouched, classification `pre-existing`. No current-run ledger
end timestamp exists because canonical run did not start; cleanup result
`not-applicable`. Service operation is separately recorded below.

Runner isolation: **failed precondition**. Relevant process/listener lane
inventory was clear, but relevant pytest temporary inventory had pre-existing
unowned state. No baseline or allowlist exception used. Required escalation is
isolated runner/environment; review stopped before `uv run task test`.

Service stop/restart/health: confirmed exact pre-existing Docker resource before
control at `2026-08-21T09:18:32-03:00`: container `omaha-web-1`, ID
`63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`, image
`omaha:dev`, published `0.0.0.0:8000` and `[::]:8000`, status healthy. Owner
evidence was exact Docker name/ID/image/port inspection; no name-pattern or
host-wide cleanup. Controlled `docker stop omaha-web-1` then
`docker start omaha-web-1` completed (`stop_start_epoch=1787314719.167234160`,
`stop_end_epoch=1787314722.275002164`, `start_end_epoch=1787314723.338039237`).
First immediate health probe caught expected startup race (health `starting`,
HTTP connection reset); second poll reached LAN HTTP successfully. Final
container status `running`, Docker health `healthy`, LAN URL
`http://192.168.1.4:8000`, health `reachable`. Service restored; no suite
resource overlap.

Verdict: **BLOCKED**

#### R1-F01 — Trusted runner isolation unavailable due pre-existing pytest temp root
Status: blocked
Requirement/task: `dev-tasks` Requirement “Current-run pytest temp root
reconciles exactly”; `shared-test-support` Requirement “Current-run pytest
temporary ownership is receipt-bound”; task 3.2.
Evidence: exact `stat` of `/tmp/pytest-of-juca` at review preflight showed
directory mtime `2026-08-21 09:16:18 -0300`, while current review had no
ownership receipt or process identity for it. Preflight classification is
`pre-existing`, not `owned-current-run`, `owned-cleaned`, or `absent`.
Required change: provide isolated review runner/environment with no relevant
pre-existing, foreign, unknown, contradictory, or incomplete process,
listener, or test-temp state; rerun this review preflight and, only if trusted,
execute exactly one `uv run task test`. Do not delete, adopt, kill, free, scan,
or allowlist `/tmp/pytest-of-juca` or any foreign resource. Excluded scope:
T34 code fixes, broad cleanup, retries/skips/xfails, lane topology, F58,
product code, DB/seed/migrations, T33/I08 archives.
Acceptance: ledger contains complete ownership fields and classifications;
canonical receipt has one run ID, six lane exit-0 receipts, PID/PGID and visual
8768 lifecycle evidence, exact temp paths reconciled only as `absent` or
`owned-cleaned`, coverage/skips/node reconciliation, trusted postflight, and
elapsed wall-clock through cleanup <=300s.

## Execution Evidence

### Pre-edit boundary

- Apply captured `git diff HEAD~1` before editing, per PRD §4.14. Existing
  worktree changes include `scripts/run_full_suite.py`, `tests/conftest.py`,
  `tests/scripts/test_t29_harness.py`, `pyproject.toml`, application/config
  files, visual baselines, F58/T34 dossiers, and unrelated documentation.
- T34 owns only its dossier plus the mapped runner/shared-test-support files
  named in the apply brief. Existing hunks in those files are preserved; no
  F58 implementation, route/model/template, DB/seed/migration, production DB,
  host resource, T33/I08 archive, or task/config change is owned by this pass.

### Apply validation ledger — T34 initial diagnosis

- Run ID: `t34-apply-initial-diagnosis-20260821T090058-0300`
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`
- Owner evidence: this ledger registration was written before focused
  taskipy validation; run timestamp is `2026-08-21T09:00:58-03:00`.
- Registered resources before use: current taskipy/pytest child process and
  process group (PID/PGID assigned by invocation), pytest-owned test DB/temp
  paths (IDs assigned by fixtures), and controlled listener only inside
  `test_t29_harness.py` stale-listener scenario. No Omaha LAN server, fixed
  canonical lane port, production DB, or broad `/tmp` resource is registered.
- Cleanup decision: only exact resources created and attributable to this run
  may be cleaned by their test fixtures; no PID, port, path, or DB is adopted
  from observation alone.
- Diagnosis extension registered at `2026-08-21T09:03:49-03:00` under same run:
  controlled pytest process/group, pytest-owned DB/temp resources, and one
  in-process stale-listener socket. Owner evidence is the current taskipy
  invocation plus fixture/socket creation in the selected test; no fixed lane
  port or live server is used.

### Diagnosis result

- `uv run task test-one tests/scripts/test_t29_harness.py -k "lineage or vanished_child or parent_sigterm"` -> `3 passed, 46 deselected` before diagnostic contracts.
- `uv run task test-one tests/scripts/test_t29_harness.py -k "server or listener or readiness"` -> `1 passed, 48 deselected` before diagnostic contracts.
- Added controlled contracts for actual PGID/lifecycle identity, visual `8768`
  dead-child log evidence, and run/lane temp receipt. Their bounded RED run:
  `uv run task test-one tests/scripts/test_t29_harness.py -k "actual_pgid or wait_for_port or temp_receipt"` -> `3 failed` with only confirmed missing boundaries: `_lane_metadata(temp_root/lifecycle)`, `wait_for_port(log_path/run_id/lane)`, and `emit_temp_root_receipt`.
- Diagnosis selects three repairs only: record actual PGID and lifecycle events;
  bind visual failure evidence to child/log/run/lane; publish and reconcile
  exact runner-declared pytest base temp path. No task topology or product code
  boundary implicated.
- Repair validation run registration: `t34-apply-focused-20260821T090935-0300`,
  owner `t34/... / apply`, registered `2026-08-21T09:09:35-03:00` before
  taskipy use. Resources are current taskipy/pytest PID+PGID and fixture-owned
  temp/DB paths; no fixed lane listener or live Omaha server. Exact controlled
  listener/resource cleanup remains fixture-owned and bounded.
- Focused run surfaced test drift only: new exact temp receipt made the prior
  finalization-double condition non-empty. Test now keys controlled failure on
  missing timing receipt, preserving its original failure oracle; no runtime
  behavior was weakened.

### Implementation / focused acceptance evidence

- Changed runtime symbols: `scripts/run_full_suite.py::_lane_environment`,
  `_lane_metadata`, `_record_lifecycle`, `_owned_process_group`, `_stop`,
  `_reap`, `launch`, `monitor`, `_reconcile_temp_root`, `_server_events`, and
  lane finalization; `tests/support/browser.py::wait_for_port`/
  `shutdown_uvicorn`; `tests/support/server.py::run_test_server`;
  `tests/support/db.py::emit_temp_root_receipt`; `tests/conftest.py::_omaha_test_env`.
- Changed contracts: `tests/scripts/test_t29_harness.py` adds controlled actual
  PGID, lifecycle, visual 8768 log/readiness, server launch/teardown, exact
  temp ownership, mismatch preservation, and receipt-event tests. Existing
  T29 tests retained; one finalization test now triggers its controlled error
  through missing timing evidence because temp receipt output is now expected.
- `uv run task test-one tests/scripts/test_t29_harness.py -k "lineage or vanished_child or parent_sigterm"` -> `4 passed, 49 deselected`.
- `uv run task test-one tests/scripts/test_t29_harness.py -k "server or listener or readiness"` -> `2 passed, 55 deselected`.
- `uv run task test-one tests/scripts/test_t29_harness.py -k "temp or receipt or ownership"` -> `14 passed, 39 deselected` before final additions; final full focused module below covers additions.
- `uv run task test-one tests/scripts/test_t29_harness.py -k "runtime_child_command or lane"` -> `14 passed, 42 deselected`.
- `uv run task test-file tests/scripts/test_t29_harness.py` -> `57 passed in 0.33s` (final receipt run; wrapper PID/PGID `609003`).
- `PYTHONPATH=. uv run task test-file scripts/test_browser_harness.py` -> `5 passed in 0.13s` (wrapper PID/PGID `609041`). Plain taskipy invocation without `PYTHONPATH=.` failed collection because this pre-existing script test is outside pytest `tests/` import path; no code failure. `PYTHONPATH=.` is bounded import-path correction for focused validation only.
- Targeted `uv run ruff check scripts/run_full_suite.py tests/support/browser.py tests/support/server.py tests/support/db.py tests/conftest.py tests/scripts/test_t29_harness.py` -> all checks passed.
- `git diff --check` -> clean. `pyproject.toml` unchanged by T34; lane/task topology,
  ports, DB allow-list, coverage/no-cov flags, skips, fail-fast, and 300-second
  ceiling unchanged.
- OpenSpec validation: change strict `valid=true`; specs strict `70/70 passed`
  with existing informational long-requirement notices only.

### Resource ownership receipt — focused apply runs

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `609003` (`task-file` harness wrapper) | T34 apply | wrapper printed PID before `exec uv run task`; run `t34-apply-focused-20260821T090935-0300` | `2026-08-21T09:16:10-03:00` | `2026-08-21T09:16:11-03:00` | exited | owned-cleaned | `57 passed`; no child failure or residue in focused receipt | pytest/taskipy exited; bounded fixture teardown completed; no cleanup action by apply |
| process group | PGID `609003` | T34 apply | wrapper printed PGID equal to owner PID before task launch | `2026-08-21T09:16:10-03:00` | `2026-08-21T09:16:11-03:00` | exited | owned-cleaned | same-run wrapper group only; no signal/kill operation performed | idempotent no-op; already exited |
| child process | PID `609041` (`scripts/test_browser_harness.py` wrapper) | T34 apply | wrapper printed PID before `exec env PYTHONPATH=. uv run task` | `2026-08-21T09:16:17-03:00` | `2026-08-21T09:16:18-03:00` | exited | owned-cleaned | `5 passed`; controlled fake processes only | idempotent no-op; already exited |
| process group | PGID `609041` | T34 apply | wrapper printed PGID equal to owner PID before task launch | `2026-08-21T09:16:17-03:00` | `2026-08-21T09:16:18-03:00` | exited | owned-cleaned | no live server or fixed lane listener | idempotent no-op; already exited |
| test DB resource | dynamic `omaha-conftest-safe-*` paths emitted by current pytest conftest | T34 apply | current taskipy pytest session created and conftest bound safe DB before collection; production path rejected by existing guard | per focused pytest session | per focused pytest session | exited | owned-cleaned | test-only dynamic DB; no `data/portfolio.db` access | fixture/session teardown; no production cleanup |
| temporary path | pytest-owned per-session/per-test `tmp_path` resources | T34 apply | current pytest invocation and fixture ownership; no broad `/tmp` discovery | per focused pytest session | per focused pytest session | exited | owned-cleaned | controlled tests use pytest temp fixtures only | pytest teardown; no broad cleanup or unrecorded deletion |
| port | controlled ephemeral stale-listener socket in T29 test | T34 apply | test created socket and recorded local handle before use | test-local | test-local | absent | absent | socket closed in test `finally`; no 8765-8768 listener | idempotent no-op; already closed |

Cleanup decision: only current-run wrapper/test resources were observed;
owned entries exited or fixture-cleaned. No foreign, pre-existing, unknown,
production, fixed-lane, or broad `/tmp` resource was adopted, signaled, freed,
or deleted. Canonical review isolation remains review's preflight gate.

Final scope audit: T34 changed only its dossier and mapped runner/shared-test
support/harness files. Pre-existing worktree files listed under Pre-edit
boundary remain outside this slice. No canonical full suite was run by apply;
task 3.2 remains open for review's exactly-one isolated `uv run task test`.

### Review R2

Scope audit: proposal pass; design pass; delta specs `dev-tasks` and
`shared-test-support` pass; task 3.2 executed exactly once and remains failing;
task 3.3 validation pass (`change valid=true`, stable specs `70/70`); PID/PGID
lineage static mapping pass; visual child/readiness/log mapping pass by static
audit; exact temp ownership **finding** from canonical receipt; six-lane
acceptance **finding**; coverage/skips/reconciliation **finding**; service
identity/health pass; scope boundary pass. Excluded F58/MyProfit/product code,
I08/T33 archives, broad cleanup, retries/skips/xfails, lane changes,
DB/seed/migrations. No code, archive, commit, or push performed by review.

Full suite: `uv run task test` -> **red**, wrapper exit `124`, runner receipt
`reports/test-profile/20260821T112339-run.json`, run ID
`20260821T112339-618393`; external wall-clock `381.795s` from
`2026-08-21T11:23:39-03:00` through `2026-08-21T11:30:00-03:00`; runner
elapsed `381.24866050097626s`; duration limit `300s`; cleanup state
`untrusted-resource`; `duration_exceeded=true`, `deadline_triggered=true`.
Six lanes: unit `241`/SIGTERM deadline, integration `1`/process PID-not-found,
audit `241`/SIGTERM deadline, e2e `241`/SIGTERM deadline, bdd `1`/35 terminal
failed nodes, visual `241`/SIGTERM deadline. Coverage unavailable; unit and
integration stopped during collection, audit had no final coverage receipt,
browser lanes used `--no-cov` but did not finish. Reported skips `[]`; manifest
node reconciliation incomplete. Fail-fast/deadline disposition: deadline
signaled remaining owned groups; first observed integration lifecycle failure
was not converted to green. No retry, skip, or xfail was run.

Preflight: `2026-08-21T11:23:11-03:00`, after owner-authorized exact cleanup.
Ledger fields: `resource_kind=process/listener/temp path`, resource IDs were
the six canonical lane process classes, ports `8765-8768`, and exact
`/tmp/pytest-of-juca`; owner `T34 final review`; owner evidence was empty
relevant-process inventory, `ss` showing no lane listeners, and exact `stat`
showing `/tmp/pytest-of-juca` absent; started/ended timestamps recorded at
preflight boundary; status `absent`; classification `absent`; cleanup result
`not applicable`. No unknown, pre-existing, foreign, contradictory, or
incomplete state observed. Runner isolation precondition passed. Initial
metadata captured before removal: exact path `/tmp/pytest-of-juca`, type
directory, owner `juca:juca`, mode `700`, inode `1365472`, size `140`, birth
`2026-08-20 21:45:51.433505348 -0300`, atime/mtime/ctime
`2026-08-21 09:16:18.317472960 -0300`; removal used only `rm -rf --
/tmp/pytest-of-juca`, no wildcard, parent, or broad `/tmp` operation.

Postflight: `2026-08-21T11:30:18-03:00`. Runner processes exited, but exact
current-run residue remained: listener `127.0.0.1:8766`, PID/PGID `618454`,
parent `1`, command `/home/juca/github/omaha/.venv/bin/python3 -m u...`, and
six exact runner-declared pytest roots under
`reports/test-profile/.20260821T112339-618393-*`, all owner `juca:juca` with
birth times from `11:23:39`/`11:23:43`/`11:23:44`. Classification:
`owned-current-run` by run-ID/path evidence, cleanup result `untouched`; no
authorization existed to remove any path except `/tmp/pytest-of-juca`, and no
process, listener, or other temp path was killed/freed/deleted/adopted. The
authorized path remained absent. Docker resource was not stopped: pre-confirmed
`omaha-web-1`, ID `63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`,
image `omaha:dev`, published `0.0.0.0:8000`/`[::]:8000`, status `running`,
health `healthy`; LAN URL `http://192.168.1.4:8000`; `/healthz` returned
`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.

Runner isolation: precondition passed before launch; postflight cleanup
receipt is untrusted because current-run listener/temp roots remained and temp
receipt reconciliation failed. No baseline or allowlist exception used.

Verdict: **CHANGES_REQUESTED**

#### R2-F01 — Canonical suite exceeds hard ceiling and leaves untrusted temp receipt
Status: open
Requirement/task: `dev-tasks` Test coverage report and scenarios “Full task
concurrently preserves complete coverage” / “Current-run pytest temp root
reconciles exactly”; task 3.2; PRD §4.13.
Evidence: `reports/test-profile/20260821T112339-run.json:5-8,19-28,55-65,93-135`
records `381.24866050097626s`, deadline, `duration_exceeded=true`, and each
lane's `temp_root_reconciliation.classification=unknown` with empty
`reported_paths` for unit/integration and incomplete evidence for remaining
lanes. Exact roots remained at postflight. External receipt measured `381.795s`.
Required change: make canonical run finish within `300s` and emit exactly one
matching `T29_TEMP_ROOT`, run ID, and lane receipt per lane so every declared
root reconciles only to `absent` or `owned-cleaned`; preserve all six lanes,
coverage, manifest/skips, fail-fast, and exact-cleanup safety. Do not remove
tests, reduce coverage, retry, or broaden cleanup. Excluded scope: F58/product,
DB/seed/migrations, archives, and host-wide cleanup.
Acceptance: one future trusted `uv run task test` receipt with six exit-0 lanes,
complete coverage/skips/node reconciliation, no residue outside exact owned
paths, and wall-clock `<=300s` through child cleanup.

#### R2-F02 — Integration lifecycle still reports vanished child and visual/e2e child transport breaks
Status: open
Requirement/task: `dev-tasks` scenarios “PID lineage and vanished child preserve
causal failure” and “Interrupted full task reaps browser and server children”;
`shared-test-support` lifecycle scenarios; tasks 2.1-2.2 and 3.2.
Evidence: `reports/test-profile/20260821T112339-integration.log:10` reports
`process PID not found (pid=618421)`; `reports/test-profile/20260821T112339-e2e.log:15-39`
and `reports/test-profile/20260821T112339-visual.log:14-38` show Playwright
Node `write EPIPE`; postflight `ss` shows listener `127.0.0.1:8766` owned by
current-run PID/PGID `618454` after runner cleanup. These are not a trusted
green lifecycle receipt.
Required change: repair controlled runner/shared-harness lifecycle boundary
so actual child/PGID ownership, signal/wait/reap, server readiness/log events,
and EPIPE/PID disappearance evidence remain attributable without accepting or
terminating unrelated listeners. Preserve causal first failure and bounded
cleanup; no browser navigation retry or broad process/port cleanup.
Acceptance: focused controlled lifecycle contracts plus one canonical receipt
show no orphaned current-run listener, child-aware visual readiness, explicit
bounded race evidence, and all six lanes exit 0.

#### R2-F03 — BDD lane has 35 terminal failures without diagnosable failure evidence
Status: open
Requirement/task: `dev-tasks` “Full task concurrently preserves complete
coverage”; task 3.2.
Evidence: `reports/test-profile/20260821T112339-bdd.log:14-49` lists 35
terminal `FAILED` nodes, but provides no traceback or assertion cause before
runner reports PID disappearance. Classification: **Unknown**; available
receipt cannot distinguish T34 lifecycle regression from an unrelated BDD
failure. Do not guess or mask.
Required change: reproduce in controlled remediation and capture per-test
failure evidence, then fix confirmed T34 harness cause or document unrelated
environmental cause for owner decision; preserve every BDD node, serial lane,
and no-skip/no-xfail policy.
Acceptance: BDD lane has diagnosable output and exits 0 in same one-run
canonical receipt; if cause remains unknown, return BLOCKED rather than approve.

## Remediation 1/2 — R2 finding set

### Pre-edit boundary and controlled diagnosis

- `git diff HEAD~1` captured before remediation. Existing worktree includes
  unrelated application/config/F58 changes, `pyproject.toml`, visual baselines,
  T34/F58 dossiers, and prior T34 edits in mapped files. This remediation owns
  only `scripts/run_full_suite.py`, `tests/support/server.py`,
  `tests/support/browser.py`, `tests/conftest.py`, `tests/support/db.py`,
  `tests/scripts/test_t29_harness.py`, plus T34 `design.md`/`tasks.md` evidence.
  No existing hunk outside exact R2 runner/shared-harness boundaries is owned.
- Exact preflight inventory at `2026-08-21T11:45:37-03:00`: `/tmp/pytest-of-juca`
  absent; listener `127.0.0.1:8766` present as PID/PGID `618454`, parent PID
  `1`, command `/home/juca/github/omaha/.venv/bin/python3 -m uvicorn ...`.
  Classification `foreign`/pre-existing relative to remediation; no adoption,
  signal, kill, port free, deletion, or masking performed. Focused harness tests
  use no fixed canonical lane port.
- R2 duration attribution remains bounded: receipt
  `20260821T112339-618393` recorded lifecycle events through deadline/cleanup;
  it did not retain a phase-level reason for the 80-second monitor/deadline
  attribution gap. Remediation adds bounded wait and reserves cleanup margin;
  workload/task configuration remains unchanged.
- R2-F03 controlled evidence before remediation remains unknown: BDD log had
  35 terminal `FAILED` lines without traceback, while e2e/visual logs showed
  Playwright `write EPIPE` and postflight showed detached BDD server residue.
  No BDD rerun is authorized while foreign `8766` listener remains; no product,
  feature, or BDD test edit is made.

### Implementation evidence

- `scripts/run_full_suite.py`: bounded final child wait; cleanup deadline now
  reserves grace plus bounded wait; per-lane receipt parses
  `T29_TEST_FAILURE` traceback records and retains them with run/lane evidence.
  Lane topology, taskipy commands, ports, DB allow-list, coverage, skips,
  fail-fast, and 300-second ceiling remain unchanged.
- `tests/support/server.py` / `tests/support/browser.py`: shared uvicorn no
  longer detaches from lane-owned process group; direct child teardown is used
  when server PGID equals parent lane PGID; launch/readiness/teardown events
  retain parent/child/PGID/port state and are published to lane output.
- `tests/conftest.py` / `tests/support/db.py`: exact runner temp boundary is
  published before collection on its own line; session fixture avoids duplicate
  matching receipt; failure hook emits one structured traceback record per failed
  test with run/lane/PID/PGID.
- `tests/scripts/test_t29_harness.py`: adds parser contract for per-test
  failure evidence and updates controlled child wait double for bounded wait.

### Focused validation ownership ledger — remediation 1/2

Run ID: `t34-remediation1-focused-20260821T114537-0300`
Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58` / `apply`
Owner evidence: ledger registration in this section before taskipy launch;
timestamp `2026-08-21T11:45:37-03:00`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | to be assigned by taskipy invocation | T34 remediation 1/2 apply | current run registration before launch | pending | pending | pending | owned-current-run | focused harness pytest child only | cleanup exact child/group after exit |
| process group | to be assigned by taskipy invocation | T34 remediation 1/2 apply | current run registration before launch | pending | pending | pending | owned-current-run | current taskipy wrapper group only | cleanup exact group or idempotent absent no-op |
| test DB resource | dynamic pytest safe DB | T34 remediation 1/2 apply | pytest session fixture in current invocation | pending | pending | pending | owned-current-run | test-only DB; no production DB target | fixture teardown only |
| temporary path | pytest current-session temp paths | T34 remediation 1/2 apply | pytest invocation/fixture ownership | pending | pending | pending | owned-current-run | no broad `/tmp` discovery | fixture teardown only |
| port | controlled ephemeral stale-listener socket | T34 remediation 1/2 apply | T29 test creates socket before use | pending | pending | pending | owned-current-run | no fixed 8765-8768 port use | test closes exact socket or absent no-op |

No cleanup target includes foreign listener `127.0.0.1:8766` PID/PGID
`618454`; it remains untouched. Final timestamps, classifications, evidence,
and bounded cleanup results are appended after validation.

Focused rerun registration: `t34-remediation1-focused2-20260821T114700-0300`,
owner `T34 remediation 1/2 apply`, registered before launch. Exact owned
temporary boundary `/home/juca/github/omaha/reports/test-profile/.t34-remediation1-focused2-pytest`
is registered before use; no fixed lane port is registered. Wrapper PID/PGID
and start timestamp are emitted by the owner registration line immediately
before `exec uv run task test-file tests/scripts/test_t29_harness.py`.

### Remediation validation results and finding disposition

- Focused taskipy run `t34-remediation1-focused-20260821T114537-0300`:
  wrapper PID/PGID `622036`, owner registration `2026-08-21T11:46:42-03:00`,
  exited `2026-08-21T11:46:43-03:00`; command
  `uv run task test-file tests/scripts/test_t29_harness.py` -> `58 passed in
  0.53s`. Child/group classification `owned-cleaned`; already exited, no
  signal/kill needed. First run created `/tmp/pytest-of-juca`, but exact parent
  path was not registered before use; classify `unknown` and leave untouched.
  Foreign listener `127.0.0.1:8766` PID/PGID `618454` remained untouched.
- Focused taskipy run `t34-remediation1-focused2-20260821T114700-0300`:
  wrapper PID/PGID `622250`, owner registration `2026-08-21T11:48:03-03:00`,
  exited `2026-08-21T11:48:07-03:00`; command
  `env T29_RUN_ID=... T29_DB_RECEIPT_LANE=unit PYTEST_ADDOPTS=--basetemp=...`
  `uv run task test-file tests/scripts/test_t29_harness.py` -> `58 passed in
  2.21s`. Exact registered boundary
  `/home/juca/github/omaha/reports/test-profile/.t34-remediation1-focused2-pytest`
  was `owned-current-run`, then exact cleanup returned absent;
  classification `owned-cleaned`, bounded exact cleanup only. No fixed
  canonical port was used. Dynamic safe test DB identity was not emitted by
  non-`-s` focused task output; classify DB receipt `unknown/incomplete` and do
  not scan or clean `/tmp`.
- Focused lint `t34-remediation1-lint-20260821T115000-0300`: PID/PGID
  `622513`, registration `2026-08-21T11:49:17-03:00`, exited nonzero on import
  ordering only; no resource residue. Surgical import-order correction applied
  in `tests/support/server.py`.
- Focused lint `t34-remediation1-lint2-20260821T115000-0300`: PID/PGID
  `622589`, registration `2026-08-21T11:49:30-03:00`, exited
  `owned-cleaned`; command
  `uv run ruff check scripts/run_full_suite.py tests/support/server.py
  tests/support/browser.py tests/conftest.py tests/support/db.py
  tests/scripts/test_t29_harness.py` -> `All checks passed!`.

R2-F01: **attributable correction complete; canonical acceptance pending**.
Exact temp marker newline/module-load publication fixes parser loss; runner
bounded wait/deadline margin fixes cleanup attribution. No workload, taskipy,
coverage, skip, lane, or timeout policy tuning. Review task 3.2 still requires
one trusted canonical receipt for `<=300s`, six lanes, coverage/skips, and exact
reconciliation.

R2-F02: **attributable correction complete; canonical acceptance pending**.
Shared server no longer detaches from lane-owned group; direct teardown avoids
signaling parent group; structured launch/readiness/teardown events reach lane
output; focused harness contracts and lint pass. Existing foreign listener
`127.0.0.1:8766` PID/PGID `618454` remains untouched, so no canonical lifecycle
rerun is authorized in this environment.

R2-F03: **BLOCKED_FOR_IMPLEMENTATION_BRIEF**. Runner/conftest now retain
run/lane/PID/PGID per-test traceback records and server lifecycle output, but no
controlled BDD reproduction was safe while foreign `8766` listener exists.
Historical BDD 35 failures therefore remain causally unknown; no BDD test,
feature, product, retry, skip, xfail, or lane change was made. Owner must provide
isolated runner/environment, then review may perform one canonical suite and
classify BDD cause from emitted evidence.

### Remediation ownership receipt

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `622036` | T34 remediation 1/2 apply | owner registration before taskipy exec | 2026-08-21T11:46:42-03:00 | 2026-08-21T11:46:43-03:00 | exited | owned-cleaned | 58 focused tests passed | already exited; no signal/kill |
| process group | PGID `622036` | T34 remediation 1/2 apply | wrapper PGID printed before exec | 2026-08-21T11:46:42-03:00 | 2026-08-21T11:46:43-03:00 | exited | owned-cleaned | taskipy wrapper group | idempotent no-op |
| child process | PID `622250` | T34 remediation 1/2 apply | owner registration before taskipy exec | 2026-08-21T11:48:03-03:00 | 2026-08-21T11:48:07-03:00 | exited | owned-cleaned | 58 focused tests passed | already exited; no signal/kill |
| process group | PGID `622250` | T34 remediation 1/2 apply | wrapper PGID printed before exec | 2026-08-21T11:48:03-03:00 | 2026-08-21T11:48:07-03:00 | exited | owned-cleaned | taskipy wrapper group | idempotent no-op |
| temporary path | `/home/juca/github/omaha/reports/test-profile/.t34-remediation1-focused2-pytest` | T34 remediation 1/2 apply | exact path registered before use; stat owner `juca:juca`, mtime `11:48:07` | 2026-08-21T11:48:03-03:00 | 2026-08-21T11:48:18-03:00 | cleanup-attempted | owned-cleaned | exact current-run path only | bounded exact removal; absent after cleanup |
| temporary path | `/tmp/pytest-of-juca` | T34 remediation 1/2 apply | observed after first run; exact identity not registered before use | 2026-08-21T11:46:44-03:00 | 2026-08-21T11:49:30-03:00 | present | unknown | stat showed relevant directory | untouched; safe stop, no adoption |
| port | `127.0.0.1:8766`, PID/PGID `618454` | prior review/foreign run | exact `ss` + `ps`, parent PID `1` | pre-existing | 2026-08-21T11:49:30-03:00 | active | foreign | unrelated detached uvicorn listener | untouched; no kill/free/adoption |
| child process | PID `622513` | T34 remediation 1/2 apply | owner registration before lint exec | 2026-08-21T11:49:17-03:00 | 2026-08-21T11:49:17-03:00 | exited | owned-cleaned | import-order diagnostic | already exited; no cleanup |
| process group | PGID `622513` | T34 remediation 1/2 apply | wrapper PGID printed before lint exec | 2026-08-21T11:49:17-03:00 | 2026-08-21T11:49:17-03:00 | exited | owned-cleaned | lint wrapper group | idempotent no-op |
| child process | PID `622589` | T34 remediation 1/2 apply | owner registration before lint exec | 2026-08-21T11:49:30-03:00 | 2026-08-21T11:49:31-03:00 | exited | owned-cleaned | ruff all checks passed | already exited; no cleanup |
| process group | PGID `622589` | T34 remediation 1/2 apply | wrapper PGID printed before lint exec | 2026-08-21T11:49:30-03:00 | 2026-08-21T11:49:31-03:00 | exited | owned-cleaned | lint wrapper group | idempotent no-op |

Cleanup decision: exact current-run process/groups and registered temp path
cleaned/no-op. Unknown `/tmp/pytest-of-juca` and foreign `8766` listener left
untouched. Any canonical review preflight finding either resource MUST safe-stop
and request isolated environment; no baseline or allowlist exception.

Focused acceptance: `58 passed` and targeted ruff clean. No canonical
`uv run task test` run by apply; task 3.2 remains review-owned/open.

### Review R3

Scope audit: proposal pass; design pass; delta specs `dev-tasks` and
`shared-test-support` pass; tasks 1.1-1.2, 2.1-2.4, 3.1, and 3.3 pass by
artifact/static audit; task 3.2 **finding**; runner PID/PGID lifecycle pass;
visual/server lifecycle **finding**; exact pytest-temp ownership pass for this
run; BDD diagnostic evidence pass but BDD acceptance **finding**; scope boundary
pass. Excluded F58/product/BDD test changes, I08/T33, DB/seed/migrations,
retries/skips/xfails/lane changes, and unrelated cleanup. Stable change
validation `valid=true`; stable specs `70/70` valid (informational long-text
notices only).

Full suite: exactly one `uv run task test`, run ID `20260821T124708-625837`.
External wall clock `334.497s`, from `2026-08-21T12:47:07.846362719-03:00`
through `2026-08-21T12:52:42.370271137-03:00`; runner receipt elapsed
`333.95465493001393s`; exit `124`; duration limit `300s`; classification
**red and over ceiling**. Receipt: `reports/test-profile/20260821T124708-run.json`.
Lane results: unit `241`/SIGTERM deadline, integration `241`/SIGTERM deadline,
audit `241`/SIGTERM deadline, e2e `1`/process PID-not-found plus Playwright
EPIPE, bdd `1`/19 `T29_TEST_FAILURE` records, visual `1`/process PID-not-found
plus Playwright EPIPE. Unit/integration collected zero nodes before deadline;
audit collected 40 and stopped; e2e collected 51/one started node; BDD
collected 51/19 failed records before runner stop; visual collected 20/8
selected. Coverage unavailable; reported skips `[]`; manifest/node
reconciliation incomplete. Fail-fast/deadline disposition: deadline triggered,
remaining owned groups received SIGTERM, no retry/skip/xfail. Per-test BDD
tracebacks retained in `reports/test-profile/20260821T124708-bdd.log` and
receipt lines 8941 onward; first/root cause is `TypeError: a bytes-like object
is required, not 'str'` at `tests/support/server.py:36` while writing launch
event to binary `NamedTemporaryFile`.

Preflight: trusted after owner-authorized exact cleanup. Per-run ledger
`/tmp/t34-r3-review-ledger.jsonl` records all six relevant listeners and exact
`/tmp/pytest-of-juca`. Before cleanup, endpoint receipt proved
`127.0.0.1:8766` LISTEN owned by PID `618454`, PGID `618454`, PPID `1`, user
`juca`, command `/home/juca/github/omaha/.venv/bin/python3 -m uvicorn
omaha.main:app --host 127.0.0.1 --port 8766 --log-level warning`; `ss` showed
exact endpoint and `pid=618454`, so exact endpoint verification passed. Owner
authorized `kill -TERM 618454` only; post-receipt PID absent and port absent,
classification `owned-cleaned`. No group/name-pattern kill. Exact path metadata
before removal: directory `/tmp/pytest-of-juca`, owner `juca:juca`, mode `700`,
inode `1388056`, size `80`, birth `2026-08-21 11:46:44.989320772 -0300`, mtime
`2026-08-21 11:46:44.989320772 -0300`; owner-authorized `rm -rf --
/tmp/pytest-of-juca` only, post-stat absent, classification `owned-cleaned`.
Preflight after cleanup: ports `8765-8768` absent, exact path absent, no
unknown/pre-existing/foreign/contradictory relevant state.

Postflight: runner PID/PGID/child resources exited; exact six run-declared
pytest roots under `reports/test-profile/.20260821T124708-625837-*` all absent;
exact listeners `8765-8768` all absent; no postflight cleanup action taken.
Receipt itself marks unit/integration test DB ownership `unknown` because lanes
were terminated during collection, so cleanup verdict remains untrusted even
though exact pytest roots reconciled `owned-cleaned`. No foreign resource was
adopted or touched.

Server receipt: Docker `/omaha-web-1`, ID
`63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`, image
`omaha:dev`, published `0.0.0.0:8000` and `[::]:8000`, status `running`, health
`healthy`; `http://127.0.0.1:8000/healthz` returned
`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
No stop/restart or DB mutation performed; service remained restored.

Verdict: **CHANGES_REQUESTED**. Red suite and elapsed wall clock exceed hard
300-second ceiling. No approval, archive, commit, push, or implementation edit.

#### R3-F01 — Canonical suite remains red and exceeds hard ceiling
Status: open
Requirement/task: `dev-tasks` Test coverage report and scenarios “Full task
concurrently preserves complete coverage” / “Deadline includes bounded
cleanup”; task 3.2; PRD §4.13; prior `R2-F01`.
Evidence: `reports/test-profile/20260821T124708-run.json:2-8,123-151` records
elapsed `333.95465493001393`, deadline, exit `124`, incomplete coverage/node
reconciliation, unit/integration DB residue classification `unknown`, and
external timing is `334.497s`. Lane summary is recorded above.
Required change: restore complete six-lane green execution within `<=300s`
through cleanup and emit complete coverage/skips/manifest, DB, PID/PGID,
visual, and exact-temp receipts. Preserve all tests, coverage, taskipy
entrypoints, lanes, fail-fast, and cleanup safety. Excluded scope: F58/product,
BDD feature/test edits, DB/seed/migrations, retries/skips/xfails, lane changes,
and broad cleanup.
Acceptance: one future canonical receipt has six exit-0 lanes, complete
coverage/skips/node reconciliation, no unknown cleanup/resource classification,
and external wall clock `<=300s`.

#### R3-F02 — Server event instrumentation writes text to binary log
Status: open
Requirement/task: `shared-test-support` Requirement “Shared test-server
lifecycle preserves lane ownership”, dead-child/readiness scenarios; task 2.2;
prior `R2-F02`/`R2-F03`.
Evidence: `reports/test-profile/20260821T124708-bdd.log:15-72` and
`reports/test-profile/20260821T124708-run.json:8941` onward show every BDD
startup fails at `tests/support/server.py:36` with
`TypeError: a bytes-like object is required, not 'str'`; `tests/support/browser.py:72`
returns binary `NamedTemporaryFile`, while `_server_event` performs
`log_handle.write(line + "\\n")` at `tests/support/server.py:36`. This is a
direct remediation-introduced code bug, not test drift or environmental
unknown. E2E/visual then report PID-not-found and Playwright EPIPE in their
lane logs.
Required change: correct only owned server-event log I/O so launch/readiness/
teardown events are emitted without TypeError, preserving binary subprocess
capture, exact host/port, child-aware readiness, bounded teardown, no browser
retry, and no BDD/product/test edits. Excluded scope: BDD feature/scenario
changes, E2E/visual behavior changes, broad process/port cleanup, and lane
policy.
Acceptance: focused server contracts plus future canonical receipt show launch,
readiness, exit, and teardown events for exact requested ports; BDD/e2e/visual
lanes run without this exception and all six lanes exit 0.

#### R3-F03 — Canonical receipt cannot prove complete DB/coverage acceptance
Status: open
Requirement/task: `dev-tasks` Requirements “Test coverage report” and “Full run
receipt”; task 3.2.
Evidence: `reports/test-profile/20260821T124708-run.json:97-105,136-151`
classifies unit/integration test DB resources `unknown` because collection was
terminated before complete lane receipts; coverage is unavailable and manifest
reconciliation is incomplete. Exact pytest roots are `owned-cleaned`, but this
does not satisfy complete receipt acceptance.
Required change: after fixing attributable lifecycle failure, ensure every lane
publishes complete DB, coverage, skip, node, and cleanup evidence before final
receipt; preserve production-DB guard and exact-only reconciliation. Excluded
scope: production DB/seed/migrations, test removal, coverage reduction, retries,
skips, xfails, or broad cleanup.
Acceptance: future single canonical receipt reports complete non-unknown DB and
coverage evidence, exact six-lane node/skip reconciliation, and all resource
classifications trusted.

## Remediation 2/2 — R3 finding set

### Pre-edit boundary

- Captured `git diff HEAD~1` before this remediation. Existing worktree changes
  include prior T34 runner/shared-harness edits, unrelated F58/MyProfit/product
  files, `pyproject.toml`, visual baselines, and active OpenSpec dossiers.
- This final remediation owns only the direct R3 correction in
  `tests/support/server.py` and its focused contract in
  `tests/scripts/test_t29_harness.py`. `tests/support/browser.py` and
  `scripts/run_full_suite.py` were inspected but require no edit: R3 proves
  their PID/PGID/readiness and deadline behavior was downstream of the server
  TypeError. No F58/MyProfit/product/BDD test or feature, I08/T33, DB/seed/
  migration, config, topology, or live service change is owned.

### Validation ownership registration — remediation 2/2

- Run ID: `t34-remediation2-focused-20260821T133754-0300`
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`
- Owner evidence: this registration was written before focused taskipy launch;
  registration timestamp `2026-08-21T13:37:54-03:00`.
- Registered resources before use: taskipy/pytest child and process group,
  pytest-owned test-only DB/temp paths, and exact fixture-owned temporary
  files. No Omaha LAN process, canonical lane listener, production DB, or
  unrecorded path is a cleanup target.
- Exact pytest boundary registered before launch:
  `reports/test-profile/.t34-remediation2-focused-pytest`.
- Cleanup rule: classify only exact current-run ledger entries; clean owned
  entries or record idempotent absent/no-op. Leave foreign, pre-existing,
  unknown, or contradictory resources untouched.

- Lint run ID: `t34-remediation2-lint-20260821T133920-0300`
- Lint owner evidence: registration timestamp
  `2026-08-21T13:39:20-03:00`, before taskipy launch; only taskipy/prek child
  and process group plus no test DB/temp/listener resource expected.
- `uv run task lint -- tests/support/server.py tests/scripts/test_t29_harness.py`
  exited before lint: repository has no `prek.toml` or
  `.pre-commit-config.yaml`. No implementation failure or resource residue;
  taskipy/prek wrapper PID `628972`, PGID `628972`, started
  `2026-08-21T13:39:34-03:00`, exited immediately and was not retried.
- Direct targeted Ruff fallback registration ID:
  `t34-remediation2-ruff-20260821T133959-0300`; owner evidence recorded before
  launch at `2026-08-21T13:39:59-03:00`.

### Remediation 2/2 validation results

- `uv run task test-file tests/scripts/test_t29_harness.py` with registered
  `PYTEST_ADDOPTS=--basetemp=reports/test-profile/.t34-remediation2-focused-pytest`
  -> **59 passed in 2.25s**. This includes
  `test_server_event_writes_binary_log_handle`; binary event encoding prevents
  the R3 TypeError while existing launch/readiness/teardown contracts remain
  green.
- Exact focused pytest boundary was present after the run, classified
  `owned-current-run` from prior registration and exact path identity, then
  removed by bounded exact cleanup; final state `absent` / `owned-cleaned`.
  PID/PGID `628806` was absent at post-run inventory; ports `8765-8768` had no
  listeners. No foreign or unknown resource was touched.
- `uv run task lint -- tests/support/server.py tests/scripts/test_t29_harness.py`
  could not enter lint because this checkout has no `prek.toml` or
  `.pre-commit-config.yaml`; taskipy wrapper PID/PGID `628972` exited
  immediately. No retry or config edit was made.
- Targeted lint fallback
  `uv run ruff check tests/support/server.py tests/scripts/test_t29_harness.py`
  -> **All checks passed!**. `git diff --check` -> clean. OpenSpec change
  validation -> `valid=true`.

### R3 finding disposition

- **R3-F01:** attributable startup blocker removed only. No runner script,
  timeout, workload, lane, coverage, skip, fail-fast, or cleanup-policy edit.
  Canonical `<=300s` and six-lane green receipt remain review task 3.2 evidence.
- **R3-F02:** corrected in `tests/support/server.py::_server_event`; binary
  `NamedTemporaryFile` payload now receives bytes, text controlled handles
  remain supported, and focused regression passes.
- **R3-F03:** downstream PID-not-found/EPIPE and incomplete lane receipts are
  attributable to child startup failure at R3-F02. No BDD/E2E/visual test or
  feature changed; canonical complete DB/coverage/skip/node receipt remains
  review-owned task 3.2 evidence.

### Resource ownership receipt — remediation 2/2

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `628806` | T34 remediation 2/2 apply | wrapper printed PID before `exec uv run task`; run registration above | 2026-08-21T13:38:50-03:00 | 2026-08-21T13:38:56-03:00 | exited | owned-cleaned | 59 focused tests passed; post-run PID absent | idempotent no-op; already exited |
| process group | PGID `628806` | T34 remediation 2/2 apply | wrapper printed PGID before exec | 2026-08-21T13:38:50-03:00 | 2026-08-21T13:38:56-03:00 | exited | owned-cleaned | no fixed lane listener; no signal operation | idempotent no-op; already exited |
| temporary path | `reports/test-profile/.t34-remediation2-focused-pytest` | T34 remediation 2/2 apply | exact path registered before launch; stat owner `juca:juca`, mode `700` | 2026-08-21T13:38:50-03:00 | 2026-08-21T13:39:00-03:00 | cleanup-attempted | owned-cleaned | exact current-run path; no parent/broad `/tmp` discovery | exact `rm -rf --` bounded; absent after cleanup |
| test DB resource | no DB fixture allocated | T34 remediation 2/2 apply | focused module inventory; no production target | 2026-08-21T13:38:50-03:00 | 2026-08-21T13:38:56-03:00 | absent | absent | focused harness tests used controlled paths only | idempotent no-op; absent |
| port | `8765-8768` | T34 remediation 2/2 apply | exact post-run `ss` inventory; focused module used no canonical listener | 2026-08-21T13:38:56-03:00 | 2026-08-21T13:38:56-03:00 | absent | absent | no relevant listener observed | idempotent no-op; untouched |
| child process | PID `628972` | T34 remediation 2/2 apply | wrapper printed PID before `exec uv run task lint` | 2026-08-21T13:39:34-03:00 | 2026-08-21T13:39:34-03:00 | exited | owned-cleaned | missing prek config stopped before lint | idempotent no-op; already exited |
| process group | PGID `628972` | T34 remediation 2/2 apply | wrapper printed PGID before exec | 2026-08-21T13:39:34-03:00 | 2026-08-21T13:39:34-03:00 | exited | owned-cleaned | no child/resource residue | idempotent no-op; already exited |
| child process | PID `629125` | T34 remediation 2/2 apply | wrapper printed PID before `exec uv run ruff check` | 2026-08-21T13:40:13-03:00 | 2026-08-21T13:40:13-03:00 | exited | owned-cleaned | targeted Ruff passed | idempotent no-op; already exited |
| process group | PGID `629125` | T34 remediation 2/2 apply | wrapper printed PGID before exec | 2026-08-21T13:40:13-03:00 | 2026-08-21T13:40:13-03:00 | exited | owned-cleaned | no child/resource residue | idempotent no-op; already exited |

Cleanup decision: exact current-run process groups were already absent; exact
pytest boundary was cleaned. No foreign/pre-existing/unknown resource was
adopted, killed, freed, deleted, or allowlisted. No canonical suite was run by
apply; review task 3.2 remains the single full-suite gate.

### Scope-only diff boundary

- This remediation adds one type-correction branch in
  `tests/support/server.py::_server_event`, one regression test in
  `tests/scripts/test_t29_harness.py`, and durable T34 evidence/decision text.
- `tests/support/browser.py` and `scripts/run_full_suite.py` retain prior
  content; no unrelated worktree hunk is claimed by this pass.

## Review Findings

### Review R4

Scope audit: proposal **pass**; design **pass**; delta specs
`dev-tasks`/`shared-test-support` **pass**; task completion **finding** (task
3.2 remains unchecked); binary server-event write **pass** by focused evidence;
owned child/readiness/teardown lifecycle **finding** from canonical readiness and
PID receipts; PID/PGID receipts **pass** for launched lane groups but acceptance
**finding** because two lanes became untrusted; per-lane pytest-temp
reconciliation **pass** (all six exact roots `owned-cleaned`); failure
preservation/no masking **pass** (deadline and nonzero lane results retained);
six-lane topology/task/coverage/skip boundary **pass** by static audit;
canonical six-lane acceptance **finding**; scope boundary **pass** (T34 mapped
runner/harness files and T34 dossier only; unrelated worktree changes excluded);
stable change/spec validation **pass** (`valid=true`, stable specs `70/70`);
LAN service identity/health **pass**. No F58/MyProfit/product/BDD test or
feature, I08/T33, DB/seed/migration, retry/skip/xfail, lane topology, timeout
tuning, archive, commit, push, or broad cleanup was performed by review.

Full suite: exactly one `uv run task test`, run ID
`20260821T134451-629990`, receipt
`reports/test-profile/20260821T134451-run.json`. Receipt elapsed
`281.75858117701137s`, limit `300.0s`, `duration_exceeded=false`,
`deadline_triggered=true`; canonical result **red**, not approval-eligible.
The external wrapper was started with wall-clock capture, but its final metadata
print failed after suite exit because timing variables were not exported; the
durable runner elapsed value is retained as available duration evidence.
Six lanes: unit `241`/SIGTERM deadline; integration `241`/SIGTERM deadline;
audit `1`/process PID-not-found after 40 collected items; e2e `241`/SIGTERM
deadline; bdd `241`/SIGTERM deadline after 14 structured failures and server
readiness timeout; visual `1`/process PID-not-found plus Playwright EPIPE.
Coverage unavailable; reported skips `[]`; unit/integration stopped during
collection, audit stopped after 40 items, browser lanes did not complete, and
manifest/node reconciliation is incomplete. Fail-fast/deadline disposition:
deadline triggered, remaining owned groups received SIGTERM, groups were
reaped, no retry/skip/xfail or failure masking occurred. Six lanes did not exit
0. Test gate classification: **blocked by unknown/red lifecycle failures**;
`<=300s` duration alone does not pass.

Preflight: ledger `/tmp/t34-r4-review-ledger.jsonl`, recorded
`2026-08-21T13:44:16-03:00`, before standards/spec audit and suite launch.
Relevant runner/pytest/Playwright/uvicorn process inventory was absent; ports
`8765-8768` were absent; exact `/tmp/pytest-of-juca` was absent. Every ledger
row contains required resource identity, owner evidence, timestamps, status,
classification, evidence, and cleanup result. Classifications:
process absent, listeners absent, temp path absent. No unknown,
pre-existing, foreign, contradictory, or incomplete state; runner isolation
precondition **passed**. No resource was adopted, killed, freed, deleted, or
allowlisted.

Postflight: recorded `2026-08-21T13:50:29-03:00` in same ledger. Lane child
PIDs/PGIDs `629991`, `629994`, `629996`, `629999`, `630002`, `630005` were
absent; all six exact receipt-declared pytest roots were absent after
`exact-root-removed`; listeners `8765-8768` were absent. Current-run process,
group, listener, and temp classifications were `owned-cleaned`/`absent` with
no residue. Receipt still marks unit/integration test DB ownership `unknown`
because collection terminated before lane DB receipt, so cleanup is not a
trusted full-suite acceptance. No foreign resource was touched.

Runner isolation: precondition passed before launch; postflight host residue
was clean. Isolation does not override red lanes, unknown DB ownership, missing
coverage, or incomplete reconciliation.

LAN receipt: exact Docker resource `/omaha-web-1`, ID
`63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`, image
`omaha:dev`, remained `running`/`healthy`; `http://127.0.0.1:8000/healthz`
returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
No stop/restart was required or performed; service identity was checked before
and after suite, and no LAN service mutation occurred.

Verdict: **BLOCKED**

#### R4-F01 — Canonical suite red; complete acceptance not proven
Status: blocked
Requirement/task: `dev-tasks` Test coverage report and scenarios “Full task
concurrently preserves complete coverage” / “Deadline includes bounded
cleanup”; task 3.2; PRD §4.13; prior `R3-F01`/`R3-F03`.
Evidence: `reports/test-profile/20260821T134451-run.json:2-8,97-151` records
six nonzero lane outcomes, `deadline_triggered=true`, unit/integration DB
classification `unknown`, unavailable coverage, incomplete reconciliation, and
elapsed `281.75858117701137s`; lane logs show audit PID-not-found and browser
failures. Failure classification: **Unknown** for aggregate acceptance because
receipt cannot establish whether all lane failures share one attributable T34
cause; no green run exists.
Required change: owner must provide isolated diagnostic decision or approved
remediation direction; do not request or perform third repair pass here. Future
acceptance must retain all tests and topology, produce six exit-0 lanes,
complete coverage/skips/manifest and DB receipts, trusted cleanup, and external
wall-clock `<=300s`. Excluded scope: F58/product/BDD edits, DB/seed/migrations,
retries/skips/xfails, lane or timeout tuning, broad cleanup.
Acceptance: one trusted canonical receipt satisfying every task 3.2 condition.

#### R4-F02 — Audit and integration lifecycle evidence remains unexplained
Status: blocked
Requirement/task: `dev-tasks` PID lineage and vanished-child scenarios; task
2.1/3.2; prior `R3-F01`.
Evidence: `20260821T134451-audit.log:46` ends with `process PID not found
(pid=630022)` after 40 collected audit items and lane exit `1`; integration
log `20260821T134451-integration.log:14` ends during collection, while receipt
marks unit/integration DB ownership `unknown` after deadline. Receipt proves
launched child/PGID identity and reaping, but does not identify source of the
PID-not-found text or prove complete child/DB lifecycle. Failure
classification: **Unknown**; available evidence cannot distinguish runner
boundary regression from lane/environment failure.
Required change: owner decision in isolated environment; if implementation is
authorized later, capture source-attributed process/lane event and complete DB
receipt without changing topology or masking the failure. No third remediation
pass requested by this review. Excluded scope: audit/integration test edits,
F58/product, retries/skips/xfails, broad cleanup.
Acceptance: controlled lifecycle evidence attributes PID disappearance and a
canonical receipt has non-unknown DB ownership for every lane.

#### R4-F03 — Shared server readiness and browser lanes remain untrusted
Status: blocked
Requirement/task: `shared-test-support` lifecycle scenarios “fails on dead
child”/“tears down deterministically”; `dev-tasks` interrupted-child scenario;
task 2.2/3.2; prior `R3-F02`/`R3-F03`.
Evidence: `20260821T134451-bdd.log:16-25` and
`tmp/uvicorn-logs/bdd-live-url-y9af4auy.log:1-3` show binary event write now
works and launch/teardown events are emitted, but `127.0.0.1:8766` timed out
after 30s while child return code was null and captured server log had no
startup output; BDD produced 14 `T29_TEST_FAILURE` records. Visual
`20260821T134451-visual.log:15-40` reports PID-not-found and Playwright EPIPE;
e2e has the same deadline/EPIPE family in receipt. Failure classification:
**Unknown**; no child startup exception or foreign listener evidence identifies
T34 code as cause, and review cannot guess after remediation 2/2.
Required change: owner must supply isolated attribution or approve future
implementation work; do not alter browser navigation, timeout, lane topology,
or BDD/E2E/visual tests in this gate. Excluded scope: product/BDD feature
changes, retries/skips/xfails, broad process/port cleanup.
Acceptance: child-aware launch/readiness/exit/teardown evidence for exact
ports, no EPIPE/PID-not-found failure, and all browser lanes exit 0 in one
trusted canonical run.

## Owner-authorized controlled remediation 3/3

Owner authorized one exception beyond normal remediation limit. Scope is
restricted to diagnosis of R4-F01/R4-F02/R4-F03 and one evidence-confirmed
runner/shared-harness correction, if any. Canonical `uv run task test` remains
review-owned and is prohibited in this pass.

### Pre-edit boundary and isolated focused-run preflight

- `git diff HEAD~1` captured before this pass. Existing hunks include prior
  T34 runner/shared-harness work, unrelated application/F58/config files,
  visual baselines, and active dossiers. This pass owns only mapped T34
  runner/shared-harness files plus T34 `design.md`/`tasks.md`; no existing
  hunk outside confirmed R4 repair is owned.
- Preflight at `2026-08-21T15:27:19-03:00`: relevant
  `scripts.run_full_suite`/pytest/Playwright/uvicorn process inventory absent;
  ports `8765-8768` absent; `/tmp/pytest-of-juca` absent. The only matching
  `pgrep` row was the inventory shell itself. Classification: process
  `absent`, listeners `absent`, temporary path `absent`. No foreign,
  pre-existing, unknown, contradictory, or incomplete resource found; no
  adoption, kill, port free, deletion, or allowlist exception.
- Focused-run ownership registration before launch:
  run IDs `t34-remediation3-audit-20260821T152719-0300`,
  `t34-remediation3-bdd-20260821T152719-0300`, and
  `t34-remediation3-visual-20260821T152719-0300`; owner
  `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 /
  apply`; exact taskipy wrapper PID/PGID assigned by each `setsid` launch;
  exact basetemp paths under `reports/test-profile/` registered per lane;
  audit dynamic safe DB identity to be emitted by current lane; BDD
  `data/test_bdd.db`; visual `data/test_visual.db`; BDD port `8766`; visual
  port `8768`. No production DB, LAN service, MyProfit, or unrelated port is
  a cleanup target.
- Cleanup decision: only exact current-run wrapper/group and registered
  basetemp entries may be reconciled. Foreign, pre-existing, unknown, or
  contradictory resources remain untouched and trigger safe stop.

### Focused diagnosis plan

- Reproduce audit, BDD, and visual lanes only through taskipy entrypoints with
  run/lane env, exact `--basetemp`, `-s`, and profile receipt output.
- Capture parent/child/PGID, launch, poll, signal, wait, exit, stdout/stderr,
  exact port/readiness, server log, and per-test traceback evidence. Do not
  run canonical full suite or alter product/BDD feature/test files.

### Focused remediation 3/3 results

- First audit invocation was bounded and failed before pytest collection because
  the diagnostic command omitted the runner's `PYTHONPATH=scripts` export:
  `uv run task test-audit-integration -- -s -p test_profile_plugin` -> exit 1,
  stderr `ModuleNotFoundError: No module named 'test_profile_plugin'`. Outer
  PID/PGID `635652/635652` exited at `2026-08-21T15:28:26-03:00`; no test DB,
  temp root, listener, or child residue. This is invocation evidence, not a
  product or harness failure. Corrected reproduction used `PYTHONPATH` only
  as the runner's documented child environment does.
- Audit corrected reproduction:
  `PYTHONPATH=./scripts T29_RUN_ID=t34-remediation3-audit2-20260821T152834-0300
  T29_DB_RECEIPT_LANE=audit PYTEST_ADDOPTS=--basetemp=reports/test-profile/.t34-remediation3-audit2-pytest
  uv run task test-audit-integration -- -s -p test_profile_plugin` -> **40
  passed in 31.69s**, outer PID/PGID `635745/635745`, parent wrapper PID
  `635743`, launch `15:28:52`, polls each second, wait exit 0 at `15:29:27`.
  Stdout contains exact dynamic DB
  `/tmp/omaha-conftest-safe-bvddwbdv/portfolio.db` and one exact run/lane temp
  receipt. Stderr contains expected child test diagnostic
  `audit FAIL: FileNotFoundError ... nonexistent.css` while the corresponding
  test passes; no `process PID not found` occurred.
- BDD reproduction:
  `PYTHONPATH=./scripts T29_RUN_ID=t34-remediation3-bdd-20260821T152719-0300
  T29_DB_RECEIPT_LANE=bdd PYTEST_ADDOPTS=--basetemp=reports/test-profile/.t34-remediation3-bdd-pytest
  uv run task test-bdd -- -s -p test_profile_plugin` -> **51 passed in
  155.39s**, outer PID/PGID `635938/635938`, parent wrapper PID `635936`,
  launch `15:29:50`, poll/wait exit 0 at `15:32:29`. Pytest PID `635951`,
  server child PID `635957`, server PGID `635938`; exact `127.0.0.1:8766`
  launch/readiness events are present in stdout after wrapper launch at
  `15:29:50`, followed by teardown-start,
  teardown-complete return `-15`, `port_free=true`. No BDD traceback,
  EPIPE, or PID-not-found; all 51 nodes pass, no skip/xfail.
- Visual reproduction:
  `PYTHONPATH=./scripts T29_RUN_ID=t34-remediation3-visual-20260821T152719-0300
  T29_DB_RECEIPT_LANE=visual PYTEST_ADDOPTS=--basetemp=reports/test-profile/.t34-remediation3-visual-pytest
  uv run task test-visual -- -s -p test_profile_plugin` -> **8 passed, 12
  deselected in 41.96s**, outer PID/PGID `637659/637659`, parent wrapper PID
  `637657`, launch `15:32:49`, poll/wait exit 0 at `15:33:35`. Pytest PID
  `637672`, server child PID `637781`, server PGID `637659`; exact
  `127.0.0.1:8768` launch at `15:32:57`, ready at `15:32:59`, teardown-start,
  teardown-complete return `-15`, `port_free=true`. No EPIPE or PID-not-found;
  all eight selected visual nodes pass. Existing 12 deselections are task
  selection, not introduced by T34.
- Postflight at `2026-08-21T15:33:44-03:00`: outer groups `635745`, `635938`,
  `637659`, pytest/server descendants, and ports `8765-8768` absent. Exact
  current-run temp roots were present after each lane and removed only by
  exact path at `2026-08-21T15:34:21-03:00`; all three final states absent.
  Audit dynamic test DB parent
  `/tmp/omaha-conftest-safe-bvddwbdv` was removed by exact path at
  `2026-08-21T15:34:29-03:00`; post-stat absent. BDD/visual fixed test DBs
  were pre-existing test resources and remained untouched.

### R4 finding disposition after remediation 3/3

- **R4-F01:** **BLOCKED_FOR_IMPLEMENTATION_BRIEF**. Focused audit/BDD/visual
  lanes pass, but canonical receipt remains red with `deadline_triggered=true`,
  six nonzero lanes, unknown unit/integration DB ownership, unavailable
  coverage, and incomplete manifest reconciliation at `281.75858117701137s`.
  This pass cannot run canonical `uv run task test`; no scoped runtime defect
  is proven and no timeout/topology/workload change is authorized.
- **R4-F02:** **BLOCKED_FOR_IMPLEMENTATION_BRIEF**. Audit reproduction passes
  40/40 with complete wrapper PID/PGID and wait/exit evidence, but R4's
  integration PID `630022`/unknown DB lifecycle was not reproduced because
  this gate authorizes audit/visual/BDD lanes only. Mapped files contain no
  source for literal `process PID not found`; no integration or runner repair
  can be proven without an isolated integration-only diagnostic decision.
- **R4-F03:** **Resolved for reproduced shared-harness boundary; canonical
  acceptance pending.** BDD 51/51 and visual 8/8 pass with exact child-aware
  `8766`/`8768` launch/readiness/teardown events, flushed server logs,
  `port_free=true`, no EPIPE, and no PID-not-found. No code edit is justified.
  One trusted canonical receipt is still required by review task 3.2.

### Remediation 3/3 ownership ledger receipt

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `635652` | T34 remediation 3/3 apply | registration before first audit launch; wrapper PID printed | 2026-08-21T15:28:24-03:00 | 2026-08-21T15:28:26-03:00 | exited | owned-cleaned | plugin-import failure before collection; no descendants | idempotent no-op; already exited |
| process group | PGID `635652` | T34 remediation 3/3 apply | `setsid` returned PGID equal to child PID | 2026-08-21T15:28:24-03:00 | 2026-08-21T15:28:26-03:00 | exited | owned-cleaned | same-run failed audit wrapper | idempotent no-op; already absent |
| child process | PID `635745` | T34 remediation 3/3 apply | registration before corrected audit launch; wrapper PID/PGID output | 2026-08-21T15:28:52-03:00 | 2026-08-21T15:29:27-03:00 | exited | owned-cleaned | 40 audit tests passed; wait return 0 | idempotent no-op; already exited |
| process group | PGID `635745` | T34 remediation 3/3 apply | exact `setsid` group identity | 2026-08-21T15:28:52-03:00 | 2026-08-21T15:29:27-03:00 | exited | owned-cleaned | no listener; no survivor | idempotent no-op; already absent |
| child process | PID `635951` | T34 remediation 3/3 apply | BDD stdout run/lane events and current wrapper lineage | 2026-08-21T15:29:52-03:00 | 2026-08-21T15:32:29-03:00 | exited | owned-cleaned | 51 BDD tests passed; server child `635957` exited `-15` | no signal by apply; fixture teardown reaped child |
| child process | PID `635957` | T34 remediation 3/3 apply | BDD launch event run/lane/child/PGID/port | 2026-08-21T15:29:52-03:00 | 2026-08-21T15:32:28-03:00 | exited | owned-cleaned | teardown return `-15`; exact port free | bounded fixture teardown; already absent |
| process group | PGID `635938` | T34 remediation 3/3 apply | `setsid` wrapper identity; server event confirms same PGID | 2026-08-21T15:29:50-03:00 | 2026-08-21T15:32:29-03:00 | exited | owned-cleaned | BDD wrapper and server shared group | idempotent no-op; already absent |
| child process | PID `637672` | T34 remediation 3/3 apply | visual stdout run/lane events and current wrapper lineage | 2026-08-21T15:32:52-03:00 | 2026-08-21T15:33:35-03:00 | exited | owned-cleaned | 8 selected visual tests passed; server child `637781` exited `-15` | no signal by apply; fixture teardown reaped child |
| child process | PID `637781` | T34 remediation 3/3 apply | visual launch event run/lane/child/PGID/port | 2026-08-21T15:32:57-03:00 | 2026-08-21T15:33:14-03:00 | exited | owned-cleaned | teardown return `-15`; exact port free | bounded fixture teardown; already absent |
| process group | PGID `637659` | T34 remediation 3/3 apply | `setsid` wrapper identity; server event confirms same PGID | 2026-08-21T15:32:49-03:00 | 2026-08-21T15:33:35-03:00 | exited | owned-cleaned | visual wrapper and server shared group | idempotent no-op; already absent |
| port | `127.0.0.1:8766` | T34 remediation 3/3 apply | BDD launch event requested exact port; postflight `ss` absent | 2026-08-21T15:29:52-03:00 | 2026-08-21T15:32:28-03:00 | exited | owned-cleaned | ready then `port_free=true` | fixture teardown freed exact current-run listener; absent |
| port | `127.0.0.1:8768` | T34 remediation 3/3 apply | visual launch event requested exact port; postflight `ss` absent | 2026-08-21T15:32:57-03:00 | 2026-08-21T15:33:14-03:00 | exited | owned-cleaned | ready then `port_free=true` | fixture teardown freed exact current-run listener; absent |
| temporary path | `reports/test-profile/.t34-remediation3-audit2-pytest` | T34 remediation 3/3 apply | exact path registered before audit launch; stat owner `juca:juca` | 2026-08-21T15:28:52-03:00 | 2026-08-21T15:34:21-03:00 | cleanup-attempted | owned-cleaned | exact root only | bounded exact removal; absent |
| temporary path | `reports/test-profile/.t34-remediation3-bdd-pytest` | T34 remediation 3/3 apply | exact path registered before BDD launch; stat owner `juca:juca` | 2026-08-21T15:29:50-03:00 | 2026-08-21T15:34:21-03:00 | cleanup-attempted | owned-cleaned | exact root only | bounded exact removal; absent |
| temporary path | `reports/test-profile/.t34-remediation3-visual-pytest` | T34 remediation 3/3 apply | exact path registered before visual launch; stat owner `juca:juca` | 2026-08-21T15:32:49-03:00 | 2026-08-21T15:34:21-03:00 | cleanup-attempted | owned-cleaned | exact root only | bounded exact removal; absent |
| test DB resource | `/tmp/omaha-conftest-safe-bvddwbdv/portfolio.db` | T34 remediation 3/3 apply | audit stdout exact `T29_DB_TARGET`; path created during current run | 2026-08-21T15:28:53-03:00 | 2026-08-21T15:34:29-03:00 | cleanup-attempted | owned-cleaned | dynamic test-only DB; no production target | bounded exact parent removal; absent |
| test DB resource | `/home/juca/github/omaha/data/test_bdd.db` | T34 remediation 3/3 apply | BDD stdout exact `T29_DB_TARGET`; fixed test DB pre-existed | 2026-08-21T15:29:50-03:00 | 2026-08-21T15:32:29-03:00 | exited | pre-existing | test-only fixed lane DB | untouched; foreign/pre-existing resource |
| test DB resource | `/home/juca/github/omaha/data/test_visual.db` | T34 remediation 3/3 apply | visual stdout exact `T29_DB_TARGET`; fixed test DB pre-existed | 2026-08-21T15:32:49-03:00 | 2026-08-21T15:33:35-03:00 | exited | pre-existing | test-only fixed lane DB | untouched; foreign/pre-existing resource |
| log | `reports/test-profile/t34-remediation3-{audit2,bdd,visual}.{stdout,stderr}.log` | T34 remediation 3/3 apply | paths created by current-run wrappers; exact names retained | 2026-08-21T15:28:24-03:00 | 2026-08-21T15:33:35-03:00 | exited | owned-current-run | stdout/stderr and traceback evidence retained | no deletion; durable evidence retained |
| child process | PID `638798` | T34 remediation 3/3 apply | lint registration before `setsid uv run ruff check`; wrapper PID/PGID output | 2026-08-21T15:36:52-03:00 | 2026-08-21T15:36:53-03:00 | exited | owned-cleaned | targeted Ruff exit 0 | idempotent no-op; already exited |
| process group | PGID `638798` | T34 remediation 3/3 apply | exact `setsid` group identity | 2026-08-21T15:36:52-03:00 | 2026-08-21T15:36:53-03:00 | exited | owned-cleaned | no child/resource residue | idempotent no-op; already absent |

Cleanup decision: owned current-run wrappers/groups, server children, exact
ports, dynamic audit DB, and exact basetemp paths exited or were cleaned. Fixed
BDD/visual test DBs stayed untouched as pre-existing test resources. No foreign,
unknown, production, LAN, or broad `/tmp` resource was adopted or changed.

Focused lint registration: run ID `t34-remediation3-lint-20260821T153500-0300`,
owner T34 apply, registration before launch; taskipy/ruff child and process
group only, no test DB/temp/listener resource expected.

- Targeted lint:
  `uv run ruff check scripts/run_full_suite.py tests/support/server.py
  tests/support/browser.py tests/conftest.py tests/support/db.py
  tests/scripts/test_t29_harness.py` -> **All checks passed!**. Wrapper
  PID/PGID `638798/638798`, parent `638796`, registered before launch at
  `2026-08-21T15:36:52-03:00`, wait exit 0 at `15:36:53`; no test resource,
  listener, or residue.
- `git diff --check` -> clean. Change strict validation -> `valid=true`;
  stable specs -> `70/70` valid with existing informational long-requirement
  notices. No implementation file changed in remediation 3/3; no focused
  regression was added because no mapped runtime defect was confirmed.

### Remediation 3/3 stop condition

Stop reached after authorized focused diagnosis. Do not run canonical
`uv run task test`, do not retry lane reproductions, and do not edit mapped
runtime code without new evidence. Review task 3.2 remains open; T34 cannot
return `READY_FOR_REVIEW` because R4-F01 aggregate acceptance and R4-F02
integration attribution remain unproven under this pass's authorized lane
boundary.

## Owner-authorized isolated integration remediation — R4-F02

### Pre-edit boundary and diagnosis registration

- Captured `git diff HEAD~1` before this pass with:
  `rtk git diff HEAD~1 --no-ext-diff --unified=0 -- scripts/run_full_suite.py
  tests/conftest.py tests/support/db.py tests/scripts/test_t29_harness.py`.
  Existing worktree boundaries remain those recorded above: prior T34 edits in
  mapped files, unrelated application/F58/config files, visual baselines, and
  active dossiers. This pass owns only the four files named by owner brief plus
  this dossier. `tests/test_admin_recovery.py` is read-only evidence; no server,
  browser, product, DB schema, seed, migration, task topology, or LAN change is
  owned.
- Isolated preflight at `2026-08-21T16:17:55-03:00`: canonical ports
  `8765-8768` had no listeners; exact `/tmp/pytest-of-juca` was absent; relevant
  process inventory had no pre-existing runner/pytest/Playwright/uvicorn child.
  Inventory command's own shell/python rows contained search terms and were
  excluded as self-observation. No foreign, pre-existing, unknown, or
  contradictory resource was adopted or changed.
- Diagnosis run registration before launch: run ID
  `t34-r4-integration-diagnosis-20260821T161755-0300`; owner
  `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 /
  apply`; exact pytest boundary
  `reports/test-profile/.t34-r4-integration-diagnosis-pytest`; exact temporary
  parent for fixture/Alembic resources
  `reports/test-profile/.t34-r4-integration-diagnosis-tmp`; owner evidence is
  this registration and `started_at` recorded before invocation. Planned
  resource IDs are wrapper PID/PGID and descendant identities captured before
  cleanup; no canonical listener, production DB, or unrecorded path is a
  cleanup target.
- Cleanup rule: reconcile only exact current-run wrapper/group, exact pytest
  boundary, and fixture-reported DB path under registered temporary parent.
  Foreign, pre-existing, unknown, contradictory, or unregistered resources
  remain untouched and cause safe stop.

### Focused integration diagnosis plan

- Run exactly one integration-only taskipy entrypoint using runner-equivalent
  child command, run/lane identity, `PYTHONPATH=./scripts`, `-s`, profile
  plugin, and exact `--basetemp`. Restrict collection to observed path
  `tests/test_admin_recovery.py`; do not edit that evidence file.
- Monitor wrapper → taskipy → pytest → conftest/Alembic subprocess lineage by
  PID/PPID/PGID, command, timestamp, poll/wait/return code, and receipt output.
  No canonical `uv run task test`, retry, broad process/port/tmp scan, or
  product/test behavior change.

### Diagnosis result and R4-F02 disposition

- Focused command (one integration diagnosis):
  `uv run task test-integration -- -s -p test_profile_plugin
  tests/test_admin_recovery.py` with `T29_RUN_ID`,
  `T29_DB_RECEIPT_LANE=integration`, runner-equivalent `PYTHONPATH=./scripts`,
  exact `PYTEST_ADDOPTS=--basetemp=reports/test-profile/.t34-r4-integration-diagnosis-pytest`,
  and `TMPDIR=reports/test-profile/.t34-r4-integration-diagnosis-tmp`.
  Result: **13 passed in 5.52s**, pytest reported 13 collected tests and no
  failure, signal, EPIPE, or `process PID not found`.
- Captured lineage: run/lane
  `t34-r4-integration-diagnosis-20260821T161755-0300` / `integration`;
  diagnostic monitor PID/PPID `641700/641697`, lane-wrapper command
  `uv run task test-integration -- -s -p test_profile_plugin
  tests/test_admin_recovery.py`, wrapper PID/PPID/PGID
  `641701/641700/641701`; launch `2026-08-21T16:19:23-03:00`, final poll
  `0` at `16:19:34-03:00`, wait return `0`, exit return `0`, elapsed `11.359s`.
  No signal was issued. Wrapper process became zombie after exit and was then
  absent; no descendant remained.
- Fixture linkage: conftest emitted
  `T29_DB_TARGET=reports/test-profile/.t34-r4-integration-diagnosis-tmp/omaha-conftest-safe-stmar_iw/portfolio.db`
  and exact `T29_TEMP_ROOT`, run ID, and lane receipts. `tests/support/db.py`
  maps fixture bootstrap to subprocess command
  `[sys.executable, "-m", "alembic", "upgrade", "head"]`; no separate
  Alembic PID was observed in the bounded process-tree snapshots. This missing
  child identity prevents claiming complete runner → pytest → Alembic PID
  attribution.
- PID `630022` was not reproduced. R4's exact source is audit log line
  `reports/test-profile/20260821T134451-audit.log:46`, not the integration log;
  permitted integration diagnosis therefore cannot distinguish audit tooling,
  runner, or external process ownership. No literal `process PID not found`
  source exists in permitted T34 files. **R4-F02 status: BLOCKED_FOR_IMPLEMENTATION_BRIEF**.
  Owner recommendation: authorize separate isolated audit-lane/source
  attribution or assign next runner/audit boundary slice; do not patch T34 on
  this non-reproduction.

### Diagnosis ownership receipt

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `641701` | T34 R4 integration diagnosis / apply | exact Popen PID/PPID/PGID printed immediately after launch under registered run ID | 2026-08-21T16:19:23-03:00 | 2026-08-21T16:19:34-03:00 | exited | owned-cleaned | taskipy integration wrapper; poll/wait/exit `0` | idempotent no-op; already absent after wait |
| process group | PGID `641701` | T34 R4 integration diagnosis / apply | `os.getpgid(641701)=641701` immediately after launch; `start_new_session=True` | 2026-08-21T16:19:23-03:00 | 2026-08-21T16:19:34-03:00 | exited | owned-cleaned | no signal required; no survivor | idempotent no-op; group absent |
| child process | diagnostic monitor PID `641700` | T34 R4 integration diagnosis / apply | current-run launcher PID printed before Popen; PPID `641697` | 2026-08-21T16:19:23-03:00 | 2026-08-21T16:19:34-03:00 | exited | owned-cleaned | monitor completed bounded poll/wait capture | idempotent no-op; already absent |
| test DB resource | `reports/test-profile/.t34-r4-integration-diagnosis-tmp/omaha-conftest-safe-stmar_iw/portfolio.db` | T34 R4 integration diagnosis / apply | exact `T29_DB_TARGET` emitted by current conftest session under registered `TMPDIR` parent | 2026-08-21T16:19:24-03:00 | 2026-08-21T16:19:35-03:00 | cleanup-attempted | owned-cleaned | test-only dynamic DB; no production path | removed with exact registered parent; post-stat absent |
| temporary path | `reports/test-profile/.t34-r4-integration-diagnosis-pytest` | T34 R4 integration diagnosis / apply | exact path registered before launch and matched three temp receipts | 2026-08-21T16:19:23-03:00 | 2026-08-21T16:19:35-03:00 | cleanup-attempted | owned-cleaned | exact current-run pytest basetemp | exact path removed; post-stat absent |
| temporary path | `reports/test-profile/.t34-r4-integration-diagnosis-tmp` | T34 R4 integration diagnosis / apply | exact path registered before fixture bootstrap; contained emitted DB only | 2026-08-21T16:19:23-03:00 | 2026-08-21T16:19:35-03:00 | cleanup-attempted | owned-cleaned | exact current-run TMPDIR boundary | exact parent removed; post-stat absent |
| port | `8765-8768` | T34 R4 integration diagnosis / apply | exact pre/post `ss` inventory; integration path opened no canonical listener | 2026-08-21T16:17:55-03:00 | 2026-08-21T16:19:35-03:00 | absent | absent | no relevant listener before or after | idempotent no-op; untouched |
| child process | PID `630022` | unknown / prior R4 run | prior R4 audit log text only; no current-run owner evidence | pre-existing evidence | not adopted | absent from current inventory | unknown | source/lane/parent/PGID unproven | untouched; safe stop, no adoption |

Cleanup decision: exact current-run wrapper, group, monitor, pytest root, and
fixture DB parent were cleaned or already absent. PID `630022`, foreign or
unknown resources, production DB, fixed lane ports, and unrelated paths were
untouched. Canonical review isolation still requires no relevant unowned
resource before review launch.

### Focused diagnosis stop condition

No runtime file or focused regression changed: integration equivalent passed,
PID `630022` remains unproven and R4 source is audit-lane text. Stop with
`BLOCKED_FOR_IMPLEMENTATION_BRIEF`; task 3.2 remains review-owned and open.

### Targeted lint registration

- Run ID `t34-r4-integration-lint-20260821T162000-0300`; owner T34 apply;
  registration before launch. Planned resources: one exact Ruff child/process
  group, no DB/temp/listener resource. Cleanup only exact child/group; no
  broad process operation.
- Targeted command:
  `uv run ruff check scripts/run_full_suite.py tests/conftest.py
  tests/support/db.py tests/scripts/test_t29_harness.py` -> **All checks
  passed!** Wrapper PID/PGID `642314/642314`, started
  `2026-08-21T16:23:11-03:00`, exited before postflight; exact PID/PGID absent
  at `2026-08-21T16:23:12-03:00`, idempotent no-op cleanup.
- `git diff --check` -> clean. OpenSpec change validation -> `valid=true`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `642314` | T34 R4 integration lint / apply | exact wrapper identity printed before `exec uv run ruff check` | 2026-08-21T16:23:11-03:00 | 2026-08-21T16:23:12-03:00 | exited | owned-cleaned | Ruff exit `0`; all checks passed | idempotent no-op; already absent |
| process group | PGID `642314` | T34 R4 integration lint / apply | exact `setsid` PGID printed before exec | 2026-08-21T16:23:11-03:00 | 2026-08-21T16:23:12-03:00 | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; already absent |

## Owner-authorized isolated audit attribution — R4-F02

### Pre-edit boundary and ownership registration

- Captured `git diff HEAD~1` before edits with
  `rtk git diff HEAD~1 --no-ext-diff --unified=0 -- scripts/run_full_suite.py
  tests/conftest.py tests/support/db.py tests/scripts/test_t29_harness.py`.
  Existing hunks remain pre-existing T34 work plus unrelated F58/MyProfit,
  product, config, visual, and active dossier changes. This pass owns only the
  four files named by owner brief plus T34 `design.md`/`tasks.md`; no audit test,
  fixture, task topology, or dependency file is editable.
- Isolated preflight at `2026-08-21T16:43:59-03:00`: canonical ports
  `8765-8768` absent; relevant runner/pytest/Playwright/uvicorn inventory absent
  after excluding inventory command self-observation; `/tmp/pytest-of-juca`
  absent. No foreign, pre-existing, unknown, contradictory, or incomplete
  relevant resource was adopted or changed.
- Diagnosis registration before launch: run ID
  `t34-audit-attribution-20260821T164359-0300`; owner
  `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 /
  apply`; exact pytest boundary
  `reports/test-profile/.t34-audit-attribution-20260821T164359-pytest`; exact
  `TMPDIR` parent
  `reports/test-profile/.t34-audit-attribution-20260821T164359-tmp`; stdout,
  stderr, timing, and process-tree logs under
  `reports/test-profile/t34-audit-attribution-20260821T164359.*`. Owner
  evidence and timestamps were recorded before resource launch. No canonical
  listener, production DB, or unrecorded path is a cleanup target.
- Cleanup decision: reconcile only exact current-run wrapper/group, exact
  pytest boundary, exact TMPDIR parent, and fixture-reported dynamic DB path.
  Foreign, pre-existing, unknown, contradictory, or unregistered resources stay
  untouched and force safe stop.

### Focused audit diagnosis plan

- Run one taskipy audit entrypoint only, with runner-equivalent `PYTHONPATH`,
  run/lane identity, `-s`, profile plugin, exact `--basetemp`, and exact
  `TMPDIR`. Monitor diagnostic wrapper → taskipy audit wrapper → pytest →
  conftest safe DB bootstrap → Alembic subprocess lineage by PID/PPID/PGID,
  command, timestamp, poll/wait/exit, and receipt output.
- Inspect directly invoked audit test/plugin and taskipy implementation only as
  evidence. Do not edit audit tests/fixtures, `pyproject.toml`, product/F58,
  DB/seed/migrations, or run canonical suite.

### Focused harness validation registration

- Run ID `t34-audit-attribution-harness-20260821T164650-0300`; owner T34/apply;
  registration timestamp `2026-08-21T16:46:50-03:00`, before launch. Planned
  resources: one exact taskipy/pytest wrapper process group, exact pytest
  basetemp `reports/test-profile/.t34-audit-attribution-harness-20260821T164650-pytest`,
  exact TMPDIR parent
  `reports/test-profile/.t34-audit-attribution-harness-20260821T164650-tmp`, and
  timing log `reports/test-profile/t34-audit-attribution-harness-20260821T164650.timings`.
  No fixed lane listener or production DB is a cleanup target.
- Cleanup: exact current-run wrapper/group and exact basetemp only; fixture DB
  resources remain test-only and are reconciled only when receipt identity is
  observed. Unknown/foreign/pre-existing resources remain untouched.

- The first harness invocation used unsupported `task-file` argument forwarding
  (`-- -s -p test_profile_plugin`), so pytest collected zero items and exited
  `4`; this is command-shape diagnosis, not a test result. Its exact wrapper
  group `645028` and TMPDIR parent were exited/cleaned with no residue. Correct
  focused command registration: run ID
  `t34-audit-attribution-harness2-20260821T164752-0300`, exact basetemp
  `reports/test-profile/.t34-audit-attribution-harness2-20260821T164752-pytest`,
  exact TMPDIR parent
  `reports/test-profile/.t34-audit-attribution-harness2-20260821T164752-tmp`,
  owner T34/apply, registered `2026-08-21T16:47:52-03:00` before launch.

### Targeted lint registration

- Run ID `t34-audit-attribution-lint-20260821T164850-0300`; owner T34/apply;
  registration timestamp `2026-08-21T16:48:50-03:00`, before launch. One exact
  Ruff child/process group and current-run log
  `reports/test-profile/t34-audit-attribution-lint-20260821T164850.log` only;
  no DB, temp, listener, or production resource is expected or a cleanup
  target.

### Audit attribution result

- Focused command, run exactly once:
  `PYTHONPATH=./scripts T29_RUN_ID=t34-audit-attribution-20260821T164359-0300
  T29_DB_RECEIPT_LANE=audit T29_PROFILE_PATH=reports/test-profile/t34-audit-attribution-20260821T164359.timings
  PYTEST_ADDOPTS=--basetemp=reports/test-profile/.t34-audit-attribution-20260821T164359-pytest
  TMPDIR=reports/test-profile/.t34-audit-attribution-20260821T164359-tmp
  uv run task test-audit-integration -- -s -p test_profile_plugin` -> **40
  passed in 31.13s**, outer wait/exit `0`, no signal, no `process PID not
  found` text. Audit stderr contains only expected `FileNotFoundError` diagnostic
  from `test_cli_missing_css_returns_nonzero`; corresponding test passed.
- Run/lane linkage: `t34-audit-attribution-20260821T164359-0300` / `audit`.
  Diagnostic outer PID/PPID/PGID `644420/644417/644420`; taskipy wrapper
  `644434` (PPID `644420`, PGID `644420`); task shell `644435` (PPID `644434`);
  pytest uv wrapper `644436` (PPID `644435`); pytest PID `644439` (PPID
  `644436`); fixture Alembic subprocess PID `644440` (PPID `644439`, observed
  during polls). All observed in exact current-run PGID `644420`.
- Timeline: launch `2026-08-21T16:45:28-03:00`; poll snapshots every second,
  `n=0..39` through `2026-08-21T16:46:08-03:00`; child tree ended
  `2026-08-21T16:46:10-03:00`; wait return/outer exit `0`; no signal call.
  Process log: `reports/test-profile/t34-audit-attribution-20260821T164359.process.log`.
- Fixture linkage: `tests/conftest.py` emitted exact dynamic test DB
  `reports/test-profile/.t34-audit-attribution-20260821T164359-tmp/omaha-conftest-safe-5i7is4ao/portfolio.db`
  and exact run/lane temp receipt for
  `reports/test-profile/.t34-audit-attribution-20260821T164359-pytest`.
  `tests/support/db.py::prepare_safe_test_database` launched
  `[sys.executable, "-m", "alembic", "upgrade", "head"]`; the Alembic child
  was observed in the same PGID and disappeared before later poll snapshots.
  Timing plugin linked all 40 nodes; slowest audit node was
  `test_inventory_for_patrimonio_has_rows_with_template_field` at `16.411s`.
- Historical source attribution is proven outside T34 boundary: R4 audit log
  `reports/test-profile/20260821T134451-audit.log:46` contains PID `630022`;
  traceback `reports/test-profile/20260820T122938-audit.log:42-107` reaches
  `taskipy/task_runner.py:183-186`, where `signal_handler` calls
  `psutil.Process(process.pid)` after its shell child vanished. Current taskipy
  source confirms same code at `.venv/lib/python3.12/site-packages/taskipy/task_runner.py:168-195`.
  T34 files contain no literal source for this failure. `630022` is therefore
  an external taskipy signal-handler race, not a proven runner/shared-fixture
  defect.
- **R4-F02: `BLOCKED_FOR_IMPLEMENTATION_BRIEF`.** Cause/source attribution is
  complete, but no permitted T34 boundary file can correct dependency code
  without changing taskipy/runner scope. Owning recommendation: owner-authorize
  separate taskipy compatibility/runner-boundary slice; do not patch T34 or
  alter task topology here.

### Focused harness and lint results

- First harness command was malformed for taskipy `test-file`:
  `uv run task test-file tests/scripts/test_t29_harness.py -- -s -p test_profile_plugin`
  -> pytest collected `0`, stderr `ERROR: file or directory not found: -s`,
  exit `4`. No test failure; exact group `645028` and exact TMPDIR parent
  were exited and cleaned. No retry of audit diagnosis occurred.
- Correct focused harness command:
  `uv run task test-file tests/scripts/test_t29_harness.py` with exact current
  run `t34-audit-attribution-harness2-20260821T164752-0300`, basetemp/TMPDIR
  boundaries registered before launch -> **59 passed in 2.35s**, wrapper/group
  `645244/645244`, wait/exit `0`, exact basetemp/TMPDIR absent after bounded
  cleanup. Process/fixture chain was `645244 → 645258 task → 645259 shell →
  645260 uv → 645263 pytest → 645264 Alembic`, all PGID `645244`.
- Targeted lint:
  `uv run ruff check scripts/run_full_suite.py tests/conftest.py
  tests/support/db.py tests/scripts/test_t29_harness.py` -> **All checks
  passed!**, PID/PGID `645506/645506`, started
  `2026-08-21T16:49:21-03:00`, ended `2026-08-21T16:49:22-03:00`, return `0`.
  `git diff --check` -> clean.

### Ownership ledger receipt — isolated audit attribution

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `644420` outer audit launcher | T34 audit attribution / apply | exact `setsid` launch under registered run/lane command | 2026-08-21T16:45:28-03:00 | 2026-08-21T16:46:10-03:00 | exited | owned-cleaned | wait/exit `0`, PGID `644420` | idempotent no-op; already absent |
| child process | PID `644434` taskipy wrapper | T34 audit attribution / apply | process-tree snapshot PPID `644420`, PGID `644420` | 2026-08-21T16:45:29-03:00 | 2026-08-21T16:46:10-03:00 | exited | owned-cleaned | taskipy `test-audit-integration` wrapper | idempotent no-op; already absent |
| child process | PID `644435` task shell | T34 audit attribution / apply | process-tree snapshot PPID `644434`, PGID `644420` | 2026-08-21T16:45:29-03:00 | 2026-08-21T16:46:10-03:00 | exited | owned-cleaned | exact task command shell | idempotent no-op; already absent |
| child process | PID `644439` pytest | T34 audit attribution / apply | process-tree snapshot PPID `644436`, PGID `644420` | 2026-08-21T16:45:29-03:00 | 2026-08-21T16:46:10-03:00 | exited | owned-cleaned | 40 audit tests passed | idempotent no-op; already absent |
| child process | PID `644440` Alembic | T34 audit attribution / apply | conftest subprocess command plus same-run process snapshot | 2026-08-21T16:45:29-03:00 | 2026-08-21T16:45:37-03:00 | exited | owned-cleaned | fixture migration subprocess in owned PGID | idempotent no-op; already absent |
| process group | PGID `644420` | T34 audit attribution / apply | `setsid` identity and all descendants same PGID | 2026-08-21T16:45:28-03:00 | 2026-08-21T16:46:10-03:00 | exited | owned-cleaned | no signal; no survivor | idempotent no-op; group absent |
| test DB resource | `reports/test-profile/.t34-audit-attribution-20260821T164359-tmp/omaha-conftest-safe-5i7is4ao/portfolio.db` | T34 audit attribution / apply | exact `T29_DB_TARGET` from current audit stdout under registered TMPDIR | 2026-08-21T16:45:29-03:00 | 2026-08-21T16:46:10-03:00 | cleanup-attempted | owned-cleaned | dynamic test-only DB; no production path | exact registered TMPDIR removed; post-stat absent |
| temporary path | `reports/test-profile/.t34-audit-attribution-20260821T164359-pytest` | T34 audit attribution / apply | exact `T29_TEMP_ROOT` matched run/lane before cleanup | 2026-08-21T16:45:28-03:00 | 2026-08-21T16:46:10-03:00 | cleanup-attempted | owned-cleaned | exact pytest boundary only | exact path removed; post-stat absent |
| temporary path | `reports/test-profile/.t34-audit-attribution-20260821T164359-tmp` | T34 audit attribution / apply | exact TMPDIR registered before launch | 2026-08-21T16:45:28-03:00 | 2026-08-21T16:46:10-03:00 | cleanup-attempted | owned-cleaned | contained only current-run fixture DB and uv lock | exact path removed; post-stat absent |
| log | `reports/test-profile/t34-audit-attribution-20260821T164359.stdout.log`, `.stderr.log`, `.timings`, `.process.log` | T34 audit attribution / apply | exact paths registered before launch; current-run evidence retained | 2026-08-21T16:45:28-03:00 | 2026-08-21T16:46:10-03:00 | exited | owned-current-run | source attribution and test linkage retained | retained as durable evidence; no cleanup |
| child process | PID `645028` malformed harness wrapper | T34 harness validation / apply | exact registered command launch | 2026-08-21T16:47:27-03:00 | 2026-08-21T16:47:31-03:00 | exited | owned-cleaned | pytest argument-shape error, exit `4` | idempotent no-op; already absent |
| process group | PGID `645028` | T34 harness validation / apply | `setsid` identity before focused command | 2026-08-21T16:47:27-03:00 | 2026-08-21T16:47:31-03:00 | exited | owned-cleaned | no test/port residue | idempotent no-op; group absent |
| child process | PID `645244` harness wrapper | T34 harness validation / apply | exact registered corrected command launch | 2026-08-21T16:48:17-03:00 | 2026-08-21T16:48:23-03:00 | exited | owned-cleaned | 59 tests passed, exit `0` | idempotent no-op; already absent |
| process group | PGID `645244` | T34 harness validation / apply | `setsid` identity and descendant snapshots | 2026-08-21T16:48:17-03:00 | 2026-08-21T16:48:23-03:00 | exited | owned-cleaned | no listener or survivor | idempotent no-op; group absent |
| temporary path | `reports/test-profile/.t34-audit-attribution-harness2-20260821T164752-{pytest,tmp}` | T34 harness validation / apply | exact paths registered before launch | 2026-08-21T16:48:17-03:00 | 2026-08-21T16:48:23-03:00 | cleanup-attempted | owned-cleaned | exact current-run paths only | exact paths removed; post-stat absent |
| child process | PID `645506` Ruff | T34 targeted lint / apply | exact `setsid uv run ruff` launch and registered log | 2026-08-21T16:49:21-03:00 | 2026-08-21T16:49:22-03:00 | exited | owned-cleaned | Ruff exit `0` | idempotent no-op; already absent |
| process group | PGID `645506` | T34 targeted lint / apply | exact `setsid` PGID | 2026-08-21T16:49:21-03:00 | 2026-08-21T16:49:22-03:00 | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; group absent |
| log | `reports/test-profile/t34-audit-attribution-lint-20260821T164850.log` | T34 targeted lint / apply | exact log path registered before launch | 2026-08-21T16:49:21-03:00 | 2026-08-21T16:49:22-03:00 | exited | owned-current-run | Ruff output retained | retained as durable evidence; no cleanup |

Cleanup decision: all exact current-run processes/groups and dynamic test
resources exited or were cleaned; durable logs retained. PID `630022` remained
untouched and was never adopted. No foreign/pre-existing/unknown resource,
production DB, fixed lane port, or broad `/tmp` path was changed.

### Stop condition

No runtime or focused regression edit is justified. Source is proven as
external taskipy `signal_handler` race; T34 boundary cannot correct it without
scope change. Stop with `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; review task 3.2
remains open and no canonical suite was run.

## 4. Owner-authorized amendment — Taskipy compatibility boundary

These tasks amend T34 only. Prior completed tasks, receipts, review findings,
and stop conditions remain unchanged. No task below authorizes editing installed
site-packages, changing F58/MyProfit/product behavior, altering test behavior,
changing lane topology, adding retries/skips/xfails, reopening I08/T33, or
running the canonical suite at proposal/apply gate.

- [x] 4.1 Record external fault and package matrix. Target files/symbols:
  `pyproject.toml:[dependency-groups].dev::taskipy`,
  `pyproject.toml:[tool.taskipy.settings/tasks]`, `uv.lock` Taskipy and psutil
  package blocks, and read-only installed
  `.venv/.../taskipy/task_runner.py::TaskRunner.__send_signal_to_task_process`.
  Exact change: dossier-only evidence records project declaration
  `taskipy>=1.13`, locked Taskipy `1.14.1`, locked psutil `6.1.1`, Taskipy's
  `psutil>=5.7.2,<7` range, and unchanged handler in 1.13.0/1.14.1/master.
  Preserve all existing runner/harness evidence and files. Acceptance: source
  attribution names `task_runner.py:183-186`, `psutil.NoSuchProcess`, SIGTERM,
  already-exited shell child, and historical PID `630022`; no dependency or
  installed-package edit. Test file/scenario: N/A — package/source matrix and
  existing `tasks.md:1331-1373` evidence. Focused taskipy command:
  `uv run task --list`. Independent oracle: `pyproject.toml`, `uv.lock`, and
  installed/upstream source agree on resolved versions and handler behavior.

- [ ] 4.2 Select supported remedy or stop blocked. Target files/symbols:
  `pyproject.toml:[project].dependencies`/`[dependency-groups].dev`, paired
  `uv.lock:[[package]]`, and no other dependency files. Exact change: if and
  only if upstream publishes a verifiable fixed Taskipy release, raise the
  Taskipy lower bound to that exact published fixed version and regenerate
  only paired lock records; otherwise make no file change and retain
  `BLOCKED_FOR_IMPLEMENTATION_BRIEF`. Preserve Taskipy entrypoints, six lane
  names/order, flags, ports, DB allow-list, coverage, skips, fail-fast, and
  300-second deadline. Acceptance: fixed release metadata contains a handler
  correction, lock resolves that exact release, and no unsafe workaround is
  proposed. Current options `1.14.1`, `1.13.x/earlier`, psutil pin changes,
  settings-only changes, runner signal-policy changes, VCS/fork without a
  published supported artifact, and site-package patch are rejected. Test
  file/scenario: N/A until supported release exists. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  published package source plus `uv.lock` hash/version; absent fixed release
  means stop, not downgrade, monkeypatch, or invent version.

- [x] 4.3 Guard runner invocation/config boundary. Target files/symbols:
  `scripts/run_full_suite.py::LANES`, `launch`, `handle_signal`, `_stop`,
  `_reap`, and `pyproject.toml:[tool.taskipy.tasks]::test*`. Exact change:
  none unless a controlled reproduction proves invocation/config, rather than
  external Taskipy code, causes residual failure; any approved change must be
  minimal and preserve current signal ownership and task topology. Acceptance:
  no task command, shell mode, process-group policy, lane order, retry policy,
  skip/xfail policy, or timeout is changed for hypothesis. Test file/scenario:
  `tests/scripts/test_t29_harness.py` runtime-child-command, lane-topology,
  vanished-child, and parent-SIGTERM scenarios. Focused taskipy command:
  `uv run task test-one tests/scripts/test_t29_harness.py -k "runtime_child_command or lane or vanished_child or parent_sigterm"`.
  Independent oracle: mapped diff shows no invocation/config edit unless the
  controlled receipt names exact causal lines and all existing lifecycle
  contracts remain green.

- [ ] 4.4 Add conditional regression only after supported remedy. Target file/
  symbol: existing `tests/scripts/test_t29_harness.py` lifecycle contracts.
  Exact change: add one deterministic already-exited-task-child plus runner
  SIGTERM scenario proving Taskipy emits no `NoSuchProcess` traceback while
  runner preserves causal nonzero/timeout semantics and exact owned cleanup;
  do not alter existing tests or behavior. Acceptance: focused module and
  directly affected support tests pass with no retry/skip/xfail, production DB,
  fixed-lane listener, or broad `/tmp` action. Test file/scenario:
  `tests/scripts/test_t29_harness.py` new compatibility regression plus all
  existing lifecycle/topology scenarios. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  no taskipy traceback under controlled race, original runner result preserved,
  and resource ledger ends only `absent`/`owned-cleaned`.

- [ ] 4.5 Re-run gates only after 4.2 and 4.4 pass. Target artifacts:
  T34 `tasks.md` receipt, `pyproject.toml`/`uv.lock` if changed, and existing
  canonical runner receipt. Exact change: record resolved dependency versions,
  focused result, strict change/spec validation, then review runs exactly one
  `uv run task test`; no proposal-gate full suite. Preserve all prior receipts
  and review findings. Acceptance: six lanes exit 0, coverage/skips/manifest
  reconciliation complete, Taskipy race absent, DB targets test-only, every
  current-run resource `absent`/`owned-cleaned`, unknown/foreign/pre-existing
  resources untouched, and elapsed wall-clock through cleanup `<=300s`.
  Test file/scenario: canonical six-lane suite plus existing T29 compatibility
  scenario. Focused taskipy command: `uv run task test` exactly once at review
  gate. Independent oracle: same-run receipt/postflight comparison and
  `openspec validate t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 --type change --strict --json`.

### Amendment stop result

Task 4.1 evidence is complete. Task 4.2 is blocked because no supported
published Taskipy version corrects the handler race. Therefore no dependency,
lockfile, runner, invocation, test, or site-package edit is authorized by this
amendment; task 3.2 and tasks 4.2–4.5 remain open. Unknown dependency or host
resources follow existing safe-stop rules: preserve, do not adopt, kill,
delete, scan, allowlist, retry, or rerun.

## 5. Owner-authorized amendment — exact runner temp-resource boundary

These tasks amend policy relevance only. Prior tasks, receipts, findings, and
Taskipy stop conditions remain unchanged. No task authorizes implementation at
the proposal gate, canonical-suite execution, host cleanup, DB reset, archive,
commit, or push.

### Test strategy and acceptance matrix

Focused strategy uses existing bounded runner contracts, not host discovery:

| Scenario | Required result | Test file/scenario | Focused command | Independent oracle |
|---|---|---|---|---|
| Out-of-bound pre-existing temp path, including `/tmp/pytest-of-juca` | Record `preserved/non-target`; no cleanup; does not block alone | `tests/scripts/test_t29_harness.py::test_runner_preflight_inventory_ignores_harmless_host_observations` and `test_runner_preflight_inventory_records_preexisting_pytest_root_as_irrelevant` | `uv run task test-one tests/scripts/test_t29_harness.py -k "preflight_inventory"` | Inventory marks `relevant=false`, `cleanup_target=false`, `preserved=true`, `allowlisted=false`, `adopted=false`, and `ok=true` |
| Exact current-run declared path | Exact cleanup only; final classification `owned-cleaned` | `tests/scripts/test_t29_harness.py::test_runner_reconciles_owned_temp_root_exactly` | `uv run task test-one tests/scripts/test_t29_harness.py -k "owned_temp_root_exactly"` | Declared path disappears; no sibling/parent path is touched |
| Mismatch/foreign path inside declared boundary | Preserve untouched; classify untrusted/foreign; block affected operation | `tests/scripts/test_t29_harness.py::test_runner_preserves_mismatched_temp_root` plus existing foreign-resource scenario | `uv run task test-one tests/scripts/test_t29_harness.py -k "mismatched_temp_root or foreign_resource"` | Reported path remains; receipt is nonzero/untrusted; no cleanup call targets it |

The amendment's policy validation additionally checks all four policy documents
and both T34 delta specs for identical boundary language, absence of literal
allowlists and `pytest-of-*` discovery, and preserved D05 stop rules. Proposal
gate runs only OpenSpec/static validation; focused tests belong to later Apply.

- [x] 5.1 Amend review/apply policy files. Target sections/symbols:
  `.opencode/agents/review.md` preflight/isolation/postflight,
  `.opencode/agents/apply.md` resource decision procedure and canonical review
  isolation, `.opencode/skills/openspec-apply-change/SKILL.md` cleanup decision
  and guardrails, and `AGENTIC_DEVELOPMENT.md` ownership/preflight contract.
  Exact change: define cleanup-relevant temporary resources as only canonical
  runner-declared exact run/lane paths; classify exact current-run receipt match
  as `owned-cleaned` after bounded cleanup and exact absence as `absent`; leave
  mismatch/unknown/foreign/contradictory state inside that boundary untouched
  and blocking; record out-of-bound temporary observations as
  `preserved/non-target` that cannot block alone. Preserve D05 process/listener/
  DB safety, no broad cleanup, no `pytest-of-*` discovery, no literal allowlist,
  and all lane/retry/skip/xfail/timeout invariants. Acceptance: four policy
  files state same contract and no policy permits adoption, deletion, parent or
  broad `/tmp` cleanup. Test file/scenario: policy text audit plus matrix above.
  Focused taskipy command: `uv run task test-one tests/scripts/test_t29_harness.py -k "preflight_inventory or temp_root or foreign_resource"`.
  Independent oracle: exact policy diff contains only named sections; grep/text
  audit finds declaration-boundary wording and no allowlist/discovery/parent-
  cleanup exception.

- [x] 5.2 Amend T34 delta specs. Target files/symbols:
  `specs/dev-tasks/spec.md` modified coverage/temp requirements and scenarios;
  `specs/shared-test-support/spec.md` current-run temporary ownership
  requirement and scenarios. Exact change: make runner-declared exact
  run/lane paths the only cleanup-relevant temporary set; require exact
  current-run match for `owned-cleaned`; require mismatch/unknown/foreign state
  inside boundary to remain untouched and block; require out-of-bound paths to
  be recorded preserved/non-target and not block alone. Preserve canonical
  six lanes, direct/taskipy boundary already owned by I10, DB safety, markers,
  coverage, skips, fail-fast, and 300 seconds. Acceptance: both deltas contain
  explicit scenarios for non-target preservation, exact owned cleanup, and
  untouched blocking mismatch/foreign path. Test file/scenario: no runtime
  test; OpenSpec delta validation. Focused taskipy command: `uv run task
  test-one tests/scripts/test_t29_harness.py -k "temp or receipt or ownership"`.
  Independent oracle: strict change validation accepts both delta files and
  each scenario distinguishes out-of-bound from declared-boundary evidence.

- [x] 5.3 Preserve/extend focused runner acceptance only if current contracts
  lack one matrix row. Target file/symbol: existing
  `tests/scripts/test_t29_harness.py` inventory/reconciliation scenarios named
  in the matrix; do not alter runner topology or add host probing. Exact
  change: prove non-target `/tmp/pytest-of-juca` is preserved and non-blocking
  alone, exact owned path is cleaned, and mismatch/foreign declared path stays
  untouched and untrusted. Preserve existing `relevant`, `cleanup_target`,
  `allowlisted`, and `adopted` semantics. Acceptance: all three rows pass with
  no wildcard, parent, broad `/tmp`, process-name, retry, skip, or xfail action.
  Test file/scenario: same three named scenarios. Focused taskipy command: `uv
  run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  filesystem assertions and receipt classifications prove exact target set;
  foreign/mismatch path remains present and canonical inventory remains trusted
  only when no declared-boundary violation exists.

- [x] 5.4 Validate amendment artifacts and scope before Apply. Target artifacts:
  T34 `proposal.md`, `design.md`, `tasks.md`, both delta specs, and no D05/I10/
  T33/F58/product files. Exact change: record static policy parity, changed-file
  audit, and validation output while preserving all prior evidence. Acceptance:
  exact change validation and strict stable-spec validation pass; diff contains
  no policy file outside four named documents, no D05 edit, no stable-spec
  mutation, and no runtime/resource action. Test file/scenario: OpenSpec
  artifacts and worktree scope audit. Focused taskipy command: none at proposal
  gate; later oracle may run `uv run task test-one tests/scripts/test_t29_harness.py`
  only as focused smoke. Independent oracle: `openspec validate
  t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 --type
  change --strict --json`, `openspec validate --specs --strict --json`,
  `git diff --check`, and changed-file audit.

### Amendment stop condition

Proposal gate stops after artifact validation. If policy wording would make a
true foreign/unknown resource inside a canonical declared boundary non-blocking,
or would require a literal allowlist, `pytest-of-*` discovery, parent/broad
`/tmp` cleanup, or D05 safety exception, return `BLOCKED_FOR_IMPLEMENTATION_BRIEF`
with exact conflict. No implementation or test run is permitted here.

## Owner-authorized I10 receipt remediation — run registration

- Run ID: `t34-i10-remediation4-focused-20260821T190618-0300`
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`
- Owner evidence: registration recorded before focused validation at
  `2026-08-21T19:06:18-03:00`; exact basetemp and TMPDIR paths below are
  current-run-only boundaries. No canonical lane port, LAN service, production
  DB, fixed DB, or unrecorded path is a cleanup target.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664033` | T34 I10 remediation / apply | wrapper PID/PGID before exec | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:06:50-03:00 | exited | owned-cleaned | IndentationError before collection | idempotent no-op; already exited |
| process group | PGID `664033` | T34 I10 remediation / apply | wrapper PGID before exec | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:06:50-03:00 | exited | owned-cleaned | no child residue | idempotent no-op; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused-pytest` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:07:02-03:00 | absent | owned-cleaned | failed run boundary | exact bounded removal; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused-tmp` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:07:02-03:00 | absent | owned-cleaned | failed run boundary | exact bounded removal; absent |
| test DB resource | dynamic DB under registered TMPDIR | T34 I10 remediation / apply | no bootstrap reached | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:06:50-03:00 | absent | absent | no DB created | idempotent no-op |

## I10 R2 evidence remediation — execution result

### Condition attribution

| Condition | Evidence and causal status | Result |
|---|---|---|
| E2E `8765` refused | I10 receipt `20260821T184456-660477`, E2E PID/PGID `660488`, log `17-23`: refusal only; no startup exception/server event. Prior bounded shared-server contracts pass. | `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; owner: isolated E2E/runner attribution. No readiness/browser/port/retry edit. |
| BDD `8766` refused | Same receipt, BDD PID/PGID `660493`, log `15-25`: refusal only. Prior owned run `t34-remediation3-bdd-20260821T152719-0300` had server `635957`, PGID `635938`, ready/teardown/`port_free=true`, `51 passed`. | `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; owner: isolated BDD/runner attribution. No BDD/server timeout/lane edit. |
| Unit empty DB receipt | Unit PID/PGID `660478`; conftest emitted dynamic DB only after `prepare_safe_test_database` migration/bootstrap. | **Corrected T34 support fault**: dynamic receipt now publishes immediately after safe path creation; late duplicate removed. |
| Integration empty DB receipt | Integration PID/PGID `660481`; same interrupted bootstrap path and missing DB receipt. | **Corrected T34 support fault** with same early publication; DB/seed/migration behavior unchanged. |
| `data/test_bdd.db` contradiction | I10 postflight found current-run inode `34819`, size `32768`, while receipt claimed cleanup. Runner had no exact fixed-DB preflight state or post-run check. Current apply preflight found path present and preserved it. | **Corrected T34 runner fault**: exact fixed DBs present at preflight are `pre-existing`; cleanup allowed only after exact preflight absence plus matching receipt. |
| Manifest `1032` vs `1043` | I10 receipt says `1032` vs `1043`; current `tests/AUDIT.md` explicitly defines `1,032` blocking nodes plus 12 outside-lane T32 cases. | `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; owner: I10 manifest/acceptance (`tests/AUDIT.md` and I10 review). No manifest edit. |
| Two expected skips absent | Receipt `actual_skips=[]` after deadline termination; runner retains exact `EXPECTED_SKIPS`; no completed timing parse loss proven. | `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; owner: I10 canonical manifest/receipt acceptance. No skip/xfail/retry edit. |

### Changed files/symbols

- `tests/support/db.py::prepare_safe_test_database` and
  `prepare_worker_database`: early dynamic `T29_DB_TARGET` receipt.
- `tests/conftest.py` module-load receipt import/emission: duplicate late
  publication removed; safe DB import ordering preserved.
- `scripts/run_full_suite.py::_canonical_resource_inventory`,
  `_fixed_db_preflight_classification`, `_reconcile_fixed_db_targets`: exact
  fixed test-DB ownership and bounded cleanup.
- `tests/scripts/test_t29_harness.py`: fixed-DB cleanup/preservation contracts;
  host-observation test isolated from pre-existing fixed DB state.
- T34 `design.md`/`tasks.md`: durable decision, ledgers, evidence, blockers.
  No I10 command vector or policy change.

### Focused validation

- `uv run task test-file tests/scripts/test_t29_harness.py` with exact dynamic
  TMPDIR/basetemp -> **67 passed in 0.50s**, PID/PGID `664361`.
- `PYTHONPATH=. uv run task test-file scripts/test_t29_receipt_harness.py` with
  exact dynamic TMPDIR/basetemp -> **8 passed in 0.85s**, PID/PGID `664482`.
- Targeted Ruff on mapped runner/support/harness files -> **All checks passed**,
  PID/PGID `664476`.
- `openspec validate ...t34... --type change --strict --json` -> `valid=true`.
- `openspec validate --specs --strict --json` -> **70/70 valid**; informational
  long-requirement notices only. `rtk git diff --check` -> clean.
- Static parity -> six exact I10 direct base vectors unchanged; no
  `pyproject.toml`, I10 policy, lane topology, ports, flags, skips, or timeout
  policy changed.

### Final ownership/postflight

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664361` | T34 I10 remediation / apply | wrapper PID/PGID before exec | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | 67 tests passed; postflight absent | idempotent no-op; already exited |
| process group | PGID `664361` | T34 I10 remediation / apply | `setsid` identity before launch | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |
| child process | PID `664482` | T34 I10 remediation / apply | receipt wrapper PID/PGID before exec | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | 8 receipt tests passed | idempotent no-op; already exited |
| process group | PGID `664482` | T34 I10 remediation / apply | receipt wrapper PGID before launch | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |
| child process | PID `664476` | T34 I10 remediation / apply | Ruff wrapper PID/PGID before exec | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | Ruff exit `0` | idempotent no-op; already exited |
| process group | PGID `664476` | T34 I10 remediation / apply | Ruff wrapper PGID before launch | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused3-{pytest,tmp}` | T34 I10 remediation / apply | exact paths registered before creation | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | exact dynamic boundaries | exact bounded removal; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-receipt-{pytest,tmp}` | T34 I10 remediation / apply | exact paths registered before creation | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | exact receipt boundaries | exact bounded removal; absent |
| port | `127.0.0.1:8765-8768` | T34 I10 remediation / apply | exact postflight `ss` inventory | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | absent | absent | no listener | untouched; idempotent no-op |
| temporary path | `/tmp/pytest-of-juca` | prior unregistered focused run | exact stat; no current-run registration | pre-existing | 2026-08-21T19:09:54-03:00 | present | unknown | not created/adopted by current apply | untouched; safe-stop |
| test DB resource | `/home/juca/github/omaha/data/test_bdd.db` | prior I10 canonical run | exact stat; no current-run registration | pre-existing | 2026-08-21T19:09:54-03:00 | present | pre-existing | test-only fixed DB | untouched; safe-stop |

Cleanup decision: registered current-run processes/groups and exact dynamic
paths cleaned or absent. Pre-existing `/tmp/pytest-of-juca` and
`data/test_bdd.db` untouched. No canonical suite, fixed lane port, LAN service,
production DB, broad `/tmp` scan, or foreign action occurred.

### Gate result

Task 4.3 complete: direct I10 vectors and invocation/config boundary unchanged.
T34 corrections for empty dynamic DB receipts and fixed-DB contradiction are
focused-green. E2E/BDD refusal and manifest/skip mismatch remain unproven or
I10-owned. Tasks 4.2, 4.4, and 4.5 remain open. Stop with
`BLOCKED_FOR_IMPLEMENTATION_BRIEF`.

## Owner-authorized I10 receipt remediation — receipt/lint registrations

- Receipt run ID: `t34-i10-remediation4-receipt-20260821T191000-0300`.
  Registration timestamp `2026-08-21T19:10:00-03:00`, before launch. Exact
  TMPDIR `/tmp/opencode/t34-i10-remediation4-receipt-tmp` and pytest boundary
  `/tmp/opencode/t34-i10-remediation4-receipt-pytest` are current-run-only.
- Lint run ID: `t34-i10-remediation4-lint-20260821T191000-0300`. Registration
  timestamp `2026-08-21T19:10:00-03:00`, before launch. One exact Ruff child/
  group; no DB, port, or temporary resource expected.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664482` | T34 I10 remediation / apply | receipt wrapper PID/PGID before exec | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | 8 tests passed | idempotent no-op; already exited |
| process group | PGID `664482` | T34 I10 remediation / apply | receipt wrapper PGID before exec | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-receipt-pytest` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | receipt basetemp | exact bounded removal; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-receipt-tmp` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | receipt TMPDIR | exact bounded removal; absent |
| child process | PID `664476` | T34 I10 remediation / apply | Ruff wrapper PID/PGID before exec | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | Ruff exit `0` | idempotent no-op; already exited |
| process group | PGID `664476` | T34 I10 remediation / apply | Ruff wrapper PGID before exec | 2026-08-21T19:09:04-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |

### Registration receipt — deterministic inventory test correction

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664218` | T34 I10 remediation / apply | corrected-run wrapper printed PID/PGID before exec | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:07:39-03:00 | exited | owned-cleaned | `66 passed, 1 failed`; failure exposed pre-existing fixed DB in host-observation test | idempotent no-op; already exited |
| process group | PGID `664218` | T34 I10 remediation / apply | `setsid` wrapper PGID printed before exec | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:07:39-03:00 | exited | owned-cleaned | no listener or surviving child | idempotent no-op; already absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused2-pytest` | T34 I10 remediation / apply | exact path registered before command | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | cleanup-attempted | owned-cleaned | exact basetemp and fixture paths | exact bounded removal; absent after cleanup |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused2-tmp` | T34 I10 remediation / apply | exact path registered before command | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | cleanup-attempted | owned-cleaned | exact TMPDIR and dynamic DB parent | exact bounded removal; absent after cleanup |

## Owner-authorized I10 receipt remediation — final focused run registration

- Run ID: `t34-i10-remediation4-focused3-20260821T190800-0300`
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`
- Owner evidence: registration recorded before launch at
  `2026-08-21T19:08:00-03:00`; exact boundaries below are current-run-only.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664361` | T34 I10 remediation / apply | final wrapper PID/PGID before exec | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | 67 tests passed | idempotent no-op; already exited |
| process group | PGID `664361` | T34 I10 remediation / apply | final wrapper PGID before exec | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused3-pytest` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | exact basetemp | exact bounded removal; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused3-tmp` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | exact TMPDIR/dynamic DB boundary | exact bounded removal; absent |
| test DB resource | dynamic DB under registered TMPDIR | T34 I10 remediation / apply | fixture path under exact boundary | 2026-08-21T19:08:25-03:00 | 2026-08-21T19:09:54-03:00 | absent | owned-cleaned | test-only dynamic DB | exact parent cleanup; absent |
| port | `127.0.0.1:8765-8768` | T34 I10 remediation / apply | preflight and postflight exact `ss` inventory | 2026-08-21T19:06:18-03:00 | 2026-08-21T19:09:54-03:00 | absent | absent | no listener observed | untouched; idempotent no-op |
| temporary path | `/tmp/pytest-of-juca` | prior unowned focused run | exact stat after prior unregistered validation | pre-existing | not adopted | present | unknown | no current-run owner evidence | untouched; safe-stop resource |
| test DB resource | `data/test_bdd.db` | prior I10 canonical run | exact stat before remediation | pre-existing | not adopted | present | pre-existing | no current-run owner evidence in this run | untouched; safe-stop resource |

Canonical review isolation is not trusted in this workspace because the exact
pytest root and `data/test_bdd.db` are unowned pre-existing resources. No
canonical suite is authorized in this apply pass.

## Execution Evidence — exact runner temp-resource policy amendment

### Pre-edit boundary

- Captured `rtk git diff HEAD~1` before edits. Existing worktree changes remain
  outside this pass unless listed below; no runtime runner, product, DB/seed,
  process/port, I10, I08, T33, D05, or F58 files are owned.
- This pass owns only `.opencode/agents/review.md`, `.opencode/agents/apply.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`, `AGENTIC_DEVELOPMENT.md`,
  the two T34 delta specs, `design.md`, and `tasks.md`. Existing T34 harness
  tests already contain all three acceptance rows, so no test code edit is
  needed.

### Focused validation ownership registration

- Run ID: `t34-policy-boundary-focused-20260822T003200-0300`
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`
- Owner evidence: this registration is written before focused taskipy launch;
  registration timestamp `2026-08-22T00:32:00-03:00`.
- Exact temporary boundary registered before use:
  `reports/test-profile/.t34-policy-boundary-focused-pytest`.
- Planned resources: one taskipy/pytest child and process group assigned by the
  current invocation, exact registered pytest boundary above, test-only pytest
  fixture paths, and no fixed canonical listener or production DB. Only exact
  current-run entries may be cleaned; out-of-bound observations remain
  preserved/non-target.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | taskipy/pytest child PID not emitted by first tool invocation | T34 policy amendment / apply | current-run registration before launch; second receipt-bearing run provides PID | `2026-08-22T00:34:39-03:00` | `2026-08-22T00:35:42-03:00` | exited | owned-cleaned | first focused command `71 passed`; no child residue observed | command exited; exact cleanup receipt below is authoritative |
| process group | taskipy/pytest group not emitted by first tool invocation | T34 policy amendment / apply | current-run registration before launch; second receipt-bearing run provides PGID | `2026-08-22T00:34:39-03:00` | `2026-08-22T00:35:42-03:00` | exited | owned-cleaned | no listener or group residue observed | idempotent no-op; already absent |
| temporary path | `reports/test-profile/.t34-policy-boundary-focused-pytest` | T34 policy amendment / apply | exact path registered before launch | `2026-08-22T00:34:39-03:00` | `2026-08-22T00:35:42-03:00` | cleanup-attempted | owned-cleaned | pytest root existed after `71 passed` | exact path removed; post-check absent |
| test DB resource | no test DB resource allocated by focused harness | T34 policy amendment / apply | focused module inventory; no production DB target | `2026-08-22T00:34:39-03:00` | `2026-08-22T00:35:42-03:00` | absent | absent | harness doubles only | idempotent no-op; absent |

The first focused invocation returned `71 passed in 2.26s`; its exact registered
basetemp remained present after pytest and was removed only by the bounded exact
cleanup above. A second receipt-bearing focused invocation is registered below
to retain wrapper PID/PGID evidence before the final handoff.

### Receipt-bearing focused validation registration

- Run ID: `t34-policy-boundary-focused-receipt-20260822T003600-0300`
- Owner evidence: registration recorded before launch at
  `2026-08-22T00:36:00-03:00`.
- Exact temporary boundary:
  `reports/test-profile/.t34-policy-boundary-focused-receipt-pytest`.
- Planned resources: wrapper child/process group with PID/PGID printed before
  `exec`, exact pytest boundary, and test-only fixture paths. No fixed lane
  listener or production DB is registered.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `25236` | T34 policy amendment / apply | wrapper printed PID before `exec uv run task` | `2026-08-22T00:36:00-03:00` | `2026-08-22T00:37:00-03:00` | exited | owned-cleaned | `71 passed in 2.12s`; wrapper exit `0` | bounded wait; already absent |
| process group | PGID `25236` | T34 policy amendment / apply | wrapper printed PGID before exec; `setsid` group | `2026-08-22T00:36:00-03:00` | `2026-08-22T00:37:00-03:00` | exited | owned-cleaned | no listener or descendant residue | bounded wait; group absent |
| temporary path | `reports/test-profile/.t34-policy-boundary-focused-receipt-pytest` | T34 policy amendment / apply | exact path registered before launch; post-run stat owner `juca:juca` | `2026-08-22T00:36:00-03:00` | `2026-08-22T00:37:00-03:00` | cleanup-attempted | owned-cleaned | exact pytest basetemp only | exact path removed; post-check absent |
| test DB resource | no test DB resource allocated by focused harness | T34 policy amendment / apply | focused module inventory; no production DB target | `2026-08-22T00:36:00-03:00` | `2026-08-22T00:37:00-03:00` | absent | absent | harness doubles only | idempotent no-op; absent |

### Targeted lint and artifact-validation registration

- Run IDs: `t34-policy-boundary-ruff-20260822T003700-0300` and
  `t34-policy-boundary-spec-20260822T003700-0300`.
- Owner: T34 policy amendment / apply. Registration timestamp:
  `2026-08-22T00:37:00-03:00`, before launch of each command.
- Planned resource IDs: one exact Ruff wrapper/process group and one exact
  OpenSpec validation process per command. No test DB, listener, or temporary
  cleanup target is registered; any command-created process is waited and left
  absent, with no foreign-resource action.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `25524` | T34 policy amendment / apply | wrapper printed PID before `exec uv run ruff` | `2026-08-22T00:37:00-03:00` | `2026-08-22T00:37:10-03:00` | exited | owned-cleaned | Ruff all checks passed | idempotent no-op; already absent |
| process group | PGID `25524` | T34 policy amendment / apply | wrapper printed PGID before exec | `2026-08-22T00:37:00-03:00` | `2026-08-22T00:37:10-03:00` | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; already absent |
| child process | PID `25967` change validator | T34 policy amendment / apply | wrapper printed PID before `exec openspec validate` | `2026-08-22T00:37:10-03:00` | `2026-08-22T00:37:11-03:00` | exited | owned-cleaned | change strict `valid=true` | idempotent no-op; already absent |
| process group | PGID `25967` change validator | T34 policy amendment / apply | wrapper printed PGID before exec | `2026-08-22T00:37:10-03:00` | `2026-08-22T00:37:11-03:00` | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; already absent |
| child process | PID `25968` spec validator | T34 policy amendment / apply | wrapper printed PID before `exec openspec validate --specs` | `2026-08-22T00:37:10-03:00` | `2026-08-22T00:37:11-03:00` | exited | owned-cleaned | stable specs `70/70` valid | idempotent no-op; already absent |
| process group | PGID `25968` spec validator | T34 policy amendment / apply | wrapper printed PGID before exec | `2026-08-22T00:37:10-03:00` | `2026-08-22T00:37:11-03:00` | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; already absent |

### Amendment execution result

- Tasks 5.1–5.4 complete. Four policy documents now use same exact-boundary
  matrix; both T34 deltas state declaration-only relevance and explicit
  non-target/mismatch scenarios. No runtime or focused test file changed.
- Acceptance: existing T29 contracts passed `71 passed in 2.12s` in the
  receipt-bearing run. Exact owned temp root reached `owned-cleaned`; exact
  mismatch/foreign contracts preserve the path and return untrusted; synthetic
  out-of-bound `/tmp/pytest-of-juca` inventory is `relevant=false`,
  `cleanup_target=false`, `preserved=true`, `allowlisted=false`, `adopted=false`,
  and inventory `ok=true`.
- Lint: `uv run ruff check tests/scripts/test_t29_harness.py` -> all checks
  passed. Artifact validation: strict T34 change `valid=true`; strict stable
  specs `70/70 valid` with existing informational long-requirement notices;
  `rtk git diff --check` clean.
- Postflight: PID/PGID `25236` absent, ports `8765-8768` absent, exact
  registered pytest root absent after bounded exact cleanup. Current host
  inventory preserves `/tmp/pytest-of-juca` as out-of-bound evidence; no
  production or fixed test DB path was touched.

Cleanup decision: current-run wrapper/group and exact basetemp were
`owned-cleaned` or idempotent absent; no foreign, unknown, pre-existing,
production, listener, or broad `/tmp` resource was acted on.

### Final artifact revalidation registration

- Run ID: `t34-policy-boundary-final-spec-20260822T004000-0300`.
- Owner: T34 policy amendment / apply. Registration recorded before launch at
  `2026-08-22T00:40:07-03:00`.
- Resources: two exact validator child/process groups, one per strict change and
  stable-spec command; no DB, listener, temporary path, or cleanup target.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PIDs `27197`/`27202` | T34 policy amendment / apply | wrappers printed PID before exact validator execs | `2026-08-22T00:40:07-03:00` | `2026-08-22T00:40:08-03:00` | exited | owned-cleaned | change `valid=true`; specs `70/70 valid` | idempotent no-op; already absent |
| process group | PGIDs `27197`/`27202` | T34 policy amendment / apply | wrappers printed PGID before exact validator execs | `2026-08-22T00:40:07-03:00` | `2026-08-22T00:40:08-03:00` | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; already absent |

Final artifact revalidation result: strict T34 change validation passed
(`valid=true`); strict stable-spec validation passed (`70/70`), with only
existing informational long-requirement notices. No runtime or host resource
operation occurred.


### Registration receipt — failed preflight validation

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664033` | T34 I10 remediation / apply | wrapper printed PID/PGID before exec under registered run | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:06:50-03:00 | exited | owned-cleaned | focused command stopped at `tests/conftest.py:72` IndentationError before collection | idempotent no-op; already exited |
| process group | PGID `664033` | T34 I10 remediation / apply | `setsid` wrapper PGID printed before exec | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:06:50-03:00 | exited | owned-cleaned | no child, listener, or DB process remained | idempotent no-op; already absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused-pytest` | T34 I10 remediation / apply | exact path registered before command | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:07:02-03:00 | cleanup-attempted | owned-cleaned | exact basetemp path created by current command | exact bounded removal; absent after cleanup |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused-tmp` | T34 I10 remediation / apply | exact path registered before command | 2026-08-21T19:06:50-03:00 | 2026-08-21T19:07:02-03:00 | cleanup-attempted | owned-cleaned | exact TMPDIR path created by current command | exact bounded removal; absent after cleanup |

New focused validation registration follows after surgical indentation fix.

## Owner-authorized consolidated T34 remediation

### Apply scope

- [x] C1 Preserve valid unit/integration dynamic DB ownership independently of
  incomplete collection; reconcile only emitted paths inside registered lane
  temp boundaries.
- [x] C2 Persist bounded run/phase/lane timing and receipt-write observations
  sufficient to attribute hard-ceiling time after failure.
- [x] C3 Reproduce E2E `8765` and BDD `8766` startup concurrently under
  runner-equivalent direct-child conditions; change lifecycle code only if the
  reproduction proves a T34 boundary fault.
- [x] C4 Run focused harness/receipt/concurrent-startup checks, targeted lint,
  diff/spec validation, and record RC-1..RC-3 status plus ownership receipts.

### Validation ownership registration — consolidated pass

- Run ID: `t34-consolidated-remediation-20260821T224900-0300`
- Owner: `t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 / apply`
- Owner evidence: this registration was written before validation launch at
  `2026-08-21T22:49:00-03:00`; each later process, group, port, log, exact
  temp path, and test DB entry will be registered before use.
- Cleanup boundary: current-run ledger entries only. Foreign, pre-existing,
  unknown, contradictory, production, LAN, and unregistered resources remain
  untouched and cause safe stop.

### Correction validation registration

- Run ID: `t34-consolidated-remediation-correction-20260821T225006-0300`
- Owner evidence: registered at `2026-08-21T22:50:06-03:00` before launch;
  exact TMPDIR `/tmp/opencode/t34-consolidated-correction-20260821T225006-tmp`
  and pytest boundary `/tmp/opencode/t34-consolidated-correction-20260821T225006-pytest`
  are current-run resources. No fixed lane port or production DB is a target.

- Receipt-harness run ID: `t34-consolidated-receipt-20260821T225047-0300`;
  registered `2026-08-21T22:50:47-03:00` before launch. Exact TMPDIR
  `/tmp/opencode/t34-consolidated-receipt-20260821T225047-tmp` and pytest
  boundary `/tmp/opencode/t34-consolidated-receipt-20260821T225047-pytest` are
  current-run-only resources; no fixed lane port is used.

- Concurrent startup run ID: `t34-concurrent-e2e-bdd-20260821T225159-0300`;
  owner evidence and isolated preflight recorded at
  `2026-08-21T22:51:59-03:00` before launch. Planned current-run resources:
  exact E2E/BDD wrapper PID+PGID, ports `127.0.0.1:8765` and `127.0.0.1:8766`,
  per-lane pytest/TMPDIR boundaries under `/tmp/opencode`, and separate
  stdout/stderr/lifecycle logs. Fixed DB paths were absent at preflight;
  production DB and LAN port 8000 are excluded. No cleanup may target an
  unregistered or foreign resource.

## Owner-authorized I10 receipt remediation — corrected run registration

- Run ID: `t34-i10-remediation4-focused2-20260821T190702-0300`
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`
- Owner evidence: registration recorded before launch at
  `2026-08-21T19:07:02-03:00`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `664218` | T34 I10 remediation / apply | corrected wrapper PID/PGID before exec | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | exited | owned-cleaned | 66 passed, 1 failed; deterministic test drift corrected | idempotent no-op; already exited |
| process group | PGID `664218` | T34 I10 remediation / apply | corrected wrapper PGID before exec | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | exited | owned-cleaned | no group residue | idempotent no-op; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused2-pytest` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | absent | owned-cleaned | exact basetemp | exact bounded removal; absent |
| temporary path | `/tmp/opencode/t34-i10-remediation4-focused2-tmp` | T34 I10 remediation / apply | exact path registered before creation | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | absent | owned-cleaned | exact TMPDIR/dynamic DB boundary | exact bounded removal; absent |
| test DB resource | dynamic DB under registered TMPDIR | T34 I10 remediation / apply | fixture path under exact boundary | 2026-08-21T19:07:38-03:00 | 2026-08-21T19:08:00-03:00 | absent | owned-cleaned | test-only dynamic DB | exact parent cleanup; absent |

## Owner-authorized isolated E2E/BDD/manifest remediation — run registration

- Owner authorization: remove only exact `/tmp/pytest-of-juca` and
  `data/test_bdd.db`; no parent, wildcard, broad, process, port, or unrelated
  test-DB cleanup. Exact metadata was captured before removal; both paths are
  absent after removal.
- E2E run ID registered before launch:
  `t34-e2e-readiness-20260821T195950-0300`; BDD run ID will be registered with
  its own timestamp immediately before BDD launch.
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58`
  / `apply`.
- Planned exact resources per run: one `setsid` taskipy/pytest process group,
  one exact pytest basetemp under `reports/test-profile/`, one exact TMPDIR
  under `/tmp/opencode/`, stdout/stderr logs, and lane ports E2E `8765/8767`
  or BDD `8766`. `data/test_e2e.db` and `data/test_e2e_short_ttl.db` are
  test-only lane resources but are not authorized cleanup targets in this pass.
- Owner evidence and timestamps are recorded here before each process launch;
  actual PID/PGID, readiness polls, child/server events, stdout/stderr, exit,
  and teardown are appended after each bounded run. Unknown or unowned
  resources remain untouched and block trusted cleanup.

### E2E run receipt

- Run ID `t34-e2e-readiness-20260821T195950-0300`; registration `2026-08-21T20:00:33-03:00`.
- Exact boundaries registered before launch:
  `reports/test-profile/.t34-e2e-readiness-20260821T195950-pytest` and
  `/tmp/opencode/t34-e2e-readiness-20260821T195950-tmp`.
- Wrapper PID/PGID `668358/668358`; lineage observed as taskipy `668369`,
  shell `668370`, uv pytest `668374`, Playwright driver `668384`, and uvicorn
  children `668477` (`8765`) and `669950` (`8767`), all in PGID `668358`.
- Focused command: `PYTHONPATH=./scripts T29_RUN_ID=... T29_DB_RECEIPT_LANE=e2e
  PYTEST_ADDOPTS=--basetemp=... TMPDIR=... uv run task test-e2e`.
- stdout/stderr/lifecycle receipts:
  `reports/test-profile/t34-e2e-readiness-20260821T195950.{stdout,stderr,lifecycle}.log`.
- Result: stdout reports `51 passed in 178.45s`; stderr empty. Readiness polls
  observed exact listeners `127.0.0.1:8765` and `127.0.0.1:8767`, with owned
  uvicorn PIDs above. No E2E refusal, EPIPE, or server event error occurred.
- Lifecycle caveat: outer validation shell hit its 180s tool bound before it
  appended wait/exit; later exact PID/PGID and ports were absent. Exit code and
  final teardown therefore remain `unknown`, not green acceptance evidence.
- Resource receipt: wrapper/group `owned-cleaned` by exact postflight absence;
  exact pytest/TMPDIR paths and E2E fixed DBs remain current-run evidence and
  were not deleted because owner authorized cleanup only for the two exact
  paths named above. No foreign process, port, DB, or broad path was touched.

### BDD run registration

- Run ID `t34-bdd-readiness-20260821T200441-0300`; registration recorded before
  launch at `2026-08-21T20:04:41-03:00`.
- Exact boundaries: `reports/test-profile/.t34-bdd-readiness-20260821T200441-pytest`
  and `/tmp/opencode/t34-bdd-readiness-20260821T200441-tmp`; stdout/stderr/
  lifecycle logs use same run ID. BDD port `8766`; exact `data/test_bdd.db`
  may be removed only after this run proves current-run ownership and records
  post-run metadata.

### E2E/BDD bounded-result receipt and exact cleanup

- BDD completed with trustworthy lane result: `reports/test-profile/t34-bdd-readiness-20260821T200441.stdout.log`
  reports `51 passed in 151.49s`; stderr is empty. Lifecycle log ends with
  `exit=0` at `2026-08-21T20:07:41-03:00`. Exact process lineage was wrapper
  PID/PGID `671094/671094`, taskipy `671105`, shell `671106`, pytest `671110`,
  server `671124` on `127.0.0.1:8766`, and Alembic children `671119`/`671141`,
  all observed in current-run PGID `671094`. Port was LISTEN only with owned
  server PID `671124`; final lifecycle poll shows no listener and server
  process absent. No refusal, EPIPE, PID-not-found, or test failure occurred.
- BDD fixed DB metadata was captured before authorized cleanup:
  `data/test_bdd.db`, size `126976`, SHA-256
  `d084d94480e53c9ec6da9efbf08ce18f7e0cc53ea7915813c16ed01226953bd5`.
  Exact file was removed with `rm -f -- data/test_bdd.db`; post-stat is absent.
  No other DB path was removed.
- E2E remains incomplete as a lifecycle receipt: stdout reports `51 passed in
  178.45s`, exact owned listeners appeared on `8765` (`668477`) and `8767`
  (`669950`), and no refusal/EPIPE/server-event error appeared. Outer bounded
  shell timed out before appending wait/exit; later exact process/listener
  inventory was absent, but exit and teardown return codes remain unknown.
- E2E exact registered pytest/TMPDIR roots remain present and untouched because
  owner authorization allowed deletion only for `/tmp/pytest-of-juca` and
  `data/test_bdd.db`:
  `reports/test-profile/.t34-e2e-readiness-20260821T195950-pytest` and
  `/tmp/opencode/t34-e2e-readiness-20260821T195950-tmp`. BDD exact registered
  roots also remain present and untouched:
  `reports/test-profile/.t34-bdd-readiness-20260821T200441-pytest` and
  `/tmp/opencode/t34-bdd-readiness-20260821T200441-tmp`. These are
  `owned-current-run` residue with complete registration evidence, not cleanup
  targets under current authorization. Fixed E2E DBs remain untouched test-only
  resources: `data/test_e2e.db` SHA-256
  `7a6a8fbccbc6d46f7d1dbeccc5662632af1a52e9d17989d47ecd9bf4ad55d435` and
  `data/test_e2e_short_ttl.db` SHA-256
  `c7eb888813bf69d372643ca3b0261177b083339279f478002d416428283394f1`.
- Postflight inventory at `2026-08-21T20:11:10-03:00` observed no relevant runner,
  pytest, Playwright, or uvicorn process and no listener on `8765-8768`; the
  only matching `pgrep` row was inventory shell self-observation. No foreign
  resource was adopted or acted on.

### Manifest/skip attribution and amendment stop

- Direct source inspection confirms `tests/AUDIT.md` is current governance:
  lines 4, 13, 85-90 declare `1,032` blocking/manifest nodes plus 12
  versioned outside-lane T32 cases and two skipped nodes. `scripts/build_test_inventory.py`
  lines 22-26 defines the same six lanes and exact `EXPECTED_SKIPS`; lines
  127-134 require proof receipts to match `load_manifest(ROOT / "tests/AUDIT.md")`
  population, checksum, and skip IDs; lines 238-246 generate the same summary.
  Historical `1,043` receipts are not current governance. No manifest or skip
  edit is authorized by T34.
- Task 4.2 remains blocked: no published Taskipy release fixes the verified
  `taskipy/task_runner.py` absent-PID race. Therefore no `pyproject.toml`,
  `uv.lock`, runner invocation, installed package, or regression-test edit is
  authorized. Conditional task 4.4 and gate task 4.5 cannot run without a
  supported remedy. Review task 3.2 remains review-owned.

### Final bounded ownership receipt for isolated E2E/BDD remediation

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `668358`, E2E wrapper | T34 E2E/BDD remediation / apply | exact run registration and lifecycle launch record | 2026-08-21T20:00:33-03:00 | 2026-08-21T20:11:10-03:00 | absent/exit-unknown | owned-cleaned for observed postflight | exact lineage and ports; stdout `51 passed`; outer wait receipt missing | no cleanup action; idempotent no-op on absent observed resource; final exit/teardown untrusted |
| process group | PGID `668358` | T34 E2E/BDD remediation / apply | exact lifecycle PGID record | 2026-08-21T20:00:33-03:00 | unknown; later inventory absent | absent | owned-cleaned | no current-run group observed postflight | idempotent no-op; already absent |
| child process | PID `671094`, BDD wrapper | T34 E2E/BDD remediation / apply | exact run registration and lifecycle launch record | 2026-08-21T20:05:05-03:00 | 2026-08-21T20:07:41-03:00 | exited | owned-cleaned | lifecycle `exit=0`; 51 tests passed | idempotent no-op; already exited |
| process group | PGID `671094` | T34 E2E/BDD remediation / apply | exact lifecycle PGID record | 2026-08-21T20:05:05-03:00 | 2026-08-21T20:07:41-03:00 | exited | owned-cleaned | no descendant/listener after final poll | idempotent no-op; already absent |
| port | `127.0.0.1:8766`, server PID `671124` | T34 E2E/BDD remediation / apply | lifecycle LISTEN record tied to BDD PGID | 2026-08-21T20:05:15-03:00 | 2026-08-21T20:07:41-03:00 | absent | owned-cleaned | exact port owned during run; absent final poll | fixture/task teardown; no host-wide port action |
| temporary path | `reports/test-profile/.t34-e2e-readiness-20260821T195950-pytest` | T34 E2E/BDD remediation / apply | exact path registered before E2E launch | 2026-08-21T20:00:33-03:00 | 2026-08-21T20:11:10-03:00 | present | owned-current-run | exact path exists at postflight observation | untouched; authorization did not include path |
| temporary path | `/tmp/opencode/t34-e2e-readiness-20260821T195950-tmp` | T34 E2E/BDD remediation / apply | exact path registered before E2E launch | 2026-08-21T20:00:33-03:00 | 2026-08-21T20:11:10-03:00 | present | owned-current-run | exact path exists at postflight observation | untouched; authorization did not include path |
| temporary path | `reports/test-profile/.t34-bdd-readiness-20260821T200441-pytest` | T34 E2E/BDD remediation / apply | exact path registered before BDD launch | 2026-08-21T20:05:05-03:00 | 2026-08-21T20:11:10-03:00 | present | owned-current-run | exact path exists at postflight observation | untouched; authorization did not include path |
| temporary path | `/tmp/opencode/t34-bdd-readiness-20260821T200441-tmp` | T34 E2E/BDD remediation / apply | exact path registered before BDD launch | 2026-08-21T20:05:05-03:00 | 2026-08-21T20:11:10-03:00 | present | owned-current-run | exact path exists at postflight observation | untouched; authorization did not include path |
| test DB resource | `data/test_bdd.db` | T34 E2E/BDD remediation / apply | exact BDD lane receipt plus pre-delete metadata | 2026-08-21T20:05:05-03:00 | 2026-08-21T20:11:10-03:00 | absent | owned-cleaned | exact current-run fixed DB; SHA-256 recorded above; absent at final receipt observation | exact `rm -f -- data/test_bdd.db`; post-stat absent |
| test DB resource | `data/test_e2e.db`, `data/test_e2e_short_ttl.db` | T34 E2E/BDD remediation / apply | exact E2E lane receipt; test-only fixed DBs | 2026-08-21T20:00:33-03:00 | 2026-08-21T20:11:10-03:00 | present | owned-current-run | exact files remain at postflight observation; hashes recorded above | untouched; authorization did not include paths |

Cleanup decision: only authorized exact `/tmp/pytest-of-juca` and
`data/test_bdd.db` were removed. All other current-run paths and test DBs were
left untouched. Canonical review isolation is not satisfied while registered
current-run temp roots remain, and E2E exit/teardown evidence is incomplete.
Stop with `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; do not run canonical suite or
perform further cleanup without owner authorization.

### Post-receipt dossier validation registration

- Run ID: `t34-e2e-bdd-receipt-dossier-validation-20260821T201110-0300`.
- Owner: `t34/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58` / `apply`.
- Owner evidence: registration written before validation commands at
  `2026-08-21T20:11:10-03:00`. Planned resources: one OpenSpec CLI process and
  one git-check process; no DB, port, test-temp, server, or cleanup resource.
- Cleanup rule: process resources only; no filesystem or host cleanup.

- Validation result: `openspec validate t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 --type change --strict --json` -> `valid=true`; `rtk git diff --check -- openspec/changes/t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58/tasks.md` -> clean. Wrapper PID/PGID `674196/674196`, started `2026-08-21T20:12:30-03:00`, absent by `2026-08-21T20:12:34-03:00`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `674196` | T34 dossier validation / apply | exact `setsid` wrapper identity printed before OpenSpec command | 2026-08-21T20:12:30-03:00 | 2026-08-21T20:12:34-03:00 | exited | owned-cleaned | change validation passed; diff check clean | idempotent no-op; already absent |
| process group | PGID `674196` | T34 dossier validation / apply | exact `setsid` PGID printed before command | 2026-08-21T20:12:30-03:00 | 2026-08-21T20:12:34-03:00 | exited | owned-cleaned | no descendant/resource residue | idempotent no-op; group absent |

## Final apply validation registration

- Run ID: `t34-final-focused-validation-20260821T230131-0300`.
- Owner: `t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 / apply`.
- Owner evidence: registration written before validation launch at
  `2026-08-21T23:01:31-03:00`.
- Planned resources: exact validation child/process group, OpenSpec validation
  child/process group, Ruff/compile child/process group, and exact test paths
  `/tmp/opencode/t34-final-focused-validation-pytest` and
  `/tmp/opencode/t34-final-focused-validation-tmp`. No DB, listener, server,
  production path, or unregistered temporary cleanup resource. Existing
  worktree files outside T34 mapped files remain pre-existing and untouched.
- Cleanup rule: reconcile only exact validation process/group entries; record
  already-absent resources as idempotent no-op. No filesystem or host cleanup.
- Final receipt wrapper/log registration: `setsid` wrapper PID/PGID and
  `/tmp/opencode/t34-final-focused-validation-20260821T230324.log` are recorded
  by the wrapper before executing validation. Exact test boundaries above remain
  the only temporary paths eligible for cleanup.

### Consolidated remediation completion evidence

- C1: `scripts/run_full_suite.py` now accepts only runner-registered lane temp
  boundaries, reconciles emitted dynamic DB paths independently of collection
  completeness, and preserves unknown/out-of-bound paths. Focused harness and
  receipt tests pass; no production DB target was accessed.
- C2: run/lane receipts now persist monotonic elapsed timing, wall-clock phase
  bounds, lifecycle observations, and receipt-write/finalization timing without
  changing the 300-second deadline or fail-fast policy.
- C3: concurrent run
  `t34-concurrent-e2e-bdd-20260821T225159-0300` reached owned readiness on
  `127.0.0.1:8765` and `127.0.0.1:8766`; server launch/readiness events carried
  matching run/lane/PID/PGID identity. E2E/BDD later produced application/test
  failures and the bounded harness timed out before natural exit, so no T34
  lifecycle fault was proven and no shared lifecycle edit was made. Exact owned
  groups were SIGTERM-cleaned; no SIGKILL was needed; ports and descendants were
  absent afterward. This is diagnostic completion, not canonical acceptance.
- C4: final validation wrapper PID/PGID `691535/691535`, registered before use
  at `2026-08-21T23:03:49-03:00`, exited `0` at `2026-08-21T23:03:53-03:00`:
  `uv run task test-file tests/scripts/test_t29_harness.py` -> `70 passed in
  0.41s`; `uv run task test-file scripts/test_t29_receipt_harness.py` -> `8
  passed in 0.83s`; `python3 -m py_compile ...` -> pass; targeted Ruff -> pass;
  `uv lock --check` -> pass. `openspec validate ... --type change --strict`
  -> `valid=true`; `openspec validate --specs --strict` -> `70/70 valid`;
  `git diff --check` -> clean.

### RC disposition

- RC-1 dynamic DB ownership: **resolved**. Early receipt publication and exact
  boundary reconciliation preserve valid test-only ownership through interrupted
  collection; no production path is eligible.
- RC-2 timing attribution: **resolved for instrumentation**. Phase/run/lane
  timing and receipt persistence are present; canonical duration/coverage result
  remains review-owned.
- RC-3 concurrent E2E/BDD startup: **not a proven T34 fault**. Both exact ports
  became ready with owned children; observed test failures lack evidence tying
  them to runner/shared-server lifecycle. Stop without speculative repair.

### Final validation ownership receipt

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `691535` | T34 final focused validation / apply | `setsid` wrapper printed PID/PGID before validation commands | 2026-08-21T23:03:49-03:00 | 2026-08-21T23:03:53-03:00 | exited | owned-cleaned | all focused tests, compile, Ruff, and lock checks exit 0 | idempotent no-op; PID absent after exit |
| process group | PGID `691535` | T34 final focused validation / apply | wrapper PGID matched recorded PID before command use | 2026-08-21T23:03:49-03:00 | 2026-08-21T23:03:53-03:00 | exited | owned-cleaned | no descendant or listener residue | idempotent no-op; group absent |
| temporary path | `/tmp/opencode/t34-final-focused-validation-pytest` | T34 final focused validation / apply | exact path registered before test launch; owner stat `1000:1000`, mode `700` | 2026-08-21T23:03:49-03:00 | 2026-08-21T23:03:54-03:00 | cleanup-attempted | owned-cleaned | exact pytest boundary created by current run | exact bounded removal; absent after cleanup |
| temporary path | `/tmp/opencode/t34-final-focused-validation-pytest-receipt` | T34 final focused validation / apply | exact path registered before receipt test launch; owner stat `1000:1000`, mode `700` | 2026-08-21T23:03:49-03:00 | 2026-08-21T23:03:54-03:00 | cleanup-attempted | owned-cleaned | exact receipt-test boundary created by current run | exact bounded removal; absent after cleanup |
| temporary path | `/tmp/opencode/t34-final-focused-validation-tmp` | T34 final focused validation / apply | exact TMPDIR registered before launch | 2026-08-21T23:03:49-03:00 | 2026-08-21T23:03:54-03:00 | absent | absent | no path created | idempotent no-op; already absent |
| temporary path | `/tmp/opencode/t34-final-focused-validation-tmp-receipt` | T34 final focused validation / apply | exact TMPDIR registered before receipt launch | 2026-08-21T23:03:49-03:00 | 2026-08-21T23:03:54-03:00 | absent | absent | no path created | idempotent no-op; already absent |
| port | `127.0.0.1:8765-8768` | T34 final focused validation / apply | exact post-run `ss` inventory | 2026-08-21T23:03:54-03:00 | 2026-08-21T23:03:54-03:00 | absent | absent | no listener | untouched; idempotent no-op |

Final cleanup decision: only exact current-run validation boundaries were
removed; process/group resources were already absent. No foreign, pre-existing,
unknown, production, LAN, fixed-DB, or unregistered resource was touched.

### Canonical review isolation observation

- Inventory at `2026-08-21T23:05:31-03:00`: no relevant runner/pytest/Playwright/
  uvicorn process, no listener on `8765-8768`, and exact known paths
  `/tmp/pytest-of-juca`, `data/test_bdd.db`, `data/test_e2e.db`,
  `data/test_e2e_short_ttl.db`, plus concurrent-run temp boundaries were absent.
  The inventory command's own shell row matched search terms and was excluded as
  self-observation; it was not adopted or acted on. No baseline or allowlist
  exception used.
- Review can perform trusted preflight only if same isolated state remains. This
  apply pass did not launch canonical `uv run task test`.

### Apply stop result

Focused implementation and validation are green. Apply cannot claim canonical
acceptance: review task 3.2 remains open, conditional Taskipy task 4.2 has no
supported fixed release, and task 4.5 is consequently blocked. Return
`BLOCKED_FOR_IMPLEMENTATION_BRIEF` rather than `READY_FOR_REVIEW`.

## Owner-authorized final concurrent-startup remediation

### Preflight and registration

- Owner authorization: one bounded final remediation for I10 Review R7-F02.
  Scope is limited to proven shared runner/server/browser startup boundary in
  `scripts/run_full_suite.py`, `tests/support/server.py`,
  `tests/support/browser.py`, `tests/conftest.py`, and
  `tests/scripts/test_t29_harness.py`, plus directly required receipt helper.
  No product/F58/MyProfit, E2E/BDD test or feature, I10 vector/policy,
  topology/lane order, retry/skip/xfail, timeout, DB/seed/migration, I08/T33,
  LAN service, or canonical `uv run task test` action is authorized.
- `git diff HEAD~1` captured before this pass; existing T34/I10 evidence and
  prior findings remain preserved. Preflight at `2026-08-21T23:44:09-03:00`:
  no runner/pytest/Playwright/uvicorn process, ports `8765-8768` absent,
  fixed test DBs absent, and `/tmp/pytest-of-juca` absent. LAN port `8000`
  was not inspected as a suite resource and remains untouched.
- Run ID: `t34-final-concurrent-startup-20260821T234409-0300`.
  Owner: `t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 /
  apply`. Owner evidence and registration timestamp were recorded before
  launch. Planned resources: six exact direct lane child PIDs/PGIDs, E2E
  ports `127.0.0.1:8765`/`8767`, BDD port `127.0.0.1:8766`, visual port
  `127.0.0.1:8768`, six exact lane temp boundaries, six stdout/stderr logs,
  and test-only DB receipts. Only current-run registered resources may be
  cleaned; foreign, unknown, pre-existing, contradictory, and unregistered
  resources remain untouched.
- Exact registered paths before launch:
  `/tmp/opencode/t34-final-concurrent-startup-20260821T234409-{unit,integration,audit,e2e,bdd,visual}-pytest`
  and matching `.stdout.log`/`.stderr.log` files under `/tmp/opencode/`.
  Exact process/group identities are assigned by each
   `start_new_session=True` `Popen` and recorded immediately after launch.

### Final concurrent-startup diagnosis result

- E2E, BDD, and visual browser failures are source-attributed to Chromium's
  Unix socket limit, not T34 server/runner lifecycle. Logs contain fatal
  `chrome/browser/process_singleton_posix.cc:313: Socket path too long` for
  `.../t34-final-concurrent-startup-20260821T234409-0300-{e2e,bdd,visual}-pytest/.../SingletonSocket`.
  Resulting Playwright `TargetClosedError` is downstream of that fatal child
  exit.
- BDD server reached owned readiness on `127.0.0.1:8766` at
  `2026-08-21T23:46:45.721038-03:00` before browser launch. This rules out BDD server
  readiness as cause of observed browser failures. Visual/E2E logs show same
  socket-path failure family.
- Integration lane failures are independent SQLite setup failures in concurrent
  diagnostic, not shared runner/server startup exceptions. No runtime source
  change is justified by this run.
- Canonical runner boundary remains safe: `_create_lane_temp_root()` creates
  `/tmp/o-*` roots and rejects derived Chromium socket path at or above
  `UNIX_SOCKET_PATH_MAX`; existing focused contract
  `test_runner_temp_boundary_is_chromium_socket_safe_and_reconciles_exactly`
  covers it. Diagnostic long manually supplied roots did not exercise canonical
  boundary.
- Disposition: `BLOCKED_FOR_IMPLEMENTATION_BRIEF` for this diagnostic gate;
  preserve R7 evidence, do not add browser retry, shorten paths inside shared
  browser code, alter lane topology, or run canonical suite in apply.

### Final concurrent-startup ownership receipt

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | PID `700671` unit | T34 final concurrent startup / apply | Popen PID recorded immediately under registered run ID | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | exact lane child receipt; signaled after bounded observation | owned group exited; no retry |
| child process | PID `700672` integration | T34 final concurrent startup / apply | Popen PID recorded immediately under registered run ID | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | SQLite setup failures retained in lane log | owned group exited; no retry |
| child process | PID `700673` audit | T34 final concurrent startup / apply | Popen PID recorded immediately under registered run ID | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | bounded diagnostic lane receipt | owned group exited; no retry |
| child process | PID `700674` E2E | T34 final concurrent startup / apply | Popen PID recorded immediately under registered run ID | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | Chromium socket-path failure in descendants | owned group exited; no retry |
| child process | PID `700675` BDD | T34 final concurrent startup / apply | Popen PID recorded immediately under registered run ID | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | server ready, browser socket failure, exact group signal | owned group exited; no retry |
| child process | PID `700676` visual | T34 final concurrent startup / apply | Popen PID recorded immediately under registered run ID | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | Chromium socket-path failure in descendants | owned group exited; no retry |
| process group | PGIDs `700671`, `700672`, `700673`, `700674`, `700675`, `700676` | T34 final concurrent startup / apply | `start_new_session=True`; actual PGID recorded after launch | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | exact current-run groups only | bounded SIGTERM; no SIGKILL; absent postflight |
| child process | PID `700701` BDD server | T34 final concurrent startup / apply | server launch event ties child to BDD lane PGID `700675` | `2026-08-21T23:46:37-03:00` | `2026-08-21T23:47:15-03:00` | exited | owned-cleaned | BDD ready then exact teardown | fixture/owned-group teardown; absent |
| port | `127.0.0.1:8766` | T34 final concurrent startup / apply | BDD server event ties listener to PID `700701`/PGID `700675` | `2026-08-21T23:46:37-03:00` | `2026-08-21T23:47:15-03:00` | absent | owned-cleaned | BDD ready event then exact postflight absence | fixture/owned-group teardown; absent |
| temporary path | six `/tmp/opencode/t34-final-concurrent-startup-...-pytest` roots | T34 final concurrent startup / apply | exact paths registered before launch | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | present | owned-current-run | diagnostic roots retained as evidence; not canonical runner roots | untouched; no cleanup authorization |
| log | `/tmp/opencode/t34-final-concurrent-startup-20260821T234409-0300-*` | T34 final concurrent startup / apply | exact paths registered before launch | `2026-08-21T23:46:32-03:00` | `2026-08-21T23:47:15-03:00` | retained | owned-current-run | browser/server/integration causal evidence | retained; no deletion |

Cleanup decision: exact current-run groups and BDD listener were bounded and
absent after observation. Registered diagnostic temp roots and logs remain
owned-current-run evidence because this pass had no authorization to remove
them. No foreign, unknown, pre-existing, production, LAN, fixed-DB, or broad
`/tmp` resource was touched.

### Post-diagnosis dossier validation registration

- Run ID: `t34-final-concurrent-diagnosis-validation-20260821T235300-0300`.
- Owner: `t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 / apply`.
- Owner evidence: registration written before validation commands at
  `2026-08-21T23:53:00-03:00`.
- Planned resources: one OpenSpec CLI child/process group and one git-check
  child/process group. No DB, listener, server, browser, or temporary path is
  used or eligible for cleanup.
- Cleanup rule: reconcile only exact registered process/group entries; record
  already-absent resources as idempotent no-op. No filesystem or host cleanup.
- Validation process registration: exact shell child/process group for
  `git status --short` and `git diff --stat`, to be recorded before invocation.

### Post-diagnosis dossier validation result

- `openspec validate t34-diagnosticar-e-corrigir-bloqueadores-do-runner-harness-para-f58 --type change --strict --json` -> valid; 1/1 passed.
- `openspec validate --specs --strict --json` -> valid; 70/70 passed. Informational long-requirement notices only.
- `git diff --check` -> passed.
- `git status --short` / `git diff --stat` -> confirmed broad pre-existing
  worktree boundary. T34-owned changes remain dossier files plus previously
  mapped T34 implementation/test files; no unrelated file was edited by this
  validation pass.

### Post-diagnosis validation ownership receipt

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process / process group | PID/PGID `702453` | T34 dossier validation / apply | self-registration printed before OpenSpec and diff commands under exact run ID | `2026-08-21T23:53:31-03:00` | `2026-08-21T23:53:31-03:00` | exited | owned-cleaned | exact `setsid` wrapper completed all three validation commands; post-check found no PID | idempotent no-op; no child/group residue |
| child process / process group | PID/PGID `702829` | T34 dossier validation / apply | self-registration printed before git status/stat/check commands under exact run ID | `2026-08-21T23:54:32-03:00` | `2026-08-21T23:54:32-03:00` | exited | owned-cleaned | exact `setsid` wrapper completed status, stat, and diff-check commands | idempotent no-op; no child/group residue |

Validation cleanup decision: only exact current-run wrappers were reconciled;
both exited cleanly and required no cleanup. No foreign, pre-existing,
unknown, listener, DB, temporary-path, LAN, or production resource was acted
on.

## Review Findings

### Review R5

Scope audit: proposal **pass**; design and implementation decisions **pass**;
delta specs `dev-tasks` and `shared-test-support` **pass**; exact temporary
resource policy parity across `.opencode/agents/review.md`,
`.opencode/agents/apply.md`, `.opencode/skills/openspec-apply-change/SKILL.md`,
and `AGENTIC_DEVELOPMENT.md` **pass**; runner receipt/lifecycle focused
contracts **pass**; exact owned cleanup, out-of-bound preservation, and
declared-boundary mismatch/foreign blocking **pass**; no broad cleanup,
allowlist, test deletion, lane/retry/skip/xfail change, or direct-dispatch
change **pass**; scope exclusions F58/MyProfit, product, D05, I08, T33,
and unrelated worktree files **pass**; focused acceptance **pass**; task 3.2
and canonical task 4.5 correctly deferred by maintenance suspension; conditional
Taskipy tasks 4.2/4.4 remain stopped because no supported fixed release exists,
outside this policy-only approval boundary **pass**; complete scope audit
**pass**.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**; elapsed
0s, duration limit `300s`, cleanup not applicable. Canonical command was not
launched, per owner-authorized I10 state in `openspec/config.yaml:85-100` and
the review policy at `.opencode/agents/review.md:93-103`. Six lanes: unit
not run; integration not run; audit integration not run; e2e not run; bdd not
run; visual not run. Coverage, tests/skips, node reconciliation, and fail-fast
disposition are canonical-only and deferred until reactivation. No red test
exists in this review because no canonical process started.

Preflight: no fresh process/listener/DB/temp operation performed, per gate
request and suspended policy. Canonical preflight is not applicable while
suite gate is suspended. Durable focused ledgers were inspected: current-run
resources have complete ownership fields and end `absent`/`owned-cleaned`;
out-of-bound `/tmp/pytest-of-juca` is preserved/non-target and was not adopted,
deleted, or allowlisted. No baseline or allowlist exception used.

Postflight: no canonical run, therefore no canonical child cleanup or postflight
inventory. Focused postflight evidence in this dossier records wrapper/group,
exact declared temp roots, ports, and test-only DB resources as
`absent`/`owned-cleaned` or untouched pre-existing; no foreign action occurred.

Runner isolation: canonical isolated-runner precondition **deferred**, not
failed; it becomes mandatory on I10 reactivation. Relevant policy requires
only exact runner-declared run/lane temp paths to be cleanup-relevant. Exact
current-run receipt match permits bounded cleanup as `owned-cleaned`; exact
absence is `absent`; mismatch/unknown/foreign/contradictory state inside a
declared boundary remains untouched and blocks affected operation. Any path
outside declared boundaries, including `/tmp/pytest-of-juca`, is
`preserved/non-target` and cannot block alone. No pathname, parent, broad `/tmp`,
`pytest-of-*`, or literal-path inference is permitted.

Focused evidence: receipt-bearing policy run
`uv run task test-file tests/scripts/test_t29_harness.py` -> **71 passed in
2.12s**; exact declared temp root `owned-cleaned`; mismatch/foreign paths
preserved and untrusted; synthetic `/tmp/pytest-of-juca` inventory reported
`relevant=false`, `cleanup_target=false`, `preserved=true`,
`allowlisted=false`, `adopted=false`, `ok=true` (tasks evidence
`1845-1867`). Final focused runner/support validation -> `70 passed in 0.41s`
and receipt harness `8 passed in 0.83s`; targeted Ruff, compile, lock, change
validation, stable-spec validation (`70/70`), and diff check passed (tasks
evidence `2132-2184`). Existing lifecycle evidence also records audit `40
passed`, BDD `51 passed`, and visual `8 passed` with owned readiness/teardown;
canonical acceptance remains deferred.

Specs/diff: T34 delta requirements and scenarios explicitly distinguish
declared-boundary resources from out-of-bound observations. Policy diff is
limited to four named policy documents; delta specs carry exact-boundary
language; no runtime/product/F58/MyProfit/D05/I08/T33 file is claimed by this
review. Stable specs and strict change validation remain valid per durable
apply receipt.

Verdict: **APPROVED**

No blocking findings. Canonical suite absence is non-blocking only because
owner-authorized `maintenance-suspended` is explicit. Reactivation must first
resolve I10 diagnosis, then run exactly one isolated green six-lane suite
through cleanup in `<=300s`; no canonical task is approved as completed here.
