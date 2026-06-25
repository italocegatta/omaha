## Context

The Omaha dev DB is seeded by two orthogonal scripts:

| Script | What it does | Mode |
|---|---|---|
| `src/omaha/seed.py` | Creates `User` + `Profile` rows for Italo & Ana | Idempotent, non-destructive |
| `scripts/dev_reset.py` | Wipes Italo's `positions` / `import_previews` / `assets` / `asset_classes` and reseeds 6 classes from a hardcoded `CLASS_SPECS` list | Destructive, but `--profile italo` is hardcoded too |

`dev_reset.py` is the "data setup" tool used to bootstrap a fresh dev
DB before manual import-flow testing (`db-reset` taskipy task). It is
also the only place that materialises class targets — the
`Asset.target_pct` column is created in the 0006 migration and
populated via the inline editor at runtime, but never at seed time.
Positions are NOT seeded at all; they only come from the runtime
broker-CSV import flow.

**State of the world right now:**

```
┌──────────────────────────────────────────────────────────────────────┐
│ Reference (xlsx + posicao)        │  Code (dev_reset.py)              │
├────────────────────────────────────┼───────────────────────────────────┤
│ RF Dinâmica  25%                   │  RF Dinâmica  26%   ← divergente  │
│ RF Pós       20%                   │  RF Pós       16%   ← divergente  │
│ Internacional 18%                  │  Internacional 21%  ← divergente  │
│ FII          15%                   │  FII          15%   ✓              │
│ Cripto        8%                   │  Cripto        8%   ✓              │
│ Ações        14%                   │  Ações        14%   ✓              │
│ per-asset target %  (Italo: 47,    │  (não populado)                   │
│   Ana: 46)                         │                                   │
│ positions (Italo: 48, Ana: 43)     │  (não populado)                   │
│ Ana profile (6 classes, 46 assets) │  (não existe — só Italo)          │
└────────────────────────────────────┴───────────────────────────────────┘
```

The xlsx and posicao CSVs are in a sibling project
(`~/github/investing/`), not under version control here. The user
wants the **editable text source of truth** to live in the omaha
repo so future allocation / position edits don't require opening
Excel or re-importing broker CSVs. The end state the user wants:
log into Italo's profile, see 6 classes with their target bars, 47
assets with their per-class `target_pct`, and 48 positions rendered
against the broker truth. Same for Ana.

## Goals / Non-Goals

**Goals:**

1. Move class + asset allocation out of Python literals and into
   per-profile CSV files under `data/seed/`.
2. Bootstrap the CSVs from the canonical xlsx (classes + assets)
   and posicao (positions) references for both Italo and Ana
   during the apply phase — read the source files one final time,
   hand-derive the CSVs, then commit. The xlsx and posicao CSVs
   are never accessed again after this change is merged.
3. Replace `scripts/dev_reset.py` with `scripts/seed_from_csv.py`
   that reads the CSV triplet (classes + assets + positions),
   validates `sum == 100` per class and per asset group,
   cross-references positions against assets, and writes
   idempotently in `--mode {reset,upsert,diff}`.
4. Add a small integration test that locks the contract: the six
   CSVs round-trip into the DB cleanly, sum-violating CSVs are
   rejected, orphan positions are rejected, the non-tradeable
   `qty=1` sentinel preserves current_value, and `--mode reset`
   is idempotent across all three layers.
5. Update `AGENTS.md` to permit asset AND position seeding via the
   CSV path exclusively, and wire the new files into the marker
   allow-list so `task test-integration` covers the new test.

**Non-Goals:**

- Adding `currency` / `fl_comprar` / `fl_vender` / `nm_arca` columns
  to the `Asset` model. The xlsx has them, the model doesn't, the
  apply phase drops them on the floor. A separate change can extend
  the schema; this one stays inside the existing model surface.
- Auto-running seed on app startup. `db-seed-from-csv` remains an
  explicit task.
