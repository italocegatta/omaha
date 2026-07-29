# OpenSpec Roadmap Register — Reference

Use this file when bootstrapping `openspec/roadmap.md` or adding slices.
All guidance in this reference must stay token-saving and operationally concise.

---

## `openspec/config.yaml` baseline

Use this baseline for token and loading limits.
Treat this config as operational guidance only: do not regenerate, rewrite, or recreate OpenSpec specs from `openspec/config.yaml`.

```yaml
openspec_roadmap:
  mode: default
  register: openspec/roadmap.md
  token_budget:
    max_input_tokens: 18000
    reserved_output_tokens: 4000
  context_loading:
    include_only:
      - roadmap_register
      - selected_slice
      - linked_openspec_change
      - directly_referenced_files
    load_full_prd_when: "slice_is_ambiguous"
  pruning:
    compact_history_after_archived_slices: 8
  quality_gate:
    applied_requires:
      - tests_pass
      - affected_specs_updated
      - no_unrelated_files_changed
      - acceptance_verified
```

---

## Temporary assets policy

When roadmap work requires temporary artifacts (for example `audit.md`, draft notes, interim checklists, or scratch outputs), store them under:

- `openspec/.temp_assets/`

Rules:

- Do not place temporary roadmap assets in `openspec/changes/` or alongside `openspec/roadmap.md`.
- Ensure `.gitignore` contains `openspec/.temp_assets/` during bootstrap/initialization.
- Treat this folder as ephemeral working state for definition/apply support files.

---

## Roadmap template (default)

The default template is maintained only in [ROADMAP_SKELETON.md](ROADMAP_SKELETON.md).
Do not duplicate or rewrite that template in this reference.
When needed, link to it and keep this document focused on rules, constraints, and checklists.

---

## Legacy migration (one-time)

When bootstrapping or refactoring a consumer repo, migrate obsolete planning files into the **single canonical roadmap** at **`openspec/roadmap.md`**. This path is fixed: there is no `roadmap_<context>.md` and legacy filenames must not survive under another name.

### Do not rename in place

| Wrong | Right |
|-------|-------|
| `git mv openspec/TIMELINE_foo.md openspec/roadmap.md` when content is still the old timeline layout | Merge slice sections into `openspec/roadmap.md` using the current roadmap skeleton, then delete `TIMELINE_foo.md` |
| Keep `TIMELINE_*` “for reference” or read it when `roadmap.md` is missing | One source of truth: `openspec/roadmap.md` only; delete legacy files after merge |
| Multiple planning files (`roadmap.md` + `TIMELINE_bar.md`) | One `openspec/roadmap.md`; merge all legacy sources into it |

Renaming without merge leaves obsolete section structure, wrong agent-doc references, and split planning state. **Merge + delete** is mandatory.

### Migration procedure

1. **Discover** — list `openspec/TIMELINE_*.md`, `openspec/programs/*.md`, and whether `openspec/roadmap.md` already exists.
2. **Target** — create or open `openspec/roadmap.md` (canonical path only).
3. **Merge** — copy slice blocks, statuses, candidate change ids, spec links, and progress from each legacy file into the roadmap; normalize to the lite slice format in [ROADMAP_SKELETON.md](ROADMAP_SKELETON.md).
4. **Reconcile** — one PRD link block, one **Recommended Execution Order**, one **Compacted history** (see merge order below). On id collision across files (e.g. two `F01`), renumber or prefix and fix linked `openspec/changes/` references if needed.
5. **Delete legacy** — remove every `TIMELINE_*` and `openspec/programs/*.md` file from the repo after merge verifies in `roadmap.md`.
6. **Update agent docs** — replace `openspec-program`, `TIMELINE_*`, “program layer”, and legacy paths in `AGENTS.md` (and mirrors) with `openspec-roadmap` and `openspec/roadmap.md`.
7. **Verify** — confirm no `TIMELINE_*` or `openspec/programs/` paths remain; agents must not read them again.

| Legacy path | Action |
|-------------|--------|
| `openspec/TIMELINE_<context>.md` | Merge into `openspec/roadmap.md`, then **delete** (not rename) the legacy file |
| `openspec/programs/<slug>.md` | Merge into `openspec/roadmap.md`, then **delete** (not rename) the legacy file |
| Multiple legacy files | Merge all into one `openspec/roadmap.md`; resolve slice id collisions; manual review required |
| `openspec/roadmap.md` already present | Merge legacy into existing roadmap; do not add parallel planning files |
| `AGENTS.md` and mirrors | Replace references to `openspec-program`, `TIMELINE_*`, or “program layer” with `openspec-roadmap` and `openspec/roadmap.md` |

Suggested merge order:

1. PRD links at top — if several PRDs, use a bullet list.
2. Union all **Slices** sections.
3. Rebuild one **Recommended Execution Order**.
4. Merge **Compacted history** entries.

