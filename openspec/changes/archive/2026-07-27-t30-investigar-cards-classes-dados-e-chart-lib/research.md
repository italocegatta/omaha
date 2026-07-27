# T30 — Durable F49 handoff

Status: investigation complete; research-only. This tracked record is the
durable handoff for a fresh checkout. It preserves conclusions previously
captured in the ignored working note
`openspec/.temp_assets/t30-notes.md`; source evidence below is independent of
that ignored file. Observations and line ranges reflect inspection on
2026-07-26.

## Confirmed evidence

### 1. Current class cards

`src/omaha/templates/_rebalance_plan.html:40-79` renders
`.rebalance-class-summary` only when `plan.category_plan` is truthy. The
container has `data-testid="rebalance-class-summary"` and
`aria-label="Resumo por classe"`; `template x-for` iterates `displayCategories`
and renders `div.rebalance-class-card` with dynamic
`rebalance-class-card-<category_name>` test IDs. Each card renders
`category_name`, `current_pct`, `target_pct`, `deviation_pct`, `delta`, and
frontend-derived `projected_pct`. Individual cards have no `role`,
`aria-label`, `aria-labelledby`, or `aria-describedby`.

`src/omaha/static/app.css:2847-2914` uses
`repeat(auto-fit, minmax(13rem, 1fr))`, `0.9rem` gap, `min-width: 0`, and two
internal metric columns. Cards use `--surface`, `--border-strong`, `--ink`,
`--ink-muted`, `--positive`, and `--negative`; above/below states use positive
or negative top/border treatment. `@media (max-width: 640px)` only changes
parameter controls, not class-card layout. CSS contains no numeric contrast
audit.

`src/omaha/templates/rebalance.html:318-385` copies asset rows and computes
categories. `classCardClass` at `:434-436` uses only the sign of
`deviation_pct` (`above` for non-negative, `below` otherwise); no class action
exists. Formatters at `:88-118,418-431` use BRL currency, one-decimal
percentages, and signed percentage-point deviation.

### 2. Data contract and projected percentage

`src/omaha/rebalance/schemas.py:41-53` defines exactly seven
`RebalanceCategoryPlanRow` fields and `extra="forbid"` at `:44`:

| Field | Type | Source | Card use |
|---|---|---|---|
| `category_name` | `str` | `glue.py:207`, native row name | name/key/test ID |
| `current_value` | `float` | `glue.py:195`, native current value | base for current percentage/delta |
| `projected_value` | `float` | `glue.py:196`, native projected value | base for projected percentage |
| `delta` | `float` | `glue.py:197`, `projected - current` | “Valor”, BRL, signed state |
| `target_pct` | `float = 0.0` | `glue.py:199-202`, target values / portfolio total | “Alvo” |
| `current_pct` | `float = 0.0` | `glue.py:198`, current value / portfolio total | “Atual” |
| `deviation_pct` | `float = 0.0` | `glue.py:204`, current percentage - target | “Desvio” and card state |

`projected_pct` is not schema data. In
`src/omaha/templates/rebalance.html:373-385`, Alpine sums
`Number(r.projected_value) || 0` over `plan.asset_plan` as `totalProjected` and
computes, per category:

```text
projected_pct = projected_value / totalProjected * 100
```

When `totalProjected <= 0`, it emits `0`, avoiding division by zero. This is
projected portfolio weight, not currency. Empty categories may roll up as
zero in `src/omaha/rebalance/postprocessing.py:248-253`.

### 3. Rebalance semantics and data gaps

`src/omaha/rebalance/postprocessing.py:75-110` derives projected values from
current values plus buys minus sells. Category aggregation is at
`src/omaha/rebalance/glue.py:187-214` reconstructs category percentages and
delta. Native category shapes at `engine.py:140-152` and
`solver_stub.py:56-60` carry only category name/current/projected values.

Therefore `delta = projected_value - current_value` is class-level net value
change: positive means net increase, negative net decrease, approximately zero
net hold. Algebraic examples: 4,000 → 5,000 gives +1,000 (net buy); 6,000 →
5,000 gives -1,000 (net sell); 5,000 → 5,000 gives zero (net hold). These are
formula examples, not a fixture snapshot. A 500 buy in one asset plus a 500
sale in another can produce zero delta while operations exist.

