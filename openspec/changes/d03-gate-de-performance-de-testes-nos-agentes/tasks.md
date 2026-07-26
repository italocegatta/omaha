## Tasks

- [ ] 1. Update `.opencode/agents/apply.md` — add "Performance gate" section after the existing "Test gate (ZERO TOLERANCE)" section. Content: time budgets (3 min target, 5 min ceiling), measurement instruction, escalation protocol when ceiling breaks (investigate, never disable), reference to T16-T18 as optimization patterns.

- [ ] 2. Update `.opencode/agents/review.md` — add "Performance gate" section after the existing "Test gate (ZERO TOLERANCE)" section. Content: same time budgets, measurement instruction, CHANGES_REQUESTED verdict when ceiling exceeded, warning log when 3–5 min.

- [ ] 3. Update `.opencode/skills/openspec-apply-change/SKILL.md` — add "Test performance gate" note in the guardrails section (after "After ALL tasks complete, run `uv run task test`"). Content: measure wall-clock, escalate if > 5 min, investigation playbook.

- [ ] 4. Update `.opencode/skills/code-review/SKILL.md` — add "Test performance gate" paragraph in the "Test gate (mandatory)" section (after the existing failure classification). Content: measure wall-clock, block approval if > 5 min, report timing data.

- [ ] 5. Verify all 4 files parse correctly (no broken markdown, sections render properly).
