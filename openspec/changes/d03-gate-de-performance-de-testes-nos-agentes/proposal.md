## Why

Agent docs `apply.md` and `review.md` enforce a ZERO TOLERANCE test gate (all tests must pass), but say nothing about *how long* the suite may take. A 15-minute full suite silently wastes every apply/review cycle. The user wants agents to enforce a time budget: target < 3 min, hard ceiling 5 min — and when the ceiling breaks, agents must investigate and optimize, not disable tests.

## What Changes

- Add a **performance gate** section to `.opencode/agents/apply.md`: after running `uv run task test`, measure wall-clock time. If > 3 min, log a warning. If > 5 min, block delivery and require investigation.
- Add an equivalent **performance gate** section to `.opencode/agents/review.md`: same time budget, blocks APPROVED verdict when ceiling exceeded.
- Add a **test performance gate** section to `.opencode/skills/openspec-apply-change/SKILL.md`: guidance for the apply skill on what to do when the ceiling breaks (investigate root cause, optimize, never disable).
- Add a **test performance gate** section to `.opencode/skills/code-review/SKILL.md`: guidance for the review skill on how to report ceiling breaches.
- Reference existing archived slices T16-T18 as examples of valid optimization patterns (lane separation, session-scoped fixtures, parallelization).

## Capabilities

### New Capabilities

- `agent-test-performance-gate`: Agent-level enforcement of test suite execution time budgets (3 min target, 5 min hard ceiling) with mandatory investigation protocol when limits are breached.

### Modified Capabilities

None. The `test-suite-quality` spec already covers test gate semantics; this change adds a time dimension at the agent layer, captured as a new capability.

## Impact

- **Files touched**: 4 agent/skill markdown files (no code, no tests, no templates).
- **Risk**: None — agent docs only. No runtime behavior changes.
- **Precedent**: Extends existing ZERO TOLERANCE gate pattern with a time dimension.
