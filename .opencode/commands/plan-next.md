---
description: The driver — carry the plan to its next state (propose/apply/archive a change, close a phase, advance)
---

Drive the **Plan** forward. Follow the **next** procedure in the `plan-workflow`
skill — the stateful driver:

1. **Read state** from `PLAN.md` + the change engine via `openspec list --json`
   (per-change `status` + `completedTasks`/`totalTasks`; absent ⇒ archived);
   lightly reconcile obvious drift.
2. **Find position** — the first phase not `[x]`, and within it the first carrying
   change not yet `archived`.
3. **Perform the next transition**, showing the action + the command and
   confirming before real work or any decision:
   - *not yet proposed* → offer **propose** vs **explore**;
   - *proposed* → **apply**;
   - *applied* → **archive** (the change);
   - *change archived, phase done* → close the phase (`[x]`, stamp Status);
   - *all phases done* → suggest `/plan-archive`.
   Dispatch each engine handoff (`opsx-*`) to a **subagent** by default.
4. **Loop until it needs you** — auto-chain bookkeeping (archive a done change,
   close a phase, advance), but stop to confirm before propose/apply.
5. **Persist** every transition to `PLAN.md` so the plan stays resumable. Record
   any **divergence** surfaced while landing.

## Active plan

```bash
test -f PLAN.md && cat PLAN.md || echo "No PLAN.md found. Run /plan-create to start one."
```

## Change engine state (OpenSpec)

```bash
openspec list --json 2>/dev/null || echo "(openspec not available or no changes)"
```