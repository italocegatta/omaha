## Context

I10 is a narrow compatibility boundary for T34. `uv run task test` already
enters `scripts/run_full_suite.py`; that supervisor currently launches six
children with `uv run task <lane>`. Taskipy 1.14.1 can raise
`psutil.NoSuchProcess` in its SIGTERM handler after its shell child has exited,
so runner ownership and causal fail-fast evidence become untrusted. T34's
existing dossier confirms this root cause and forbids dependency vendoring,
site-package edits, retries, lane changes, broad cleanup, and product changes.

## Owner-authorized maintenance-gate amendment

This amendment changes delivery policy only; it does not change I10's direct
lane implementation contract. The parallel canonical `uv run task test` result
is temporarily `maintenance-suspended` as a mandatory apply/review/pre-push
gate. The command remains canonical and available, and all six lanes, test
content, skips, coverage, DB isolation, receipts, cleanup, fail-fast behavior,
and the `<=300s` ceiling remain required whenever the canonical gate is active.

Focused policy is binding during suspension: each change selects and runs its
applicable focused Taskipy command(s); product behavior tests cannot be omitted,
weakened, skipped, xfailed, retried, or replaced by static evidence. Apply
reports focused command/result and never runs routine full suite. Review audits
scope, product-test coverage, focused evidence, and suspension state, but does
not launch `uv run task test`. Existing pre-push focused hooks remain blocking;
only any parallel canonical full-suite requirement is non-blocking.

Reactivation is exact and ordered: first resolve both concurrent dynamic SQLite
readonly-DB diagnosis and BDD browser-timeout diagnosis; then run one isolated
canonical `uv run task test` that is green across all six lanes, emits complete
coverage/skips/manifest/DB/temp/cleanup receipts, and finishes through cleanup
within `300s`. No partial diagnosis, focused green result, or historical receipt
reactivates the gate.

### Policy code map

| File / symbol | Current role and boundary to preserve |
|---|---|
| `openspec/PRD.md` §4.13 and §4.8 | Canonical no-mask/full-suite and Taskipy rules; add only owner-authorized suspension and retain command/test invariants. |
| `AGENTIC_DEVELOPMENT.md` standard flow, durable record, duration gate, criterion of ready | Shared lifecycle currently requires review full suite and <=300s; make those clauses conditional on active gate and require focused evidence during suspension. |
| `.opencode/agents/apply.md` test gate/handoff | Apply already owns focused tests; make suspension explicit and preserve red-focused-test stop and receipt requirements. |
| `.opencode/agents/review.md` workflow/test gate/handoff | Review currently owns one full suite; make launch conditional on active gate and require a durable non-blocking suspended receipt otherwise. |
| `AGENTS.md` workflow/status summaries and PRD §4 pointer | Navigation currently promises one full suite; mirror conditional lifecycle without changing unrelated standing rules. |
| `openspec/config.yaml::openspec_roadmap.quality_gate` | Planning gate currently names full-suite tests/duration unconditionally; retain existing keys and add explicit maintenance-suspended state/reactivation trigger. |
| `openspec/specs/dev-tasks/spec.md` delta | Preserve `task test` and six-lane runtime contract; state suspension is policy-only and does not authorize test deletion or lane changes. |
| `openspec/specs/agent-test-performance-gate/spec.md` delta | Formalize focused apply/review evidence and conditional single-suite review gate. |
| `openspec/specs/test-suite-quality/spec.md` delta | Reconcile temporary gate suspension with no-mask/no-deletion and full reactivation proof. |
| I10 `proposal.md`, `design.md`, `tasks.md` | Durable owner scope, exact policy, implementation map, executable tasks, lifecycle impact, and acceptance evidence. |

## Owner-authorized normative population amendment

### Authoritative source and calculation

`tests/AUDIT.md` is the selected normative source for current canonical
population. Its summary declares 1,032 blocking nodes, node checksum
`31d93ee09ba067c1370cd36392d5af4abeaeba18f2c41402b28b83d3d3022ea1`, and six
lane checksums. It also declares 12 owner-approved, versioned T32 cases outside
the standard blocking lanes. Canonical expected population is calculated as:

```text
expected_canonical_nodes = current AUDIT blocking node-ID set
expected_population = len(expected_canonical_nodes) = 1,032
```

