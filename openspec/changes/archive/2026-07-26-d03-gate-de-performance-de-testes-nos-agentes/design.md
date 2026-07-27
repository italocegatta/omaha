## Context

`apply.md` already says focused tests belong to apply and full-suite verification belongs to review. `openspec-apply-change/SKILL.md` conflicts by requiring `uv run task test` after all apply tasks. Full routine baseline is 272.48s wall-clock, so a five-minute delivery ceiling is safe now; under three minutes remains aspirational, not acceptance criteria.

## Goals / Non-Goals

**Goals:**

- Make focused test validation sole routine test responsibility of apply.
- Make review run exactly one full `uv run task test`, measure elapsed wall-clock from process start to finish, and include command, result, elapsed time, threshold classification, and verdict in report.
- Preserve zero-tolerance correctness: any red test blocks approval regardless of elapsed time.
- Treat 3–5 minutes as warning telemetry; over five minutes blocks approval and triggers evidence-led remediation.
- Require no test disabling, skipping, masked-pass mechanism, or coverage reduction to meet ceiling.

**Non-Goals:**

- No immediate test-suite speed optimization, test changes, taskipy changes, new timing tooling, or new test contract.
- No sub-three-minute acceptance gate or promise.
- No second normal full-suite execution by apply or review.

## Decisions

### D1 — Separate focused apply validation from full review validation

`apply.md` and `openspec-apply-change` will require smallest relevant test set derived from task, diff, and affected behavior. Remove skill's full-suite-after-all-tasks guardrail. Apply reports exact focused command and result; related failures remain delivery blockers.

`review.md` and `code-review` will require exactly one full `uv run task test` run before code review. Review captures wall-clock externally around this command without replacing taskipy command. No routine repeat occurs.

### D2 — Classify measured full-suite time without weakening correctness

| Measured wall-clock | Review action |
|---|---|
| Under 3m | Record timing; continue if all tests green and review clear. |
| 3m through 5m | Record warning telemetry and timing; continue if all tests green and review clear. |
| Over 5m | Cannot APPROVE, even if green; return `CHANGES_REQUESTED` with timing and bottleneck evidence. |

Any red test returns `CHANGES_REQUESTED` first; elapsed time never converts red result into approval.

### D3 — Over-ceiling investigation is measured and bounded

Review uses output from its one full run and existing measured lane evidence to identify bottleneck. Current baseline context is full 272.48s wall-clock; e2e 195.31s, BDD 198.00s, visual 82.24s, unit 19.35s. Report suspected slow lane/test only when evidence supports it. If exact per-test data is absent, require focused profiling/remediation in follow-up work rather than rerunning full suite.

Required remediation must preserve full test set and coverage. Future scoped work can assess patterns demonstrated by T16–T18 and T23: lane separation, safe parallelization, or repeated setup reduction. T29 establishes current routine population; it is not authorization to remove tests. D03 itself contains no optimization task.

## Risks / Trade-offs

- [Environment variance makes wall time noisy] → record actual wall-clock and classify thresholds; 3–5m remains telemetry only.
- [Over-five-minute result lacks per-test timing] → block approval, report measured lane evidence, request focused profiling; do not duplicate full suite.
- [Apply misses broad regression] → review retains exactly one green full-suite gate before any approval.
- [Pressure to meet ceiling reduces coverage] → explicit prohibition on skips, masked passes, test removal, or coverage reduction.

## Migration Plan

1. Align four instruction files with D1–D3.
2. No rollout, data migration, or rollback needed; revert documentation change if instructions prove unclear.

## Open Questions

None.
