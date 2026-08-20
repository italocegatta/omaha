## Context

I08 owns runner mechanics left deliberately outside D05. F61 R1 recorded an
854.89-second run with `process PID not found`, `psutil.NoSuchProcess`, and
Playwright `write EPIPE`; F58 R1 recorded `ERR_ABORTED` plus collateral sibling
termination. D05's documentation-only contract audit passed its ownership,
classification, stop, and receipt vocabulary, but D05 remains `Blocked` because
its review full suite reported unrelated unknown PID and visual failures. Owner
explicitly authorizes I08 to consume that audited vocabulary. This exception
does not make D05 approved or archived and does not reopen F58 R1-F02, F58,
F61, or their review state.

### Code map

- `scripts/run_full_suite.py::LANES`, `PORTS`, `LANE_DATABASES`, `KNOWN_DATABASES`:
  canonical six-lane topology and recognized test-resource boundaries. Preserve
  exact lane names/order, taskipy task names, test DB allow-list, and ports.
- `scripts/run_full_suite.py::_preflight`, `_validate_db_targets`,
  `_lane_environment`, `_runtime_child_command`: pre-launch input validation,
  lane environment/DB receipt binding, and taskipy command construction. No
  production DB, raw pytest, or alternate lane entrypoint may enter this flow.
- `scripts/run_full_suite.py::_stop`, `_reap`, `_final_exit_code`,
  `_stop_deadline`, `_duration_exceeded`: current signal forwarding, grace/KILL
  cleanup, result selection, and 300-second deadline behavior. These are the
  primary race and causal-result repair points.
- `scripts/run_full_suite.py::main`, nested `handle_signal`, `launch`, and
  `monitor`: creates lane children with `start_new_session=True`, monitors
  fail-fast/deadline state, gathers logs/timing/DB receipts, reconciles
  population, writes `<stamp>-run.json`, and returns the final status.
- `scripts/run_full_suite.py::reconcile_population` and
  `reconcile_preflight`: six-lane/node/skip/checksum reconciliation. Ownership
  telemetry must augment this evidence, never replace it.
- `scripts/run_expanded_lane.py::main`: separately named T32 expanded taskipy
  entrypoint. It runs visual-pruned then selected pytest cases sequentially;
  I08 preserves this behavior and does not turn it into a canonical lane or
  alter its selection topology.
- `pyproject.toml:[tool.taskipy.tasks]::test`, `test-unit`,
  `test-integration`, `test-audit-integration`, `test-e2e`, `test-visual`,
  `test-bdd`, `test-t32-expanded`: canonical taskipy command boundary and
  coverage/no-coverage flags. Existing commands remain the runner's only child
  commands.
- `tests/scripts/test_t29_harness.py::test_runner_returns_first_lane_failure_after_sibling_term`,
  `test_runner_parent_sigterm_stays_signal_exit`, DB receipt tests, and
  reconciliation tests: current focused oracle for first-failure preservation,
  signal exit, lane-scoped resources, and six-lane population/skips. Extend
  this file with controlled process/resource doubles; do not remove or skip
  existing coverage.
- `openspec/changes/d05-formalizar-contrato-operacional-de-limpeza-e-preflight/`
  `specs/test-run-ownership-contract/spec.md`, `design.md`, and review evidence:
  audited vocabulary for `owned-current-run`, `owned-cleaned`, `absent`,
  `foreign`, `unknown`, `pre-existing`, ledger identity/evidence, bounded
  idempotent cleanup, safe stop, and mandatory receipts. Read-only dependency;
  no D05 file is an I08 edit target.
- `openspec/changes/archive/2026-08-20-f61-documentar-ambiente-local-e-alinhar-cookie-seguro/tasks.md`
  R1-F01 and `openspec/changes/f58-integrar-automacao-playwright-myprofit/tasks.md`
  R1-F01/R1-F02: historical failure boundaries and non-goals, not repair scope.

### Current relevant flow

1. `uv run task test` invokes `uv run python -m scripts.run_full_suite` from
   `pyproject.toml`. Runner loads governance policy, refuses production DB
   targets, probes four test ports, loads the manifest, selects pre-run cases,
   and checks the 300-second budget before child launch.
