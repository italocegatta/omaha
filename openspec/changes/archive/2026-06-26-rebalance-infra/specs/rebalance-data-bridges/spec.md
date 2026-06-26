# Spec: rebalance-data-bridges

## Purpose

Define the pure-function bridges that translate the omaha ORM (Profile → AssetClass → Asset →
Position) into the data shapes the reference CVXPY rebalance solver expects. Phase 4
(`rebalance-engine`) consumes these bridges; Phase 3 (`rebalance-route`) wires them to a
HTTP endpoint.

## ADDED Requirements

### Requirement: PortfolioSetup builder translates ORM to DataFrame

The system SHALL provide `rebalance.builders.build_setup_from_db(db, profile)` that returns a
`PortfolioSetup` dataclass with two pandas DataFrames matching the reference algorithm's
expected schema, derived from the given `Profile`'s `AssetClass` and `Asset` rows.

The `categories` DataFrame SHALL contain one row per `AssetClass` with columns
`category_name`, `category_key`, `target_weight` (∈ [0,1], derived from
`AssetClass.target_pct / 100`), and `category_order` (re-numbered `0..N-1` regardless of
`display_order` gaps).

The `assets` DataFrame SHALL contain one row per `Asset` with columns
`asset_name`, `asset_key` (= `Asset.name.casefold()`),
`category_name`, `category_key` (= `AssetClass.name.casefold()`),
`currency_code`, `buy_enabled`, `sell_enabled`,
`target_weight_in_category` (= `Asset.target_pct / 100`),
`target_weight` (= `Asset.target_pct * AssetClass.target_pct / 10000`),
`asset_order` (re-numbered `0..N-1` per class),
and the omaha-specific column `quote_kind` (= `AssetClass.quote_kind`).

Empty categories or assets SHALL produce empty DataFrames with the correct column schema
(not `pd.DataFrame()` with no columns), so the solver's `merge`/`reindex` calls do not raise.

#### Scenario: Profile with three classes and five assets

- **WHEN** `build_setup_from_db` runs against a profile with three classes (target_pct 60/30/10)
  and five assets distributed across them with `buy_enabled`/`sell_enabled`/`currency_code`
  populated
- **THEN** the returned `categories` DataFrame has 3 rows summing `target_weight == 1.0`
  and the returned `assets` DataFrame has 5 rows whose `target_weight` values sum to `1.0`
  (tolerance `1e-6`) and whose `target_weight_in_category` values sum to `1.0` per category

#### Scenario: Empty profile returns empty DataFrames with full schema

- **WHEN** `build_setup_from_db` runs against a profile with no `AssetClass` rows
- **THEN** `categories` is an empty DataFrame with all four required columns and
  `assets` is an empty DataFrame with all eleven required columns (no `KeyError` on downstream
  merge)

#### Scenario: Asset name collision across classes is shadowed with warning

- **WHEN** two `AssetClass` rows under the same profile contain an `Asset` with the same
  `name` (cross-class collision)
- **THEN** the `assets` DataFrame contains exactly one row per `asset_key` (the first by
  `display_order`, ties broken by `id`), and the builder returns a warnings list with one
  entry per collision naming both `asset_class_id` values

### Requirement: Position builder aggregates per-asset holdings

The system SHALL provide `rebalance.builders.build_position_frame(db, profile)` that returns
a pandas DataFrame with one row per `Asset` (whether or not it has positions), aggregating
all matching `Position` rows by `asset_key`.

The DataFrame SHALL contain columns
`asset_key`, `asset_name`, `category_name`, `category_key`,
`quantity` (sum of `Position.qty`),
`invested_value` (sum of `Position.total_invested`, treating `NULL` as `0`),
`current_value` (sum of `Position.total_current`, treating `NULL` as `0`),
and `current_weight` (= `current_value / sum(current_value)`, or `0.0` when total is `0`).

Aggregation MUST sum the broker-published `total_invested` / `total_current` columns directly;
it MUST NOT recompute `qty * price` (the broker totals are the source of truth — see
`broker-csv-import-totals` change).

#### Scenario: Asset with three positions aggregates totals

- **WHEN** an `Asset` has three `Position` rows with `total_invested` `100`, `200`, `300` and
  `total_current` `110`, `220`, `330`
- **THEN** the resulting row has `quantity` = sum of `qty`, `invested_value` = `600`,
  `current_value` = `660`

#### Scenario: Asset with no positions has zero totals

- **WHEN** an `Asset` has zero `Position` rows
- **THEN** the resulting row has `quantity = 0`, `invested_value = 0`, `current_value = 0`,
  `current_weight = 0`

#### Scenario: Empty portfolio produces zero current_weight per asset

- **WHEN** the profile's positions sum to `total_current == 0`
- **THEN** every row's `current_weight` is `0.0` (not `NaN`, not the result of division)

### Requirement: Quote symbol resolution adds `.SA` for BRL tickers

The system SHALL provide `rebalance.market_prices.resolve_quote_symbol(asset_name, currency_code)`
that returns a yfinance-compatible symbol string. For `currency_code == "BRL"` and a
non-empty `asset_name`, the symbol SHALL have `.SA` appended when not already present.
For `currency_code == "USD"` or any other allowlist value, the symbol SHALL be returned
verbatim (no suffix added).

Empty `asset_name` SHALL return an empty string (no symbol).

#### Scenario: BRL ticker gets .SA suffix

- **WHEN** `resolve_quote_symbol("PETR4", "BRL")` is called
- **THEN** the return value is `"PETR4.SA"`

#### Scenario: BRL ticker already suffixed is idempotent

