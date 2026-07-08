# color-tokens Specification

## Purpose
CSS custom-property color tokens defined in `src/omaha/static/app.css :root`, paired with documented WCAG 2.1 AA contrast ratios. Tokens are dark warm-neutral (post-F05 inversion, hue 60 body warmth preserved), re-derived against the Status Invest maximal register per D02 (post-F08): emerald accent, fern-leaning positive, coral negative, magenta-red class-3 to disambiguate from negative, amber warning. Foreground/background pairs resolve four ambiguity invariants — hue gap, lightness hierarchy, chromatic separation, Python-vs-CSS tuple parity.

## Requirements
### Requirement: Design tokens define unambiguous foreground/background pairs

The system SHALL define a complete set of CSS custom properties in `app.css` `:root` block where every foreground token is paired with a background token and every pair meets WCAG 2.1 AA contrast on the dark surface (`--bg: oklch(L≈0.18 hue≈60 chroma≈0.01)` warm-neutral, NOT pure black, NOT cold blue-gray). Color tokens SHALL resolve four ambiguity invariants documented in the D02 redesign session: (a) `--class-3` and `--negative` SHALL differ by ≥ 320° hue so a red class swatch is chromatically distinguishable from a red loss number; (b) `--positive` SHALL sit at lightness ≥ 0.74 so the "data signal" reads as bright against the dark body; (c) the Python `_CLASS_COLORS` tuple SHALL mirror the `--class-N` tokens (one source of truth — no hex-vs-OKLCH drift); (d) `--accent` and `--positive` SHALL differ by ≥ 6° hue with positive lightness ≥ accent lightness, so the brand-mark-green and the gain-green are visually distinct.

#### Scenario: Every foreground token has a paired background context
- **WHEN** the audit's `color_token_inventory()` analyzes `app.css`
- **THEN** every `--*-fg`, `--*-ink`, and `--*-text` token SHALL have a known adjacent background token
- **AND** every foreground/background pair SHALL meet WCAG 2.1 AA contrast on the dark surface (`--bg` lightness ≈ 0.18)

#### Scenario: Class swatch tokens meet body text contrast on dark surface
- **WHEN** `color_token_inventory()` computes contrast ratio for each `--class-*` token against `--bg`
- **THEN** every `--class-*` token SHALL have contrast ≥ 4.5:1 against the dark `--bg`
- **AND** swatch 2 SHALL be hue-shifted (≤ 135) to remain visually distinct from `--positive` (hue 145)
- **AND** `--class-3` hue SHALL be ≥ 320° distant from `--negative` hue (post-F08: class-3 hue 350, negative hue 25 — gap 325°)

#### Scenario: Status ink tokens meet contrast on status fills
- **WHEN** `color_token_inventory()` computes contrast ratio for `--negative-ink` against `--negative` and `--positive-ink` against `--positive`
- **THEN** each status ink SHALL have contrast ≥ 4.5:1 against its paired fill
- **AND** `--negative-ink` and `--positive-ink` SHALL be dark (lightness ≤ 0.25) because the fills are lightness-lifted to ≥ 0.65 on dark mode
- **AND** `--positive` lightness SHALL be ≥ 0.74 so the gain signal reads as bright against the dark body (post-F08: positive at `oklch(0.79 0.19 145)`)

#### Scenario: Accent and positive are chromatically distinct
- **WHEN** `color_token_inventory()` computes the hue and lightness delta between `--accent` and `--positive`
- **THEN** `hue(--positive) - hue(--accent)` SHALL be ≥ 6° (post-F08: positive hue 145, accent hue 152 — gap 7°)
- **AND** `lightness(--positive) > lightness(--accent)` SHALL hold so positive reads as the brighter signal (post-F08: positive L 0.79 > accent L 0.68)

#### Scenario: Python class-color tuple mirrors the CSS tokens
- **WHEN** the audit compares `_CLASS_COLORS` (Python tuple in `routes/pages.py` and `audit/inventory.py`) against the `--class-N` tokens in `app.css`
- **THEN** each `_CLASS_COLORS[i]` SHALL parse to the same OKLCH value as `--class-(i+1)`
- **AND** the tuple SHALL contain 8 OKLCH strings, NOT inline hex literals (post-F08: zero hex literals in either tuple)

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

The system SHALL document minimum WCAG 2.1 AA contrast ratios for every foreground/background token pair in DESIGN.md token table, calibrated against the dark `--bg` surface. Post-F08 the documented values reflect the D02 register decision: emerald accent at `oklch(0.68 0.20 152)`, fern-leaning positive at `oklch(0.79 0.19 145)`, coral negative at `oklch(0.69 0.20 25)`, class-3 magenta-red at `oklch(0.72 0.18 350)`, amber warning at `oklch(0.78 0.16 75)`.

#### Scenario: Token table includes Contrast column
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** every row SHALL include a "Contrast" column with the minimum ratio (e.g., "≥ 4.5:1" or "≥ 3:1")

#### Scenario: Every `--class-*` token documents its contrast on dark surface
- **WHEN** a reader views the token table in DESIGN.md
- **THEN** each `--class-*` row SHALL include its documented contrast ratio against `--bg` (dark surface)
- **AND** swatch 2 row SHALL document its hue shift away from `--positive` hue
- **AND** swatch 3 row SHALL document its hue gap to `--negative` (post-F08: hue 350 vs negative hue 25, gap 325°)

### Requirement: DESIGN.md reflects corrected token values with rationale

DESIGN.md SHALL be updated to reflect the D02 Status Invest maximal register. The color strategy section SHALL include rationale for the inversion (lightness flip, hue preserved), the class-3 hue rotation (25 → 350 magenta-red), the accent / positive chromatic separation (hue gap 7° + positive lightness > accent lightness), and the Python-vs-CSS tuple alignment. The component inventory SHALL be annotated with token references for the new dark surface.

#### Scenario: Color strategy section explains the dark inversion
- **WHEN** a reader views DESIGN.md after F08
- **THEN** the color strategy section SHALL document that body `--bg` was inverted from off-white to dark warm-neutral (lightness ≈ 0.18, hue 60, chroma ≈ 0.01)
- **AND** SHALL explain that hue 60 was preserved (NOT shifted to cold blue) to maintain the "domestic" register
- **AND** SHALL explain that `--accent` and `--positive` were re-derived (post-F08) so positive lightness (0.79) sits above accent lightness (0.68) — positive reads as the brighter signal, accent as the brand mark
- **AND** SHALL explain that `--class-3` was hue-shifted from 25 to 350 (magenta-red) to disambiguate from `--negative` (hue 25) — categorical class label ≠ financial loss signal

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
