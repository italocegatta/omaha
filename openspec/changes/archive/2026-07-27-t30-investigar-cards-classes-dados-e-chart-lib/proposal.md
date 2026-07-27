## Why

F49 needs decision-grade evidence about current class cards, their rebalance data contract, and a chart-rendering direction before any bridge graphic can be proposed safely. T30 isolates that research without changing runtime behavior.

## What Changes

- Produce `openspec/.temp_assets/t30-notes.md` with findings for all ten T30 investigation points: card structure, data flow and calculations, class-level action semantics, chart-library trade-off, test exposure, data-contract gaps, accessibility, and responsive fit.
- Confirm or reject assumptions about `delta`, `net_action`, projected percentages, threshold behavior, and affected rebalance pipeline layers using source evidence.
- Record SVG/CSS versus Apache ECharts recommendation and conditions that would change it.
- Preserve a research-only boundary: no production, test, dependency, schema, UI, seed, or roadmap changes.

## Capabilities

### New Capabilities

- `rebalance-bridge-investigation`: internal decision record required before the
  dependent F49 bridge-graphic proposal; it has no runtime behavior.

### Modified Capabilities

None. Existing behavioral requirements remain unchanged.

## Impact

Only OpenSpec planning artifacts and temporary research notes are created. Findings reference current rebalance templates, schema, postprocessing, glue/engine/stub translation layers, styles, and existing integration, unit, visual, and E2E coverage. F49 will consume the notes; no dependency is added.
