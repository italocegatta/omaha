# Plan — Design Rationale

This is the ratified model: vocabulary, discipline rules (R1–R7), artifact shape,
and lifecycle. Adapted from
[mattmccray/plan DESIGN.md](https://github.com/mattmccray/plan/blob/master/DESIGN.md).
**When the skill, commands, or template disagree with this file, fix them — don't
let them drift.**

## Core claim

OpenSpec (and similar change engines) own the **unit of work** — one change,
propose → apply → archive. They do not own the **program**: a phased roadmap that
sequences many changes. Plan fills that gap with one human-readable file
(`PLAN.md`) that sequences **Phases**, each carried by one or more **Changes**.

The two layers never duplicate. Plan points at changes; it never restates their
task lists. The PLAN.md document is the state — everything needed to resume
lives in PLAN.md itself.

## Vocabulary

| Term | Definition |
| --- | --- |
| **Plan** | The roadmap (`PLAN.md`); one active plan per program. |
| **Phase** | A coarse, sequenced chunk: goal + deliverables + acceptance + status. |
| **Change** | A unit of work that **carries** a phase's tasks (OpenSpec by default). |
| **Invariants** | Cross-cutting definition-of-done across every phase. |
| **Divergence** | A recorded, signed-off deviation from a source of truth. |

Linking verb: **carry** — "a phase is carried by changes."

## Discipline rules

- **R1 Coarse, never duplicated.** Granular tasks live only in the carrying
  change. The plan states goal / deliverables (coarse) / acceptance / status.
- **R2 Point, don't restate.** Link sources of truth; never re-explain them.
- **R3 Every phase maps to changes.** Each named with a lifecycle state.
- **R4 Status reflects reality.** Keep current so the plan is resumable.
- **R5 Divergences recorded, never silent.** Inline, with rationale + sign-off.
- **R6 Invariants are a DoD overlay.** Breaking one = phase not done.
- **R7 Plans are kept.** Archive completed, never delete.

## Lifecycle

```
Active plan     = PLAN.md at repo root
Archived plan   = plans/archive/YYYY-MM-DD-<program>.md
Change engine   = declared in PLAN.md header (default: OpenSpec)
Change states   = not yet proposed → proposed → applied → archived
Phase states    = [ ] not started · [~] in progress · [x] done
```

Completed plans are kept, not deleted — they're the historical record of why a
program was built the way it was.

## Composability

Plan does not hard-code OpenSpec: the plan declares its change engine in its
header, and the workflow drives whatever is declared (defaulting to OpenSpec). It
is one tool in a constellation of single-purpose, AI-first workflow tools —
adopt it alongside a change engine and (optionally) an issue inbox, picking only
what a project needs. No central store, no dispatcher; each tool owns its own
file and its own slash namespace.

## Engine seam

The plan's header declares its change engine (`Engine: OpenSpec`). Drive whatever
is declared; default to OpenSpec. To carry a phase, propose / apply / archive a
change via that engine.

**Engine handoffs run in a subagent by default.** The driver session stays light;
the subagent does the work and returns a concise summary + resulting state.