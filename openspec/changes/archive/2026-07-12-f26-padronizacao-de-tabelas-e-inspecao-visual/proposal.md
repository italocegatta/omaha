## Why

Tabela surface in `/patrimonio`, `/rebalanceamento`, and import review still drift in spacing, wrap, and font rhythm. Small CSS/template edits can leave headers cramped or make labels like `Atual` read with different typographic weight than neighboring cells, so visual regressions slip past behavior-only checks.

## What Changes

- Normalize shared table typography, padding, wrapping, and numeric-cell rhythm across table partials.
- Remove page-specific table overrides that create header crowding or typographic mismatch.
- Expand committed visual baselines for table-heavy states on desktop and mobile so wrap/overflow drift is reviewable.
- Add or tighten e2e visual inspection around table states so table layout issues are caught before release.
- Keep existing alignment and behavior contracts intact; no route, data, or API changes.

## Capabilities

### Modified Capabilities

- `visual-regression-baseline`: broaden visual contract to include table-heavy states and explicit readability checks for wrap, overflow, and typographic drift.

## Impact

- `src/omaha/static/app.css`
- `src/omaha/templates/_patrimonio_*.html`
- `src/omaha/templates/_rebalance_*.html`
- `src/omaha/templates/_patrimonio_add_asset_modal.html`
- `tests/visual/test_snapshots.py`
- `tests/e2e/test_asset_table.py` and related table-alignment e2e coverage
- `tests/visual/baselines/*.png`
- `DESIGN.md` if visual-gate guidance needs table-specific notes
