## Context

The asset table grew from 8 → 11 columns during F02 (added
Compra / Venda / Moeda). The `<colgroup>` in
`templates/patrimonio.html` was updated to include
`<col class="col-buy">`, `<col class="col-sell">`,
`<col class="col-currency">`. The CSS `:root` block and the
`.asset-table col:nth-child(...)` rules were updated during the
T01 verification phase (commit alongside this slice) so the table
cells distribute correctly across the 11 columns.

What was not updated was the matching header — `.class-section-
header` still declared an 8-column `grid-template-columns` and
used the original 8 `--col-*` variables. The result: header pills
sat over cols 1-8 with the original percentages (sum = 100 %),
while the table cells sat over the new 11-column percentages
(sum = 100 %). Pills landed in completely different physical
positions than the `<th>` cells they decorate.

The four e2e tests in
`tests/e2e/test_class_section_alignment.py` measure the
delta with `getBoundingClientRect().left` and assert
`abs(delta) <= 1.0`. Post-F02 the deltas were 130-251 px; the
tests failed loudly. The fix is to extend the header grid to
mirror the full 11-column `<colgroup>`.

Stakeholders: the operator (Juca), who runs `task test-e2e` to
gate every slice. No external consumers depend on this surface.

## Goals / Non-Goals

**Goals:**
- Restore the 1.0 px alignment invariant between the
  class-section-header pills and the asset-table `<th>` cells
  they decorate.
- Make the fix surface-correct: the header grid must mirror the
  full asset-table column set so future column additions (or
  removals) only need to touch the `<colgroup>` and the matching
  `:root` `--col-*` variables in one place.
- Lock the invariant with the existing four e2e scenarios (no new
  tests).

**Non-Goals:**
- No refactor of the asset-table column set.
- No changes to the BRL formatting, the inline-edit input, or the
  chevron / color-swatch layout.
- No delta spec changes — the existing
  `class-section-consolidated-totals` requirement already states
  the invariant ("stats sit under their matching `<th>`"); the
  implementation had drifted, not the contract.

## Decisions

**D1 — Mirror the 11-column `<colgroup>` in `.class-section-
header`.** The header's `grid-template-columns` now lists all
eleven `--col-*` variables (sum = 100 %). The leading group
(`<div class="hdr-leading">`) still spans cols 1-3 (chevron +
swatch + name + ×). Valor, Alvo, Atual, Sobra|Falta retain their
grid-column placements; cols 10-11 land empty (the table cells
for Venda and Moeda have no header counterpart today, but the
grid must still allocate the space or cols 1-9 compress).

**D2 — No gap on the header grid.** `gap: 0` is implicit (no
`gap` rule on the grid). A gap would shift every cell by
`gap × column-index` from the matching `<th>`; with `gap: 8px`
col 5 would shift by 32 px and the test would still fail. The
table cells use `padding` for visual separation, so the header
mirrors by matching column boundaries, not by adding internal
gaps.

**D3 — Test assertion contract unchanged.** The four scenarios
in `test_class_section_alignment.py` already encode the
invariant (`abs(delta) <= 1.0`). The fix is purely on the CSS
side; the tests pass once the layout is correct. Adding a new
tolerance or new scenarios would dilute the contract.

**D4 — No new spec capability needed.** The new spec
`class-section-alignment-rebaseline` would merely restate what
`class-section-consolidated-totals` already says. Per the
design principle "don't duplicate contract", we add a single
deprecation note in the proposal and let the existing spec carry
the invariant.

## Risks / Trade-offs

- **R1 — Browser rounding across the 11-column grid could push
  deltas to 1-2 px.** The tolerance is 1.0 px. Mitigation: the
  variables are percentages with one decimal (`21.5%` etc.), so
  even with `table-layout: fixed` and `width: calc(100% - 2rem)`
  on the container, Chromium resolves each column to within
  sub-pixel precision and rounding accumulates to < 1 px.
  If a future Chromium rev pushes past 1 px, the test fails
  loudly — the same fail-loud-not-silently-widen pattern as the
  per-asset `width` checks elsewhere in the suite.

- **R2 — Future column additions still require updating both
  the header grid and the table `<colgroup>`.** The single
  source of truth is the `:root` `--col-*` block (consumed by
  both `nth-child(N)` rules in `.asset-table col` and by the
  header `grid-template-columns`). A future column addition
  must touch all three places. Mitigation: the comment block
  on `.class-section-header` now flags this dependency so the
  next author sees it before pushing. A DRY follow-up could
  collapse the three into a single CSS custom property list,
  but that's out of scope for this slice.

## Migration Plan

Single PR, applied via `openspec-archive-change`. No
backwards-compatibility concerns (the layout was already
broken; this restores it). No data migration. No rollback
risk beyond re-introducing the misalignment.

## Open Questions

None.
