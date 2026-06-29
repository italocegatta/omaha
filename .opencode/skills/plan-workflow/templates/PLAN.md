# <Program> — Implementation Plan

**Program:** <program-id> · **Status:** active · **Engine:** OpenSpec (`openspec/changes/`)
**Started:** <YYYY-MM-DD> · **Completed:** —

This is the **development roadmap** for <program>. It is a *coarse, phase-level*
tracker: each phase states a goal, its deliverables, an acceptance bar, and the
dependency order. The **granular task lists live in the Change(s)** that carry
each phase (`openspec/changes/<name>/tasks.md`) — this file points at them rather
than duplicating them, so the two never drift.

This is a **temporary, living document.** Check items off as phases land; revise
the plan as the work teaches you something. When the program is complete, archive
it to `plans/archive/`.

> **Sources of truth this plan serves — read these, don't restate them here:**
> <link the PRD / specs / design docs / architecture this program serves>

## How to read this

- `[ ]` not started · `[~]` in progress · `[x]` done.
- A phase is **done** only when its acceptance bar is met *and* the cross-cutting
  invariants below still hold.
- Each phase names the **Change(s)** that carry it, with a lifecycle state:
  *not yet proposed → proposed → applied → archived.*

## Sequencing strategy (decided)

<The decided approach and its rationale — why this order, what bends and why.
Link the architecture/design doc that justifies it. Keep it short; point, don't
restate.>

```
Phase 0  <title>   <one-line scope>
Phase 1  <title>   <one-line scope>
Phase 2  <title>   <one-line scope>
...
```

---

## Phase 0 — <title>

**Goal.** <one or two sentences: what this phase delivers and why.>

- [ ] <coarse deliverable — not a granular task list>
- [ ] <coarse deliverable>

**Acceptance.** <the bar that proves this phase is done.>

**Status:** not started

**Carried by:** <change-name> — not yet proposed

<!-- Divergences (record any deviation from a source of truth, with sign-off):
- _Divergence (recorded):_ <what & why; signed off>
-->

## Phase 1 — <title>

**Goal.** <…>

- [ ] <coarse deliverable>

**Acceptance.** <…>

**Status:** not started

**Carried by:** <change-name(s)> — not yet proposed

<!-- Add phases as needed. A phase may be carried by several changes; label them
freely ("Change A", "Slice ①") but the noun is always "change". -->

---

## Cross-cutting invariants (hold every phase)

A phase that violates one of these is not done, however green its own acceptance
bar:

- <invariant — e.g. an architectural rule, a contract that must not break>
- <invariant>

## Out of scope (do not pull forward)

<Things deliberately not in this program — explicit fast-follows or always-out —
so they don't get pulled in "because it seemed natural".>