- Multi-profile CSV (one CSV triplet per profile, not a single
  global triplet). Profiles are an auth boundary; per-profile files
  keep the data decoupled.
- Nullable `qty` / `avg_price` on `Position` (would let us model
  non-tradeable items honestly). The `qty=1` sentinel is the
  workaround for the existing NOT NULL schema.
- Multi-broker per asset (the seed produces one `Position` per asset
  with `broker_ticker = asset_name`). The import flow still exists
  for cases where the user wants to track the same asset across
  brokers.

## Decisions

### Decision 1: Per-profile CSV triplet (`{profile}_classes.csv` + `{profile}_assets.csv` + `{profile}_positions.csv`), not a single global set

- *Rationale:* Profiles are an auth boundary; per-profile files match
  the existing data model (`AssetClass.profile_id`, `Asset` is
  indirected via class → profile, `Position` is indirected via asset
  → class → profile). They also let Ana's allocation evolve
  independently of Italo's without a merge conflict on every edit.
- *Alternatives considered:*
  - **Single global set with a `profile` column on every row.**
    Rejected: it puts the seed in conflict with the per-profile
    auth model. A single edit mistake in one profile could leak
    data into the other.
  - **YAML instead of CSV.** Rejected: the user explicitly asked for
    CSV for manual editing.

### Decision 2: Three CSVs per profile (not one)

- *Rationale:* Classes, assets, and positions have different
  validation rules (per-profile sum, per-class sum, no sum) and
  different lifecycles (class list is stable, asset list churns as
  the user imports new tickers, position list churns daily as the
  broker updates prices). Splitting them keeps each CSV's column
  set and validation simple.
- *Alternative:* Single CSV with a `kind` column (`class` / `asset`
  / `position`). Rejected: complicates validation (group by `kind`
  and pivot) and makes the file harder to grep / sort / diff.

### Decision 3: Three modes — `reset` (default), `upsert`, `diff`

- *Rationale:* The current `dev_reset.py` is destructive but the
  user edits the CSV by hand. Two safe scenarios:
  1. "I changed `target_pct` of one class, I want just that one
     updated" → `upsert`.
  2. "Show me what would change before I commit" → `diff`.
  `reset` matches the current behavior; `upsert` and `diff` are
  additive safety nets.
- *Alternative:* Only `reset`. Rejected: the user will edit the CSV
  repeatedly; an always-destructive seed would wipe positions they
  hand-curated in between.

### Decision 4: `reset` keeps the same destructive wipe as `dev_reset.py`

- *Rationale:* The `db-reset` task is already documented as
  "wipe + reseed" and tests rely on the wipe semantics. Changing the
  default to `upsert` would silently let pre-existing assets and
  positions survive and break the test contract.
- *Alternative:* Default to `upsert`. Rejected: surprising. The
  `dev_reset.py` semantics are well-known. `upsert` is the
  opt-in path for "I edited the CSV, apply it".

### Decision 5: `Asset.target_pct` populated with 0 for items the xlsx flags as non-tradeable

- *Rationale:* The xlsx has 13 items for Italo with `pc_ativo_alocacao_categoria = 0`
  (CDBs, RDBs, "Conta corrente em dólar Avenue"). The model has no
  "tradeable" flag, so the only representation is `target_pct = 0`.
  These rows DO appear in the user's reference (they are existing
  positions with no current allocation target) and dropping them
  would make the seed incomplete vs the xlsx.
- *Alternative:* Skip rows with `pc = 0`. Rejected: a CDB the user
  holds is a real position that should appear in the asset list
  with `target_pct = 0` (so the import matcher can link broker CSVs
  to it). The per-class sum still validates because `0 + 25 + 25 = 50`
  is the same modulo-zero as `25 + 25 = 50` for the validator.
- *Validator behaviour:* `validate_target_pct_sum([0, 0, 25, 25, 50])`
  still returns `(True, None)` because `sum == 100`. The validator
  does not need to special-case zeros.