The 12 outside-lane cases are excluded from canonical lane membership and are
not added to `expected_population`. They remain versioned evidence and are not
deleted, reclassified, or newly selected by I10.

### Exact skip contract

The canonical receipt SHALL report exactly two expected skip identities:

- `tests/test_dockerfile.py::test_docker_build_pro_image_succeeds`
- `tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user`

These are skip outcomes, not population exclusions. Any other skip identity,
missing skip evidence, or mismatch against this ordered pair fails receipt
acceptance. Existing governance pre-run deselection remains separate and does
not authorize new skips, xfails, deletion, or lane changes.

### Amendment conflict check

The selected `tests/AUDIT.md` count agrees with the owner-selected 1,032
blocking-node contract; no authoritative-count conflict exists. If an
implementation inspection finds a different current AUDIT count, node set,
lane checksum, or skip pair, implementation MUST stop with the exact conflict
recorded rather than inventing a replacement count.

## Implementation Decisions

### Maintenance suspension is explicit state, not test suppression

- **Context:** the latest I10 canonical attempt is red in concurrent dynamic
  SQLite readonly-DB and BDD browser-timeout paths; making that maintenance
  failure a mandatory delivery blocker prevents unrelated product work.
- **Decision:** represent suspension in policy/config/deltas as one named,
  owner-authorized state with exact affected gate and reactivation trigger.
- **Impact:** `task test` and every individual lane remain unchanged and
  available; only mandatory full-suite enforcement is non-blocking until
  reactivation. Focused product tests remain mandatory.
- **Rejected:** deleting/disabling `task test`, removing tests or lanes,
  adding skips/xfails/retries, reducing coverage, changing pre-push focused
  hooks, or treating focused evidence as reactivation evidence.

### Review has conditional ownership

- **Context:** review instructions currently require one canonical full suite,
  while owner temporarily suspends that gate.
- **Decision:** review runs exactly one canonical suite only when gate state is
  active; during suspension it records `NOT RUN — maintenance-suspended` and
  audits focused evidence, product-test coverage, scope, and policy visibility.
- **Impact:** review can approve eligible non-dependent product work on green
  focused evidence while preserving reactivation debt. F58 stays blocked behind
  T34's eventual canonical proof; T34 may continue bounded work.
- **Rejected:** approving red focused tests, silently omitting product tests,
  or converting a maintenance suspension into a permanent exemption.

### Direct vectors remain derived from unchanged Taskipy definitions

- **Context:** `pyproject.toml` already exposes one direct pytest command for
  each canonical lane, including coverage/XML, `--no-cov`, and visual marker
  flags.
- **Decision:** add explicit `DIRECT_LANE_COMMANDS` vectors in
  `scripts/run_full_suite.py`, keyed by existing Taskipy task name, and append
  only supervisor-owned `-s`, plugin, and governance deselections.
- **Impact:** child dispatch no longer enters Taskipy, while `pyproject.toml`
  and every non-canonical Taskipy entrypoint remain unchanged.
- **Evidence:** `shlex.split` comparison of all six task definitions against
  `DIRECT_LANE_COMMANDS` passed before focused test execution.

### Individual Taskipy commands are explicit policy inventory

- **Context:** static policy validation found that the amendment named lane
  categories but did not expose the literal `test-audit-integration` shortcut in
  every machine-readable policy surface.
- **Decision:** enumerate all six unchanged individual commands in the PRD,
  `openspec/config.yaml`, and the I10 `dev-tasks` delta:
  `test-unit`, `test-integration`, `test-audit-integration`, `test-e2e`,
  `test-bdd`, and `test-visual`.
- **Impact:** suspension remains limited to parallel canonical full-suite
  enforcement; operators retain explicit individual Taskipy entrypoints and
  validation can compare docs/config/deltas without inferring names from lane
  labels.
- **Evidence:** focused policy consistency assertion initially exposed missing
  literal `test-audit-integration`; amended surfaces passed exact command-list
  assertion before strict OpenSpec validation.

### Receipts retain logical task identity and add exact child command

- **Context:** existing lane metadata labelled `task` with a Taskipy wrapper,
  which would be false after direct dispatch.
- **Decision:** keep `task` as existing logical task name and record exact
  runtime argv in `command`; launch updates this field with dynamic
  governance deselections.
- **Impact:** six placeholders and lifecycle/ownership fields stay compatible,
  while final receipts truthfully identify direct child commands.