- **WHEN** `resolve_quote_symbol("PETR4.SA", "BRL")` is called
- **THEN** the return value is `"PETR4.SA"` (no double suffix)

#### Scenario: USD ticker is not suffixed

- **WHEN** `resolve_quote_symbol("AAPL", "USD")` is called
- **THEN** the return value is `"AAPL"`

#### Scenario: Empty asset name returns empty symbol

- **WHEN** `resolve_quote_symbol("", "BRL")` is called
- **THEN** the return value is `""`

### Requirement: OmahaMarketPriceLookup satisfies the Protocol via QuoteCache

The system SHALL provide `rebalance.quotes_adapter.OmahaMarketPriceLookup` that implements
the `MarketPriceLookup` Protocol from `rebalance.market_prices`. Its `get_quotes(assets)`
method SHALL return a DataFrame with columns
`asset_key`, `quote_symbol`, `quote_price`, `quote_currency`, `quote_timestamp`,
`quote_status`, `usdbrl_rate`,
one row per input asset row.

For each input asset:
- `quote_symbol` is `resolve_quote_symbol(asset.name, asset.currency_code)`, or `""` if the
  asset has no `broker_ticker` (no `Position` rows).
- `quote_kind == "auto"` assets consult `QuoteCache.get_many([quote_symbol])`. A fresh row
  produces `quote_status = "available"`, `quote_price = cache.price`. A stale or missing
  row produces `quote_status = "unavailable"`, `quote_price = NaN`.
- `quote_kind ∈ {"none", "manual"}` assets fall back to the asset's first `Position.current_price`
  (by `Position.id` ASC), with `quote_status = "not-requested"` and
  `quote_currency = Asset.currency_code`. If no positions exist, `quote_price = 0.0` and
  `quote_status = "not-requested"`.
- For `currency_code == "USD"` assets, `usdbrl_rate` is the cached price of `BRL=X` (NaN if
  unavailable). For BRL assets, `usdbrl_rate` is `NaN`.

#### Scenario: Auto BRL asset with fresh cache returns available quote

- **WHEN** the adapter queries an asset with `quote_kind = "auto"`, `currency_code = "BRL"`,
  `broker_ticker = "PETR4"`, and the `QuoteCache` holds a fresh row for `"PETR4.SA"` at price
  `38.50` (currency `BRL`)
- **THEN** the output row has `quote_symbol = "PETR4.SA"`, `quote_price = 38.50`,
  `quote_currency = "BRL"`, `quote_status = "available"`, `usdbrl_rate = NaN`

#### Scenario: Auto BRL asset with stale cache returns unavailable

- **WHEN** the cache holds a `PETR4.SA` row older than `QUOTE_TTL_SECONDS`
- **THEN** `quote_status = "unavailable"` and `quote_price` is `NaN`

#### Scenario: None-class asset falls back to broker price

- **WHEN** the adapter queries an asset with `quote_kind = "none"` and one `Position` whose
  `current_price = 145.32`
- **THEN** `quote_price = 145.32`, `quote_status = "not-requested"`,
  `quote_currency = asset.currency_code`

#### Scenario: USD asset populates usdbrl_rate from BRL=X

- **WHEN** the adapter queries an asset with `currency_code = "USD"` and the cache holds a
  fresh `BRL=X` row at price `5.12`
- **THEN** `usdbrl_rate = 5.12` and the row's own `quote_price` is filled from the asset's
  USD symbol (e.g. `AAPL`)

#### Scenario: USD asset with missing BRL=X is marked unavailable

- **WHEN** the cache has no `BRL=X` row (or it is stale)
- **THEN** the USD asset row has `quote_status = "unavailable"` regardless of its own quote
  freshness (FX dependency makes the price unactionable)

#### Scenario: Asset with no Position returns zero quote

- **WHEN** the adapter queries an asset with zero `Position` rows
- **THEN** `quote_symbol = ""`, `quote_price = 0.0`, `quote_status = "not-requested"`

### Requirement: QuoteService fetches BRL=X when any USD asset exists

The system SHALL extend `QuoteService._collect_symbols` to additionally include the symbol
`BRL=X` in the list returned for the refresh batch when at least one `Asset` row exists with
`currency_code = "USD"` (across all profiles). When no USD asset exists, the symbol list is
unchanged from the current behavior.

#### Scenario: USD assets present triggers BRL=X refresh

- **WHEN** the refresh tick runs and at least one `Asset.currency_code == "USD"` exists in
  the database
- **THEN** `BRL=X` is included in the symbols list passed to the provider

#### Scenario: No USD assets leaves the symbol list unchanged

- **WHEN** the refresh tick runs and no `Asset.currency_code == "USD"` exists
- **THEN** `BRL=X` is **not** in the symbols list (no extra yfinance HTTP call)

### Requirement: Empty class with non-zero target emits a warning

The `build_setup_from_db` function SHALL return a warnings list (in addition to the
`PortfolioSetup` dataclass) containing one entry per `AssetClass` whose `target_pct > 0`
but which has zero `Asset` rows. The warning text SHALL identify the class by name and target
percentage.

#### Scenario: Empty class with target 20% emits a warning

- **WHEN** the profile has an `AssetClass` named `"Crypto"` with `target_pct = 20` and zero
  `Asset` rows
- **THEN** the warnings list contains `"Classe 'Crypto' está vazia mas com target_pct=20.00%; solver irá alocar caixa residual."`

#### Scenario: Empty class with target 0% does not warn

- **WHEN** the profile has an `AssetClass` with `target_pct = 0` and zero `Asset` rows
- **THEN** no warning is emitted for that class (the solver will not allocate to it anyway)
