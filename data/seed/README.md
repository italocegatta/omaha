# `data/seed/` — per-profile CSV triplet

Per-profile source of truth for **asset classes**, **per-class asset
targets**, and **current broker positions**. Consumed exclusively by
the `scripts/seed_from_csv/` package (one module per concern:
`loaders.py`, `validation.py`, `profiles.py`, `modes.py`, plus
`__main__.py` for the CLI driver and `__init__.py` for the public
re-exports). Invoked via Taskipy: `task db-seed-from-csv` /
`db-seed-diff` / `db-seed-upsert` / `db-reset`.

The CSVs are the source of truth. The xlsx workbooks in
`~/github/investing/input/` and the broker export files in the same
directory were consulted exactly once during the initial bootstrap of
this folder; they are **not runtime dependencies** after that. If a
future change needs to re-bootstrap from an updated source, regenerate
the CSVs by hand (edit-then-validate workflow below).

## Files

For each profile (`italo`, `ana`):

| File                         | Header                                            | Purpose                                                         |
|------------------------------|---------------------------------------------------|-----------------------------------------------------------------|
| `{profile}_classes.csv`      | `name,target_pct,display_order,quote_kind`        | Per-profile class list. `sum(target_pct)` must equal 100. `quote_kind` must be explicit (`auto` / `manual` / `none`). |
| `{profile}_assets.csv`       | `class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code` | Per-asset target within its class. `sum(target_pct)` per class must equal 100. The three trade-control columns feed the Fase 1 rebalance foundation; `currency_code` must be one of `BRL`, `USD` (CHECK constraint `ck_asset_currency_code` in migration `0016_asset_trade_flags`). |
| `{profile}_positions.csv`    | `asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current` | Current broker position. `asset_name` must match an asset row in `{profile}_assets.csv`; `broker_ticker` is the broker-side symbol and MAY diverge from `asset_name` (e.g. `asset_name="Petrobras PN"`, `broker_ticker="PETR4"`). Uniqueness is per `(asset_name, broker_ticker)` pair — multi-broker positions on the same asset are supported. `total_invested` / `total_current` are the broker-published per-row totals; they are inserted **verbatim** (never recomputed from `qty * price`) and an empty cell parses to `NULL` (contributes `0` to the dashboard aggregate). |

`data/seed/fixtures/` is reserved for ad-hoc, non-canonical CSV fixtures
used by focused tests. Runtime seed source of truth remains the six
top-level `{profile}_*.csv` files above.

## Validation rules (run by `scripts.seed_from_csv`)

1. Header must match exactly, in order, for all three CSV kinds.
2. Class rows require non-empty `name`, `target_pct ∈ [0, 100]`,
   `display_order >= 0`, unique `name`, and `quote_kind ∈ {auto,
   manual, none}`.
3. Asset rows require non-empty `class_name` + `name`,
   `target_pct ∈ [0, 100]`, `display_order >= 0`, unique
   `(class_name, name)`, and `currency_code ∈ {BRL, USD}`.
4. `buy_enabled` / `sell_enabled` parse as permissive booleans
   (`true/false/1/0/yes/no`); empty cell defaults to `false`.
5. Every asset row must reference a `class_name` that exists in the
   matching `{profile}_classes.csv`.
6. Position rows require non-empty `asset_name` + `broker_ticker`,
   unique `(asset_name, broker_ticker)`, and `qty`, `avg_price`,
   `current_price >= 0`.
7. Every position row must reference an `asset_name` that exists in
   the matching `{profile}_assets.csv`.
8. Class `target_pct` must sum to 100 per profile, and asset
   `target_pct` must sum to 100 per class (tolerance 0.01; same
   `Falta X%` / `Sobra X%` wording as runtime validators).
9. `total_invested` / `total_current` are optional (empty cell →
   `NULL`); non-empty cell must be decimal `>= 0` and is stored
   verbatim. Seed path never recomputes totals from `qty * price`.

### Header changes are hard fails (no silent fallback)

A `{profile}_assets.csv` with the legacy 4-column header
(`class_name,name,target_pct,display_order`) is rejected by
the seed script (`scripts/seed_from_csv/`) with an `abort()`
error and exit code 1 — the same hard-fail pattern as
`quote_kind`. This forces every CSV on disk to be updated in
lockstep with the schema; no auto-upgrade with silent defaults.

## Sum invariant (validated before any DB write)

- `{profile}_classes.csv`: `sum(target_pct) == 100` (tolerance 0.01).
  Aborts with `Falta X%` / `Sobra X%` from `omaha.validators`.
- `{profile}_assets.csv`: `sum(target_pct)` per `class_name` group
  must equal 100 (tolerance 0.01). Aborts with
  `<class_name>: Falta X%` / `<class_name>: Sobra X%`.
- `{profile}_positions.csv`: no sum invariant (positions are absolute
  R$ values, not percentages).

## Non-tradeable position convention

Current canonical CSVs do **not** use the old `qty = 1` sentinel.
For non-tradeable instruments (RDB, CDB, treasury bond held to
maturity), canonical seed rows keep unit fields zeroed and carry the
broker-truth values in the explicit totals columns:

```
qty           = 0
avg_price     = 0
current_price = 0
total_invested = <broker total invested>
total_current  = <broker total current>
```

This works because the dashboard aggregate uses
`Position.total_current` / `Position.total_invested` verbatim when
present. The zeroed unit fields are descriptive placeholders only;
they are not used for portfolio footer math.

## Edit workflow

1. Edit the CSV(s) you care about in any text editor.
2. `uv run task db-seed-diff` — preview what would change without
   touching the DB. Aborts on any validation error before printing.
3. `uv run task db-seed-upsert` — apply non-destructively (creates /
   updates only, never deletes).
4. `uv run task db-seed-from-csv` — destructive single-profile reset
   (defaults to Italo; override with `-- --profile ana`). Use this when
   one profile's CSV is source of truth and the DB should reflect it.
5. `uv run task db-reset` — destructive two-profile reset via
   `scripts.reset_both_profiles.py`. Use this for canonical "ready to
   test" state.
6. Or, freeze the current DB state with `uv run task db-snapshot`
   and commit the resulting `git diff data/seed/`. The snapshot
   exports live DB state to all 6 CSVs in the canonical profile set
   (`italo`, `ana`).

`db-seed-from-csv` and `db-reset` are intentionally different:
single-profile reset vs full two-profile reset. `db-seed-diff` and
`db-seed-upsert` keep their single-profile override pattern via
`-- --profile ana --mode <m>`.

## Trade-offs

- **Non-ASCII asset names** (e.g. `Tesouro IPCA+ 2035`,
  `Caixinha Turbo NuCel`) are valid UTF-8. Python's `csv` module
  reads UTF-8 by default when given a text-mode file.
- **Zeroed unit fields on non-tradeables** are a known compromise.
  The dashboard footer stays correct because it uses explicit totals,
  but row-level `qty` / price cells do not represent literal broker
  quantities for those instruments.
- **Per-profile coupling.** Assets reference classes by `name`
  string; positions reference assets by `name` string. The seed
  script cross-references all three layers and rejects mismatches
  with a clear error.
