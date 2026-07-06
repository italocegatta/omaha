## Why

`src/omaha/templates/patrimonio.html` is 2186 lines and 7 distinct visual
sections (actions toolbar, portfolio header, distribution, per-class article,
empty-state, onboarding, add-asset modal). The template grew organically
through F01 / F02 / F05 / F06 / F07 and is now the largest file under
`src/omaha/`. Reading or editing any one section forces the whole file into
context. Extending the established `_rebalance_*.html` partials pattern
into patrimonio breaks the file into navigable, testable units without
changing the rendered DOM, behaviour, or any spec.

## What Changes

- Extract `src/omaha/templates/patrimonio.html` into 7 partials under
  `src/omaha/templates/_patrimonio_*.html` matching the existing
  underscore-prefix convention (sibling to `_rebalance_*`).
- Each partial renders one of the existing sections verbatim — no
  markup, attribute, testid, or class changes.
- `patrimonio.html` becomes a thin shell that `{% include %}`s the
  partials in the same order they appear today.
- No behavioural, visual, or testid change: every existing
  `data-testid` remains in the same rendered HTML tree at the same
  parent.
- No route, model, seed, migration, or test fixture change.

## Capabilities

### New Capabilities

- `patrimonio-template-partials`: internal template-layout capability
  describing how `src/omaha/templates/patrimonio.html` is split into
  partials. Mirrors the precedent set by `csv-seed-internals` (R02
  archive) — captures the file-level organisation that keeps future
  contributors from re-inflating the shell. No rendered-DOM change.

### Modified Capabilities

<!-- None. Every requirement across all existing specs continues to
     bind to the same rendered DOM. The portfolio-header spec still
     binds to `data-testid="patrimonio-portfolio-header"`; the
     class-section spec still binds to `data-testid="class-summary-row"`
     and the asset-table testids; cross-profile-sharing still binds to
     the family-mode branches; etc. No requirement text changes. -->

## Impact

- `src/omaha/templates/patrimonio.html` (rewritten as shell)
- `src/omaha/templates/_patrimonio_actions.html` (new — lines 59-81)
- `src/omaha/templates/_patrimonio_portfolio_header.html` (new —
  lines 82-110)
- `src/omaha/templates/_patrimonio_distribution.html` (new —
  lines 111-149)
- `src/omaha/templates/_patrimonio_class_section.html` (new —
  lines 150-468; the largest, one article per class)
- `src/omaha/templates/_patrimonio_empty_states.html` (new —
  lines 469-510; both inline + onboarding)
- `src/omaha/templates/_patrimonio_add_asset_modal.html` (new —
  lines 511-end)
- Tests: zero new tests. Existing tests (e2e selector inventory,
  BDD `class_crud.feature`, integration `test_patrimonio_route`)
  continue to assert against the rendered DOM, which is byte-equivalent.
  No `data-testid` moves; no parent re-nesting; no class swap.