Trade thresholds are asset-level in `postprocessing.py:297-323`. Defaults are
`min_deviation_value=1000` and `min_deviation_pct=1` from `schemas.py:18-19`;
a trade is suppressed when either absolute value or percentage deviation is
below its minimum. Thus R$800/2% and R$1,200/0.5% hold, while R$1,200/2% is
actionable; equality is not suppressed. `DISPLAY_TOLERANCE` removes numerical
dust at `postprocessing.py:110-112`.

`RebalanceAssetPlanRow.action` exists and is asset-level
(`glue.py:40-45,178-181`). `RebalanceCategoryPlanRow` has no `action` or
`net_action`. F49 may derive only a clearly labelled **net** display from
delta, with tolerance and compensation caveat. An operational class action
requires a separate contract through schema, native translation, solver/
postprocessing source, glue, wire tests, integration tests, and UI tests.

### 4. Chart decision

For two horizontal measures per 13rem card, inline SVG/CSS is recommended:
zero new dependency, no build step, direct CSS-token theming, small DOM
surface, and sufficient manual transitions. Apache ECharts offers richer
tooltips, scales, legends, animation, and interaction, but adds bundle,
lifecycle, asset policy, theme synchronization, and maintenance cost.
Accessibility remains product-owned with either option. SVG must retain
visible numeric/text fallback and either expose coherent `role="img"` name/
description or remain decorative beside accessible HTML text.

Reverse this recommendation only if F49 requires multiple series/scales,
rich tooltips, zoom, keyboard navigation over points, hundreds of categories,
complex comparative animation, or reused chart infrastructure. Do not add
ECharts in T30.

### 5. Regression exposure

Integration coverage: `tests/test_rebalance_page.py` —
`test_get_rebalanceamento_populated_profile_renders_zero_plan`,
`test_post_rebalanceamento_valid_contribution_renders_plan`,
`test_post_rebalanceamento_thresholds_round_trip_into_rendered_plan`, and
`test_post_rebalanceamento_zero_contribution_renders_plan`; current assertions
mostly check summary presence, not card internals.

Schema/unit coverage: `tests/test_rebalance_schemas.py` —
`test_category_plan_row_carries_exactly_seven_fields`,
`test_response_round_trips_through_model_dump`, and
`test_response_top_level_has_five_fields`. Visual coverage:
`tests/visual/test_snapshots.py::test_rebalance_form_snapshot` and
`::test_rebalance_plan_snapshot`. E2E coverage:
`tests/e2e/test_rebalance_page.py::test_editing_contribution_refreshes_plan_automatically`
checks summary presence; no E2E test inspects individual class-card values,
states, or labels. F49 should update visual coverage and add focused card
assertions if bridge markup becomes contractual.

### 6. Accessibility and responsive constraints

Current summary has an accessible name, but individual cards do not. Token
usage (`app.css:2866-2872,3223-3224`) proves visual intent, not WCAG
compliance; contrast is unverified. F49 must target at least 4.5:1 for normal
text, avoid color-only state, and keep labels, values, and state text available
without hover. At `minmax(13rem, 1fr)`, the grid can become one column, but
rendered fit is unverified. F49 must test 13rem/single-column behavior,
long names, BRL values, percentages, and horizontal overflow. Empty and
zero-total states need explicit text rather than an ambiguous 0% chart.

## Assumptions, risks, and F49 decisions

- Assumption: F49 remains two horizontal measures per card; confirm in its
  proposal/design before implementation.
- Assumption: a delta-derived label is acceptable only when explicitly
  qualified “líquido”; validate domain wording before making it a contract.
- Risk: compensated asset trades make delta unsafe as an operational order.
- Risk: zero totals/empty classes can look like ordinary hold state.
- Risk: unmeasured contrast, missing card semantics, or hidden SVG text can
  fail accessibility.
- Risk: two-column internals can overflow at the 13rem minimum.
- Decision: preserve seven wire fields; keep `projected_pct` client-derived
  unless F49 explicitly opens a contract change.
- Decision: use inline SVG/CSS with visible text fallback; no ECharts now.
- Decision: if operational class action is required, open schema/pipeline work
  before UI; do not infer missing `net_action`.
- Acceptance follow-up: cover zero-total, empty class, near-zero delta,
  threshold, accessibility, and 13rem viewport states before accepting F49.

## Scope and checklist reconciliation

The ignored working note records completion of all ten investigation points,
its acceptance checklist, and the research-only boundary. Inspection of the
T30 diff found no production, test, dependency, schema, template, CSS, seed,
database, roadmap, F48, or F49 changes. The only durable corrective artifact
added here is this handoff; `tasks.md` records the evidenced T30 work.
