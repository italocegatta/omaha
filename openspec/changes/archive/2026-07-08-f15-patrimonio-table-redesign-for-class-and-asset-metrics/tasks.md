## 1. Aggregate payload redesign

- [x] 1.1 Extend `src/omaha/routes/pages.py` aggregate builders with the financial fields needed by F15 (`qty`, `avg_price`, `gain_value`, `gain_pct`, position deviation, class deviation, portfolio deviation, grouped totals-row values)
- [x] 1.2 Decide and codify placeholder behavior for family-view target/deviation cells where one merged target is not meaningful
- [x] 1.3 Preserve existing `Compra` / `Venda` / `Moeda` payload behavior while removing reliance on the legacy asset-row `Classe` column

## 2. Table structure and Alpine behavior

- [x] 2.1 Rebuild `_patrimonio_class_section.html` grouped table headers and class totals row to match the approved mockup order
- [x] 2.2 Keep `Ganho` visually as one column while rendering separate absolute and percentual subcells for alignment
- [x] 2.3 Update `classSection` sort metadata/helpers in `_patrimonio_add_asset_modal.html` so every visible column is sortable with correct text-vs-numeric behavior
- [x] 2.4 Preserve inline-edit flows for class target and asset target values inside the redesigned table layout

## 3. Formatting and visual states

- [x] 3.1 Introduce centralized formatting helpers for money-by-currency, one-decimal percentages, rounded absolute values, and sign-aware deltas
- [x] 3.2 Update `src/omaha/static/app.css` with redesigned `--col-*` widths, grouped headers, class totals row alignment, merged-gain styling, and long-name wrapping
- [x] 3.3 Add positive/negative icon+color states for `Ganho` and `Desvio` in both class totals row and asset rows
- [x] 3.4 Update `_patrimonio_portfolio_header.html` to render split `Ganho` values with sign-state iconography

## 4. Spec and test updates

- [x] 4.1 Sync delta specs for `class-section-totals`, `dashboard-inline-editing`, and `patrimonio-portfolio-header` with implemented behavior
- [x] 4.2 Update integration/BDD assertions for grouped headers, removed `Classe` column, formatting rules, and sign-state rendering
- [x] 4.3 Update e2e selectors/assertions for sortable headers, aligned class totals row, and collapsed-state visibility
- [x] 4.4 Run `opsx list --specs` and resolve any spec-health issues before leaving apply-ready state

## 5. Verification and delivery

- [x] 5.1 Run `task lint`
- [x] 5.2 Run targeted tests (`task test-unit`, `task test-integration`, relevant e2e/bdd coverage for patrimônio)
- [x] 5.3 Run `refresh-for-test` so `/patrimonio` is live on LAN URL with known DB state
- [x] 5.4 Verify manually that grouped headers, totals alignment, sorting, formatting, and sign indicators match the approved mockup
