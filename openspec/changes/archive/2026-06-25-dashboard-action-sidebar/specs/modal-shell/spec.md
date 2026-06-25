## Purpose

A shared CSS class set for modal overlays that gives every modal in
the app a consistent visual shell. The shell is presentation-only; the
Alpine stores that back each modal (and the field-level markup inside
`.modal-body`) stay bespoke per modal.

## ADDED Requirements

### Requirement: Modal shell class set

The app MUST define a shared CSS class set for modal overlays:
`.modal-overlay`, `.modal-panel`, `.modal-header`, `.modal-title`,
`.modal-body`, `.modal-footer`, `.modal-close`. Every modal in the app
(importModal, addAssetModal, newClassModal, and any future modal) MUST
render inside a `<div class="modal-overlay">` containing a
`<div class="modal-panel">`. The overlay MUST be a fixed full-viewport
container with a semi-opaque backdrop; the panel MUST be a centered
card with `--surface` background, 1px border, 8px radius, max-width
480px, padding 1.5rem, max-height 90vh, vertical overflow scroll.

#### Scenario: Overlay covers the viewport

- **WHEN** any modal is open
- **THEN** the `.modal-overlay` element has computed `position: fixed`
- **AND** it covers the entire viewport (`inset: 0`)
- **AND** it has a backdrop background (a semi-opaque fill over
  `--ink`)

#### Scenario: Panel is centered and scrollable

- **WHEN** the modal is open
- **THEN** the `.modal-panel` is visually centered in the viewport
- **AND** the panel's `max-height` is `90vh`
- **AND** the panel's content scrolls vertically when it overflows
  the available height

### Requirement: Modal header has title and close button

Each modal's `.modal-header` MUST contain a `.modal-title` element
holding the modal's Portuguese title (e.g. `Importar extrato`,
`Adicionar ativo`, `Nova classe`) and a `.modal-close` button labeled
with the multiplication sign (`×`) that closes the modal. The header
MUST have a 1px bottom border separating it from the body.

#### Scenario: Header renders title and close

- **WHEN** any modal is open
- **THEN** the `.modal-header` contains a `.modal-title` with the
  modal's title text in Portuguese
- **AND** a `.modal-close` button with `×` is rendered in the header

#### Scenario: Close button dismisses modal

- **WHEN** the user clicks the `.modal-close` button
- **THEN** the modal's Alpine store `open` flag becomes `false`
- **AND** the overlay becomes hidden

### Requirement: Modal footer carries the action buttons

Each modal's `.modal-footer` MUST contain the modal's primary action
button (Save / Submit / Confirm) and any cancel button. The footer
MUST right-align its content (`justify-content: flex-end`) and MUST
sit below the `.modal-body` with a top margin separating it.

#### Scenario: Footer right-aligns action buttons

- **WHEN** any modal is open
- **THEN** the `.modal-footer` element has computed
  `justify-content: flex-end`
- **AND** the primary action button is rendered in the footer

### Requirement: Modal body is bespoke per modal

The `.modal-body` element's content MUST be unique to each modal:
the import modal renders the file-picker step and preview step; the
add-asset modal renders the class selector, name, and target_pct
inputs; the new-class modal renders the name and target_pct inputs.
No shared `.modal-body` content is required — only the wrapper class.

#### Scenario: Import modal body shows step 1 by default

- **WHEN** the import modal opens
- **THEN** `.modal-body` renders the file-picker step with
  `data-testid="import-step1"`

#### Scenario: New-class modal body shows form fields

- **WHEN** the new-class modal opens
- **THEN** `.modal-body` renders a name input
  (`data-testid="new-class-modal-name-input"`) and a target_pct input
  (`data-testid="new-class-modal-pct-input"`)