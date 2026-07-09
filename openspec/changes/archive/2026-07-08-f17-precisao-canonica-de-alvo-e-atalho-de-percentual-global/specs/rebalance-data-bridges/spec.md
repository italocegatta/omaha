## MODIFIED Requirements

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
`target_weight_in_category` (= canonical `Asset.target_pct / 100`),
`target_weight` (= canonical `Asset.target_pct * AssetClass.target_pct / 10000`),
`asset_order` (re-numbered `0..N-1` per class),
and the omaha-specific column `quote_kind` (= `AssetClass.quote_kind`).

Target derivation SHALL happen in `Decimal` using canonical persisted values first; conversion
to `float` SHALL happen only when the final DataFrame columns are materialized for pandas /
numpy / CVXPY consumption. The builder MUST NOT treat rounded display values of
`target_pct_total` as input truth.

Empty categories or assets SHALL produce empty DataFrames with the correct column schema
(not `pd.DataFrame()` with no columns), so the solver's `merge`/`reindex` calls do not raise.

#### Scenario: Profile with three classes and five assets

- **WHEN** `build_setup_from_db` runs against a profile with three classes (target_pct 60/30/10)
  and five assets distributed across them with `buy_enabled`/`sell_enabled`/`currency_code`
  populated
- **THEN** the returned `categories` DataFrame has 3 rows summing `target_weight == 1.0`
- **AND** the returned `assets` DataFrame has 5 rows whose `target_weight` values sum to `1.0`
  within solver tolerance after final float conversion
- **AND** the canonical `target_weight_in_category` values close to `1.0` per category before
  the float boundary is crossed

#### Scenario: Global-target edits still derive canonical builder weights

- **WHEN** an asset's last edit came through the dashboard's `% ativo na carteira` shortcut
- **THEN** `build_setup_from_db` reads the persisted canonical `Asset.target_pct`
- **AND** the resulting `target_weight_in_category` / `target_weight` are derived from that
  canonical value plus the owning class target
- **AND** no client-rounded `target_pct_total` value is needed or trusted by the builder

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