2. `main.launch` opens lane log/timing paths, creates each child with
   `start_new_session=True`, sets `T29_DB_RECEIPT_LANE` and timing paths, and
   appends metadata only after `Popen` succeeds. A launch exception can therefore
   leave no receipt for that lane.
3. `monitor` polls all launched children. First nonzero child or deadline calls
   `_stop`, which currently calls `os.killpg(process.pid, signal)` while only
   suppressing `ProcessLookupError`. A child can disappear between `poll`,
   signal, and `wait`; cleanup exceptions can obscure the original failure.
4. `_reap` waits grace, KILLs survivors by process group, then waits every
   process. It returns only a boolean, so lane-level signal, PGID, survivor,
   resource, residue, and cleanup evidence are absent from receipts.
5. After cleanup, `main` reads each launched lane log/timing/DB receipt, updates
   metadata with exit and collection data, reconciles six lanes/nodes/skips,
   writes the run receipt, and chooses the final exit code. Missing launch
   metadata and incomplete cleanup can make attribution ambiguous.
6. `run_expanded_lane.main` invokes its existing taskipy visual-pruned command
   and selected pytest command sequentially. It is outside canonical six-lane
   receipt/reconciliation and must remain separately runnable.

Boundary conditions:

- Child may vanish before signal, between signal attempts, before wait, or
  while descendant cleanup is being observed. PID-not-found/`NoSuchProcess` and
  EPIPE are cleanup observations, not permission to retry broadly.
- A launched lane owns its process group (`start_new_session=True`) and exact
  run-created log/timing/temporary/DB receipt paths recorded before cleanup.
  Matching name, PID, port, path, or descendant without current-run evidence is
  `unknown`/`foreign`/`pre-existing`, not cleanable.
- Partial launch must produce one receipt entry for every canonical lane,
  including launch-failed lanes with null PID/PGID and explicit reason.
- Original first lane failure, parent SIGINT/SIGTERM result, or deadline
  `TIMEOUT_EXIT_CODE` must survive cleanup observations. Cleanup failure can
  force a nonzero outcome but cannot replace a known causal failure.
- Full-suite elapsed time includes bounded child cleanup and remains a hard
  `MAX_FULL_SUITE_SECONDS = 300.0` ceiling.

## Goals / Non-Goals

**Goals:**

- Make signal, fail-fast, deadline, and reap paths safe when children vanish.
- Track owned process groups and exact lane resources before use; reconcile
  descendants/resources without broad host actions.
- Emit complete, machine-readable receipts for all six lanes and all launch,
  stop, cleanup, residue, failure, and timeout paths.
- Prove behavior with deterministic doubles for vanished child, survivor,
  foreign process/port, fail-fast sibling stop, partial launch, and timeout.
- Preserve taskipy entrypoints, six lanes/order, fail-fast, coverage and skips,
  current population reconciliation, expanded-lane behavior, and 300 seconds.

**Non-Goals:**

- No new lane, task, retry policy, timeout relaxation, coverage reduction,
  test deletion, skip/xfail, manifest/topology change, or visual baseline work.
- No broad kill, process-name/pattern kill, host-wide port cleanup,
  indiscriminate descendant termination, foreign-resource adoption, or
  production DB/file cleanup.
- No F58 implementation or R1-F02 remediation, F61 edits, D05 lifecycle/spec
  changes, agent-doc changes, server refresh, database reset, or full-suite run
  at proposal/apply focused gates.
- No claim that D05 is archived/approved; its vocabulary is consumed only under
  the owner-authorized exception recorded above.

## Decisions

### 1. Represent ownership as per-lane ledger metadata

Create one metadata entry before each launch and retain entries for every lane.
Each entry records lane/task, PID and PGID when launch succeeds, exact log and
timing paths, owned DB/resource mapping, `started_at`/`ended_at`, signal sent,
return code, launch/stop/cleanup status, residue classification, owner
evidence, sibling-stop reason, and diagnostic error. Run-level receipt records
run timestamps, elapsed time, deadline, final result, and reconciliation.

