# Tasks — F18 Rebalanceamento UI

> **Status: All tasks complete** — 2026-07-09

## 1. Schema + Glue (backend)

### 1.1 Add `target_pct`, `current_pct`, `deviation_pct` to `RebalanceCategoryPlanRow`

File: `src/omaha/rebalance/schemas.py`

Add three optional float fields with default `0.0`:
- `target_pct: float = 0.0`
- `current_pct: float = 0.0`
- `deviation_pct: float = 0.0`

### 1.2 Add `deviation_value`, `deviation_pct` to `RebalanceAssetPlanRow`

File: `src/omaha/rebalance/schemas.py`

Add two optional float fields with default `0.0`:
- `deviation_value: float = 0.0`
- `deviation_pct: float = 0.0`

### 1.3 Compute new fields in glue

File: `src/omaha/rebalance/glue.py`

After solver returns the native plan and before mapping to wire format:
1. Compute `total_portfolio = sum(row.current_value for row in asset_plan)`
2. For each category row:
   - `current_pct = (current_value / total_portfolio * 100)` if `total_portfolio > 0` else `0`
   - `target_pct = sum(target_value for assets in category) / total_portfolio * 100`
   - `deviation_pct = current_pct - target_pct`
3. For each asset row:
   - `deviation_value = current_value - target_value`
   - `deviation_pct = ((current_value - target_value) / target_value * 100)` if `target_value != 0` else `0.0`

### 1.4 Update existing tests for new schema fields

Files: `tests/test_rebalance_route.py`, `tests/test_rebalance_page.py`

- Assert new fields exist on serialized rows
- Assert deviation calculations are correct for known fixture values
- Assert division-by-zero case (`target_value = 0`) returns `deviation_pct = 0.0`

## 2. Template — Parameter bar

### 2.1 Replace stat grid with compact params bar

File: `src/omaha/templates/_rebalance_plan.html`

Remove the `<section class="rebalance-stat-grid">` block (6 cards).

Add new `<div class="rebalance-params-bar" data-testid="rebalance-params-bar">`
with 4 inline children:
1. Label + input for Aporte (R$) — preserve `data-testid="rebalance-contribution-input"`
2. Label + input for Desvio mínimo (R$) — `data-testid="rebalance-threshold-abs"`, default `1000`
3. Label + input for Desvio mínimo (%) — `data-testid="rebalance-threshold-pct"`, default `1`
4. Submit button — preserve `data-testid="rebalance-submit-btn"`

Inputs 2-3 are NOT form fields (no `name` attribute). They bind to Alpine
state `thresholdAbs` and `thresholdPct` via `x-model.number`.

### 2.2 Move form element to wrap params bar

File: `src/omaha/templates/rebalance.html`

The `<form class="rebalance-form">` currently wraps only the aporte input.
Restructure so the form wraps the entire params bar (aporte input + button),
while threshold inputs sit outside the form (Alpine-only state).

## 3. Template — Class deviation summary

### 3.1 Replace category table with horizontal class cards

File: `src/omaha/templates/_rebalance_plan.html`

Remove the `<section class="rebalance-category-section">` with the 4-column
`<table>`.

Add `<section class="rebalance-class-summary" data-testid="rebalance-class-summary">`
containing a flex container with one card per category:

```html
<template x-for="c in displayCategories" :key="c.category_name">
  <div class="rebalance-class-card"
       :class="classCardClass(c)"
       :data-testid="'rebalance-class-card-' + c.category_name">
    <span class="rebalance-class-card-name" x-text="c.category_name"></span>
    <div class="rebalance-class-card-metrics">
      <span>Atual <strong x-text="formatPct(c.current_pct)"></strong></span>
      <span>Alvo <strong x-text="formatPct(c.target_pct)"></strong></span>
      <span :class="c.deviation_pct >= 0 ? 'rebalance-deviation--pos' : 'rebalance-deviation--neg'">
        <span x-text="formatDeviationPp(c.deviation_pct)"></span>
      </span>
      <span :class="c.delta >= 0 ? 'rebalance-deviation--pos' : 'rebalance-deviation--neg'">
        <span x-text="formatBRL(c.delta)"></span>
      </span>
    </div>
    <div class="rebalance-class-card-projected">
      <span>Projetado <strong x-text="formatPct(c.projected_pct)"></strong></span>
    </div>
  </div>
</template>
```

### 3.2 Add `formatPct` and `formatDeviationPp` helpers to Alpine

