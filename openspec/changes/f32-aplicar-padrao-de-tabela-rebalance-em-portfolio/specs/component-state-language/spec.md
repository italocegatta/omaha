## MODIFIED Requirements

### Requirement: Data tables SHALL render sticky headers, hover lift, total row emphasis, and on-hover action column

The system SHALL render `<thead>` sticky within scroll, lift row background
on hover, emphasize the total row with bold + thicker border, and reveal
action column affordances only when the user hovers the row. Numeric columns
SHALL use tabular figures and right-align. Post-F14: asset tables use
`--surface-sunk` background (inset feel), row padding compacted to
`0.05rem` vertical, asset-table headers use a tinted background plus a
stronger separator line, and numeric cells use `--ink` at weight 600+
for maximum contrast.

Post-F32: portfolio asset tables (`.asset-table`) SHALL inherit the same
visual design as rebalance tables (`.rebalance-table`). This includes:
- Shell gradient background, border-radius 14px, heavy shadow
- Header: uppercase, `font-weight: 700`, `letter-spacing: 0.06em`,
  tinted background, hover accent lift
- Rows: alternating odd/even backgrounds, hover accent tint,
  buy/sell/hold row-level color classes
- Cells: padding matching rebalance, `font-variant-numeric: tabular-nums`,
  hairline bottom borders

Portfolio-specific exceptions (documented, not removed):
1. 2-level header (group row + subhead row) — inherits shared header base
   but keeps rowspan/colspan structure.
2. `class-totals-row` summary row — keeps sunk background and bold text,
   palette harmonized with rebalance total row.
3. Inline editing cells — keep click-to-edit UX, cell styling changes only.
4. Delete confirmations — behavior-only, no visual change needed.

#### Scenario: Sticky table header on scroll
- **WHEN** the user scrolls a page containing `.table-sticky-header`
- **THEN** the `<thead>` remains pinned to `top: 0` with
  `background: var(--surface-sunk)` and `z-index: 1`

#### Scenario: Asset table header differentiates from data rows
- **WHEN** a class section renders its `.asset-table`
- **THEN** each header cell SHALL use
  `background: color-mix(in srgb, var(--accent) 10%, var(--surface))`
- **AND** each header cell SHALL use
  `border-bottom: 2.5px solid var(--border-strong)`

#### Scenario: Sticky header is NOT applied to tables inside modals
- **WHEN** a table renders inside a `<dialog>` or modal container
- **THEN** the table does NOT receive `.table-sticky-header` (sticky
  behavior is reserved for top-level page tables only)

#### Scenario: Row hover lifts the background
- **WHEN** the user hovers the cursor over a `<tr>` in a table
- **THEN** every `<td>` in that row receives `background: var(--bg-hover)`
  for the duration of the hover

#### Scenario: Total row renders with bold + thick border-top
- **WHEN** a `<tr class="table-total">` renders at the bottom of a table
- **THEN** the row has `font-weight: 600` and
  `border-top: 2px solid var(--border-strong)`

#### Scenario: Action column is hidden in idle state
- **WHEN** the user views a table row in its idle state
- **THEN** any `<td class="row-actions">` renders with `opacity: 0`

#### Scenario: Action column reveals on row hover
- **WHEN** the user hovers the cursor over a row containing action cells
- **THEN** the action cells transition to `opacity: 1` within 80ms

#### Scenario: Action column is always visible on mobile
- **WHEN** the viewport is `max-width: 768px`
- **THEN** action cells render with `opacity: 1` regardless of hover state

#### Scenario: Asset table renders with sunk background
- **WHEN** a class section renders its asset table
- **THEN** the table SHALL use `background: var(--surface-sunk)` for an
  inset feel
- **AND** the table SHALL create visual hierarchy: page shell
  (`--surface`) > portfolio header / class section (`--surface-elevated`)
  > asset table (`--surface-sunk`)

#### Scenario: Row padding is compact
- **WHEN** asset table rows render
- **THEN** each `<td>` SHALL use `padding: 0.05rem 0.4rem` for
  extra-dense vertical compaction

#### Scenario: Numeric columns use tabular figures
- **WHEN** a `<td>` contains a numeric value (currency or percent)
- **THEN** the cell renders with `font-variant-numeric: tabular-nums` and
  `text-align: right`

#### Scenario: Numeric cells use high-contrast ink
- **WHEN** a `<td>` contains a numeric value (currency, percent, or quantity)
- **THEN** the cell SHALL render with `color: var(--ink)` and
  `font-weight: 600` or higher

#### Scenario: Portfolio asset row color-codes by trade status
- **WHEN** an asset row renders in the portfolio table
- **THEN** the row SHALL receive a color class based on trade flags:
  - `buy_enabled && !sell_enabled` → green tint (buy)
  - `!buy_enabled && sell_enabled` → red tint (sell)
  - Both enabled or both disabled → neutral (hold)
- **AND** the color SHALL match the rebalance palette:
  - Buy: `color-mix(in srgb, var(--positive) 7%, var(--surface))`
  - Sell: `color-mix(in srgb, var(--negative) 10%, var(--surface))`
  - Neutral: `color-mix(in srgb, var(--surface) 82%, var(--surface-sunk) 18%)`

#### Scenario: Portfolio table shell matches rebalance shell
- **WHEN** the portfolio page renders asset tables
- **THEN** `.portfolio-table-shell` SHALL use the same visual values as
  `.rebalance-table-shell`: `border-radius: 14px`, gradient background,
  `box-shadow: 0 18px 34px rgba(8, 10, 20, 0.14)`

#### Scenario: Portfolio table headers match rebalance headers
- **WHEN** portfolio table headers render
- **THEN** `.asset-table th` SHALL use the same visual values as
  `.rebalance-table-th`: uppercase, `font-weight: 700`,
  `letter-spacing: 0.06em`, tinted background, hover accent lift

#### Scenario: Portfolio table cells match rebalance cells
- **WHEN** portfolio table cells render
- **THEN** `.asset-table td` SHALL use the same padding and border values
  as `.rebalance-asset-cell`: `padding: 0.82rem 0.75rem`, hairline
  bottom border, `font-variant-numeric: tabular-nums` on numeric cells

#### Scenario: Trade toggle buttons match rebalance action-badge style
- **WHEN** a trade toggle button renders in the portfolio table
- **THEN** the button SHALL use the rebalance action-badge visual language:
  rounded pill shape (`border-radius: 4px`), color-coded background at
  12-18% opacity, matching foreground color

#### Scenario: Class-totals-row palette harmonizes with rebalance
- **WHEN** the class totals summary row renders
- **THEN** the row SHALL use the same background and border values as
  rebalance total rows, with `font-weight: 600` and sunk background

#### Scenario: Portfolio hover effect matches rebalance
- **WHEN** the user hovers over a portfolio asset row
- **THEN** the row SHALL highlight with the same accent tint as rebalance:
  `color-mix(in srgb, var(--accent) 10%, var(--surface))`
