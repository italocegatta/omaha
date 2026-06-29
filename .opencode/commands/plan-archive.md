---
description: Finalize a completed plan — move it to plans/archive/, optionally chain into a new plan
---

Archive the completed **Plan**. Follow the **archive** procedure in the
`plan-workflow` skill:

1. Verify the plan is complete (all phases `[x]`, or remaining work explicitly
   accepted as out-of-scope).
2. In `PLAN.md`, set **Status: complete** and stamp the **Completed** date.
3. Move it to `plans/archive/YYYY-MM-DD-<program>.md` (date = completion date,
   suffix = program identity). Create `plans/archive/` if needed.
4. Offer to chain into `/plan-create` for the next program.

## Active plan

```bash
test -f PLAN.md && head -8 PLAN.md || echo "No PLAN.md found — nothing to archive."
```