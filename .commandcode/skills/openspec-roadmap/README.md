# OpenSpec Roadmap

Agent skill that sits **between a large PRD and many small OpenSpec changes**.

When you receive a PRD or epic that would normally become one oversized OpenSpec proposal, use this skill first: decompose the work, track slices in `openspec/roadmap.md`, then delegate each slice to the existing OpenSpec skills (`openspec-propose`, `openspec-apply-change`, `openspec-archive-change`). You orchestrate and keep state in sync; you do not replace the OpenSpec CLI.

## The gap you are filling

OpenSpec gates a **single** change well: proposal, design, tasks, implement, archive.

A PRD or epic is usually **many** changes — different priority, risk, and scope. Without a roadmap, you will either:

- propose one mega change that is hard to review and resume, or
- lose track of which slices were proposed, applied, or archived.

This skill adds **`openspec/roadmap.md`**: one markdown file listing slices and status. Each slice still gets its own change under `openspec/changes/`.

## Your responsibilities

| Situation | What to do |
|-----------|------------|
| PRD exists, no execution plan | **Bootstrap** → `openspec/roadmap.md` |
| Operator asks what is next | Pick highest-priority slice with status `Ready` |
| Slice is `Ready` | Run `openspec-propose` with the slice's **exact** `Candidate OpenSpec change id` → `openspec/changes/<id>/` |
| Change approved / implementing | Run `openspec-apply-change`; set slice `Applying` |
| Change complete | Run `openspec-archive-change`; set slice `Archived` |
| No formal PRD yet | Create a `PRD.md` file (or equivalent), then bootstrap |
| Legacy `TIMELINE_*` or `openspec/programs/` files exist | **Merge + delete** into fixed path `openspec/roadmap.md` — do **not** rename `TIMELINE_*` in place; see [REFERENCE.md](REFERENCE.md#legacy-migration-one-time) |

The roadmap is a **map and status board**, not a copy of `proposal.md` or `tasks.md`. Link paths; do not duplicate OpenSpec artifacts.

## Workflow

```
PRD or tracked issue
        ↓
openspec-roadmap  →  openspec/roadmap.md
        ↓
For each slice marked Ready:
        openspec-propose  →  openspec/changes/<id>/
        openspec-apply-change
        openspec-archive-change
        ↓
Update the roadmap after each step
```

You act as **roadmap coordinator**: decomposition and bookkeeping only.

## How to use command-style prompts

The skill supports concise command-style prompts that map to deterministic actions on `openspec/roadmap.md`.

Common commands:

- `status`: summarize counts by status, blockers, and top recommended next slices.
- `next:dry`: resolve the active slice and show exactly one next gate action (`propose` or `apply` or `archive`) without executing it.
- `next`: execute exactly one OpenSpec gate according to lifecycle state, run OpenSpec spec verification, fix issues if needed, then stop and update the roadmap.
- `add "<feature description>"`: add a new slice from intent. The skill generates slice id/title, fills minimum fields, and inserts it at the best position in execution order with rationale.
- `add-next "<feature description>"`: same as `add`, but force placement as the next executable work item when valid.
- `start <slice-id>`: move a selected slice into the next actionable lifecycle step.
- `update <slice-id> "<feature delta>"`: update feature scope for a non-executed slice, then re-evaluate dependencies and execution order.
- `block <slice-id> "<reason>"`: mark a slice as blocked with recommendation.
- `deprecate <slice-id> "<reason>"`: remove slice from active plan without deleting history, then reorder if needed.
- `restore <slice-id>`: reactivate a deprecated slice, reinsert in execution order, and reorder if needed.
- `reorder`: update Recommended Execution Order with a rationale note.

Notes:

- Prefer deprecating over deleting to preserve audit history.
- Any lifecycle-changing command must update `openspec/roadmap.md`.
- OpenSpec delegation remains mandatory (`openspec-propose` / `openspec-apply-change` / `openspec-archive-change`).
- `Candidate OpenSpec change id` must include the slice id as prefix: `<slice-id-lower>-<slice-title-kebab>`.
- On propose (`next`, `start`, or manual): pass that candidate id verbatim to `openspec-propose`; do not invent a slug from goal/PRD text.
- On `reorder`, `add`, `add-next`, `update`, `deprecate`, or `restore`, if a non-applied slice (`Ready` or `Spec Proposed`) already has a change folder and the computed id changes, rename the folder and update links in the roadmap.
- Temporary artifacts used for planning/apply support (for example `audit.md`) must live in `openspec/.temp_assets/`.
- During initialization/bootstrap, ensure `.gitignore` includes `openspec/.temp_assets/`.

## Example workflow with commands

Scenario: a PRD was decomposed into `openspec/roadmap.md`.

1. Check current state — `status`
2. Preview the next gate — `next:dry`
3. Execute one gate — `next` (repeat with review between gates)
4. Add in-flight work — `add "..."` or `add-next "..."`
5. Update scope — `update F05 "..."`
6. Deprecate outdated work — `deprecate R02 "..."`
7. Continue — `status`

## Parallelism and WIP

- multiple slices can be in `Spec Proposed` at the same time
- keep at most **2** slices in `Applying` globally
- keep at most **1** `Applying` slice in critical domains (for example checkout, auth, payments)
- keep `next` atomic (one gate for one slice)

## Paths you should know

| Path | Role |
|------|------|
| `openspec/roadmap.md` | Roadmap (single planning file) |
| `openspec/config.yaml` | Token limits and `openspec_roadmap` loading scope |
| `openspec/changes/<slice-id-lower>-<title-kebab>/` | OpenSpec artifacts per slice |
| `openspec/.temp_assets/` | Temporary roadmap support files (ignored) |

Slice prefixes: **F** (feature), **R** (refactoring), **T** (testing), **D** (documentation), optional **I** (infrastructure/tooling). Number sequentially (`F01`, `R02`, …).

Slice lifecycle: `Ready` → `Spec Proposed` → `Applying` → `Applied` → `Archived`, plus `Blocked`.

## Default operating profile

- Use concise roadmap entries by default.
- Enforce context loading from `openspec/config.yaml` (`openspec_roadmap`): roadmap, selected slice, linked change, directly referenced files.
- Do not load full PRD unless the slice is ambiguous.
- Do not use this flow for small work (quick bugfixes, one-file refactors, isolated UI copy edits, exploratory spikes).

## Repository setup (first use)

When this skill is adopted in a repo, document the roadmap layer in **repository agent instructions** (`AGENTS.md` or mirrors).

On bootstrap:

1. If legacy `TIMELINE_*` or `openspec/programs/` exist: **merge** into `openspec/roadmap.md`, **delete** legacy files (never rename-only); see REFERENCE.
2. Create or update `openspec/roadmap.md`.
3. Add or merge an **OpenSpec Roadmap** section in agent instruction files ([REFERENCE.md](REFERENCE.md#agent-docs-snippet)).
4. Point to the installed `openspec-roadmap` skill path in any task → skill routing table.

Reinstall note: remove any old `openspec-program` install path from agent skill directories; use `openspec-roadmap` instead.

## Files in this skill folder

| File | Use |
|------|-----|
| [SKILL.md](SKILL.md) | Procedures, modes, gates — primary instruction set |
| [REFERENCE.md](REFERENCE.md) | Roadmap template, migration, agent-doc snippets, checklists |
| [ROADMAP_SKELETON.md](ROADMAP_SKELETON.md) | Copy-ready default roadmap skeleton |
| [README.md](README.md) | Intent and mental model (this file) |

## Out of scope for this skill

- Replacing `openspec-propose`, apply, or archive.
- Storing full OpenSpec content in the roadmap.
- Writing verbose, spec-like prose in `openspec/roadmap.md`.

Full procedures: [SKILL.md](SKILL.md). Templates and instruction-file snippets: [REFERENCE.md](REFERENCE.md).
