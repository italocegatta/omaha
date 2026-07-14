## Context

Rebalance page (`rebalance.html`) defines `rebalancePage()` Alpine component with inline formatters: `formatBRL()`, `formatPct()`, `formatQuantity()`, `formatDeviationPp()`, `actionLabel()`, `rowClass()`, `cellClass()`, `formatCell()`, `cellInnerClass()`.

Portfolio page (`_patrimonio_add_asset_modal.html`) defines `classSection()` Alpine component with inline formatters: `formatMoney()`, `formatPct()`, `formatPctOrDash()`, `formatBRL()`, `formatBRLCompact()`, `formatQty()`, `signClass()`, `signIcon()`.

Import modal (`$store.importModal` in same file) defines its own: `formatBRL()`, `formatMoney()`, `formatPct()`, `signClass()`, `signIcon()`.

Three copies, diverging signatures (e.g. `formatMoney` handles currency code; `formatBRL` is hardcoded BRL), different null-handling (`—` vs `R$ 0,00` vs empty string).

## Goals / Non-Goals

**Goals:**
- Single JS module exporting all table formatters as pure functions
- Both Alpine components consume the same API — no behavior change
- Easy to extend for future tables (F32, any new page)
- Preserve all existing formatting output exactly

**Non-Goals:**
- Changing CSS classes or visual appearance (R30 handles CSS)
- Changing template HTML structure
- Adding new formatters not already in use
- Changing filter/sort logic (R31 handles filter panels)

## Decisions

### D1 — Module format: ES module via `<script type="module">`

**Choice**: Export functions from `static/table-formatters.js` as named ES module exports. Templates import via `<script type="module">` with static import.

**Why**: Alpine.js components are defined inline in `<script>` tags inside Jinja templates. ES modules work natively in all target browsers (no build step per PRD). The module can be imported once per page; Alpine component definitions reference the imported functions.

**Alternative considered**: Global namespace (`window.OmahaFormatters`). Rejected — pollutes global scope, no tree-shaking benefit, harder to discover usage.

### D2 — Function signatures: preserve existing behavior exactly

**Choice**: Each shared function matches the most permissive existing signature. Example: `formatMoney(value, currency)` where `currency` defaults to `'BRL'` (from portfolio's implementation). `formatQty(value, assetName)` where BTC gets 3 decimals (from rebalance's implementation).

**Why**: Refactoring slice — zero behavior change. Templates keep calling `formatMoney(a.gain_value, a.currency_code)` and `formatBRL(c.delta)` unchanged.

### D3 — `formatBRL` becomes thin wrapper

**Choice**: `formatBRL(value, fractionDigits)` delegates to `formatMoney(value, 'BRL')` internally. `formatMoney` is the canonical implementation.

**Why**: Portfolio already has multi-currency `formatMoney`. Making it canonical means any future multi-currency table gets it for free. `formatBRL` stays as convenience alias for backward compat.

### D4 — `signClass` / `signIcon` null handling: portfolio's behavior wins

**Choice**: `signClass(null)` returns `'metric-neutral'`, `signIcon(null)` returns `'remove'`. Threshold: `Math.abs(Number(value)) < 0.0001`.

**Why**: Portfolio's implementation handles null/undefined/zero explicitly. Rebalance's `rowClass` doesn't use `signClass` (it uses action-based classes), so no conflict.

### D5 — `rowClass` stays parameterized by row action

**Choice**: `rowClass(row)` returns action-based class string. Kept separate from `signClass` (which is value-sign-based).

**Why**: Rebalance rows color-code by buy/sell/hold action. Portfolio rows don't use `rowClass`. Different semantic — don't merge.

### D6 — Template wiring: `<script>` tag before Alpine init

**Choice**: Each template that defines an Alpine component adds `<script type="module">` import at the top, then the Alpine component definition references imported functions via closure.

**Why**: Alpine components are defined in inline `<script>` blocks. Importing the module at the top of the script block makes the functions available in the component's method definitions. No Alpine plugin or store needed.

## Risks / Trade-offs

- **[Risk] Import order**: Module must load before Alpine initializes the component. → Mitigation: `<script type="module">` is deferred by default; Alpine's `x-data` init runs after DOMContentLoaded. The import will resolve before Alpine processes the component.
- **[Risk] Jinja + ES module interaction**: Jinja templates output HTML; ES modules are client-side. → Mitigation: The `<script type="module">` tag lives inside the template, importing a static file. No Jinja/JS conflict.
- **[Trade-off] Function count**: 11 exported functions may feel large. → Acceptable: each is small, pure, and independently useful. Grouping by concern (formatting, sign, row/cell) keeps it navigable.
