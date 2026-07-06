## Why

The repo accumulated debug SQLite databases (`probe*.db`, `test_*.db`), a stray pytest debug log, and a throwaway auto-generated fixture that leaked past the local `.gitignore`. None of these artefacts affect runtime behaviour, but they confuse `git status`, pollute `data/` inventory, and tempt future contributors to commit them by accident.

The slice `R01 - Limpar arquivos órfãos / dumps / snapshots antigos` (roadmap §Slices, lines 173-186) is the canonical home for this work. Owner accepted entering the OpenSpec loop with a tautological spec delta under `dev-tasks` so that the housekeeping is recorded as a unit of work rather than an ad-hoc wipe — the requirement duplicates what `.gitignore` already enforces, and that trade-off is explicit.

## What Changes

- Purge debug SQLite databases from the working tree:
  - `data/probe.db`, `data/probe2.db`, `data/probe3.db`, `data/probe_debug.db`, `data/probe_fix.db`, `data/probe_short_ttl.db`
  - `data/test_bdd.db`, `data/test_e2e.db`, `data/test_e2e_short_ttl.db`
- Purge `pytestdebug.log` from the repo root.
- Purge `data/seed/fixtures/auto_class.csv` (auto-generated fixture leftover).
- Confirm `data/portfolio.db` (canonical live DB) is untouched and still readable.
- No changes to `.gitignore` (existing rules already cover these patterns).
- No changes to `.gitkeep` files or any tracked source.

## Capabilities

### New Capabilities

(none — no new capability surface)

### Modified Capabilities

- `dev-tasks`: a new `Housekeeping purge of debug artefacts` requirement is appended, formalising the canonical live DB exception while existing `.gitignore` rules keep the purged patterns from re-entering the working tree after `git clean`.

## Impact

- Working tree only: deletes untracked/gitignored files. No source, no test, no runtime path touched.
- `data/portfolio.db` integrity verified before/after via `sqlite3 .tables`.
- Roadmap entry R01 lifecycle moves `Ready → Spec Proposed → Applying → Applied → Archived`.
