## Purpose

Vocabulário 5-state feedback (idle/hover/focus/disabled/error) + table
pattern upgrade (sticky `<thead>`, hover row bg lift, total row
emphasis, action column só-on-hover) + extras D02 (section dividers
hairline, `::selection`, form autofill override, eyebrow labels,
form R$ prefix, prefers-reduced-motion respect, warning-line
border-left 4px como única exceção ao anti-pattern). Materializa o
contrato memorializado por `design-register-decision` (D02
§Components) como parte do register Status Invest maximal.

Aplicado em `src/omaha/static/app.css` bloco F10 (linhas finais do
arquivo) + 7 templates (`patrimonio.html`, `_patrimonio_class_section
.html`, `classes.html`, `rebalance.html`, `_rebalance_plan.html`,
mais fallthrough automático em `base.html`, `login.html`,
`import.html` via CSS-only). Spec não toca runtime contracts —
descreve apenas o contrato visual que F08/F09/F10 entregam juntos.

## Requirements

### Requirement: All interactive elements SHALL declare 5-state feedback vocabulary

The system SHALL render inputs, buttons, tabs, and table rows with explicit
feedback for five states: `idle`, `hover`, `focus`, `disabled`, `error`. Each
state SHALL use the fg/bg pair documented in `DESIGN.md` §Components and SHALL
preserve WCAG AA contrast in the active palette.

#### Scenario: Idle state on a button
- **WHEN** the user views a button in its resting state
- **THEN** the button renders with `--ink` foreground on `--surface`
  background, no outline

#### Scenario: Hover state on a button
- **WHEN** the user hovers the cursor over a button
- **THEN** the button background lifts to `--bg-hover` while the foreground
  remains `--ink`

#### Scenario: Focus state on an input via keyboard
- **WHEN** the user tabs to an input field
- **THEN** the input renders an `outline: 2px solid var(--color-focus)`
  ring with `outline-offset: 2px`

#### Scenario: Focus state via mouse click does NOT show ring
- **WHEN** the user clicks an input with the mouse (not keyboard)
- **THEN** the input does NOT render the focus ring (`:focus-visible`
  is honored, not `:focus`)

#### Scenario: Disabled state on a button
- **WHEN** a button is disabled (via `aria-disabled="true"` or `.is-disabled`)
- **THEN** the foreground is `--ink-muted`, background is `--surface`, cursor
  is `not-allowed`, and opacity is `0.6`

#### Scenario: Error state on an input
- **WHEN** an input has the `.is-error` class with an inline message
- **THEN** the foreground is `--error-fg`, background is `--error-bg`, and
  an inline `.input-error-message` element renders below the input

### Requirement: Data tables SHALL render sticky headers, hover lift, total row emphasis, and on-hover action column

The system SHALL render `<thead>` sticky within scroll, lift row background
on hover, emphasize the total row with bold + thicker border, and reveal
action column affordances only when the user hovers the row. Numeric columns
SHALL use tabular figures and right-align. Post-F14: asset tables use
`--surface-sunk` background (inset feel), row padding compacted to
`0.05rem` vertical, asset-table headers use a tinted background plus a
stronger separator line, and numeric cells use `--ink` at weight 600+
for maximum contrast.

#### Scenario: Sticky table header on scroll
- **WHEN** the user scrolls a page containing `.table-sticky-header`
- **THEN** the `<thead>` remains pinned to `top: 0` with
  `background: var(--surface-sunk)` and `z-index: 1`

#### Scenario: Asset table header differentiates from data rows
- **WHEN** a class section renders its `.asset-table`
- **THEN** each header cell SHALL use
  `background: color-mix(in srgb, var(--accent) 10%, var(--surface))`
- **AND** each header cell SHALL use
  `border-bottom: 2.5px solid var(--border-strong)`

#### Scenario: Sticky header is NOT applied to tables inside modals
- **WHEN** a table renders inside a `<dialog>` or modal container
- **THEN** the table does NOT receive `.table-sticky-header` (sticky
  behavior is reserved for top-level page tables only)

#### Scenario: Row hover lifts the background
- **WHEN** the user hovers the cursor over a `<tr>` in a table
- **THEN** every `<td>` in that row receives `background: var(--bg-hover)`
  for the duration of the hover

