## 0. Owner-authorized acceptance amendment

- [x] 0.1 Bind canonical population acceptance to `tests/AUDIT.md` and the
  existing `scripts/run_full_suite.py::load_manifest` / `EXPECTED_SKIPS`
  contract. Preserve direct `uv run pytest` child mapping, six lanes, all prior
  execution evidence, and every exclusion. Acceptance: dossier states the
  calculation `len(current AUDIT blocking node-ID set) = 1,032`; excludes the
  12 explicitly outside-lane T32 cases; names exact node checksum/lane
  membership source; and names only these two expected skips:
  `tests/test_dockerfile.py::test_docker_build_pro_image_succeeds` and
  `tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user`.
  Any source conflict is recorded exactly and blocks implementation; no count
  is invented. Test strategy: artifact/static contract audit only; no test
  files are added, deleted, or edited. Test files/scenarios:
  `tests/AUDIT.md` summary/checksum and `tests/PERFORMANCE.md` skip-ID evidence.
  Focused command: `openspec validate i10-substituir-taskipy-no-boundary-da-suite-canonica --type change --strict --json`.
  Independent oracle: exact grep finds no obsolete population requirement and
  finds 1,032 blocking nodes, 12 outside-lane cases, and the exact two skip IDs.

## 1. Direct lane command boundary

- [x] 1.1 Inspect `pyproject.toml:[tool.taskipy.tasks]` entries `test-unit`,
  `test-integration`, `test-audit-integration`, `test-e2e`, `test-bdd`, and
  `test-visual` against the mapping in `design.md`. Preserve every path,
  marker, ignore, coverage/XML, `--no-cov`, verbosity, and visual-selection
  flag. Acceptance: mapping is exact; if any current task cannot be represented
  without semantic drift, stop with `BLOCKED_FOR_IMPLEMENTATION_BRIEF` and name
  task plus mismatched argv. Test file/scenario: none; source inspection only.
  Focused taskipy command: `uv run task test-one tests/scripts/test_t29_harness.py -k "runtime_child_command"` (after mapping implementation). Independent oracle: `git diff -- pyproject.toml` is empty unless exact mapping evidence names a necessary line.

- [x] 1.2 Update `scripts/run_full_suite.py::_runtime_child_command` and its
  lane/task mapping to emit the six direct `uv run pytest` argv vectors from
  `design.md`, then append unchanged `-s`, `-p test_profile_plugin`, and
  governance `--deselect` pairs. Keep `LANES`, order, six concurrent launches,
  `_lane_environment`, `start_new_session=True`, process-group lifecycle,
  receipts, DB validation, reconciliation, fail-fast, and 300-second logic
  unchanged. Acceptance: every canonical child command contains no
  `uv run task <lane>` wrapper and exact vector equality passes for all six
  lanes; non-canonical Taskipy tasks are untouched. Test file/scenario:
  `tests/scripts/test_t29_harness.py` command-vector and lane-topology cases.
  Focused taskipy command: `uv run task test-one tests/scripts/test_t29_harness.py -k "runtime_child_command or lane"`. Independent oracle: static diff shows only direct command construction plus required command evidence; `LANES`, `LANE_PORTS`, `LANE_DATABASES`, and lifecycle symbols retain topology and behavior.

- [x] 1.3 Preserve or minimally extend `_lane_metadata` receipt command
  evidence so lane/task identity remains compatible and any exact child
  command recorded is truthful. Do not alter ownership mappings, PID/PGID
  fields, timestamps, signal status, cleanup verdicts, DB receipts, or
  reconciliation fields. Acceptance: six placeholder records still persist
  before launch and final JSON reports direct command identity without
  replacing existing lifecycle telemetry. Test file/scenario:
  `tests/scripts/test_t29_harness.py` partial-launch, placeholder, and final
  receipt scenarios. Focused taskipy command: `uv run task test-one tests/scripts/test_t29_harness.py -k "receipt or placeholder or partial_launch"`. Independent oracle: receipt has six lanes, explicit nulls for unlaunched identities, unchanged ownership/resource keys, and no missing evidence treated as success.

## 2. Focused contract and policy updates

- [x] 2.1 Update `tests/scripts/test_t29_harness.py` and
  `scripts/test_t29_receipt_harness.py` only where existing assertions assume
  Taskipy wrapper positions. Add exact six-lane command-vector assertions and
  retain lifecycle, fail-fast, vanished-child, coverage, skip, DB, temp-root,
  and receipt tests. Preserve markers and do not add retry, skip, xfail, or
  lane reduction. Acceptance: tests prove direct vectors, plugin/output
  visibility, dynamic environment, and unchanged lane lifecycle semantics.
  Test files/scenarios: both named focused harness files. Focused taskipy
  command: `uv run task test-file tests/scripts/test_t29_harness.py` and
  `PYTHONPATH=. uv run task test-file scripts/test_t29_receipt_harness.py`.
  Independent oracle: `git diff -- tests/scripts/test_t29_harness.py scripts/test_t29_receipt_harness.py` contains assertion adaptation only; no test selection is weakened.

- [x] 2.2 Update `openspec/PRD.md` §4.8, `openspec/specs/dev-tasks/spec.md`
  delta target, and only contradictory Taskipy summary wording in `AGENTS.md`.
  State exact exception: existing Python supervisor entered by `uv run task
  test` may launch only six mapped pytest children directly; serve, DB, lint,
  coverage, focused tests, and all other shortcuts remain Taskipy. Acceptance:
  policy/spec text is narrow, names no generic raw-command permission, and
  stable requirement retains process ownership, receipts, cleanup, coverage,
  skips, DB safety, fail-fast, and <=300s clauses. Test file/scenario: policy
  text audit plus existing `tests/scripts/test_t29_harness.py` lane-policy
  scenario. Focused taskipy command: `uv run task test-one tests/scripts/test_t29_harness.py -k "lane"`. Independent oracle: `openspec validate --specs --strict --json` and `git diff --check`; only I10 policy files differ.

## 3. Focused verification and parity audit

- [x] 3.1 Run focused runner verification after implementation with the full
  `tests/scripts/test_t29_harness.py` module and direct receipt harness. Verify
  command parity, six-lane topology, fail-fast causal result, process-group
  ownership, interruption/deadline behavior, coverage/skips, dynamic/fixed DB
  isolation, temp-root reconciliation, and foreign-resource preservation.
  Acceptance: both focused targets pass with no added skip/xfail/retry and
  direct mapping tests are green. Test files/scenarios:
  `tests/scripts/test_t29_harness.py`, `scripts/test_t29_receipt_harness.py`.
  Focused taskipy command: `uv run task test-file tests/scripts/test_t29_harness.py` and `PYTHONPATH=. uv run task test-file scripts/test_t29_receipt_harness.py`. Independent oracle: `git diff --check`; focused receipts show six placeholders, owned process groups, exact DB/temp evidence, and unchanged exit precedence.

- [x] 3.2 Run unaffected canonical task lanes separately before review to prove
  Taskipy remains usable outside supervisor child dispatch: unit and
  integration focused lanes plus one canonical lane selected by existing task
  entrypoint. Preserve their existing DB/coverage/browser semantics. Acceptance:
  `test-unit`, `test-integration`, and one selected lane exit zero; no
  `pyproject.toml` task command changed. Test files/scenarios: current unit,
  integration, and selected lane suites. Focused taskipy command: `uv run task test-unit`; `uv run task test-integration`; `uv run task test-visual`. Independent oracle: command logs show each standalone taskipy task executed its existing definition, expected coverage/no-coverage behavior, and no production DB target.

- [x] 3.3 Audit changed-file scope before review. Preserve exclusions: no
  Taskipy removal for serve/DB/lint/focused tasks, no product/MyProfit/F58,
  T33, I08, dependency, DB data, migration, seed, retry, skip/xfail, lane
  removal/serialization, or broad cleanup changes. Acceptance: only runner,
  required focused assertions, listed policy/spec docs, and I10 artifacts are
  changed; `pyproject.toml` is unchanged unless task mapping proof requires
  it. Test file/scenario: changed-file and command audit. Focused taskipy
  command: `uv run task test-one tests/scripts/test_t29_harness.py -k "runtime_child_command or lane"`. Independent oracle: `git status --short`, `git diff --stat`, and exact grep proving no canonical child command contains `uv run task`.

## 4. Review-owned canonical acceptance

- [ ] 4.1 Reactivation-only canonical acceptance: while the owner-authorized
  `maintenance-suspended` state is active, review MUST NOT run `uv run task
  test`; it records `NOT RUN — maintenance-suspended` and does not block an
  otherwise eligible change. After exact diagnosis resolves concurrent dynamic
  SQLite readonly-DB and BDD browser-timeout failures, review runs exactly one
  isolated canonical `uv run task test`. Acceptance evidence: six lanes launch
  in parallel and exit green; direct child vectors have no Taskipy lane
  wrapper; fail-fast and signal semantics remain available; coverage, current
  `tests/AUDIT.md` 1,032-node blocking manifest/checksum and lane
  reconciliation pass; 12 outside-lane T32 cases remain excluded; receipt
  reports exactly the two Docker skip IDs; DB/temp ownership cleanup is trusted;
  no foreign/unknown residue is touched; elapsed wall-clock through cleanup is
  <=300s. Test file/scenario: canonical six-lane receipt only after
  reactivation. Focused taskipy command: `uv run task test` exactly once,
  review-only and reactivation-only. Independent oracle: policy receipt says
  suspended before trigger, then one green same-run receipt plus bounded
  postflight; any red lane, missing evidence, mismatch, untrusted cleanup, or
  duration over 300s blocks reactivation.

- [x] 4.2 Perform final I10 artifact/spec validation after canonical review
  evidence when gate active; while this owner amendment is suspended, validate
  policy receipt instead. Do not archive, commit, push, or alter T34/F58
  lifecycle. Acceptance: exact change validates strictly, stable specs validate,
  task checklist and any canonical receipt are complete or explicitly
  `NOT RUN — maintenance-suspended`, and no unrelated files changed. Test
  file/scenario: OpenSpec validation and mapped diff audit. Focused taskipy
  command: `uv run task test-one tests/scripts/test_t29_harness.py -k
  "runtime_child_command or lane"` only if focused smoke is needed; never run
  another full suite during suspension. Independent oracle: `openspec validate
  i10-substituir-taskipy-no-boundary-da-suite-canonica --type change --strict
  --json`, `openspec validate --specs --strict --json`, and `git status --short`.

## 5. Owner-authorized maintenance-gate amendment

- [x] 5.1 Update `openspec/PRD.md` §4.13 and the mirrored policy text in
  `AGENTS.md` and `AGENTIC_DEVELOPMENT.md`. Preserve `task test`, all six
  individual commands, product behavior test requirements, no-test-deletion /
  no-skip / no-xfail / no-retry / no-lane-change / no-coverage-reduction rules,
  and the `<=300s` contract when active. Add exact state
  `maintenance-suspended`, affected gate `parallel canonical uv run task test`
  as apply/review/pre-push requirement, and ordered reactivation trigger.
  Acceptance: docs explicitly say product work may proceed on applicable green
  focused evidence, T34 may continue bounded work, F58 remains Blocked, and no
  wording disables or removes any test command. Test file/scenario: policy text
  audit. Focused taskipy command: N/A — policy-only, no product behavior
  changed. Independent oracle: exact text search plus `git diff --check`.

- [x] 5.2 Update `.opencode/agents/apply.md` and `.opencode/agents/review.md`
  with conditional gate behavior. Apply SHALL run applicable focused command(s),
  report exact result, and block red product tests. Review SHALL audit scope,
  product-test coverage, focused evidence, and suspension visibility; it SHALL
  record `NOT RUN — maintenance-suspended` and not launch `uv run task test`
  while suspension is active. Acceptance: canonical suite is conditional only
  after trigger; no routine apply full suite, review retry, test masking, or
  changed cleanup protocol is introduced. Test file/scenario: agent-policy
  static audit. Focused taskipy command: N/A — policy-only. Independent oracle:
  exact command/state audit and `git diff --check`.

- [x] 5.3 Add owner-authorized deltas for `agent-test-performance-gate` and
  `test-suite-quality`; amend `dev-tasks` delta without weakening its direct
  six-lane/task-defined command contract. Preserve every test, lane, marker,
  skip, xfail, coverage, DB-safety, receipt, cleanup, and `task test` command.
  Acceptance: each delta states focused delivery, mandatory product behavior
  tests, non-blocking suspension, exact reactivation diagnosis pair, and one
  green isolated canonical run `<=300s`; no delta authorizes deletion or
  disablement. Test file/scenario: OpenSpec delta scenarios. Focused taskipy
  command: N/A — spec-only. Independent oracle: strict exact-change and stable-
  spec validation.

- [x] 5.4 Add explicit `maintenance-suspended` status and reactivation trigger
  to `openspec/config.yaml` without removing existing quality-gate keys. Amend
  I10 `proposal.md`, `design.md`, and this `tasks.md` with code map, current
  policy flow, decisions, change map, risks, executable evidence, and T34/F58
  lifecycle impact. Update only I10's roadmap status/notes to `Spec Proposed`;
  leave T34 `Applying`, F58 `Blocked`, T33 archived, and I08 blocked unchanged.
  Acceptance: config and dossier have one identical suspension state and
  trigger; implementation files are policy/docs/config only; no product/test/
  runner/DB/process/cleanup edits are requested. Test file/scenario: mapped
  artifact audit. Focused taskipy command: N/A — dossier/config-only.
  Independent oracle: `git status --short`, `git diff --stat`, and exact changed-
  file allowlist.

- [x] 5.5 Validate amendment before implementation handoff. Run exact change
  validation, stable-spec validation, YAML/Markdown whitespace checks, and
  audit focused-policy wording. Do not run `uv run task test`, any lane, browser,
  server, DB, cleanup, archive, commit, or push during proposal/apply of this
  policy amendment. Acceptance: change and stable specs validate, focused policy
  is explicit, no canonical full-suite receipt is falsely claimed, and all
  individual Taskipy commands remain named. Test file/scenario: OpenSpec
  validation only. Focused taskipy command: N/A — full suite is explicitly
  suspended and this slice changes no product behavior. Independent oracle:
  `openspec validate i10-substituir-taskipy-no-boundary-da-suite-canonica
  --type change --strict --json`, `openspec validate --specs --strict --json`,
  `git diff --check`, and `git status --short`.

