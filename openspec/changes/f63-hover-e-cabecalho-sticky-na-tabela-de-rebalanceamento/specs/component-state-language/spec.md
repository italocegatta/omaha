## ADDED Requirements

### Requirement: Rebalance asset table SHALL use existing sticky and hover table states

The single top-level rebalance asset table SHALL opt into the existing table-state language without creating a new visual pattern. Its header cells SHALL remain sticky at `top: 0` with existing header contrast, and every data cell in a hovered asset row SHALL use the existing `--bg-hover` cue for the duration of pointer hover. Idle zebra and action-state backgrounds SHALL remain unchanged outside hover.

#### Scenario: Rebalance header remains visible during page scroll

- **WHEN** the user scrolls a populated `/rebalanceamento` page past the asset table header
- **THEN** `data-testid="rebalance-asset-table"` has existing `table-sticky-header` behavior
- **AND** its `<thead>` cells remain `position: sticky` with `top: 0` and `z-index: 1`
- **AND** no new internal table scroll container is introduced

#### Scenario: Rebalance row hover lifts every cell

- **WHEN** the user hovers any rendered `rebalance-asset-row`
- **THEN** every `<td>` in that row receives `background: var(--bg-hover)` for hover duration
- **AND** row content, action controls, sort state, filters, and data do not change

#### Scenario: Rebalance idle row states remain unchanged

- **WHEN** the pointer is not over a rebalance asset row
- **THEN** existing odd/even zebra backgrounds and buy/sell/neutral state colors remain in force
- **AND** no persistent selection or tooltip is rendered

#### Scenario: Patrimônio table remains source-pattern stable

- **WHEN** the user renders or hovers a patrimônio asset table
- **THEN** its existing sticky-header and row-hover behavior remains unchanged
- **AND** F63 adds no new class, handler, or content to `_patrimonio_class_section.html`
