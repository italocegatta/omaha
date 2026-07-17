# Shared Table Pattern

## Purpose

Define shared CSS base classes and custom properties for all data tables, enabling consistent visual styling and easy theme customization across rebalance and portfolio tables.

## Canonical Reference

**The rebalance page table (`_rebalance_plan.html`) is the single source of truth for functionality and visual style.** All table patterns, CSS tokens, interaction behaviors, and visual decisions originate from the rebalance table.

**The portfolio page asset table (`_patrimonio_class_section.html`) is broken and MUST NOT be used as reference.** It has inconsistent class naming, duplicated rules, and misaligned visual patterns. It will be refactored to match the rebalance table standard in slice F32.

When making table-related decisions:
- Always check the rebalance table first
- Never copy patterns from the portfolio table
- Portfolio table deviations from rebalance are bugs, not features

## Requirements

### Requirement: Shared table base classes

The system SHALL provide `.data-table-shell`, `.data-table`, `.data-table-thead`, `.data-table-th`, `.data-table-tbody`, `.data-table-tr`, `.data-table-td` CSS classes that define shared visual properties for all data tables (shell container, table element, header row, header cell, body container, body row, body cell).

#### Scenario: Base classes applied to rebalance table
- **WHEN** the rebalance plan table is rendered
- **THEN** each structural element (`<div>` shell, `<table>`, `<thead>`, `<th>`, `<tbody>`, `<tr>`, `<td>`) SHALL carry both the base class (e.g. `.data-table-shell`) and the specific class (e.g. `.rebalance-table-shell`)

#### Scenario: Base classes applied to portfolio table
- **WHEN** the portfolio asset table is rendered
- **THEN** each structural element SHALL carry both the base class and the specific class (e.g. `.portfolio-table-shell`)

#### Scenario: Visual parity after base extraction
- **WHEN** base classes are applied alongside existing specific classes
- **THEN** the rendered visual output SHALL be identical to the pre-refactor state (no pixel-level differences in spacing, colors, borders, or typography)

### Requirement: Table CSS custom properties

The system SHALL define `--table-shell-bg`, `--table-header-bg`, `--table-row-odd`, `--table-row-even`, `--table-row-hover`, `--table-border`, `--table-border-strong`, `--table-text`, `--table-text-muted` as CSS custom properties on `:root`.

#### Scenario: Variables resolve to current palette
- **WHEN** the page loads
- **THEN** all `--table-*` variables SHALL resolve to values that produce the same visual result as the current hardcoded color-mix formulas

#### Scenario: Palette swap via variables
- **WHEN** a `--table-*` variable is overridden (e.g. via a class or media query)
- **THEN** ALL tables consuming that variable SHALL reflect the new value without any other CSS changes

### Requirement: Specific classes override base

Specific table classes (`.rebalance-table-shell`, `.portfolio-table-shell`, `.rebalance-table`, `.asset-table`, etc.) SHALL override base class properties only where they differ. Properties that are identical between tables SHALL NOT be duplicated in specific classes.

#### Scenario: Rebalance-specific overrides
- **WHEN** rebalance table has properties that differ from the base (e.g. row color-coding by action: buy/sell/neutral)
- **THEN** `.rebalance-*` classes SHALL provide those overrides and the base SHALL NOT include them

#### Scenario: Portfolio-specific overrides
- **WHEN** portfolio table has properties that differ from the base (e.g. 2-level header, summary row background)
- **THEN** `.portfolio-*` / `.asset-table` classes SHALL provide those overrides and the base SHALL NOT include them

#### Scenario: No duplicated identical rules
- **WHEN** a CSS property has the same value in both rebalance and portfolio tables
- **THEN** that property SHALL exist only in the base class, not in both specific classes

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

#### Scenario: Adding a new column to the asset table

- **WHEN** a new `<col>` is added to the `<colgroup>` in `_patrimonio_class_section.html`
- **THEN** the F15 `:root` block SHALL gain a `--col-<name>` variable with an appropriate pixel width
- **AND** the `.asset-table col:nth-child(N)` block SHALL be updated to reference the new variable
- **AND** the `.class-section-header` `grid-template-columns` SHALL include the new variable
- **AND** no other `col:nth-child()` block MAY define widths for the same nth-child indices
- **AND** all column header text SHALL remain single-line (no wrapping to second line)