**After migration:** no fallback reads of `TIMELINE_*` or `openspec/programs/`. If bootstrap finds legacy files, migration runs first; do not skip by creating a fresh empty `roadmap.md` beside them.

---

## Slice field reference

| Field | Required | Notes |
|-------|----------|-------|
| Status | Yes | One lifecycle value |
| Goal | Yes | One short outcome statement |
| Candidate OpenSpec change id | Yes | format `<slice-id-lower>-<slice-title-kebab>`; 1:1 with change dir |
| Spec link | Yes | Path to the OpenSpec change dir |
| Files | Yes | 1-5 starting files |
| Notes | Optional | Keep to one short line |
| Progress | Yes | Update at each lifecycle step |

Do not add full-spec style sections by default.

### Slice ID prefixes

| Prefix | Use |
|-------|-----|
| `F` | Product feature slices |
| `R` | Refactoring slices (no intended behavior change) |
| `T` | Testing and quality slices |
| `D` | Documentation-only slices |
| `I` | Infrastructure/tooling slices (optional) |

Use sequential numbering within each prefix (`F01`, `R02`, ...).

### Candidate change id format

- Derive change ids from the slice id and title.
- Required format: `<slice-id-lower>-<slice-title-kebab>`.
- Example: `T10 - audit legacy test harness` -> `t10-audit-legacy-test-harness`.
- Keep `Spec link` synchronized with the same id under `openspec/changes/`.
- For non-applied slices only (`Ready`, `Spec Proposed`), if title/order updates imply a new id and a change folder already exists, rename that folder and update references in the roadmap.

### At propose (mandatory)

When a slice is `Ready` and you delegate to `openspec-propose`:

1. Use the slice's `Candidate OpenSpec change id` from `openspec/roadmap.md` **verbatim** as `<change-id>`.
2. Create or target `openspec/changes/<change-id>/` — do not derive a different slug from goal, PRD, or chat text.
3. If the candidate id is missing or wrong, fix the roadmap (recompute `<slice-id-lower>-<slice-title-kebab>`) before proposing.
4. After propose, `Spec link` and progress log must reference the same folder path.

Example: `### T09 - Location Search And Proposal Add Discovery` → `t09-location-search-and-proposal-add-discovery` → `openspec/changes/t09-location-search-and-proposal-add-discovery/`.

---

## Definition of done for `Applied`

A slice cannot be marked `Applied` unless:

- tests pass
- affected docs/specs are updated
- no unrelated files changed
- spec acceptance criteria are verified

---

## Parallelism and WIP limits

OpenSpec roadmaps can run multiple slices in parallel, with controlled implementation concurrency.

- Multiple slices may stay in `Spec Proposed`.
- Keep a maximum of **2** slices in `Applying` globally.
- For critical domains (for example auth, payments, checkout), keep a maximum of **1** slice in `Applying`.
- Keep lifecycle transitions atomic: one command should move one gate for one slice.

Why this matters:

- prevents review and CI bottlenecks from too many active branches
- reduces merge conflicts and rework from long-running concurrent implementation
- improves completion rate by pushing slices to `Archived` faster
- preserves clear per-slice auditability

---

## Mandatory spec verification between gates

Always run the repository OpenSpec spec verification command between lifecycle gates and fix any issues before moving forward.

- after `propose` and before `apply`
- after `apply` and before `archive`
- after `archive` and before picking the next slice

Verification failures are blocking: resolve issues, re-run verification, then continue.

---

## Do-not-use gate

Do not use the roadmap flow for:

- bugfixes under 30 minutes
- isolated copy/UI changes
- one-file refactors
- exploratory spikes

---

## Scope changes in roadmap

### Add a new in-flight feature

- Add a new `### <ID> - <Title>` block with default roadmap fields.
- Default status is `Ready` unless implementation already started.
- Insert item in `## Recommended Execution Order` at the best position, not automatically at the end.
- Choose insertion position using:
  - dependency readiness (must come after required prerequisites)
  - risk reduction and unblock potential
  - expected leverage for upcoming slices
  - user urgency constraints, if provided
- Record a short rationale near the updated execution order (for example: "Inserted F05 after R03 to reuse new interfaces and reduce rework before F06").
- If insertion changes what should run next, explicitly state the new next slice.

### Add-next for immediate placement

- Use `add-next <slice-id> "<title>"` when the user explicitly wants the new slice as next work.
- Insert the new slice at the nearest valid next position.
- If dependencies block immediate placement, place at the earliest valid slot and explain the blocker.
- Record a short rationale near the updated execution order.

### Deprecate instead of delete

- Keep the slice block in place.
- Add `Deprecated on YYYY-MM-DD: <reason>` in `Notes`.
- Remove from active `Recommended Execution Order`.
- Add a compacted-history entry if needed.

### Restore a deprecated slice