- **Evidence:** focused harness asserts exact vectors and receipt placeholder
  tests continue to require six lanes and unchanged ownership fields.

### Chromium temp boundary uses a fixed short Unix parent

- **Context:** review R5 reproduced Chromium's `SingletonSocket` overflow from
  the run-id/lane pytest boundary nested under `reports/test-profile`. Browser
  setup failed before tests ran, so fail-fast cascaded into incomplete
  population, skips, and coverage receipts.
- **Decision:** create each runner-owned pytest boundary with the existing
  `tempfile.mkdtemp` mechanism under fixed `/tmp` using the short `o-` prefix;
  validate the generated boundary plus Chromium's observed
  `/org.chromium.Chromium.XXXXXX/SingletonSocket` suffix against Unix's 108-byte
  socket limit. Keep `T29_TEMP_ROOT_BOUNDARY`, `TMPDIR`, `--basetemp`, exact
  receipt matching, and `_reconcile_temp_root` cleanup unchanged.
- **Impact:** browser user-data/socket paths stay bounded independently of the
  repository and run-id length. Ownership remains run/lane-bound and cleanup
  removes only the exact registered boundary.
- **Evidence:** R5 visual log shows the failing suffix at
  `reports/test-profile/.20260821T230929-692949-visual-pytest-61cvv356/org.chromium.Chromium.g1e2o4/SingletonSocket`;
  new focused harness regression asserts the generated byte bound and
  `owned-cleaned` exact-root reconciliation.

## Code map

| File / symbol | Current role and boundary to preserve |
|---|---|
| `scripts/run_full_suite.py::LANES` | Six canonical names and launch order: `unit`, `integration`, `audit`, `e2e`, `bdd`, `visual`; logical task names remain unchanged. |
| `scripts/run_full_suite.py::_runtime_child_command` | Builds child argv by wrapping each task with `uv run task <task> --`, then appending `-s`, `-p test_profile_plugin`, and governance deselections. This is the replacement point. |
| `scripts/run_full_suite.py::_lane_environment` | Adds lane-scoped `T29_DB_RECEIPT_LANE`, `T29_RUN_ID`, exact `T29_TEMP_ROOT_BOUNDARY`, and `PYTEST_ADDOPTS=--basetemp=...`; direct pytest must receive same environment. |
| `scripts/run_full_suite.py::_lane_metadata` | Creates six durable placeholders and ownership mappings before launch. Preserve receipt fields, resource ownership, and cleanup state; record direct child command without falsely claiming a Taskipy child if metadata is extended. |
| `scripts/run_full_suite.py::main` (`launch`, `monitor`, signal handlers, finalization) | Launches all six children concurrently, stops owned groups on first failure/interruption/deadline, reaps them, parses logs/timings/DB receipts, reconciles population, and enforces nonzero/error semantics. No lifecycle redesign. |
| `scripts/run_full_suite.py::_stop`, `_reap`, `_final_exit_code` | Exact process-group signaling, bounded grace/KILL, lifecycle-race recording, causal exit precedence. Direct pytest child must remain `start_new_session=True` and have same PID/PGID ownership. |
| `scripts/run_full_suite.py::_collection`, `_summary`, `_reconcile_temp_root`, DB receipt validation | Consumes pytest output, T29 timings, dynamic/fixed DB receipts, coverage/skips, and exact temp-root evidence. Direct argv must retain `-s`, plugin, markers, and all task flags so parsers see same output. |
| `scripts/run_full_suite.py::load_manifest`, `EXPECTED_SKIPS`, and `tests/AUDIT.md` | Load current blocking node set, population/checksum/lane checksums, and exact two skip identities. Historical T29 counts are non-normative evidence. |
| `pyproject.toml:[tool.taskipy.tasks]::test`, `test-unit`, `test-integration`, `test-audit-integration`, `test-e2e`, `test-bdd`, `test-visual` | Source of truth for current lane command mapping. Inspection baseline; no edit expected because each definition already exposes a direct pytest command. |
| `tests/scripts/test_t29_harness.py` and `scripts/test_t29_receipt_harness.py` | Existing focused runner/lifecycle/receipt oracles. Extend command-vector assertions and adapt command-index assumptions only as required by direct argv. |
| `openspec/PRD.md` §4.8 | Canonical policy currently prefers Taskipy for every test; narrow exception must be documented here. |
| `openspec/specs/dev-tasks/spec.md` test-coverage requirement | Stable contract currently requires Taskipy-owned lane entrypoints; modify only that boundary while retaining all test/receipt semantics. |
| `AGENTS.md` Taskipy rule and test workflow references | Navigation/policy text that must distinguish default Taskipy usage from this one supervisor exception, if wording remains contradictory after PRD update. |