## Execution Evidence

### Pre-edit boundary

- Before first edit, `git diff HEAD~1` was captured. It includes pre-existing
  work across `.opencode/`, `AGENTIC_DEVELOPMENT.md`, README, archived D05/I08
  artifacts, roadmap/spec updates, MyProfit/F57 files, `pyproject.toml`,
  `scripts/run_full_suite.py`, test support, visual baselines, and `uv.lock`.
- `git status --short` before this slice showed pre-existing modifications in
  `.env.example`, README, roadmap, stable specs, `pyproject.toml`, runner,
  application/test support, visual baselines, and `uv.lock`, plus untracked F58,
  I10, T34, MyProfit, and connector files. Those boundaries are not owned by
  I10. `pyproject.toml` lane definitions remain unchanged; its existing
  dependency diff is pre-existing.
- I10-owned changes are limited to direct lane command construction and receipt
  identity in `scripts/run_full_suite.py`, command/lane assertions in the two
  named harness files, narrow policy wording in `openspec/PRD.md`, stable and
  delta `dev-tasks` specs, `AGENTS.md`, and this dossier.
- Amendment-owned changes are policy/docs/config only: `AGENTS.md`,
  `AGENTIC_DEVELOPMENT.md`, `.opencode/agents/apply.md`,
  `.opencode/agents/review.md`, `openspec/PRD.md`, `openspec/config.yaml`,
  three I10 delta specs, I10 artifacts, and the I10 roadmap status/notes.
  Runtime runner, product, test content, task definitions, DB, process,
  cleanup, T34, F58, T33, and I08 remain excluded.

### Initial apply validation ledger registration

Run owner: `i10-substituir-taskipy-no-boundary-da-suite-canonica / apply-initial / apply`.
Owner evidence recorded before resource use at `2026-08-21T17:42:25-03:00`.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| command process | `i10-apply-r1-mapping` | apply-initial | run id registered in this receipt before launch | 2026-08-21T17:42:25-03:00 | 2026-08-21T17:43:30-03:00 | exited | owned-cleaned | mapping command and two diagnostic invocations exited; no child residue | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-mapping` | apply-initial | unique run path registered before creation | 2026-08-21T17:42:25-03:00 | 2026-08-21T17:43:30-03:00 | absent | absent | exact path absent at cleanup check | idempotent no-op |
| command process | `i10-apply-r1-runner` | apply-initial | run id registered in this receipt before launch | 2026-08-21T17:42:25-03:00 | 2026-08-21T17:45:00-03:00 | exited | owned-cleaned | first full harness attempt externally timed out; process absent at cleanup check | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-runner` | apply-initial | unique run path registered before creation | 2026-08-21T17:42:25-03:00 | 2026-08-21T17:45:00-03:00 | absent | owned-cleaned | exact path removed after failed attempt | exact bounded removal |
| command process | `i10-apply-r1-debug-partial-launch` | apply-initial | debug run id registered before launch after first focused failure | 2026-08-21T17:44:00-03:00 | 2026-08-21T17:45:00-03:00 | exited | owned-cleaned | isolated partial-launch node diagnosed helper task/lane mismatch | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-debug-partial-launch` | apply-initial | unique debug path registered before creation | 2026-08-21T17:44:00-03:00 | 2026-08-21T17:45:00-03:00 | absent | owned-cleaned | exact path removed after receipt inspection | exact bounded removal |
| command process | `i10-apply-r1-runner-fixed` | apply-initial | fixed-run id registered before launch after test diagnosis | 2026-08-21T17:49:00-03:00 | 2026-08-21T17:49:30-03:00 | exited | owned-cleaned | partial-launch node and full 65-node runner harness passed | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-runner-fixed` | apply-initial | unique fixed-run path registered before creation | 2026-08-21T17:49:00-03:00 | 2026-08-21T17:49:30-03:00 | absent | owned-cleaned | exact path removed after passing run | exact bounded removal |
| command process | `i10-apply-r1-receipt` | apply-initial | receipt run id registered before launch | 2026-08-21T17:49:30-03:00 | 2026-08-21T17:50:30-03:00 | exited | owned-cleaned | direct receipt harness 8 passed | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-receipt` | apply-initial | unique receipt path registered before creation | 2026-08-21T17:49:30-03:00 | 2026-08-21T17:50:30-03:00 | absent | owned-cleaned | exact path removed after passing run | exact bounded removal |
| command process | `i10-apply-r1-standalone-lanes` | apply-initial | standalone run id registered before launch | 2026-08-21T17:50:32-03:00 | 2026-08-21T17:53:30-03:00 | exited | owned-cleaned | unit passed; first integration attempt hit external 120s tool bound and was diagnosed | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-standalone-lanes` | apply-initial | unique standalone path registered before creation | 2026-08-21T17:50:32-03:00 | 2026-08-21T17:53:30-03:00 | absent | owned-cleaned | exact path removed after bounded cleanup | exact bounded removal |
| test DB resource | `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, `data/test_visual.db` | apply-initial | preflight observed existing test-only paths; no ownership adoption | 2026-08-21T17:50:32-03:00 | 2026-08-21T17:58:05-03:00 | absent | pre-existing | existing test DB files; production DB excluded; no cleanup attempted | preserved; no-op |
| command process | `i10-apply-r1-integration-complete` | apply-initial | bounded timeout diagnosis run registered before launch | 2026-08-21T17:53:51-03:00 | 2026-08-21T17:56:05-03:00 | exited | owned-cleaned | unchanged integration Taskipy lane: 390 passed, 698 deselected, 130.56s | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-integration-complete` | apply-initial | unique integration retry path registered before creation | 2026-08-21T17:53:51-03:00 | 2026-08-21T17:56:05-03:00 | absent | owned-cleaned | exact path removed after passing run | exact bounded removal |
| command process | `i10-apply-r1-visual` | apply-initial | visual lane run id registered before launch | 2026-08-21T17:56:21-03:00 | 2026-08-21T17:57:30-03:00 | exited | owned-cleaned | unchanged visual Taskipy lane: 8 passed, 12 deselected, 47.17s | no-op; no process resource remained |
| temporary path | `/tmp/opencode/i10-apply-r1-visual` | apply-initial | unique visual path registered before creation | 2026-08-21T17:56:21-03:00 | 2026-08-21T17:57:30-03:00 | absent | owned-cleaned | exact path removed after passing run | exact bounded removal |

### Validation results

- Mapping source audit: `pyproject.toml` unchanged; `shlex.split` equality
  passed for all six task definitions against `DIRECT_LANE_COMMANDS`.
- Direct mapping: `uv run task test-one tests/scripts/test_t29_harness.py::test_runtime_child_command_maps_exact_task_definition` -> 6 passed.
- The dossier's `test-one ... -k "runtime_child_command"` form selected zero
  nodes because Taskipy's `test-one` shortcut accepts one positional node;
  exact node invocation above supplied same focused oracle without changing
  selection.
- Runner harness: `uv run task test-file tests/scripts/test_t29_harness.py` -> 65 passed.
- Receipt harness: `PYTHONPATH=. uv run task test-file scripts/test_t29_receipt_harness.py` -> 8 passed.
- Standalone Taskipy lanes: `uv run task test-unit` -> 574 passed, 2 skipped,
  501 deselected; `uv run task test-integration` -> 390 passed, 698 deselected;
  `uv run task test-visual` -> 8 passed, 12 deselected. First integration attempt
  hit external validation-tool 120-second bound at 98% without assertion
  failure; diagnosis rerun with same task and bounded 300-second tool window
  passed in 130.56s. No task timeout or lane semantics changed.
- First runner-harness attempt exposed test-double mismatch: adapted helper
  compared lane name with logical task failure selector, so it launched all
  doubles until tool timeout. Fixed assertion-only test mapping to compare task
  selector; focused node then passed and full harness passed. No production
  runner lifecycle code changed for this diagnosis.
- Static/policy checks: `uv run ruff check ...` passed; `rtk git diff --check`
  passed; direct parity/no-wrapper Python audit passed; `openspec validate
  i10-substituir-taskipy-no-boundary-da-suite-canonica --type change --strict
  --json` passed; `openspec validate --specs --strict --json` passed all 70
  specs (informational long-text notices only).
- No canonical full-suite command ran. Review owns exactly one `uv run task test`.

### Acceptance evidence

- Six `LANES` names/order and concurrent supervisor lifecycle unchanged.
- Direct child vectors preserve task-defined markers, paths, ignores, coverage,
  XML, `--no-cov`, visual `not t32_pruned`, `-vv`, `-s`, plugin, and dynamic
  deselection suffix.
- Receipt command identity is direct argv; logical task identity, six
  placeholders, process groups, DB/temp mappings, fail-fast, cleanup, and
  reconciliation fields remain present.
- `pyproject.toml`, serve, DB, lint, coverage, focused tasks, dependencies,
  product code, DB data, migrations, seeds, I08/T33 artifacts unchanged by I10.
- Exact current-run temp paths were cleaned or recorded absent. Pre-existing
  test DB files and unrelated host resources were preserved; no foreign action,
  broad process kill, port cleanup, production DB access, or live MyProfit run.

No canonical full-suite command is registered or run by apply. Review owns
exactly one `uv run task test` execution only after gate reactivation; while
`maintenance-suspended`, review records `NOT RUN — maintenance-suspended`.

### Maintenance-gate amendment apply pass — 2026-08-22

- Pre-edit boundary: `rtk git diff HEAD~1 --` was captured before this pass.
  Existing owner-amendment policy/docs/config edits were limited to the approved
  I10 paths: `openspec/PRD.md`, `AGENTS.md`, `AGENTIC_DEVELOPMENT.md`,
  `.opencode/agents/apply.md`, `.opencode/agents/review.md`,
  `openspec/config.yaml`, and the I10 dossier/deltas. Runtime runner, product,
  test content, task definitions, DB/seed, process/cleanup behavior, T34, F58,
  T33, and I08 remained outside this pass.
- Preflight symbol audit: PRD §4.13, agent workflow/test-gate sections, config
  `openspec_roadmap.quality_gate.canonical_full_suite_gate`, and all three I10
  delta scenarios agree on `maintenance-suspended`; focused/product tests stay
  mandatory; `uv run task test` and individual lane commands remain available;
  review receipt is `NOT RUN — maintenance-suspended`; reactivation is ordered
  diagnosis of concurrent dynamic SQLite readonly-DB and BDD browser timeout,
  then one isolated green six-lane run through cleanup in `<=300s`.
- Tasks 5.1–5.4 completed by policy/static audit. No runtime or test-content
  implementation was added. Roadmap remains `I10: Applying` per owner handoff;
  no roadmap lifecycle edit was made.

### Maintenance-gate validation ledger registration

Run owner: `i10-substituir-taskipy-no-boundary-da-suite-canonica / apply-policy-validation / apply`.
Owner evidence recorded before validation launch at
`2026-08-22T01:23:24-03:00`: current handoff authorizes policy/docs/config-only
validation and forbids canonical suite, lanes, browser, server, DB, cleanup,
archive, commit, and push.

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| validation process batch | `i10-maintenance-policy-validation-20260822T012324-0300` | apply-policy-validation | run id and exact command batch registered before launch | `2026-08-22T01:23:24-03:00` | `2026-08-22T01:24:12-03:00` | exited | owned-cleaned | validation stopped before OpenSpec commands because `python` executable was unavailable; no test runner command or other resource launched | no-op; shell exited and no process/resource residue remained |
| validation process batch | `i10-maintenance-policy-validation-uv-20260822T012412-0300` | apply-policy-validation | second run id registered after bounded diagnosis; exact `uv run python` batch authorized before launch | `2026-08-22T01:24:12-03:00` | `2026-08-22T01:25:18-03:00` | exited | owned-cleaned | static assertion found missing explicit `test-audit-integration` command name; no OpenSpec command or test runner launched | no-op; shell exited and no process/resource residue remained |
| validation process batch | `i10-maintenance-policy-validation-uv-20260822T012518-0300` | apply-policy-validation | third run id and corrected policy assertion batch registered before launch | `2026-08-22T01:25:18-03:00` | `2026-08-22T01:25:50-03:00` | exited | owned-cleaned | focused policy consistency PASS; strict change validation 1/1 PASS; strict stable-spec validation 70/70 PASS with informational long-text notices; `git diff --check` PASS; no canonical suite/lane/browser/server/DB command | no-op; bounded validation processes exited and no process/resource residue remained |
| validation process batch | `i10-maintenance-policy-validation-final-20260822T012715-0300` | apply-policy-validation | final run id registered before relaunch after documentation/dossier evidence edits | `2026-08-22T01:27:15-03:00` | `2026-08-22T01:27:50-03:00` | exited | owned-cleaned | final focused policy consistency PASS; strict change validation 1/1 PASS; strict stable-spec validation 70/70 PASS with informational long-text notices; `git diff --check` PASS; no canonical suite/lane/browser/server/DB command | no-op; bounded validation processes exited and no process/resource residue remained |

### Maintenance-gate validation result

- Focused policy check: `uv run python` YAML/policy consistency assertions ->
  **PASS**. Confirmed config status, canonical command, all six individual
  commands, affected boundary, mandatory focused policy, ordered diagnosis pair,
  `<=300s` trigger, and prohibited suppression actions. Confirmed all approved
  policy/delta files carry `maintenance-suspended`; PRD, review policy, and
  performance delta carry exact `NOT RUN — maintenance-suspended` receipt text.
- OpenSpec change validation: `openspec validate
  i10-substituir-taskipy-no-boundary-da-suite-canonica --type change --strict
  --json` -> **PASS**, 1/1.
- Stable spec validation: `openspec validate --specs --strict --json` ->
  **PASS**, 70/70. Existing informational long-text notices only; no failures.
- Whitespace validation: `git diff --check` -> **PASS**.
- Canonical suite: **not run**. No `uv run task test`, individual lane, browser,
  server, DB, cleanup, archive, commit, or push command was launched. Review
  receipt requirement remains exact `NOT RUN — maintenance-suspended` while
  owner-authorized suspension is active.
