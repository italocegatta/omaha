## Preflight Boundaries

- Captured `rtk git diff HEAD~1` before editing. Pre-existing work includes
  `.env.example`, `.opencode/agents/apply.md`, `.opencode/agents/review.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`, `AGENTIC_DEVELOPMENT.md`,
  `README.md`, `data/seed/italo_classes.csv`, `openspec/roadmap.md`,
  `openspec/specs/myprofit-profile-credentials/spec.md`, `pyproject.toml`,
  `src/omaha/config.py`, `tests/conftest.py`, `tests/test_auth.py`,
  `tests/test_f57_myprofit_profile_config.py`, and `uv.lock`, plus untracked
  D05/F58/I08 dossiers and F58 connector files. Diff showed `pyproject.toml`
  changes only for F58 dependencies; no I08 runner or harness hunk exists.
- I08 owns only `scripts/run_full_suite.py`,
  `scripts/run_expanded_lane.py`, the existing taskipy definitions in
  `pyproject.toml` if verification requires a no-op-preserving edit,
  `tests/scripts/test_t29_harness.py`, and I08 artifacts/evidence. D05 docs,
  F58/F58 R1-F02, F61, application files, DB, reports, local `.env`, host
  processes, ports, and unrelated hunks remain outside this slice.
- No real child termination, port cleanup, broad process discovery, DB reset,
  server refresh, or canonical full-suite command is permitted at apply.

## 1. Record complete owned lane lifecycle

- [x] 1.1 `scripts/run_full_suite.py::main`, nested `launch`, metadata setup,
  and receipt finalization — pre-register one ledger/receipt entry for each
  `LANES` item before any `Popen`; record lane/task, PID/PGID or explicit null,
  exact log/timing paths, owned DB/resource mapping, owner evidence,
  `started_at`/`ended_at`, launch status/error, signal, return code, sibling
  stop reason, residue classification, cleanup result, and timeout telemetry;
  update entries through launch, monitor, reap, log parsing, DB validation, and
  final JSON write. Preserve current six-lane order, task names, environment
  variables, log/timing formats, manifest/node/skip reconciliation, and one
  `<stamp>-run.json` output. Acceptance: partial launch and any cleanup/receipt
  error still produce six explicit lane entries and run-level elapsed,
  deadline, cleanup, and reconciliation evidence; missing identity is null plus
  reason, never omitted or green. Test file/scenario:
  `tests/scripts/test_t29_harness.py::test_runner_partial_launch_emits_all_lane_receipts`
  and receipt-field assertions for successful/failed entries. Focused taskipy
  command: `uv run task test-file tests/scripts/test_t29_harness.py`. Independent
  oracle: JSON shape contains exactly `runner.LANES` lane keys and every
  required field/status, including failed launch with null PID/PGID.

- [x] 1.2 `scripts/run_full_suite.py::_preflight`, `_validate_db_targets`,
  `_lane_environment`, and ledger/resource reconciliation — bind exact
  current-run ownership evidence to process group, log/timing, permitted lane
  DB, and any mapped test resource; classify absent, owned-current-run,
  owned-cleaned, foreign, unknown, or pre-existing without adopting matches.
  Preserve production DB refusal, four-port preflight, lane DB allow-list,
  lane-scoped `T29_DB_RECEIPT_LANE`, and no raw pytest/DB task execution.
  Acceptance: foreign process/port/resource double remains untouched and receipt
  records foreign/unknown residue as untrusted/nonzero; owned resource is the
  only cleanup target and repeated absence is idempotent no-op. Test file/
  scenario: `tests/scripts/test_t29_harness.py::test_runner_preserves_foreign_resource`
  and owned-resource/idempotence cases. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  monkeypatched signal/resource calls show no call for foreign identity and
  exact owned group/resource mapping for cleanup.

## 2. Harden signal, fail-fast, deadline, and reap behavior

- [x] 2.1 `scripts/run_full_suite.py::_stop` and signal handler — signal only
  live, current-run-owned process groups; record signal and sibling-stop reason;
  classify `ProcessLookupError`/PID-not-found, `NoSuchProcess`, and EPIPE
  between poll/signal as bounded vanished-child observations, while preserving
  unexpected errors as diagnostics. Preserve parent SIGINT/SIGTERM exit
  semantics and fail-fast first-failure capture. Acceptance: vanished child
  does not raise over original lane failure, no retry/broad kill occurs, and
  foreign group is never signaled. Test file/scenario:
  `tests/scripts/test_t29_harness.py::test_runner_vanished_child_during_signal_preserves_failure`
  plus parent SIGTERM and fail-fast sibling cases. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  fake `os.killpg` raises expected lifecycle errors; assertions verify one
  owned-group attempt, recorded race, original exit code, and no foreign call.

- [x] 2.2 `scripts/run_full_suite.py::_reap`, `_stop_deadline`,
  `_duration_exceeded`, and `_final_exit_code` — make bounded grace, owned-only
  SIGKILL escalation, wait/reap, cleanup verdict, and causal exit selection
  explicit. Preserve `GRACE_SECONDS`, timeout code 124, deadline margin, parent
  interruption priority, first lane failure, and nonzero result for cleanup or
  receipt failure. Acceptance: descendant survivor is escalated only within
  owned PGID; vanished child before wait is recorded/no-op; timeout receipt
  includes deadline and elapsed-through-cleanup and returns 124; cleanup cannot
  convert known failure to success. Test file/scenario:
  `tests/scripts/test_t29_harness.py::test_runner_reaps_owned_survivor`,
  `::test_runner_vanished_child_during_wait`, and
  `::test_runner_timeout_receipt_includes_cleanup`. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  fake clock/processes and monkeypatched `killpg`/wait produce exact signal
  order, survivor evidence, causal return code, and `duration_exceeded` state.

