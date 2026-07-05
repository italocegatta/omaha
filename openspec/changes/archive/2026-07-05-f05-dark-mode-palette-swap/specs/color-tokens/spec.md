## MODIFIED Requirements

### Requirement: Design tokens define unambiguous foreground/background pairs

The system SHALL define a complete set of CSS custom properties in `app.css` `:root` block where every foreground token is paired with a background token and every pair meets WCAG 2.1 AA contrast on the dark surface (`--bg: oklch(L≈0.18 hue≈60 chroma≈0.01)` warm-neutral, NOT pure black, NOT cold blue-gray).

#### Scenario: Every foreground token has a paired background context
- **WHEN** the audit's `color_token_inventory()` analyzes `app.css`
- **THEN** every `--*-fg`, `--*-ink`, and `--*-text` token SHALL have a known adjacent background token
- **AND** every foreground/background pair SHALL meet WCAG 2.1 AA contrast on the dark surface (`--bg` lightness ≈ 0.18)

#### Scenario: Class swatch tokens meet body text contrast on dark surface
- **WHEN** `color_token_inventory()` computes contrast ratio for each `--class-*` token against `--bg`
- **THEN** every `--class-*` token SHALL have contrast ≥ 4.5:1 against the dark `--bg`
- **AND** swatch 2 SHALL be hue-shifted (≤ 135) to remain visually distinct from `--positive` (hue 145)

#### Scenario: Status ink tokens meet contrast on status fills
- **WHEN** `color_token_inventory()` computes contrast ratio for `--negative-ink` against `--negative` and `--positive-ink` against `--positive`
- **THEN** each status ink SHALL have contrast ≥ 4.5:1 against its paired fill
- **AND** `--negative-ink` and `--positive-ink` SHALL be dark (lightness ≤ 0.25) because the fills are lightness-lifted to ≥ 0.65 on dark mode

#### Scenario: Error feedback tokens meet body text contrast
- **WHEN** `color_token_inventory()` computes contrast ratio for `--error-fg` against `--error-bg`
- **THEN** contrast SHALL be ≥ 4.5:1
- **AND** `--error-bg` SHALL be a darkness-shifted red surface (lightness ≤ 0.35) with `--error-fg` as a lightness-lifted red foreground (lightness ≥ 0.70)

#### Scenario: Body background renders as dark warm-neutral
- **WHEN** `body { background: var(--bg); }` is applied
- **THEN** `--bg` SHALL resolve to `oklch(L≈0.18 hue≈60 chroma≈0.01)` — dark warm-neutral, NOT `oklch(0 0 0)`, NOT `oklch(0.18 0.01 220)`

#### Scenario: Surface elevation via lightness, not shadow
- **WHEN** cards use `--surface` and form wells use `--surface-sunk`
- **THEN** `--surface` SHALL be lightness ≥ +0.03 over `--bg` (cards lift via claridade)
- **AND** `--surface-sunk` SHALL be lightness ≤ -0.02 under `--bg` (form wells descem via escurecimento)
- **AND** no card SHALL reintroduce `box-shadow` to compensate for the new lightness gradient

### Requirement: Each token pair has documented minimum contrast ratio

The system SHALL document minimum WCAG 2.1 AA contrast ratios for every foreground/background token pair in DESIGN.md token table, calibrated against the dark `--bg` surface.

#### Scenario: Token table includes Contrast column
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** every row SHALL include a "Contrast" column with the minimum ratio (e.g., "≥ 4.5:1" or "≥ 3:1")

#### Scenario: Every `--class-*` token documents its contrast on dark surface
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** each `--class-*` row SHALL include its documented contrast ratio against `--bg` (dark surface)
- **AND** swatch 2 row SHALL document its hue shift away from `--positive` hue

### Requirement: DESIGN.md reflects corrected token values with rationale

DESIGN.md SHALL be updated to reflect the dark token system. The color strategy section SHALL include rationale for the inversion (lightness flip, hue preserved, accent lifted) and the component inventory SHALL be annotated with token references for the new dark surface.

#### Scenario: Color strategy section explains the dark inversion
- **WHEN** a reader views DESIGN.md after F05
- **THEN** the color strategy section SHALL document that body `--bg` was inverted from off-white to dark warm-neutral (lightness ≈ 0.18, hue 60, chroma ≈ 0.01)
- **AND** SHALL explain that hue 60 was preserved (NOT shifted to cold blue) to maintain the "domestic" register
- **AND** SHALL explain that `--accent`, `--positive`, `--negative` were lightness-lifted (NOT hue-shifted) to keep the same fern-green / coral / blue identities
- **AND** SHALL explain that swatch 2 was hue-shifted to 130 to disambiguate from `--positive` (hue 145)

#### Scenario: Component inventory lists token dependencies
- **WHEN** a reader views the component inventory in DESIGN.md
- **THEN** each component SHALL list the foreground and background tokens it depends on
- **AND** the documented pairs SHALL resolve to AA contrast on the dark surface
