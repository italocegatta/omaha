## Why

F58 Review R6 produced one canonical `uv run task test` attempt, but the receipt
was not trusted: integration reported `process PID not found`, visual failed
before `127.0.0.1:8768` readiness, and postflight found a pytest temp root that
the runner called clean. F58 code was absent from both failures. T34 is the
single bounded prerequisite for one trusted green F58 verification.

## Owner-authorized scope amendment — Taskipy compatibility boundary

The isolated audit attribution is now proven: external taskipy 1.14.1
`taskipy/task_runner.py:183-186` constructs `psutil.Process(process.pid)` after
its shell child has already exited while the runner is delivering SIGTERM. The
lookup raises `psutil.NoSuchProcess`, producing the historical `process PID not
found` failure. Owner authorizes absorbing this dependency-boundary diagnosis
and correction gate into T34; no new slice is created.

Amendment is limited to selecting a supported project-boundary remedy. It may
change `pyproject.toml` and its paired `uv.lock`, or a runner invocation/config
only when controlled evidence proves that boundary necessary. Installed
site-packages, taskipy source, F58/MyProfit/product code, tests' behavior,
lane topology, retries/skips/xfails, broad cleanup, I08, and T33 remain out of
scope. Existing T34 implementation and validation evidence remains historical
evidence and is not replaced.

## What Changes

- Capture bounded, run/lane-linked evidence for runner PID, PGID, parent/child
  lineage, poll/wait/exit events, visual server launch/readiness/port/log
  lifecycle, and exact pytest temporary ownership.
- Correct only defects confirmed by that evidence in the runner or shared test
  harness; preserve current taskipy commands, six lanes, fail-fast, coverage,
  skips, DB isolation, reconciliation, and the 300-second ceiling.
- Evaluate and, only if supported, apply the minimal Taskipy compatibility
  correction through project dependency metadata/lockfile or a proven runner
  invocation boundary. If no published supported Taskipy correction exists,
  retain the exact blocker and make no dependency, runner, or site-package edit.
- Reconcile each current-run pytest temporary root as `absent` or
  `owned-cleaned`; classify missing, pre-existing, foreign, contradictory, or
  untrusted evidence without adopting, deleting, or scanning broad `/tmp`.
- Add focused deterministic contracts to
  `tests/scripts/test_t29_harness.py` before focused validation.
- Execute exactly one authorized canonical `uv run task test` after focused
  repair and retain its complete receipt as acceptance evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `dev-tasks`: canonical runner receipts must prove current-run PID/PGID
  lineage, lifecycle outcomes, lane ownership, and temporary-resource
  reconciliation without weakening suite topology or cleanup safety.
- `shared-test-support`: server startup/readiness/teardown evidence must bind
  readiness to its spawned child and preserve exact lane ownership; DB/temp
  helpers must publish current-run temporary ownership receipts.

## Impact

Expected implementation surface is limited to
`scripts/run_full_suite.py`, `tests/support/server.py`,
`tests/support/browser.py`, `tests/conftest.py`, `tests/support/db.py`, and
focused contracts in `tests/scripts/test_t29_harness.py`. `pyproject.toml` or
another task/config file may change only if direct evidence proves a boundary
configuration defect. Amendment candidate files are `pyproject.toml` taskipy
dependency/settings/invocation entries, paired generated `uv.lock` entries, and
`scripts/run_full_suite.py` invocation code only when required by that evidence.
No installed site-package edit is permitted. No F58 implementation,
application route/model/template, production DB, seed, host resource, broad
`/tmp` cleanup, retry/skip/xfail, lane topology, T33 archive, or I08 archive
changes.

The existing `dev-tasks` and `shared-test-support` delta specs remain the
contract carriers for this amendment; they are amended below rather than
creating a new capability or slice.

## Owner-authorized scope amendment — exact runner temp-resource boundary

Owner authorizes narrowing T34's overly broad review preflight rule. The
amendment aligns written apply/review policy with the already-proven runner
boundary: only canonical runner-declared, exact run/lane temporary paths are
cleanup-relevant. It does not create a literal path allowlist and does not
weaken safety for a true foreign or unknown resource inside that declared
boundary.

For a declared exact path, an exact current-run receipt match with complete
ownership evidence is `owned-cleaned` after bounded cleanup; an exact absent
path is `absent`. A mismatch, unknown, foreign, contradictory, or incomplete
receipt/path inside the declared boundary remains untouched and blocks the
affected handoff or review verdict. An observed path outside the declared
runner boundary, including pre-existing `/tmp/pytest-of-juca`, is recorded as
preserved/non-target and cannot block review by itself. Independent process,
listener, DB, or declared-boundary safety findings retain existing blocking
behavior.

The amended policy contract must be named in and later applied through:
`.opencode/agents/review.md`, `.opencode/agents/apply.md`,
`.opencode/skills/openspec-apply-change/SKILL.md`, and
`AGENTIC_DEVELOPMENT.md`, while preserving the D05
`test-run-ownership-contract` boundary. No policy implementation occurs at
this proposal gate.

### What this amendment changes

- Replace review's blanket “any relevant unowned test-temporary resource blocks”
  wording with canonical exact runner-declared relevance.
- Keep exact current-run receipt matching, bounded cleanup, and blocking for
  mismatch/unknown/foreign state inside a declared run/lane boundary.
- Record out-of-bound temporary observations as preserved/non-target; they do
  not block alone and are never adopted, deleted, allowlisted, discovered by
  `pytest-of-*`, or used to infer a parent/broad `/tmp` cleanup target.
- Add focused acceptance for non-target preservation, exact owned cleanup, and
  untouched blocking mismatch/foreign resources.

### Amended allowed files

T34 implementation may touch only the four named policy documents, the two
existing T34 delta specs, and the already-mapped runner/test files required by
focused acceptance. D05 artifacts, stable specs, T33/I08 archives, I10
direct-dispatch policy, F58/product code, lanes, retries/skips/xfails, host
resources, and broad `/tmp` operations remain excluded. This amendment does
not authorize edits or test execution at proposal time.