- No-test-removal confirmation: no test file/content, marker, skip, xfail,
  retry, lane, coverage, task definition, runner, product, DB/seed, process, or
  cleanup behavior changed in this maintenance-gate pass.

## Review Findings

### Review R1
Scope audit: requirements/spec scenarios `pass` by static audit; task/design
mapping and direct command identity `pass`; six-lane topology, process-group
lifecycle, fail-fast, receipts, coverage/skips, manifest reconciliation, and
cleanup behavior `not assessable` because trusted runner preflight blocked before
launch; policy alignment `pass`; changed-file scope `pass` against apply's
declared pre-edit boundary (working tree also contains unrelated pre-existing
changes); OpenSpec change validation `pass`; stable specs validation `pass`.

Full suite: `uv run task test` -> NOT RUN; trusted isolated-runner precondition
failed before launch; elapsed N/A; duration limit 300 seconds; cleanup N/A (no
suite resources created). Canonical command was not attempted, so six lane
results are `unit=N/A, integration=N/A, audit=N/A, e2e=N/A, bdd=N/A,
visual=N/A`; coverage N/A; tests/skips N/A; manifest/checksum N/A; fail-fast
disposition N/A; <=300s classification N/A.

Preflight: ledger `review-r1-1787346140`, 2026-08-21 18:02:20 -0300 to
18:02:20 -0300. Ledger fields inspected: `resource_kind`, `resource_id`,
`owner`, `owner_evidence`, `started_at`, `ended_at`, `status`,
`classification`, `evidence`, `cleanup_result`. Canonical lane ports 8765,
8766, 8767, 8768 classified `absent`. Fixed test DB resources
`data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, and
`data/test_visual.db` classified `pre-existing`: exact paths existed, with no
current-run ownership evidence. `reports/test-profile` also pre-existed and
was preserved. No process, port, DB, path, or report resource was adopted,
deleted, freed, killed, or masked. Decision: BLOCKED before suite launch.

Postflight: 2026-08-21 18:03:01 -0300. Bounded canonical inventory repeated;
ports remained `absent`; four fixed test DB paths remained `pre-existing`;
no suite process, child PGID, log, timing, temp root, or cleanup resource was
created. Cleanup result: no cleanup attempted. No current-run residue exists;
pre-existing DB resources remain preserved. Decision: BLOCKED; no restoration
required.

Runner isolation: failed isolated-runner precondition. Relevant fixed test DB
resources had no trusted current-run owner evidence. No foreign-resource,
baseline, or allowlist exception was used. LAN receipt: canonical suite lane
ports 8765-8768 had no listeners; LAN service port 8000 was not touched because
suite does not claim it. No service stop or restoration performed.

Direct-command receipt: static audit of `scripts/run_full_suite.py:41-76,
209-217` and `pyproject.toml:236-245` shows six exact `uv run pytest` vectors,
with no `uv run task` lane wrapper; dynamic `-s`, plugin, and deselection suffix
remain at `scripts/run_full_suite.py:209-217`. Apply focused evidence records
65 runner-harness passes, 8 receipt-harness passes, and standalone lane results
574 unit passes/2 skips, 390 integration passes, and 8 visual passes. These are
apply receipts only, not canonical-suite evidence.

Policy alignment: `openspec/PRD.md:427-444`,
`openspec/specs/dev-tasks/spec.md:57-70`, and `AGENTS.md:226` describe narrow
supervisor-only exception; noncanonical Taskipy entrypoints remain required.
`openspec validate i10-substituir-taskipy-no-boundary-da-suite-canonica
--type change --strict --json` passed; `openspec validate --specs --strict
--json` passed all 70 specs (informational long-text notices only). `git diff
--check` passed. `pyproject.toml` has pre-existing dependency changes recorded
by apply boundary evidence; no I10 task-definition edit was attributed.

Verdict: BLOCKED

#### R1-F01 — Trusted isolated runner unavailable
Status: blocked
Requirement/task: `dev-tasks` requirement on ownership-safe preflight and task
4.1 canonical acceptance (`tasks.md:90-99`).
Evidence: review ledger `review-r1-1787346140` found existing fixed test DBs at
`data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, and
`data/test_visual.db` without current-run owner evidence. Their presence is
explicitly recorded in apply evidence at `tasks.md:146`, and no ownership
adoption is permitted. Preflight therefore blocked before `uv run task test`;
no canonical suite result exists.
Required change: provide isolated review runner/environment with no relevant
pre-existing, foreign, unknown, contradictory, or incomplete lane resource
state, and a per-run ownership ledger proving exact process/PGID, port, DB,
log, timing, temp, and cleanup ownership before launch. Then perform the one
canonical `uv run task test` attempt and record full six-lane receipt. Excluded:
no host cleanup, DB deletion/reset, process kill, port freeing, code change,
retry, or second suite attempt in this review.
Acceptance: trusted preflight classifies every relevant resource as `absent` or
`owned-current-run`; one canonical run launches six lanes in parallel with
direct child vectors, emits green lane/coverage/skips/manifest/receipt evidence,
reconciles cleanup to `absent` or `owned-cleaned`, and completes through cleanup
within 300 seconds.

### Review R2
Scope audit: requirements and delta scenarios `pass` by dossier/spec/static audit; direct command vectors and Taskipy boundary `pass`; design decisions and changed symbols `pass`; six-lane topology, parallel launch, fail-fast, process-group signaling, DB/temp isolation, receipts, coverage/skips, manifest reconciliation, and cleanup `finding` because canonical receipt was not green or trusted; policy alignment `pass`; excluded product/F58/MyProfit/I08/T33, dependency, retry, skip/xfail, and lane-topology scope `pass` against declared pre-edit boundary; changed-file audit `pass` for I10-owned paths with unrelated working-tree edits preserved; LAN/production DB safety `pass`; final OpenSpec validation `pass`.

Exact DB cleanup proof: owner authorization was supplied in review request. Before deletion, exact metadata was captured for `data/test_e2e.db` (126976 bytes, inode 26614, sha256 `2ce005a97d4499eb503a1c0bc51870ae1aeaae9803b7e34268bc8ac523d83015`), `data/test_e2e_short_ttl.db` (126976 bytes, inode 562169, sha256 `9a952eca9f22dd23b87846704eae31bca95483403f54d131b121c443e02d52aa`), `data/test_bdd.db` (126976 bytes, inode 34581, sha256 `934c418c2685510aaaf5b3783229612a69cbe5c6f3f5049d6256138907206234`), and `data/test_visual.db` (143360 bytes, inode 34558, sha256 `cebce919cff7f6fb4548b6baaf1f44d3caa57f6ed978c8c1f0b78d1e5e67e726`). Exact `pathlib.Path.unlink()` calls removed only those four paths. Post-delete checks showed all four absent. `data/portfolio.db` remained unchanged: 208896 bytes, inode 241846, sha256 `b5c596f903a3b446b72419dff9a019bd401cf43d5fde542e63e9639094ff61d6`. Canonical run recreated `data/test_bdd.db`; it remains current-run residue and was left untouched after receipt contradiction, not masked or broadly cleaned.

Full suite: `uv run task test` -> RED/TIMEOUT, runner elapsed `387.2496793209866s` through cleanup; external wall-clock `387.701s`; duration limit `300s`; process returned `124`. Six lanes launched in parallel: unit `143` (empty collection receipt), integration `143` (empty collection receipt), audit `143` (31 collected/passed before deadline), e2e `143` (server startup failed, connection refused on `8765`), bdd `143` (six recorded fixture/server startup failures, connection refused on `8766`), visual `143` (12 deselected, no collected result). Deadline triggered at 300 seconds; all owned child groups were signaled/reaped. Coverage unavailable. Exact skips were `[]` versus the two expected Docker skip IDs. Receipt manifest snapshot was `1032` nodes, matching current AUDIT population; reconciliation remained `ok=false`, `skip_mismatch=true`, because unit and integration published empty collection receipts.

Preflight: ledger `i10-review-r2-20260821`, 2026-08-21T21:44:51Z. Relevant ports `8765-8768` and four exact fixed DB paths were `absent`; no targeted suite process existed; `reports/test-profile` directory and LAN port `8000` were pre-existing and preserved. `_preflight()` returned `ok=true`, with no unknown/foreign relevant resources. LAN server was not touched.

Postflight: run `20260821T184456-660477` ended at runner epoch `1787349083.6891172`; ports `8765-8768` absent. Owned lane process groups and pytest temp roots reconciled `owned-cleaned`; durable lane logs/timings remained owned-current-run evidence. Unit/integration temporary DB receipts were classified `unknown` by runner because receipt collection was empty. Fixed `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, and `data/test_visual.db` were absent; `data/test_bdd.db` existed as current-run residue (size 32768, inode 34819, sha256 `24e9485fd7b254ac54c160e879d522c7bb533a662e06c9028e2c305dab32daee`). Cleanup verdict was `untrusted`; no foreign resource was touched.

Runner isolation: trusted prelaunch precondition `pass`; no baseline or allowlist exception. Postflight cleanup trust `fail` due unknown DB receipts, fixed-DB residue, and contradictory lane evidence. Direct-command receipt confirmed all six commands start `uv run pytest` and contain no `uv run task` lane wrapper. Taskipy remains present in `pyproject.toml`; its diff is pre-existing dependency work, not I10.

Policy alignment: `openspec/PRD.md` §4.8, stable/delta `dev-tasks`, and `AGENTS.md` retain narrow supervisor-only exception; noncanonical Taskipy entrypoints stay required. `openspec validate i10-substituir-taskipy-no-boundary-da-suite-canonica --type change --strict --json` passed. `openspec validate --specs --strict --json` passed all 70 specs, with informational long-text notices only.

LAN receipt: `http://127.0.0.1:8000/patrimonio` returned HTTP `303`; port `8000` was retained and never stopped/restored. Production DB hash remained unchanged.

Direct-command/ownership receipt: unit PID/PGID `660478/660478`, command `uv run pytest -m unit --ignore=tests/bdd --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin`; integration `660481/660481`, `uv run pytest -m integration --ignore=tests/audit_integration --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin`; audit `660484/660484`, `uv run pytest tests/audit_integration -vv -s -p test_profile_plugin`; e2e `660488/660488`, `uv run pytest tests/e2e -vv --no-cov -s -p test_profile_plugin`; bdd `660493/660493`, `uv run pytest tests/bdd -vv --no-cov -s -p test_profile_plugin`; visual `660497/660497`, `uv run pytest tests/visual -vv --no-cov -m 'not t32_pruned' -s -p test_profile_plugin`. Receipt retained dynamic governance deselections. Lane ports were e2e `8765,8767`, bdd `8766`, visual `8768`; unit/integration/audit had none. Temp roots were exact per-lane `reports/test-profile/.20260821T184456-660477-<lane>-pytest-*` and reconciled `owned-cleaned`.

Verdict: CHANGES_REQUESTED

#### R2-F01 — Canonical suite exceeded hard ceiling and did not produce green acceptance
Status: open
Requirement/task: `dev-tasks` Test coverage report; `tasks.md:90-99` task 4.1.
Evidence: `reports/test-profile/20260821T184456-run.json` records `elapsed_seconds=387.2496793209866`, `duration_exceeded=true`, `final_exit_code=124`, six lane exit `143`, manifest `1032` matching current AUDIT population, and `reconciliation.ok=false`; external wrapper measured `387.701s`.
Required change: diagnose and correct I10-compatible runner/suite bottleneck so one future canonical receipt is green and completes through child cleanup in `<=300s`, preserving all six lanes, tests, coverage, manifest, skips, DB isolation, fail-fast, and receipts. Excluded: no test deletion, skip/xfail, retry, lane reduction/serialization, timeout relaxation, product/F58/MyProfit/I08/T33 work, or second suite attempt in this review.
Acceptance: one owner-authorized isolated review run has six green lanes, current AUDIT `1032`-node blocking manifest/checksum, the exact two Docker skips, trusted cleanup, and measured elapsed wall-clock `<=300s`.

#### R2-F02 — Canonical receipt contains unknown DB ownership and fixed-DB residue
Status: open
Requirement/task: `dev-tasks` ownership/cleanup requirements; `tasks.md:90-99` task 4.1.
Evidence: same-run receipt cleanup verdict is `untrusted`; unit and integration have `receipt_error` for empty collection receipts and unknown temporary DB ownership; `data/test_bdd.db` remains after run despite lane receipt claiming `owned-cleaned`.
Required change: make canonical lane DB receipt publication and postflight reconciliation complete and truthful for all six lanes, with every current-run DB/temp/process resource classified `owned-cleaned` or `absent`; preserve unknown/foreign resources and never mask contradiction. Excluded: no host-wide cleanup, foreign-resource deletion, production DB mutation, or second full-suite run in this review.
Acceptance: receipt contains complete DB/PID/PGID/temp/port ownership evidence, no unknown/pre-existing/foreign relevant residue, cleanup verdict trusted, and all six lane results remain causal.

Failure classification: E2E and BDD startup failures are `Unknown` from this single run: logs show lane-local uvicorn readiness timeout/connection refused, not an assertion tied to I10 mapping (`20260821T184456-e2e.log:17-23`, `20260821T184456-bdd.log:15-25`). Unit/integration/audit/visual `143` results are deadline-induced, not independent assertion failures. Do not treat unknown environmental failure as approval evidence; retain full logs and resolve under R2-F01/R2-F02.

### Review R3
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**; tasks 1.1-3.3 **pass** by dossier/static audit; tasks 4.1-4.2 **not assessable** without canonical acceptance; direct vectors/no lane Taskipy wrappers **pass**; six-lane topology and policy wording **pass**; coverage/skips/manifest, lifecycle, ownership reconciliation, and canonical acceptance **not assessable** because trusted preflight blocked before launch; excluded product/F58/MyProfit, Taskipy changes outside canonical boundary, T34 code fixes, I08/T33, lane topology, retries/skips/xfails **pass**; changed-file scope **pass** against I10 boundary; strict change/spec validation **pass**; LAN/production DB safety **pass**.