Use process group identity established by `start_new_session=True` as the
owned descendant boundary. Do not infer ownership from names, ports, paths, or
current process scans. Record exact resources already emitted by lane receipts;
unknown/foreign/pre-existing resources remain untouched and make cleanup
untrusted/nonzero rather than becoming cleanup targets.

Alternative rejected: append metadata only after `Popen` and infer missing lanes
afterward. That loses partial-launch evidence and cannot satisfy complete lane
receipts.

### 2. Make signal and reap operations race-tolerant but narrow

Centralize group signal/cleanup observation so `ProcessLookupError`, the
platform PID-not-found form, and EPIPE are recorded as an idempotent absent or
vanished-child observation for that owned entry. Catch only expected
process-lifecycle races; preserve unexpected `OSError`/cleanup errors as
diagnostics. Reap every launched child, record survivors and KILL escalation,
and never scan or terminate processes outside recorded owned groups.

Capture `first_failure`, parent interruption, and deadline before cleanup. Final
exit selection uses those causal values first, then cleanup/receipt failure,
then lane return codes, so cleanup telemetry cannot turn a failure into success
or mask the original lane code.

Alternative rejected: suppress all cleanup exceptions or retry signal until it
works. Broad suppression hides unsafe cleanup; retries amplify PID reuse and
foreign-resource risk.

### 3. Keep receipt generation independent from successful launch/cleanup

Pre-create six lane metadata records, update them through launch, monitor, stop,
reap, log/timing/DB reconciliation, and finalization, and write the run JSON
even when launch, child execution, cleanup, or reconciliation fails. Missing
fields use explicit null/empty values plus status and reason, not omission.
Receipt must expose sibling termination cause and timeout/deadline evidence,
including elapsed wall-clock through cleanup and `clean_children`/cleanup
verdict.

Alternative rejected: emit only successful lane records or rely on lane log
text. Log text is interrupted by exactly the failures I08 must attribute.

### 4. Preserve taskipy and suite contracts verbatim

Continue constructing child commands from the existing task names with `uv run
task`; keep `LANES`, order, coverage flags, browser `--no-cov`, exact skips,
manifest/node reconciliation, fail-fast, expanded task, and 300-second
deadline. `run_expanded_lane.main` remains a separate sequential taskipy
entrypoint and receives no new canonical lane or selection policy.

Alternative rejected: add a dedicated cleanup task, raw pytest fallback, or
extra recovery lane. Those change operational topology and weaken the existing
contract.

### 5. Controlled doubles, no host/process operations in focused tests

Extend `tests/scripts/test_t29_harness.py` with fake `Popen`-like children,
monkeypatched `os.killpg`/clock/file outputs, and deterministic launch/monitor/
reap inputs. Tests assert receipt fields, causal exit code, exact owned-group
signals, untouched foreign resource, all-six-lane partial receipts, and timeout
classification. No test kills a real process, binds a real canonical port, or
uses broad process discovery.

## Implementation Decisions

- **Context:** Existing `metadata` was appended only after `Popen`, `_stop`
  suppressed only `ProcessLookupError`, and `_reap` returned one boolean. This
  left partial launches and vanished-child observations without lane evidence.
  **Decision:** pre-register six plain JSON lane records, pass an explicit
  current-run metadata map through stop/reap, and retain legacy `exit_code` plus
  new `return_code`/cleanup fields. **Impact:** launch, signal, reap, and
  receipt failures remain attributable without changing lane commands or order.
  **Evidence:** controlled partial-launch and timeout receipts in
  `tests/scripts/test_t29_harness.py`.
- **Context:** `os.killpg` and `wait` can report PID-not-found, `NoSuchProcess`,
  or EPIPE after the owned child has already disappeared. **Decision:** classify
  only those lifecycle errors (including ESRCH/EPIPE errno forms) as bounded
  races; record phase/class/message and return non-clean cleanup, while leaving
  unexpected errors diagnostic. **Impact:** first lane/interruption/deadline
  result is selected before cleanup status and is never replaced by race noise.
  **Evidence:** vanished-signal and vanished-wait controlled doubles.
