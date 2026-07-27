## 1. Align apply validation guidance

- [ ] 1.1 Update `.opencode/agents/apply.md`: retain mandatory focused relevant tests and green-related-test handoff; explicitly state full-suite timing/verification belongs only to review and is not run after apply passes.
- [ ] 1.2 Update `.opencode/skills/openspec-apply-change/SKILL.md`: remove conflicting full-suite-after-all-tasks guardrail; require focused relevant test command/result reporting, preserving blocked handoff for related red tests.

## 2. Add timed full-review gate

- [ ] 2.1 Update `.opencode/agents/review.md`: require exactly one full `uv run task test` run per review; record elapsed wall-clock, command, result, classification, and warning telemetry for 3–5m; retain no-approval for any red test.
- [ ] 2.2 Update `.opencode/skills/code-review/SKILL.md`: align mandatory test gate with one timed full suite and same report fields; over five minutes returns `CHANGES_REQUESTED`, with measured-bottleneck evidence and remediation requirement that preserves all tests and coverage.

## 3. Verify instruction contract

- [ ] 3.1 Inspect four changed Markdown files for consistent ownership: apply uses focused relevant tests; review owns one full suite; no normal duplicate full-suite run remains.
- [ ] 3.2 Confirm 3–5m is warning telemetry, over five minutes cannot approve, red tests cannot approve, and no instruction permits disabling tests or reducing coverage.
