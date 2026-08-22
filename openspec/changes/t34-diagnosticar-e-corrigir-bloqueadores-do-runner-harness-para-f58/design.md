## Context

T34 is consolidated follow-up for F58 R6. R6 evidence is bounded and
specific:

- `reports/test-profile/20260820T214446-integration.log:12-16` reports
  `process PID not found (pid=533637)` while integration was running.
- `reports/test-profile/20260820T214446-visual.log:39-135` reports all eight
  visual nodes errored because `127.0.0.1:8768` never became ready after its
  child exited; server output was empty.
- `reports/test-profile/20260820T214446-run.json:5-7,81-82` says cleanup was
  complete, while R6 postflight found `/tmp/pytest-of-juca` created during the
  same run.

R6 found no F58 symbol in either failure. R5/R6 and D05/I08 vocabulary define
  safe ownership terms: `owned-current-run`, `owned-cleaned`, `absent`,
  `foreign`, `unknown`, and `pre-existing`. T34 consumes that vocabulary; it
  does not reopen D05, T33, or I08.

### Code map

| File / symbols | Role in current flow |
|---|---|
| `scripts/run_full_suite.py::LANES`, `LANE_PORTS`, `LANE_DATABASES`, `KNOWN_DATABASES` | Canonical six-lane topology, task names, ports, fixed DB allow-list. Preserve exactly. |
| `scripts/run_full_suite.py::_lane_metadata`, `_preflight`, `_persist_receipt` | Creates ownership placeholders, validates canonical resources, and persists run JSON before/through lifecycle. |
| `scripts/run_full_suite.py::main` nested `launch`, `monitor`, `handle_signal`, plus `_stop`, `_reap`, `_final_exit_code` | Launches taskipy children, observes failure/fail-fast/deadline, signals owned groups, reaps children, and selects causal exit code. |
| `scripts/run_full_suite.py::_collection`, DB receipt parsing, finalization | Converts lane logs/timings/DB lines into node/skip/coverage and cleanup reconciliation. Add exact temp receipt reconciliation here, never broad filesystem discovery. |
| `tests/support/server.py::run_test_server` | Builds lane server environment, launches uvicorn, waits for readiness, yields `127.0.0.1:<port>`, and tears down the spawned process. |
| `tests/support/browser.py::wait_for_port`, `uvicorn_log_file`, `read_log_tail`, `shutdown_uvicorn` | Socket readiness, child-poll checks, server diagnostics, bounded terminate/kill/wait. Preserve host/port and browser args. |
| `tests/conftest.py::_omaha_test_env`, module-load safe DB setup, marker allow-lists | Binds test imports to dynamic safe DB before collection and owns explicit marker classification. Publish current pytest temp-root receipt without changing marker decisions or DB binding. |
| `tests/support/db.py::prepare_safe_test_database`, `prepare_worker_database`, `emit_db_receipt` | Creates dynamic safe DB roots and emits lane-scoped DB receipt lines. Extend receipt helper for exact run/lane temp ownership only. |
| `tests/scripts/test_t29_harness.py` existing runner/server/receipt tests | Unit-owned controlled oracle for stale listener, ownership matrix, lifecycle races, six-lane receipts, reconciliation, fail-fast, timeout, and production-DB refusal. Extend; do not delete or weaken. |
| `pyproject.toml:[tool.taskipy.tasks]::test*` | Canonical taskipy command boundary. Inspection only; change only if bounded evidence identifies direct task/config causality. |

### Current relevant flow

1. `uv run task test` invokes `uv run python -m scripts.run_full_suite`.
2. Runner preflights ports `8765-8768`, refuses production DB targets, loads
   manifest/governance, creates one run ID and six lane metadata records, then
   launches each existing `uv run task <lane>` child with `start_new_session`.
3. Current metadata records runner PID and assumes `pgid == child PID` after
   `Popen`, but does not retain a complete parent/child/actual-PGID lifecycle
   timeline. Stop/reap observes expected disappearance, yet R6 integration
   evidence cannot prove which process/parent/PGID exited or when.
4. Each lane emits `T29_DB_TARGET` from its conftest. Dynamic unit/integration/
   audit DB roots and pytest `tmp_path` roots are not represented in the run
   receipt as exact current-run resources. Runner therefore can report clean
   while postflight discovers a pytest root created during the run.
5. Visual/e2e/BDD fixtures call `run_test_server`. It starts uvicorn, opens a
   per-server log, calls `wait_for_port(..., process=proc)`, and yields after a
   TCP accept. Readiness and teardown diagnostics are not structured with
   run/lane ID, parent/child/PGID, readiness timestamp, or port observation
   timeline. The helper must never accept a stale listener for a dead child.
6. On first lane failure, runner records fail-fast, signals remaining owned
   lane groups, reaps them, reads logs/timings/DB receipts, reconciles nodes and
   skips, and persists final cleanup. Cleanup observations must not replace the
   first causal failure or turn missing evidence into green.

Boundary conditions: no production `data/portfolio.db`; no host-wide process or
port scan; no foreign/pre-existing resource adoption; no broad `/tmp` traversal
or deletion; no retries, skips, xfails, lane removal/serialization, coverage
change, manifest change, or browser navigation retry.

## Goals / Non-Goals

**Goals:**

- Make every integration lane lifecycle auditable by run ID, lane, parent PID,
  child PID, actual PGID, launch/start/end times, poll/wait/exit observations,
  signal phase, and return code.
- Make visual server readiness prove spawned-child liveness and preserve a
  launch/readiness/port/log/teardown timeline for `127.0.0.1:8768`.
- Register exact current-run pytest temp roots and reconcile them with receipt
  and postflight state; clean only exact roots created by this run when their
  ownership evidence is complete.
- Correct only an evidence-confirmed runner/harness boundary and lock it with
  deterministic focused tests.
- Produce exactly one later trusted green canonical suite receipt within 300s,
  with six lanes, fail-fast, coverage, skips, reconciliation, and DB isolation
  intact.

**Non-Goals:**

- No F58 connector, MyProfit, application route/model/template, seed,
  migration, production DB, or LAN service changes.
- No reopening or editing T33, T32, I08, D05, or their archives/deltas.
- No broad host cleanup, broad `/tmp` scan, name-pattern kill, process adoption,
  foreign-resource termination, or deletion of pre-existing temp roots.
