## 1. Extend `seed_from_csv.py` positions pipeline with `broker_ticker`

- [x] 1.1 Update `POSITION_HEADER` in `scripts/seed_from_csv.py` from
  `("asset_name", "qty", "avg_price", "current_price")` to
  `("asset_name", "broker_ticker", "qty", "avg_price", "current_price")`.
- [x] 1.2 Add `broker_ticker: str` to the `PositionRow` dataclass
  (frozen) alongside the existing fields. Update `line_no` to stay
  last.
- [x] 1.3 Update the positions CSV parser: parse `broker_ticker` as a
  required non-empty string; abort with line number on empty /
  missing value.
- [x] 1.4 Update the cross-reference check to key by the pair
  `(asset_name, broker_ticker)`: each row's `asset_name` must match
  an asset in `{profile}_assets.csv`, AND no two rows may share the
  same `(asset_name, broker_ticker)` pair within the file (this is
  the CSV-side mirror of the DB unique constraint
  `(asset_id, broker_ticker)`). Abort with line number + duplicate
  pair on collision.
- [x] 1.5 Update `--mode reset` position insertion: insert
  `broker_ticker` from the CSV row instead of aliasing to
  `asset_name`. Keep `asset_id` resolution by `asset_name` lookup
  against the freshly inserted assets (preserves dependency order:
  classes → assets → positions).
- [x] 1.6 Update `--mode upsert` and `--mode diff` to key positions
  by `(asset_id, broker_ticker)` instead of
  `(asset_id, asset_name)`. Update the per-row diff output to print
  `asset_name=<name> broker_ticker=<ticker>` so the pair is
  identifiable in the log.
- [x] 1.7 Update `tests/test_seed_from_csv.py` fixture data: add a
  `broker_ticker` column to every positions CSV fixture used in
  the existing tests, populated with `asset_name` (preserves the
  historical 1:1 mapping; existing assertions still pass).
- [x] 1.8 Add a new scenario to `tests/test_seed_from_csv.py`:
  `reset` with a positions CSV where one row has
  `broker_ticker = "PETR4"` against `asset_name = "Petrobras PN"`
  produces a `Position` row with `broker_ticker == "PETR4"` and
  the dashboard renders the position under "Petrobras PN".

## 2. Implement `scripts/snapshot_to_csv.py`

- [x] 2.1 Create `scripts/snapshot_to_csv.py` with module docstring
  mirroring the structure of `scripts/seed_from_csv.py` (Why,
  What, Usage section).
- [x] 2.2 Define `PROFILES = ("italo", "ana")` at module top,
  matching `seed_from_csv.py:55`.
- [x] 2.3 Implement `_format_decimal(value: Decimal, places: int) ->
  str` helper: `quantize(Decimal(10) ** -places)` and string-render.
  Used for `target_pct` (2 places) and qty/price (8 places).
- [x] 2.4 Implement `_format_bool(value: bool) -> str` returning
  `"true"` or `"false"` lowercase (matches the
  `seed_from_csv.py` permissive parser).
- [x] 2.5 Implement `_atomic_write_csv(path: Path, header: tuple[str,
  ...], rows: Iterable[tuple])`: write to `path.with_suffix(path.suffix
  + ".tmp")` then `os.replace(tmp, path)`. Use `csv.writer` with
  `lineterminator="\n"` (matches the existing CSVs in `data/seed/`).
- [x] 2.6 Implement `snapshot_classes(profile: Profile, profile_name:
  str) -> int`: query `profile.asset_classes` ordered by
  `display_order`, write `data/seed/{profile_name}_classes.csv` with
  the 4-column header, return row count. Reuse `_atomic_write_csv`.
- [x] 2.7 Implement `snapshot_assets(profile: Profile, profile_name:
  str) -> int`: iterate `profile.asset_classes` ordered by
  `display_order`, for each class iterate `class.assets` ordered by
  `display_order`, write `data/seed/{profile_name}_assets.csv` with
  the 7-column header, return row count.
- [x] 2.8 Implement `snapshot_positions(profile: Profile, profile_name:
  str) -> int`: iterate `profile.asset_classes` → `class.assets` →
  `asset.positions` in that order; sort positions within each asset
  by `broker_ticker` ascending; write
  `data/seed/{profile_name}_positions.csv` with the 5-column header
  (`asset_name,broker_ticker,qty,avg_price,current_price`); return
  row count.
- [x] 2.9 Implement `snapshot_profile(session: Session, profile_name:
  str) -> tuple[int, int, int]`: look up profile by name, call the
  three `snapshot_*` helpers, return `(classes, assets, positions)`
  counts. Aborts with `seed_from_csv.abort(f'snapshot FAIL: profile
  "{profile_name}" missing from DB')` if not found.
- [x] 2.10 Implement `main(argv: list[str] | None = None) -> int`:
  open `SessionLocal`, query all `Profile` rows, validate the set
  against `PROFILES` (abort if any name is outside the set), iterate
  `PROFILES` in order calling `snapshot_profile` for each, print
  per-profile summary
  (`{profile}: {C} classes, {A} assets, {P} positions -> 3 files
  written`) plus a final aggregate. Exit 0 on success, 1 on
  failure.