## Current relevant flow

1. Operator runs `uv run task test`.
2. `pyproject.toml::test` invokes `uv run python -m scripts.run_full_suite`.
3. Runner performs bounded port/DB preflight, loads manifest/governance,
   creates run ID and six lane placeholders, and chooses pre-run deselections.
4. `_runtime_child_command(task, selected)` currently returns
   `uv run task <task> -- -s -p test_profile_plugin` plus each selected
   `--deselect <nodeid>`.
5. `main` launches one `Popen` per lane with lane environment, unique temp-root
   boundary, log/timing files, and `start_new_session=True`. It then monitors
   all lanes concurrently. First nonzero exit stops only remaining owned groups.
6. Finalization reads lane output, parses T29 collection/skip/timing/server/DB
   receipts, reconciles the current 1,032-node blocking manifest and exact two
   skips, excludes the 12 explicitly outside-lane T32 cases, validates dynamic
   DB targets, reconciles temp roots, persists cleanup evidence, and applies the
   <=300s elapsed-through-cleanup result.

Boundary conditions: no production `data/portfolio.db`; no host-wide process,
port, or `/tmp` scan; no foreign-resource adoption; no retries or new skip/
xfail; no lane removal or serialization; no coverage/manifest change.

Policy boundary during current suspension: change author runs applicable focused
Taskipy command(s); product behavior tests remain required. Apply and review do
not use the canonical full-suite result as a blocking gate, and review records
the command as `NOT RUN — maintenance-suspended` rather than masking it.
Reactivation requires the exact two diagnosis resolutions followed by one green
isolated six-lane canonical run through cleanup in `<=300s`.

## Direct command mapping

Map logical task names to the current `pyproject.toml` pytest argv exactly,
then append supervisor-owned runtime arguments in their current order:
`-s`, `-p`, `test_profile_plugin`, followed by governance `--deselect`
pairs. Each vector starts `uv run pytest`; no vector contains `uv run task`.

| Lane / current task | Direct base argv copied from `pyproject.toml` | Effective child argv before dynamic deselections |
|---|---|---|
| `unit` / `test-unit` | `uv run pytest -m unit --ignore=tests/bdd --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv` | `uv run pytest -m unit --ignore=tests/bdd --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin` |
| `integration` / `test-integration` | `uv run pytest -m integration --ignore=tests/audit_integration --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv` | `uv run pytest -m integration --ignore=tests/audit_integration --cov=src/omaha --cov-report=xml:reports/coverage.xml -vv -s -p test_profile_plugin` |
| `audit` / `test-audit-integration` | `uv run pytest tests/audit_integration -vv` | `uv run pytest tests/audit_integration -vv -s -p test_profile_plugin` |
| `e2e` / `test-e2e` | `uv run pytest tests/e2e -vv --no-cov` | `uv run pytest tests/e2e -vv --no-cov -s -p test_profile_plugin` |
| `bdd` / `test-bdd` | `uv run pytest tests/bdd -vv --no-cov` | `uv run pytest tests/bdd -vv --no-cov -s -p test_profile_plugin` |
| `visual` / `test-visual` | `uv run pytest tests/visual -vv --no-cov -m 'not t32_pruned'` | `uv run pytest tests/visual -vv --no-cov -m 'not t32_pruned' -s -p test_profile_plugin` |

The visual marker remains one pytest `-m` value, represented in subprocess
argv as `"not t32_pruned"`; shell quoting is not part of the argv. No task
definition is rewritten. If inspection finds any mapping mismatch, stop with
`BLOCKED_FOR_IMPLEMENTATION_BRIEF` rather than inventing flags or semantics.

## Goals / Non-Goals

**Goals:**

- Remove Taskipy only between `run_full_suite.py` and its six lane children.
- Preserve lane names/order, concurrent launch, fail-fast, interrupt priority,
  process groups, bounded cleanup, logs/timings, receipts, DB isolation,
  coverage, skips, manifest reconciliation, and 300-second classification.