File: `src/omaha/templates/rebalance.html`

Add to `rebalancePage`:
- `formatPct(v)` — returns `v.toFixed(1) + '%'`
- `formatDeviationPp(v)` — returns signed pp string like `+2.0 pp` or `-1.5 pp`
- `classCardClass(c)` — returns `'rebalance-class-card--over'` if
  `Math.abs(c.deviation_pct) >= this.thresholdPct` else `'rebalance-class-card--ok'`

### 3.3 Compute `projected_pct` for category cards

File: `src/omaha/templates/rebalance.html`

In the `init()` or `sortByCategory()`, compute `projected_pct` for each
category row: `projected_pct = (c.projected_value / totalProjected * 100)`.
Store on the displayCategories array.

## 4. Template — Asset table redesign

### 4.1 Add Desvio columns to asset table

File: `src/omaha/templates/_rebalance_plan.html`

After the "Alvo" `<th>`, add two new `<th>`:
- Desvio (R$) — `data-testid="rebalance-asset-th-deviation-value"`,
  `@click="sortBy('deviation_value')"`
- Desvio (%) — `data-testid="rebalance-asset-th-deviation-pct"`,
  `@click="sortBy('deviation_pct')"`

In the row template, add two `<td>`:
- Desvio (R$): `x-text="formatBRL(row.deviation_value)"`,
  class with pos/neg coloring
- Desvio (%): `x-text="formatDeviationPp(row.deviation_pct)"`,
  class with pos/neg coloring

### 4.2 Add filter bar above asset table

File: `src/omaha/templates/_rebalance_plan.html`

Add `<div class="rebalance-filter-bar" data-testid="rebalance-filter-bar">`
before the `<table>`:

1. Classe filter: dropdown trigger + checkbox list
   ```html
   <div class="rebalance-filter-group" x-data="{open: false}">
     <button @click="open = !open" class="rebalance-filter-trigger">
       Classe <span x-text="selectedClasses.length === 0 ? '(todas)' : selectedClasses.length + ' selecionada(s)'"></span>
     </button>
     <div class="rebalance-filter-panel" x-show="open" x-cloak @click.outside="open = false">
       <label class="rebalance-filter-option">
         <input type="checkbox" @change="toggleAllClasses()" :checked="selectedClasses.length === 0">
         <span>Todas</span>
       </label>
       <template x-for="cls in uniqueClasses" :key="cls">
         <label class="rebalance-filter-option">
           <input type="checkbox" :checked="isClassSelected(cls)" @change="toggleClassFilter(cls)">
           <span x-text="cls"></span>
         </label>
       </template>
     </div>
   </div>
   ```

2. Ação filter: same pattern with `uniqueActions = ['Comprar', 'Vender', 'Manter']`

3. Search input:
   ```html
   <input type="search" placeholder="Buscar ativo..."
          x-model="searchTerm" data-testid="rebalance-filter-search"
          class="rebalance-filter-search">
   ```

### 4.3 Add filteredRows computed to Alpine

File: `src/omaha/templates/rebalance.html`

Add to `rebalancePage`:
```js
selectedClasses: [],
selectedActions: [],
searchTerm: '',
get uniqueClasses() { return [...new Set(this.plan.asset_plan.map(r => r.category_name))].sort(); },
get uniqueActions() { return ['Comprar', 'Vender', 'Manter']; },
get filteredRows() {
  var rows = this.displayRows;
  if (this.selectedClasses.length > 0) {
    rows = rows.filter(r => this.selectedClasses.includes(r.category_name));
  }
  if (this.selectedActions.length > 0) {
    rows = rows.filter(r => this.selectedActions.includes(this.actionLabel(r.action)));
  }
  if (this.searchTerm.trim()) {
    var q = this.searchTerm.trim().toLowerCase();
    rows = rows.filter(r => r.asset_name.toLowerCase().includes(q));
  }
  return rows;
},
toggleClassFilter(cls) { /* toggle in/out of selectedClasses */ },
toggleActionFilter(action) { /* toggle in/out of selectedActions */ },
isClassSelected(cls) { return this.selectedClasses.length === 0 || this.selectedClasses.includes(cls); },
isActionSelected(action) { return this.selectedActions.length === 0 || this.selectedActions.includes(action); },
toggleAllClasses() { this.selectedClasses = []; },
toggleAllActions() { this.selectedActions = []; },
```

Update `<template x-for>` to use `filteredRows` instead of `displayRows`.

### 4.4 Add rowClass function to Alpine

