## Context

Debug SQLite databases, a stray pytest log, and an auto-generated fixture landed in the working tree from local debug sessions and BDD runs. `.gitignore` already excludes them (`data/*`, `*.log`, `data/seed/fixtures/*`), but the files remain on disk and confuse inventory tooling. Slice R01 (roadmap §Slices, lines 173-186) is the canonical entry for the wipe.

## Goals / Non-Goals

**Goals:**
- Delete the enumerated debug artefacts from the working tree.
- Verify `data/portfolio.db` is intact before and after the wipe.
- Land the change through the full OpenSpec loop so the housekeeping unit is auditable.

**Non-Goals:**
- Touching `.gitignore`, `.gitkeep`, source, tests, scripts, or any tracked file.
- Reorganising `backups/` (separate task `task backup` lists those — out of scope for R01).
- Introducing any new taskipy task for the purge (one-shot wipe, not recurring automation).

## Decisions

- **`rm` not `git rm`** — artefacts are untracked/gitignored; `git rm` would fail for files not in the index.
- **No `.gitignore` change** — existing rules already cover the patterns; adding more would be tautological noise.
- **Atomic change folder** — everything lives in `openspec/changes/r01-clean-orphaned-files-and-snapshots/`; the spec delta lives under `specs/dev-tasks/` per owner direction (tautology accepted).

## Risks / Trade-offs

- [Loss of useful debug DB] → Mitigated: artefacts are reproducible from `task db-seed-from-csv` or test setup; nothing references them.
- [Tautological spec delta] → Accepted by owner; documented in `proposal.md` Why section.