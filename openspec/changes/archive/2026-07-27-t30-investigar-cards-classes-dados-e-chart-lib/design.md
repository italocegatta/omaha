## Context

Current class cards are rendered from `category_plan` by Jinja plus Alpine. Server output exposes seven `RebalanceCategoryPlanRow` fields; Alpine derives `projected_pct` from summed asset projected values. F49 needs an evidence-backed bridge-graphic proposal, including whether class action can derive safely from `delta`, before it changes this surface.

## Goals / Non-Goals

**Goals:**

- Create one durable, source-linked investigation record at `openspec/.temp_assets/t30-notes.md`.
- Answer all ten roadmap investigation points, including concrete buy, sell, and hold examples and any threshold exception.
- Give F49 an explicit SVG/CSS-versus-ECharts recommendation, accessibility/responsive constraints, test impact inventory, and schema-gap decision path.

**Non-Goals:**

- No runtime code, templates, CSS, tests, schemas, dependencies, seeds, DB state, roadmap, or UI changes.
- No chart prototype, library install, schema expansion, or F49 implementation.

## Decisions

### Inspect source boundaries, not runtime state

Evidence comes from linked template, schema, postprocessing, CSS, and test files, plus directly named rebalance glue, engine, and stub layers. This proves existing contract and change blast radius without running application or test suites.

Alternative: infer behavior from roadmap assertions alone. Rejected because F49 needs code-level evidence and discrepancies must be recorded.

### Treat `projected_pct` and class `net_action` as separate findings

Notes must distinguish server schema fields from Alpine-derived values. They must confirm whether `delta = projected_value - current_value` can classify class buy/sell/hold, document solver threshold effects, and state whether F49 needs a frontend derivation or a schema/pipeline extension.

Alternative: label `delta` directly as action. Rejected until solver examples and threshold behavior support it.

### Prefer SVG/CSS unless documented future requirements justify ECharts

Comparison covers dependency/bundle cost, interaction capability, animation, theming, accessibility ownership, and suitability for two horizontal measures per 13rem card. Preliminary recommendation remains inline SVG/CSS; notes must state conditions that warrant ECharts.

Alternative: select ECharts now. Rejected because T30 does not add dependencies and current visual need is narrow.

### Research-only delta spec

The existing `specs/rebalance-bridge-investigation/spec.md` is an intentional
delta spec for T30's internal, decision-grade investigation record. It adds no
runtime behavior and is not a stable product capability contract: its single
requirement governs only the source-linked research handoff required before
F49 is proposed. This matches the proposal's `rebalance-bridge-investigation`
internal capability and the research-only boundary; no existing capability is
modified and no production contract is introduced.

## Risks / Trade-offs

- [Delta appears to imply action but solver thresholds suppress trades] → document evidence, thresholds, and decision boundary; do not assert equivalence without confirmation.
- [Source paths or current implementation differ from roadmap line references] → cite actual symbols and line ranges in notes, then report discrepancy for F49.
- [Accessibility depends on token contrast not visible from component rules] → identify exact token pairs and mark unverified contrast for F49 rather than claim compliance.
- [Notes become speculative design] → segregate confirmed facts, assumptions, and F49 decisions; cite source path/symbol for each fact.
