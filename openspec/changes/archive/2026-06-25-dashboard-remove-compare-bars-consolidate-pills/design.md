## Context

The dashboard renders each asset class as a card with three layers
of competing information: (1) the class card header, with a
vertical stack of Alvo/Atual in the top-right and a small × delete
button; (2) the asset-table group header row inside the table, a
duplicate of class name + Alvo + Atual + per-class delta badge;
(3) horizontal progress bars — one for the class
(target-vs-current overlay) and one per asset row (current % of
class). The duplication and the bars compete for visual attention
without adding signal: the Alvo/Atual numbers already convey the
same information the bars encode.

The current `.class-section-delete-btn` is 22×22 px with transparent
background and `color: var(--muted)` — only red on hover. A
destructive action that pages reload should be scannable from a
glance, not require hovering to discover.

The `classDeltaMessage` getter (`dashboard.html:945`) hides the
Sobra/Falta badge unless the user is mid-edit on an asset. This
makes the badge effectively invisible in steady state, so the
per-class delta is only surfaced through the global sticky alert
card at the top of the page.

## Goals / Non-Goals

**Goals:**
- Single source of truth for class name, Alvo, Atual, and per-class
  delta — the class card header.
- Drop the class-level compare bar and per-asset progress bars
  (information is already in the pills).
- Drop the duplicate asset-table group header row.
- Make the X delete action scannable in steady state (red border
  visible without hover).
- Surface the per-class Sobra/Falta pill in the header whenever the
  delta exceeds tolerance, regardless of editing state.
- Keep all existing test-ids that BDD steps depend on
  (`class-target-pct-view`, etc.) so step definitions don't need
  to change.

**Non-Goals:**
- No backend changes — no model, route, validator, or migration.
- No new API endpoints, no new server-rendered fields.
- No redesign of the asset-table column layout, sort behaviour, or
  inline edit semantics — only the per-row progress-bar `<tr>` is
  removed.
- No changes to the chevron (kept per design decision — collapsed
  state is dead code but the icon stays).
- No responsive layout work — the existing `@media (max-width: 480px)`
  rules remain authoritative; the new header pills wrap naturally
  via `flex-wrap` if needed (no new breakpoints introduced).

## Decisions

### Decision 1 — Pills in the header replace both Alvo/Atual vertical stack and the asset-group-header row

Three pills inline between the class name and the X button:

- **Alvo pill** (`pct-target-pill`, dashed border, neutral fill):
  reuses the existing inline-edit `commitEditClassPct` flow.
  Dashed border signals "click to edit". `data-testid="class-target-pct-view"`
  is preserved so BDD steps and `target_steps.py:36` continue to work.
- **Atual pill** (`pct-current-pill`, status-coloured): green when
  `|classCurrentPct - classTargetPct| <= 0.01` (within tolerance),
  red when off. `data-testid="class-current-pct"` is preserved.
- **Delta pill** (`pct-delta-pill`): shows "Sobra X%" or "Falta X%"
  when `|classDelta| > 0.01`. Red background for "Falta"
  (under-allocated), green for "Sobra" (over-allocated) — matches
  the existing semantic colouring in
  `app.css:1244-1252` (`.class-delta-badge--short/--long`).
  `data-testid="class-delta-badge"` is preserved so the existing
  e2e selector and the per-class pill contract from
  `asset-allocation-alerts/spec.md` continue to work.

Why pills, not stacked stats: the vertical `.class-section-stats`
column on the right was the source of the duplication problem
(both header and group header showed the same numbers, in slightly
different visual treatments — header integer-rounded, group header
2-decimal). Inline pills force a single horizontal layout, which
makes duplication impossible and matches the user's "consolidate"
intent.

### Decision 2 — `classCurrentStatus` is a new Alpine getter on `classSection`

Add `get classCurrentStatus()` returning `'ok'` or `'off'` based on
the same tolerance the `classDelta` getter uses
(`SUM_TOLERANCE = 0.01` in `omaha.validators`). The Atual pill binds
`:class="'pct-current-pill--' + classCurrentStatus"`.

Why a getter, not a stored field: `classCurrentPct` updates from
PATCH responses and the `classSum` store already reactively
recomputes on every asset edit. A getter re-evaluates on every
Alpine tick that reads it, so no manual `set()` calls are needed.

### Decision 3 — Drop the `editingAssetId === null` guard in `classDeltaMessage`

Current code at `dashboard.html:950`:

```js
if (this.editingAssetId === null) return '';
```

This guard hides the Sobra/Falta badge in steady state. The user
explicitly wants the delta pill in the header to be a permanent
fixture — visible whenever the per-class sum is off, not only
during inline edits. Removing the guard keeps `Math.abs(delta) <= 0.01`
as the only condition, which already matches the spec contract in
`asset-allocation-alerts/spec.md:138-152`.

