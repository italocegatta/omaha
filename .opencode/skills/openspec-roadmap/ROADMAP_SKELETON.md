# Roadmap

PRD: <issue URL, path, or "see conversation YYYY-MM-DD">

This roadmap is a short execution map used to generate OpenSpec changes per slice.
Keep entries concise. Do not duplicate proposal/design/tasks content.

## How To Use This Roadmap

1. Pick the highest-priority `Ready` slice.
2. Create/update one OpenSpec change for that slice.
3. Move lifecycle forward and update the progress log.
4. Keep scope limited to that slice.

## Status Model

`Ready` -> `Spec Proposed` -> `Applying` -> `Applied` -> `Archived` (plus `Blocked`)

## Parallelism and WIP limits

- Multiple slices may be `Spec Proposed` in parallel.
- Global cap: max **2** slices in `Applying`.
- Critical-domain cap (for example auth, payments, checkout): max **1** slice in `Applying`.
- `next` remains atomic: one command moves one lifecycle gate for one slice.

## Spec verification gate (mandatory)

- Run the repository OpenSpec spec verification command after each lifecycle gate.
- `propose` must be verified before `apply`.
- `apply` must be verified before `archive`.
- `archive` must be verified before selecting the next slice.
- If verification reports issues, resolve them and re-run verification before continuing.

## Slices

### T01 - <short title>
Status: `Ready`
Goal: <1-2 lines>
Candidate OpenSpec change id: `<slice-id-lower>-<slice-title-kebab>` (propose must use this exact id)
Spec link: `openspec/changes/<change-id>/`
Files:
- `path/to/file.ts`
Notes: <one short line or "none">
Progress:
- Proposed: pending
- Applying: pending
- Applied: pending
- Archived: pending

## Dependencies

### T01
Depends on: none
Blocks: T02
Can run in parallel: no

## Recommended Execution Order

1. T01 - <short title>
2. T02 - <short title>

## Compacted history

Keep only short archived summaries after the configured threshold.

- <slice-id> -> <outcome> -> <changed files> -> <validation>

## Post-implementation reality check

For every `Applied` slice, append:

- What changed from original plan:
- Unexpected issues:
- Follow-up needed:
