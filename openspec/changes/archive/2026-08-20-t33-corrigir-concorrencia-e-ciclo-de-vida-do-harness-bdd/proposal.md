## Why

The required BDD lane currently fails under concurrent expanded-lane execution: the
final T32 review recorded 47 failures and 4 passes, predominantly
`net::ERR_CONNECTION_REFUSED` against `127.0.0.1:8766`, while an isolated exact
scenario and the canonical full-suite receipt were green. The failure is therefore
owned by BDD harness/server/port lifecycle until evidence proves otherwise, and
must be diagnosed before any correction is selected.

## What Changes

- Capture an isolated BDD baseline and a controlled concurrent run of
  `test-bdd` with `test-t32-expanded`, preserving receipts, timestamps, child
  process state, port ownership, uvicorn logs, and test-DB state.
- Diagnose whether the refusal comes from a stale or falsely-ready port owner,
  BDD uvicorn death/teardown, runner process-group interference, or shared host
  resource pressure. Record symptoms, reproduction conditions, observability,
  falsification evidence, and minimum correction scope.
- Add focused harness contract coverage in the existing T29 harness test file
  before changing runtime harness code.
- Apply only the smallest correction at the boundary confirmed by the controlled
  test; preserve BDD serial execution, port assignments, DB ownership, and the
  T32 governance/pruning/population policy.
- Prove deterministic isolated and concurrent BDD/expanded execution, then the
  canonical full-suite green receipt within 300 seconds.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite-quality`: BDD harness delivery requires deterministic isolated and
  concurrent evidence without weakening lane membership or T32 governance.
- `e2e-fixture-isolation`: session-scoped test servers must expose a valid child
  readiness/ownership boundary and complete teardown without leaving the BDD
  port unavailable.
- `shared-test-support`: shared server lifecycle helpers must make startup and
  teardown failures observable and preserve lane-owned DB/port isolation.

## Impact

Expected implementation surface is limited to the task entrypoints in
`pyproject.toml`, BDD/server/browser harness helpers under `tests/`, and focused
contract tests in `tests/scripts/test_t29_harness.py`. `tests/conftest.py` and
`tests/bdd/step_defs/_workflows.py` are inspection boundaries whose marker and
workflow contracts must remain unchanged unless diagnosis proves a direct
harness defect. No production code, T32 artifact, pruning rule, lane population,
skip, xfail, or coverage policy changes are authorized.