Exact authorized cleanup: latest T34 ledger `tasks.md:1804-1825` recorded these six paths as `owned-current-run` and owner authorized only these paths. Metadata was read immediately before removal (pre-removal command timestamp was not separately captured): `reports/test-profile/.t34-e2e-readiness-20260821T195950-pytest` directory, `juca:juca`, mode `700`, inode `34630`, size `4096`, birth `2026-08-21 20:00:35.661283922 -0300`; `/tmp/opencode/t34-e2e-readiness-20260821T195950-tmp` directory, `juca:juca`, mode `775`, inode `1415051`, size `100`, birth `2026-08-21 20:00:33.509285502 -0300`; `reports/test-profile/.t34-bdd-readiness-20260821T200441-pytest` directory, `juca:juca`, mode `700`, inode `34832`, size `4096`, birth `2026-08-21 20:05:09.681343878 -0300`; `/tmp/opencode/t34-bdd-readiness-20260821T200441-tmp` directory, `juca:juca`, mode `775`, inode `1427535`, size `80`, birth `2026-08-21 20:05:05.781339389 -0300`; `data/test_e2e.db` regular file, `juca:juca`, mode `644`, inode `34633`, size `151552`, SHA-256 `7a6a8fbccbc6d46f7d1dbeccc5662632af1a52e9d17989d47ecd9bf4ad55d435`; `data/test_e2e_short_ttl.db` regular file, `juca:juca`, mode `644`, inode `34798`, size `126976`, SHA-256 `c7eb888813bf69d372643ca3b0261177b083339279f478002d416428283394f1`. Exact command removed only those six literal paths; no wildcard, parent, broad `/tmp`, production, foreign, unknown, or pre-existing path was removed. Post-removal checks: all six `ABSENT`.

Full suite: `uv run task test` -> **NOT RUN**. Canonical launch was blocked by trusted isolated-runner preflight; elapsed N/A; duration limit `300s`; cleanup N/A for suite. Six lanes `unit=N/A, integration=N/A, audit=N/A, e2e=N/A, bdd=N/A, visual=N/A`; coverage N/A; tests/skips N/A; manifest/checksum N/A; fail-fast N/A; no second suite, retry, skip, xfail, or focused Taskipy wrapper run. `<=300s` classification N/A.

Preflight: per-run ledger `i10-final-r3-20260821T205618-0300`, owner `I10 final review`, owner evidence exact inventory commands and this receipt, started/ended `2026-08-21T20:56:18-03:00`, fields inspected: `resource_kind`, `resource_id`, `owner`, `owner_evidence`, `started_at`, `ended_at`, `status`, `classification`, `evidence`, `cleanup_result`. Relevant process inventory: `NO_RELEVANT_PROCESSES`; lane listeners `8765-8768`: absent; exact `/tmp/pytest-of-juca`: absent; exact fixed DBs `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, `data/test_visual.db`: absent. However, six pre-existing runner-declared pytest roots remained under `reports/test-profile`, each owned `juca:juca`, mode `700`, with birth times from prior run `20260821T112339-618393`: `.20260821T112339-618393-unit-pytest-j5ic41dt` inode `34461`; `integration-pytest-d_tva1uc` inode `34495`; `audit-pytest-obe879b7` inode `34496`; `e2e-pytest-veunxpqj` inode `34499`; `bdd-pytest-61o_auyn` inode `34500`; `visual-pytest-umkj06jk` inode `34462`. Classification: `pre-existing`/unowned current run; owner evidence belongs prior T34 R2 run, not R3. No adoption, deletion, masking, allowlist, kill, or port free. Decision: **BLOCKED before launch**.

Postflight: no canonical suite started; no current-run process, listener, DB, temp, log, timing, or cleanup resources were created. Authorized six-path cleanup remained absent. Pre-existing six pytest roots remained untouched. Cleanup result: no suite cleanup applicable. Decision: **BLOCKED**.

Runner isolation: **failed**. No baseline or allowlist exception. Relevant pre-existing pytest roots are unowned residue; safe escalation is isolated runner/environment. LAN receipt: `http://127.0.0.1:8000/healthz` returned `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`; LAN service remained running and untouched. Production DB was not changed.

Direct-command receipt: `scripts/run_full_suite.py:41-77` contains six direct `uv run pytest` vectors; `scripts/run_full_suite.py:209-217` appends `-s`, `-p test_profile_plugin`, and governance deselections; no canonical child vector contains `uv run task`. Logical lanes remain `unit`, `integration`, `audit`, `e2e`, `bdd`, `visual`. No runtime receipt exists because launch was blocked.

Policy alignment: `openspec/PRD.md:215-219` permits direct pytest only inside existing supervisor invoked by `uv run task test`; stable `openspec/specs/dev-tasks/spec.md:58-93` preserves six lanes, task-defined flags, ownership, cleanup, receipts, and noncanonical Taskipy shortcuts. Change validation passed; stable specs `70/70` passed with informational long-text notices only.

Verdict: **BLOCKED**

#### R3-F01 — Trusted isolated runner unavailable after authorized exact cleanup
Status: blocked
Requirement/task: `dev-tasks` ownership-safe preflight and task 4.1 (`tasks.md:90-99`).
Evidence: preflight ledger `i10-final-r3-20260821T205618-0300` found six exact pre-existing pytest temp roots under `reports/test-profile` from prior run `20260821T112339-618393`; exact stat metadata and classifications recorded above. They are relevant runner temp resources without current-run ownership. Canonical command was not launched.
Required change: provide isolated runner/environment with no relevant pre-existing, foreign, unknown, contradictory, or incomplete state; preserve these roots until owner-authorized cleanup. Then perform exactly one canonical `uv run task test` and record complete six-lane receipt, coverage/skips/manifest, direct command identity, DB/process/temp/port ownership, and postflight reconciliation within 300 seconds. Excluded: no further host cleanup, no deletion/adoption of these roots without explicit authorization, no code changes, no T34/F58/product/MyProfit/I08/T33 work, no retries/skips/xfails, no lane changes, no second suite.
Acceptance: trusted preflight classifies every relevant resource `absent` or `owned-current-run`; one run produces six green lanes, complete manifest/skip/coverage/DB receipts, direct child vectors, trusted cleanup `absent`/`owned-cleaned`, and wall-clock `<=300s`.

### Review R4
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**; tasks 1.1-3.3 **pass**; task 4.1 **finding**; task 4.2 **pass** after strict validation; direct six-vector mapping and no lane Taskipy wrapper **pass**; six-lane topology and concurrent launch **pass** by receipt; fail-fast/deadline signaling **pass** as exercised; coverage/skips/manifest **finding**; process/port/DB/temp/report ownership and cleanup reconciliation **finding**; excluded product/F58/MyProfit/T34/I08/T33 code, task topology, retries/skips/xfails, broad cleanup, and DB/seed scope **pass**; changed-file scope **pass** against I10 boundary; LAN/production DB safety **pass**; policy alignment **pass**.

Exact authorized cleanup: owner authorization limited deletion to six R3 ledger roots. Removed only these literal directories, never wildcarded and never removed parent `reports/test-profile`: `reports/test-profile/.20260821T112339-618393-unit-pytest-j5ic41dt` (`juca:juca`, mode `700`, inode `34461`, size `4096`, birth from R3 ledger `2026-08-21` run `112339`); `reports/test-profile/.20260821T112339-618393-integration-pytest-d_tva1uc` (`juca:juca`, mode `700`, inode `34495`, size `4096`, same run); `reports/test-profile/.20260821T112339-618393-audit-pytest-obe879b7` (`juca:juca`, mode `700`, inode `34496`, size `4096`, same run); `reports/test-profile/.20260821T112339-618393-e2e-pytest-veunxpqj` (`juca:juca`, mode `700`, inode `34499`, size `4096`, same run); `reports/test-profile/.20260821T112339-618393-bdd-pytest-61o_auyn` (`juca:juca`, mode `700`, inode `34500`, size `4096`, same run); `reports/test-profile/.20260821T112339-618393-visual-pytest-umkj06jk` (`juca:juca`, mode `700`, inode `34462`, size `4096`, same run). Post-delete exact-path checks: all six `absent`; parent and all other reports preserved.

Full suite: `uv run task test` -> **RED/TIMEOUT**, one attempt only. Canonical runner receipt `reports/test-profile/20260821T212035-679347-run.json`; runner elapsed `691.19347973002s`, deadline `300.0s`, `deadline_triggered=true`, final exit `124`, all lane returns `143`. External tool terminated wrapper at `360000ms` before shell summary; receipt is authoritative for runner-through-cleanup duration, and `>300s` classification is unambiguous. Coverage unavailable; exact skips unavailable (`[]` not emitted as a trusted complete result); manifest/checksum unavailable; fail-fast disposition was deadline sibling stop, not green acceptance. No retry, skip, xfail, second suite, focused suite, or implementation edit performed.

| lane | result | collected/failure evidence | receipt cleanup |
|---|---|---|---|
| unit | `143`, deadline | collection incomplete; `20260821T212035-unit.log:1-14`; no test traceback | `untrusted-resource`; DB ownership `unknown` |
| integration | `143`, deadline | collection incomplete; `20260821T212035-integration.log:1-14`; no test traceback | `untrusted-resource`; DB ownership `unknown` |
| audit | `143`, deadline | 40 collected, output reached test execution; deadline stopped lane | `owned-cleaned` |
| e2e | `143`, deadline | 40 setup errors; server `8765` startup timeout/connection failure at `20260821T212035-e2e.log:17-23` with traceback per emitted `T29_TEST_FAILURE` | `owned-cleaned`; DB paths absent |
| bdd | `143`, deadline | 29 failures; server `8766` startup timeout/connection refused at `20260821T212035-bdd.log:16-30` with traceback per emitted `T29_TEST_FAILURE` | `owned-cleaned`; DB absent |
| visual | `143`, deadline | 8 selected/12 deselected, output stopped during execution at `20260821T212035-visual.log:13-25` | `owned-cleaned` |

Failure classification: E2E startup failures are **Unknown** (server readiness timeout on `8765`, not an assertion or I10 direct-vector mismatch); BDD startup failures are **Unknown** (connection refused/readiness timeout on `8766`, not an assertion or I10 direct-vector mismatch); unit/integration incomplete collection are **Unknown** (no assertion reached before deadline); audit/visual `143` are deadline-induced, not independent test failures. Complete stdout/stderr and traceback receipts remain in six lane logs above; runner stdout/stderr is `/tmp/opencode/i10-final-r4-suite.log`.

Preflight: ledger `i10-final-r4-20260821`, owner `I10 final review`, `2026-08-21T21:20:27-0300` to `2026-08-21T21:20:28-0300`. Ledger fields inspected: `resource_kind`, `resource_id`, `owner`, `owner_evidence`, `started_at`, `ended_at`, `status`, `classification`, `evidence`, `cleanup_result`. Relevant process inventory, lane ports `8765-8768`, fixed DBs `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, `data/test_visual.db`, exact `/tmp/pytest-of-juca`, and six authorized roots were `absent`; no unknown/foreign/pre-existing relevant resource remained. Decision: **TRUSTED; launch permitted**. LAN port `8000` was intentionally outside suite ownership and retained.

Postflight: runner receipt ended at epoch `1787358727.0292659`; all owned lane PIDs/PGIDs absent, ports `8765-8768` absent, all six current-run pytest roots absent, and current-run logs remained as durable owned evidence. Unit DB `/tmp/omaha-conftest-safe-7d7tydo9/portfolio.db` and integration DB `/tmp/omaha-conftest-safe-jnr0foji/portfolio.db` still existed but receipt classified both `unknown`; they were preserved and not adopted, deleted, or masked. Audit DB was owned-current-run in receipt; E2E/BDD/visual fixed DBs were absent. Cleanup decision: **untrusted**, because unknown DB ownership and missing/incomplete lane timing/collection evidence remain. PID-not-found observations are recorded races after receipt finalization; no broad cleanup attempted.

Runner isolation: prelaunch **pass** after exact authorized cleanup; no baseline or allowlist exception. Postflight **fail** due current-run unknown DB resources. Direct receipts show six child commands start `uv run pytest`, retain task-defined flags plus `-s`, plugin, and deselections, and contain no `uv run task` lane wrapper. Receipt run ID `20260821T212035-679347`; its observed historical manifest field `1043` is retained as evidence only and does not satisfy current AUDIT `1032`/checksum and exact two-skip acceptance.

Policy alignment: `openspec/PRD.md` §4.8, stable/delta `dev-tasks`, and `AGENTS.md` retain narrow supervisor-only direct-child exception; noncanonical Taskipy entrypoints remain required. Strict change validation and strict stable-spec validation passed after this round. `pyproject.toml` lane definitions remain unchanged. LAN receipt: `http://127.0.0.1:8000/healthz` returned HTTP `200`, `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`; LAN service and production DB were untouched.

Verdict: **BLOCKED**

#### R4-F01 — Canonical suite red and over hard ceiling
Status: open
Requirement/task: `dev-tasks` Test coverage report; task 4.1 (`tasks.md:90-99`).
Evidence: `reports/test-profile/20260821T212035-679347-run.json` records `elapsed_seconds=691.19347973002`, `duration_exceeded=true`, `final_exit_code=124`, deadline sibling stop, and all six lane exit codes `143`; external tool hit `360000ms` without wrapper completion. E2E/BDD logs record readiness failures; unit/integration logs stop during collection.
Required change: diagnose one owner-approved runner/environment bottleneck and produce one future trusted receipt with six green lanes, current AUDIT `1032`-node blocking manifest/checksum, the exact two Docker skips, coverage, and elapsed-through-cleanup `<=300s`. Preserve all tests, lanes, flags, fail-fast, cleanup, and receipts. Excluded: no test removal, skip/xfail, retry, timeout relaxation, lane change, product/F58/MyProfit/T34/I08/T33 edit, or second suite in this review.
Acceptance: future isolated canonical run `uv run task test` returns green, six lanes pass, manifest/skips/coverage reconcile, and measured duration is `<=300s`.