- [x] 2.11 Add `__main__` guard that calls `sys.exit(main())`.

## 3. Wire taskipy task

- [x] 3.1 Add `db-snapshot` to `[tool.taskipy.tasks]` in
  `pyproject.toml` with the command
  `uv run python -m scripts.snapshot_to_csv` and a help string
  documenting that it runs over both canonical profiles.

## 4. Update test marker allow-list

- [x] 4.1 Add the `tests/test_snapshot_to_csv` prefix to
  `_INTEGRATION_PREFIXES` in `tests/conftest.py` so the new test
  file auto-receives the `integration` marker (per AGENTS.md "Test
  marker rule").

## 5. Update data/seed documentation

- [x] 5.1 In `data/seed/README.md`, update the positions CSV row in
  the file schema table: add `broker_ticker` column with
  description "broker-side symbol; required, may diverge from
  `asset_name` (e.g. `asset_name='Petrobras PN'`,
  `broker_ticker='PETR4')`. Uniqueness is per
  `(asset_name, broker_ticker)` pair."
- [x] 5.2 Add a new step to the "Edit workflow" section: "Or,
  freeze the current DB state with `task db-snapshot` and commit
  the resulting `git diff data/seed/`. The snapshot exports live
  DB state to all 6 CSVs in the canonical profile set
  (`italo`, `ana`)."

## 5b. Update root README.md

- [x] 5b.1 In `README.md`, add a new row to the Development tasks
  table (lines 49-82) for `db-snapshot`, placed alphabetically
  next to `db-reset`. Description:
  `Export live DB state (classes + assets + positions) to data/seed/*.csv for both profiles. Internal dev tool.`
  Keep the table's existing single-sentence row format.
- [x] 5b.2 In `README.md`, add a new subsection "Snapshot the
  wallet state" in the "Testing the app" section (after the
  `db-reset` example, ~line 240). Show the `task db-snapshot`
  invocation with the expected per-profile output, then a
  `git diff data/seed/` line and a one-sentence description of
  the round-trip workflow. Match the section's existing tone
  (sentence-case headings, fenced bash blocks with expected
  output).

## 6. Add integration test

- [x] 6.1 Create `tests/test_snapshot_to_csv.py` with the `omaha_db`
  fixture and the `subprocess` pattern from
  `tests/test_seed_from_csv.py` (invoke the script via
  `python -m scripts.snapshot_to_csv`).
- [x] 6.2 Test: round-trip stability for Italo — seed a known
  Italo state (use the `omaha_db` fixture's existing seed), run
  snapshot, run `seed_from_csv --mode reset --profile italo`,
  assert all four tables match the pre-snapshot column values
  for every row (excluding `id`, `created_at`, `imported_at`).
- [x] 6.3 Test: round-trip stability for Ana — same as 6.2 for
  the Ana profile.
- [x] 6.4 Test: `broker_ticker` preserved — add a one-off
  `Asset(name="Petrobras PN", ...)` and
  `Position(broker_ticker="PETR4", ...)` to the Italo profile
  via direct ORM, run snapshot, reset, assert the resulting
  `Position` has `broker_ticker == "PETR4"` and the CSV column
  for that row is `Petrobras PN`.
- [x] 6.5 Test: unknown profile error — insert a
  `Profile(name="test_orphan", user_id=...)` into the DB, run
  snapshot, assert `exit code == 1` and stderr contains
  `"test_orphan" not in canonical set`. Assert no CSV file in
  `data/seed/` was modified (compare mtimes or file contents).
- [x] 6.6 Test: idempotency — run snapshot twice on the same DB
  state, assert the two outputs are byte-equal (read both CSVs
  and compare). Run in a tempdir copy of `data/seed/` so the
  real repo files are not touched.
- [x] 6.7 Test: header shape guard — assert the first line of
  each emitted CSV exactly equals the documented header tuple
  (`name,target_pct,display_order,quote_kind` for classes;
  `class_name,name,target_pct,display_order,buy_enabled,
  sell_enabled,currency_code` for assets;
  `asset_name,broker_ticker,qty,avg_price,current_price` for
  positions).

## 7. Update spec delta

- [x] 7.1 In `openspec/changes/add-db-snapshot/specs/data-driven-
  seed/spec.md`, replace the existing "Requirement: CSV schema
  for per-profile current positions" with the new 5-column header
  and add an explicit "The `broker_ticker` column is independent
  of `asset_name` and MAY diverge" sentence. Add scenarios for
  divergent `broker_ticker` round-trip.
- [x] 7.2 Update the cross-reference requirement text to key by
  the `(asset_name, broker_ticker)` pair instead of `asset_name`
  alone.
- [x] 7.3 Update the "Requirement: `reset` mode also seeds
  positions" text to say `broker_ticker` is taken verbatim from
  the CSV (not aliased to `asset_name`).

## 8. Manual verification and CI gate

- [x] 8.1 `uv run task db-reset` — confirm both profiles seed
  cleanly. Baseline counts unchanged.
- [x] 8.2 `uv run task db-snapshot` — confirm 6 CSV files are
  written, per-profile summary printed, exit 0. Confirm
  `git status data/seed/` shows a clean diff (snapshot of
  current state equals current CSVs after the prior `db-reset`).
- [x] 8.3 Edit a row directly via SQL (e.g. bump one
  `AssetClass.target_pct` by 1), run snapshot, confirm
  `git diff data/seed/italo_classes.csv` shows the change.
- [x] 8.4 `uv run task test-integration` — full integration
  suite green, including the 7 new tests in
  `tests/test_snapshot_to_csv.py` and the 1 new scenario in
  `tests/test_seed_from_csv.py`.
- [x] 8.5 `uv run task check` — lint + unit gate green.
- [x] 8.6 `uv run task db-clear-assets` — confirm regression-free
  (it deletes positions via cascade; subsequent snapshot produces
  empty position CSVs).

## 9. Stop recomputing totals in the seed path (broker-csv-import-totals invariant)

The seed pipeline used to compute `Position.total_invested = qty *
avg_price` and `Position.total_current = qty * current_price` as a
"best effort" fallback when the CSV did not carry explicit totals.
That arithmetic is the exact drift source the broker-csv-import-totals
change eliminates — totals are broker-published values, never
recomputed. This section adds the missing seed/snapshot CSV columns
so the round-trip preserves whatever the broker (or the user's UI
edits) put in the DB.

- [x] 9.1 Extend `POSITION_HEADER` in `scripts/seed_from_csv.py`
  from 5 columns to 7 — append `total_invested`, `total_current`.
- [x] 9.2 Add `total_invested: Decimal | None` and
  `total_current: Decimal | None` to the `PositionRow` dataclass
  (verbatim, not recomputed).
- [x] 9.3 Implement `_optional_decimal` helper: empty cell → `None`;
  non-empty cell must parse as a decimal `>= 0`. Wire it into
  `load_positions` for the two new cells.
- [x] 9.4 Update `run_reset` position insertion: insert
  `total_invested` / `total_current` verbatim from the CSV; no
  `qty * price` recompute.
- [x] 9.5 Update `run_upsert` and `run_diff` position handling:
  when the CSV cell is empty (`None`), leave the existing row's
  value untouched (upsert should not overwrite a missing opinion);
  when non-empty, take verbatim.
- [x] 9.6 Update `scripts/snapshot_to_csv.py`:
  - Extend `POSITION_HEADER` to 7 columns.
  - Write `Position.total_invested` / `total_current` verbatim
    (4-dp to match the DB column); empty cell ↔ `None`.
- [x] 9.7 Populate `data/seed/{italo,ana}_positions.csv` with the
  new columns. Sentinel `qty=1` rows get `totals = avg / cur` (per
  the existing convention); other rows start empty and pick up
  broker-truth values the next time the user imports the broker
  CSV.
- [x] 9.8 Update `tests/test_seed_from_csv.py`:
  - Update `test_reset_preserves_divergent_broker_ticker` to
    include totals columns in its injected row.
  - Add `test_reset_preserves_totals_verbatim_no_recompute`:
    inject sentinel totals that DO NOT equal `qty * price` and
    assert they survive `reset`.
  - Add `test_reset_null_total_cells_contribute_zero`: empty
    totals cells parse to `None` (not 0, not a recompute).
  - Fix `test_position_referencing_missing_asset_is_rejected`
    replace-string to handle the new 7-column format.
- [x] 9.9 Update `tests/test_snapshot_to_csv.py`:
  - Update header assertion for positions to 7 columns.
  - Extend the round-trip helper to capture `total_invested` /
    `total_current`.
  - Add `seed_dir_backup` fixture that restores
    `data/seed/*.csv` after each test that drives the snapshot
    subprocess (prevents repo-file pollution across test runs).
  - Add `test_totals_preserved_through_round_trip`: inject
    sentinel totals (≠ `qty * price`) into the DB, run
    `snapshot → reset → snapshot`, assert the values survive
    byte-equal.
- [x] 9.10 Update `data/seed/README.md`:
  - Extend the positions CSV row in the schema table to
    document the two new totals columns + the verbatim /
    NULL semantics.
  - Add rule #9 to the validation list: empty cell → `NULL`;
    non-empty cell is decimal `>= 0`; never recomputed.
- [x] 9.11 Update `openspec/changes/add-db-snapshot/specs/data-
  driven-seed/spec.md`:
  - Extend the MODIFIED Requirement "CSV schema for per-profile
    current positions" header from 5 to 7 columns; document
    the new totals cells.
  - Add an ADDED Requirement "Positions CSV carries broker-
    published totals verbatim" with three scenarios (verbatim
    round-trip, empty cells parse to NULL, reset never
    recomputes).
- [x] 9.12 Verification:
  - `uv run task test-integration`: full suite green (342
    passed).
  - `uv run task check`: lint + unit green (150 passed).
  - Manual round-trip: set SMH totals to non-`qty * price`
    sentinel values → `db-snapshot` → `db-reset` →
    `db-snapshot` (byte-equal); DB preserves the sentinels.
  - `task db-snapshot` is idempotent across consecutive runs.