#### Scenario: Total row renders with bold + thick border-top
- **WHEN** a `<tr class="table-total">` renders at the bottom of a table
- **THEN** the row has `font-weight: 600` and
  `border-top: 2px solid var(--border-strong)`

#### Scenario: Action column is hidden in idle state
- **WHEN** the user views a table row in its idle state
- **THEN** any `<td class="row-actions">` renders with `opacity: 0`

#### Scenario: Action column reveals on row hover
- **WHEN** the user hovers the cursor over a row containing action cells
- **THEN** the action cells transition to `opacity: 1` within 80ms

#### Scenario: Action column is always visible on mobile
- **WHEN** the viewport is `max-width: 768px`
- **THEN** action cells render with `opacity: 1` regardless of hover state

#### Scenario: Asset table renders with sunk background
- **WHEN** a class section renders its asset table
- **THEN** the table SHALL use `background: var(--surface-sunk)` for an
  inset feel
- **AND** the table SHALL create visual hierarchy: page shell
  (`--surface`) > portfolio header / class section (`--surface-elevated`)
  > asset table (`--surface-sunk`)

#### Scenario: Row padding is compact
- **WHEN** asset table rows render
- **THEN** each `<td>` SHALL use `padding: 0.05rem 0.4rem` for
  extra-dense vertical compaction

#### Scenario: Numeric columns use tabular figures
- **WHEN** a `<td>` contains a numeric value (currency or percent)
- **THEN** the cell renders with `font-variant-numeric: tabular-nums` and
  `text-align: right`

#### Scenario: Numeric cells use high-contrast ink
- **WHEN** a `<td>` contains a numeric value (currency, percent, or quantity)
- **THEN** the cell SHALL render with `color: var(--ink)` and
  `font-weight: 600` or higher

### Requirement: Class section headers SHALL differentiate via tinted background and color border

The system SHALL render class section headers with a tinted background
(`color-mix(in srgb, var(--class-N) 30%, var(--bg))`) and a
`2px solid var(--class-N)` bottom border. The class name text SHALL carry
the class color. The swatch square SHALL be removed — the tinted header
itself provides class identity.

#### Scenario: Class header renders with tinted background
- **WHEN** a class section renders on the patrimonio page
- **THEN** the header SHALL use
  `background: color-mix(in srgb, var(--class-N) 30%, var(--bg))`
- **AND** the header SHALL use `border-bottom: 2px solid var(--class-N)`

#### Scenario: Class name carries the class color
- **WHEN** the class name renders in the header
- **THEN** the text SHALL use `color: var(--class-N)` and `font-weight: 700`
- **AND** no swatch square SHALL render next to the class name

#### Scenario: Class header differentiates from asset table
- **WHEN** the user views a class section
- **THEN** the header SHALL be visually distinct from the asset table below it
- **AND** the tinted background creates a clear boundary between class sections

### Requirement: Class section cards SHALL share the elevated summary-card surface

The system SHALL render each `.class-section` card with the same
`--surface-elevated` background used by the portfolio summary cards so the
class block reads as its own layer above the page shell.

#### Scenario: Class section card uses elevated surface
- **WHEN** the patrimonio dashboard renders class blocks
- **THEN** each `.class-section` SHALL use
  `background: var(--surface-elevated)`
- **AND** the class block SHALL visually separate from the parent page shell
  even before the tinted header appears

### Requirement: Trade toggle SHALL differentiate active and blocked states with color

The system SHALL render trade toggles with clear color differentiation:
Liberado (active) uses success green, Bloqueado (blocked) uses danger red.
Both states use angular borders (`border-radius: 4px`).

#### Scenario: Liberado toggle renders with success green
- **WHEN** a trade toggle shows "Liberado"
- **THEN** it SHALL render with
  `background: color-mix(in srgb, var(--positive) 15%, var(--surface))`
  and `color: var(--positive)`
- **AND** the border SHALL use
  `color-mix(in srgb, var(--positive) 50%, var(--border))`

#### Scenario: Bloqueado toggle renders with danger red
- **WHEN** a trade toggle shows "Bloqueado"
- **THEN** it SHALL render with
  `background: color-mix(in srgb, var(--negative) 12%, var(--surface))`
  and `color: var(--negative)`
