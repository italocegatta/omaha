## Why

F61 and F58 review evidence exposed a canonical runner race: a lane child can
vanish between polling, signal forwarding, and reap, producing `NoSuchProcess`,
PID-not-found, or EPIPE noise that hides the original failure. The runner also
does not leave complete per-lane ownership and cleanup evidence, making sibling
termination, partial launch, survivors, and 854.89-second timeout behavior
expensive to attribute.

Owner authorizes this implementation slice now under an explicit dependency
exception. D05 remains `Blocked` and cannot be claimed archived or approved;
I08 consumes its audited ownership/stop vocabulary because D05's contract audit
passed and its documentation-only review was blocked by unrelated unknown PID
and visual failures.

## What Changes

- Harden `scripts/run_full_suite.py` signal, fail-fast, deadline, and reap paths
  against vanished children; preserve the causal lane/fail-fast/deadline result
  when cleanup observes `NoSuchProcess`, PID-not-found, or EPIPE.
- Reconcile descendants and lane resources only through current-run ownership
  evidence; clean owned process groups/resources in bounded, idempotent scope
  and preserve foreign or unknown processes, ports, paths, and databases.
- Emit complete six-lane receipts with PID, PGID, owned resource mapping,
  timestamps, signal/return code, cleanup verdict, residue/foreign evidence,
  sibling-stop attribution, partial-launch state, and timeout telemetry.
- Keep `scripts/run_expanded_lane.py` and `pyproject.toml` taskipy behavior
  aligned with the canonical runner without changing lane topology.
- Add controlled harness tests for vanished child, descendant survivor, foreign
  resource, fail-fast sibling stop, partial launch, and timeout scenarios.
- Preserve six lanes, fail-fast, coverage, retained tests/skips, taskipy
  entrypoints, and the hard 300-second ceiling. No broad process termination.

## Capabilities

### New Capabilities

- None. I08 implements existing runner/taskipy contracts using D05's audited
  ownership vocabulary; it does not claim D05 stable-spec approval.

### Modified Capabilities

- `dev-tasks`: strengthen canonical taskipy runner lifecycle, ownership-scoped
  cleanup, vanished-child handling, and complete per-lane receipt requirements
  while preserving existing lane, coverage, fail-fast, and ceiling behavior.

## Impact

- Runner implementation: `scripts/run_full_suite.py` and
  `scripts/run_expanded_lane.py`.
- Task entrypoint contract: `pyproject.toml`.
- Focused unit harness contracts: `tests/scripts/test_t29_harness.py`.
- New delta spec for `dev-tasks`; no F58, F58 R1-F02, F61, D05, agent-doc,
  database, application, lane-topology, test-population, skip, coverage, or
  ceiling changes.