- [x] 2.3 `scripts/run_full_suite.py::monitor`, `launch`, and finalization —
  preserve first nonzero lane and deadline before sibling cleanup, handle launch
  failure without entering an unowned process path, and retain diagnostic
  telemetry when lane log/timing/DB receipt is partial. Preserve fail-fast,
  all-six lane finalization, collection reconciliation, expected skips, and no
  second suite/retry. Acceptance: fail-fast receipt identifies failing lane,
  every sibling signal/reason, partial launch has no fabricated success, and
  missing lane output is explicit plus nonzero. Test file/scenario:
  `tests/scripts/test_t29_harness.py::test_runner_fail_fast_receipt_attributes_sibling_stop`
  and partial-launch/partial-receipt cases. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  deterministic fake process sequence yields first failure as final causal code,
  six lane records, and no signal outside owned launched groups.

## 3. Preserve taskipy entrypoints and lock controlled harness coverage

- [x] 3.1 `scripts/run_expanded_lane.py::main` and
  `pyproject.toml:[tool.taskipy.tasks]` entries `test`, `test-unit`,
  `test-integration`, `test-audit-integration`, `test-e2e`, `test-visual`,
  `test-bdd`, and `test-t32-expanded` — inspect and preserve exact taskipy
  commands, coverage/no-coverage flags, expanded-lane separation, and return
  semantics; make no raw pytest fallback, new lane, task rename, selection,
  skip, or ceiling change. Acceptance: diff contains no task/lane topology
  change and `uv run task test` still resolves to `uv run python -m
  scripts.run_full_suite`; expanded lane remains separately named. Test file/
  scenario: `tests/scripts/test_t29_harness.py` command-construction and
  existing lane/coverage assertions. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py`. Independent oracle:
  exact `pyproject.toml` task strings and `runner.LANES` equal pre-change six
  names/order; `git diff` shows no unrelated task or topology hunk.

- [x] 3.2 `tests/scripts/test_t29_harness.py` — add deterministic controlled
  doubles for vanished child between poll/signal/wait, owned descendant
  survivor, foreign process/port/resource, fail-fast sibling stop, partial
  launch, and timeout; assert complete per-lane receipts, PID/PGID/resource
  evidence, cleanup verdict, causal return code, six lanes, fail-fast,
  coverage/skips, and 300-second classification. Preserve every existing test,
  marker, T33 lifecycle assertion, DB receipt assertion, reconciliation case,
  and no-mask policy; do not kill real processes or bind canonical ports.
  Acceptance: each roadmap scenario has a named passing focused test, no
  `skip`/`xfail`/test deletion is introduced, and foreign resource remains
  untouched. Test file/scenario: this exact file, scenarios listed above.
  Focused taskipy command: `uv run task test-file tests/scripts/test_t29_harness.py`.
  Independent oracle: focused pytest output is green and source audit finds no
  broad process discovery/termination or masked-pass construct.

## 4. Validate I08 dossier and scoped implementation evidence

- [x] 4.1 I08 change directory and delta `specs/dev-tasks/spec.md` — record
  implementation results against every modified requirement/scenario, including
  vanished child, owned survivor, foreign preservation, fail-fast, partial
  launch, timeout, six complete receipts, taskipy, coverage/skips, and <=300s;
  validate exact change artifacts and changed-file scope. Preserve D05 as
  `Blocked` and read-only; do not claim D05 approved/archived or alter D05,
  F58/F58 R1-F02, F61, T33, agent docs, DB, reports, or host resources.
  Acceptance: proposal/design/tasks/delta are complete/apply-ready; strict
  change and stable-spec checks pass; diff scope is only I08 artifacts plus
  mapped runtime/test files; no full suite was run at apply gate. Test file/
  scenario: OpenSpec artifact validation and scope audit, with focused harness
  receipt from task 3.2. Focused taskipy command:
  `uv run task test-file tests/scripts/test_t29_harness.py` (implementation
  evidence; not proposal gate). Independent oracle: `openspec status --change
  i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane --json`, strict
  change/spec validation, `git diff --check`, and mapped-file audit.

## Test strategy

- Primary focused test file: `tests/scripts/test_t29_harness.py`, marked unit
  and executed only through taskipy `uv run task test-file
  tests/scripts/test_t29_harness.py` (or narrower taskipy `test-one` during
  debugging). Controlled doubles monkeypatch process, signal, clock, and file
  boundaries; no real process termination, port cleanup, DB reset, server, or
  external service is allowed.
- Required scenarios: child vanishes between poll/signal/wait; owned descendant
  survivor; foreign process/port/resource preservation; fail-fast sibling stop;
  partial launch; timeout/deadline; complete six-lane receipts; existing DB
  receipt and population/skip reconciliation.
- Focused acceptance oracle: green named tests, exact owned-only signal calls,
  unchanged foreign doubles, complete six-lane JSON entries, preserved causal
  exit code, cleanup/timeout telemetry, and unchanged taskipy command strings.
- No proposal-gate tests or taskipy command run before artifacts are complete;
  no canonical `uv run task test` at proposal/apply gate. Review owns exactly
  one later full-suite invocation and must evaluate all six lanes, coverage,
  skips, fail-fast, cleanup, and <=300 seconds.

## Execution Evidence

### Initial apply pass

- Tasks 1.1/1.2/2.1/2.2/2.3 complete. Changed
  `scripts/run_full_suite.py` symbols `_lane_metadata`, `_stop`, `_reap`,
  `main.launch`, `main.monitor`, signal handling, and receipt finalization.
  Six lanes register before `Popen`; each receipt carries PID/PGID or null,
  ports, owned-resource mapping, owner evidence, timestamps, signal, return
  code, sibling reason, timeout, residue, cleanup, and launch/receipt
  diagnostics. Lifecycle races are limited to PID-not-found/ESRCH,
  `NoSuchProcess`, EPIPE, and `BrokenPipeError`; foreign entries never enter
  process map or signal path. Known interruption/first-failure/deadline values
  remain primary over cleanup status.
- Tasks 3.1/3.2 complete. `scripts/run_expanded_lane.py` and taskipy lane
  commands in `pyproject.toml` remain unchanged by I08; controlled doubles in
  `tests/scripts/test_t29_harness.py` cover vanished signal/wait, NoSuchProcess,
  owned survivor SIGKILL, foreign resource preservation, fail-fast sibling
  attribution, partial launch, complete six-lane receipt fields, and timeout
  receipt cleanup evidence. No real process, canonical port, host scan, or DB
  operation was used.
- Task 4.1 complete. I08 `design.md` records concrete implementation
  decisions and this file records boundaries/evidence. I08 delta remains
  unchanged as apply oracle; D05 remains read-only and `Blocked`.
- Focused validation: `uv run task test-file tests/scripts/test_t29_harness.py`
  -> **40 passed**. First `uv run task lint` invocation only formatted mapped
  files and returned hook modified-files failure; rerun `uv run task lint` ->
  **passed**. `uv run python -m compileall -q scripts/run_full_suite.py
  tests/scripts/test_t29_harness.py` -> **passed**.
- OpenSpec validation: strict I08 change validation -> valid, 1/1 passed,
  0 issues. Strict stable-spec validation -> valid, 70/70 passed, 0 failures;
  existing informational long-requirement notices only. `git diff --check` on
  I08 mapped files -> clean.
- No canonical `uv run task test`, refresh, server, DB reset, real process
  cleanup, port cleanup, or external service operation was run.

## Acceptance evidence

- Signal-safe vanished-child behavior: named tests demonstrate
  PID-not-found/`NoSuchProcess`/EPIPE observations do not obscure causal lane,
  sibling, interruption, or deadline failure.
- Owned-only descendant/resource cleanup: named tests demonstrate exact PGID/
  resource ownership, bounded escalation, idempotent absent cleanup, and no
  broad process termination.
- Complete telemetry: every six-lane receipt includes PID/PGID/null, owned
  mapping, start/end, signal/return, cleanup, residue/foreign evidence, sibling
  reason, and timeout/deadline state, including partial launch/failure.
- Preserved invariants: six lanes/order, fail-fast, coverage producers,
  retained tests/skips, taskipy entrypoint/flags, expanded lane separation, and
  300-second hard ceiling remain unchanged.
- Scope/dependency: D05 audited vocabulary consumed under owner exception;
  D05 remains `Blocked`, not approved/archived; F58/F58 R1-F02 and F61 remain
  separate; no agent docs or host/process resources changed.

## Proposal Gate Evidence

- `openspec status --change
  i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane --json` → complete;
  all four planning artifact IDs are `done`; apply-ready.
- `openspec validate i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane
  --type change --strict --json` → valid, 1/1 passed, 0 issues.
- `openspec validate --specs --strict --json` → valid, 70/70 stable specs
  passed, 0 failures; informational long-requirement notices only.
- `rtk git diff --check --
  openspec/changes/i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane`
  → clean. Scoped status lists only `.openspec.yaml`, `proposal.md`,
  `design.md`, `tasks.md`, and `specs/dev-tasks/spec.md`; roadmap changes are
  limited to I08 lifecycle/progress/dependency-exception lines.
- Tests run: none. Proposal gate intentionally ran no taskipy command,
  pytest, full suite, lint, server, cleanup, database, browser, network, or
  external-service operation.
- D05 exception remains durable: D05 status/lifecycle and dossier were not
  changed; I08 consumes audited vocabulary only and cannot claim D05 approved
  or archived.

## Review Findings

### Review R1
Scope audit: dossier/proposal/design/tasks/delta-spec `pass`; apply evidence and
8/8 tasks `pass`; six pre-registered lane receipts `pass` by source audit;
vanished-child handling `pass` for narrow lifecycle exceptions; current-run
process-group signal/reap `pass`; foreign-resource preservation and untrusted
residue propagation `finding`; first-failure/fail-fast and timeout mechanics
`pass` by source audit; taskipy, six lanes, coverage, skips, manifest
reconciliation, and 300-second preservation `pass` by source audit; focused
harness scenario presence `finding`; D05 isolated-runner preflight `finding`;
scope boundaries and F58/D05 exclusions `pass`; OpenSpec validation `pass`;
full-suite acceptance `not assessable` because trusted preflight blocked before
launch.

Full suite: `uv run task test` -> NOT RUN; canonical run correctly withheld after
unclean isolated-runner preflight; duration N/A; cleanup N/A (no suite
resources created and no cleanup attempted); duration limit 300 seconds;
explicit verdict `BLOCKED`.

Preflight receipt: `D05-R1-2026-08-20T17:31:57-03:00`. Owner-selected policy:
runner isolated, no foreign baseline or allowlist exception. Inventory found
unowned listeners `0.0.0.0:8000` and `0.0.0.0:5443`, `opencode` PID 252080
listening on `0.0.0.0:4096`, and pre-existing `/tmp/pytest-of-juca/` with
pytest directories and `pytest-current` symlink. No current-run ledger or owner
evidence existed for these resources. All classified pre-existing/unknown;
nothing was killed, adopted, allowlisted, freed, or deleted. Preflight stopped
before suite launch, per D05 isolation protocol.

OpenSpec verification: `openspec validate
i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane --type change --strict
--json` -> valid, 1/1 passed, 0 issues; `openspec validate --specs --strict
--json` -> valid, 70/70 passed, 0 failures (informational long-requirement
notices only); D05 status remains complete artifacts / lifecycle `Blocked` and
was read-only during review.

Verdict: BLOCKED

#### R1-F01 — Isolated-runner preflight has unowned relevant residue
Status: resolved in remediation 1; canonical full-suite gate remains review-owned
Requirement/task: D05 isolated-runner policy; I08 task 4.1; delta Scenario
`Full task concurrently preserves complete coverage` and D05 review preflight
contract.
Evidence: preflight receipt above; `ss -ltnp` showed listeners on 8000, 5443,
and 4096; `opencode` PID 252080 owned no I08 ledger entry; `/tmp/pytest-of-juca/`
contained pre-existing pytest state. D05 policy forbids cleanup, adoption,
baseline exception, or allowlist exception.
Required change: owner must provide isolated runner with no unowned relevant
process, listener, or test-temporary resource, then request one new review
gate. Excluded scope: no host cleanup, environment repair, D05 edits, F58/F58
R1-F02 edits, or I08 code/test edits by review.
Acceptance: repeat preflight records complete inventory and ownership ledger;
only `absent` or current-run `owned-current-run`/`owned-cleaned` remains; then
exactly one `uv run task test` runs and produces six-lane postflight receipt.

#### R1-F02 — Resource residue cannot become untrusted cleanup result
Status: resolved in remediation 1
Requirement/task: I08 delta Requirement `Test coverage report`, lines 20-34;
tasks 1.2 and 3.2; scenarios `Foreign process or port is preserved` and
`Full task concurrently preserves complete coverage`.
Evidence: `scripts/run_full_suite.py:227-262` initializes database and port
resources as `unknown`; `scripts/run_full_suite.py:904-925` computes cleanup
success only from child `cleanup_result` and `clean`, without checking those
resource classifications or reconciling foreign/unknown resources. No runner
path records a foreign port/process/path observation as residue and forces
untrusted/nonzero. The focused test at
`tests/scripts/test_t29_harness.py:436-445` creates `foreign` but never passes
it to `_stop` or any resource reconciliation, so it proves no foreign-resource
contract.
Required change: implement explicit per-resource preflight/postflight
classification and receipt propagation; preserve every foreign/unknown
resource without action and force cleanup verdict untrusted plus nonzero when
observed. Replace/extend controlled harness coverage to inject foreign
process/port/resource observations and assert zero foreign calls, residue
classification, untrusted cleanup, and nonzero exit. Excluded scope: no lane
topology, coverage, skip, timeout, D05 protocol, F58, or host-resource change.
Acceptance: controlled foreign-resource scenario leaves foreign identity
untouched, emits residue evidence, returns nonzero; owned resources alone may
reach `owned-cleaned` and clean verdict.

#### R1-F03 — Full-suite acceptance remains unassessed
Status: open — intentionally unassessed; review-owned
Requirement/task: I08 task 4.1; delta scenarios `Full task concurrently
preserves complete coverage`, `Fail-fast sibling stop is attributable`, and
`Deadline includes bounded cleanup`; PRD §4.13.
Evidence: no six-lane receipt, coverage/skips receipt, fail-fast disposition,
postflight cleanup receipt, or elapsed wall-clock exists because R1-F01 blocked
before launch. Apply's 40 focused harness tests cannot establish canonical
suite green or <=300 seconds.
Required change: after R1-F01 resolution (and R1-F02 remediation), run exactly
one timed `uv run task test`; record all six lane outcomes, coverage, skips,
fail-fast disposition, cleanup/postflight state, elapsed wall-clock, and 300s
classification. Excluded scope: no suite rerun in this review, no test masking,
skip reduction, coverage reduction, or timeout relaxation.
Acceptance: green canonical suite, trusted cleanup/postflight, complete six
lane receipt, and elapsed wall-clock <=300 seconds.

### Remediation 1 — bounded canonical preflight and receipt propagation

- R1-F01 resolved in implementation scope. `scripts/run_full_suite.py` now
  declares canonical ports `8765-8768`, fixed test DB paths, and current-run
  PGID/path/log evidence. Observations on `8000`, `5443`, `4096`, and
  `/tmp/pytest-of-juca/` are recorded with `relevant=false`,
  `classification=pre-existing`, `preserved=true`, `allowlisted=false`,
  `adopted=false`, and `cleanup_target=false`; no host-wide scan or cleanup is
  introduced. `tests/scripts/test_t29_harness.py` covers harmless host
  observations and pre-existing pytest root.
- R1-F02 resolved in implementation scope. Canonical foreign/unknown
  observations propagate through `_propagate_resource_inventory` into lane
  mappings and residue, force `cleanup.verdict=untrusted` plus nonzero result,
  and prevent `_stop`/`_reap` signal or wait targeting for affected entries.
  Owned PGID cleanup remains bounded and tested. Canonical preflight blocking
  emits six explicit `preflight-blocked` lane receipts. No destructive process,
  port, path, or DB operation is used by controlled tests.
- R1-F03 remains open and intentionally unassessed. No canonical
  `uv run task test` was run in this remediation; later review owns exactly one
  full-suite acceptance receipt.

### Execution Evidence — Remediation 1

- Changed files/symbols: `scripts/run_full_suite.py` — `LANE_PORTS`,
  `CANONICAL_DATABASE_PATHS`, `PreflightError`,
  `_canonical_resource_inventory`, `_preflight`,
  `_write_preflight_blocked_receipt`, `_propagate_resource_inventory`,
  `_resource_cleanup_verdict`, `_owned_process_group`, `_stop`, `_reap`,
  `_lane_metadata`, launch/final receipt paths; `tests/scripts/test_t29_harness.py`
  — controlled canonical inventory, foreign propagation, owned cleanup,
  preflight receipt, and per-lane mapping assertions.
- Focused validation: `uv run task test-file
  tests/scripts/test_t29_harness.py` -> **45 passed**; `uv run task lint` ->
  **passed** on second invocation after formatter hook; `uv run python -m
  compileall -q scripts/run_full_suite.py tests/scripts/test_t29_harness.py` ->
  **passed**.
- OpenSpec validation: strict I08 change validation -> valid, 1/1 passed,
  0 issues; strict stable-spec validation -> valid, 70/70 passed, 0 failures;
  existing informational long-requirement notices only; `git diff --check`
  mapped files -> clean.
- Boundary confirmation: no D05, F58, F61, application files, taskipy
  entrypoint, lane topology, coverage/skips, ceiling, server, DB reset, host
  resource, or canonical full-suite file/operation changed or run.

## Review Findings

### Review R2
Scope audit: dossier/proposal/design/tasks/delta-spec `pass`; 8/8 tasks `pass`;
R1-F01 resolution `pass` by focused canonical/irrelevant inventory tests;
R1-F02 resolution `pass` by focused foreign-resource propagation and owned-only
signal tests; vanished-child handling `pass`; process-group ownership and
bounded reap `pass`; six-lane receipt source coverage `pass`; taskipy/lane
topology/coverage/skips/manifest preservation `pass` by source audit; D05/F58
scope isolation `pass`; OpenSpec validation `pass`; canonical full-suite
acceptance `finding`; full-suite wall-clock measurement `not assessable`.

Full suite: `uv run task test` -> **RED**. Runner printed unit=0,
integration=1, audit=0, e2e=241, bdd=241, visual=241. E2E/BDD/visual 241 are
fail-fast sibling-stop consequences after integration failure, not independent
failures. Per-lane receipt/log for run stamp `20260820T175206` was absent after
command; no six-lane postflight JSON was available. Existing lane evidence
shows BDD failure `tests/bdd/test_scenarios.py::test_full_journey_import_modal`
(`1 failed, 38 passed in 110.29s`), but cannot prove it belongs to this run
because runner receipt is missing. Integration exit=1 has no retained lane
summary or traceback. Timing wrapper failed after suite completion with
`python: command not found`; external wall-clock duration is therefore
unknown. Available lane timing: BDD 110.29s, E2E 86.42s. Cleanup state:
unknown; runner emitted no postflight receipt, while no host cleanup command
was run. Duration limit 300 seconds: not assessable. Explicit verdict
`BLOCKED`.

Verdict: BLOCKED

#### R2-F01 — Canonical suite red with missing causal receipt
Status: blocked
Requirement/task: I08 task 4.1; delta Requirement `Test coverage report`,
Scenarios `Full task concurrently preserves complete coverage` and `Fail-fast
sibling stop is attributable`; PRD §4.13; R1-F03.
Evidence: exactly one `uv run task test` invocation produced integration exit
1 and sibling exits 241; no `20260820T175206-run.json` or corresponding lane
logs exist under `reports/test-profile/`; command output ended after lane exit
lines. Existing `reports/bdd_durations.log` records
`tests/bdd/test_scenarios.py::test_full_journey_import_modal` failed, but run
identity is unproven. Integration failure cause is unknown because its receipt,
summary, and traceback are unavailable. This is an **Unknown** test failure,
not safe to attribute to I08 or pre-existing work.
Required change: owner must provide isolated rerun evidence with durable
per-lane logs/run receipt and diagnose integration failure before any approval;
then run one new review gate under exact one-suite policy. If failure is slice
bug, fix runner/receipt preservation; if test drift, update test to intended
behavior; if regression, revert/fix injected change; if environmental,
re-establish isolated environment. Do not mask, skip, delete, or reduce tests.
Excluded scope: no host cleanup, no D05/F58 edits, no review-side code/test
fix, no extra suite retry in this gate.
Acceptance: one canonical run records all six lanes, coverage, skips,
fail-fast cause, trusted cleanup/postflight verdict, and external wall-clock
duration <=300s; every red failure has stable traceback and classification;
suite green.

#### R2-F02 — Full-suite wall-clock and cleanup receipt unavailable
Status: blocked
Requirement/task: I08 tasks 1.1, 2.2, 4.1; delta Scenarios `Deadline includes
bounded cleanup` and `Full task concurrently preserves complete coverage`;
PRD §4.13.
Evidence: wrapper around canonical command attempted external timing but
failed to print duration because environment lacks `python`; runner receipt
for `20260820T175206` is absent, so elapsed-through-cleanup, deadline
classification, and cleanup trust cannot be verified. Available BDD/E2E lane
durations do not establish full process wall-clock or cleanup duration.
Required change: preserve runner receipt through failing runs and provide a
portable external timing receipt before review; record cleanup trust and
elapsed wall-clock from runner start through child cleanup. Do not rerun this
gate or alter the 300-second ceiling/coverage policy here.
Excluded scope: no host/process/port cleanup, no D05/F58 changes, no test
masking, no timeout relaxation.
Acceptance: canonical receipt contains `elapsed_seconds`,
`through_elapsed_seconds`, `duration_exceeded`, six lane cleanup states, and
final cleanup verdict; externally measured command duration is <=300s.

### Remediation 2 — crash-safe run receipt persistence

- **R2-F01 — resolved in I08.** `scripts/run_full_suite.py` now persists the
  run identity and all six placeholder lane records before first `Popen`, then
  persists after launch, fail-fast/deadline stop, cleanup, each lane log/timing
  and DB reconciliation, population reconciliation, and finalization. First
  failure stores lane, reason, return code, and sibling-stop signals before
  cleanup; later receipt errors append to `receipt_errors` and do not replace
  prior lane telemetry. Controlled finalization/partial-artifact coverage is in
  `test_runner_retains_partial_artifacts_after_lane_finalization_exception`.
- **R2-F02 — resolved in I08 implementation; canonical measurement remains
  review-owned.** Receipt writes use flushed temporary-file replacement and
  retain `elapsed_seconds`, cleanup `through_elapsed_seconds`, deadline state,
  six cleanup results, final cleanup verdict, and serialization/write errors.
  Serialization fallback converts only failed snapshot to JSON-safe diagnostics
  while preserving prior run identity, return code, and sibling reason. Coverage
  is in `test_runner_persists_six_placeholders_before_first_launch` and
  `test_runner_serialization_failure_falls_back_without_losing_telemetry`.

### Execution Evidence — Remediation 2

- Changed files/symbols: `scripts/run_full_suite.py` —
  `_record_receipt_error`, `_json_safe`, `_atomic_write_receipt`,
  `_persist_receipt`, pre-launch ledger, launch/monitor/cleanup persistence,
  lane artifact/finalization guards, and final elapsed/cleanup receipt fields;
  `tests/scripts/test_t29_harness.py` — pre-launch six-placeholder,
  finalization exception/partial-artifact, and serialization-fallback controlled
  tests; `design.md` — crash-safe receipt implementation decision.
- Focused validation: `uv run task test-file
  tests/scripts/test_t29_harness.py` -> **49 passed**; `uv run task lint` ->
  **passed**; `uv run python -m compileall -q scripts/run_full_suite.py
  tests/scripts/test_t29_harness.py` -> **passed**; `rtk git diff --check --`
  mapped files -> **clean**.
- Acceptance evidence: receipt exists before first child launch; partial
  artifacts and finalization exceptions retain six lanes and receipt errors;
  serialization failure retains run identity, integration return code, and
  sibling-stop reason; atomic receipt replacement preserves last durable
  snapshot; foreign resources remain untouched by existing focused contract.
- Boundary: no canonical `uv run task test`, review wrapper/agent docs, D05,
  F58/F58 R1-F02, taskipy entrypoint, lane topology, coverage/skips, ceiling,
  application code, DB reset, server, or host process operation changed/run.

## Review Findings

### Review R3
Scope audit: dossier/proposal/design/tasks/delta-spec `pass`; 8/8 tasks `pass`;
R1-F01 canonical-resource relevance and foreign preservation `pass`; R1-F02
foreign-resource propagation and owned-only cleanup `pass`; R2 receipt
persistence, six placeholders, atomic replacement, and `receipt_error` fallback
`pass` by source audit plus remediation focused evidence; vanished-child,
owned-survivor, bounded reap, interruption, first-failure/sibling-stop, partial
launch, timeout, six-lane topology, taskipy commands, coverage/no-cov flags,
retained skips, manifest/checksum reconciliation, and 300-second ceiling `pass`
by source/receipt audit; D05 read-only dependency and F58/F58 R1-F02 exclusion
`pass`; OpenSpec verification `pass`; canonical full-suite acceptance `finding`;
test-failure attribution `not assessable` for integration failure because sibling
stop truncated its traceback.

Preflight receipt: runtime receipt `/home/juca/github/omaha/reports/test-profile/20260820T181808-run.json`;
canonical inventory in receipt marks ports `8765-8768` and fixed test DB paths
`relevant=true`; host `8000`, `5443`, `4096`, and pytest-root observations remain
outside canonical inventory (`relevant=false`, preserved, not allowlisted,
adopted, or cleanup targets) per focused remediation evidence. Source audit
confirms six lane records are created and atomically persisted before first
`Popen`; focused remediation evidence reports 49 harness tests green.

Full suite: `/usr/bin/time -f 'elapsed_seconds=%e\\nexit_status=%x' -o /tmp/i08-r3-time.txt uv run task test`;
canonical command result **RED**, external wall-clock `202.20s`, runner receipt
elapsed `201.93612950699753s`, duration limit `300.0s`, `duration_exceeded=false`,
cleanup `clean`, `clean_children=true`, all launched lane process groups
`owned-cleaned`, residue `[]`, receipt errors `[]`, no host cleanup attempted.
Receipt records six lanes: unit `0` (515 passed, 2 skipped), integration `241`
(terminated sibling; log also contains `test_real_csv_flow.py::TestParseRealCsv::test_parse_real_csv_47_positions FAILED`),
audit `0` (40 passed), e2e `241` (sibling stop), bdd `1` (sibling stop), visual
`1` (5 failed, 3 passed). First-failure telemetry records visual with reason
`lane exited nonzero; fail-fast sibling stop`; sibling stop reason is recorded
for integration/e2e/bdd. Reconciliation is `ok=true`, 997 observed nodes,
expected skips preserved, no duplicate/missing/unexpected nodes. Visual log
provides five stable screenshot failures; integration traceback is absent after
cleanup-triggered sibling termination. Suite gate explicit verdict `BLOCKED`.

Verdict: BLOCKED

#### R3-F01 — Canonical full suite red; causal integration failure unknown
Status: blocked
Requirement/task: I08 task 4.1; delta Requirement `Test coverage report`,
Scenarios `Full task concurrently preserves complete coverage`, `Fail-fast
sibling stop is attributable`, and PRD §4.13; prior R1-F03/R2-F01.
Evidence: `/tmp/i08-r3-time.txt` records `elapsed_seconds=202.20` and
`exit_status=1`; runtime receipt `reports/test-profile/20260820T181808-run.json`
records final exit `1`, visual `5 failed`, and sibling exits 241. Visual log
lines 30-367 records screenshot-size and 23.7445%/26.5121% visual diffs;
integration log line 269 records `test_real_csv_flow.py::TestParseRealCsv::test_parse_real_csv_47_positions FAILED`
but no traceback before sibling cleanup. This is **Unknown** attribution for
integration and **Unknown/pre-existing or environmental** attribution for visual;
no I08 code path changes application visuals or CSV behavior, but receipt cannot
prove pre-existing status. E2E/BDD failures are sibling-stop consequences,
not independent failures.
Required change: owner decision required after diagnosing each red test from
isolated evidence; classify every failure as code bug, regression, test drift,
or environmental/pre-existing, then repair/revert/update only within authorized
scope. Do not mask, skip, delete, rerun blindly, reduce coverage, alter timeout,
or request third automatic I08 repair pass. A future review gate may approve
only with green canonical suite and complete causal receipt.
Acceptance: one owner-authorized follow-up establishes stable traceback/cause
for integration and visual failures, preserves six lanes/coverage/skips and
owned cleanup, and satisfies exactly one subsequent suite gate with green
result in <=300 seconds.

#### R3-F02 — Prior review acceptance remains blocked by red suite
Status: blocked
Requirement/task: R2-F01, R2-F02, I08 task 4.1; delta scenarios `Deadline
includes bounded cleanup` and `Full task concurrently preserves complete
coverage`.
Evidence: R3 receipt now proves pre-launch ledger persistence, six lane
placeholders, atomic lifecycle snapshots, `receipt_error` empty on successful
serialization, first-failure/sibling telemetry, elapsed-through-cleanup, clean
owned cleanup, and `duration_exceeded=false`; however test gate is red, so no
approval is permitted under PRD §4.13 and review zero-tolerance policy.
Required change: owner must resolve R3-F01 and obtain owner decision before any
third I08 repair; review must not issue another automatic remediation loop.
Excluded scope: no review-side code/test/doc edit, no D05/F58/F58 R1-F02
change, no archive/sync/commit/push, no host cleanup.
Acceptance: prior R1/R2 receipt findings remain source-verified, every red test
has classified cause, canonical suite is green in <=300 seconds, and no open
blocking finding remains.

### Execution Evidence — Owner-authorized surgical follow-up

- Pre-edit boundary: captured `rtk git diff HEAD~1 --stat` and full diff before
  editing. Existing worktree changes remain outside this follow-up: `.env.example`,
  `.opencode/agents/apply.md`, `.opencode/agents/review.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`, `AGENTIC_DEVELOPMENT.md`,
  `README.md`, current seed CSV edits, `openspec/roadmap.md`, F58 config/spec/
  connector files, `pyproject.toml`, `scripts/run_full_suite.py`,
  `src/omaha/config.py`, `tests/conftest.py`, `tests/scripts/test_t29_harness.py`,
  `tests/test_auth.py`, `tests/test_f57_myprofit_profile_config.py`, and
  `uv.lock`, plus pre-existing untracked D05/F58/I08 artifacts and connector
  test files. No pre-edit diff hunk touched `src/omaha/csv_import.py`,
  `tests/test_real_csv_flow.py`, or visual baselines.
- Changed files/symbols: `src/omaha/csv_import.py` — `_KNOWN_AVG_LABELS`
  receives only `avg_price`; `_KNOWN_CUR_LABELS` receives only `current_price`.
  `tests/test_real_csv_flow.py::TestParseRealCsv::test_parse_real_csv_47_positions`
  now asserts SMH qty `11`, avg `990.92`, current `2974.98`. Exactly five
  owner-approved baselines changed: `patrimonio-desktop`,
  `rebalance-form-desktop`, `rebalance-plan-desktop`, `import-form-desktop`,
  `import-review-desktop`. `rentabilidade-desktop` and `proventos-desktop`
  were generated by update mode but restored immediately; no other baseline
  remains changed.
- Bug evidence: before fix, target test parsed seed SMH as qty `11`, avg
  `990.92`, current `990.92`; canonical header inspection showed omitted
  snake_case aliases. After fix, parser returns current `2974.98` without
  changing normalization, fallback, heuristics, seed files/loaders, totals, or
  unrelated parser behavior.
- Focused validation: `uv run task test-file tests/test_real_csv_flow.py` ->
  **18 passed**; `uv run task test-file tests/test_csv_import.py` -> **46
  passed**; combined direct target/file run -> **47 passed, 1 initially failed
  before edit**; `git diff --check` -> **clean**.
- Baseline receipt: `UPDATE_VISUAL_BASELINES=1 uv run task test-visual` -> **8
  passed, 12 deselected**; update mode generated seven desktop files, then the
  two unapproved stub files were restored. `uv run task test-visual` -> **8
  passed, 12 deselected**. Exactly five named baseline files remain changed.
- Scope gate: no canonical `uv run task test`, CSS/template/snapshot-logic
  change, F58/D05/I08 runner change, production DB operation, real MyProfit
  access, commit, or push. Review-owned open findings remain **R3-F01** and
  **R3-F02** until one later canonical full-suite gate classifies them.

## Review Findings

### Review R4
Scope audit: proposal/design/tasks/delta-spec `pass`; 8/8 tasks `pass`; R1/R2
receipt persistence, race-tolerant signal/reap, owned-only cleanup, six-lane
ledger, fail-fast attribution, partial launch, timeout fields, taskipy
entrypoints, lane topology, coverage/skips, manifest reconciliation, and
300-second ceiling `pass` by source and canonical receipt audit; external CSV
alignment `pass` and outside I08 scope; external visual alignment `pass` and
outside I08 scope; D05 read-only dependency and F58/F58 R1-F02 exclusion `pass`;
OpenSpec validation `pass`; canonical suite result `finding`; failure
classification `finding` for one independent BDD failure and `pass` for two
fail-fast sibling terminations.

Full suite: `/usr/bin/time -f 'elapsed_seconds=%e\\nexit_status=%x' -o
/tmp/i08-final-review-time.txt uv run task test` -> **RED**, external wall-clock
238.65s, process cleanup complete; runner receipt
`reports/test-profile/20260820T191822-run.json` reports elapsed-through-cleanup
238.35944175599434s, duration limit 300.0s, `duration_exceeded=false`,
`deadline_triggered=false`, `clean_children=true`, cleanup verdict `clean`,
owned resources `owned-cleaned`, residue `[]`, and receipt errors `[]`.
Receipt contains all six lanes, expected skips, reconciliation `ok=true`, and
lane results unit 0 (515 passed, 2 skipped), audit 0 (40 passed), visual 0 (8
passed), BDD 1 (50 passed, 1 failed), integration 143 (fail-fast sibling), and
E2E 143 (fail-fast sibling). No host cleanup was attempted. Duration gate
passed; test gate failed. Explicit verdict `BLOCKED`.

External alignment audit: `src/omaha/csv_import.py:60-67` adds only
`avg_price`/`current_price` aliases; `tests/test_real_csv_flow.py:238-240`
asserts canonical SMH qty `11`, avg `990.92`, current `2974.98`. Durable
focused evidence records real CSV 18 passed and csv-import 46 passed. Exactly
five approved baselines remain changed: `patrimonio-desktop`,
`rebalance-form-desktop`, `rebalance-plan-desktop`, `import-form-desktop`, and
`import-review-desktop`; `rentabilidade-desktop` and `proventos-desktop` are
not changed. Durable visual evidence records 8 passed. These corrections match
R3 diagnosis, remain owner-authorized external suite alignment, and are not
absorbed into I08 requirements, tasks, or runner scope.

OpenSpec verification: `openspec validate
i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane --type change --strict
--json` -> valid, 1/1 passed, 0 issues; `openspec validate --specs --strict
--json` -> valid, 70/70 passed, 0 failures, informational long-requirement
notices only. D05 remains read-only and `Blocked`.

Verdict: BLOCKED

#### R4-F01 — Canonical suite remains red after external alignment
Status: blocked
Requirement/task: I08 task 4.1; delta Requirement `Test coverage report`;
Scenarios `Full task concurrently preserves complete coverage` and `Fail-fast
sibling stop is attributable`; PRD §4.13; prior R3-F01/R3-F02.
Evidence: `/tmp/i08-final-review-time.txt` records exit status 1 and 238.65s.
`reports/test-profile/20260820T191822-run.json` records first failure lane
`bdd`, code 1, and sibling exits 143. BDD log
`reports/test-profile/20260820T191822-bdd.log:127-134` identifies
`tests/bdd/test_scenarios.py::test_patch_per_asset_target[Ana]` failing with
Playwright `Page.goto: net::ERR_ABORTED` at `http://127.0.0.1:8766/` after
50 passed. Integration and E2E exit 143 are cleanup-triggered fail-fast sibling
terminations, not independent failures; receipt records their sibling reason
`fail-fast:bdd`. This is an **Unknown** BDD failure: traceback identifies a
server/navigation abort, but does not establish I08 runner bug, test drift,
regression, or environmental ownership. No red test may be approved.
Required change: owner decision required; classify and resolve the BDD
navigation failure (or establish environmental/pre-existing attribution) in
authorized follow-up, then request next gate only if owner chooses. Do not
issue third automatic I08 repair request; do not rerun this gate, mask/skip
tests, reduce coverage, alter timeout, or modify I08 review-side code.
Excluded scope: no host cleanup; no D05/F58/F58 R1-F02 edits; no absorption of
CSV or visual alignment into I08; no archive, sync, commit, or push.
Acceptance: one owner-authorized later gate has green `uv run task test`,
complete six-lane receipt, trusted cleanup, preserved skips/coverage, failure
classification, and external wall-clock <=300s.

