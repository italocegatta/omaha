# OpenSpec Program — domain terms

Workflow vocabulary for **`openspec-program`** in a **consumer repo**. Product language (features, domains, user-facing names) still comes from that repo’s root `CONTEXT.md`—do not merge the two.

## Language

**Roadmap register** (canonical)  
The single planning file at **`openspec/roadmap.md`** listing slices, priorities, and lifecycle status. It is not an OpenSpec change.

**Program register (timeline register)** — *legacy, migrate on bootstrap*  
Obsolete path: `openspec/TIMELINE_<context>.md` or `openspec/programs/<slug>.md`. On bootstrap, **merge** content into `openspec/roadmap.md` and **delete** legacy files; do **not** rename `TIMELINE_*` → `roadmap.md` without merging to the current roadmap format.  
_Avoid_: timeline (as product name), backlog file, keeping `TIMELINE_*` as a fallback after migration

**Slice**  
One decomposed unit of work inside the register, with an id (`F01`, `R02`, `T03`, …) and a candidate OpenSpec change id.  
_Avoid_: ticket, story (unless the consumer’s issue tracker uses those terms externally)

**Slice prefix**  
`F` (feature), `R` (refactor), `T` (testing/quality), `D` (documentation), `I` (infrastructure, optional). Part of the slice id, not a separate entity.  
_Avoid_: type label, workstream

**Slice status**  
Lifecycle on a slice: `Ready`, `Spec Proposed`, `Applying`, `Applied`, `Archived`, or `Blocked`. Distinct from issue labels or git branch state.  
_Avoid_: stage, phase (generic)

**OpenSpec change**  
The artifact set under `openspec/changes/<change-id>/` in a consumer repo (proposal, design, tasks, etc.). Created by OpenSpec tooling/skills, not by the program register.  
_Avoid_: spec folder, change package

**OpenSpec CLI skills**  
Upstream skills such as `openspec-propose`, `openspec-apply-change`, and `openspec-archive-change`. `openspec-program` orchestrates them; it does not replace them.  
_Avoid_: OpenSpec commands (ambiguous with the CLI binary)

**Repository agent instructions**  
Files in a consumer repo that tell every agent session how to work (commonly `AGENTS.md`, sometimes mirrored elsewhere). Document the program layer there when `openspec-program` is adopted.  
_Avoid_: relying on the skill folder alone without consumer-side routing

## Relationships

- A **program register** contains many **slices**; each implementable **slice** maps 1:1 to an **OpenSpec change** (except documented audit-only cases).
- **Slice status** advances as **OpenSpec CLI skills** run; the register is updated after each step.
- **Repository agent instructions** in the consumer repo point agents at installed skill paths and this workflow.

## Flagged ambiguities

| Term | Resolution |
|------|------------|
| “timeline” | Filename pattern `TIMELINE_<context>.md` or informal progress log—not a separate product entity. |
| “change” | Prefer **OpenSpec change** in consumer repos; prefer **skill** in the Skillbook catalog repo. |
| “PRD” | Product/requirements document in the consumer’s issue tracker or docs—not owned by Skillbook. |
