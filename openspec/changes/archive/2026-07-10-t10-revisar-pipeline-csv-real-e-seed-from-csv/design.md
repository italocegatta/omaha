## Context

Two CSV data paths exist in this repo:

1. **Seed path** (`scripts/seed_from_csv/`): reads `data/seed/{profile}_*.csv` triplets, validates cross-references + sum invariants, writes to DB in three modes (reset/upsert/diff). Contract documented in specs `csv-seed-internals`, `data-driven-seed`, `seeded-state`.

2. **Import path** (`src/omaha/csv_import.py` + `routes/imports.py`): parses broker-extract CSVs (real `posicao*.csv`), suggests class mapping, and commits positions via HTTP API. Tested by `tests/test_real_csv_flow.py` against fixture `data/seed/italo_positions.csv`.

Both paths currently green (38 test cases across 4 test files). No live failure. Purpose of this slice is contract-level audit: verify spec vs implementation vs CSV data are aligned.

## Goals / Non-Goals

**Goals:**
- Audit `scripts/seed_from_csv/` module layout, re-export surface, and per-concern split against `csv-seed-internals` spec — flag any drift.
- Audit `data/seed/` CSV triplet headers, validation rules, and data against `data-driven-seed` spec — flag any drift.
- Audit `test_real_csv_flow.py` fixture/assertion assumptions against `seeded-state` spec — flag any drift.
- Audit `data/seed/README.md` for accuracy against current spec + code.
- Audit `data/seed/fixtures/` directory — currently empty; document purpose or recommend removal.
- Audit `test_seed_from_csv.py` stale path reference (`SEED_FROM_CSV = .../seed_from_csv.py` vs current package `.../seed_from_csv/`).
- Fix minority side: if spec is wrong → correct spec; if code/CSV/README is wrong → correct code/CSV/README.
- Log any drift that requires a follow-up slice as a gap entry.

**Non-Goals:**
- No new capabilities, no new specs, no schema changes.
- No changes to `src/omaha/csv_import.py` or `routes/imports.py` logic.
- No browser/UI changes.
- No rebalance changes.
- No test count increase (existing tests should remain at same count unless a spec-correction adds an assertion).

## Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Scope boundary | Read-only audit + minority-side fix only | Prevents scope creep into feature work. If drift is found, fix the side with fewer changes (likely spec comment or README, not production code). |
| Stale `SEED_FROM_CSV` path | Fix if it points at old single-file name | The identifier in `test_seed_from_csv.py` references `scripts/seed_from_csv.py` — but the package is now `scripts/seed_from_csv/`. If the constant is unused, document and leave it; if it's used in test logic, correct the path. |
| `data/seed/fixtures/` empty dir | Leave in place but document | Removing it would be unrelated cleanup. Document in README or spec that the dir is reserved for non-standard fixture profiles. |
| Spec drift | Corrections go into delta specs within this change, then sync to main specs on archive | Standard OpenSpec workflow: delta spec captures what changed vs main spec; on archive, delta is merged into main. |

## Risks / Trade-offs

- **No live failure now** → the audit may find only cosmetic drift. That's acceptable: the slice's value is confidence that contract matches reality, not bug volume.
- **Minority-side fix ambiguity** → if spec and code both disagree but in different directions, err on side of spec (spec is contract; code that violates it is a bug). Document in gap log.
- **False positive from stale test** → `test_seed_from_csv.py` line 57 has `SEED_FROM_CSV = .../seed_from_csv.py` which may be a dead constant (the test uses `subprocess` with `python -m scripts.seed_from_csv`, not the path). Verify and fix if truly dead.
