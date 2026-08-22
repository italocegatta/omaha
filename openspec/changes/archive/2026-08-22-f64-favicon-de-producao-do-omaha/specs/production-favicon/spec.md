## ADDED Requirements

### Requirement: Production favicon asset

The system SHALL provide one self-contained production favicon at
`src/omaha/static/favicon.svg`. The SVG SHALL use a `viewBox="0 0 32 32"`
coordinate system, an opaque dark background derived from DESIGN.md `--bg`,
and a teal geometric “O” formed by aligned ledger-like rails derived from
DESIGN.md `--accent`. The asset SHALL contain no text, emoji, animation,
gradient, external reference, or alternate candidate mark. The encoded mark
and background SHALL provide at least 4.5:1 contrast.

#### Scenario: Favicon is legible at 16px

- **WHEN** browser rasterizes `favicon.svg` into a 16px by 16px favicon slot
- **THEN** the result shows a distinct teal geometric “O” against an opaque
  dark background
- **AND** the mark remains identifiable without text or page context

#### Scenario: Favicon preserves geometry at 32px

- **WHEN** browser rasterizes `favicon.svg` at 32px by 32px
- **THEN** the ledger-rail “O” remains continuous, aligned, and recognizable
- **AND** no clipping or external resource is required

#### Scenario: Favicon uses approved dark palette and contrast

- **WHEN** an implementation inspects the SVG's encoded background and mark
  colors
- **THEN** background maps to DESIGN.md `--bg` intent and mark maps to
  DESIGN.md `--accent` teal intent
- **AND** the pair measures at least 4.5:1 contrast

### Requirement: Shared browser favicon discovery

The system SHALL emit exactly one shared favicon discovery link from the
`<head>` of `src/omaha/templates/base.html` with
`rel="icon"`, `type="image/svg+xml"`, and
`href="/static/favicon.svg"`. Pages that extend `base.html` SHALL inherit the
same link; page-specific templates SHALL NOT introduce alternate favicon
links.

#### Scenario: Browser discovers favicon from shared head

- **WHEN** browser loads any page rendered through `base.html`
- **THEN** document head contains exactly one `rel="icon"` link for
  `/static/favicon.svg`
- **AND** browser can request that URL successfully as an SVG static asset

#### Scenario: Shared link covers login and application pages

- **WHEN** browser loads `/login` and an authenticated page that extends
  `base.html`
- **THEN** both documents expose the same favicon link
- **AND** no page-specific head block changes favicon identity

#### Scenario: Written direction gates Apply

- **WHEN** F64 is handed from proposal to Apply
- **THEN** owner-approved written direction “O” geométrico com trilhos de
  ledger, teal sobre fundo escuro, próprio e legível em 16px is present
- **AND** no mock, static preview, browser preview example, preview server, or
  preview file is required before Apply
- **AND** Apply remains blocked when written direction approval is absent

#### Scenario: Browser rendering is mandatory during Apply

- **WHEN** focused validation runs during Apply
- **THEN** browser rendering at 16px and 32px is executed and recorded
- **AND** browser discovery and actual raster output remain part of acceptance

#### Scenario: Owner validates rendering after review before finalize

- **WHEN** F64 has review approval and is ready for finalization
- **THEN** owner validates actual browser rendering at 16px and 32px against
  the approved written direction
- **AND** finalize remains blocked when either size lacks owner validation
