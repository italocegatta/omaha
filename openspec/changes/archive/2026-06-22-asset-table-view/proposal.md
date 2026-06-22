## Why

The dashboard currently renders assets as nested collapsible cards (one per class)
with a 4-cell percentage grid per asset. Comparing assets across classes requires
eye-jumping between cards, the "alvo % total" column is read-only (derived), and
edits are blocked with a 422 whenever the per-class sum drifts off 100%. The user
has to clear the rejection, re-edit, and try again — there is no guided path to
converge on 100%. The change replaces the card layout with a sortable table
grouped by class, makes both `alvo % classe` and `alvo % total` editable, removes
the rejection gate so every edit is accepted, and surfaces the deviation through
a sticky alert card + per-class inline badges with severity coloring.

## What Changes

- **Table layout replaces per-class card list.** Assets render as `<table>` rows
  with one row per asset, grouped by class via a colored `<tr class="class-group-header">`
  band that carries the class name, target %, current %, and inline alert badge.
  Same data as today (name, class, qty, current value, alvo% classe, atual% classe,
  alvo% total, atual% total).
- **All columns sortable** via click on `<th>`. Two-state toggle per column
  (asc/desc). Default sort: class asc, alvo% classe asc. No persistence across
  reloads (in-memory only).
- **Both `alvo % classe` and `alvo % total` are editable inline.** Editing
  `alvo % classe` derives `alvo % total` server-side (no math change vs today).
  Editing `alvo % total` back-solves `alvo % classe` against the class's
  current `target_pct` (classe âncora) and shows a confirm hint explaining the
  effect is contained to that asset's position within the class.
- **Per-class sum-to-100 gate is removed on `PATCH /api/assets/{id}` and
  `POST /api/assets`.** Edits always commit. The `validate_target_pct_sum`
  helper stays as the formatter for the alert message but no longer blocks
  writes.
- **Class sections default to expanded and stay expanded after any edit.**
  Removes the D016 default-closed rule. `isOpen` is forced to `true` after a
  successful PATCH on any asset or class within that section.
- **Sticky alert card at the top of the "Ativos" section** shows the
  portfolio-level delta ("Carteira: 80% — Falta 20%") and lists every class
  whose per-asset sum is off 100%. Severity is colored: green when the
  delta is within 0.01 of 100 (and 0 deviations), yellow when
  `0.01 < |delta| ≤ 5`, red when `|delta| > 5`. Per-class `<tr class="class-group-header">`
  carries an inline badge with the same severity coloring.
- **Alert card persists while any deviation is present.** Disappears when
  all classes and the portfolio sum to 100%. No popups.
- **`+ Ativo` add form moves from per-class inline form to a single
  dashboard-level "+ Ativo" button that opens a modal** (or a top-of-table
  form). One place to add, not N. **BREAKING** for the per-class
  `data-testid="dashboard-add-asset-btn"` / `dashboard-add-asset-form` and
  the per-class confirm dialog wiring.

## Capabilities

### New Capabilities

- `asset-allocation-alerts`: persistent sticky alert card + per-class inline
  badges reporting per-asset sum deviation and portfolio-level deviation,
  with green/yellow/red severity tiers.

### Modified Capabilities

- `dashboard-inline-editing`: card layout → table layout; default expanded
  and stay expanded; `alvo % total` becomes editable (back-solves
  `alvo % classe` against class anchor); per-class sum gate removed from
  `PATCH /api/assets/{id}` and `POST /api/assets`; add-asset form moves to
  a single dashboard-level control; alert surface reuses the existing
  `classSum` store extended to per-class sums.

## Impact

- **Template**: `src/omaha/templates/dashboard.html` — replace the
  `.dashboard-asset-list` card body with a `<table class="asset-table">`;
  expand the `classSection` Alpine component to own per-class sum
  state, sort state, and the per-class delta badge; replace the
  per-class `+ Ativo` form with a single dashboard-level add control.
- **Route**: `src/omaha/routes/assets.py` — drop the
  `validate_target_pct_sum` call on `POST /api/assets` (line 294) and
  `PATCH /api/assets/{id}` (line 390). Per-row range check
  (0 ≤ pct ≤ 100) stays.
- **Validator**: `src/omaha/validators.py` — `validate_target_pct_sum`
  stays as a pure function; the unit tests in
  `tests/test_t01_asset_target.py` are unaffected.
- **Tests broken by gate removal** (need to invert from 422 to 200):
  - `tests/test_t99_assets_patch.py::test_patch_asset_invalid_sum_returns_422`
    and any sibling that pins the rejection
  - E2E selectors in `tests/e2e/test_s01_inline_edit.py` that assert
    the save button is disabled when off-100
- **CSS**: `src/omaha/static/app.css` — new rules for `.asset-table`,
  `.asset-table th`, `.asset-group-header`, `.asset-allocation-alert`,
  severity colors (`--alert-ok`, `--alert-warn`, `--alert-danger`).
- **Testids dropped** (per-class add-form):
  `data-testid="dashboard-add-asset-btn"`,
  `data-testid="dashboard-add-asset-form"`. Replaced by a single
  dashboard-level `data-testid="dashboard-add-asset-open"` and a modal
  form with `data-testid="dashboard-add-asset-modal"`.
- **Testids kept**: all `data-testid="asset-target-pct-class*"`,
  `data-testid="asset-current-pct-class"`, `data-testid="asset-target-pct-total"`,
  `data-testid="asset-current-pct-total"`, `data-testid="asset-current-value"`,
  `data-testid="asset-row-name"`, `data-testid="dashboard-asset-row"`,
  `data-testid="class-delta-badge"`, `data-testid="class-summary-total"`,
  `data-testid="class-color-swatch"`, `data-testid="class-section-name"`.