- **Context:** port numbers and configured DB paths identify possible test
  resources but do not prove current-run ownership. **Decision:** record ports
  and DB mappings as `unknown` until exact current-run launch/receipt evidence
  exists; never scan, adopt, or clean them. Process-group ownership is proven
  only by the returned `Popen` child created with `start_new_session=True`.
  **Impact:** foreign resources remain outside signal/reap scope and become
  explicit receipt residue when lane evidence is incomplete. **Evidence:**
  foreign-resource controlled contract and lane resource mappings.
- **Context:** review R1 classified host services on `8000`, `5443`, and `4096`
  plus `/tmp/pytest-of-juca/` as relevant only because preflight treated host
  state as an empty-run baseline. **Decision:** bound preflight inventory to
  canonical suite ports `8765-8768`, fixed test DB paths, and resources with
  current-run PGID/path/log evidence; retain other observations as
  `relevant=false`, `pre-existing`, preserved, and never allowlisted/adopted or
  cleaned. **Impact:** host services do not block canonical preflight, while a
  canonical collision remains untrusted and blocks before launch. **Evidence:**
  `_canonical_resource_inventory`, controlled harmless-observation,
  pre-existing pytest-root, and canonical-collision tests.
- **Context:** foreign canonical observations were previously test-only data and
  did not reach cleanup verdict or signal scope. **Decision:** propagate
  canonical foreign/unknown observations into lane resource mappings, mark
  cleanup `untrusted-resource`, return nonzero, and skip all signal/reap calls
  for affected entries; only current-run PGID mappings may be signaled. **Impact:**
  foreign canonical resources remain untouched and six-lane preflight-blocked
  receipts remain explicit. **Evidence:** `_propagate_resource_inventory`,
  `_resource_cleanup_verdict`, `_owned_process_group`, and controlled foreign
  resource/receipt tests.
- **Context:** existing lane receipts listed every canonical port for every
  lane, obscuring which child could own a listener. **Decision:** map `e2e` to
  `8765,8767`, `bdd` to `8766`, `visual` to `8768`, and non-server lanes to no
  ports; retain fixed DB mapping per lane. **Impact:** receipts expose exact
  lane resource boundaries without changing six-lane topology or taskipy
  commands. **Evidence:** partial-launch receipt mapping assertions.
- **Context:** review R2 showed that final receipt creation happened only after
  cleanup, log/timing collection, reconciliation, and serialization had all
  succeeded. A red integration lane could therefore terminate siblings while
  leaving no durable run identity, wall-clock, or cleanup evidence. **Decision:**
  create exact `<stamp>-run.json` ledger before first `Popen`, persist snapshots
  after each lifecycle boundary, and write snapshots with flushed temporary-file
  replacement. Serialization failures record `receipt_error` and retry with
  JSON-safe diagnostics; write failures remain nonzero and never erase
  in-memory telemetry. **Impact:** crash/failure/finalization paths retain six
  lane placeholders, first-failure lane/reason, sibling-stop signals, return
  codes, cleanup verdict, and elapsed-through-cleanup timing. **Evidence:**
  `test_runner_persists_six_placeholders_before_first_launch`,
  `test_runner_retains_partial_artifacts_after_lane_finalization_exception`,
  `test_runner_receipt_retains_first_integration_failure_and_sibling_reason`,
  and `test_runner_serialization_failure_falls_back_without_losing_telemetry`.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `scripts/run_full_suite.py::_stop` | Sends group signal and suppresses only `ProcessLookupError`; no per-entry result | Signal only recorded owned process groups; classify expected vanished/PID-not-found/EPIPE races as bounded observations and retain diagnostics for unexpected errors | Prevent cleanup race from hiding causal result or touching foreign resources |
