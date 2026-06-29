# `data/seed/` — per-profile CSV triplet

Per-profile source of truth for **asset classes**, **per-class asset
targets**, and **current broker positions**. Consumed exclusively by
`scripts/seed_from_csv.py` (Taskipy: `task db-seed-from-csv` /
`db-seed-diff` / `db-seed-upsert` / `db-reset`).

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
| `{profile}_classes.csv`      | `name,target_pct,display_order,quote_kind`        | Per-profile class list. `sum(target_pct)` must equal 100. `quote_kind` defaults to `none`. |
| `{profile}_assets.csv`       | `class_name,name,target_pct,display_order,buy_enabled,sell_enabled,currency_code` | Per-asset target within its class. `sum(target_pct)` per class must equal 100. The three trade-control columns feed the Fase 1 rebalance foundation; `currency_code` must be one of `BRL`, `USD` (CHECK constraint `ck_asset_currency_code` in migration `0016_asset_trade_flags`). |
| `{profile}_positions.csv`    | `asset_name,broker_ticker,qty,avg_price,current_price,total_invested,total_current` | Current broker position. `asset_name` must match an asset row in `{profile}_assets.csv`; `broker_ticker` is the broker-side symbol and MAY diverge from `asset_name` (e.g. `asset_name="Petrobras PN"`, `broker_ticker="PETR4"`). Uniqueness is per `(asset_name, broker_ticker)` pair — multi-broker positions on the same asset are supported. `total_invested` / `total_current` are the broker-published per-row totals; they are inserted **verbatim** (never recomputed from `qty * price`) and an empty cell parses to `NULL` (contributes `0` to the dashboard aggregate). |

## Validation rules (run by `seed_from_csv.py`)

1. Header is required.
2. `target_pct` must be a number in `[0, 100]`.
3. `name` must be unique within the file (per file, for classes; per
   `(class_name, name)` for assets).
4. Every row in `{profile}_assets.csv` must reference a `class_name`
   that exists in `{profile}_classes.csv`.
5. Every row in `{profile}_positions.csv` must reference an `asset_name`
   that exists in `{profile}_assets.csv`.
6. `qty`, `avg_price`, `current_price` must be `>= 0`.
7. `quote_kind` must be one of `auto`, `manual`, `none`. See the
   `asset-class-quote-kind` capability spec in
   `openspec/changes/add-market-quote-service/specs/` for the policy
   semantics; the short version is `auto` means the QuoteService
   fetches a live price, `none` (and `manual` for v1) keeps the
   broker CSV's `current_price` as the source of truth.
8. `buy_enabled` / `sell_enabled` parse as permissive booleans
   (`true/false/1/0/yes/no`); empty cell defaults to `false`.
   `currency_code` must be one of `BRL`, `USD` (case-insensitive;
   the loader upper-cases the value before insert). The DB
   `ck_asset_currency_code` CHECK rejects anything else.
9. `total_invested` / `total_current` are optional (empty cell →
   `NULL`); non-empty cell must be a decimal `>= 0`. They are
   inserted verbatim into `Position.total_invested` /
   `Position.total_current` — the seed script never falls back to
   `qty * price` (see the `broker-csv-import-totals` change for
   why this invariant matters).

### Header changes are hard fails (no silent fallback)

A `{profile}_assets.csv` with the legacy 4-column header
(`class_name,name,target_pct,display_order`) is rejected by
`scripts/seed_from_csv.py` with an `abort()` error and exit code
1 — the same hard-fail pattern as `quote_kind`. This forces every
CSV on disk to be updated in lockstep with the schema; no
auto-upgrade with silent defaults.

## Sum invariant (validated before any DB write)

- `{profile}_classes.csv`: `sum(target_pct) == 100` (tolerance 0.01).
  Aborts with `Falta X%` / `Sobra X%` from `omaha.validators`.
- `{profile}_assets.csv`: `sum(target_pct)` per `class_name` group
  must equal 100 (tolerance 0.01). Aborts with
  `<class_name>: Falta X%` / `<class_name>: Sobra X%`.
- `{profile}_positions.csv`: no sum invariant (positions are absolute
  R$ values, not percentages).

## Non-tradeable position convention

For non-tradeable instruments (RDB, CDB, treasury bond held to
maturity) the broker CSV reports `Qtd = "-"` and `Preço médio = "-"`.
The seed represents these with a sentinel:

```
qty         = 1
avg_price   = total_investido
current_price = total_atual
```

This works because the dashboard computes
`current_value = qty × current_price` and
`invested = qty × avg_price`. With the sentinel, both equal the
broker-truth numbers (`total_atual` and `total_investido`
respectively). The `qty = 1` is a documented lie — see "Trade-offs"
below.

The seed script picks the sentinel automatically when both `Qtd` and
`Preço médio` are `-` in the source posicao CSV.

## Edit workflow

1. Edit the CSV(s) you care about in any text editor.
2. `uv run task db-seed-diff` — preview what would change without
   touching the DB. Aborts on any validation error before printing.
3. `uv run task db-seed-upsert` — apply non-destructively (creates /
   updates only, never deletes).
4. `uv run task db-reset` — destructive: wipes `positions`,
   `import_previews`, `assets`, `asset_classes` for the Italo profile
   and re-seeds from scratch. Use this only when the CSV is the new
   source of truth and the DB should reflect it.
5. Or, freeze the current DB state with `uv run task db-snapshot`
   and commit the resulting `git diff data/seed/`. The snapshot
   exports live DB state to all 6 CSVs in the canonical profile set
   (`italo`, `ana`).

`db-seed-from-csv` aliases to the destructive `db-reset` for
convenience; pass `-- --profile ana --mode <m>` for Ana or other
modes.

## Trade-offs

- **Non-ASCII asset names** (e.g. `Tesouro IPCA+ 2035`,
  `Caixinha Turbo NuCel`) are valid UTF-8. Python's `csv` module
  reads UTF-8 by default when given a text-mode file.
- **Sentinel `qty = 1`** is a known lie. The dashboard renders a
  literal `1` in the Qtd column for an RDB with no countable units.
  `current_value` and `invested` are correct. A future change can make
  `Position.qty` nullable and drop the sentinel.
- **Per-profile coupling.** Assets reference classes by `name`
  string; positions reference assets by `name` string. The seed
  script cross-references all three layers and rejects mismatches
  with a clear error.