- Add `Restored on YYYY-MM-DD` note.
- Set status back to actionable value (usually `Ready`).
- Reinsert into `Recommended Execution Order`.

Hard deletion is allowed only when explicitly requested by the user.

---

## Progress log patterns

**After propose:**

```markdown
- Proposed: `openspec/changes/<change-id>/`
```

**After apply:**

```markdown
- Applying: `<branch or agent context>`
- Validation: `<command>` -> `<result>`
- Applied: `<key files changed>`
```

**After archive:**

```markdown
- Archived: `openspec/changes/archive/YYYY-MM-DD-<change-id>/` on `YYYY-MM-DD`
```

Use `pending` for steps not yet reached.

---

## Bootstrap checklist

```
- [ ] Legacy TIMELINE_* / openspec/programs/ merged into `openspec/roadmap.md` and deleted (not renamed in place)
- [ ] `openspec/config.yaml` contains openspec_roadmap mode/token/loading limits
- [ ] `openspec/roadmap.md` exists
- [ ] `.gitignore` contains `openspec/.temp_assets/`
- [ ] PRD/issue link at top
- [ ] How-to + status model sections
- [ ] Lite slices only (concise fields)
- [ ] Candidate change ids are unique and follow `<slice-id-lower>-<slice-title-kebab>`
- [ ] Dependencies map filled for active slices
- [ ] Recommended execution order
- [ ] Compacted history section present
- [ ] Post-implementation reality check section present
- [ ] WIP limit policy documented (`Applying` max and critical-area cap)
- [ ] Mandatory OpenSpec spec verification gate documented between propose/apply/archive
```

---

## Agent docs snippet

Insert or merge into the repo’s primary agent instruction file (usually `AGENTS.md`), under or beside existing OpenSpec rules. Mirror the same block in any secondary entrypoints that load agent rules for that repository. Replace `<skill-path>` with the installed path.

### Section: OpenSpec Roadmap (merge into OpenSpec workflow)

```markdown
## OpenSpec Roadmap (PRD → multiple changes)

Use this layer when a PRD or epic would otherwise become one oversized OpenSpec change.

| Step | What | Where |
|------|------|--------|
| 1 | PRD or issue | Issue tracker / `PRD.md` file |
| 2 | Decompose into prioritized slices | `openspec/roadmap.md` |
| 3 | Per slice with status `Ready` | `openspec-propose` → `openspec/changes/<Candidate OpenSpec change id>/` (exact id from roadmap) |
| 4 | Implement | `openspec-apply-change` (slice → `Applying` → `Applied`) |
| 5 | Complete | `openspec-archive-change` (slice → `Archived`) |

**Rules**

- `openspec/roadmap.md` is the planning file only — do not copy `proposal.md` / `design.md` / `tasks.md` into it.
- Implementable slices are **1:1** with OpenSpec changes (`Candidate OpenSpec change id`).
- On propose, pass the slice's `Candidate OpenSpec change id` verbatim to `openspec-propose` — format `<slice-id-lower>-<slice-title-kebab>`; never invent a folder name from goal/PRD text.
- Slice lifecycle: `Ready` → `Spec Proposed` → `Applying` → `Applied` → `Archived` (`Blocked` when decisions are pending).
- Keep `next` atomic (one gate per command) and enforce `Applying` WIP limits from the roadmap policy.
- Run OpenSpec spec verification after each lifecycle gate and fix issues before the next gate.
- Pick the next slice by priority and recommended execution order in the roadmap.
- Update the roadmap after every propose, apply, and archive step.
- Keep roadmap entries concise and operational.
- Enforce context/token limits via `openspec/config.yaml` (`openspec_roadmap`).

**Skill**

| Task | Skill file |
|------|------------|
| Bootstrap roadmap, add slices, update lifecycle | `<skill-path>/SKILL.md` |
| Roadmap template and checklists | `<skill-path>/REFERENCE.md` |
```

### Routing table variant (GitNexus-style repos)

If `AGENTS.md` already uses a task → skill file table, append:

```markdown
| Decompose PRD/epic into OpenSpec slices | `<skill-path>/SKILL.md` |
| Pick next roadmap slice / update slice status | `<skill-path>/SKILL.md` |
```

### Agent docs checklist

```
- [ ] Primary agent instruction file contains OpenSpec Roadmap subsection
- [ ] Secondary entrypoints mirrored where the repo uses them
- [ ] Skill path in table matches install location (`openspec-roadmap`)
- [ ] Roadmap path documented as `openspec/roadmap.md`
- [ ] No duplicate conflicting OpenSpec instructions
```

---

## Doc-only / audit slices

For inventory or harness-audit work:

- Candidate id often `audit-<topic>` or `reclassify-<topic>`.
- Likely verification: documentation and planning; follow with per-cluster OpenSpec changes if needed.
- May remain a single change for the audit slice itself.