- Make focused tests prove exact direct vectors and prove Taskipy remains used
  by `task test` entrypoint and non-canonical tasks.
- Record direct command identity in any new/changed receipt field without
  changing existing ownership/cleanup semantics; retain stable lane/task data.
- Document exception narrowly in PRD §4.8, `dev-tasks`, and only contradictory
  `AGENTS.md` wording.

**Non-Goals:**

- No removal or downgrade of Taskipy dependency.
- No changes to `serve`, DB, Docker, lint, coverage shortcut, focused-test
  tasks, `test` entrypoint, or unrelated task definitions.
- No changes to tests' selection, markers, skips, xfails, retries, lane count,
  lane order, serial/concurrent policy, fixtures, DB data, seed, product,
  MyProfit/F58, T33, I08, D05, or installed packages.
- No broad cleanup, process discovery, port freeing, temp-root traversal,
  dependency update, `uv.lock` edit, or canonical full-suite execution at
  proposal/apply; review owns exactly one canonical run only after gate
  reactivation, and records it not run while suspension is active.

## Decisions

### 1. Keep Taskipy as public entrypoint, replace only child boundary

`uv run task test` remains the operator-facing and policy-recognized command.
Only `_runtime_child_command` changes its child argv. This preserves existing
task discovery and all non-canonical workflows while bypassing Taskipy's
signal-handler race.

Rejected: removing Taskipy, adding a second runner, changing `test` to a raw
shell fan-out, or editing installed Taskipy. Those broaden scope and weaken
the established supervisor ownership model.

### 2. Derive direct vectors from current task definitions

Use an explicit mapping keyed by existing task name or lane, with the six
current pytest command vectors above. Append current plugin/output and dynamic
deselection args in `_runtime_child_command`; do not rely on shell expansion,
Taskipy nesting, or inferred flags. Keep `LANES` as the authoritative order.

Rejected: invoking `pytest` with only paths/markers, reconstructing flags from
lane names, or adding a new pyproject task. Any mapping/config mismatch blocks
implementation.

### 3. Preserve process lifecycle and receipts verbatim

Keep `Popen(..., start_new_session=True)`, environment construction, ledger
pre-persistence, actual PGID lookup, polling, signal forwarding, bounded
reaping, lifecycle-race classification, finalization, reconciliation, and
exit-code precedence unchanged. The direct command is data passed to the same
child boundary, not a reason to alter lifecycle behavior. If command identity
needs durable evidence, add a non-breaking exact-command field while retaining
existing lane/task and ownership fields.

Rejected: changing signal grace, making children share a process group,
serializing browser lanes, retrying failed children, or treating direct pytest
as permission to loosen cleanup validation.

### 4. Policy exception is explicit and non-transitive

PRD §4.8 remains default Taskipy guidance. It gains one exception: the
existing Python supervisor invoked by canonical `uv run task test` may launch
the six mapped pytest children directly. `dev-tasks` repeats only this
contractual distinction; `AGENTS.md` changes only its summary wording if
needed. Focused commands and operational tasks continue to use Taskipy.

Rejected: a generic “raw commands are allowed for tests” rule, which would
reopen command drift and violate the reason for task definitions.

## Change map