### Decision 6: Non-tradeable positions use the `qty=1, avg_price=total_investido, current_price=total_atual` sentinel

- *Rationale:* The dashboard computes `current_value = qty ×
  current_price` and `invested = qty × avg_price`
  (`src/omaha/routes/pages.py:188`). For tradeable items, the
  posicao CSV provides `qty`, `avg_price`, and `current_price`
  directly. For non-tradeable items (RDB, CDB), the posicao CSV has
  `qty="-"` and `avg_price="-"` but does carry `total_investido`
  and `total_atual` — the user knows the position's R$ value but
  not its units. Using the sentinel `qty=1` and treating
  `total_investido` as `avg_price` and `total_atual` as
  `current_price` makes both dashboard derivations correct:
  - `current_value = 1 × total_atual = total_atual` ✓
  - `invested = 1 × total_investido = total_investido` ✓
  - `gain = current_value - invested = total_atual - total_investido` ✓
  - `gain_pct = gain / invested = (total_atual - total_investido) / total_investido` ✓
  All four broker-truth numbers survive into the dashboard. The
  `qty=1` is a known lie that the README documents.
- *Alternatives considered:*
  - **`qty=0` for non-tradeable.** Rejected: `current_value = 0`,
    losing R$70k+ from Italo's portfolio current_value. The
    `gain_pct` is `0/0 = NaN` which the dashboard renders as
    garbage.
  - **Skip non-tradeable positions entirely.** Rejected: the asset
    shows up in the dashboard with `position_count=0` and
    `current_value=0`, which is misleading — the user *does* hold
    R$26k of that RDB.
  - **Make `Position.qty` and `Position.avg_price` nullable.**
    Rejected: out of scope (model change, and the dashboard's
    `qty or ZERO` guards would need to be updated in lockstep).
    A future change can add nullability and remove the sentinel.

### Decision 7: No `broker_ticker` column in the positions CSV; always `= asset_name`

- *Rationale:* The seed produces a 1:1 mapping from asset to
  position with one position per asset. The model carries
  `broker_ticker` as a separate column to support multi-broker
  positions (e.g. "PETR4" on XP and "PETR4" on Rico for the same
  asset), but the seed scenario is a single broker. Making the
  CSV default to `broker_ticker = asset_name` keeps the schema
  minimal; if a future change wants multi-broker, the column is
  added then.
- *Alternative:* Explicit `broker_ticker` column with default =
  `asset_name`. Rejected: adds a column that 100% of seed rows
  leave blank or equal to `asset_name`; net zero information gain
  at the cost of a redundant column.

### Decision 8: Position CSV does NOT enforce a `sum == 100` invariant

- *Rationale:* Positions are absolute values, not percentages. The
  sum of `qty × current_price` is the portfolio's
  `current_value`, which is free to be any number (R$ 1.1M for
  Italo, R$ 685k for Ana). Forcing a sum would require picking
  an arbitrary total and computing `pct_of_portfolio` per row,
  which the model doesn't store and the dashboard computes
  on-the-fly in `pages.py:240-270`.
- *Alternative:* Require `sum(qty × current_price) == portfolio_total`.
  Rejected: the seed would have to hardcode the portfolio total
  (R$ 1.1M, R$ 685k) and reject any edit that changed a single
  position's `current_price`, which defeats the point of CSV
  editing.

### Decision 9: CSV header is required, not optional

- *Rationale:* The CSVs are not large (≤ 50 rows each). Header
  presence costs nothing and prevents the `name` vs `target_pct`
  column-order bug from blowing up silently. The parser raises a
  clear "header missing" error otherwise.
- *Alternative:* No header, column order fixed. Rejected: humans
  hand-edit these; a header is essential for readability.

### Decision 10: Tests live under `tests/test_seed_from_csv.py`, marked `integration` (DB + TestClient)

