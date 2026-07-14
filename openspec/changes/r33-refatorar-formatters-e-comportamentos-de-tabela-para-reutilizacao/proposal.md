## Why

Rebalance and portfolio tables duplicate JavaScript formatters with different names and inconsistent behavior. `rebalancePage()` has `formatBRL()`, `formatPct()`, `formatQuantity()`, `rowClass()`, `cellClass()`, `formatCell()`, `actionLabel()`. `classSection()` has `formatMoney()`, `formatPctRounded()`, `formatQty()`, `signClass()`, `signIcon()`. The import modal (`$store.importModal`) has its own `formatBRL()`, `formatMoney()`, `formatPct()`, `signClass()`, `signIcon()`. Three copies of the same logic, diverging implementations (e.g. `formatMoney` handles multi-currency; `formatBRL` is BRL-only), and no shared API for future tables.

Extracting a shared module eliminates drift, makes F32 (port rebalance visual to portfolio) mechanical, and gives any new table the same formatting API for free.

## What Changes

- **New shared JS module** (`static/table-formatters.js`): exports pure functions — `formatMoney(value, currency)`, `formatPct(value)`, `formatPctRounded(value)`, `formatQty(value, assetName)`, `formatDeviationPp(value)`, `signClass(value)`, `signIcon(value)`, `rowClass(row, actionMap)`, `cellClass(row, column, opts)`, `formatCell(row, column, formatters)`, `actionLabel(action)`.
- **Rebalance component** (`rebalancePage()`): replace inline formatter definitions with calls to shared module. No behavior change — same output, same CSS classes.
- **Portfolio component** (`classSection()`): replace inline formatter definitions with calls to shared module. Multi-currency `formatMoney` becomes the canonical implementation (BRL-only `formatBRL` becomes `formatMoney(value, 'BRL')`).
- **Import modal** (`$store.importModal`): replace inline `formatBRL`, `formatMoney`, `formatPct`, `signClass`, `signIcon` with shared module calls.
- **No behavior change**: formatting output, CSS class names, sign logic, and row color-coding remain identical.

## Capabilities

### New Capabilities
- `shared-table-formatters`: Centralized JS/Alpine formatting module for numeric values (BRL, USD, %, quantity), sign logic (signClass/signIcon), row color-coding, and cell formatting. Consumed by rebalance, portfolio, and import modal.

### Modified Capabilities
- `rebalance-page`: Formatter implementation changes from inline to shared module import. No spec-level behavior change.
- `patrimonio-portfolio-header`: Formatter implementation changes from inline to shared module import. No spec-level behavior change.

## Impact

- **Files created**: `src/omaha/static/table-formatters.js`
- **Files modified**: `src/omaha/templates/rebalance.html`, `src/omaha/templates/_patrimonio_add_asset_modal.html`
- **Templates unchanged**: `_rebalance_plan.html` and `_patrimonio_class_section.html` call Alpine methods by name — method names stay the same, only implementation source changes
- **No API changes**: formatters are pure client-side functions
- **No test marker changes**: no new test files
- **Dependency**: R30 (shared CSS) should be applied first — this slice handles JS only