- **AND** the border SHALL use
  `color-mix(in srgb, var(--negative) 40%, transparent)`

#### Scenario: Both toggle states use angular borders
- **WHEN** any trade toggle renders
- **THEN** `border-radius` SHALL be `4px` (not `999px`)

### Requirement: Pills and badges SHALL use angular border radius

The system SHALL render all pills, badges, and toggle elements with
`border-radius: 4px` instead of `999px`. This creates a consistent angular
aesthetic across the UI.

#### Scenario: Pill renders with angular border
- **WHEN** a pill (`.pill`, `.pill-alvo`, `.pill-ok`) renders
- **THEN** `border-radius` SHALL be `4px`

#### Scenario: Trade toggle renders with angular border
- **WHEN** a trade toggle (`.trade-pill`) renders
- **THEN** `border-radius` SHALL be `4px`

#### Scenario: Currency badge renders with angular border
- **WHEN** a currency badge (`.currency`) renders
- **THEN** `border-radius` SHALL be `4px`

### Requirement: Sections SHALL render hairline dividers between major blocks

The system SHALL render `<hr class="section-divider">` between the three
major blocks of the patrimonio page (portfolio header, classes summary,
distribution) and between major blocks on the rebalance page.

#### Scenario: Section divider renders as a hairline horizontal rule
- **WHEN** the patrimonio page renders with all three major blocks
- **THEN** two `<hr class="section-divider">` elements appear, one between
  portfolio header and classes summary, another between classes summary
  and distribution

#### Scenario: Section divider is a single 1px border-top
- **WHEN** the section divider renders
- **THEN** it shows `border-top: 1px solid var(--border)` with
  `margin: 24px 0` and transparent background

### Requirement: Text selection SHALL use the accent color

The system SHALL style the `::selection` pseudo-element with
`background: var(--accent)` and `color: var(--accent-ink)` for all text
selection, making copy-paste legible in the brand color.

#### Scenario: Selecting body text shows accent background
- **WHEN** the user drags to select body text
- **THEN** the selection renders with `--accent` background and
  `--accent-ink` foreground

### Requirement: Form fields SHALL override browser autofill styles

The system SHALL override the default yellow/blue autofill background
applied by Chromium and WebKit so that autofilled fields render with
the same surface and ink tokens as manually-typed fields.

#### Scenario: Autofilled field renders with surface tokens
- **WHEN** the browser autofills an input (via password manager or
  address autofill)
- **THEN** the input shows `-webkit-text-fill-color: var(--ink)` and
  `box-shadow: 0 0 0 1000px var(--surface) inset`

### Requirement: Eyebrow labels SHALL render above totals and stats

The system SHALL render `<div class="label-xs">` elements as uppercase
section labels above totals and statistics. The label uses
`--ink-muted` foreground, `0.04em` letter-spacing, and `0.75rem` font-size.

#### Scenario: Eyebrow label renders above a total
- **WHEN** a section shows a total value
- **THEN** the label above renders uppercase with `0.04em` tracking and
  `--ink-muted` foreground

### Requirement: Currency input fields SHALL render with an R$ prefix

The system SHALL render a `<span class="input-prefix">R$</span>` inside
the label wrapper for numeric currency inputs. The R$ prefix SHALL apply
to the aporte input on the rebalance form.

#### Scenario: R$ prefix renders left of the aporte input
- **WHEN** the user views the `/rebalanceamento` page
- **THEN** the aporte input is wrapped in `<label class="input-prefix-wrap">`
  containing the `R$` span and the input itself, with a flat border between
  the prefix and the input

### Requirement: Motion SHALL respect the prefers-reduced-motion preference

The system SHALL honor `prefers-reduced-motion: reduce` by zeroing out all
CSS transitions and animations globally, ensuring users who disable motion
do not see animation effects.

#### Scenario: User with reduced motion sees no animations
- **WHEN** the user's OS or browser sets `prefers-reduced-motion: reduce`
- **THEN** all elements with `transition` or `animation` declarations render
  without those effects (overridden via `* { transition: none !important;
  animation: none !important }`)