- *Rationale:* Matches the existing convention. The script hits
  `SessionLocal` directly (no FastAPI) so the tests need a real
  `omaha_db` fixture but no `TestClient`. Both are present.
- *Update needed:* add the prefix `tests/test_seed_from_csv` to
  `_INTEGRATION_PREFIXES` in `tests/conftest.py` so the
  `pytest_collection_modifyitems` partition assigns the `integration`
  marker, not `unit`. (Per the AGENTS.md "Test marker rule" — without
  the allow-list, the new file would silently become `unit` and skip
  the DB setup.)

### Decision 11: `data/seed/README.md` documents all three CSV schemas + edit workflow

- *Rationale:* The user said "para eu poder editar manualmente no
  futuro". A README pinned to the data dir explains the column
  meaning of each CSV, the sum invariant, the non-tradeable
  sentinel convention, and how to regenerate after editing the
  xlsx / posicao CSVs.
- *Alternative:* Inline docstring in the seed script. Rejected: the
  README is more discoverable when the user opens the CSV folder.

## Risks / Trade-offs

- **Risk:** CSV editor saves with `sum != 100` (off-by-one typo).
  → *Mitigation:* the seed script validates before writing and exits
  non-zero with the exact line number. `task db-seed-from-csv` will
  fail loudly; the user sees the diagnostic.

- **Risk:** The user edits the CSV and runs `db-reset` (which calls
  `reset`) by reflex, losing imported positions.
  → *Mitigation:* `db-reset` already has destructive semantics and
  the taskipy help text says "Wipe + reseed". No new behaviour
  surface. `db-seed-upsert` is the safe path for "I edited the CSV,
  apply without wiping".

- **Risk:** `xlsx` / `posicao_*.csv` and CSV drift. User updates
  the source files, forgets to regenerate the seed CSVs (or
  vice-versa).
  → *Mitigation:* the seed's source of truth is the CSV triplet.
  The source files are consulted exactly once, during the apply
  phase, to bootstrap the CSVs. After merge, neither the application
  code nor any runtime script reads the source files — the CSV is
  the source of truth. Future edits go to the CSV. If the source
  files are later updated, the user re-derives the CSV by hand (per
  the README workflow); there is no automated bridge.

- **Risk:** Position CSV references an asset that doesn't exist in
  the assets CSV (typo, deleted asset, etc.).
  → *Mitigation:* the seed script cross-references positions against
  the assets file and aborts with the offending row's line number
  and the missing `asset_name`. No DB write on failure.

- **Risk:** Three CSVs per profile triple the file count (6 files
  for 2 profiles). Per-profile coupling is implicit (assets
  reference classes by name string, positions reference assets by
  name string).
  → *Mitigation:* the seed script cross-references all three layers
  and rejects mismatches with a clear error. A class missing from
  the classes file but referenced by the assets file aborts the
  seed with the offending asset row. An asset missing from the
  assets file but referenced by the positions file aborts with the
  offending position row.

- **Trade-off:** `Asset.target_pct = 0` for non-tradeable items
  makes the asset list noisier in the UI. The user can hide them
  via the dashboard filter, but a future improvement is a
  `tradeable: bool` column on `Asset` (deferred).

- **Trade-off:** `qty=1` sentinel for non-tradeable positions means
  the dashboard renders a literal "1" in the Qtd column for an RDB
  that has no countable units. The `current_value` and `invested`
  columns are correct, so the user is unlikely to be misled. A
  future change can make `Position.qty` nullable and remove the
  sentinel.

- **Trade-off:** Per-profile CSV triplet means a future 3rd profile
  needs three new files. Acceptable — the script iterates the
  triplet, no code change needed for the iteration itself, only the
  per-profile bootstrap data.

