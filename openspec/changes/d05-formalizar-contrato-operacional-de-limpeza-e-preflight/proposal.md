## Why

F61 and F58 reviews exposed unsafe ambiguity at full-suite boundaries: a
runner can leave PID/PGID, port, browser, log, or temporary-resource residue,
while cleanup and review may not know whether it is owned by current run.
D05 makes ownership, preflight, stop, and receipt semantics explicit before
I08 changes runner mechanics.

## What Changes

- Define run-owned resource ledger fields: PID, PGID, port, temporary resource,
  owner, start/end timestamps, and evidence/cleanup result.
- Require `apply` cleanup to act only on resources recorded as owned by its run;
  cleanup is idempotent and leaves unknown, pre-existing, or foreign residue
  untouched.
- Require `review` preflight before canonical `uv run task test` and postflight
  after it, with ownership attribution, residue classification, safe blocking,
  and a receipt before verdict.
- Define stop/escalation behavior for unknown ownership, stale state, vanished
  children, PID races, EPIPE, and incomplete cleanup; no broad repair attempt.
- Preserve six canonical lanes, fail-fast behavior, coverage, tests/skips,
  taskipy entrypoints, and the 300-second full-suite ceiling.
- Keep D05 protocol-only. Leave runner mechanics to I08 and do not alter F58,
  F58 R1-F02, F61, application code, tests, or database state.

## Capabilities

### New Capabilities

- `test-run-ownership-contract`: operational ownership ledger, bounded cleanup,
  review preflight/postflight, residue classification, safe stop policy, and
  receipts for apply/review test execution.

### Modified Capabilities

- None. Existing performance and suite contracts remain normative; this change
  adds a separate operational ownership contract without changing lane,
  coverage, fail-fast, skip, or duration requirements.

## Impact

- Documentation targets for apply/review workflow:
  `.opencode/agents/apply.md`, `.opencode/agents/review.md`,
  `.opencode/skills/openspec-apply-change/SKILL.md`, and
  `AGENTIC_DEVELOPMENT.md`.
- New OpenSpec delta/stable capability under the D05 change folder; no runtime,
  runner, taskipy, test, application, database, F58, F61, or I08 artifacts.
- Proposal validation is bounded to OpenSpec artifact/change and stable-spec
  validation plus scope/whitespace inspection. No implementation tests run.
