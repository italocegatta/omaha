## Owner-authorized maintenance-gate amendment — 2026-08-22

Owner authorizes temporary suspension of only the parallel canonical
`uv run task test` full-suite result as a mandatory apply/review/pre-push
delivery gate. `task test` remains present, callable, and canonical; its six
lanes, tests, skips, coverage, DB isolation, receipts, cleanup, fail-fast, and
300-second contract remain intact. Suspension means non-blocking maintenance
status, not deletion, disablement, skip, xfail, retry, lane change, or coverage
reduction.

During suspension, every change runs applicable focused command(s), and product
behavior tests remain mandatory. Apply records focused evidence and does not run
the routine full suite. Review audits scope, product-test coverage, focused
commands/results, and suspension visibility; review does not launch the
canonical full suite. Existing pre-push focused hooks remain mandatory; any
parallel canonical full-suite check is maintenance-suspended and non-blocking.

Reactivation requires both conditions, in order: (1) isolated diagnosis resolves
the concurrent dynamic SQLite readonly-DB failure and BDD browser timeout; and
(2) one isolated canonical `uv run task test` run is green across all six lanes,
with complete receipts/coverage/skips/reconciliation and elapsed wall-clock
through cleanup `<=300s`. Until then, product changes may proceed when their
focused product tests pass; T34 may continue bounded diagnosis/correction, but
F58 remains `Blocked` behind T34's reactivated canonical acceptance. I10 does
not alter F58, T34 code, T33, I08, product behavior, tests, task definitions,
DB, process state, cleanup, archive, commit, or push.

## Retained owner-authorized population amendment

The normative population source is the current `tests/AUDIT.md` manifest. It
defines **1,032 blocking nodes** for the canonical six-lane suite plus **12
owner-approved, versioned T32 cases explicitly outside canonical lanes**. The
canonical population calculation is therefore `len(blocking manifest node IDs)
= 1,032`; the 12 outside-lane cases are excluded, not added to the canonical
receipt population.

When canonical-gate reactivation is active, acceptance requires one
`uv run task test` receipt with six green lanes, current AUDIT
node-set/lane-membership/checksum reconciliation, and exactly these two
expected skips:

- `tests/test_dockerfile.py::test_docker_build_pro_image_succeeds`
- `tests/test_dockerfile.py::test_docker_run_pro_image_runs_as_omaha_user`

No other skip identity, population, lane, or checksum satisfies acceptance.
Direct six-lane runner scope and prior execution evidence remain unchanged.
Historical population figures remain evidence only, never current acceptance.

## Why

The canonical full-suite supervisor launches each lane through Taskipy. Taskipy
1.14.1 can race during SIGTERM handling after its shell child exits, producing
`psutil.NoSuchProcess` and an untrusted fail-fast receipt. Replace only this
supervisor boundary with direct pytest commands so T34 can obtain one trusted
canonical run without removing Taskipy from normal development workflows.

## What Changes

- Make `scripts/run_full_suite.py` map each existing lane task to its exact
  direct pytest command, preserving current selection, coverage, `--no-cov`,
  skips, plugin, `-s`, order, and pre-run deselection arguments.
- Keep `uv run task test` as the canonical public entrypoint; only child lane
  invocation stops using `uv run task <lane>`.
- Preserve six concurrent process groups, fail-fast and interruption signal
  behavior, bounded cleanup/reaping, dynamic DB isolation, ownership receipts,
  reconciliation against the current 1,032-node blocking manifest, exact two
  skips, and the 300-second ceiling.
- Update the narrow Taskipy policy exception in `openspec/PRD.md` §4.8,
  `openspec/specs/dev-tasks/spec.md`, and `AGENTS.md` only where needed to
  document this canonical-supervisor boundary.
- Add focused command-mapping/lane-parity assertions without changing test
  selection or adding retries, skips, xfails, or lane topology changes.
- Amend only policy/docs/config for owner-authorized `maintenance-suspended`
  enforcement: focused applicable tests stay mandatory; canonical full-suite
  execution becomes non-blocking until exact reactivation evidence exists.
- Do not implement runtime, test, runner, process, DB, cleanup, archive, commit,
  or push work in this amendment.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `dev-tasks`: permit direct pytest child commands only inside the existing
  Python supervisor invoked by canonical `uv run task test`; retain Taskipy
  entrypoints for serve, database, lint, coverage, focused tests, and all
  other shortcuts.
- `agent-test-performance-gate`: suspend only the mandatory canonical full-suite
  apply/review/pre-push result while requiring applicable focused evidence and
  product behavior tests; define exact reactivation evidence.
- `test-suite-quality`: make the owner-authorized maintenance suspension
  explicit without weakening the task, lane, test, skip, coverage, or
  no-deletion contracts.

## Impact

- Existing I10 runtime change remains `scripts/run_full_suite.py`; this
  owner-amendment adds no runtime implementation.
- `pyproject.toml` is inspection-only unless exact task-definition mapping
  proves a configuration adjustment necessary; Taskipy dependency and all
  non-canonical tasks remain unchanged.
- Policy/spec documentation: `openspec/PRD.md`, `AGENTS.md`,
  `AGENTIC_DEVELOPMENT.md`, `.opencode/agents/apply.md`,
  `.opencode/agents/review.md`, `openspec/config.yaml`, and deltas for
  `dev-tasks`, `agent-test-performance-gate`, and `test-suite-quality`.
- Focused runner contract tests will verify command vectors and unchanged
  lifecycle semantics. No product, MyProfit/F58, database, seed, migration,
  dependency, T33, or I08 changes.