- **Trade-off:** The xlsx and posicao CSVs in
  `~/github/investing/input/` are consulted exactly once, during
  the apply phase, to bootstrap the six CSVs. After merge, neither
  the application code nor any runtime script reads the source
  files — the CSV triplet is the source of truth. If the user
  later wants to re-bootstrap from a future version of the source
  files, they edit the CSVs by hand (per the README workflow).
  The source files are effectively archived at that point.

## Migration Plan

- **Day 0 (apply phase):**
  1. Read `~/github/investing/input/setup_italo.xlsx` and
     `setup_ana.xlsx` one final time. Extract `categoria` and
     `ativo` sheets. Write the four class/asset CSVs.
  2. Read `~/github/investing/input/posicao_italo.csv` and
     `posicao_ana.csv` one final time. Parse the European number
     format (`R$`, comma decimal, dot thousands) into plain decimal
     strings. Apply the `qty=1, avg=total_investido, cur=total_atual`
     sentinel for non-tradeable items. Drop the `Minha Categoria`
     and `% Patrimônio` columns (used only for cross-checking in
     the apply phase). Write the two position CSVs.
  3. Add `data/seed/README.md` documenting the three CSV schemas,
     the sum invariant, the non-tradeable sentinel, and the
     non-runtime-dependency policy.
  4. Add `scripts/seed_from_csv.py`.
  5. Add `tests/test_seed_from_csv.py`; add prefix to
     `_INTEGRATION_PREFIXES`.
  6. Update `pyproject.toml` taskipy tasks (`db-seed-from-csv`,
     `db-seed-diff`, `db-seed-upsert`; repoint `db-reset`).
  7. Update `AGENTS.md` (relax "no asset seed" rule for the CSV
     path; extend to positions).
  8. Update `openspec/config.yaml` (project context).
  9. Delete `scripts/dev_reset.py` (after `db-reset` is repointed).
- **Day 0 (manual verification):**
  1. `uv run task db-reset` — confirm Italo gets 6 classes at the
     new targets (25 / 20 / 18 / 15 / 8 / 14), 47 assets, and 48
     positions. Open the dashboard, verify the
     `portfolio.current_value` matches the posicao footer's
     `R$ 1.101.350,86`.
  2. `uv run task db-seed-from-csv -- --profile ana` (or extend
     `db-reset` to also reset Ana) — confirm Ana gets 6 classes at
     25 / 29 / 20 / 15 / 0.1 / 10.9, 46 assets, 43 positions.
     Verify Ana's `portfolio.current_value` matches
     `R$ 684.763,60`.
  3. `uv run task db-seed-diff` — confirm the diff output is empty
     (CSV triplet matches DB state).
  4. `uv run task test-integration` — confirm new test passes.
  5. `uv run task check` — full lint + unit gate.
- **Rollback:** revert the change commit. The pre-change `dev_reset.py`
  no longer exists, so a rollback also requires restoring
  `scripts/dev_reset.py` from git history (one-line revert via
  `git revert <commit>`). The CSVs are additive — leaving them in
  `data/seed/` post-rollback is harmless.

## Open Questions

- **Q: Should `db-reset` reset both profiles, or stay Italo-only?**
  Current `dev_reset.py` is Italo-only. The new task name
  `db-reset` is profile-agnostic; it could take a `--profile` flag
  and reset one. **Proposal:** keep `db-reset` as Italo-only for
  backward compat (matches today's behaviour); add `db-seed-from-csv`
  for the full-featured CLI. Operators wanting to reset Ana run
  `uv run task db-seed-from-csv -- --profile ana --mode reset`.
  Decision deferred to implementation — if the user wants symmetry,
  one extra taskipy line covers it.

- **Q: Encoding handling for non-ASCII asset names (e.g.
  "Tesouro IPCA+ 2035", "Caixinha Turbo NuCel").** CSV default is
  UTF-8. Python's `csv` module reads UTF-8 by default when given a
  text-mode file. We don't anticipate issues but the integration
  test should round-trip one non-ASCII name to catch any encoding
  surprise.