#### R4-F02 — Unknown current-run DB ownership prevents trusted cleanup
Status: open
Requirement/task: `dev-tasks` ownership/cleanup requirements; task 4.1 (`tasks.md:90-99`).
Evidence: same-run receipt lane mappings classify `/tmp/omaha-conftest-safe-7d7tydo9/portfolio.db` and `/tmp/omaha-conftest-safe-jnr0foji/portfolio.db` as `unknown` because required lane receipts were not published; exact paths remained present postflight. No deletion or adoption was performed.
Required change: make lane DB publication and postflight reconciliation complete and truthful for every current-run DB, with owner evidence and cleanup `owned-cleaned` or `absent`; preserve unknown/foreign resources and return nonzero on contradiction. Excluded: no foreign cleanup, host-wide scan, production DB action, DB reset/seed, or second full-suite run in this review.
Acceptance: future receipt contains complete DB/PID/PGID/temp/port ownership for all lanes, no unknown residue, trusted cleanup verdict, and causal lane results.

#### R4-F03 — Server readiness failures lack causal attribution
Status: open
Requirement/task: `dev-tasks` full-task scenario and task 4.1 (`tasks.md:90-99`).
Evidence: E2E `20260821T212035-e2e.log:17-23` reports `127.0.0.1:8765` not ready after 30s; BDD `20260821T212035-bdd.log:16-25` reports `127.0.0.1:8766` connection refused and forced server termination. Emitted tracebacks are fixture setup failures, not I10 command assertions.
Required change: on isolated owner-approved runner, diagnose server startup/readiness cause and provide causal evidence distinguishing environment/runner failure from I10 regression; preserve port ownership, bounded teardown, and all browser tests. Excluded: no product/server feature rewrite, port freeing, broad process kill, test masking, or extra full-suite attempt in this review.
Acceptance: future canonical receipt has E2E and BDD startup success, all browser lanes green, and server lifecycle/port receipts reconcile.

### Review R5
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**;
tasks 0.1 and 1.1-3.3 **pass** by dossier/static audit; direct six-vector
mapping/no lane Taskipy wrapper **pass**; six-lane concurrent launch,
process-group ownership, fail-fast signaling, and bounded cleanup **pass** by
same-run receipt; canonical acceptance **finding**; population/checksum/skips/
coverage **finding**; current-run resource reconciliation **pass**; policy and
excluded scope (product/F58/MyProfit, T34 implementation beyond shared-runner
evidence, Taskipy outside canonical boundary, DB/seed, archives, retries,
skip/xfail, lane topology) **pass**; changed-file audit **pass** against I10
boundary with unrelated worktree changes preserved; LAN/production DB safety
**pass**. All audited areas assessable; no `not assessable` area remains.

Full suite: `uv run task test` -> **RED**, one canonical attempt. Receipt:
`reports/test-profile/20260821T230929-run.json`, run
`20260821T230929-692949`; runner elapsed `12.23201156500727s`, external
wall-clock `12.596494s`, limit `300s`, `duration_exceeded=false`,
`deadline_triggered=false`, process return `1`, through-cleanup
`12.231954965012847s`. Duration gate passes; red suite blocks approval. No
retry or second suite launched.

| lane | direct argv | result | evidence | cleanup |
|---|---|---:|---|---|
| unit | `uv run pytest -m unit --ignore=tests/bdd --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin` + governance deselections | `143`, sibling-stop | 0 collected; collection interrupted | owned-cleaned |
| integration | `uv run pytest -m integration --ignore=tests/audit_integration --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin` | `143`, sibling-stop | 0 collected; collection interrupted | owned-cleaned |
| audit | `uv run pytest tests/audit_integration -vv -s -p test_profile_plugin` | `143`, sibling-stop | 31 collected/passed before stop | owned-cleaned |
| e2e | `uv run pytest tests/e2e -vv --no-cov -s -p test_profile_plugin` | `143`, sibling-stop | 51 collected; 11 Chromium setup errors | owned-cleaned |
| bdd | `uv run pytest tests/bdd -vv --no-cov -s -p test_profile_plugin` | `143`, sibling-stop | 51 collected; no terminal outcome | owned-cleaned |
| visual | `uv run pytest tests/visual -vv --no-cov -m 'not t32_pruned' -s -p test_profile_plugin` | `1`, first failure | 20 collected / 12 deselected / 8 selected; 8 setup errors | owned-cleaned |

Population/skip/coverage: manifest snapshot `1,032`, node checksum
`31d93ee09ba067c1370cd36392d5af4abeaeba18f2c41402b28b83d3d3022ea1`; 12
outside-lane T32 cases remain excluded. Receipt actual nodes `31` (audit only),
`reconciliation.ok=false`; expected skip IDs were exact two Docker identities,
actual skips `[]` because visual fail-fast stopped suite. Coverage unavailable;
unit/integration emitted no XML result. No intentional skip, xfail, deletion,
retry, or lane reduction occurred.

Preflight: ledger `i10-final-r5-20260821T000001Z`, owner `I10 final review`,
started/ended `1787364557.2864401`/`1787364557.354394`; inspected all required
fields (`resource_kind`, `resource_id`, `owner`, `owner_evidence`, timestamps,
status, classification, evidence, cleanup_result). Relevant process inventory,
ports `8765-8768`, four fixed DBs, hidden runner roots, and `/tmp/pytest-of-juca`
were `absent`; LAN `8000` was separately `pre-existing` with controlled-owner
evidence and untouched. Decision: **TRUSTED; launch permitted**. No unknown,
foreign, contradictory, or incomplete suite resource was adopted or changed.

Postflight: ledger `i10-final-r5-20260821T230929`; runner/pytest/Playwright/
uvicorn processes, ports `8765-8768`, fixed DBs, and run temp roots all
`absent`; every current-run cleanup `owned-cleaned`; receipt
`cleanup.verdict=clean`, `owned_only=true`, `residue=[]`. Durable logs/timings/
JSON remain evidence. LAN remained running; production DB untouched.

Runner isolation: prelaunch **pass**, no baseline/allowlist exception;
postflight **pass**. Receipt phases: preflight
`1787364569.6515503..1787364569.702106`; launch
`1787364569.7292268..1787364581.364451`; monitor
`1787364569.8412786..1787364581.319490`; cleanup
`1787364581.4116583..1787364581.4118145`; finalization
`1787364581.4471946..1787364581.8554273`; reconciliation
`1787364581.8554735..1787364581.8555896`. Six placeholders persisted before
launch. All six direct commands began `uv run pytest`; none contained a lane
`uv run task` wrapper.

LAN receipt: `bash scripts/print_lan_url.sh` -> `http://192.168.1.4:8000`;
read-only `GET /healthz` -> HTTP `200`; port 8000 left running.

Verdict: **CHANGES_REQUESTED**

#### R5-F01 — Chromium socket path overflow breaks browser lanes
Status: resolved
Requirement/task: `dev-tasks` direct lane/full-task scenarios; task 4.1
(`tasks.md:107-124`).
Evidence: visual is first failure. `reports/test-profile/20260821T230929-visual.log:88-91`
reports Chromium fatal `Socket path too long` for the runner-created path under
`reports/test-profile/.20260821T230929-692949-visual-pytest-61cvv356`; E2E
reports same launch failure at `20260821T230929-e2e.log:16-17`.
`scripts/run_full_suite.py:1607-1608` creates these long `--basetemp` roots.
Failure classification: **Code bug** in current runner/temp-boundary
integration, not assertion failure. Fail-fast then produced sibling `143`s.
Required change: keep exact direct vectors, six lanes, coverage, manifest,
skips, fail-fast, ownership, and cleanup, but make registered browser temp
boundaries compatible with Chromium socket limits; prove browser startup and
natural exit. Excluded: product/browser-test edits, test removal, skip/xfail,
retry, serialization, coverage/population reduction, broad cleanup, LAN/DB
operations. Acceptance: E2E, BDD, visual, and all other lanes exit 0 in one
future canonical receipt with trusted resource reconciliation.

Resolution: `scripts/run_full_suite.py::_create_lane_temp_root` now creates
each registered pytest boundary under fixed `/tmp` with short `o-` prefix and
rejects any generated path whose observed Chromium SingletonSocket suffix would
reach Unix's 108-byte socket limit. `_lane_environment`, exact temp receipt
matching, and `_reconcile_temp_root` remain unchanged. Regression
`tests/scripts/test_t29_harness.py::test_runner_temp_boundary_is_chromium_socket_safe_and_reconciles_exactly`
proves generated byte bound, run/lane receipt identity, exact-root cleanup, and
`owned-cleaned` classification. Focused result recorded below.

#### R5-F02 — Canonical population, skip, and coverage receipt incomplete
Status: resolved
Requirement/task: `dev-tasks` manifest/skip/coverage/receipt requirements;
task 4.1 (`tasks.md:107-124`).
Evidence: same JSON records `final_exit_code=1`, first failure `visual`, all
sibling lanes `143`, actual population `31` versus `1,032`,
`reconciliation.ok=false`, actual skips `[]` versus exact two Docker IDs, and
no coverage. Classification: browser root cause is **Code bug** R5-F01; unit,
integration, audit, and BDD `143`s are **Regression/propagated sibling-stop**
outcomes, not independent assertions; population/skip/coverage mismatch is
**Regression** of acceptance evidence caused by premature fail-fast.
Required change: after R5-F01-compatible correction, obtain one future
canonical receipt with complete six-lane timing, 1,032-node checksum/lane
reconciliation, 12 outside-lane exclusion, exact two skips, coverage, and
trusted cleanup. Preserve all tests/evidence; no second suite attempt in this
review. Acceptance: one future `uv run task test` is green, <=300s through
cleanup, exact contract passes, every resource `absent`/`owned-cleaned`.

Resolution: R5-F02 was fail-fast cascade from R5-F01's browser setup failure;
no receipt logic, lane topology, skip policy, coverage flags, or cleanup code
changed. The corrected bounded boundary removes documented root cause; review
must verify one future canonical receipt for complete 1,032-node/lane checksum
reconciliation, 12 outside-lane exclusion, exact two Docker skips, coverage,
and trusted cleanup. No second suite was run during apply remediation.

### R5 remediation execution evidence

- Pre-edit boundary: `git diff HEAD~1 -- scripts/run_full_suite.py
  tests/scripts/test_t29_harness.py scripts/test_t29_receipt_harness.py` was
  captured before edit; prior R1-R5 evidence and findings remain above.
- Changed symbols: `_create_lane_temp_root`, `main` temp-boundary creation, and
  focused Chromium boundary/ownership regression.
- Focused validation: `uv run task test-file tests/scripts/test_t29_harness.py`
  -> **71 passed in 0.42s**; `PYTHONPATH=. uv run task test-file
  scripts/test_t29_receipt_harness.py` -> **8 passed in 0.87s**. Targeted
  `uv run ruff check scripts/run_full_suite.py tests/scripts/test_t29_harness.py
  scripts/test_t29_receipt_harness.py` -> **passed**; `rtk git diff --check`
  -> **passed**; strict change validation -> **passed**; strict stable-spec
  validation -> **70/70 passed**, informational long-text notices only.
  Canonical `uv run task test` remains review-owned and was not run here.

Ledger closure for remediation focused commands:

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| child process | `focused-harness-remediation-1` | remediation-1/apply | exact runner-harness command registered before launch | `2026-08-21T23:16:28-03:00` | `2026-08-21T23:16:30-03:00` | exited | owned-cleaned | 71 tests passed; child process exited; no suite child/PGID/listener created | bounded command exit; no-op cleanup |
| temporary path | `/tmp/o-*` exact generated boundary | remediation-1/apply | `_create_lane_temp_root` creates under fixed `/tmp`; regression passes exact path to receipt reconciliation | `2026-08-21T23:16:28-03:00` | `2026-08-21T23:16:30-03:00` | absent | owned-cleaned | regression reports `<108` bytes for observed Chromium suffix and exact path reconciliation | `exact-root-removed`; no wildcard cleanup |
| test DB resource | `pytest-managed test-only dynamic DB` | remediation-1/apply | focused pytest command registered before launch; production DB excluded | `2026-08-21T23:16:28-03:00` | `2026-08-21T23:16:30-03:00` | exited | owned-cleaned | test process exited after 71 green nodes; no production target | pytest-owned test-only teardown; no external cleanup |
| child process | `receipt-harness-remediation-1` | remediation-1/apply | exact receipt harness command registered before launch | `2026-08-21T23:16:30-03:00` | `2026-08-21T23:16:32-03:00` | exited | owned-cleaned | 8 receipt tests passed; no suite child/PGID/listener created | bounded command exit; no-op cleanup |
| temporary path | `pytest-managed focused-test temp paths` | remediation-1/apply | pytest invocation owns only its test temp resources | `2026-08-21T23:16:30-03:00` | `2026-08-21T23:16:32-03:00` | absent | absent | no runner temp boundary remained; browser boundary exact cleanup asserted | idempotent no-op; no unrecorded deletion |
| child process | `lint-and-spec-validation-remediation-1` | remediation-1/apply | exact ruff/diff/OpenSpec command registered before launch | `2026-08-21T23:17:12-03:00` | `2026-08-21T23:17:12-03:00` | exited | owned-cleaned | ruff, diff check, change validation, and 70 stable specs passed | no-op; no process residue |

### Review R6
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**;
tasks 0.1 and 1.1-3.3 **pass** by dossier/static audit; direct six-vector
mapping, Chromium short-boundary implementation, and no lane Taskipy wrapper
**pass**; policy exception wording **pass**; stable `dev-tasks` normative
population text **finding**; canonical six-lane acceptance, coverage/skips,
manifest/lane reconciliation, process lifecycle, and post-launch cleanup **not
assessable** because trusted preflight blocked before launch; excluded
product/F58/MyProfit/T34/I08/T33, Taskipy outside canonical boundary, lane
vectors/topology, retries/skips/xfails, DB/seed scope **pass**; changed-file
scope **pass** against I10 boundary; LAN/production DB safety **pass**.

Full suite: `uv run task test` -> **NOT RUN**; trusted isolated-runner
precondition failed before launch; elapsed N/A; duration limit 300 seconds;
cleanup N/A (no suite resources created). Six lanes:
`unit=N/A, integration=N/A, audit=N/A, e2e=N/A, bdd=N/A, visual=N/A`.
Coverage, tests/skips, manifest/checksum, fail-fast, and elapsed-through-cleanup
are N/A. No retry, second suite, skip, xfail, or code edit occurred.