| File / symbol | From → to | Reason |
|---|---|---|
| `scripts/run_full_suite.py::_runtime_child_command` and direct mapping constant | `uv run task <task> --` wrapper → exact `uv run pytest ...` vector from table, with unchanged plugin/deselect suffix | Bypass Taskipy SIGTERM race while preserving pytest semantics. |
| `scripts/run_full_suite.py::load_manifest` / `EXPECTED_SKIPS` | Historical population acceptance → current `tests/AUDIT.md` 1,032 blocking-node set, 12 outside-lane exclusion, and exact two skip identities | Align receipt acceptance with owner-selected current audit without changing runner topology or test population. |
| `scripts/run_full_suite.py::_lane_metadata` only if command evidence needs a new field | Existing lane/task receipt data → same fields plus exact direct child command, without changing ownership fields | Keep receipts truthful and auditable without breaking consumers. Avoid change if existing field can remain compatible and truthful. |
| `tests/scripts/test_t29_harness.py` focused command/lifecycle scenarios | Implicit command-index assumptions → lane-aware direct-vector assertions; lifecycle oracles unchanged | Prove direct mapping and keep six-lane/fail-fast receipts testable. |
| `scripts/test_t29_receipt_harness.py` runtime command assertion, if affected | Wrapper-shaped assumptions → direct pytest vector assertions | Verify `-s`, plugin, env, and receipt visibility under direct child. |
| `openspec/PRD.md` §4.8 | Blanket preference against raw commands → same default plus one supervisor-only exception | Policy must authorize I10 without broadening exception. |
| `openspec/specs/dev-tasks/spec.md` test-coverage requirement | Six lanes required to use Taskipy-owned entrypoints → six lanes required to preserve exact task-defined pytest semantics, with direct child exception | Stable contract matches implementation while retaining all safety clauses. |
| `AGENTS.md` §4 summary / test workflow text, only if contradictory | “Taskipy, not raw commands” without exception → default rule linked to PRD §4.8 exception | Keep agent navigation consistent with canonical policy. |
| `openspec/PRD.md` §4.13, `AGENTIC_DEVELOPMENT.md`, agent policies | Unconditional full-suite apply/review/pre-push gate → owner-authorized `maintenance-suspended` state with focused mandatory evidence | Stop maintenance-only global runner failure from blocking unrelated product delivery. |
| `openspec/config.yaml` quality-gate metadata | Full-suite/duration acceptance lacks operational state → explicit suspension state and exact reactivation trigger | Make suspension visible to orchestration and validation. |
| `agent-test-performance-gate` / `test-suite-quality` deltas | Full-suite result always mandatory → temporary non-blocking state with focused evidence and reactivation proof | Remove policy contradiction while retaining no-mask/no-deletion contract. |
| `pyproject.toml` lane tasks | No intended change | Current definitions already provide exact source vectors; edit only if inspection proves direct mapping impossible, otherwise record unchanged. |

## Risks / Trade-offs

- **[Flag drift]** Direct vectors can diverge from `pyproject.toml` later → keep
  one explicit table/mapping, focused equality tests, and document mapping
  source; future task-definition changes require runner review.
- **[Arg ordering drift]** Pytest option order or visual marker quoting can
  alter collection → assert exact argv lists, including `-m "not t32_pruned"`,
  `--no-cov`, coverage paths, plugin, and deselection pairs.
- **[Receipt misattribution]** Direct child output may differ from Taskipy
  wrapper output → retain `-s`, unchanged env/paths, exact logs/timings, and
  run focused receipt parsing tests before canonical execution.
- **[Policy overreach]** Raw-command exception could spread to other workflows
  → wording names only `scripts/run_full_suite.py` child lanes and explicitly
  preserves Taskipy elsewhere.
- **[Population drift]** Historical T29 evidence can be mistaken for current
  acceptance → bind implementation and receipt checks to `tests/AUDIT.md`, its
  1,032 blocking-node checksum/lane checksums, and exact two skip IDs; stop on
  source conflict.
- **[Performance]** Direct pytest could alter startup enough to exceed 300s →
  review measures elapsed wall-clock through cleanup; over-ceiling remains
  `TIMEOUT_EXIT_CODE`, with no retry or lane reduction.
- **[Policy drift]** Temporary suspension could become indefinite or broad →
  name exact state, affected gate, owner date, diagnosis pair, one-run
  reactivation proof, and unchanged individual commands in every policy mirror.
- **[False product confidence]** Focused evidence could be mistaken for
  full-suite proof → review receipt labels canonical suite `NOT RUN —
  maintenance-suspended`; F58 remains blocked until T34 obtains reactivation
  evidence.

## Migration Plan

No dependency, DB, migration, seed, or deployment migration. This amendment
changes policy/config/dossier only: no runner, test, product, process, DB,
cleanup, archive, commit, or push work. Apply the policy amendment with
focused OpenSpec/static validation; product changes still run their applicable
focused Taskipy tests. While suspension is active, review does not run the
canonical suite. Rollback is removal of the explicit suspension state, which
restores the existing canonical full-suite gate; reactivation instead follows
the exact diagnosis-plus-one-green-run trigger above.

## Open Questions

None for proposal. Direct mappings are fully determined by current
`pyproject.toml`; if implementation discovers a flag, ordering, output, or
receipt mismatch that cannot preserve current semantics, stop with
`BLOCKED_FOR_IMPLEMENTATION_BRIEF`.