File: `src/omaha/templates/rebalance.html`

```js
rowClass(row) {
  if (row.action === 'hold') return 'rebalance-asset-row--neutral';
  if (Math.abs(row.deviation_pct) >= this.thresholdPct ||
      Math.abs(row.deviation_value) >= this.thresholdAbs) {
    return 'rebalance-asset-row--over';
  }
  return 'rebalance-asset-row--ok';
}
```

Apply to `<tr>`: `:class="rowClass(row)"`

### 4.5 Update sort comparators for new fields

File: `src/omaha/templates/rebalance.html`

Add `deviation_value` and `deviation_pct` to `NUMERIC_KEYS` in
`rebalanceSortFn`.

## 5. CSS

### 5.1 Remove stat grid styles

File: `src/omaha/static/app.css`

Remove:
- `.rebalance-stat-grid` (lines 2885-2901)
- `.rebalance-stat` (lines 2904-2912)
- `.rebalance-stat-label` (lines 2914-2920)
- `.rebalance-stat-value` (lines 2922-2927)

### 5.2 Add params bar styles

File: `src/omaha/static/app.css`

```css
.rebalance-params-bar {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin: 1rem 0;
  flex-wrap: wrap;
}
.rebalance-params-bar .rebalance-form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
.rebalance-params-bar label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--ink-muted);
  font-weight: 500;
}
.rebalance-params-bar input[type="number"] {
  width: 140px;
  padding: 0.4rem 0.5rem;
  font: inherit;
  font-size: 0.9rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--ink);
}
```

### 5.3 Add class card styles

```css
.rebalance-class-summary {
  display: flex;
  gap: 0.75rem;
  overflow-x: auto;
  padding: 0.5rem 0;
  margin: 1rem 0;
}
.rebalance-class-card {
  min-width: 160px;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  border: 1px solid var(--border);
  border-left: 3px solid var(--border);
  background: var(--surface-sunk);
  font-size: 0.85rem;
}
.rebalance-class-card--ok {
  border-left-color: var(--positive);
  background: color-mix(in srgb, var(--positive) 6%, var(--surface-sunk));
}
.rebalance-class-card--over {
  border-left-color: var(--negative);
  background: color-mix(in srgb, var(--negative) 6%, var(--surface-sunk));
}
.rebalance-class-card-name {
  font-weight: 600;
  color: var(--ink);
  display: block;
  margin-bottom: 0.5rem;
}
.rebalance-class-card-metrics {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  color: var(--ink-muted);
  font-size: 0.8rem;
}
.rebalance-class-card-metrics strong {
  color: var(--ink);
}
```

### 5.4 Add filter bar styles

```css
.rebalance-filter-bar {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin: 0.75rem 0;
  flex-wrap: wrap;
}
.rebalance-filter-group {
  position: relative;
}
.rebalance-filter-trigger {
  padding: 0.35rem 0.75rem;
  font-size: 0.85rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--ink);
  cursor: pointer;
}
.rebalance-filter-panel {
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 20;
  min-width: 180px;
  padding: 0.5rem;
  background: var(--surface);
  border: 1px solid var(--border-strong);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  max-height: 240px;
  overflow-y: auto;
}
.rebalance-filter-option {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0;
  font-size: 0.85rem;
  color: var(--ink);
  cursor: pointer;
}
.rebalance-filter-search {
  flex: 1;
  min-width: 200px;
  padding: 0.35rem 0.5rem;
  font-size: 0.85rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--surface);
  color: var(--ink);
}
```

### 5.5 Add row color-coding styles

```css
.rebalance-asset-row--over td {
  background: color-mix(in srgb, var(--negative) 8%, transparent);
}
.rebalance-asset-row--ok td {
  background: color-mix(in srgb, var(--positive) 6%, transparent);
}
.rebalance-asset-row--neutral td {
  /* no additional bg */
}
.rebalance-deviation--pos { color: var(--positive); }
.rebalance-deviation--neg { color: var(--negative); }
```

## 6. Verification

### 6.1 Run lint + type check

```bash
uv run task lint
```

### 6.2 Run unit tests

```bash
uv run task test-unit
```

### 6.3 Run integration tests

```bash
uv run task test-file tests/test_rebalance_page.py tests/test_rebalance_route.py
```

### 6.4 Spec health check

```bash
openspec list --specs
```

### 6.5 Refresh for test

Invoke `refresh-for-test` skill: restart server, verify DB state,
smoke-test `/rebalanceamento` in browser.
