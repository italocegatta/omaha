## Design

### Mechanism

The performance gate is a wall-clock measurement wrapper around the existing `uv run task test` invocation. No new tooling — agents already run the full suite. The gate adds time tracking and escalation logic to the existing test gate sections.

### Time Budgets

| Threshold | Meaning | Agent action |
|-----------|---------|--------------|
| < 3 min | Target | No action — proceed normally |
| 3–5 min | Warning | Log warning in report, proceed |
| > 5 min | Hard ceiling | **Block delivery/approval**, require investigation |

### Investigation Protocol (when > 5 min)

Agent MUST:

1. **Classify the bottleneck**: run `uv run task test --durations=20` to identify slowest tests.
2. **Check known patterns** against the optimization playbook:
   - Repeated DB setup → session-scoped fixtures (pattern from T18)
   - Serial tests that could parallelize → xdist worker isolation (pattern from T17)
   - Browser tests mixed into fast lane → lane separation (pattern from T16)
   - Markers wrong → fix `_INTEGRATION_PREFIXES` / `_UNIT_FILES` (pattern from T24)
   - Stale/slow tests → audit for redundancy (pattern from T21/T25)
3. **Propose specific optimizations** — never disable tests, never skip, never reduce coverage.
4. **Re-run and report** after optimization: new time, what changed, before/after comparison.

If agent cannot optimize below 5 min within the current slice scope, it MUST:
- Report the breach with full timing data
- Propose a follow-up slice for deeper optimization
- **Still block delivery** — the ceiling is absolute

### Enforcement Points

**apply.md** — after the "All green" outcome in the test gate:
- Measure time. If > 5 min → classify as blocked, enter investigation protocol.
- If 3–5 min → warning logged, proceed.

**review.md** — in the test gate verdict:
- Measure time. If > 5 min → automatic CHANGES_REQUESTED with reason "suite exceeds 5 min ceiling".
- If 3–5 min → warning in report, proceed to code review.

**openspec-apply-change SKILL.md** — in the "After ALL tasks complete" guardrail:
- Add note about time measurement and escalation.

**code-review SKILL.md** — in the "Test gate (mandatory)" section:
- Add time measurement and ceiling enforcement.

### What This Does NOT Do

- No new scripts, no new taskipy tasks, no new pytest plugins.
- No changes to test suite itself — this is agent-level enforcement only.
- No changes to `test-suite-quality` spec — the spec's "Delivery gate requires full suite green" already covers correctness; this adds the time dimension at the agent layer.

## Alternatives Considered

1. **pytest plugin with hard timeout** — rejected: adds complexity to test infrastructure, harder to tune per-environment.
2. **CI-level enforcement only** — rejected: user wants agents to catch this during local development, not just in CI.
3. **Soft guideline without blocking** — rejected: user explicitly wants "nunca entregar acima de 5 min".
