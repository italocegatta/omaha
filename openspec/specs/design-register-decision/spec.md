# design-register-decision Specification

## Purpose
Owner-resolved design register direction, memorialized in canonical
documentation artifacts (`openspec/PRD.md` §4.10 as descriptive
memorial; `DESIGN.md` §Color strategy, §Typography, §Component
inventory, §Iconography, §Anti-patterns as canonical implementation
reference). The register chosen by the owner (D02, archived
2026-07-07) is **Status Invest maximal, sidebar not reintroduced**.
This spec records the architectural decisions for auditability and
to unblock subsequent visual-surface slices (F08 palette, F09
typography, F10 component state language + table pattern, F12
Material Symbols icons) and explicitly blocks F11 (sidebar
reintroduce) and F13 (light/dark toggle) because they are
incompatible with the chosen register.

## Requirements

### Requirement: Design register memorialized in PRD and DESIGN.md

The system SHALL memorialize the owner-resolved design register
decisions (D02) in `openspec/PRD.md` §4.10 (as a descriptive
memorial, not prescriptive rules) and `DESIGN.md` §Color strategy,
§Typography, §Component inventory, §Iconography, and §Anti-patterns
(as the canonical implementation reference).

The memorialized register SHALL be:

- **Register**: Status Invest maximal, sidebar NOT reintroduced
- **Class-3 hue**: 350 magenta-red (perceptually distinct from
  `--negative` at hue 25)
- **Display face**: Red Hat Display (sans, 700+) for portfolio header
  and other prominent data surfaces
- **Sidebar**: NOT reintroduced — top nav from F02 preserved
- **Light/dark toggle**: NOT introduced — dark-only per F05
  D-F05.10 maintained
- **Body warmth**: hue 60 warm-neutral (chroma ~0.012) maintained
- **Scope of delivery**: 3 slices (F08 palette → F09 typography →
  F10 component state language + table pattern)

#### Scenario: PRD §4.10 reads as memorial
- **WHEN** owner or auditor reads PRD §4.10
- **THEN** the section SHALL describe the chosen register in prose
  rather than prescribe token values
- **AND** the section SHALL reference `DESIGN.md` as the canonical
  source for token values

#### Scenario: DESIGN.md §Color strategy reflects SI maximal
- **WHEN** owner or auditor reads DESIGN.md §Color strategy
- **THEN** the section SHALL document emerald accent (`oklch(0.68
  0.20 152)`), fern-leaning positive (`oklch(0.79 0.19 145)`),
  coral negative (`oklch(0.69 0.20 25)`), amber warning, and
  class-3 magenta-red (`oklch` family near hue 350)
- **AND** the section SHALL document surface warm-neutral dark
  with hue 60 + chroma ~0.012

#### Scenario: DESIGN.md §Typography reflects Red Hat Display
- **WHEN** owner or auditor reads DESIGN.md §Typography
- **THEN** the section SHALL document Red Hat Display as display
  face for portfolio header (700+) and Inter variable with
  feature-settings `tnum, cv01, ss01, ss02` for body

#### Scenario: DESIGN.md §Component inventory reflects 5-state language
- **WHEN** owner or auditor reads DESIGN.md §Component inventory
- **THEN** the section SHALL enumerate the 5 states (idle/hover/
  focus/disabled/error) for inputs, buttons, tabs, and table rows
- **AND** the section SHALL document table pattern upgrade (sticky
  headers, hover row bg lift, total row emphasis, action column
  visible only on hover, numeric tnum + right-alignment)
- **AND** the section SHALL document section dividers hairline +
  `::selection` accent + form autofill override

#### Scenario: DESIGN.md §Iconography reflects Material Symbols
- **WHEN** owner or auditor reads DESIGN.md §Iconography
- **THEN** the section SHALL document Material Symbols Outlined as
  the icon system (loaded via Google Fonts)
- **AND** the section SHALL list icon catalog: add class, add
  asset, import, sign out, warning triangle, close, expand chevron,
  theme toggle (if F13 unblocks)

#### Scenario: PRD §5.3 marks D02 gate as resolved
- **WHEN** owner or auditor reads PRD §5.3
- **THEN** the section SHALL indicate D02 as resolved (date +
  register chosen)
- **AND** the section SHALL list F08-F10 + F12 as unblocked
- **AND** the section SHALL list F11 + F13 as effectively blocked
  (F11 = register ≠ A; F13 = owner did not request toggle)

### Requirement: D02 unblocks F08, F09, F10, F12

When D02 is archived, the system SHALL permit proposing F08
(palette overhaul v2), F09 (typography refresh), F10 (component
state language + table pattern), and F12 (Material Symbols icons)
without further owner gates.

#### Scenario: F08 ready after D02 archived
- **WHEN** D02 has been archived
- **THEN** an agent SHALL be able to invoke `openspec-propose` for
  `f08-palette-overhaul-v2` and the resulting proposal SHALL be
  `valid: true` without requiring additional owner input

#### Scenario: F11 and F13 remain blocked after D02 archived
- **WHEN** D02 has been archived
- **THEN** F11 (sidebar reintroduce) SHALL remain effectively
  blocked because register ≠ A
- **AND** F13 (light/dark toggle) SHALL remain blocked because
  owner did not request it
- **AND** both slices SHALL remain in the roadmap as historical
  record with `Blocked` status and explicit notes referencing D02