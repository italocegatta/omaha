## 1. Preserve research-only boundary

- [x] 1.1 Inspect only T30-linked card, schema, postprocessing, CSS, and test files, plus directly named rebalance glue, engine, stub, and E2E files needed to establish evidence.
- [x] 1.2 Create working note `openspec/.temp_assets/t30-notes.md` and maintain durable tracked handoff `research.md`; do not change production code, tests, dependencies, schemas, seeds, database state, UI, or roadmap. Evidence: ignored working note exists and `research.md` contains durable handoff findings.

## 2. Map current cards and percentage data

- [x] 2.1 Document current class-card HTML in `_rebalance_plan.html`, including rendered fields, container semantics, test IDs, and absence/presence of per-card ARIA labeling. Evidence: `research.md`, §1.
- [x] 2.2 Document card CSS in `app.css`, including grid/card sizing, above/below visual states, typography, token pairs, and narrow-viewport constraints. Evidence: `research.md`, §1.
- [x] 2.3 Document Alpine card behavior in `rebalance.html`: `_computeCategories`, `classCardClass`, and percentage/currency/deviation formatters. Evidence: `research.md`, §1.
- [x] 2.4 List all seven `RebalanceCategoryPlanRow` fields with type, source, and card use; confirm `projected_pct` is frontend-derived rather than Pydantic schema data. Evidence: `research.md`, §2.
- [x] 2.5 Document exact `projected_pct = projected_value / totalProjected * 100` calculation, `totalProjected` source, zero-total behavior, and its meaning as projected portfolio weight rather than currency. Evidence: `research.md`, §2.

## 3. Investigate rebalance semantics and data gaps

- [x] 3.1 Trace `current_pct`, `target_pct`, `deviation_pct`, and `delta` through postprocessing, engine, glue, and native stub; cite symbols and line ranges. Evidence: `research.md`, §3.
- [x] 3.2 Confirm or reject `delta` as class-level net purchase/sale using solver-backed examples for positive, negative, and approximately zero delta; document `min_deviation_value` and `min_deviation_pct` effects on hold classification. Evidence: `research.md`, §3; examples are formula-derived, not fixture snapshots.
- [x] 3.3 Verify whether class-level `action`/`net_action` exists separately from `RebalanceAssetPlanRow.action`; document safe frontend derivation or exact schema/pipeline/test impact if F49 requires a new field. Evidence: `research.md`, §3.

## 4. Evaluate bridge rendering and regression exposure

- [x] 4.1 Compare Apache ECharts and inline SVG/CSS for two horizontal class-card measures: dependency and bundle cost, interaction/animation capability, theming, accessibility responsibility, and maintainability; record recommendation and reversal conditions. Evidence: `research.md`, §4.
- [x] 4.2 Catalog affected integration, unit, visual-snapshot, and E2E tests by exact path and test name; state whether E2E currently inspects class cards directly or only summary presence. Evidence: `research.md`, §5.
- [x] 4.3 Assess accessibility and responsiveness: container/card labels and roles, text/color contrast evidence and unverified gaps, required SVG text fallback, minimum 4.5:1 contrast target, and fit at 13rem/single-column mobile width. Evidence: `research.md`, §6.

## 5. Deliver and accept technical notes

- [x] 5.1 Write working note `openspec/.temp_assets/t30-notes.md` with separately labeled confirmed evidence, assumptions, risks, F49 decisions, source references, and findings for all ten investigation points; preserve corresponding durable handoff in tracked `research.md`. Evidence: ignored working note exists and `research.md` is the durable handoff.
- [x] 5.2 Complete acceptance checklist across working note and durable handoff: seven schema fields/types/origins; projected percentage formula; delta/action conclusion and exceptions; chart comparison/recommendation; impacted tests; data gaps; accessibility/responsiveness; and explicit confirmation that no production or test file changed. Evidence: durable `research.md`, §§1-6 and scope reconciliation, reconciles working note findings.
- [x] 5.3 Run repository OpenSpec verification and confirm proposal artifacts plus investigation spec are valid; do not run application or test suite for this documentation-only slice. Evidence: `openspec validate t30-investigar-cards-classes-dados-e-chart-lib --strict` passed.