Preflight: ledger `i10-review-r6-20260822T022052Z`, owner `I10 final review
remediation 1/2`, owner evidence exact process/listener/path inventory and
ledger fields `resource_kind`, `resource_id`, `owner`, `owner_evidence`,
`started_at`, `ended_at`, `status`, `classification`, `evidence`,
`cleanup_result`. Relevant lane process/PGID inventory: absent. Lane ports
8765, 8766, 8767, 8768: absent. Fixed test DBs
`data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`,
`data/test_visual.db`: absent. Runner hidden roots under
`reports/test-profile`: absent. Exact `/tmp/pytest-of-juca`: **pre-existing**,
directory, owner `juca:juca`, mode `700`, inode `1447627`, size `120`, mtime
`2026-08-21 23:17:05 -0300`; no current-run ownership evidence. LAN port 8000
is pre-existing host service outside suite ownership and was not touched.
Decision: **BLOCKED before launch**. No resource was adopted, killed, freed,
deleted, masked, or allowlisted.

Postflight: no canonical suite started; repeat inventory retained lane ports,
fixed DBs, and runner hidden roots absent, while exact `/tmp/pytest-of-juca`
remained pre-existing/unowned. No current-run process, PGID, log, timing,
temp-root, DB, or cleanup resource existed. Cleanup result: no suite cleanup
attempted; pre-existing temp root preserved. Decision: **BLOCKED**.

Runner isolation: **failed**. Relevant test-temporary resource had unowned
pre-existing state; no foreign-resource baseline or allowlist exception used.
Canonical direct vectors remain `uv run pytest` with task-defined flags,
supervisor `-s -p test_profile_plugin`, and governance deselections. Static
socket evidence: `_create_lane_temp_root` uses `/tmp/o-*` and focused
remediation receipt proves observed Chromium suffix `<108` bytes plus exact-root
`owned-cleaned`. No canonical runtime socket receipt exists in R6.

Population/skip/coverage receipt: static manifest audit reports 1,032 nodes,
node checksum `31d93ee09ba067c1370cd36392d5af4abeaeba18f2c41402b28b83d3d3022ea1`,
12 outside-lane T32 cases excluded, and exact expected skips Docker build/run;
runtime actual population, lane checksums, exact skips, and coverage are N/A.

LAN receipt: `ss -ltn` observed `0.0.0.0:8000` and `[::]:8000`; service was
outside suite ownership and left running. No stop, restart, DB mutation, or
restoration performed.

Policy/spec validation: `openspec validate
i10-substituir-taskipy-no-boundary-da-suite-canonica --type change --strict
--json` passed; `openspec validate --specs --strict --json` passed 70/70 with
informational notices. However, stable `openspec/specs/dev-tasks/spec.md:103-105`
and `:118` still require obsolete immutable 1,043-node population, while I10
proposal/delta, `tests/AUDIT.md`, and runner require current 1,032-node
population. `git diff --check` passed; mapped I10 files only remain in scope,
with unrelated working-tree changes preserved.

Verdict: **BLOCKED**

#### R6-F01 — Trusted isolated runner unavailable
Status: resolved
Requirement/task: `dev-tasks` ownership-safe preflight; task 4.1
(`tasks.md:107-124`).
Evidence: R6 ledger found exact `/tmp/pytest-of-juca` pre-existing without
current-run owner evidence; metadata is recorded above. Canonical lane ports,
fixed DBs, hidden runner roots, and suite processes were absent. Protocol
requires stopping on any relevant pre-existing test-temporary resource.
Required change: provide isolated review runner/environment with no relevant
pre-existing, foreign, unknown, contradictory, or incomplete state; retain
current resource until owner-authorized action. Then perform exactly one
canonical `uv run task test` and record complete six-lane direct-command,
population/skip/coverage, PID/PGID/DB/temp/port, socket, and cleanup receipt
within 300 seconds. Excluded: host cleanup, temp-root deletion, adoption,
process kill, port freeing, code change, retry, second suite, and unrelated
scope.
Acceptance: preflight classifies every relevant resource `absent` or
`owned-current-run`; one canonical run is green, reconciles current AUDIT
manifest and exact skips, and postflight classifies current-run resources
`absent` or `owned-cleaned`.
Late finding reason: remediation changed Chromium boundary, but did not provide
isolated runner state; final gate rechecked mandatory preflight.

Resolution: owner-authorized exact cleanup removed only `/tmp/pytest-of-juca`
after pre-removal metadata capture. Focused validation registered its exact
pytest root lifecycle, cleaned only the current-run-created root, and confirmed
the exact path absent with `/tmp` preserved. No canonical suite was run by
apply; review must perform fresh isolated preflight.

#### R6-F02 — Stable dev-tasks spec retains obsolete population contract
Status: resolved
Requirement/task: `dev-tasks` T29 population requirement and task 4.2
(`tasks.md:126-131`).
Evidence: `openspec/specs/dev-tasks/spec.md:103-105` requires immutable
1,043-node manifest/checksum and `:118` requires 1,043 nodes, contradicting
I10 delta `specs/dev-tasks/spec.md:57-70`, proposal/design amendment,
`tests/AUDIT.md` 1,032-node source, and `scripts/run_full_suite.py` current
manifest contract. Strict schema validation passes syntax, not this normative
conflict.
Required change: owner-authorized sync/update stable `dev-tasks` population
language to current `tests/AUDIT.md` 1,032 blocking-node/checksum/lane contract,
12 outside-lane exclusion, and exact two Docker skip identities; preserve all
runner safety, coverage, receipt, and noncanonical Taskipy clauses. Excluded:
no runner code, test selection, lane topology, skip/xfail, retry, DB/seed,
product/F58/MyProfit/T34/I08/T33 work.
Acceptance: stable and delta specs state same normative source/count/checksum
and exact skips; strict change/spec validation passes; static audit finds no
obsolete 1,043 requirement.
Late finding reason: prior rounds recorded validator success but did not audit
stable normative population text against owner-authorized R6 acceptance.

Resolution: stable `openspec/specs/dev-tasks/spec.md` now matches current
`tests/AUDIT.md`: 1,032 blocking node IDs, recorded node/lane checksums, 12
outside-lane T32 cases excluded from canonical membership, and exact ordered
Docker skip identities. No obsolete 1,043 normative wording remains.

## R6 remediation 2/2 execution evidence

### Pre-edit boundary and ownership registration

- Before this remediation edit, `rtk git diff HEAD~1 --` was captured. Prior
  worktree boundaries and all earlier execution/review evidence above remain
  preserved; no prior finding text was deleted or rewritten.
- Remediation run: `i10-apply-r6-remediation-2-20260821T232420-0300`.
  Owner: `i10-substituir-taskipy-no-boundary-da-suite-canonica / apply /
  remediation 2/2`. Owner evidence was registered before cleanup at
  `2026-08-21T23:24:20-03:00`: owner authorization in current handoff names
  exact path `/tmp/pytest-of-juca` and forbids parent/wildcard/broad `/tmp`
  removal.

### R6-F01 exact cleanup proof

- Pre-removal exact-path metadata for `/tmp/pytest-of-juca`: directory,
  `juca:juca`, mode `700`, inode `1447627`, size `120` bytes, mtime and ctime
  `2026-08-21T23:17:05-03:00` (captured by exact `lstat` before removal). Its
  only registered cleanup target was that literal path; parent `/tmp` and
  siblings were not targets.
- Owner-authorized bounded operation: `shutil.rmtree(Path("/tmp/pytest-of-juca"))`
  after asserting resolved target equals `/tmp/pytest-of-juca`; no wildcard,
  parent, pattern, process, port, DB, or broad `/tmp` operation.
- Post-removal exact check at `2026-08-21T23:24:27-03:00`: literal path
  `absent`; `/tmp` preserved. Cleanup classification: `owned-cleaned` under
  owner-authorized exact-path exception; no foreign or unknown resource was
  touched.

### R6-F02 contract alignment

- Changed stable `openspec/specs/dev-tasks/spec.md` only: normative source is
  current `tests/AUDIT.md`; canonical population is 1,032 blocking node IDs;
  node checksum and six lane checksums are named; 12 versioned T32 cases remain
  outside canonical lanes; exact ordered Docker skip pair is named.
- Removed obsolete normative 1,043 wording. No runner behavior, test selection,
  lane topology, skip/xfail policy, DB/seed behavior, or unrelated spec changed.

### Remediation ledger

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| temporary path | `/tmp/pytest-of-juca` | apply/remediation-2 | exact literal path and owner authorization registered before use | `2026-08-21T23:24:20-03:00` | `2026-08-21T23:24:27-03:00` | cleanup-attempted | owned-cleaned | pre-existing metadata captured; exact path removed; exact post-check absent; `/tmp` parent preserved | bounded exact-root removal only |
| child process | `i10-focused-remediation-2` | apply/remediation-2 | run id registered before exact focused taskipy node launch | `2026-08-21T23:25:32-03:00` | `2026-08-21T23:25:40-03:00` | exited | owned-cleaned | command started `23:25:38`; 1 passed in 0.05s; command child exited; no process or listener residue | bounded command exit; no-op cleanup |
| temporary path | `/tmp/pytest-of-juca` | apply/remediation-2 | exact path was absent in pre-run inventory; focused command run id registered before launch; post-run creation timestamp `2026-08-21T23:25:40-03:00` binds root to current run | `2026-08-21T23:25:38-03:00` | `2026-08-21T23:26:58-03:00` | cleanup-attempted | owned-cleaned | post-run metadata inode `1448082`, mode `700`, size `80`, entries `pytest-0`, `pytest-current`; exact path only | exact `shutil.rmtree` removal; post-check absent; `/tmp` preserved |
| validation process batch | `i10-remediation-2-validation-batch` | apply/remediation-2 | remediation run id and command batch registered before validation commands | `2026-08-21T23:27:00-03:00` | `2026-08-21T23:27:49-03:00` | exited | owned-cleaned | change validation passed; 70/70 stable specs passed; ruff passed; diff check passed; inventory found no relevant process, hidden pytest root, fixed test DB, or exact pytest root | bounded command exits; no process residue; no cleanup target adopted |
| temporary path | `/tmp/i10-r6-change-validation.json` | apply/remediation-2 | exact output path registered in final validation command before redirection | `2026-08-21T23:28:54-03:00` | `2026-08-21T23:29:38-03:00` | cleanup-attempted | owned-cleaned | regular file, inode `1448093`, mode `664`, size `495`; exact post-check absent | exact `Path.unlink()`; no parent or sibling cleanup |
| temporary path | `/tmp/i10-r6-spec-validation.json` | apply/remediation-2 | exact output path registered in final validation command before redirection | `2026-08-21T23:28:54-03:00` | `2026-08-21T23:29:38-03:00` | cleanup-attempted | owned-cleaned | regular file, inode `1448094`, mode `664`, size `34837`; exact post-check absent | exact `Path.unlink()`; no parent or sibling cleanup |

Focused validation and exact current-run pytest-root cleanup are complete below.
Review canonical suite stays unrun; no `uv run task test` was launched by apply.

### Focused validation and cleanup result

- `uv run task test-one tests/scripts/test_t29_harness.py::test_runner_temp_boundary_is_chromium_socket_safe_and_reconciles_exactly`
  -> **1 passed in 0.05s**. This I10 regression proves short Chromium-safe
  boundary generation and exact `owned-cleaned` root reconciliation.
- Before focused launch, exact `/tmp/pytest-of-juca` inventory was `absent`.
  After launch, pytest created only that current-run root; metadata was captured
  before cleanup. Exact `shutil.rmtree(Path("/tmp/pytest-of-juca"))` ran only
  after asserting literal path identity and non-symlink directory state.
  Post-check: exact path `absent`; `/tmp` parent exists; no sibling/pattern/
  parent cleanup.
- Stable-spec static audit: no `1,043`/`1043`; required `1,032`, `tests/AUDIT.md`,
  12 outside-lane T32 wording, and both exact Docker IDs present.
- `rtk git diff --check` -> **passed**. No canonical `uv run task test` run.
- Post-validation isolation inventory at `2026-08-21T23:27:49-03:00`: no
  `run_full_suite.py`, pytest, or uvicorn process; ports `8765-8768` absent;
  hidden runner pytest roots absent; fixed test DBs absent; exact
  `/tmp/pytest-of-juca` absent. Existing LAN listeners `8000`, `5443`, and
  `9631` were observed as pre-existing and untouched; no baseline or allowlist
  exception used.
- Final validation receipt files `/tmp/i10-r6-change-validation.json` and
  `/tmp/i10-r6-spec-validation.json` were exact current-run outputs; metadata
  was captured before exact `Path.unlink()` cleanup. Both post-checks are
  absent. No other `/tmp` entry was targeted.

### Review R7
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**;
tasks 0.1 and 1.1-3.3 **pass**; direct six-vector mapping/no lane Taskipy
wrapper **pass**; short Chromium socket boundary **pass** by runtime receipts;
six-lane concurrent launch, process groups, fail-fast/deadline signaling,
receipts, and bounded cleanup **pass** by same-run receipt; canonical
acceptance **finding**; population/checksum/skips/coverage **finding**;
excluded product/F58/MyProfit/T34/I08/T33, DB/seed, lane topology,
retries/skips/xfails, broad cleanup, and noncanonical Taskipy scope **pass**;
changed-file scope **pass** against I10 boundary; policy alignment **pass**;
strict change/stable-spec validation **pass**; LAN/production DB safety
**pass**. All audited areas assessable; no `not assessable` area remains.

Full suite: `uv run task test` -> **RED/TIMEOUT**, exactly one canonical
attempt. Run `20260821T233306-698408`; runner elapsed `283.0701384610147s`,
external elapsed `283.52128052711487s`, limit `300s`,
`duration_exceeded=false`, `deadline_triggered=true`, final/parent return
`124`. Cleanup verdict `clean`, `owned_only=true`, through-cleanup
`283.07009176100837s`; no retry or second suite run.