- No retry policy, skip/xfail, lane removal, lane serialization, coverage
  reduction, manifest/checksum change, visual baseline update, or test weakening.
- No separate diagnostic deliverable: instrumentation exists only to select and
  prove the bounded correction in this slice.

## Decisions

### 1. Capture evidence before selecting repair

Runner and server diagnostics use one `T29_RUN_ID` plus lane label. Each
observation is timestamped and records only exact resources already owned or
reported by that lane. The receipt must retain parent PID, child PID, actual
PGID, process state, poll/wait/exit values, and phase-specific errors rather
than collapsing `PID not found` into an unqualified cleanup failure.

Alternative rejected: infer ownership from process name, PID alone, port,
path, or a later host scan. Those signals cannot distinguish PID reuse or a
foreign listener.

### 2. Preserve causal failure and narrow lifecycle races

At launch, record runner parent PID and returned child PID; obtain actual PGID
from the launched child rather than assuming it. Signal/reap only the recorded
current-run PGID. Record `poll`, signal, `wait`, and exit transitions. Treat
only expected disappearance forms (`ProcessLookupError`, `ESRCH`, EPIPE, and
known `NoSuchProcess`) as bounded lifecycle observations. Unexpected errors
remain receipt errors and force nonzero.

Known first lane failure, parent interruption, and deadline remain primary in
`_final_exit_code`; cleanup/receipt uncertainty can force nonzero but cannot
replace known cause.

Alternative rejected: retry signal/wait or suppress all `OSError`. Retry can
hit reused PIDs; broad suppression can falsely claim trusted cleanup.

### 3. Use child-aware visual readiness, not a browser retry

`run_test_server` and `wait_for_port` retain `127.0.0.1`, assigned port, log
path, environment, and bounded timeout. Readiness records child identity and
must fail immediately with child return code plus flushed log tail when child
exits. A TCP listener is acceptable only while the spawned child is alive and
the exact port is the requested lane port. Startup/readiness/teardown events
are emitted into the lane-owned diagnostic stream with run/lane identity.

Diagnosis rules before code change:

- dead child before readiness → correct only the confirmed child/log lifecycle
  boundary; no browser retry;
- stale/foreign listener → reject readiness and preserve listener;
- live owned child with no readiness → retain bounded startup failure and fix
  only the proven server boundary if controlled evidence identifies one;
- runner signal reaches the visual child/group unexpectedly → correct runner
  ownership/PGID handling, not server startup;
- no causal evidence or contradictory evidence → stop with
  `BLOCKED_FOR_IMPLEMENTATION_BRIEF`, no speculative patch.

Alternative rejected: add `page.goto` retries, accept any listener, increase
timeouts without evidence, or serialize visual with another lane.

### 4. Make pytest temp ownership explicit and exact

Runner gives each canonical run/lane a unique, exact pytest temp-root boundary
and passes run/lane identity through child environment. `tests/conftest.py`
obtains the actual `tmp_path_factory.getbasetemp()` path at session setup;
`tests/support/db.py` emits it as a lane-scoped `T29_TEMP_ROOT` receipt. Runner
requires the emitted path to match the run/lane boundary and records it before
cleanup.

After lane exit, runner checks only emitted/declared exact paths. A root created
by this run and containing no foreign/pre-existing evidence is removed as
`owned-cleaned`; absent root is `absent`. Missing receipt, path mismatch,
pre-existing path, foreign owner marker, contradictory timestamps, or cleanup
failure is `unknown`/`foreign`/`pre-existing`, remains untouched, and forces
untrusted nonzero. No traversal starts from `/tmp`, and no parent-level
pytest-root deletion is inferred from a child path.

Alternative rejected: discover `/tmp/pytest-of-*` after the run or delete by
name. R6 specifically proves that broad postflight discovery cannot establish
current-run ownership.

### 5. Preserve canonical suite topology verbatim

Do not alter `LANES`, order, taskipy child commands, `LANE_PORTS`, DB allow-list,
coverage flags, exact skips, manifest reconciliation, fail-fast, or 300-second
deadline. Any task/config edit requires direct evidence from a controlled
reproduction and remains limited to the boundary identified by that evidence.

## Implementation Decisions

### 1. Repair boundaries selected by controlled RED contracts

- **Context:** Existing T29 lifecycle and stale-listener contracts passed, but
  controlled contracts failed because runner metadata lacked an explicit temp
  boundary/lifecycle timeline, `wait_for_port` could not include flushed log
  evidence, and DB support had no run/lane temp receipt helper.
- **Decision:** Add only those three boundaries. Runner records actual PGID from
  `os.getpgid` and signals only that recorded owned PGID; visual helper records
  child-aware startup evidence; pytest receives one exact `--basetemp` path per
  run/lane and publishes it through `T29_TEMP_ROOT` lines.
- **Impact:** Existing lane commands, six-lane order, ports, DB validation,
  fail-fast, coverage, skips, and deadline remain unchanged. Exact temp paths
  may be reconciled; no broad `/tmp` discovery or cleanup is introduced.
- **Evidence:** RED command recorded in `tasks.md` under Diagnosis result;
  current code showed `entry["pgid"] = process.pid`, no lifecycle list,
  `wait_for_port` accepted no log/run/lane context, and `db.py` emitted only
  `T29_DB_TARGET`.

### 2. Keep shared servers inside lane-owned process groups

- **Context:** R2 postflight observed listener `127.0.0.1:8766`, PID/PGID
  `618454`, parent PID `1`, after runner cleanup. `run_test_server` used
  `start_new_session=True`, so runner signal/reap of the pytest lane group
  could not reach its server child.
- **Decision:** Start shared uvicorn without detaching from its lane process
  group. Preserve actual PGID and parent PGID in server events; normal fixture
  teardown uses direct child terminate/kill when both PGIDs match, while a
  distinct recorded group remains eligible for exact group signaling.
- **Impact:** Fail-fast/deadline lane-group signaling reaches BDD/e2e/visual
  servers without port scans or foreign-resource action. Hosts, ports, DB
  paths, browser scopes, and bounded teardown remain unchanged.
