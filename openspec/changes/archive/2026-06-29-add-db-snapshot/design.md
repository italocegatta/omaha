# Design — `add-db-snapshot`

## Overview

```
┌──────────────────────────────────────────────────────────────┐
│  task db-snapshot                                            │
│  └─ scripts/snapshot_to_csv.py                               │
│     ├─ open SessionLocal                                     │
│     ├─ discover profiles in DB                               │
│     ├─ if any profile name ∉ {italo, ana}: abort 1           │
│     ├─ for each profile (italo, ana):                        │
│     │   ├─ query Profile → AssetClass → Asset → Position     │
│     │   ├─ write data/seed/{profile}_classes.csv             │
│     │   ├─ write data/seed/{profile}_assets.csv              │
│     │   └─ write data/seed/{profile}_positions.csv           │
│     └─ print per-profile + aggregate summary                 │
└──────────────────────────────────────────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────────────────────────┐
│  data/seed/{italo,ana}_*.csv   ← authoritative source        │
│  task db-reset          → reads CSVs, writes DB              │
└──────────────────────────────────────────────────────────────┘
```

The script is symmetric to `seed_from_csv.py`: one reads CSVs and
writes DB, the other reads DB and writes CSVs. The shared schema
contract is the CSV header + per-row shape, not code (no shared
dataclass import — the two scripts stay independently auditable).

## Profile discovery and the "unknown profile" rule

The canonical set is `PROFILES = ("italo", "ana")` — same constant
shape as `scripts/seed_from_csv.py:55` for symmetry. Discovery is
DB-driven, not filesystem-driven:

1. Query all `Profile` rows ordered by `(user_id, display_order)`.
2. For each row, check `profile.name in {"italo", "ana"}`.
3. If **any** row has a name outside the set, print
   `snapshot FAIL: profile "X" not in canonical set {italo, ana}`
   to stderr and `sys.exit(1)`. No CSV is written.
4. Otherwise, iterate the canonical set in order and export each.

Rationale for fail-fast (per the user's "erro explícito"
decision): a stray profile usually means a test left a row
behind. Silently skipping it would let the DB and the CSV drift
further apart. Aborting makes the operator look at the DB
immediately.

Edge cases:

- **Profile missing from DB.** If `italo` (or `ana`) is not in
  the DB at all, abort with `snapshot FAIL: profile "italo"
  missing from DB` and `sys.exit(1)`. The canonical set is the
  floor for what `db-reset` expects.
- **Profile exists but has zero classes / assets / positions.**
  Export an empty CSV with just the header. This is a valid state
  for a freshly seeded profile (post-`db-clear-assets`).

## CSV output format

### Classes — `data/seed/{profile}_classes.csv`

```csv
name,target_pct,display_order,quote_kind
RF Dinâmica,25.00,0,none
RF Pós,20.00,1,none
Internacional,18.00,2,none
FII,15.00,3,none
Cripto,8.00,4,none
Ações,14.00,5,none
```

- `target_pct`: `str(Decimal)` rendered with `quantize(Decimal("0.01"))`
  so `25.0` → `"25.00"` and `0.1` → `"0.10"`. Matches the
  `seed_from_csv.py` parser expectation.
- `display_order`: `int` literal.
- `quote_kind`: enum value (`auto` / `manual` / `none`), unchanged.
- Rows sorted by `display_order` ascending so the output diff is
  stable across runs.
- `created_at` is **not** exported — the DB column has no CSV
  counterpart, and the round-trip restores a fresh
  `server_default=func.now()` timestamp.

### Assets — `data/seed/{profile}_assets.csv`

```csv
class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code
RF Dinâmica,Tesouro Selic 2029,100.00,0,true,true,BRL
RF Dinâmica,Caixinha Nubank,0.00,1,true,true,BRL
...
```

- All `target_pct`, `buy_enabled`, `sell_enabled`, `currency_code`,
  `display_order` exported verbatim.
- `buy_enabled` / `sell_enabled` rendered as `true` / `false`
  lowercase (matches `seed_from_csv.py` permissive boolean
  parser).
- `currency_code` upper-cased before write (matches the existing
  `seed_from_csv.py:71` allowlist normalization).
- Rows sorted by `(class_name, display_order)` ascending.
- `created_at` not exported (same reason).

### Positions — `data/seed/{profile}_positions.csv`

```csv
asset_name,broker_ticker,qty,avg_price,current_price
Tesouro Selic 2029,Tesouro Selic 2029,1,20000.00,26475.01
Petrobras PN,PETR4,100,32.50,38.75
IVVB11,IVVB11,50,250.00,275.30
```

- **`broker_ticker` is the new column** — added between
  `asset_name` and `qty` to keep the leading "lookup pair"
  together.
