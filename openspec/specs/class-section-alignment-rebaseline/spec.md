# class-section-alignment-rebaseline Specification

## Purpose
TBD - created by archiving change t04-e2e-class-section-alignment-baselines. Update Purpose after archive.
## Requirements
### Requirement: Class-section header pills mirror the asset-table column grid

The system SHALL render the `.class-section-header` element with a
`grid-template-columns` declaration that mirrors the full
`<colgroup>` width set of the asset table inside the same class
section. The four stats (Valor, Alvo, Atual, Sobra|Falta) MUST
land under their matching `<th>` so that the pill's
`getBoundingClientRect().left` is within `1 px` of the
corresponding `<th>`'s left coordinate.

#### Scenario: Valor pill aligns with Valor <th> on /patrimonio

- **WHEN** the dashboard renders a class section that has at least
  one asset with a positive `current_value`
- **THEN** the `class-total-value` pill's `left` coordinate is
  within `1 px` of `asset-table-th-current-value`'s `left`
  coordinate inside the same class section

#### Scenario: Alvo-Total pill aligns with Alvo-Total <th>

- **WHEN** the dashboard renders a class section that has at least
  one asset with a non-zero `target_pct`
- **THEN** the `class-target-pct-view` pill's `left` coordinate is
  within `1 px` of `asset-table-th-target-pct-total`'s `left`
  coordinate inside the same class section

#### Scenario: Atual-Total pill aligns with Atual-Total <th>

- **WHEN** the dashboard renders a class section that has at least
  one asset with a non-zero `current_pct`
- **THEN** the `class-current-pct` pill's `left` coordinate is
  within `1 px` of `asset-table-th-current-pct-total`'s `left`
  coordinate inside the same class section

#### Scenario: Sobra/Falta pill aligns with Alvo-Classe <th>

- **WHEN** the dashboard renders a class section whose asset
  `target_pct` sum differs from the class `target_pct` by more
  than `0.01 %` (delta badge visible)
- **THEN** the `class-delta-badge` pill's `left` coordinate is
  within `1 px` of `asset-table-th-target-pct-class`'s `left`
  coordinate inside the same class section

### Requirement: Asset-table column widths come from a single CSS variable source

The system SHALL source every asset-table `<colgroup>` width from
a single `:root` block of `--col-*` CSS custom properties. The
`.class-section-header` `grid-template-columns` SHALL consume the
same variables (verbatim, in the same order) so the two layouts
resolve to the same column boundaries without manual duplication.

#### Scenario: Adding a new asset-table column updates the header

- **WHEN** the `<colgroup>` in `templates/patrimonio.html` gains a
  new `<col class="col-X">` entry
- **AND** the corresponding `--col-X` CSS variable is added to
  `:root`
- **THEN** the `.class-section-header` `grid-template-columns` is
  updated to include `var(--col-X)` in the same position so the
  alignment invariant continues to hold
- **AND** no other pill position drifts more than `1 px`

#### Scenario: Column widths sum to 100 %

- **WHEN** the `:root` `--col-*` variables are summed
- **THEN** the total is exactly `100 %` (modulo rounding error
  within `0.1 %`) so the table fills its container without
  overflow or empty space
