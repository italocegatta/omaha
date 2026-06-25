## 1. Generate CSV seed files from the xlsx + posicao references (one-time bootstrap)

- [x] 1.1 Read `~/github/investing/input/setup_italo.xlsx`, `setup_ana.xlsx`, `posicao_italo.csv`, and `posicao_ana.csv` one final time. Extract `categoria` and `ativo` sheets from the xlsx; extract the position columns from the posicao CSVs. Do NOT create any code that reads these files afterwards — they are the bootstrap input, the CSVs are the source of truth.
- [x] 1.2 Create `data/seed/` directory and add `data/seed/README.md` documenting the three CSV schemas (classes, assets, positions), the sum invariant, the non-tradeable `qty=1` sentinel convention, the edit workflow, and the fact that the xlsx and posicao CSVs are **not** runtime dependencies
- [x] 1.3 Write `data/seed/italo_classes.csv` with 6 rows from the `categoria` sheet of `setup_italo.xlsx` (RF Dinâmica 25, RF Pós 20, Internacional 18, FII 15, Cripto 8, Ações 14; `display_order` 0..5)
- [x] 1.4 Write `data/seed/italo_assets.csv` with 48 rows from the `ativo` sheet of `setup_italo.xlsx` (`pc_ativo_alocacao_categoria × 100` rounded to 2 decimals, `display_order` 0..N per class). Note: spec said 47 but the xlsx contains 48 rows (includes `RBFM11` with `target_pct=0` in FII).
- [x] 1.5 Write `data/seed/ana_classes.csv` with 6 rows from the `categoria` sheet of `setup_ana.xlsx` (RF Dinâmica 25, RF Pós 29, Internacional 20, FII 15, Cripto 0.1, Ações 10.9; `display_order` 0..5)
- [x] 1.6 Write `data/seed/ana_assets.csv` with 46 rows from the `ativo` sheet of `setup_ana.xlsx`
- [x] 1.7 Write `data/seed/italo_positions.csv` with 47 rows from `posicao_italo.csv`. Note: spec said 48 but the source posicao CSV has 47 data rows.
  - European number format (`R$ 13.831,36`) → plain decimal (`13831.36`)
  - For 7 non-tradeable rows (RDB, CDB with `Qtd="-"` and `Preço médio="-"`): use `qty=1, avg_price=total_investido, current_price=total_atual`
  - Drop `Minha Categoria` and `% Patrimônio` columns (the asset's class is resolved via cross-reference to the assets CSV)
  - Drop header/footer noise (UTF-8 BOM, "47 ativos" footer row)
- [x] 1.8 Write `data/seed/ana_positions.csv` with 43 rows from `posicao_ana.csv` (same conversion rules; 2 non-tradeable rows)
- [x] 1.9 Sanity check: confirm `sum(target_pct) == 100` per profile (classes) and per class (assets) for all four class/asset files; confirm position counts (Italo: 47, Ana: 43)

## 2. Implement the CSV-driven seed script

- [x] 2.1 Create `scripts/seed_from_csv.py` with `argparse` for `--profile {italo,ana}` and `--mode {reset,upsert,diff}`
- [x] 2.2 Add CSV loader: parse `data/seed/{profile}_classes.csv` and `data/seed/{profile}_assets.csv` with required-header check, type coercion, range check on `target_pct`, uniqueness check on `name` (per file) and `(class_name, name)` (asset file)
- [x] 2.3 Add cross-reference check: every asset's `class_name` must match a class `name` in the class file
- [x] 2.4 Add sum check using `omaha.validators.validate_target_pct_sum`: per profile (class file) and per class (asset file); abort with the validator's `Sobra X%` / `Falta X%` message on failure
- [x] 2.5 Add positions CSV loader: parse `data/seed/{profile}_positions.csv` with required-header check, type coercion, range check (`qty >= 0`, `avg_price >= 0`, `current_price >= 0`); cross-reference each row's `asset_name` against the asset CSV's `name` (must match); abort with the offending line number on miss
- [x] 2.6 Implement `--mode reset`: wipe `positions` / `import_previews` / `assets` / `asset_classes` for the profile (same SQL as `scripts/dev_reset.py:39-62`), then insert classes → assets → positions in `display_order` ascending; positions MUST be inserted after their asset exists so the FK resolves
- [x] 2.7 Implement `--mode upsert`: no delete; create-or-update classes by `(profile_id, name)`, assets by `(asset_class_id, name)`, and positions by `(asset_id, broker_ticker)` where `broker_ticker = asset_name`; print per-row diff including `positions: created=A updated=B unchanged=C`
- [x] 2.8 Implement `--mode diff`: no write; print `would-create` / `would-update` / `would-orphan` sections for each of the three layers (classes, assets, positions)
- [x] 2.9 Add a `__main__` entry point that opens a short-lived session and prints a one-line summary (`profile=X mode=Y classes=A assets=B positions=K created=C updated=D unchanged=E`)

## 3. Wire taskipy tasks and repoint db-reset

- [x] 3.1 Add `db-seed-from-csv`, `db-seed-diff`, `db-seed-upsert` tasks to `[tool.taskipy.tasks]` in `pyproject.toml` per the spec
- [x] 3.2 Repoint the `db-reset` task to `uv run python -m scripts.seed_from_csv --profile italo --mode reset` (preserves current destructive behaviour)
- [x] 3.3 Delete `scripts/dev_reset.py` after `db-reset` is repointed (no parallel path)

## 4. Update project rules and config

- [x] 4.1 Update `AGENTS.md` "Seed data" section: replace the absolute "MUST NOT create assets" rule with the CSV-path exception for both `Asset` AND `Position` rows, per the spec (`data-driven-seed` capability)
- [x] 4.2 Populate `openspec/config.yaml` `context:` block with project framing (tech stack, PT-BR UI, SQLite, CSV-driven seed location, AGENTS.md rule references)
- [x] 4.3 Add the `tests/test_seed_from_csv` prefix to `_INTEGRATION_PREFIXES` in `tests/conftest.py` so the new test gets the `integration` marker (per AGENTS.md "Test marker rule")

## 5. Add integration test

- [x] 5.1 Create `tests/test_seed_from_csv.py` with the `omaha_db` fixture (integration marker auto-assigned via the prefix above)
- [x] 5.2 Test: `reset` on a fresh profile creates 6 classes + 48 assets + 47 positions for Italo with `sum(target_pct) == 100` per profile and per class. Note: spec said 47/48 but the actual source files have 48 assets and 47 positions for Italo.
- [x] 5.3 Test: `reset` on a populated profile wipes positions / previews / assets / classes before re-seeding the full triplet
- [x] 5.4 Test: `reset` is idempotent (run twice → same DB state including positions)
- [x] 5.5 Test: `upsert` updates a changed `target_pct`, a changed `current_price`, and creates a missing asset + position without deleting other rows
- [x] 5.6 Test: `diff` on a populated profile lists only the changes across all three layers; no write happens (verify by counting rows before/after)
- [x] 5.7 Test: sum-violating class CSV is rejected with the validator's `Sobra X%` / `Falta X%` message and no DB write
- [x] 5.8 Test: asset referencing a missing class is rejected with the offending line number and no DB write
- [x] 5.9 Test: position referencing a missing asset is rejected with the offending line number and no DB write
- [x] 5.10 Test: non-tradeable position (RDB with `qty=1, avg=20000, cur=26475.01`) survives `reset` and contributes R$ 26.475,01 to the portfolio's `current_value`
- [x] 5.11 Test: non-ASCII asset name round-trips correctly (`Tesouro IPCA+ 2035`, `Caixinha Turbo NuCel`)

## 6. Manual verification and CI gate

- [x] 6.1 `uv run task db-reset` — confirm Italo gets 6 classes at 25/20/18/15/8/14, 48 assets, and 47 positions. Dashboard `portfolio.current_value` is R$ 964.381,97 (sum of `qty × current_price`), not the broker's claimed R$ 1.101.350,86 footer total. The discrepancy is broker data quality: the source posicao CSV's unit prices × qty don't multiply to the reported totals (the broker footer sums `total_atual`, but the dashboard formula uses `qty × current_price`). The non-tradeable RDB sentinel rows (`qty=1, cur=total_atual`) do contribute exactly R$ 26.475,01 each — that test (5.10) passes.
- [x] 6.2 `uv run python -m scripts.seed_from_csv --profile ana --mode reset` — Ana gets 6 classes at 25/29/20/15/0.1/10.9, 46 assets, 43 positions. Dashboard total: R$ 629.225,05 (vs broker's claimed R$ 684.763,60; same broker-data issue as Italo).
- [x] 6.3 `uv run task db-seed-diff` — diff is empty (CSV triplet matches DB state) ✓
- [x] 6.4 `uv run task test-integration` — all 198 integration tests pass, including the 11 new ones in `tests/test_seed_from_csv.py` ✓
- [x] 6.5 `uv run task check` — full lint + unit gate green (129 passed, 2 skipped) ✓
- [x] 6.6 `uv run task db-clear-assets` — works (deletes 94 assets), no regression ✓
