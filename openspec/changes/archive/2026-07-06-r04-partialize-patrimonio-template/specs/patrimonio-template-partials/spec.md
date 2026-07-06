## ADDED Requirements

### Requirement: Patrimonio template SHALL be organised as a shell plus partials
`src/omaha/templates/patrimonio.html` SHALL be organised as a thin
shell that composes the page from partials under
`src/omaha/templates/_patrimonio_*.html`. The shell renders only the
`<main>` wrapper, the read-only note (when `view == "family"`), and
the `{% include %}` directives that compose the page sections in
visual order. No section markup lives in the shell.

#### Scenario: Shell size after partialization
- **WHEN** a contributor reads `src/omaha/templates/patrimonio.html`
- **THEN** the file contains the `<main>` element, the read-only
  conditional, and 6 `{% include %}` directives (one per partial)
- **AND** the file size is under 50 lines

#### Scenario: All sections moved to partials
- **WHEN** a contributor searches for any of the following
  `data-testid` values across `src/omaha/templates/`
- **THEN** each one appears in exactly one
  `_patrimonio_*.html` partial and does NOT appear in
  `patrimonio.html` directly:
  `patrimonio-actions`, `patrimonio-portfolio-header`,
  `dashboard-distribution`, `class-summary-row`, `asset-table`,
  `empty-assets`, `empty-state-onboarding`,
  `add-asset-modal-overlay`

### Requirement: Each partial SHALL render one visual section verbatim
Each `_patrimonio_*.html` partial SHALL render one top-level visual
section of the page (the same section it replaced in the pre-R04
template). The partial uses plain `{% include %}` (no `{% with %}`
arguments, no Jinja macros) and reads the rendering context that the
shell already populated. No partial introduces a new `data-testid`,
class, or Alpine binding that the pre-R04 template did not already
have.

#### Scenario: data-testid count preserved across refactor
- **WHEN** `rg -c 'data-testid=' src/omaha/templates/_patrimonio_*.html`
  runs after R04 lands
- **THEN** the sum across all 6 partials equals the
  `rg -c 'data-testid=' src/omaha/templates/patrimonio.html` count
  from the pre-R04 template (captured in
  `openspec/changes/r04-partialize-patrimonio-template/tasks.md`
  task 4.5)

#### Scenario: Alpine bindings preserved per section
- **WHEN** `rg 'x-data=' src/omaha/templates/_patrimonio_*.html` runs
  after R04 lands
- **THEN** every `x-data` declaration that was in the pre-R04
  template appears in exactly one partial, with the same component
  name and same element scope

#### Scenario: Partial uses plain include, no arguments
- **WHEN** a contributor reads each `_patrimonio_*.html` partial
- **THEN** the partial does not declare `{% with %}` or `{% macro %}`
  blocks; it does not take parameters; it relies entirely on the
  rendering context that the shell already populated

### Requirement: Partial names SHALL follow the underscore-prefix convention
Each partial name SHALL start with `_patrimonio_` and end with a
section-descriptor that matches the section it renders. The
underscore prefix signals "include-only, not rendered directly". The
`patrimonio_` middle namespacing prevents collision with the existing
`_rebalance_*.html` partials in Jinja's `FileSystemLoader`.

#### Scenario: Naming convention matches the rebalance precedent
- **WHEN** a contributor lists `src/omaha/templates/_*.html`
- **THEN** the listing includes both `_rebalance_*.html` (existing
  precedent) and `_patrimonio_*.html` (new partials)
- **AND** every `_patrimonio_*.html` file matches the pattern
  `_patrimonio_<descriptor>.html` where `<descriptor>` is one of:
  `actions`, `portfolio_header`, `distribution`, `class_section`,
  `empty_states`, `add_asset_modal`

#### Scenario: No orphan partials after refactor
- **WHEN** `rg -l '_patrimonio_' src/omaha/templates/` runs
- **THEN** every `_patrimonio_*.html` file is referenced by exactly
  one `{% include %}` in `patrimonio.html`
- **AND** no `_patrimonio_*.html` file is referenced from any other
  template (`rebalance.html`, `rentabilidade.html`, `proventos.html`)
  unless a future slice adds that cross-reference explicitly

### Requirement: Rendered HTML byte-equivalence
The system SHALL render `GET /patrimonio` (and its `?view=family` and
`?profile=ana` variants) byte-equivalent to the pre-R04 rendered
output for the same DB state and auth context, modulo whitespace
inside Jinja control tags.

#### Scenario: GET /patrimonio byte-equivalence
- **WHEN** a contributor captures the rendered HTML of
  `GET /patrimonio` before R04 (saved to
  `.temp_assets/r04_pre_render.html`)
- **AND** R04 lands
- **AND** the contributor captures the rendered HTML of
  `GET /patrimonio` again
- **THEN** `diff` between the two captures is empty (whitespace-only
  differences inside Jinja control tags are acceptable; visible-DOM
  differences are not)

#### Scenario: GET /patrimonio?view=family byte-equivalence
- **WHEN** the same byte-equivalence check runs against
  `GET /patrimonio?view=family` (saved to
  `.temp_assets/r04_pre_render_family.html`)
- **THEN** the F06 collapse-by-name + target_pct suppression paths
  still resolve correctly through the new partials
- **AND** the diff is empty

#### Scenario: Cross-profile rendering byte-equivalence
- **WHEN** the same byte-equivalence check runs against
  `GET /patrimonio?profile=ana` (saved to
  `.temp_assets/r04_pre_render_ana.html`)
- **THEN** the cross-profile rendering path resolves correctly through
  the new partials
- **AND** the diff is empty
