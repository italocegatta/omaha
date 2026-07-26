# Agent Test Performance Gate

## Purpose

Time-budget enforcement for apply and review agents running the full test suite.

## Requirements

### Requirement: Agents enforce test suite time budget
The `apply` and `review` agents SHALL measure wall-clock time of `uv run task test` after every implementation pass or review. The time budget has two thresholds:
- **Target**: < 3 minutes. No action required.
- **Warning**: 3–5 minutes. Agent logs a warning in its report but proceeds.
- **Hard ceiling**: > 5 minutes. Agent MUST block delivery (apply) or approval (review).

#### Scenario: Suite runs under 3 minutes
- **WHEN** `uv run task test` completes in < 3 minutes
- **THEN** the agent proceeds normally with no performance notes

#### Scenario: Suite runs between 3 and 5 minutes
- **WHEN** `uv run task test` completes in 3–5 minutes
- **THEN** the agent logs a warning in its report
- **AND** proceeds with delivery or approval

#### Scenario: Suite exceeds 5 minute ceiling
- **WHEN** `uv run task test` completes in > 5 minutes
- **THEN** the `apply` agent blocks delivery and enters investigation protocol
- **AND** the `review` agent returns CHANGES_REQUESTED with reason "suite exceeds 5 min ceiling"

### Requirement: Agents investigate root cause when ceiling breaks
When the 5-minute ceiling is exceeded, the agent SHALL NOT disable tests, skip tests, or reduce coverage. The agent MUST:
1. Identify the slowest tests (via `--durations` or equivalent).
2. Check known optimization patterns: session-scoped fixtures, parallelization, lane separation, marker correctness, test redundancy.
3. Propose specific optimizations with before/after comparison.
4. If optimization is beyond current slice scope, propose a follow-up slice — but still block delivery.

#### Scenario: Agent identifies slow fixtures
- **WHEN** the ceiling breaks and repeated DB setup is the bottleneck
- **THEN** the agent proposes session-scoped fixtures (pattern from archived slice T18)

#### Scenario: Agent identifies serial tests that could parallelize
- **WHEN** the ceiling breaks and serial execution is the bottleneck
- **THEN** the agent proposes xdist worker isolation (pattern from archived slice T17)

#### Scenario: Agent never disables tests
- **WHEN** the ceiling breaks
- **THEN** the agent MUST NOT add `skip`, `xfail`, `pytest.skip`, or any masked-pass construct
- **AND** MUST NOT reduce the set of tests that run