| `scripts/run_full_suite.py::_reap` | Boolean grace/KILL result with no lane evidence | Reap returns/updates per-lane cleanup evidence: survivor list, signal/escalation, absent/no-op state, wait result, and bounded cleanup verdict | Make descendant survivor and cleanup outcomes auditable |
| `scripts/run_full_suite.py::_final_exit_code` | Chooses interruption/first failure/child return after boolean cleanup | Preserves known interruption, first lane failure, and deadline before applying cleanup/receipt failure; never converts incomplete cleanup to success | Preserve causal failure and safe nonzero semantics |
| `scripts/run_full_suite.py::main`, `launch`, `monitor`, receipt finalization | Metadata starts only after successful launch; cleanup and lane receipts incomplete | Pre-register all six lanes, record PID/PGID/resources/timestamps/status/reasons through lifecycle, and always write complete lane/run receipts | Cover partial launch, sibling stop, timeout, vanished child, and cleanup failure |
| `scripts/run_full_suite.py::_preflight` / resource reconciliation | Checks ports/DB targets but does not carry ownership evidence into cleanup receipt | Preserve existing checks and attach exact owned resource mapping/classification; reject unknown/foreign cleanup rather than broad repair | Apply D05 vocabulary without changing preflight topology or production safety |
| `scripts/run_expanded_lane.py::main` | Sequential visual-pruned then selected pytest task execution | Preserve same taskipy commands and return semantics; no canonical lane/cleanup/topology expansion | Keep expanded lane separate and prevent coverage/lane drift |
| `pyproject.toml:[tool.taskipy.tasks]` test tasks | `test` delegates to canonical runner and six task names define lane behavior | No command/topology change; verify taskipy entrypoint remains exact and document no raw-command fallback only if needed | Preserve task contract, coverage, skips, and six lanes |
| `tests/scripts/test_t29_harness.py` runner tests | Covers DB receipts, reconciliation, first failure, parent signal, and timing | Add controlled scenarios for vanished child, survivor, foreign resource, fail-fast sibling stop, partial launch, and timeout/complete receipts | Lock measurable acceptance without host cleanup or reduced coverage |
| I08 delta `specs/dev-tasks/spec.md` | Existing dev-task requirement requires groups/signals/reap and nonzero failure but not complete ownership telemetry/race semantics | Full modified requirement adds D05 vocabulary, owned-only descendant/resource cleanup, complete six-lane receipts, causal failure preservation, and six controlled scenarios while preserving all existing invariants | Stable implementation oracle for apply/review |

## Validation and compatibility

- Focused command is `uv run task test-file tests/scripts/test_t29_harness.py`;
  implementation may add narrower `task test-one` invocations while debugging,
  but must report exact results. No canonical `uv run task test` at proposal or
  apply gate; review retains exactly one full-suite invocation.
- Validate OpenSpec change syntax and stable specs after artifacts; validate
  changed-file scope and whitespace. Stable `dev-tasks` remains unchanged until
  owner-authorized archive/sync; I08 delta is the apply oracle.
- Preserve all current `test_*` task commands, coverage producers (unit and
  integration), browser `--no-cov`, expected skips, manifest reconciliation,
  six lane order, fail-fast, signal exit, and 300-second ceiling.
- Error policy: expected child disappearance is recorded and bounded; foreign
  or unknown resource is preserved and makes cleanup untrusted/nonzero;
  unexpected cleanup error is recorded and nonzero; original known failure or
  deadline remains primary.

## Risks / Trade-offs

- **Cleanup helper catches too broadly** → catch only expected lifecycle races,
  retain error class/message metadata without secrets, and test unexpected
  errors as nonzero.
- **PGID/PID reuse is mistaken for ownership** → record process group at launch,
  owner/run identity, start timestamp, and exact resource evidence; never adopt
  a matching external process or port.
- **Partial launch drops a lane** → create all six receipt entries before
  `Popen`; launch failures carry explicit status and null identity.
- **Receipt writing fails after cleanup** → preserve in-memory lane/run evidence,
  attempt final serialization once, return nonzero on receipt failure, and never
  claim green from missing telemetry.
- **Telemetry changes timing** → keep bounded polling/grace/deadline constants,
  avoid retries/full-suite reruns, and assert hard 300-second classification.
- **D05 dependency is misrepresented** → keep exception in proposal/design/
  tasks; state D05 remains Blocked and do not edit D05 or claim approval/archive.
- **T33/T32 mixed harness history is reopened** → limit tests to I08 scenarios
  in the named file, preserve existing tests, and do not alter lane topology or
  archived T33/T32 state.

