## Why

`/rebalanceamento` asset table lacks two existing readability cues already available in `/patrimonio`: row-wide hover feedback and a sticky header during page scroll. Porting those cues makes dense rebalance data easier to scan without changing its data or interaction contract.

Scope is owner-approved for proposal. Apply is gated on F60 reaching `Applied`, owner visual validation of F60, and owner approval of a static mock, prototype, or browser rendering for this slice.

## What Changes

- Port existing patrimoine row-hover feedback to the single `rebalance-asset-table`, affecting the whole hovered data row only while the pointer is over it.
- Port existing sticky-header behavior to the rebalance table header so its filters and labels remain readable during page scroll.
- Preserve patrimoine behavior byte/semantically unchanged.
- Preserve rebalance filters, columns, sorting, data, actions, zebra rows, layout, and all other behavior.
- Do not add tooltips, persistent selection, new internal scroll, generic alternate patterns, or unrelated refactors.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `component-state-language`: extend existing table hover and sticky-header requirements to the rebalance asset table while preserving current portfolio behavior.
- `rebalance-page`: require the single rebalance asset table to expose existing row-hover and sticky-header cues without changing its data or interaction surface.

## Impact

- Runtime surface: `_rebalance_plan.html` and `app.css`; `_patrimonio_class_section.html` is inspection-only and must remain unchanged.
- Verification: focused rebalance integration assertions in `tests/test_rebalance_page.py` and browser visual assertions in `tests/visual/test_snapshots.py`.
- No API, model, database, seed, route, filter, sort, column, action, or public data changes.
