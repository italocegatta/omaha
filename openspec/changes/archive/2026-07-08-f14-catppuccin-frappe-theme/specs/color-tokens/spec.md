## MODIFIED Requirements

### Requirement: Design tokens define unambiguous foreground/background pairs

The system SHALL define a complete set of CSS custom properties in `app.css` `:root` block where every foreground token is paired with a background token and every pair meets WCAG 2.1 AA contrast on the dark surface (`--bg: oklch(0.329 0.032 274.8)` Catppuccin Frappe cool blue-gray, NOT warm brown hue 60). Color tokens SHALL resolve four ambiguity invariants: (a) `--class-3` and `--negative` SHALL differ by sufficient hue gap so a class swatch is chromatically distinguishable from a loss number; (b) `--positive` SHALL sit at lightness ≥ 0.74 so the "data signal" reads as bright against the dark body; (c) the Python `_CLASS_COLORS` tuple SHALL mirror the `--class-N` tokens (one source of truth — no hex-vs-OKLCH drift); (d) `--accent` and `--positive` SHALL differ by ≥ 6° hue with positive lightness ≥ accent lightness, so the brand-mark and the gain-green are visually distinct.

#### Scenario: Every foreground token has a paired background context
- **WHEN** the audit's `color_token_inventory()` analyzes `app.css`
- **THEN** every `--*-fg`, `--*-ink`, and `--*-text` token SHALL have a known adjacent background token
- **AND** every foreground/background pair SHALL meet WCAG 2.1 AA contrast on the dark surface (`--bg` lightness ≈ 0.329)

#### Scenario: Class swatch tokens meet body text contrast on dark surface
- **WHEN** `color_token_inventory()` computes contrast ratio for each `--class-*` token against `--bg`
- **THEN** every `--class-*` token SHALL have contrast ≥ 4.5:1 against the dark `--bg`
- **AND** swatch 2 SHALL be visually distinct from `--positive`
- **AND** `--class-3` SHALL be visually distinct from `--negative`

#### Scenario: Status ink tokens meet contrast on status fills
- **WHEN** `color_token_inventory()` computes contrast ratio for `--negative-ink` against `--negative` and `--positive-ink` against `--positive`
- **THEN** each status ink SHALL have contrast ≥ 4.5:1 against its paired fill
- **AND** `--negative-ink` and `--positive-ink` SHALL be dark (lightness ≤ 0.30) because the fills are lightness-lifted to ≥ 0.71 on dark mode
- **AND** `--positive` lightness SHALL be ≥ 0.74 so the gain signal reads as bright against the dark body

#### Scenario: Accent and positive are chromatically distinct
- **WHEN** `color_token_inventory()` computes the hue and lightness delta between `--accent` and `--positive`
- **THEN** `hue(--positive) - hue(--accent)` SHALL be ≥ 6°
- **AND** `lightness(--positive) > lightness(--accent)` SHALL hold so positive reads as the brighter signal

#### Scenario: Python class-color tuple mirrors the CSS tokens
- **WHEN** the audit compares `_CLASS_COLORS` (Python tuple in `routes/pages.py` and `audit/inventory.py`) against the `--class-N` tokens in `app.css`
- **THEN** each `_CLASS_COLORS[i]` SHALL parse to the same OKLCH value as `--class-(i+1)`
- **AND** the tuple SHALL contain 8 OKLCH strings, NOT inline hex literals

#### Scenario: Error feedback tokens meet body text contrast
- **WHEN** `color_token_inventory()` computes contrast ratio for `--error-fg` against `--error-bg`
- **THEN** contrast SHALL be ≥ 4.5:1
- **AND** `--error-bg` SHALL be a darkness-shifted red surface (lightness ≤ 0.40) with `--error-fg` as a lightness-lifted red foreground (lightness ≥ 0.70)

#### Scenario: Body background renders as Catppuccin Frappe cool blue-gray
- **WHEN** `body { background: var(--bg); }` is applied
- **THEN** `--bg` SHALL resolve to `oklch(0.329 0.032 274.8)` — Catppuccin Frappe base, NOT warm brown hue 60

#### Scenario: Surface elevation hierarchy via lightness
- **WHEN** page shell cards use `--surface`, portfolio header and class sections use `--surface-elevated`, and asset tables use `--surface-sunk`
- **THEN** `--surface-elevated` SHALL be lightness ≥ +0.03 over `--bg` (portfolio header and class sections lift)
- **AND** `--surface` SHALL be lightness ≥ +0.10 over `--bg` (page shell cards lift)
- **AND** `--surface-sunk` SHALL be lightness ≤ -0.04 under `--bg` (asset tables sink)
- **AND** no card SHALL reintroduce `box-shadow` to compensate for the lightness gradient

### Requirement: Each token pair has documented minimum contrast ratio

The system SHALL document minimum WCAG 2.1 AA contrast ratios for every foreground/background token pair in DESIGN.md token table, calibrated against the dark `--bg` surface. Post-F14 the documented values reflect the Catppuccin Frappe palette: teal accent at `oklch(0.783 0.073 184.6)`, green positive at `oklch(0.812 0.107 133.4)`, red negative at `oklch(0.717 0.124 19.4)`, amber warning at `oklch(0.844 0.08 83.5)`.

#### Scenario: Token table includes Contrast column
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** every row SHALL include a "Contrast" column with the minimum ratio (e.g., "≥ 4.5:1" or "≥ 3:1")

#### Scenario: Every `--class-*` token documents its contrast on dark surface
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** each `--class-*` row SHALL include its documented contrast ratio against `--bg` (dark surface)

### Requirement: DESIGN.md reflects Catppuccin Frappe token values with rationale

DESIGN.md SHALL be updated to reflect the F14 Catppuccin Frappe theme swap. The color strategy section SHALL include rationale for the hue shift (hue 60 warm brown → hue 274 cool blue-gray), the surface elevation hierarchy (page shell `--surface`, portfolio header + class section `--surface-elevated`, asset table `--surface-sunk`), the class header differentiation (tinted bg + border-bottom, no swatch square), and the Python-vs-CSS tuple alignment.

#### Scenario: Color strategy section explains the Catppuccin Frappe swap
- **WHEN** a reader views DESIGN.md after F14
- **THEN** the color strategy section SHALL document that body `--bg` was shifted from warm brown (hue 60) to Catppuccin Frappe cool blue-gray (hue ~274)
- **AND** SHALL explain the surface elevation hierarchy: `--surface` for page shell cards, `--surface-elevated` for portfolio header and class sections, `--surface-sunk` for asset tables
- **AND** SHALL explain that `--accent` shifted from emerald (hue 152) to teal (hue 184.6) to match the Catppuccin Frappe accent
- **AND** SHALL explain that class headers use tinted bg (`color-mix 30% class-color`) + 2px solid border-bottom, with no swatch square

#### Scenario: Component inventory lists token dependencies
- **WHEN** a reader views the component inventory in DESIGN.md
- **THEN** each component SHALL list the foreground and background tokens it depends on
- **AND** the documented pairs SHALL resolve to AA contrast on the dark surface

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
