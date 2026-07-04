## Why

T01's verification phase exposed four red tests in
`tests/e2e/test_class_section_alignment.py`. Each asserted that a
class-section-header pill (`class-total-value`,
`class-target-pct-view`, `class-current-pct`, `class-delta-badge`)
sits horizontally aligned with a specific asset-table `<th>`
within `1.0 px`. Post-F02 deltas ranged from 130 to 251 px.

The misalignment was **not** a pixel-baseline drift. It was a
structural CSS bug: F02 widened the asset table from 8 → 11
columns (added Compra / Venda / Moeda) but
`.class-section-header` still used an 8-column
`grid-template-columns` and the old `--col-*` variables. The
header pills were positioned over cols 1-8 while the table cells
were spread across 11 narrower cols. The header needed to mirror
the full 11-col `<colgroup>` so Valor / Alvo / Atual / Sobra|Falta
land under their matching `<th>` (cols 4 / 7 / 8 / 9 in the new
11-col grid).

This slice records the fix and the test contract so the
alignment invariant does not regress.

## What Changes

- **CSS:** `src/omaha/static/app.css` —
  `.class-section-header` `grid-template-columns` extended from 8
  to 11 columns, mirroring the asset-table `<colgroup>`. The
  leading group still spans cols 1-3; the four stats still land
  in their target columns. No new variables needed; the existing
  `--col-ativo` … `--col-currency` (added by the table-widening
  fix earlier in T01) cover the full grid.
- **Test:** `tests/e2e/test_class_section_alignment.py` — no
  assertion change. The 1.0 px tolerance remains the contract;
  the structural fix makes the actual deltas fit that tolerance
  again. The four scenarios each verify one pill / one `<th>`
  pair (Valor ↔ col-4, Alvo-Total ↔ col-7, Atual-Total ↔ col-8,
  Sobra|Falta ↔ col-5).

## Capabilities

### New Capabilities

- `class-section-alignment-rebaseline`: the post-F02 contract that
  class-section-header pills share the same column boundaries as
  the asset-table `<th>` cells they decorate.

### Modified Capabilities

- `class-section-consolidated-totals`: no requirement change.
  The existing "Stats sit under their matching `<th>`" invariant
  is restored; the underlying grid template is now correctly
  11 columns. No delta spec needed (the requirement was always
  correct; the implementation had drifted).
- `dashboard-width-and-inline-edit`: no change.

## Impact

- One CSS rule changed (`grid-template-columns` for
  `.class-section-header`).
- One comment block updated to reflect the 11-col layout.
- Zero test code changes.
- No production behaviour change other than the visual alignment
  restore.
- Zero DB / migration / API impact.
- Risk: low. The fix re-aligns UI to the existing test
  expectation, which is the test's whole purpose.