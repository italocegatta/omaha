## MODIFIED Requirements

### Requirement: Class card header inline pills

The class section header MUST carry three inline pills
(`Alvo`, `Atual`, and per-class `Sobra/Falta` delta) and one
plain-text consolidated `Valor` stat. The four items MUST be
laid out across the columns of an 8-column CSS grid that
mirrors the asset table column structure (see
`class-section-totals` capability for the alignment
contract). The `×` delete button MUST be placed immediately
after the class name in the leading grid slot, NOT at the
trailing edge of the header row.

The `Alvo` pill MUST render the class target percentage as
`Alvo NN%` (the existing `commitEditClassPct` flow turns
the pill into an inline editor on click). The pill MUST have
a dashed border to signal "click to edit" and carry
`data-testid="class-target-pct-view"`.

The `Atual` pill MUST render the class current percentage as
`Atual NN.NN%` (two-decimal format) and carry
`data-testid="class-current-pct"`. The pill MUST use the
modifier class `pct-current-pill--ok` when
`|classCurrentPct - classTargetPct| <= 0.01` (within
tolerance) and `pct-current-pill--off` otherwise.

The delta pill MUST carry `data-testid="class-delta-badge"`
and render the per-class Sobra/Falta message
(`Sobra X%` / `Falta X%`) when `|classDelta| > 0.01`. The
pill MUST NOT render when `|classDelta| <= 0.01`.

The consolidated `Valor` stat MUST render the class's
`current_value` (sum of `current_value` across the class's
assets) as plain text (NOT a pill) in BRL with no decimal
fraction digits, and MUST carry
`data-testid="class-total-value"`. Empty state (class with
no assets, `current_value == 0`): the element renders `—`
instead of `R$ 0`.

#### Scenario: Header has consolidated Valor + three pills + × in the leading slot

- **WHEN** the dashboard renders a class section header at a
  desktop viewport (>= 480px)
- **THEN** the header (data-testid="class-section-header")
  contains, in DOM order: chevron, colour swatch, class name,
  × button (data-testid="class-delete-btn"), consolidated
  Valor (data-testid="class-total-value"), `Sobra/Falta` pill
  (data-testid="class-delta-badge", when rendered), `Alvo`
  pill (data-testid="class-target-pct-view"), and `Atual`
  pill (data-testid="class-current-pct")
- **AND** the × delete button is a sibling of the class name
  inside the leading flex group, NOT a trailing child of the
  header row

#### Scenario: × button stays visible after move (discreet gray, red on hover)

- **WHEN** the dashboard renders a class section header
- **THEN** the × button (data-testid="class-delete-btn") is
  visible (the existing visibility contract from
  `dashboard-inline-editing` is unchanged)
- **AND** the × button's computed `color` in steady state is
  the value of the `--muted` CSS custom property (a low-luminance
  gray — the destructive action is intentionally discreet and
  mirrors the per-asset × button styling)
- **AND** the × button's computed `color` flips to the value of
  the `--negative` CSS custom property on `:hover` (red, with a
  light-red `var(--error-bg)` background) so the operator sees
  what the click does before committing
- **AND** the click handler still opens the
  `.class-delete-confirm` dialog and DELETEs
  `/api/classes/{id}` on confirm (no behaviour change)

#### Scenario: Clicking × from the new position still opens the confirm dialog

- **WHEN** the user clicks the × button (now positioned right
  after the class name)
- **THEN** the confirm dialog
  (data-testid="class-delete-confirm") appears
- **AND** the rest of the contract from
  `dashboard-inline-editing` "Remoção de classe com
  confirmação" is unchanged

### Requirement: Asset table column proportions live in CSS variables

The asset table column widths MUST be defined as CSS custom
properties at `:root` (one per column, `--col-ativo`
through `--col-atual-total`). The table MUST consume these
variables via a `<colgroup>` with `<col class="col-N">`
elements whose `width` is set via the corresponding variable
in `src/omaha/static/app.css`. The table MUST use
`table-layout: fixed` and `width: 100%` so the
`<colgroup>` widths are authoritative.

The proportions (in `fr` units) are:

| Column | CSS variable     | Width |
|--------|------------------|-------|
| Ativo | `--col-ativo`    | 2.5fr |
| Classe | `--col-classe`  | 1.5fr |
| Qtd | `--col-qtd`       | 0.6fr |
| Valor | `--col-valor`   | 1.2fr |
| Alvo % classe | `--col-alvo-classe` | 1fr |
| Atual % classe | `--col-atual-classe` | 1fr |
| Alvo % total | `--col-alvo-total`   | 1fr |
| Atual % total | `--col-atual-total` | 1fr |

The previous hard-coded percentage widths (24% / 18% / 6% /
14% / 11% / 11% / 9% / 7%) from the legacy "Column widths"
requirement are superseded by the `fr` units above. The
proportions are roughly equivalent — wide text columns, narrow
numeric columns — but expressed as `fr` so the table
distributes its 100% width across the available container
width rather than a fixed 800-ish-pixel target.

Long asset names MUST wrap inside their `<td>` via
`overflow-wrap: break-word` rather than overflow
horizontally or force the column to grow.

The `.class-section-header` MUST consume the same variables
via `grid-template-columns: var(--col-ativo) var(--col-classe)
... var(--col-atual-total)` so the header and the table
re-align automatically when any variable changes.

#### Scenario: Column widths are CSS-variable-driven

- **WHEN** the dashboard renders an asset table
- **THEN** the `<table class="asset-table">` element contains
  a `<colgroup>` with 8 `<col>` elements (one per column)
- **AND** the `width` of each `<col>` resolves to the
  corresponding `--col-*` CSS custom property's value
- **AND** the table's computed `table-layout` is `fixed`

#### Scenario: Header and table share the same column template

- **WHEN** both the class section header and the asset table
  are rendered
- **THEN** the computed `grid-template-columns` of
  `.class-section-header` matches the computed `width` per
  column on `.asset-table col` (8 columns, same proportions)
- **AND** mutating any `--col-*` value in DevTools
  re-aligns both header and table on the next layout

#### Scenario: Long asset names wrap, columns stay fixed

- **GIVEN** an asset with a name longer than the Ativo
  column can fit on one line (e.g. `"Tesouro Selic 2029 -
  LFT Prefixado com Juros Semestrais"`)
- **WHEN** the dashboard renders the asset table
- **THEN** the `<td>` wrapping the name contains line
  breaks (`overflow-wrap: break-word`)
- **AND** the `<th>` width stays at the CSS-variable value
  (the table does not grow to fit the name)

#### Scenario: Sum of column widths equals the table width

- **WHEN** the dashboard renders the asset table
- **THEN** the sum of the 8 `<col>` computed `width` values
  equals the table's `clientWidth` (no overflow, no
  underflow)

#### Scenario: Testids on table headers remain stable

- **WHEN** the dashboard renders the asset table
- **THEN** every `<th>` carries the existing
  `data-testid` from `dashboard-inline-editing`:
  - `asset-table-th-name`
  - `asset-table-th-class`
  - `asset-table-th-qty`
  - `asset-table-th-current-value`
  - `asset-table-th-target-pct-class`
  - `asset-table-th-current-pct-class`
  - `asset-table-th-target-pct-total`
  - `asset-table-th-current-pct-total`
- **AND** the sort click handlers (`@click="sortBy('name')"`
  etc.) and the sort indicator spans
  (`asset-table-sort-*`) are unchanged

## REMOVED Requirements

### Requirement: Column widths (legacy percentage table)

The previous "Column widths" requirement hard-coded column
widths as percentages (Ativo 24%, Classe 18%, Qtd 6%, Valor
14%, Alvo % classe 11%, Atual % classe 11%, Alvo % total 9%,
Atual % total 7%). That contract is superseded by the
"Asset table column proportions live in CSS variables"
requirement above. The percentages are no longer authoritative
— the `fr` units in the CSS variables define the new
contract.

The `<th>` `transition: width 200ms` rule from the legacy
contract is also dropped — the widths are now driven by
`<colgroup>`, and `<col>` width transitions are not reliably
animatable across browsers. Initial paint already handles
the layout transition cleanly; the explicit `width`
transition on `<th>` is no longer necessary.