| lane | direct argv / wrapper check | result | collection/failure evidence | cleanup |
|---|---|---:|---|---|
| unit | `uv run pytest -m unit --ignore=tests/bdd --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin` + deselections; no `uv run task` | `143`, deadline | collection stalled at 0; no assertion | `owned-cleaned` |
| integration | `uv run pytest -m integration --ignore=tests/audit_integration --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | collection stalled at 0; no assertion | `owned-cleaned` |
| audit | `uv run pytest tests/audit_integration -vv -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | 31 collected; interrupted | `owned-cleaned` |
| e2e | `uv run pytest tests/e2e -vv --no-cov -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | 1 collected/pass; 49 setup errors from `8765` readiness timeout | `owned-cleaned` |
| bdd | `uv run pytest tests/bdd -vv --no-cov -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | 40 collected; server-dependent failures after `8766` refusal | `owned-cleaned` |
| visual | `uv run pytest tests/visual -vv --no-cov -m 'not t32_pruned' -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | 20 collected / 12 deselected; interrupted | `owned-cleaned` |

Population/coverage/skips: current `tests/AUDIT.md` snapshot **1,032** blocking
nodes; node checksum
`31d93ee09ba067c1370cd36392d5af4abeaeba18f2c41402b28b83d3d3022ea1`; 12
versioned T32 cases remain outside canonical membership. Runtime actual nodes
`72` (unit 0, integration 0, audit 31, e2e 1, bdd 40, visual 0),
`reconciliation.ok=false`; expected skips were exactly the two Docker IDs,
actual skips `[]`. Coverage unavailable: unit/integration did not finish
collection and no trusted XML exists. No intentional skip, xfail, deletion,
retry, or lane reduction occurred.

Preflight: ledger `i10-final-r7-20260822T0233Z`, owner `I10 final review
remediation 2/2`; exact PID/PGID process inventory, lane socket probes,
fixed-DB lstat, hidden-root inventory, and `/tmp/pytest-of-juca` lstat recorded
all required ledger fields. Relevant process inventory, ports 8765-8768, fixed
DBs, hidden runner roots, and `/tmp/pytest-of-juca` were `absent`; LAN 8000 was
`pre-existing`, outside suite ownership, and untouched. Decision: **TRUSTED;
launch permitted**. No adoption, kill, free, delete, mask, or allowlist action.

Postflight: all six owned PGIDs absent, ports 8765-8768 absent, fixed DBs
absent, `/tmp/pytest-of-juca` absent, and each lane boundary `/tmp/o-*`
reconciled `owned-cleaned` / `exact-root-removed`. Durable lane logs/timings
and run JSON remain current-run evidence. No foreign or unknown residue;
cleanup reconciliation trusted and `clean`.

Runner isolation: prelaunch **pass**, no baseline/allowlist exception;
postflight **pass**. Six placeholders persisted before launch. Direct receipt
confirms all six commands start `uv run pytest`, preserve task-defined flags,
`-s`, plugin, and deselections, and contain no lane `uv run task` wrapper.
Chromium boundary was runtime-owned short `/tmp/o-*`; no socket overflow.

LAN receipt: `ss -ltn` found pre-existing host listeners on `0.0.0.0:8000` and
`[::]:8000`, outside suite ownership. Service was untouched; production DB was
not touched.

Tasks evidence: task 4.1 remains incomplete because canonical acceptance
failed. Task 4.2 validations passed: strict change validation, strict stable
spec validation (70/70), and `git diff --check`; informational notices only.
Remediation limit reached (2/2); no further automatic repair, archive, commit,
or push.

Verdict: **BLOCKED**

#### R7-F01 — Canonical suite red at deadline
Status: open
Requirement/task: stable `dev-tasks` Test coverage report and task 4.1
(`tasks.md:107-124`).
Evidence: `reports/test-profile/20260821T233306-run.json:1-9` records
`deadline_triggered=true`, final exit `124`, elapsed `283.0701384610147s`,
actual population `72` versus `1,032`, `actual_skips=[]` versus the exact two
required Docker IDs, `reconciliation.ok=false`, and no coverage result.
Required change: provide one owner-approved isolated canonical receipt with all
six direct pytest lanes green, current 1,032-node manifest/checksum/lane
reconciliation, 12 outside-lane T32 exclusion, exact two skips, coverage, and
trusted cleanup within 300 seconds. Preserve all tests, lanes, flags,
fail-fast, receipts, and DB isolation. Excluded: test removal, skip/xfail,
retry, timeout relaxation, lane reduction/serialization, product/F58/MyProfit/
T34/I08/T33 work, DB/seed action, broad cleanup, or another suite attempt in
this review.
Acceptance: future canonical receipt has six exit-0 lanes, exact manifest and
skip reconciliation, coverage, owned PID/PGID/DB/temp/port evidence, and
elapsed-through-cleanup `<=300s`.

#### R7-F02 — E2E/BDD server readiness unresolved
Status: open
Requirement/task: `dev-tasks` full-task scenario and task 4.1
(`tasks.md:107-124`).
Evidence: `20260821T233306-e2e.log` records uvicorn `127.0.0.1:8765` readiness
timeout after 30s; `20260821T233306-bdd.log` records `127.0.0.1:8766`
connection refusal, followed by setup/call failures. Classification:
**Unknown/environmental**; no I10 mapping assertion failed, but browser lanes
did not become green and deadline propagated.
Required change: provide causal owner evidence for E2E/BDD server startup on
owned ports and a green canonical receipt, preserving server lifecycle,
browser tests, process ownership, and cleanup. Excluded: product/server
rewrite, port freeing, broad process kill, test masking, extra full-suite
attempt, or scope expansion.
Acceptance: E2E and BDD servers reach readiness, browser lanes finish green,
and server/port resources reconcile. Late finding reason: remediation 2/2
changed stable population wording and prior exact temp-root cleanup; final gate
rechecked runtime readiness and found this unresolved condition.

### Review R8 — interrupted final-review recovery
Scope audit: not run. This gate only restored/verified Omaha LAN service and
determined whether a new canonical suite attempt can be trusted. No code,
product, DB, or test resource was changed.

Service restoration receipt: Omaha service was already running and healthy, so
no restart was performed. Confirmed identity: Docker container
`63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028`, name
`omaha-web-1`, image `omaha:dev`, status `running`, health `healthy`, started
`2026-08-22T03:04:58.686893586Z`, host bind `0.0.0.0:8000->8000/tcp` (also
`[::]:8000`). Container process identity: host PID `893`, PGID `893`, user
`juca`, command `/app/.venv/bin/python /app/.venv/bin/fastapi run --host
0.0.0.0 --port 8000 src/omaha/main.py`, cgroup
`docker-63fff7e6dc4b8f540604e8691e526ac423012345df423bb75956496c3c301028.scope`.
`bash scripts/print_lan_url.sh` returned `http://192.168.1.4:8000`.
Read-only `GET http://192.168.1.4:8000/healthz` returned HTTP `200` and
`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
No service restart, stop, adoption, DB operation, or cleanup occurred.

Suite attempt state: **ambiguous / started-incomplete cannot be ruled out**.
No new `20260822*` run receipt, lane log, timing file, or process record was
found. Current process inventory had no `run_full_suite.py`, pytest, Playwright,
or canonical `uv run task test` process; lane listeners `8765-8768` were
absent; hidden runner roots were absent; `/tmp/pytest-of-juca` was absent.
This absence does not prove canonical launch did not occur before interruption,
because interruption could precede durable receipt creation. Existing latest
durable canonical receipt remains R7 run `20260821T233306-698408`, not R8.
Therefore this gate does not classify R8 as definitively not-started and does
not launch `uv run task test`.

Resource state / ledger (`i10-recovery-r8-20260822T0311Z`, owner `I10 recovery`,
owner evidence: exact commands and outputs in this round):

| resource_kind | resource_id | owner | owner_evidence | started_at | ended_at | status | classification | evidence | cleanup_result |
|---|---|---|---|---|---|---|---|---|---|
| container/service | `omaha-web-1 / 63fff7e6dc4b...1028` | Omaha runtime | `docker inspect` identity + healthy state | pre-existing | `2026-08-22T03:11:17Z` | running | pre-existing | confirmed bind and health | untouched; no restart |
| process | `893/893` | Omaha runtime | `/proc/893/cmdline`, cgroup, container identity | pre-existing | `2026-08-22T03:11:17Z` | running | pre-existing | exact FastAPI Omaha command | untouched |
| listener | `0.0.0.0:8000,[::]:8000` | Omaha runtime | `ss` + LAN health receipt | pre-existing | `2026-08-22T03:11:17Z` | listening | pre-existing | HTTP 200 health | untouched |
| process group | `I10 canonical lanes` | I10 recovery | exact process inventory | `N/A` | `2026-08-22T03:11:17Z` | absent | absent | no suite processes | no cleanup |
| listener set | `8765-8768` | I10 recovery | exact socket probes | `N/A` | `2026-08-22T03:11:17Z` | absent | absent | no lane listeners | no cleanup |
| fixed test DB | `data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_visual.db` | I10 recovery | exact path checks | `N/A` | `2026-08-22T03:11:17Z` | absent | absent | paths absent | no cleanup |
| fixed test DB | `data/test_bdd.db` | prior/unresolved | exact path check; no current-run owner evidence | pre-existing | `2026-08-22T03:11:17Z` | present | pre-existing | inode `35025`, size `126976`, mtime `2026-08-21 23:46:44 -0300` | preserved; no adoption/deletion |
| temporary path | `/tmp/pytest-of-juca` | prior authorization target | exact path check | `N/A` | `2026-08-22T03:11:17Z` | absent | absent | literal path absent | no operation |

Postflight: no recovery-created suite resource existed. Omaha service remained
healthy. `data/test_bdd.db` remains pre-existing/unowned and was preserved.
No broad process, port, DB, or temporary-path cleanup was attempted.

Full suite: `uv run task test` -> **NOT RUN in R8**; no elapsed/duration
measurement; six lanes `N/A`; coverage/tests/skips/manifest/checksum/fail-fast
`N/A`; canonical hard ceiling `300s` not applicable. Prior R7 red/deadline
receipt remains historical evidence and is not reused as R8 acceptance.

Verdict: **BLOCKED**. Exact next action: owner must provide an isolated runner
and durable interruption boundary proving whether R8 launched. Because current
state is ambiguous and `data/test_bdd.db` is pre-existing without current-run
ownership, do not run another canonical suite in this task. Do not restart
Omaha while container `omaha-web-1` remains healthy.

### Review R9 — owner-authorized exact DB cleanup gate
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**;
tasks 0.1 and 1.1-3.3 **pass**; direct six-vector mapping/no lane Taskipy
wrapper **pass**; policy exception and stable population contract **pass**;
excluded product/F58/MyProfit/T34/I08/T33, DB/seed beyond authorized exact
cleanup, lane topology, retries/skips/xfails, broad cleanup, and noncanonical
Taskipy scope **pass**; changed-file scope **pass**; LAN/production DB safety
**pass**. Canonical six-lane execution, socket/readiness, population/checksum,
exact skips, coverage, runtime receipts, fail-fast, and post-launch cleanup are
**not assessable** because trusted preflight blocked before launch. All other
audited static areas assessable; no code edit performed.

Exact DB cleanup proof: owner authorization named only literal
`data/test_bdd.db`. Immediately before removal, metadata was captured:
regular file, mode `0644`, uid/gid `1000/1000`, inode `35025`, size `126976`,
mtime_ns `1787366804857347947`, SHA-256
`b983e594799bed0abb043336addcdf6886d6890d70fb24b22c0a61577b561cf4`.
Exact operation was `Path('data/test_bdd.db').unlink()`; post-check
`data/test_bdd.db` absent. Parent `data`, production `data/portfolio.db`, and
all other paths were not targets. No wildcard, parent, other DB, process, port,
or temporary-root cleanup occurred.

Full suite: `uv run task test` -> **NOT RUN**; trusted isolated-runner
precondition failed before launch; elapsed N/A; external duration N/A; limit
300 seconds; cleanup N/A because no suite resources were created. Six lanes:
`unit=N/A, integration=N/A, audit=N/A, e2e=N/A, bdd=N/A, visual=N/A`.
Direct argv, socket/readiness, coverage, tests/skips, manifest/checksum,
fail-fast, and elapsed-through-cleanup are N/A. No retry, second suite, skip,
xfail, or test masking occurred. `<=300s` classification N/A.

Preflight: ledger `i10-review-r9-20260822T0315Z`, owner `I10 review R9`,
started/ended `2026-08-22T03:15:13Z` (command timestamps
`2026-08-22T03:15:13.245383+00:00` to
`2026-08-22T03:15:13.274256+00:00`). Required fields inspected:
`resource_kind`, `resource_id`, `owner`, `owner_evidence`, `started_at`,
`ended_at`, `status`, `classification`, `evidence`, `cleanup_result`.
Canonical processes/PGIDs and ports `8765-8768` were absent. Exact fixed DBs
`data/test_e2e.db`, `data/test_e2e_short_ttl.db`, `data/test_bdd.db`, and
`data/test_visual.db` were absent after authorized cleanup. Exact
`/tmp/pytest-of-juca` was present, directory mode `0700`, inode `60`, with no
current-run ownership evidence: **unknown**. `reports/test-profile` had no
hidden runner roots. LAN `8000` was pre-existing outside suite ownership and
left untouched. Decision: **BLOCKED before launch**. Unknown temp resource was
not adopted, removed, masked, allowlisted, or otherwise changed.

Postflight: ledger `i10-review-r9-postflight-20260822T0315Z`, ended
`2026-08-22T03:15:27Z`. No canonical process or lane listener remained;
`8765-8768` absent; all four fixed test DB exact paths absent;
`/tmp/pytest-of-juca` remained present/unknown. No suite-created logs,
timings, lane temp roots, DBs, or cleanup resources existed. Cleanup result:
no suite cleanup applicable; unknown resource preserved. Decision: **BLOCKED**.

Runner isolation: **failed**. No foreign-resource baseline or allowlist
exception used. LAN receipt was outside I10 ownership; no restart, stop,
restoration, or production DB action. Canonical command was not attempted.

Tasks evidence: task 4.1 remains incomplete; task 4.2 and prior static/spec
validation remain complete. Remediation limit was already `2/2`; no automatic
third pass, archive, commit, or push.

Verdict: **BLOCKED**

#### R9-F01 — Unknown pre-existing pytest temporary root blocks isolated runner
Status: blocked
Requirement/task: `dev-tasks` ownership-safe preflight and task 4.1
(`tasks.md:107-124`).
Evidence: R9 ledger found exact `/tmp/pytest-of-juca` present with inode `60`,
mode `0700`, and no current-run owner evidence. Protocol requires stopping on
any relevant unknown resource. Canonical command was not launched.
Required change: provide isolated runner/environment with no relevant unknown,
pre-existing, foreign, contradictory, or incomplete process, listener, temp,
or fixed-DB state, then perform exactly one owner-authorized canonical
`uv run task test` and record complete six-lane direct-command, socket/readiness,
population/skip/coverage, ownership, and cleanup receipts within 300 seconds.
Excluded: no cleanup of `/tmp/pytest-of-juca`, no host cleanup, process kill,
port freeing, DB action beyond exact authorized `data/test_bdd.db` removal, code
edit, retry, skip/xfail, lane change, or second suite.
Acceptance: trusted preflight classifies every relevant suite resource
`absent` or `owned-current-run`; one canonical run is green, reconciles current
AUDIT 1,032-node/lane checksums and exact Docker skips, and postflight classifies
current-run resources `absent` or `owned-cleaned`.
Late finding reason: R8 left suite-attempt state ambiguous, so full acceptance
was not assessable; R9 is first fresh owner-authorized cleanup/preflight gate.

### Review R10
Scope audit: proposal **pass**; design **pass**; delta `dev-tasks` **pass**;
tasks 0.1 and 1.1-3.3 **pass**; task 4.1 **finding**; task 4.2 **pass**;
direct six-vector mapping/no lane Taskipy wrapper **pass**; short Chromium
socket boundary **pass** by current-run temp receipts; six-lane concurrent
launch, process groups, deadline signaling, receipts, and bounded cleanup
**pass** by same-run receipt; population/checksum/skips/coverage **finding**;
amended out-of-bound temp policy **pass**; excluded product/F58/MyProfit/T34/
I08/T33, DB/seed beyond runner-owned test resources, retries/skips/xfails,
lane topology, and noncanonical Taskipy scope **pass**; changed-file scope
**pass** against I10 boundary with unrelated worktree edits preserved;
LAN/production DB safety **pass**; strict change/stable-spec validation
**pass**. All audited areas assessable; no `not assessable` area remains.

Full suite: canonical command exactly once: `uv run task test` -> **RED/TIMEOUT**;
runner receipt `reports/test-profile/20260822T004437-run.json`, run
`20260822T004437-29027`; runner elapsed `283.306797126s`, external
`/usr/bin/time` elapsed `284.84s`, limit `300s`, `duration_exceeded=false`,
`deadline_triggered=true`, final exit `124`. Six lanes launched in parallel;
all returned `143` after deadline sibling stop. Cleanup receipt was clean and
owned-only. No retry, second suite, focused suite, test edit, skip, xfail, or
mask occurred.

| lane | direct argv / wrapper check | result | collection/failure evidence | cleanup |
|---|---|---:|---|---|
| unit | `uv run pytest -m unit --ignore=tests/bdd --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin` + governance deselections; no `uv run task` | `143`, deadline | 560 selected; no independent failure; deadline stopped lane | `owned-cleaned` |
| integration | `uv run pytest -m integration --ignore=tests/audit_integration --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | two `attempt to write a readonly database` failures in `tests/test_admin_recovery.py`; deadline stopped lane | `owned-cleaned` |
| audit | `uv run pytest tests/audit_integration -vv -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | 40 collected; output reached execution; deadline stopped lane | `owned-cleaned` |
| e2e | `uv run pytest tests/e2e -vv --no-cov -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | server `8765` reached readiness; 51 collected; deadline stopped lane | `owned-cleaned` |
| bdd | `uv run pytest tests/bdd -vv --no-cov -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | server `8766` reached readiness; `test_login_ok` Playwright URL wait timed out; deadline stopped lane | `owned-cleaned` |
| visual | `uv run pytest tests/visual -vv --no-cov -m 'not t32_pruned' -s -p test_profile_plugin`; no `uv run task` | `143`, deadline | 20 collected / 12 deselected; Playwright EPIPE appeared during sibling/deadline stop | `owned-cleaned` |

Population/skip/coverage: manifest snapshot `1,032`; node checksum
`31d93ee09ba067c1370cd36392d5af4abeaeba18f2c41402b28b83d3d3022ea1`; 12
versioned T32 cases remained outside canonical membership. Runtime actual
population was `264` versus `1,032`; `reconciliation.ok=false`; lane checksums
were incomplete/zero for browser lanes; expected skips were exactly the two
Docker identities, actual skips `[]`; coverage/XML unavailable. This receipt
does not satisfy canonical acceptance.

Preflight: ledger `i10-final-r10-20260822T0346Z`, owner `I10 final review R10`,
`2026-08-22T03:44:18.278119Z` to `2026-08-22T03:44:18.305618Z`. Ledger
contained required fields `resource_kind`, `resource_id`, `owner`,
`owner_evidence`, `started_at`, `ended_at`, `status`, `classification`,
`evidence`, `cleanup_result`. Canonical runner/lane process groups, ports
`8765-8768`, fixed DBs, and hidden runner-declared roots were `absent`.
`/tmp/pytest-of-juca` was present but outside canonical runner-declared
boundaries, classified `preserved/non-target`, and untouched. Decision:
**TRUSTED; launch permitted**. LAN `8000` was outside suite ownership and
untouched.

Postflight: ledger `i10-final-r10-postflight-20260822T0346Z`, ended
`2026-08-22T03:50:13.711405Z`. Canonical runner/lane processes and ports
`8765-8768` were absent; fixed DBs were absent; all six `/tmp/o-*` declared
lane roots reconciled `owned-cleaned`; dynamic test DBs were absent or
`owned-cleaned`; logs/timings/run JSON remained durable current-run evidence.
No foreign/unknown declared-boundary residue remained. `/tmp/pytest-of-juca`
remained preserved/non-target. Postflight decision: **TRUSTED cleanup**.
Read-only LAN receipt: `GET http://127.0.0.1:8000/healthz` returned
`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`;
LAN service and production DB were untouched.

