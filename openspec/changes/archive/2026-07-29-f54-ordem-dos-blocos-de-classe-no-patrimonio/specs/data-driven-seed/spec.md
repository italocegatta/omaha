## ADDED Requirements

### Requirement: Class CSV display_order encodes the normative /patrimonio block order

Each per-profile class CSV (`data/seed/{profile}_classes.csv`) SHALL assign `display_order` values that encode the normative display order of the `/patrimonio` class table blocks: `RF Pós` = 0, `RF Dinâmica` = 1, `FII` = 2, `Ações` = 3, `Internacional` = 4, `Cripto` = 5, identically in every seeded profile. Because `/patrimonio` renders class blocks ordered by `AssetClass.display_order` and the seed CSVs are the single source of truth for seed (PRD §4.3), the normative block order SHALL be carried solely by the CSV `display_order` column — no client-side or route-level reordering of `/patrimonio` class blocks.

The class CSV rows SHALL remain physically ordered by `display_order` ascending (file order == display_order order), preserving the convention consumed by the dynamic CSV↔DB seed comparison.

This requirement SHALL NOT alter class `name`, `target_pct`, or `quote_kind` values, the per-file `sum(target_pct) == 100` invariant, block content or styling, aggregations, filters, routes, or the rebalance solver. Classes created at runtime (UI/import, `display_order = max+1`) SHALL render after the six normative classes.

#### Scenario: /patrimonio blocks render in normative order after reset

- **WHEN** `task db-reset` runs against the normative class CSVs
- **AND** an authenticated user visits `/patrimonio` on either seeded profile
- **THEN** the class table blocks appear in the sequence `RF Pós`, `RF Dinâmica`, `FII`, `Ações`, `Internacional`, `Cripto`

#### Scenario: Both profiles carry the same normative display_order

- **WHEN** `data/seed/ana_classes.csv` and `data/seed/italo_classes.csv` are read
- **THEN** each file assigns `display_order` 0, 1, 2, 3, 4, 5 to `RF Pós`, `RF Dinâmica`, `FII`, `Ações`, `Internacional`, `Cripto` respectively
- **AND** the rows appear in ascending `display_order` order
- **AND** each class keeps its own `target_pct` and `quote_kind`, and each file's `sum(target_pct)` equals 100

#### Scenario: Family view follows the normative order automatically

- **WHEN** the family view aggregates classes across both seeded profiles
- **THEN** class blocks are ordered by the minimum `display_order` of their member classes
- **AND** the resulting sequence is `RF Pós`, `RF Dinâmica`, `FII`, `Ações`, `Internacional`, `Cripto`

#### Scenario: Runtime-created classes render after the normative classes

- **WHEN** a class is created via UI or import and receives `display_order = max+1`
- **AND** `/patrimonio` renders the class blocks
- **THEN** that class block appears after `Cripto`

#### Scenario: Positional class colors rotate with block position

- **WHEN** `/patrimonio` renders the class blocks in the normative order
- **THEN** each block receives the color of its rendered position from the existing positional palette (`_CLASS_COLORS`)
- **AND** the palette definition itself remains unchanged (no code change)