- `asset_name` = `asset.name` (the user-facing label). `broker_ticker`
  = `position.broker_ticker` (the broker-side symbol). When they
  match (the common case), both columns carry the same value.
  When they diverge (e.g. user labeled the asset "Petrobras PN"
  but the broker reports it as `PETR4`), both are preserved.
- `qty` / `avg_price` / `current_price`: `str(Decimal)` rendered
  via `quantize(Decimal("0.00000001"))` so 8 decimal places are
  preserved (matches the `Numeric(18, 8)` DB column).
- `total_invested` / `total_current` are **not exported** — they
  have no CSV counterpart today. The position is round-trippable
  via the three numeric columns because the broker-truth numbers
  collapse onto `qty=1, avg_price=total_investido,
  current_price=total_atual` for non-tradeable rows (the existing
  `qty=1` sentinel convention in `data/seed/README.md`).
- Rows sorted by `(asset_name, broker_ticker)` ascending for
  diff stability.

## `broker_ticker` semantics — the delta in `data-driven-seed`

The current spec says:

> The `broker_ticker` for the seeded `Position` row MUST equal
> `asset_name` (1:1 mapping; multi-broker is a future change).

This change relaxes that to:

> The `broker_ticker` for the seeded `Position` row MUST equal
> the value of the `broker_ticker` column in the positions CSV.
> The CSV's `broker_ticker` is independent of `asset_name` and
> MAY diverge. The pair `(asset_name, broker_ticker)` is the
> uniqueness key — two positions on the same asset with
> different `broker_ticker` values (multi-broker) become
> supported as a side effect.

In practice, today's CSVs have `broker_ticker == asset_name`
everywhere, so the snapshot export produces CSVs identical to the
current ones modulo the new column. The relaxation is forward-
looking — it does not require any existing CSV row to change
semantically, only mechanically (add a `broker_ticker` column
populated from `asset_name`).

`scripts/seed_from_csv.py` updates:

- `POSITION_HEADER = ("asset_name", "broker_ticker", "qty",
  "avg_price", "current_price")`.
- `PositionRow` dataclass gains `broker_ticker: str`.
- Parser parses `broker_ticker` as required non-empty string.
- Cross-reference check: each row's `(asset_name, broker_ticker)`
  pair must resolve — `asset_name` must match an asset row, and
  the resulting `Position` row's `(asset_id, broker_ticker)` must
  not collide with an existing row in a different asset of the
  same profile (defensive — currently impossible because
  `broker_ticker == asset_name` is unique per profile, but the
  delta removes the guarantee).
- `reset` inserts `broker_ticker` verbatim from the CSV.
- `upsert` keys by `(asset_id, broker_ticker)` instead of
  `(asset_id, asset_name)`.
- `diff` reports `(asset_name, broker_ticker)` as the position
  identifier in its output.

## Round-trip invariants

After `task db-snapshot && task db-reset`, the live DB MUST have:

| Table         | Property                                                |
|---------------|---------------------------------------------------------|
| `profiles`    | Same set of names in the same `display_order`           |
| `asset_classes` | Same `name` / `target_pct` / `display_order` / `quote_kind` |
| `assets`      | Same `name` / `target_pct` / `display_order` / `buy_enabled` / `sell_enabled` / `currency_code` |
| `positions`   | Same `broker_ticker` / `qty` / `avg_price` / `current_price` |

The integration test asserts each of these by reading the DB before
the snapshot and after the reset and asserting equality on the
listed columns.

The round-trip is **not** byte-identical on the DB because:

- `created_at` timestamps change.
- `id` autoincrement values change.
- `imported_at` on positions changes.
- `total_invested` / `total_current` (DB-only, not in CSV) are
  cleared by `reset` and back-filled to `NULL`.

These are intentional, documented in `data/seed/README.md` under
the round-trip caveat.

## File write strategy

Atomic write to avoid leaving a half-written CSV if the script
crashes mid-export:

1. Write to `data/seed/{profile}_{classes,assets,positions}.csv.tmp`
   first.
2. `os.replace(tmp, final)` to atomically swap.

This prevents a half-snapshot from being picked up by a
concurrent `db-reset` or by `git status` showing a corrupted
diff. The `.tmp` files are cleaned up on the next run regardless
(success or failure path).

## Error handling summary

| Condition                                    | Behavior                       |
|----------------------------------------------|--------------------------------|
| Profile in DB not in `{italo, ana}`          | `abort()`, exit 1, no writes   |
| Canonical profile missing from DB            | `abort()`, exit 1, no writes   |
| Empty profile (no classes)                   | Export header-only CSV         |
| Profile with classes but no assets           | Export empty assets CSV        |
| Profile with assets but no positions         | Export header-only positions CSV |
| Invalid data in DB (sum ≠ 100)               | **Export as-is** (user decision B) |
| Concurrent run / file lock conflict          | `OSError` propagates, exit 1   |
| Source CSV not writable                      | `OSError` propagates, exit 1   |

