## Why

Current `apply` agent instruction correctly limits validation to focused tests, but `openspec-apply-change` still requires a full suite after every apply completion. This duplicates expensive browser lanes. A fresh routine currently passes in 271.58s runner / 272.48s wall-clock, safe below five-minute ceiling but above aspirational three-minute target.

## What Changes

- Resolve apply instruction conflict: `apply` and `openspec-apply-change` require focused, relevant tests only; neither runs full suite as normal apply work.
- Make `review` and `code-review` own exactly one full `uv run task test` invocation per review, record elapsed wall-clock time in review result, and preserve green-only approval.
- Treat 3–5 minutes as warning telemetry, not delivery failure.
- For a run over five minutes, prohibit approval; require measured-bottleneck investigation and remediation that preserves all tests and coverage. This D03 change records policy only; it does not schedule or perform immediate suite-speed work.
- Reference prior evidence and related slices T16–T18, T23, and T29 as context for future, measured remediation—not as automatic optimization work.

## Capabilities

### New Capabilities

- `agent-test-performance-gate`: Agent instruction contract separating focused apply validation from one timed full review suite, with non-waivable correctness and performance escalation rules.

### Modified Capabilities

None.

## Impact

- **Files touched**: `.opencode/agents/apply.md`, `.opencode/agents/review.md`, `.opencode/skills/openspec-apply-change/SKILL.md`, `.opencode/skills/code-review/SKILL.md` only.
- **No product-code, test-suite, taskipy, or coverage changes**: no contract test is necessary because this change governs Markdown instructions.
- **Baseline evidence**: fresh full routine passed in 271.58s runner / 272.48s wall-clock; fresh unit lane passed in 19.35s wall-clock; recorded browser lanes: e2e 195.31s, BDD 198.00s, visual 82.24s.