## Migration Plan

1. Apply only mapped runner/taskipy verification/test files plus I08 artifacts;
   do not edit D05, F58/F58 R1-F02, F61, agent docs, reports, DB, or host
   resources.
2. Run focused harness taskipy validation and inspect diff/scope. Review later
   owns one canonical full-suite run and its receipt; no proposal/apply full
   suite or refresh-for-test is part of this proposal gate.
3. Rollback is a revert of I08 runner/test/task changes and unsynced delta;
   there is no migration, seed, server, or persistent resource operation.

## Open Questions

- None blocking proposal. Implementation must choose concrete in-process ledger
  shape and narrow lifecycle-race exception handling within decisions above;
  it must not invent ownership rules or broaden cleanup.

## Dependency Exception Record

- **Dependency:** D05 `d05-formalizar-contrato-operacional-de-limpeza-e-preflight`.
- **Normal condition:** roadmap says I08 depends on D05 approved ownership/stop
  vocabulary.
- **Observed lifecycle:** D05 status is `Blocked`; its documentation-only
  contract audit passed, while review full suite was blocked/red by unrelated
  unknown PID and visual failures. D05 is not approved or archived.
- **Owner authorization:** owner explicitly authorizes I08 proposal/apply to
  consume D05's audited vocabulary now, without changing D05 state or claiming
  D05 approval/archive.
- **Scope guard:** exception covers vocabulary consumption only. I08 must keep
  D05 as read-only evidence, preserve D05 classifications/prohibitions, and
  leave D05, F58/F58 R1-F02, F61, T33, agent docs, and host resources untouched.

## Proposal Gate Evidence

- Inspected roadmap I08/D05 entries and dependency order; D05 proposal/design/
  tasks/delta and review R1/R2 evidence; F61 R1/R2 evidence; F58 R1-F01 and
  R1-F02 evidence; runner/taskipy/test files named by I08.
- No implementation code, test, taskipy, lint, full suite, server, cleanup,
  database, browser, network, or external-service command was run.

### Validation receipt

- `openspec status --change
  i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane --json` → complete;
  proposal, design, specs, and tasks are `done`; `applyRequires: ["tasks"]`
  satisfied.
- `openspec validate i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane
  --type change --strict --json` → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json` → valid, 70/70 stable specs
  passed, 0 failures; existing informational long-requirement notices only.
- `rtk git diff --check --
  openspec/changes/i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane`
  → clean; scope contains only I08 `.openspec.yaml`, proposal, design, tasks,
  `specs/dev-tasks/spec.md`, plus the authorized I08 lifecycle/progress/
  dependency-exception lines in `openspec/roadmap.md`.
- Tests run: none. No taskipy test/lint, canonical full suite, server,
  cleanup, process operation, database, browser, network, or external-service
  command was run at proposal gate.

### Owner-authorized surgical follow-up

- **Context:** Review R3 left one real CSV integration failure and five approved
  desktop visual baseline failures unclassified. The canonical Italo seed uses
  `avg_price` and `current_price` headers, while `_normalize_cell` preserves
  underscores and the parser's alias lists omitted both labels. The target test
  still asserted the prior SMH fixture values.
- **Decision:** Apply only the two missing aliases, update only the SMH target
  assertions, and refresh only the five owner-named desktop baselines. Preserve
  normalization, fallback, numeric heuristics, seed/loaders, totals, CSS,
  templates, snapshot logic, F58, D05, I08 runner mechanics, production DB, and
  MyProfit behavior.
- **Impact:** Real CSV parsing now consumes canonical snake_case price headers;
  SMH contract is qty `11`, avg `990.92`, current `2974.98`. Visual references
  align with owner-approved current seed state. No new lane, suite policy, or
  parser behavior was introduced.
- **Evidence:** Pre-edit `git diff HEAD~1` captured; focused CSV tests reproduced
  the old assertion failure, then passed after the two aliases; baseline update
  initially selected seven desktop screenshots, and the two unapproved stub
  baselines were restored immediately, leaving exactly five named baseline files.
