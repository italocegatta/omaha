# css-cleanup

## Purpose

Enforces CSS hygiene in `app.css` — no duplicate selectors, no dead rules, no conflicting `:root` blocks, and consistent unit usage.

## Requirements

### Requirement: CSS deduplication

The stylesheet `app.css` SHALL NOT contain duplicate selectors where an earlier block is silently overridden by a later block with the same selector and identical or superseding properties.

#### Scenario: No duplicate `.btn` blocks
- **WHEN** the file is parsed
- **THEN** there SHALL be exactly one `.btn` declaration block, one `.btn-primary` block, and one `.btn:hover:not(:disabled)` block

#### Scenario: Single `:root` block for column variables
- **WHEN** the file is parsed
- **THEN** there SHALL be exactly one `:root` block defining `--col-*` variables (the pixel-based F15 version)

#### Scenario: Single `prefers-reduced-motion` media query
- **WHEN** the file is parsed
- **THEN** there SHALL be exactly one `@media (prefers-reduced-motion: reduce)` block

### Requirement: Dead code removal

The stylesheet SHALL NOT contain rules that are fully superseded by later declarations with the same selector.

#### Scenario: No dead `.dashboard-asset-list` rules
- **WHEN** `.dashboard-asset-list` rules exist at two locations
- **THEN** only the later (active) block SHALL remain

#### Scenario: No duplicate `.muted` rules
- **WHEN** `.muted` is defined twice identically
- **THEN** only one SHALL remain

#### Scenario: No empty rule blocks
- **WHEN** a rule block has zero declarations
- **THEN** it SHALL be removed

### Requirement: Unit consistency

Spacing values on generic components SHALL use `rem` units, not `px`.

#### Scenario: `.section-divider` uses rem
- **WHEN** `.section-divider` margin is declared
- **THEN** it SHALL use `rem` units (`1.5rem 0`), not `px` (`24px 0`)
