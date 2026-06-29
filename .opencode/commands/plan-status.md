---
description: Show where the plan stands — current phase, phase states, carrying-change states, and what's next
---

Report **Plan** status. Follow the **status** procedure in the `plan-workflow`
skill: read `PLAN.md`, read change state, then report the current phase, each
phase's state, the lifecycle state of each carrying change, and what's next.
Surface any drift you notice but don't fix it unasked.

## Active plan

```bash
test -f PLAN.md && head -40 PLAN.md || echo "No PLAN.md found. Run /plan-create to start one."
```

## Change engine state (OpenSpec)

```bash
openspec list --json 2>/dev/null || echo "(openspec not available or no changes)"
```