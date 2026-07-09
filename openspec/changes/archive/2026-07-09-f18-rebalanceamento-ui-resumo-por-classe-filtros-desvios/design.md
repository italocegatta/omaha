## Context

The rebalance page (`/rebalanceamento`) currently renders 6 metric cards in a
1×6 grid, a 4-column category summary table, and an 8-column asset plan table.
The operator's primary question — "which classes are off-target and by how
much?" — is not answered at a glance. The aporte input occupies full width. The
asset table has no filtering or deviation columns.

The wire format (`RebalancePlanResponse`) exposes raw monetary values but no
percentage-of-portfolio or per-asset deviation metrics, forcing the UI to
either compute them client-side (fragile) or omit them.

## Goals / Non-Goals

**Goals:**
- Operator sees class-level deviation status in < 2 seconds (color = ok/not-ok)
- Operator can filter the asset table by class and action type
- Operator sees per-asset deviation (R$ and %) without mental math
- Threshold inputs (desvio mínimo R$ and %) are editable on-page and will
  serve as future optimizer constraints
- Wire format carries computed % and deviation fields so UI is a pure renderer

**Non-Goals:**
- Changing the solver logic or optimizer (F18 is UI + schema only)
- Persisting threshold values (session-only for now)
- Adding new API endpoints (existing POST /rebalanceamento and POST /api/rebalance suffice)
- Mobile-first layout (desktop primary, responsive is stretch goal)

## Decisions

### D1: Extend wire format vs. compute client-side

**Decision:** Add 5 computed fields to the Pydantic schemas (`target_pct`,
`current_pct`, `deviation_pct` on category rows; `deviation_value`,
`deviation_pct` on asset rows).

**Rationale:** Client-side computation requires the UI to know total portfolio
value and sum of targets — fragile if the solver changes its aggregation.
Server-side computation in `glue.py` is deterministic and testable.

**Alternative considered:** Compute in Alpine from existing `current_value` and
`target_value` fields. Rejected: requires passing total portfolio value
separately, and % deviation from class target requires class-level aggregation
that the wire doesn't currently expose.

### D2: Filter implementation — Alpine multi-select vs. server-side

**Decision:** Alpine-only filtering with reactive `selectedClasses`,
`selectedActions`, `searchTerm` state. No server round-trip.

**Rationale:** The asset table has at most ~200 rows (family portfolio). Alpine
can filter/sort that in < 1ms. Server-side filtering would require a new API
endpoint or query params, adding complexity for no UX benefit.

### D3: Threshold inputs — form fields vs. separate state

**Decision:** Threshold inputs (`thresholdAbs`, `thresholdPct`) are Alpine
reactive state, NOT form inputs. They don't trigger a POST — they only affect
visual color-coding client-side. The Rebalancear button remains the only form
submit.

**Rationale:** Thresholds are a visual aid, not an optimizer parameter yet.
Making them form inputs would require server-side handling and persistence.
Future slices can wire them to the optimizer.

### D4: Class deviation cards — horizontal scroll vs. grid

**Decision:** Horizontal flex container with `overflow-x: auto` for many classes.
Each card is a fixed-width block (~160px) with border-left color indicator.

**Rationale:** Grid would wrap to multiple rows with 5+ classes, pushing the
asset table below the fold. Horizontal scroll keeps the class summary compact
and always visible.

### D5: Row color-coding — CSS classes vs. inline styles

**Decision:** Alpine computes a `rowClass` function that returns CSS class
names (`rebalance-asset-row--over`, `--ok`, `--neutral`). CSS owns the actual
colors.

**Rationale:** Keeps styling in CSS (theme-consistent), Alpine only toggles
classes. Inline styles would break dark-mode token system.

## Risks / Trade-offs

- **[Wire format breaking change]** Adding fields to `RebalanceAssetPlanRow`
  and `RebalanceCategoryPlanRow` with `extra="forbid"` will reject old clients
  that don't expect new fields. → Mitigation: New fields are additive (Pydantic
  `extra="forbid"` rejects *unknown* keys, not missing ones. Adding fields to
  the model is safe for consumers; the risk is if an old *server* is called by
  a new client expecting the new fields. Since this is a monolith, no issue.)

- **[Performance with many classes]** Horizontal scroll for 10+ classes may
  hide some cards. → Mitigation: Show count badge ("12 classes") and consider
  wrapping to 2 rows if > 6 classes (stretch goal).

- **[Threshold persistence]** Thresholds reset on page reload. → Mitigation:
  Acceptable for v1. Future slice can persist to session like aporte.

## Migration Plan

1. Extend schemas (additive, no breaking change)
2. Update glue to compute new fields
3. Rewrite `_rebalance_plan.html` (template-only, no route changes)
4. Refactor Alpine component in `rebalance.html`
5. Update CSS (remove stat-grid, add new styles)
6. Update existing tests for new schema fields
7. Run `refresh-for-test` to verify in browser
