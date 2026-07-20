## MODIFIED Requirements

### Requirement: Inline edit preserves the edited row's visual position

The asset-table view MUST keep the just-edited row in the same
ordinal position it occupied before the edit, even when the new
`target_pct` would naturally re-sort the row elsewhere under the
current sort. The freeze is released on the next user-driven
`sortBy` click (clicking a column header) or on a new edit on a
different asset. The freeze is **not** released on successful
PATCH — releasing on PATCH would cause the row to jump the
instant the response lands, which is the user-perceived bug the
freeze exists to prevent.

After any successful PATCH that mutates `displayAssets` (via
`commitEdit` or `commitEditTotal`), the component MUST re-run
`_initFilterBounds()` to recompute `headerRangeFilters` from the
updated asset data. This ensures column range filters stay in sync
with the actual data bounds and rows are not incorrectly filtered
out.

#### Scenario: Editing the top row keeps it on top

- **GIVEN** a class "RF Test" with 3 assets in this order under
  the default sort (`target_pct` asc): "Alpha" 10%, "Bravo" 20%,
  "Charlie" 30%
- **WHEN** the user clicks the "alvo % classe" cell of the row
  holding "Alpha" (the top row), types 80, presses Enter
- **THEN** the row holding "Alpha" is still the top row in the
  class table
- **AND** the cell now shows "80.00%"

#### Scenario: Freezing is released on the next sort click

- **GIVEN** the previous scenario's state (Alpha 80% pinned to
  the top)
- **WHEN** the user clicks the "Alvo % classe" column header
  to re-sort
- **THEN** the row holding "Alpha" is no longer pinned — it sits
  in the natural position for `target_pct=80` (i.e. among the
  other high-target assets, not necessarily at the top)

#### Scenario: Filter bounds stay in sync after PATCH

- **GIVEN** a class with 3 assets all at 10% target
- **WHEN** the user edits "Alpha" to 80% via inline edit
- **THEN** the row for "Alpha" remains visible in the table
- **AND** the column range filter bounds reflect the new data
  range (min=10, max=80) instead of the stale init-time bounds
  (min=10, max=10)
