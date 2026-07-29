## ADDED Requirements

### Requirement: Blocked assets excluded from asset plan table

The system SHALL exclude from the asset plan table any asset where `buy_enabled == False AND sell_enabled == False`. These assets are permanently locked ("ativo travado no setup") and always render as "manter" with zero trade amounts — they contribute no actionable information to the operator.

Assets with at least one side enabled (`buy_enabled == True OR sell_enabled == True`) SHALL remain visible in the table regardless of their computed action.

The filter SHALL apply only to the asset plan table display. Category summary cards, waterfall charts, plan metrics, and warnings SHALL reflect the complete portfolio including blocked assets.

#### Scenario: Doubly blocked asset is hidden from table

- **WHEN** the plan contains an asset with `buy_enabled = False` AND `sell_enabled = False`
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** the asset does NOT appear in the asset plan table
- **AND** `data-testid="rebalance-asset-table"` contains no row with that asset's `data-asset-key`

#### Scenario: Asset with buy disabled but sell enabled remains visible

- **WHEN** the plan contains an asset with `buy_enabled = False` AND `sell_enabled = True`
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** the asset appears in the asset plan table
- **AND** the row carries the correct `data-asset-key`

#### Scenario: Asset with sell disabled but buy enabled remains visible

- **WHEN** the plan contains an asset with `buy_enabled = True` AND `sell_enabled = False`
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** the asset appears in the asset plan table
- **AND** the row carries the correct `data-asset-key`

#### Scenario: Category summary cards include blocked assets

- **WHEN** the plan contains blocked assets (`buy_enabled = False AND sell_enabled = False`)
- **AND** `GET /rebalanceamento` renders the plan
- **THEN** category summary cards reflect the complete portfolio values including blocked assets
- **AND** waterfall charts render with the full category totals

#### Scenario: Plan metrics include blocked assets

- **WHEN** the plan contains blocked assets
- **THEN** `metrics.contribution`, `metrics.total_buy`, `metrics.total_sell`, and `metrics.residual_cash` reflect the complete plan including blocked assets
- **AND** the displayed metric values are unchanged from the unfiltered plan
