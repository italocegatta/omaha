## Why

The deviation columns ("Desvio") in the class totals row always render a value, even when deviation is exactly 0%. This clutters the row with meaningless "0%" entries. The user wants deviation to appear only when there is actual deviation — green for positive, red for negative, em-dash for zero.

## What Changes

- **Classe / Desvio** (totals row, `data-testid="class-total-deviation-class"`): when `classDeviationPctClass` is ~0, render "—" instead of the formatted deviation value. Keep existing green/red sign styling for non-zero values.
- **Carteira / Desvio** (totals row, `data-testid="class-total-deviation-portfolio"`): same conditional logic — render "—" when `classPortfolioDeviationPct` is ~0, green/red otherwise.
- No backend changes. Template logic only (Alpine.js `x-show`/`x-text` conditional + existing `signClass` CSS).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `class-section-totals`: Deviation cells in the totals row SHALL render "—" when deviation is zero, instead of showing "0%" with neutral styling.

## Impact

- **Files**: `src/omaha/templates/_patrimonio_class_section.html` (lines 139–145, 186–191)
- **CSS**: None — `metric-neutral`, `metric-positive`, `metric-negative` classes already exist
- **Backend**: None
- **Tests**: Existing BDD/e2e selectors for `class-total-deviation-class` and `class-total-deviation-portfolio` may need updated assertions for the zero-deviation case