- **Evidence:** R2 receipt/postflight identity above plus mapped code at
  `tests/support/server.py::run_test_server` and
  `tests/support/browser.py::shutdown_uvicorn`.

### 3. Make BDD failure and temp receipts survive pytest progress output

- **Context:** R2 BDD lane output contained 35 terminal `FAILED` nodes but no
  traceback. Controlled log inspection showed `T29_TEMP_ROOT=...` appended to
  pytest's node-progress line, so anchored runner parsing returned no path;
  unit/integration could be killed during collection before the session fixture
  emitted its receipt.
- **Decision:** Publish the exact runner-declared temp boundary at conftest
  module load, emit it on its own line, and avoid duplicate publication once
  pytest exposes the same base temp path. Emit run/lane/PID/PGID per-test
  failure traceback records and structured server events into lane stdout so
  runner receipts retain diagnosable evidence.
- **Impact:** Receipt parsing and diagnosis improve without changing BDD
  scenarios, feature files, product behavior, marker classification, DB
  binding, or test selection. Unknown failure causes remain blocked until a
  controlled BDD reproduction is safe and attributable.
- **Evidence:** R2 `20260821T112339` lane logs, regex result from current
  `TEMP_ROOT_RE`, and focused contracts added in
  `tests/scripts/test_t29_harness.py`.

### 4. Preserve binary subprocess capture while writing text server events

- **Context:** Review R3 isolated `tests/support/server.py::_server_event` as
  the first failure: `uvicorn_log_file` returns a binary `NamedTemporaryFile`,
  while the event writer passed `str` to `write()`. This stopped every server
  child before readiness and caused downstream PID-not-found/EPIPE evidence.
- **Decision:** Keep subprocess stdout/stderr capture binary and encode only
  event payloads when the owned log handle declares binary mode. Leave runner
  topology, readiness, teardown, ports, and timeout policy unchanged.
- **Impact:** Existing text-backed controlled handles remain supported; real
  `NamedTemporaryFile` server logs accept launch/readiness/teardown events
  without changing lifecycle behavior. Focused regression test exercises the
  exact binary handle path.
- **Evidence:** R3 receipt `20260821T124708` records
  `TypeError: a bytes-like object is required, not 'str'` at server.py:36;
  focused test `test_server_event_writes_binary_log_handle` covers correction.

### 5. Owner-authorized remediation 3/3 selects no speculative repair

- **Context:** R4 left aggregate duration/DB acceptance blocked, audit and
  integration PID evidence unexplained, and BDD/visual readiness untrusted.
  Owner authorized one final bounded pass, limited to audit/BDD/visual lane
  reproductions and mapped harness files.
- **Decision:** Reproduce exact taskipy audit, BDD, and visual entrypoints with
  explicit run/lane identity, exact basetemp, separate stdout/stderr, and
  parent/child/PGID poll/wait/exit evidence. Apply no runtime change unless
  reproduction falsifies a mapped harness boundary. Do not run canonical full
  suite or inspect/edit unlisted audit, integration, BDD, visual, product, or
  configuration files.
- **Impact:** Controlled audit (40/40), BDD (51/51), and visual (8/8) lanes
  pass. BDD `8766` and visual `8768` each emit launch, ready, teardown-start,
  teardown-complete, child PID/PGID, and `port_free=true`; no EPIPE or
  `process PID not found` occurs. Audit emits dynamic safe DB and exact temp
  receipt and passes. No confirmed T34 defect remains in reproduced lanes;
  R4 aggregate/integration acceptance remains blocked pending review-owned
  canonical evidence.
- **Evidence:** T34 tasks `Owner-authorized controlled remediation 3/3`,
  run logs `t34-remediation3-audit2`, `t34-remediation3-bdd`, and
  `t34-remediation3-visual`, plus postflight inventory at
  `2026-08-21T15:33:44-03:00` showing no `8765-8768` listener or live
  runner/pytest/Playwright/uvicorn process.

### 6. R4 integration PID diagnosis remains unproven; no repair selected

- **Context:** Owner-authorized R4 remediation required one isolated integration
  diagnosis for PID `630022`. Exact R4 evidence places that text in the audit
  lane log (`20260821T134451-audit.log:46`), while the integration log stops
  during collection and contains no PID text. A focused integration task using
  `tests/test_admin_recovery.py` passed and produced no lifecycle error.
- **Decision:** Do not edit runner/shared fixture code or add a speculative
  regression. Mark R4-F02 `BLOCKED_FOR_IMPLEMENTATION_BRIEF` because the
  observed equivalent did not reproduce the failure and the diagnostic
  wrapper could not attribute a child PID for the short-lived Alembic process.
  Preserve exact current-run resources and stop rather than infer ownership or
  adopt PID `630022`.
- **Impact:** T34 remains unchanged at runtime. Owner needs an isolated
  audit-lane or broader runner attribution decision, outside this
  integration-only boundary, before any further repair can be proven.
- **Evidence:** Diagnosis run
  `t34-r4-integration-diagnosis-20260821T161755-0300`; wrapper PID/PPID/PGID
  `641701/641700/641701`, command and receipt linkage recorded in T34 tasks;
  `13 passed in 5.52s`, dynamic DB and exact temp receipts matched run/lane,
  wrapper poll/wait/exit returned `0`, and no `8765-8768` listener or process
  residue remained after exact cleanup.

### 7. R4-F02 audit attribution is external taskipy signal handling

- **Context:** Owner-authorized isolated audit diagnosis follows R4's exact
  `process PID not found (pid=630022)` text from the audit lane. Historical
  traceback attribution identifies `taskipy/task_runner.py::signal_handler` as
  the source: its `psutil.Process(process.pid)` lookup races with the audit
  pytest child exit while the taskipy wrapper is handling runner SIGTERM.
- **Decision:** Trace one current audit taskipy invocation through wrapper,
  pytest, conftest safe-DB bootstrap, and Alembic subprocess. Do not patch
  T34 runner/shared fixtures when current equivalent passes and the only
  proven failure source is external taskipy code outside this slice's edit
  boundary.
- **Impact:** R4-F02 remains blocked for implementation. Any repair belongs to
  a taskipy/runner-boundary slice with owner-approved scope; T34 preserves
  taskipy entrypoints and does not rewrite task topology or vendor dependency
  code.
