## ADDED Requirements

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
SHALL use tabular figures and right-align.

#### Scenario: Sticky table header on scroll
- **WHEN** the user scrolls a page containing `.table-sticky-header`
- **THEN** the `<thead>` remains pinned to `top: 0` with
  `background: var(--surface-sunk)` and `z-index: 1`

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

#### Scenario: Numeric columns use tabular figures
- **WHEN** a `<td>` contains a numeric value (currency or percent)
- **THEN** the cell renders with `font-variant-numeric: tabular-nums` and
  `text-align: right`

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
