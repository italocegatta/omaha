## ADDED Requirements

### Requirement: Derived class tint tokens back import-preview chips on dark surface

The system SHALL define derived tint tokens `--class-1-tint` through `--class-8-tint` in `src/omaha/static/app.css :root`, each computed from the corresponding `--class-N` token against `--surface`. Import-preview chip backgrounds SHALL consume those tint tokens instead of inline hex literals so the preview stays aligned with the active class palette on the dark surface.

#### Scenario: Tint token family exists for every import-preview class slot
- **WHEN** the audit reads `app.css :root`
- **THEN** it SHALL find `--class-1-tint` through `--class-8-tint`
- **AND** each tint token SHALL resolve from `var(--class-N)` and `var(--surface)`, not from a hardcoded hex literal

#### Scenario: Import preview class chips consume tint tokens
- **WHEN** the stylesheet resolves `.import-class-cell--cls-0` through `.import-class-cell--cls-7`
- **THEN** each rule SHALL use the matching `var(--class-N-tint)` background
- **AND** no `.import-class-cell--cls-*` rule SHALL retain `color-mix(in srgb, #<hex> 38%, var(--surface))`
