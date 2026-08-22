## MODIFIED Requirements

### Requirement: Icon catalog is scoped at 12 names

The system SHALL limit icon usage to the documented catalog: `add`,
`add_circle`, `upload`, `logout`, `close`, `warning`, `expand_more`,
`expand_less`, `check_circle`, `help`, `filter_alt`, and `sync`. Any use of an
icon name outside this catalog is out of scope and requires a new OpenSpec
change. The catalog SHALL be documented in `DESIGN.md §Iconography`.

#### Scenario: Sync action uses catalog icon

- **WHEN** the real-profile Patrimônio action strip renders `Atualizar posição`
- **THEN** its leading icon SHALL be a `<span class="icon icon--md"
  aria-hidden="true">sync</span>`
- **AND** the icon SHALL render through the existing Material Symbols Outlined
  ligature source loaded from
  `https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined`
- **AND** the icon SHALL inherit the button's current text color

#### Scenario: Catalog name in template

- **WHEN** a template renders an icon span
- **THEN** the inner text SHALL be one of the 12 catalog names

#### Scenario: Out-of-catalog icon detected

- **WHEN** a template uses an icon name not in this catalog
- **THEN** `openspec validate iconography-tokens --json` SHALL flag the
  violation (test-gated assertion)

### Requirement: Icons are documented in DESIGN.md §Iconography

The system SHALL keep `DESIGN.md §Iconography` updated with all 12 catalog
names and one-line use-sites, including `sync` for
`_patrimonio_actions.html::dashboard-sync-btn`. The extension path SHALL still
require a new OpenSpec change for any future name outside this catalog.

#### Scenario: Sync catalog entry is documented

- **WHEN** an operator or auditor reads `DESIGN.md §Iconography`
- **THEN** `sync` appears as the icon for the Patrimônio synchronization action
- **AND** all prior catalog names and use-sites remain present
