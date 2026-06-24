## MODIFIED Requirements

### Requirement: Seções colapsáveis
The dashboard MUST render a chevron in each class section header. Clicking
the class section header MUST toggle the visibility of the class section
body (the asset table, the compare bars, the inline progress bars, and
the delete confirm dialog). The toggle state (`isOpen`) MUST be in-memory
only — reloading the page MUST reset every class section to expanded.
The default value of `isOpen` MUST be `true` (expanded) on every load.

The chevron MUST be a single rotating glyph (e.g. `▸` rotated 90° when
open) so the icon is the same width in both states. The body MUST use the
existing `max-height` + `opacity` CSS transition (200ms) so the
collapse/expand is animated, not instant.

#### Scenario: Chevron is rendered in every class header
- **WHEN** the dashboard renders the asset table
- **THEN** every class section header contains a chevron element
  (data-testid="class-chevron")
- **AND** the chevron has class `class-chevron--open` (rotated 90°,
  pointing down) on initial load
- **AND** the corresponding `<div class="class-section-body">` is visible

#### Scenario: Clicking the class header collapses the section
- **WHEN** the user clicks anywhere on a class section header
  (data-testid="class-section-header")
- **THEN** the `isOpen` state of that class section toggles to `false`
- **AND** the chevron loses the `class-chevron--open` class (rotates
  back to pointing right)
- **AND** the `<div class="class-section-body">` gains the
  `class-section-body--collapsed` class
- **AND** the asset table rows, compare bars, and progress bars inside
  that class become hidden (no longer in the rendered layout)

#### Scenario: Clicking the class header again expands the section
- **WHEN** the user clicks the class section header a second time
- **THEN** the `isOpen` state toggles back to `true`
- **AND** the chevron regains the `class-chevron--open` class
- **AND** the `class-section-body--collapsed` class is removed
- **AND** the asset table rows, compare bars, and progress bars are
  visible again

#### Scenario: Default state is expanded on every load
- **WHEN** the dashboard loads or is reloaded
- **THEN** every class section has `isOpen: true` (no persistence
  across reloads)
- **AND** every asset table is visible
- **AND** no `class-section-body--collapsed` class is present on any
  section body

#### Scenario: Collapse state is per-class, not global
- **WHEN** class A is collapsed and class B is expanded
- **THEN** clicking class B's header expands/collapses class B only
- **AND** class A's `isOpen` state is unchanged

## ADDED Requirements

### Requirement: Column widths
The asset table MUST declare explicit widths for each of the 8 columns
so text columns ("Ativo", "Classe") get enough room for typical
Brazilian-portuguese asset names and class names, and numeric columns
("Qtd", "Alvo % classe", etc.) stay readable without wasting space.

The widths MUST sum to 100% of the table width and MUST be applied via
CSS (`.asset-table th:nth-child(N) { width: X%; }`) so the layout is
centralised and survives Jinja template regeneration. The widths MUST
be:

| Column | Width |
|---|---|
| Ativo | 24% |
| Classe | 18% |
| Qtd | 6% |
| Valor | 14% |
| Alvo % classe | 11% |
| Atual % classe | 11% |
| Alvo % total | 9% |
| Atual % total | 7% |

The `<th>` elements MUST have `transition: width 200ms` so any width
change (initial paint, future responsive adjustments) animates
smoothly.

#### Scenario: Column widths match the spec
- **WHEN** the dashboard renders the asset table at a standard desktop
  viewport (1280-1920px wide)
- **THEN** the `getBoundingClientRect().width` of each `<th>` matches
  the spec ratio within ±1px tolerance
- **AND** the sum of all 8 column widths equals the table width (no
  overflow, no underflow)

#### Scenario: Text columns are wide enough for typical names
- **WHEN** an asset has a name like "Tesouro Selic 2029" or a class
  has a name like "Renda Fixa Pós-Fixada"
- **THEN** the "Ativo" and "Classe" columns render the full name
  without ellipsis
- **AND** the numeric columns ("Qtd", "Valor", "Alvo % classe", etc.)
  render their values with the existing number/percentage formatting
