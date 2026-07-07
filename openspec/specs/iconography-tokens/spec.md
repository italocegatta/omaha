# iconography-tokens

Internal capability — describes the file-level visual contract for the
Material Symbols Outlined icon system. Catalog is scoped at 10 names per
the D02 SI maximal register decision (archived 2026-07-07) and F12
slice. Out-of-catalog requests require a new OpenSpec change.

## Purpose

The iconography tokens describe the wiring contract for icons on
authenticated pages: the Google Fonts URL, the CSS class hooks, the
10-name catalog, and the markup pattern. The capability is internal —
the user-facing surface (action buttons, warnings, modals, chevrons)
inherits the icon system automatically once `base.html` and `app.css`
load the font and the catalog hooks are present.

This spec is the post-F12 contract; see
`openspec/changes/archive/2026-07-07-f12-material-symbols-icons/` for
the slice that introduced the system.

## Requirements

### Requirement: Material Symbols Outlined font is loaded

The system SHALL load the Material Symbols Outlined font from Google Fonts via a `<link rel="stylesheet">` tag in `base.html` with the URL pattern `https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined`. The preconnect to `fonts.gstatic.com` SHALL already be present (reuses the preconnect added by F09 for Inter/Red Hat Display).

#### Scenario: Font URL present in base.html
- **WHEN** the operator opens any authenticated page
- **THEN** the served `base.html` SHALL contain the Material Symbols Outlined stylesheet link
- **AND** the link SHALL appear in the document `<head>` (above any icon-using templates)

#### Scenario: Font fails to load (CDN unreachable)
- **WHEN** Google Fonts CDN is unreachable from the user's network
- **THEN** icons SHALL fall back to the system default monospace font (tofu rendering)
- **AND** the page SHALL remain functional (no JS errors, no layout collapse)

### Requirement: Icon catalog is scoped at 10 names

The system SHALL limit icon usage to the documented catalog: `add`, `add_circle`, `upload`, `logout`, `close`, `warning`, `expand_more`, `expand_less`, `check_circle`, `help`. Any use of an icon name outside this catalog is out of scope and requires a new OpenSpec change. The catalog SHALL be documented in `DESIGN.md §Iconography`.

#### Scenario: Catalog name in template
- **WHEN** a template renders an icon span
- **THEN** the inner text SHALL be one of the 10 catalog names

#### Scenario: Out-of-catalog icon detected
- **WHEN** a template uses an icon name not in the catalog
- **THEN** `openspec validate iconography-tokens --json` SHALL flag the violation (test-gated assertion)

### Requirement: Icon size scale uses three modifiers

The system SHALL provide three CSS size modifiers: `.icon--sm` (16px), `.icon--md` (20px), `.icon--lg` (24px). The `.icon` base class SHALL be required for any icon span; size modifiers are optional and default to body text size when omitted.

#### Scenario: Small icon renders at 16px
- **WHEN** a template uses `<span class="icon icon--sm">add</span>`
- **THEN** the computed font-size SHALL be 16px
- **AND** the icon SHALL render inline with body label text

#### Scenario: Medium icon renders at 20px
- **WHEN** a template uses `<span class="icon icon--md">upload</span>`
- **THEN** the computed font-size SHALL be 20px
- **AND** the icon SHALL render as the leading element of a default button

#### Scenario: Large icon renders at 24px
- **WHEN** a template uses `<span class="icon icon--lg">warning</span>`
- **THEN** the computed font-size SHALL be 24px
- **AND** the icon SHALL render inside hero / empty-state containers

#### Scenario: Icon without size modifier
- **WHEN** a template uses `<span class="icon">add</span>` without a size modifier
- **THEN** the icon SHALL inherit the parent's font-size
- **AND** the icon SHALL still render via Material Symbols Outlined font

### Requirement: Icons inherit color via currentColor

The system SHALL style icons with `color: inherit` (via Material Symbols Outlined default + `.icon` rule cascade). No hardcoded color SHALL appear in the `.icon` rule body. Icons SHALL respect their parent element's text color (including 5-state hover/focus/disabled states from F10).

#### Scenario: Icon inherits button text color
- **WHEN** an icon is the leading child of a `.btn` element
- **THEN** the icon SHALL render in the same color as the button label
- **AND** hover state transitions SHALL apply to both icon and label

#### Scenario: Icon in dark theme
- **WHEN** the dark theme palette is active (F05)
- **THEN** icons SHALL render in `--ink` color via parent cascade
- **AND** no hardcoded color override SHALL be present in `.icon` rules

### Requirement: Icon markup uses ligature text with aria-hidden

The system SHALL render icons via `<span class="icon icon--{size}" aria-hidden="true">{catalog_name}</span>`. The inner text is the Material Symbols ligature source. The `aria-hidden="true"` attribute SHALL be present because adjacent button text labels the action. Screen readers SHALL NOT read the icon name.

#### Scenario: Screen reader skips icon
- **WHEN** a screen reader navigates to a button with leading icon
- **THEN** only the button label SHALL be announced
- **AND** the icon name SHALL be skipped (aria-hidden=true honored)

#### Scenario: Icon renders visually
- **WHEN** a sighted user views the button
- **THEN** the icon SHALL render via Material Symbols Outlined ligature
- **AND** the icon SHALL appear immediately before the label text

### Requirement: Icons are documented in DESIGN.md §Iconography

The system SHALL keep `DESIGN.md §Iconography` updated with the catalog as the source of truth. The section SHALL list all 10 icon names verbatim with a one-line use-site per icon (which template uses it). Out-of-catalog requests SHALL be flagged in the section's "Extension path" subsection as requiring a new OpenSpec change.

#### Scenario: Catalog present in DESIGN.md
- **WHEN** an operator or auditor reads DESIGN.md §Iconography
- **THEN** all 10 catalog names SHALL appear in the section body
- **AND** each icon SHALL have a documented use-site (template + selector)

#### Scenario: Extension path documented
- **WHEN** an owner wants to add a new icon
- **THEN** DESIGN.md §Iconography SHALL instruct them to open a new OpenSpec change (not edit F12 in place)
- **AND** the catalog boundary SHALL be explicit (not "as needed")
