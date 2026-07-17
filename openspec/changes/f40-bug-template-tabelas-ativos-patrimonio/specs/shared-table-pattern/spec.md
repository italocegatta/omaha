## MODIFIED Requirements

### Requirement: CSS maintenance rules for asset-table headers

The following rules prevent recurring layout bugs in `_patrimonio_class_section.html` table headers. Every contributor SHALL follow them when editing `app.css`.

#### Rule: Single `.asset-table th` block for header typography

There SHALL be exactly ONE `.asset-table th` rule block that sets `white-space`, `overflow`, and `text-overflow`. No other `.asset-table th` block MAY override these properties. The canonical values are:

```css
.asset-table th {
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
```

**Why:** A second `.asset-table th` block with `white-space: normal` + `overflow-wrap: anywhere` was silently overriding `nowrap`, causing column names to wrap and the sort indicator to drop to a second line. The cascade makes the LAST matching rule win, so duplicate blocks are a silent trap.

#### Rule: No `display: block` on header label spans

The selector `span[data-testid^="asset-table-th-"]` SHALL NOT be used with `display: block` or `width: 100%`. This rule was removed on 2026-07-16 because it broke exactly the columns whose header text is wrapped in a `<span>` with `data-testid="asset-table-th-*"` (Posição, Classe/Alvo, Carteira/Atual, Carteira/Alvo). Columns without that inner span (Ativo, Qtd, etc.) were unaffected — creating an inconsistency invisible in the CSS.

**Diagnostic:** If a column's text + sort indicator wraps to a second line while adjacent columns don't, check whether that column's template has an inner `<span>` with `data-testid="asset-table-th-*"` that matches a `display: block` rule.

#### Rule: Single source of truth for column widths

Column widths SHALL be defined in the F15 `:root` block using pixel-based `--col-*` variables. There SHALL NOT be a second set of `--col-*` variables (percentage-based) used by `col:nth-child()` selectors. The old percentage block was removed on 2026-07-16 because:

1. It used different variable names (`--col-classe`, `--col-valor`, `--col-alvo-classe`) that mapped to different columns than the F15 block
2. Both blocks targeted the same selectors (`.asset-table col:nth-child(N)`), creating cascade confusion
3. The percentage variables were dead code — the F15 block always won

**Current column widths** (as of 2026-07-16):

| Variable | Width | Column |
|----------|-------|--------|
| `--col-ativo` | 205px | Ativo |
| `--col-qtd` | 65px | Qtd |
| `--col-avg-price` | 120px | Preço Médio |
| `--col-gain` | 140px | Ganho |
| `--col-position` | 130px | Posição |
| `--col-position-deviation` | 110px | Desvio (posição) |
| `--col-class-current` | 100px | Classe / Atual |
| `--col-class-target` | 110px | Classe / Alvo |
| `--col-class-deviation` | 100px | Classe / Desvio |
| `--col-portfolio-current` | 110px | Carteira / Atual |
| `--col-portfolio-target` | 110px | Carteira / Alvo |
| `--col-portfolio-deviation` | 100px | Carteira / Desvio |
| `--col-buy` | 95px | Compra |
| `--col-sell` | 95px | Venda |

#### Rule: Column header text alignment

Individual column headers (Ativo, Qtd, Preço Médio, etc.) SHALL use `text-align: left`. Group headers (Classe, Carteira) SHALL use `text-align: center`. The selector for group headers is:

```css
.asset-table-group-row th[colspan] {
  text-align: center;
}
```

#### Rule: Vertical alignment

All column headers SHALL vertically center the column name, sort indicator, and filter icon at the same level. This is achieved by:

1. `vertical-align: middle` on `.asset-table th` and `.asset-table td`
2. Filter icon (`.rebalance-header-actions`) positioned with `position: absolute; top: 50%; transform: translateY(-50%)`
3. Sort indicator (`.rebalance-table-th-indicator`) inline with the text

No additional alignment CSS is needed. If alignment breaks, check whether a `display: block` rule is pulling the sort indicator out of the inline flow.

#### Rule: First column word-break for long asset names

The first column (`<td>` for asset name) SHALL allow text wrapping for long names. The CSS rule SHALL be:

```css
.asset-table td:first-child {
  white-space: normal;
  overflow-wrap: break-word;
}
```

This overrides the generic `white-space: nowrap` on `.asset-table tbody td` only for the name column. All other columns SHALL remain `nowrap` for numeric alignment.

#### Rule: Filter panel visibility in table headers

`.asset-table th` SHALL NOT use `overflow: hidden` when the header contains absolutely-positioned filter panels. Use `overflow: clip` instead, which clips content to the padding box but does not create a new scroll container and does not clip positioned descendants in the same way. Alternatively, remove `overflow` entirely if `text-overflow: ellipsis` is not needed on the header.

**Why:** `overflow: hidden` on `.asset-table th` clips the `.rebalance-filter-panel--header` (which is `position: absolute` inside the `<th>`), making the filter panel invisible when opened. The rebalance table does not have this problem because its `<th>` elements do not use `overflow: hidden`.

#### Scenario: Adding a new column to the asset table

- **WHEN** a new `<col>` is added to the `<colgroup>` in `_patrimonio_class_section.html`
- **THEN** the F15 `:root` block SHALL gain a `--col-<name>` variable with an appropriate pixel width
- **AND** the `.asset-table col:nth-child(N)` block SHALL be updated to reference the new variable
- **AND** the `.class-section-header` `grid-template-columns` SHALL include the new variable
- **AND** no other `col:nth-child()` block MAY define widths for the same nth-child indices
- **AND** all column header text SHALL remain single-line (no wrapping to second line)

#### Scenario: Long asset name wraps in first column

- **WHEN** an asset has a name longer than the column width (e.g. "ISHARES CORE S&P 500 ETF")
- **THEN** the name SHALL wrap to multiple lines within the cell
- **AND** the cell height SHALL grow to accommodate the wrapped text
- **AND** adjacent columns SHALL NOT shift or resize

#### Scenario: Filter panel opens in all columns

- **WHEN** user clicks the filter icon on any column header in the asset table
- **THEN** the filter panel SHALL appear below the header cell
- **AND** the panel SHALL NOT be clipped by the header cell's overflow
- **AND** the panel SHALL be interactive (checkboxes/sliders respond to input)
