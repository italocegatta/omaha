# palette-tokens Specification

## Purpose

Define the system's color token architecture using OKLCH color space with guaranteed WCAG AA contrast ratios for all foreground/background pairs.

## ADDED Requirements

### Requirement: Token pairs with documented contrast

The system SHALL define all color tokens as explicit foreground/background pairs, each with a computed WCAG AA contrast ratio documented in DESIGN.md.

#### Scenario: Token contrast meets WCAG AA

- **WHEN** the contrast ratio is computed for any defined token pair
- **THEN** it SHALL be ≥4.5:1 for normal text and ≥3:1 for large text (≥18px or ≥14px bold)

### Requirement: OKLCH color space

All color values in `:root` CSS custom properties SHALL use the OKLCH color function syntax.

#### Scenario: Token values use OKLCH

- **WHEN** inspecting any `--*` custom property in `app.css :root`
- **THEN** the value SHALL use `oklch()` function syntax

### Requirement: Negative/positive ink tokens

The system SHALL provide `--negative-ink` and `--positive-ink` custom properties for text-on-colored-background scenarios (e.g., delete confirm buttons).

#### Scenario: Delete button uses --negative-ink

- **WHEN** a delete-confirm button is rendered
- **THEN** text color SHALL be `var(--negative-ink)`, not a hardcoded `#fff`

### Requirement: Automated contrast verification

The system SHALL include an automated test that verifies all token pairs meet WCAG AA contrast thresholds.

#### Scenario: Test passes for all tokens

- **WHEN** `pytest tests/test_phase02_tokens.py` runs
- **THEN** it SHALL parse `app.css`, extract all `:root` custom properties, compute contrast for each documented pair, and assert ≥4.5:1 ratio