Runner isolation: prelaunch **pass** under amended T34 policy; no baseline or
allowlist exception. Relevant process/listener/fixed-DB/declared-temp
inventory had no unowned state. Out-of-bound `/tmp/pytest-of-juca` was
recorded and preserved, not deleted, adopted, or used to block. Postlaunch
cleanup **pass** for current-run owned resources. Hard ceiling classification:
runner and external elapsed were `<=300s`, but red/deadline suite means no
approval.

Tasks evidence: task 4.1 remains incomplete because receipt is red, deadline
terminated all lanes, population/skips/coverage did not reconcile. Task 4.2
strict change validation passed; strict stable-spec validation passed `70/70`
with informational long-text notices. Remediation limit already `2/2`; no
third automatic repair loop, archive, commit, or push.

Verdict: **BLOCKED**

#### R10-F01 — Canonical suite red at deadline with incomplete acceptance
Status: blocked
Requirement/task: stable `dev-tasks` Test coverage report and task 4.1
(`tasks.md:107-124`).
Evidence: `reports/test-profile/20260822T004437-run.json` records
`deadline_triggered=true`, final exit `124`, elapsed `283.306797126s`, all six
lane exits `143`, runtime population `264` versus `1,032`,
`reconciliation.ok=false`, actual skips `[]` versus exact Docker pair, and no
coverage/XML result. Unit, audit, e2e, bdd, and visual 143 results are
deadline-induced sibling stops, not independent assertion verdicts. Visual
log records EPIPE during stop (`20260822T004437-visual.log:37-61`).
Required change: owner decision and a future compliant implementation/run
must produce six green direct pytest lanes, complete current-AUDIT node/lane
checksum reconciliation, exact two skips, coverage, and trusted cleanup under
300 seconds. Preserve every test, lane, flag, receipt, and resource boundary.
Excluded: no test deletion, skip/xfail, retry, timeout relaxation, lane
reduction/serialization, broad cleanup, product/F58/MyProfit/T34/I08/T33
scope, or second suite in this review.
Acceptance: one future canonical receipt has six exit-0 lanes, `1,032` node
population/checksum, 12 outside-lane T32 exclusion, exact Docker skip pair,
coverage, trusted cleanup, and elapsed-through-cleanup `<=300s`.

#### R10-F02 — Integration lane has readonly test-database failures
Status: blocked
Requirement/task: `dev-tasks` dynamic DB isolation and task 4.1
(`tasks.md:107-124`).
Evidence: `20260822T004437-integration.log:17-21` emits two
`T29_TEST_FAILURE` records for `test_admin_snapshots_lists_platform_snapshots`
and `test_admin_snapshots_skips_missing_files`; SQLAlchemy raises
`sqlite3.OperationalError: attempt to write a readonly database` while
inserting `asset_classes`. Failure classification: **Unknown/environmental**;
receipt shows dynamic DB target under `/tmp/o-uizzhby4/...`, but no causal
evidence proves I10 command mapping caused filesystem readonly state.
Required change: diagnose and correct owned test-DB writability/ownership on an
isolated owner-approved run, or provide causal evidence of pre-existing
environment fault; then retain all tests and emit green integration/complete
DB receipts. Excluded: no production DB action, foreign cleanup, DB reset as
review repair, code rewrite, retry, or second suite here.
Acceptance: integration lane exits 0 with writable run-owned dynamic DB and
receipt classifies DB `absent`/`owned-cleaned`.

#### R10-F03 — BDD browser assertion timed out after server readiness
Status: blocked
Requirement/task: `dev-tasks` full-task scenario and task 4.1
(`tasks.md:107-124`).
Evidence: `20260822T004437-bdd.log:15-20` shows server `8766` reached
`ready`, then `tests/bdd/test_scenarios.py::test_login_ok` failed in
`common_steps.py:430` with Playwright `TimeoutError: Timeout 5000ms exceeded`
while waiting for expected URL. Failure classification: **Unknown**;
readiness and direct argv were valid, but receipt does not establish whether
browser/app behavior or shared runner state caused timeout. Visual EPIPE is
deadline-propagated and covered by R10-F01, not separate independent failure.
Required change: diagnose causal BDD browser timeout on isolated runner and
produce green BDD/E2E/visual lanes without changing selectors, test
population, retries, skips, or lane topology. Excluded: no product rewrite,
test masking, extra full-suite attempt, broad cleanup, or scope expansion.
Acceptance: BDD login workflow completes, all browser lanes exit 0, server
readiness/port ownership receipts reconcile, and canonical receipt is green.

### Review R11 — maintenance-suspended policy gate
Scope audit: proposal **pass** for owner-authorized policy scope; design
decisions and policy code map **pass**; delta requirements/scenarios **pass**;
tasks 5.1-5.5 and policy acceptance **pass**; task 4.1 canonical reactivation
execution **deferred by explicit maintenance-suspended state**, not assessed as
runtime acceptance; policy/config consistency **pass**; focused/product-test
requirement **pass** for this docs/config-only amendment (no applicable product
behavior test changed); no-test-deletion/command-disablement/coverage/lane/
skip/retry invariants **pass** by static diff and dossier evidence; reactivation
condition **pass**; changed-file scope **pass** against approved policy/docs/
config allowlist, with pre-existing runtime/product/test worktree changes
excluded; OpenSpec validation **pass**; stable-spec validation **pass**. Excluded
runner, test, product, F58, DB, process, cleanup, and archive/commit/push work was
not reviewed as part of this policy gate.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**; owner
authorization makes parallel canonical full-suite enforcement non-blocking and
explicitly forbids launch in this review. Elapsed N/A; duration limit 300
seconds; cleanup N/A. Lanes `unit=N/A, integration=N/A, audit=N/A, e2e=N/A,
bdd=N/A, visual=N/A`; coverage N/A; tests/skips N/A; manifest/checksum N/A;
fail-fast N/A; `<=300s` classification N/A. No retry, skip, xfail, mask, lane
change, or second suite occurred.

Focused policy evidence: corrected policy consistency assertion -> **PASS**;
`openspec validate i10-substituir-taskipy-no-boundary-da-suite-canonica --type
change --strict --json` -> **PASS (1/1)**; `openspec validate --specs --strict
--json` -> **PASS (70/70)** with informational long-text notices only; `git diff
--check` -> **PASS**. Existing apply receipt records focused policy validation
PASS, exact command inventory, mandatory focused/product-test wording, and
individual Taskipy commands unchanged. No product behavior test applies to this
policy/docs/config-only amendment.

Preflight: canonical ownership preflight **not applicable and not launched**
under owner-authorized suspension. No canonical process, PGID, listener, test
DB, log, timing, or temporary resource was created. Existing apply validation
ledger `i10-maintenance-policy-validation-final-20260822T012715-0300` contains
required ownership fields and classifies its bounded validation process as
`owned-cleaned`; no suite resource was adopted, killed, freed, deleted, or
allowlisted.

Postflight: no canonical suite started; no current-run suite resource existed,
so no suite cleanup applied. Policy-validation process batches ended
`owned-cleaned`; no process/resource residue remained. Decision: suspension
receipt is trusted for policy review; canonical runtime acceptance remains
deferred until explicit reactivation.

Runner isolation: canonical runner precondition intentionally **not invoked**
because gate is suspended. No baseline or allowlist exception used. Policy
requires reactivation only after both concurrent dynamic SQLite readonly-DB and
BDD browser-timeout diagnosis resolve, followed by exactly one isolated green
six-lane `uv run task test` through cleanup in `<=300s`.

Policy receipt: `openspec/config.yaml:87-100` names state
`maintenance-suspended`, canonical command, all six individual commands,
affected boundary, focused requirement, ordered reactivation trigger, and
prohibited suppression actions. `openspec/PRD.md:785-826`,
`AGENTIC_DEVELOPMENT.md:105-112`, `.opencode/agents/apply.md:118-125`, and
`.opencode/agents/review.md:93-103` preserve focused evidence, product tests,
exact `NOT RUN — maintenance-suspended`, command availability, and no-test-
deletion rules. `pyproject.toml` task definitions remain outside amendment
scope and unchanged by this policy pass.

Verdict: **APPROVED**