- **Evidence:** R4 audit log `20260821T134451-audit.log:46` plus traceback in
  `20260820T122938-audit.log:42-107`; direct taskipy source path and one
  isolated current audit attribution run are recorded in T34 `tasks.md`.

## Change Map

| File / symbol | From → To | Reason |
|---|---|---|
| `scripts/run_full_suite.py::_lane_metadata`, `launch` | PID/PGID assumption and sparse lifecycle fields → run/lane-linked parent PID, child PID, actual PGID, lifecycle timeline, and exact temp-root declaration | Close integration PID lineage gap without changing process topology. |
| `scripts/run_full_suite.py::_stop`, `_reap`, `_final_exit_code` | Race evidence is incomplete and cleanup can be hard to attribute → phase-specific bounded observations, owned-PGID-only signaling, explicit wait/exit evidence, causal-result precedence | Preserve first failure while making cleanup trustworthy/nonzero when evidence is missing. |
| `scripts/run_full_suite.py::main`, lane env/finalization | Child env has lane/DB/timing only; final receipt lacks current pytest-temp reconciliation → add run ID/temp-root boundary, parse exact `T29_TEMP_ROOT`, reconcile exact paths, and persist verdict | Resolve R6 receipt/postflight contradiction without broad cleanup. |
| `tests/support/browser.py::wait_for_port`, `shutdown_uvicorn` | TCP/log lifecycle is mostly unstructured → child-aware readiness and structured launch/readiness/exit/port/log/teardown evidence; retain bounded cleanup | Diagnose/correct visual `8768` lifecycle while preserving helper contract. |
| `tests/support/server.py::run_test_server` | Uvicorn launch/yield/teardown lacks run/lane ownership evidence → register parent/child/PGID, flush diagnostics on startup failure, and emit lifecycle events | Make visual child failure attributable and stale readiness impossible. |
| `tests/support/db.py::emit_db_receipt`, safe DB helpers | DB receipt only reports lane DB target → add exact current-run temp-root receipt helper; preserve dynamic DB creation and production guard | Tie pytest temp ownership to runner receipt. |
| `tests/conftest.py::_omaha_test_env` / session setup | Safe DB setup has no pytest temp ownership publication → publish actual base temp path once per lane/run; preserve import ordering and marker allow-lists | Reconcile current-run temp root without changing DB isolation or test classification. |
| `tests/scripts/test_t29_harness.py` | Existing controlled tests cover prior T29/T33/I08 contracts → add deterministic lineage, readiness, temp ownership, foreign-resource, and receipt mismatch scenarios | Prove only bounded behavior; no real process/port/host cleanup. |
| `pyproject.toml` task definitions | Canonical taskipy entrypoints are current source of truth → unchanged unless direct evidence proves configuration boundary fault | Preserve six lanes and taskipy invariant. |

## Acceptance and decision rules

Evidence is valid only when it carries the same run ID and lane ID as the
receipt. Each of the three R6 symptoms needs a timeline and owner evidence:

1. integration: runner parent/child/PGID, launch, poll, signal/wait, exit, and
   first-failure attribution;
2. visual: server parent/child/PGID, requested `127.0.0.1:8768`, readiness
   probes, child exit, log state, and teardown;
3. pytest temp: declared boundary, emitted exact path, creation/ownership
   evidence, post-exit state, and `absent`/`owned-cleaned` reconciliation.

Unknown, foreign, pre-existing, missing, contradictory, or incomplete evidence
is preserved and never repaired. It blocks trusted cleanup and returns nonzero.
If controlled evidence cannot distinguish runner, server, and host cause, apply
must return `BLOCKED_FOR_IMPLEMENTATION_BRIEF`; it must not trial fixes.

## Risks / Trade-offs

- **Instrumentation changes timing** → keep event writes bounded, use existing
  lane logs/receipt persistence, and verify the hard 300s ceiling once only.
- **Actual PGID differs from PID** → record `os.getpgid` immediately after
  launch and never signal unrecorded groups.
- **Pytest creates nested temp paths** → compare only exact declared/emitted
  paths under the unique run/lane boundary; never infer ownership from parent
  names.
- **Visual child exits before log flush** → close/flush owned log before reading
  startup failure and retain missing/empty output as evidence, not success.
- **Shared helper affects BDD/e2e/visual** → preserve host, ports, DB paths,
  browser scopes, and no-retry behavior; focused tests cover dead child and
  stale listener before browser-lane validation.
- **Scope drifts into T33/I08/D05** → changed-file audit rejects archive,
  stable-spec, agent-doc, or unrelated harness edits; only T34 artifacts and
  mapped implementation files are allowed.

## Migration Plan

1. Add T34 delta specs and inspect-only evidence rules.
2. Add focused controlled tests for each lifecycle/temp contract before runtime
   edits.
3. Capture bounded diagnosis; implement only the confirmed runner/server/temp
   boundary, or stop blocked if evidence is ambiguous.
4. Run focused harness taskipy tests and changed-file/lint checks. Do not run
   full suite at proposal/apply gates.
5. Review runs exactly one canonical `uv run task test`; retain receipt,
   six-lane evidence, coverage/skips/reconciliation, trusted cleanup, and
   elapsed time <=300s. No refresh-for-test or DB reset is part of this
   harness-only slice.

Rollback is revert of mapped runner/harness/test changes and unsynced delta;
no application migration, seed, production DB write, or host cleanup exists.

## Open Questions

None blocking proposal. Apply must use decision rules above; it must not infer a
root cause from historical R6 strings alone.

## Owner-authorized amendment — external Taskipy compatibility fault

### Amendment code map