### Decision 4 — Per-row progress-bar `<tr>` removed entirely (not just CSS-hidden)

The `<tr>` at `dashboard.html:300-306` wraps each asset row with
an empty progress bar inside `colspan="8"`. Removing the entire
`<tr>` keeps the asset table rows tight (one `<tr>` per asset
instead of two). The CSS rules `.asset-progress-bar`,
`.asset-progress-fill`, `@keyframes fill-bar`, `@keyframes fill-asset`,
and the stagger via `--i` are all dead code after this change.

Why not just CSS-hide: CSS-hide would leave the markup in place and
break the "single source of truth" goal — the next refactor would
need to read this code again. Removal is one-shot.

### Decision 5 — `.class-section-delete-btn` becomes always-visible red

Current style (`app.css:1471-1495`): 22×22 px, `color: var(--muted)`,
`background: transparent`, `border: 1px solid transparent`, hover
flips to red. New style: same dimensions, `color: var(--negative)`
always, `border: 1px solid color-mix(in srgb, var(--negative) 30%, transparent)`,
`background: color-mix(in srgb, var(--negative) 6%, var(--surface))`.
Hover darkens the border and background.

Why not bigger (24-26 px): the surrounding header is already tight
(4 pills + chevron + swatch + name + X). Growing the X forces the
header height up, which would misalign all six class cards on the
page. Red border alone gives the scannability without the size cost.

### Decision 6 — `class-section-header` keeps chevron + name + swatch + pills + X

Chevron stays. Name + colour swatch stay. Three pills sit between
the class name and the X. Layout uses `flex` with `gap: 0.6rem`
(inherited from current `app.css:807`), `align-items: center`,
`flex-wrap: wrap` so the pills wrap to a second line on narrow
viewports instead of overflowing.

Why not remove chevron: out of scope. The user explicitly chose
"Manter como está". Even though `isOpen` is hardcoded `true`, the
chevron is part of the visual identity and the asset-table-view
spec (`dashboard-inline-editing/spec.md:113-164`) defines it.

## Risks / Trade-offs

- **Three signals of class deviation** (Atual pill colour + delta
  pill + sticky alert card) → user accepted the redundancy
  explicitly as a layered signal (status light + quantification +
  portfolio list). Mitigation: keep the visual hierarchy clear
  — delta pill uses fill, Atual pill uses border only, sticky card
  uses card chrome. None competes for the same eye path.
- **Header density** (chevron + swatch + name + 3 pills + X = 7
  elements in one row) → on 1280px viewport with 6 classes seeded
  (the default Italo state), header height should stay around
  48-56 px. Mitigation: `flex-wrap: wrap` kicks in below 480px,
  pushing pills to a second line. The 480px media query in
  `app.css:1256` keeps the dashboard responsive.
- **Test-id preservation risk** for `class-target-pct-view` and
  `class-current-pct` — BDD step files reference these selectors.
  Mitigation: keep both test-ids on the new pill elements; only
  the visual treatment changes.
- **E2E selectors tied to widths of removed bars** — selectors at
  `tests/e2e/test_user_journey_rebalance.py:221-236,289-297`
  assert numeric widths of the compare-bar and progress bar. They
  cannot be inverted to "not visible"; they must be removed along
  with the bar markup. Mitigation: drop those scenarios from the
  S05 polish journey and add new ones asserting pill presence
  and status colour.
- **Animation `--i` stagger on asset rows** (`app.css:916-922`)
  currently drives the progress-bar fill stagger. With the
  progress bar gone, `--i` becomes dead — no other style uses
  it. Mitigation: drop the `--i` inline style from
  `dashboard.html:215` along with the `<tr>` removal.

## Migration Plan

No data migration. No API change. The change is a pure UI swap.

Rollout:
1. Apply the template + CSS changes behind no feature flag
   (the change is mechanical — same data, same route, same DB).
2. Run `uv run task check` (lint + unit tests) before manual
   browser test.
3. Run `uv run task test-integration` to validate the
   `test_pages_routes.py` assertions flip cleanly.
4. Run `uv run task test-e2e` to validate the user journey.
5. Run `uv run task test-bdd` to validate the BDD step files.
6. Run `uv run task db-reset` to bring the dashboard back to the
   populated default state (Italo: 6 classes + 48 assets +
   47 positions), then refresh `http://192.168.1.6:8000` and
   confirm the new header layout, missing bars, and visible red
   X render as expected.

Rollback: git revert the commit. No database state to back out.

## Open Questions

None — all four design decisions (Atual pill treatment, Alvo
editability, delta pill location, chevron disposition) were
resolved with the user during the explore phase.