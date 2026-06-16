## ADDED Requirements

### Requirement: Design tokens define unambiguous foreground/background pairs

The system SHALL define a complete set of CSS custom properties in `app.css` `:root` block where every foreground token is paired with a background token and every pair meets WCAG 2.1 AA contrast.

#### Scenario: Every foreground token has a paired background context
- **WHEN** the audit's `color_token_inventory()` analyzes `app.css`
- **THEN** every `--*-fg`, `--*-ink`, and `--*-text` token SHALL have a known adjacent background token

#### Scenario: Class swatch tokens meet body text contrast
- **WHEN** `color_token_inventory()` computes contrast ratio for each `--class-*` token against `--bg`
- **THEN** every `--class-*` token SHALL have contrast ≥ 4.5:1 against `--bg`

#### Scenario: Status ink tokens meet contrast on status fills
- **WHEN** `color_token_inventory()` computes contrast ratio for `--negative-ink` against `--negative` and `--positive-ink` against `--positive`
- **THEN** each status ink SHALL have contrast ≥ 4.5:1 against its paired fill

#### Scenario: Error feedback tokens meet body text contrast
- **WHEN** `color_token_inventory()` computes contrast ratio for `--error-fg` against `--error-bg`
- **THEN** contrast SHALL be ≥ 4.5:1

### Requirement: Each token pair has documented minimum contrast ratio

The system SHALL document minimum WCAG 2.1 AA contrast ratios for every foreground/background token pair in DESIGN.md token table.

#### Scenario: Token table includes Contrast column
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** every row SHALL include a "Contrast" column with the minimum ratio (e.g., "≥ 4.5:1" or "≥ 3:1")

#### Scenario: Every `--class-*` token documents its contrast
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** each `--class-*` row SHALL include its documented contrast ratio against `--bg`

### Requirement: DESIGN.md reflects corrected token values with rationale

DESIGN.md SHALL be updated to reflect the corrected token system. The color strategy section SHALL include rationale for each change and the component inventory SHALL be annotated with token references.

#### Scenario: Color strategy section explains changes
- **WHEN** a reader views DESIGN.md after Phase 2
- **THEN** the color strategy section SHALL document the corrected token values and rationale for each correction

#### Scenario: Component inventory lists token dependencies
- **WHEN** a reader views the component inventory in DESIGN.md
- **THEN** each component SHALL list the foreground and background tokens it depends on