| File / symbol | Role in amended flow | Edit status |
|---|---|---|
| `pyproject.toml:[project].dependencies` and `[dependency-groups].dev` | Declares the supported Taskipy version range and therefore the dependency boundary used by `uv run task` | Candidate; edit only for a published fixed Taskipy release |
| `pyproject.toml:[tool.taskipy.settings]` and `[tool.taskipy.tasks]` | Defines working directory, canonical task entrypoints, and commands consumed by the six-lane runner | Inspect; edit only if direct controlled evidence proves invocation/config causality |
| `uv.lock:[[package]] name = "taskipy"` and transitive `psutil` package block | Resolves exact Taskipy/psutil artifacts used by `uv sync` and `uv run task` | Candidate only as generated companion to approved `pyproject.toml` change |
| `scripts/run_full_suite.py::LANES`, `launch`, `handle_signal`, `_stop`, `_reap` | Sends lifecycle signals to taskipy lane wrappers and preserves six-lane causal cleanup | Inspect; no topology or signal-policy change authorized by this amendment |
| `.venv/lib/python3.12/site-packages/taskipy/task_runner.py::TaskRunner.__send_signal_to_task_process` | Installed evidence source for the external defect | Read-only evidence; never edit |
| `tests/scripts/test_t29_harness.py` existing lifecycle/lane contracts | Focused oracle for task command shape, signal race recording, and topology preservation | No behavior change; add regression only after supported remedy exists |

### Amended current relevant flow

1. Input: canonical runner launches each lane through its existing `uv run task
   <name>` entrypoint. On fail-fast, deadline, SIGINT, or SIGTERM, the runner
   signals the recorded current-run-owned taskipy process group.
2. Transformation: Taskipy 1.14.1 runs the configured command through
   `subprocess.Popen(..., shell=True)`, installs a SIGTERM handler, then waits.
   Its Linux handler first calls `psutil.Process(process.pid)` and then looks up
   shell children before forwarding the signal.
3. Boundary: when the taskipy shell child exits before the handler runs,
   `psutil.Process(process.pid)` raises `psutil.NoSuchProcess`; taskipy emits
   `process PID not found` instead of completing signal handling. This is a
   race at external dependency boundary, not a T34 runner/shared-fixture
   transformation.
4. Output: lane/taskipy wrapper returns nonzero or emits traceback; runner must
   preserve that causal failure and bounded cleanup evidence. A successful
   focused audit does not prove canonical six-lane acceptance.

Boundary rules: no PID reuse inference, no signal retry, no task topology
change, no broad process discovery, and no adoption or cleanup of unknown,
foreign, or pre-existing resources.

### Root-cause evidence and package compatibility matrix

- T34 audit attribution evidence: `tasks.md:1331-1373` links historical
  `reports/test-profile/20260820T122938-audit.log:42-107` and
  `20260821T134451-audit.log:46` to the installed handler.
- Installed package: taskipy `1.14.1`, with `task_runner.py:183-186` calling
  `psutil.Process(process.pid)` without handling `psutil.NoSuchProcess`.
- Project declaration: `pyproject.toml:42` permits `taskipy>=1.13`.
- Locked artifact: `uv.lock:2385-2397` resolves taskipy `1.14.1`; its package
  metadata permits `psutil>=5.7.2,<7`.
- Locked transitive dependency: `uv.lock:1601-1614` resolves psutil `6.1.1`.
- Upstream source check on 2026-08-21: taskipy 1.13.0, 1.14.1, and current
  `master` retain same signal-handler lookup. Upstream release index reports
  1.14.1 as latest; its release note updates psutil compatibility, not this
  race. Sources: `https://github.com/taskipy/taskipy/releases` and
  `https://raw.githubusercontent.com/taskipy/taskipy/master/taskipy/task_runner.py`.

### Remedy options and decision

| Option | Decision | Rationale |
|---|---|---|
| Upgrade to a published Taskipy release containing a handler fix | Not available; blocked | Latest supported release is 1.14.1 and retains faulty code. No fixed version can be named without inventing one. |
| Downgrade Taskipy to 1.13.x or earlier | Reject | Same handler pattern; removes compatibility certainty without correcting absent-PID lookup. |
| Pin/downgrade/upgrade psutil within Taskipy's declared range | Reject | Failure is `Process(pid)` after process exit; changing psutil version does not make absent PID lookup safe and has no proven upstream fix. |
| Change `[tool.taskipy.settings]`/task command to disable handler or shell mode | Reject | No documented Taskipy setting disables this handler; changing command shape/topology would violate T34 invariants and lacks causal proof. |
| Change `scripts/run_full_suite.py` to avoid SIGTERM race | Reject for this amendment | Would alter runner signal semantics and mask external defect; no controlled evidence authorizes topology/policy change. |
| Vendor, monkeypatch, or edit installed `site-packages` | Prohibited | Outside project dependency boundary, non-reproducible, and explicitly excluded by owner. |
| Adopt an upstream fixed release later | Conditional path | If upstream publishes a verifiable fixed release, update only `pyproject.toml` plus generated `uv.lock`, add focused regression, and re-run gates. Exact version must be recorded from published metadata; none exists now. |

**Decision:** no supported minimal correction is available in current package
sources. Amendment records exact dependency/lockfile/invocation options,
selects no runtime or dependency edit, and returns
`BLOCKED_FOR_IMPLEMENTATION_BRIEF`. T34 remains the owning slice; no new slice
is created. Existing completed runner/harness evidence remains valid historical
evidence.

### Implementation boundary if upstream fix appears

Only these changes may be considered after a published fix is verified:

1. Raise `pyproject.toml` Taskipy lower bound to exact fixed release range;
   preserve all six task names, commands, flags, ports, DB allow-list,
   fail-fast, coverage, skips, and 300-second deadline.
2. Regenerate only corresponding Taskipy/transitive records in `uv.lock`; do
   not hand-edit hashes or unrelated packages.
3. Add one deterministic contract in existing
   `tests/scripts/test_t29_harness.py` for an already-exited task child under
   runner SIGTERM. Test must prove no Taskipy traceback, causal runner result
   remains correct, and exact owned-resource cleanup remains bounded.
4. Change `scripts/run_full_suite.py` or task invocation/config only if a new
   controlled reproduction proves the published fix still requires that
   boundary; otherwise these files remain unchanged.

No application behavior, database, seed, F58 connector, MyProfit workflow,
BDD feature, lane selection, retry, skip, xfail, or stable-spec behavior is
part of this conditional path.

### 8. I10 receipt diagnosis separates support evidence from manifest evidence

