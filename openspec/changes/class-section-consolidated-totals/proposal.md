## Why

Each class section card on the dashboard shows a class header
(chevron + colour swatch + class name + `Alvo` / `Atual` / `Sobra|Falta`
pills + `×` delete) and then the per-asset table below it. The table
has eight columns, three of which are class-level aggregates that
the operator already reads at the asset row: `Valor`,
`Alvo % total`, and `Atual % total`.

Today the class header duplicates the *target* (`Alvo NN%`) and
*current* (`Atual NN%`) pills, but the pills are visually unmoored
from the table columns below them — there is no horizontal
relationship between where the `Alvo` pill sits in the header and
where the `Alvo % total` column header sits in the table. The
consolidated `Valor` (sum of `current_value` across the class's
assets) is not surfaced anywhere in the header; the operator has
to mentally add up the table rows to know what the class is worth
in BRL. As the table layout evolves, the pills risk drifting out
of alignment silently.

The operator wants three consolidated values in the class header
(`Valor`, `Alvo % total`, `Atual % total`), each horizontally
aligned with the corresponding table column, so the eye can read
header → column → rows without re-anchoring. The `Sobra|Falta`
pill stays — it carries information that has no column
counterpart — but moves to the slot that aligns with
`Alvo % classe` (the column whose sum it measures). The `×`
delete button moves from the far right to right after the class
name (it is a destructive action that belongs with the class
identity, not at the trailing edge of the stats row).

## What Changes

- **`class-section-header` becomes a CSS Grid row of 8 columns**
  (`src/omaha/static/app.css`). The grid template is defined once
  via CSS custom properties (`--col-ativo`, `--col-classe`, ...,
  `--col-atual-total`) and consumed both by the header
  (`grid-template-columns: var(...)`) and by the asset table's
  `<colgroup>` (`width: var(--col-N)` per column). One change to
  the variable list re-aligns both header and table — the layout
  cannot drift.
- **`asset-table` switches to `table-layout: fixed`** so the
  `<colgroup>` widths are authoritative. Long asset names wrap
  (`overflow-wrap: break-word`) instead of forcing column growth;
  the table uses the full container width via `width: 100%` so
  wider screens give more room to text columns (Ativo, Classe).
- **Three new consolidated stat cells** render inside
  `.class-section-header`:
  - `R$ 9.389` — sum of `current_value` across the class's
    assets, plain text (no pill), BRL formatter with no decimal
    fraction digits (`R$ 9.389` not `R$ 9.389,96`). Empty
    state: `—` when the class has no assets (`current_value`
    is `0`). Carries `data-testid="class-total-value"`.
  - `Alvo NN.NN%` — the class's target_pct, repackaged as the
    consolidated `Alvo % total` value. Reuses the existing
    `pct-target-pill` (dashed border, click-to-edit) so the
    inline editor still works. Empty state: shows the class's
    configured target (the slot exists even when empty).
    Carries `data-testid="class-target-pct-view"` (unchanged).
  - `Atual NN.NN%` — the class's current_pct of the portfolio,
    repackaged as the consolidated `Atual % total` value.
    Reuses the existing `pct-current-pill` with `ok`/`off`
    status modifier. Empty state: `0.00%` (the class is
    contributing 0% of the portfolio). Carries
    `data-testid="class-current-pct"` (unchanged).
- **`Sobra|Falta` pill** moves to the grid slot aligned with
  column 5 (`Alvo % classe`) — semantically the column whose sum
  the pill measures (`classDelta = 100 - sum(asset.target_pct)`).
  Empty state: not rendered (the pill already hides when
  `|classDelta| <= 0.01`).
- **`×` delete button** moves from the trailing edge of
  `.class-section-header` to immediately after the class name
  in the leading grid slot (cols 1-3). The `data-testid` stays
  `class-delete-btn`; the visual treatment (red border + hover
  darken) is unchanged. Click behaviour is unchanged (still
  shows `.class-delete-confirm` and DELETEs `/api/classes/{id}`).
- **`class_data` blob** (the dict the Alpine `classSection`
  factory reads) gains one new field: `current_value` (the
  class-level sum of `current_value`). No other fields change.
  No backend route or model changes — the field is already
  computed by `portfolio_aggregates` in
  `src/omaha/routes/pages.py`.
- **No DB migration**. No new route. No new API. The only
  backend touch is reading `c.current_value` from the existing
  `class_aggregates` payload.

## Capabilities

### New Capabilities

- `class-section-totals`: the three consolidated header stats
  (`Valor`, `Alvo % total`, `Atual % total`) and their
  horizontal alignment with the asset table columns.

### Modified Capabilities

- `dashboard-inline-editing`: the `×` delete button moves
  inside the header; the asset table column widths become
  CSS-variable-driven; the inline-edit pills in the header are
  repositioned to align with their table columns.

## Impact

- **Template** (`src/omaha/templates/dashboard.html`):
  `class-section-header` HTML restructured (leading wrapper
  `div.hdr-leading` for cols 1-3, four explicit `grid-column`
  spans for cols 4 / 5 / 7 / 8); `class_data` blob gains
  `current_value`; new Alpine `classCurrentValue` and
  `formatBRLCompact` fields on `classSection`.
- **Stylesheet** (`src/omaha/static/app.css`):
  `:root` gains the 8 `--col-*` CSS variables plus the
  composite `--asset-table-columns`; `.class-section-header`
  switches from flex to grid; `.asset-table` switches to
  `table-layout: fixed` + `width: 100%`; `.asset-table col`
  widths read from the variables; existing `.pct-target-pill`,
  `.pct-current-pill`, `.pct-delta-pill` styling is unchanged.
- **JS** (`classSection` factory in
  `src/omaha/templates/dashboard.html`): `current_value` field
  read into `classCurrentValue`; new `formatBRLCompact` BRL
  formatter with `minimumFractionDigits: 0,
  maximumFractionDigits: 0`; `x-show` /
  `data-testid` hooks unchanged for the existing pills.
- **Routes / models / DB**: zero changes. The
  `portfolio_aggregates` payload in
  `src/omaha/routes/pages.py:136` already exposes
  `current_value` per class.
- **Tests**:
  - `tests/test_pages_routes.py` — new scenarios asserting
    `data-testid="class-total-value"` renders BRL with no
    decimals, that `data-testid="class-delete-btn"` sits
    before the stats in DOM order, that empty class shows
    `—` for `Valor` and `0.00%` for the percentages.
  - `tests/e2e/test_visual_gate.py` (or new file) — bounding
    box alignment assertion: the consolidated
    `class-total-value` spans the same x-range as the
    `Valor` `<th>`; the `Alvo` pill spans the same x-range
    as the `Alvo % total` `<th>`; same for `Atual`.
- **E2E selectors** (no breakage expected): all existing
  `data-testid` attributes preserved. New
  `data-testid="class-total-value"` for the consolidated
  Valor stat.