# patrimonio-template-partials

## Purpose

`src/omaha/templates/patrimonio.html` is the body of the `/patrimonio`
route (post-F02 rename from `dashboard.html`). After F02/F05/F06/F07
absorbed the tab nav, dark surface, family-mode branches, and
Família-sentinel hints, the file grew past 2000 lines — the largest
in `src/omaha/templates/`. Reading or editing any one visual section
forced the whole file into context.

This capability captures the **internal file layout** introduced by
R04: the template is split into six `_patrimonio_*.html` partials
sibling to the existing `_rebalance_*.html` pattern, plus a thin
shell that composes them via plain `{% include %}`. No rendered DOM
or behavior changes; every existing `data-testid` stays at the same
parent in the rendered output. The public contract bound by other
specs (`patrimonio-portfolio-header`, `class-section-totals`,
`cross-profile-sharing`, `asset-trade-flags`, `dashboard-inline-editing`,
`import-modal`, `import-modal-class-binding`,
`import-class-color-via-css-class`) is unchanged.

The split is **internal-only**. Tests, BDD steps, and e2e selectors
that bind to a `data-testid` see the same rendered HTML — only the
file that holds the markup has changed. The capability exists to
document the file-level organisation so future contributors don't
re-inflate the shell or duplicate the section markup across two
files.

## Requirements

### Requirement: Patrimonio template is organised as a shell plus partials

`src/omaha/templates/patrimonio.html` SHALL be organised as a thin
shell that composes the page from partials under
`src/omaha/templates/_patrimonio_*.html`. The shell renders only the
`<div class="patrimonio-page">` wrapper, the read-only note (when
`view == "family"`), the `<section class="class-summary">` and
`<section class="dashboard-distribution">` wrapper sections, and the
`{% include %}` directives that compose the page sections in visual
order. No section markup lives in the shell.

#### Scenario: Shell size after partialization

- **WHEN** a contributor reads `src/omaha/templates/patrimonio.html`
- **THEN** the file contains the `<div class="patrimonio-page">`
  element, the read-only conditional, the `<section
  class="class-summary">` + `<section class="dashboard-distribution">`
  wrappers, and 6 `{% include %}` directives (one per partial)
- **AND** the file size is well under 100 lines (vs the ~2186-line
  pre-R04 monolith)

#### Scenario: All section testids remain on the same rendered parent

- **WHEN** a contributor searches for any of the following
  `data-testid` values across `src/omaha/templates/`
- **THEN** each one appears in exactly one `_patrimonio_*.html`
  partial (or in the shell, for the three wrapper testids
  `patrimonio-read-only-note`, `class-summary`,
  `dashboard-distribution`) and never appears as a NEW binding at a
  different parent in the rendered HTML:
  `patrimonio-actions`, `patrimonio-portfolio-header`,
  `dashboard-distribution`, `class-summary-row`, `asset-table`,
  `empty-assets`, `empty-state-onboarding`,
  `add-asset-modal-overlay`

### Requirement: Each partial renders one visual section verbatim

Each `_patrimonio_*.html` partial SHALL render one top-level visual
section of the page (the same section it replaced in the pre-R04
template). The partial uses plain `{% include %}` (no `{% with %}`
arguments, no Jinja macros) and reads the rendering context that the
shell already populated. No partial introduces a new `data-testid`,
class, or Alpine binding that the pre-R04 template did not already
have.

#### Scenario: Data-testid count preserved across refactor

- **WHEN** `grep -c 'data-testid=' src/omaha/templates/_patrimonio_*.html`
  runs after R04 lands
- **THEN** the sum across all 6 partials (119 occurrences post-R04)
  plus the 3 wrapper testids in the shell equals the
  `grep -c 'data-testid=' src/omaha/templates/patrimonio.html` count
  from the pre-R04 template (122 occurrences)

#### Scenario: Alpine bindings preserved per section

- **WHEN** `grep 'x-data=' src/omaha/templates/_patrimonio_*.html`
  runs after R04 lands
- **THEN** every `x-data` declaration that was in the pre-R04
  template appears in exactly one partial, with the same component
  name and same element scope

#### Scenario: Partial uses plain include, no arguments

- **WHEN** a contributor reads each `_patrimonio_*.html` partial
- **THEN** the partial does not declare `{% with %}` or `{% macro %}`
  blocks; it does not take parameters; it relies entirely on the
  rendering context that the shell already populated

### Requirement: Partial names follow the underscore-prefix convention

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

- **WHEN** `grep -l '_patrimonio_' src/omaha/templates/` runs
- **THEN** every `_patrimonio_*.html` file is referenced by exactly
  one `{% include %}` in `patrimonio.html`
- **AND** no `_patrimonio_*.html` file is referenced from any other
  template (`rebalance.html`, `rentabilidade.html`, `proventos.html`)
  unless a future slice adds that cross-reference explicitly

### Requirement: Rendered HTML byte-equivalence

The system SHALL render `GET /patrimonio` (and its `?view=household`
and `?profile=ana` variants) byte-equivalent to the pre-R04 rendered
output for the same DB state and auth context, modulo whitespace
inside Jinja control tags.

#### Scenario: GET /patrimonio byte-equivalence

- **WHEN** a contributor captures the rendered HTML of
  `GET /patrimonio` before R04 (saved to
  `.temp_assets/r04_pre_render.html`)
- **AND** R04 lands
- **AND** the contributor captures the rendered HTML of
  `GET /patrimonio` again (saved to
  `.temp_assets/r04_post_render.html`)
- **THEN** `diff <(grep -v '^[[:space:]]*$' <pre>) <(grep -v
  '^[[:space:]]*$' <post>)` is empty (whitespace-only differences
  inside Jinja control tags are acceptable; non-blank-line content
  differences are not)

#### Scenario: GET /patrimonio?view=household byte-equivalence

- **WHEN** the same byte-equivalence check runs against
  `GET /patrimonio?view=household` (saved to
  `.temp_assets/r04_pre_render_family.html` /
  `r04_post_render_family.html`)
- **THEN** the F06 collapse-by-name + target_pct suppression paths
  still resolve correctly through the new partials
- **AND** the non-blank-line diff is empty

#### Scenario: Cross-profile rendering byte-equivalence

- **WHEN** the same byte-equivalence check runs against
  `GET /patrimonio` for Ana's session (saved to
  `.temp_assets/r04_pre_render_ana.html` /
  `r04_post_render_ana.html`)
- **THEN** the cross-profile rendering path resolves correctly
  through the new partials
- **AND** the non-blank-line diff is empty