- **Context:** I10 canonical receipt `20260821T184456-660477` records empty
  unit/integration DB receipts and a fixed `data/test_bdd.db` path reported as
  owned despite surviving postflight. The mapped conftest publishes dynamic DB
  identity only after migration/bootstrap, and runner fixed-DB reconciliation
  trusts receipt text without proving exact pre-run absence or post-run state.
  The same receipt reports E2E/BDD connection refusal without child startup
  exception or server lifecycle evidence; later bounded BDD/visual reproductions
  pass, so no readiness patch is proven by this receipt.
- **Decision:** publish dynamic DB receipt immediately after safe path creation,
  before imports/migration, and reconcile fixed test DB paths only when exact
  preflight classified them absent. Remove only exact current-run fixed test DB
  files after a matching lane receipt; preserve pre-existing/unknown paths.
  Do not alter direct lane vectors, Taskipy policy, server readiness behavior,
  manifest data, skip policy, or lane topology.
- **Impact:** deadline/collection interruption retains unit/integration DB
  ownership evidence; fixed BDD/E2E/visual DB residue cannot be mislabeled
  clean. Existing dynamic DB binding, migration, seed, production guard, and
  test selection remain unchanged. E2E/BDD readiness and 1,032-versus-1,043
  manifest evidence remain blocked until an attributable T34 cause exists.
- **Evidence:** I10 receipt `20260821T184456-660477` and current symbols
  `tests/conftest.py` module-load bootstrap, `tests/support/db.py` receipt order,
  `scripts/run_full_suite.py::_canonical_resource_inventory`, and
  `_validate_db_targets`/finalization. Focused regressions cover exact fixed-DB
  cleanup and pre-existing preservation.

### Acceptance, rollback, and unknown-resource rules

- Focused acceptance requires exact resolved Taskipy version and source hash,
  `uv lock --check`, targeted Ruff on changed project files, and
  `uv run task test-file tests/scripts/test_t29_harness.py`; the new race
  contract must pass without changing existing lifecycle or lane contracts.
- Review still owns exactly one canonical `uv run task test`, with six exit-0
  lanes, full coverage/skips/manifest reconciliation, trusted cleanup, no
  foreign/unknown residue action, and elapsed wall-clock through cleanup
  `<=300s`. Existing task 3.2 remains open and is not run at proposal gate.
- Any unknown, foreign, pre-existing, contradictory, or incomplete process,
  port, DB, temp-root, dependency-resolution, or receipt evidence blocks the
  gate. It remains untouched; no adoption, kill, deletion, allowlist, retry,
  or rerun is allowed.
- Rollback is removal of the conditional Taskipy constraint/lockfile delta and
  reversal of any explicitly approved invocation/config delta. No installed
  package is patched. If lockfile regeneration cannot reproduce cleanly, stop
  with dependency state unchanged.

## Implementation Decisions — consolidated T34 remediation

### 9. Keep valid dynamic DB ownership independent from collection progress

- **Context:** I10 receipts classified unit/integration DB ownership as unknown
  when deadline or collection interruption occurred before node timing output,
  although `tests/support/db.py` can publish the dynamic DB path immediately
  after safe path creation.
- **Decision:** Keep early `T29_DB_TARGET` publication, place each lane's
  temporary DB allocation inside its runner-registered exact temp boundary, and
  reconcile only emitted dynamic paths after temp cleanup. Collection/node
  completeness remains separate evidence; it cannot erase valid DB ownership.
  Paths outside the registered lane boundary remain unknown and untouched.
- **Impact:** Unit/integration collection interruption retains test-only DB
  ownership and bounded cleanup evidence without changing DB bootstrap, seed,
  migration, lane topology, or production-DB guards.
- **Evidence:** I10 receipts `20260821T184456-660477` and
  `20260821T212035-679347` had valid dynamic DB creation but empty/incomplete
  collection receipts; current `_lane_environment` and finalization coupled DB
  acceptance to `collection["nodes"]`.

### 10. Persist phase/run/lane timing as receipt data

- **Context:** Existing lifecycle timestamps and repeated receipt writes did not
  expose bounded phase durations, so hard-ceiling time could not be attributed
  reliably between preflight, launch, monitor, cleanup, and finalization.
- **Decision:** Add monotonic elapsed timing for run phases and lane phases,
  wall-clock start/end timestamps, and receipt-persistence observations. Record
  phase snapshots at existing persistence boundaries; preserve the 300-second
  ceiling and no-retry/fail-fast policy.
- **Impact:** A failed or timed-out receipt remains available with enough
  run/lane attribution to identify where ceiling time was spent. No phase gets a
  new timeout or relaxed budget.
- **Evidence:** R2/R3/R4 receipts retained total elapsed time but lacked phase
  attribution while monitor/cleanup and collection interruption were disputed.

### 11. Concurrent E2E/BDD startup is a proof gate, not a new lifecycle policy

- **Context:** Separate E2E/BDD reproductions passed, while I10's concurrent
  receipt recorded refusal on ports 8765/8766 without child startup evidence.
- **Decision:** Reproduce both runner-equivalent children concurrently with
  exact direct vectors, run/lane env, temp boundaries, stdout/stderr, PID/PGID,
  readiness polls, and bounded wait/teardown. Change shared lifecycle code only
  if this controlled concurrent run falsifies the mapped ownership/readiness
  boundary; otherwise preserve current server/browser behavior and record the
  external/unknown result.
- **Impact:** No browser retry, port scan/free, lane serialization, timeout
  change, BDD/E2E behavior change, or canonical full-suite execution.
- **Evidence:** Prior controlled BDD `51/51` on 8766 and visual `8/8` on 8768
  showed child-aware readiness and `port_free=true`; concurrent evidence is
  required before attributing I10 refusal to T34.

### 12. Concurrent readiness success does not authorize speculative lifecycle repair

- **Context:** The bounded concurrent E2E/BDD reproduction reached readiness on
  exact ports `8765` and `8766`, with matching run/lane/PID/PGID server events.
  Later E2E/BDD nodes failed in application/browser assertions and the outer
  bounded harness timed out before natural lane exit; no startup exception,
  stale-listener adoption, EPIPE during readiness, or ownership mismatch was
  observed.
- **Decision:** Treat concurrent startup as an attributable support pass, not a
  T34 lifecycle defect. Preserve existing server/browser lifecycle code and stop
  without retries, timeout changes, lane serialization, port action, or product
  test edits. Record test failures as unresolved canonical/behavior evidence for
  owner/review, not as proof of shared-harness causality.