The script reuses `seed_from_csv.abort()` for the fail-fast path
to keep the error output consistent across the two scripts
(`FAIL: <message>` to stderr, exit code 1).

## Testing strategy

`tests/test_snapshot_to_csv.py` (integration marker auto-applied
via the `_INTEGRATION_PREFIXES` carve-out):

1. **Round-trip stability** — populate the DB with a known Italo
   state (via `omaha_db` fixture), run snapshot, run
   `seed_from_csv --mode reset`, assert all four tables match the
   pre-snapshot column values for every row.
2. **Round-trip stability, Ana** — same as above for the Ana
   profile.
3. **`broker_ticker` preserved** — seed an Italo asset
   "Petrobras PN" with a `Position(broker_ticker="PETR4")`,
   snapshot, reset, assert the resulting `Position` row has
   `broker_ticker == "PETR4"` and the CSV's `asset_name` column
   is `"Petrobras PN"`.
4. **Unknown profile error** — insert a `Profile(name="test")`
   into the DB, run snapshot, assert `exit code == 1` and
   stderr contains `not in canonical set`. No CSV file is
   modified.
5. **Idempotency** — run snapshot twice on the same DB state,
   assert the two runs produce byte-equal CSVs (same content,
   same ordering, same line endings).
6. **CSV header shape** — assert the first line of every emitted
   CSV exactly matches the documented header tuple. This is a
   guardrail against accidental column reordering.

## Taskipy integration

`pyproject.toml` adds:

```toml
db-snapshot = { cmd = "uv run python -m scripts.snapshot_to_csv", help = "Export live DB state (classes + assets + positions) to data/seed/*.csv for ALL canonical profiles (italo + ana). Internal dev tool." }
```

The new entry is placed alphabetically next to the existing
`db-reset` / `db-seed-*` rows so the table stays scannable. No
other taskipy tasks change. `db-reset` keeps its current
`scripts.reset_both_profiles.py` entrypoint.

The root `README.md` Development tasks table (currently lines
49-82) gains a row for `db-snapshot` in the same alphabetical
slot. The row description mirrors the table's existing tone:

```
| `db-snapshot`   | Export live DB state (classes + assets + positions) to `data/seed/*.csv` for both profiles. |
```

## Documentation updates

Three documents gain content for this change. None of them
require structural rewrites — all are append-only within their
existing sections.

### `data/seed/README.md`

1. Updated positions CSV row in the header table — adds
   `broker_ticker` column with semantics "broker-side symbol;
   independent of `asset_name`; defaults to equal `asset_name`
   when the broker uses the same identifier".
2. New step in the "Edit workflow" section: "Or, freeze the
   current DB state with `task db-snapshot` and commit the
   resulting `git diff data/seed/`."

### `README.md` (root project)

1. **Development tasks table** (lines 49-82): new row for
   `db-snapshot`, placed alphabetically next to `db-reset`. The
   description fits the table's existing single-sentence format:

   ```
   | `db-snapshot`   | Export live DB state (classes + assets + positions) to `data/seed/*.csv` for both profiles. Internal dev tool. |
   ```

2. **Testing the app section** (line 228+): new subsection
   "Snapshot the wallet state" placed immediately after the
   `db-reset` invocation example. Content:

   ```
   ### Snapshot the wallet state

   `db-reset` is destructive — it wipes the DB before reseeding.
   If you want to preserve your current wallet state across a
   destructive change (a migration test, a UI rework, or just a
   checkpoint), `task db-snapshot` exports the live DB to the
   CSV triplet under `data/seed/`:

   ```bash
   uv run task db-snapshot
   # expected:
   #   italo: 6 classes, 48 assets, 47 positions -> 3 files written
   #   ana:   6 classes, ~40 assets, ~43 positions -> 3 files written
   #   snapshot OK: 6 files written
   ```

   Inspect the change with `git diff data/seed/` and commit it
   if the new state is the new baseline. The next `db-reset`
   reproduces the snapshotted state from scratch.
   ```

### `AGENTS.md`

No change. The existing "Seed data" rule already covers the CSV
path; the export is a new tool on that path, not a new path.

## Why this is internal-only

The script is not wired into the FastAPI app, has no route, has
no UI surface, and is not packaged for the prod image. It only
runs in the dev environment against the dev SQLite file. The
`task db-snapshot` taskipy alias makes it discoverable to
developers but invisible to end users.
