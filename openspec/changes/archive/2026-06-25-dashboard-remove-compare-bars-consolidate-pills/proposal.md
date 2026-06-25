## Why

The dashboard's per-class section duplicates Alvo/Atual across two
places (the class card header and the asset-table group header row)
and renders two progress bars that compete with the Alvo/Atual pills
for visual attention. Operators read the same numbers twice and parse
two horizontal bars that carry the same information. The X delete
button blends in (transparent background, muted color) — a destructive
action that needs to be scannable. Consolidate to a single source of
truth per metric, drop the redundant bars, and lift the delete action.

## What Changes

- **Remove** `<div class="compare-bar">` (class-level target/current
  horizontal bars) and `<div class="asset-progress-bar">` (per-row
  horizontal bar) from the class section. The Alvo/Atual numbers in
  the header already carry this information; the bars are
  redundant visual noise.
- **Remove** `<tr class="asset-group-header">` (the duplicate
  class summary row inside the asset table). The class section
  header is the single source of truth for class name, Alvo, Atual,
  and per-class delta.
- **Add** inline pills to the class section header for the three
  class metrics: a dashed-bordered Alvo pill (click → inline editor,
  unchanged), a status-coloured Atual pill (green when within
  tolerance of target, red when off), and a delta pill
  ("Sobra X%" / "Falta X%", always shown when off). All three pills
  sit between the class name and the X button.
- **Rewrite** `.class-section-delete-btn` so the X is always visible
  in red (var(--negative)) with a visible border, not just on hover.
  The destructive action needs to be scannable.
- **Unlock** the `classDeltaMessage` getter so the delta pill shows
  whenever |delta| > 0.01, not only while the user is mid-edit on an
  asset (the current "only during inline edit" guard at
  `dashboard.html:950` is dropped).

## Capabilities

### New Capabilities
None — this change modifies existing UI surface area only.

### Modified Capabilities
- `dashboard-inline-editing`: rewrite the "class section header"
  requirements to specify the inline-pill layout, drop the
  "asset-group-header row" requirement, drop the "per-class compare
  bar" and "per-asset progress bar" references from "seções
  colapsáveis", update the "Column widths" requirement to reflect
  the now-denser asset-table rows (no per-row progress bar cells).
- `asset-allocation-alerts`: relocate the "Per-class alert badge on
  group header" requirement to "Per-class delta pill in class
  section header". The pill uses the same severity tier table
  (`asset-allocation-alerts/spec.md:77-108`) and the same
  `SUM_TOLERANCE` contract, but lives in the class card header
  instead of inside the asset table. The "reactivity" requirement
  stays identical.

## Impact

- **Template**: `src/omaha/templates/dashboard.html` lines 107-142
  (header), 140 (delta badge), 170-177 (compare-bar), 199-211
  (group header), 300-306 (progress bar), 950 (delta guard).
- **Styles**: `src/omaha/static/app.css` — remove `.compare-bar*`,
  `.asset-progress-bar*`, `@keyframes fill-bar/fill-asset`, and the
  `:nth-of-type(N) .compare-bar-current-fill` color cycling rules
  (lines 79-105). Add `.pct-target-pill`, `.pct-current-pill--ok/--off`,
  `.pct-delta-pill--short/--long`. Rewrite `.class-section-delete-btn`
  with always-visible red border.
- **Alpine logic** (`classSection` factory): add `classCurrentStatus`
  getter for the Atual pill colour binding.
- **Tests** (all under `tests/`):
  - `test_pages_routes.py:343-345,353,369,385-386` — invert
    `assert ... in body` for the removed elements to
    `assert ... not in body`. Add positive assertions for the new
    pills.
  - `e2e/test_user_journey_rebalance.py:69-78,135,192,221-236,
    260,289-297` — remove compare-bar / asset-progress-bar
    selectors and the widths assertions.
  - `e2e/test_asset_table.py:39` — remove `asset_group_header_alert`
    selector and its assertions.
  - `e2e/test_inline_edit.py:81` — update `class_delta_badge`
    selector to the new pill test-id.
  - `bdd/step_defs/target_steps.py:36`,
    `bdd/step_defs/common_steps.py:178,182` — keep using
    `class-target-pct-view` (the pill reuses the same test-id).
- **BDD scenarios** under `tests/bdd/`: no scenario rewrite needed —
  the test-ids the BDD steps reference stay valid (the Alvo pill
  keeps `data-testid="class-target-pct-view"`).