- **Impact:** C3 diagnosis is complete while canonical acceptance remains blocked.
  Exact current-run groups are bounded-cleaned; no foreign or unowned resource is
  adopted. Review still requires its isolated canonical gate.
- **Evidence:** Run
  `t34-concurrent-e2e-bdd-20260821T225159-0300`; lifecycle log records
  `phase=readiness-ready ports=8765,8766`, E2E/BDD stdout records matching
  `T29_SERVER_EVENT` launch/ready and per-test failures, and teardown records
  SIGTERM followed by absent owned groups and no remaining listener.

### 13. Final concurrent browser failure is diagnostic temp-path setup, not lifecycle code

- **Context:** The final six-lane concurrent startup observation produced
  `TargetClosedError` in E2E, BDD, and visual browser fixtures. Server readiness
  still succeeded for BDD on `127.0.0.1:8766`; browser diagnostics contained
  Chromium's fatal `process_singleton_posix.cc:313` error: `Socket path too
  long` for `.../SingletonSocket` beneath each long `/tmp/opencode` lane temp
  root. Integration failures independently showed SQLite setup errors, not a
  shared startup boundary.
- **Decision:** Do not edit browser launch, server readiness, runner topology,
  timeout, or browser retry policy. Treat observation as invalid for canonical
  lifecycle attribution because manually supplied lane temp roots violated
  Unix Chromium socket-path constraint. Canonical runner already allocates
  `/tmp/o-*` lane roots, checks derived Chromium socket path against 108 bytes,
  and has focused contract for invariant. Preserve exact browser/integration
  failures as diagnostic evidence.
- **Impact:** No runtime or test behavior changes. Canonical runner remains only
  trusted source for lane temp-root shape; direct concurrent diagnostics must
  use same short registered boundary. No cleanup, retry, serialization, or path
  adoption is authorized from observation.
- **Evidence:** Run
  `t34-final-concurrent-startup-20260821T234409-0300`; E2E/BDD/visual logs
  record fatal Chromium socket-path error, BDD records `ready` before browser
  launch, and focused contract
  `test_runner_temp_boundary_is_chromium_socket_safe_and_reconciles_exactly`
  passes against `scripts/run_full_suite.py::_create_lane_temp_root`.

## Owner-authorized amendment — exact runner temp-resource boundary

This amendment changes only review/apply policy relevance for temporary paths.
All prior T34 diagnosis, implementation, receipts, findings, and stop results
remain historical evidence. The prior R1/R9 blocks proved that the old blanket
review rule was too broad when it treated an out-of-bound `/tmp` root as a
cleanup-relevant test resource; they do not authorize deleting or adopting that
root.

### Amendment code map

| File / symbol or contract | Role in current flow | Intended policy role |
|---|---|---|
| `scripts/run_full_suite.py::_create_lane_temp_root`, `_lane_environment`, `_lane_metadata`, `_reconcile_temp_root` | Creates exact short run/lane temp boundary, publishes it to child, and reconciles reported path against exact boundary | Source of cleanup-relevant temp identity; inspect/preserve existing exact behavior |
| `tests/scripts/test_t29_harness.py::test_runner_reconciles_owned_temp_root_exactly` | Proves exact current-run path reaches `owned-cleaned` | Owned-path acceptance oracle |
| `tests/scripts/test_t29_harness.py::test_runner_preserves_mismatched_temp_root` | Proves mismatch remains untouched and untrusted | Declared-boundary mismatch/foreign oracle |
| `tests/scripts/test_t29_harness.py::test_runner_preflight_inventory_ignores_harmless_host_observations` and `test_runner_preflight_inventory_records_preexisting_pytest_root_as_irrelevant` | Proves out-of-bound observations are preserved, non-target, and do not poison canonical inventory | Non-target `/tmp/pytest-of-juca` acceptance oracle without a literal allowlist |
| `.opencode/agents/review.md` — preflight/isolation lines 44-67 | Currently blocks any relevant unowned test-temporary observation | Narrow relevance to exact runner-declared run/lane paths |
| `.opencode/agents/apply.md` — resource decision procedure lines 64-92 | Defines exact cleanup ownership and review isolation handoff | Preserve declared-boundary safety; classify out-of-bound temp observations non-target |
| `.opencode/skills/openspec-apply-change/SKILL.md` — cleanup decision lines 80-102 | Operational apply/review protocol copy | Keep exact-resource rules synchronized |
| `AGENTIC_DEVELOPMENT.md` — ownership/preflight/cleanup lines 51-92 | Cross-agent protocol source | Define relevance boundary without weakening foreign-resource safety |
| D05 `openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight/specs/test-run-ownership-contract/spec.md` — review isolation and safe-stop requirements | Existing ownership vocabulary and prohibition boundary | Consumed as constraint; not edited or reopened |
| T34 delta `specs/dev-tasks/spec.md` and `specs/shared-test-support/spec.md` | T34 formal runner/support contracts | State exact declared-path relevance and the three acceptance scenarios |

### Amended current relevant flow

1. Canonical runner creates and records one exact temp boundary per run/lane;
   child receipt publishes that exact path and run/lane identity.
2. Review/apply policy evaluates cleanup relevance from the runner declaration,
   not from host-wide discovery. It does not search for `pytest-of-*`, inspect a
   broad `/tmp` parent, or infer ownership from a path name.
3. Exact declared path with current-run receipt/ownership match is eligible for
   bounded cleanup and records `owned-cleaned`; exact absent state records
   `absent`.
4. Declared-boundary mismatch, unknown, foreign, contradictory, or incomplete
   evidence remains untouched and blocks the affected operation. This preserves
   D05's true foreign-resource safety.
5. An observed temporary path outside all canonical runner-declared boundaries
   is recorded as `preserved/non-target`. It is not cleanup-relevant and cannot
   block review alone. `/tmp/pytest-of-juca` is an evidence example, not an
   allowlist entry or discovery target.
6. Independent canonical process, listener, test-DB, or declared-boundary
   findings still block under existing D05 rules. The amendment changes no
   lane, retry, skip, xfail, timeout, I10, T33, I08, product, F58, or DB rule.

### Implementation decisions

#### 1. Define relevance by canonical declaration, not observed pathname

- **Context:** Existing runner inventory already preserves unrelated host
  observations (`relevant=false`, `cleanup_target=false`) while exact lane
  temp reconciliation rejects missing or mismatched receipts. Review policy
  wording still says any relevant unowned test-temporary resource invalidates
  isolation, creating a false block for out-of-bound `/tmp` state.
- **Decision:** Policy SHALL call only canonical runner-declared exact run/lane
  paths cleanup-relevant. It SHALL record out-of-bound temp observations as
  preserved/non-target without blocking them alone.
- **Impact:** Review can proceed past unrelated pytest residue without broad
  cleanup, while declared-boundary ownership checks remain strict.
- **Evidence:** `scripts/run_full_suite.py::_canonical_resource_inventory` and
  `_reconcile_temp_root`; existing focused tests named in code map.

#### 2. Preserve strict safety inside declared boundaries

- **Context:** D05 requires ledger ownership before cleanup and safe stop for
  unknown, foreign, contradictory, or incomplete state.
- **Decision:** Exact current-run receipt match yields `owned-cleaned` only
  after bounded cleanup; absent yields `absent`; mismatch/unknown/foreign or
  contradictory state inside declared boundary stays untouched and blocks the
  affected handoff/verdict.
- **Impact:** Amendment narrows relevance, not ownership proof or destructive
  authority. No foreign-resource exception is introduced.
- **Evidence:** D05 contract requirements and T34 exact/mismatch tests.

#### 3. Keep policy copies synchronized

- **Context:** Four policy documents repeat ownership/preflight language and
  can drift independently.
- **Decision:** Apply must update the named sections in
  `.opencode/agents/review.md`, `.opencode/agents/apply.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`, and
  `AGENTIC_DEVELOPMENT.md` together; T34 delta specs become their formal
  implementation oracle. D05 files remain read-only references.
- **Impact:** Future agents receive one exact boundary vocabulary without
  broadening cleanup or changing runner mechanics.
- **Evidence:** Current duplicated policy text and D05 code map.

#### 4. Define review isolation relevance by declared temporary boundary

- **Context:** The four agent-policy copies treated every relevant unowned test
  temporary as an isolation failure, while runner inventory already marks an
  observed path outside its exact run/lane declarations as preserved and
  non-target. This made ordinary pre-existing pytest roots capable of blocking
  review without being cleanup targets.
- **Decision:** Synchronize policy wording so only canonical runner-declared
  exact run/lane temporary paths are cleanup-relevant. Exact current-run receipt
  matches may finish as `owned-cleaned`; exact absent declarations finish as
  `absent`; mismatch, unknown, foreign, contradictory, or incomplete state
  inside the declaration stays untouched and blocks. Out-of-bound temporary
  observations are recorded `preserved/non-target` and cannot block alone.
  Declaration membership is never inferred from path names or parents, and no
  literal allowlist or `pytest-of-*` discovery is permitted.
- **Impact:** Review/apply can ignore unrelated pytest residue without broad
  cleanup, while D05 safety remains strict for all declared temporary paths and
  independent process/listener/DB findings.
- **Evidence:** Existing runner functions
  `scripts/run_full_suite.py::_canonical_resource_inventory` and
  `_reconcile_temp_root`, plus focused tests
  `test_runner_preflight_inventory_records_preexisting_pytest_root_as_irrelevant`,
  `test_runner_reconciles_owned_temp_root_exactly`, and
  `test_runner_preserves_mismatched_temp_root`.

### Amended change map

| File / symbol | From → To | Reason |
|---|---|---|
| `.opencode/agents/review.md` preflight/isolation policy | Any relevant unowned test-temp blocks → only unowned state inside canonical runner-declared exact run/lane boundary blocks; out-of-bound temp is preserved/non-target | Stop false review blocks without cleanup relaxation |
| `.opencode/agents/apply.md` cleanup and canonical isolation policy | Broad “relevant test-temporary” wording → declared exact path eligibility plus strict mismatch/foreign stop | Keep apply/review handoff safe and consistent |
| `.opencode/skills/openspec-apply-change/SKILL.md` cleanup decision/guardrails | No out-of-bound relevance distinction → explicit non-target recording and no-block-alone rule | Synchronize operational skill |
| `AGENTIC_DEVELOPMENT.md` ownership contract | Blanket relevant-temp isolation → canonical declaration boundary with preserved D05 safety | Synchronize cross-agent protocol |
| T34 `specs/dev-tasks/spec.md` | Temp receipt mismatch/pre-existing text does not distinguish boundary → exact declared-path matrix and non-target scenario | Formal runner contract |
| T34 `specs/shared-test-support/spec.md` | Temp ownership requirement treats observed residue uniformly → exact runner boundary and preserved out-of-bound observations | Formal support contract |
| `tests/scripts/test_t29_harness.py` existing temp/inventory scenarios | Existing exact/mismatch/non-target oracles remain → add/update policy acceptance only as needed | Prove owned-cleaned, blocked untouched, and non-target preserved |

### Risks and preserved patterns

- **Foreign resource safety regression:** prohibited. Any foreign/unknown or
  mismatched resource inside a declared boundary still blocks untouched; true
  canonical process/listener/DB collisions still block.
- **Literal allowlist drift:** prohibited. `/tmp/pytest-of-juca` appears only as
  recorded evidence/test fixture input; implementation must use declaration
  membership, never a path exception.
- **Broad cleanup drift:** prohibited. No `pytest-of-*` discovery, parent/broad
  `/tmp` traversal, wildcard deletion, adoption, kill, retry, or rerun.
- **Policy drift:** all four named policy files and both T34 delta specs must
  use same classification terms; D05 contract remains read-only boundary.
- **Historical evidence loss:** prohibited. Prior T34 receipts and findings
  stay intact; amendment is appended and explicitly supersedes only future
  review relevance interpretation.

### Amendment validation boundary

Proposal gate performs artifact/static validation only. Apply later must use the
existing focused harness module and prove: out-of-bound path preserved and
non-blocking alone; exact owned path cleaned; declared-boundary mismatch/foreign
path untouched and blocking. No canonical suite, resource cleanup, host scan,
DB reset, archive, commit, or push belongs to this amendment gate.