## Review Findings

### Review R5
Scope audit: proposal/design/tasks/delta-spec `pass`; 8/8 tasks `pass`; R1-R4
receipt persistence, race-tolerant signal/reap, owned-only cleanup, six-lane
ledger, fail-fast attribution, partial launch, timeout fields, taskipy
entrypoints, lane topology, coverage/skips, manifest reconciliation, and
300-second ceiling `pass`; external CSV alignment `pass` and evidence-only,
outside I08 scope; external visual alignment `pass` and evidence-only, outside
I08 scope; BDD correction `pass` and outside I08 runner scope; D05 read-only
dependency and F58/F58 R1-F02 exclusion `pass`; OpenSpec verification `pass`;
full-suite acceptance `pass`; no blocking findings.

Full suite: `/usr/bin/time -f 'elapsed_seconds=%e\\nexit_status=%x' -o
/tmp/i08-r5-review-time.txt uv run task test` -> **GREEN**, external wall-clock
`240.60s`, exit status `0`; duration limit `300.0s`; runner receipt
`reports/test-profile/20260820T194321-run.json` reports elapsed-through-cleanup
`240.37117566200322s`, `duration_exceeded=false`, `deadline_triggered=false`,
`final_exit_code=0`, cleanup verdict `clean`, `owned_only=true`, residue `[]`,
and `receipt_errors=[]`. All six lanes completed with return code 0 and
`owned-cleaned` cleanup: unit 515 passed/2 skipped, integration 390 passed,
audit 40 passed, E2E 51 passed, BDD 51 passed, visual 8 passed. Reconciliation
`ok=true`; expected two Docker skips preserved; no missing/duplicate/unexpected
nodes; no host cleanup attempted. Test gate passed; duration gate passed.

I08/external correction audit: `src/omaha/csv_import.py` adds only
`avg_price`/`current_price` aliases; real-CSV assertion and exactly five
owner-authorized desktop baselines align with prior R3 diagnosis and remain
external evidence, not I08 requirements/tasks/runner scope. In
`tests/bdd/step_defs/_workflows.py`, exactly one redundant `page.goto` was
removed from `add_one_asset`; POST-201 assertion and dashboard row wait remain
present (`:180-188`). No I08 runner/taskipy/harness topology expansion found.

OpenSpec verification: `openspec validate
i08-corrigir-runner-taskipy-cleanup-e-telemetria-por-lane --type change --strict
--json` -> valid, 1/1 passed, 0 issues; `openspec validate --specs --strict
--json` -> valid, 70/70 passed, 0 failures; informational long-requirement
notices only. D05 remains read-only and `Blocked`.

Verdict: APPROVED

Findings: none. R4-F01 resolved by owner-authorized BDD correction and this
single green canonical receipt. No third remediation pass requested.
