## Context

Current patrimônio table is product-correct for the older contract but structurally mismatched with the approved operator mockup. Today the asset rows expose `Classe`, `Qtd` as position count, four percentage columns, and partial sorting. The class header aligns to that legacy shape via CSS variables shared with the `<colgroup>`. The owner now wants one denser financial reading surface: quantity and average price first, `Ganho` with absolute+percent internal split, class and portfolio metrics grouped under nested headers, visual sign signaling for `Desvio` and `Ganho`, and all columns sortable.

The current DB already stores the source inputs needed for the redesign: `Position.qty`, `avg_price`, `total_invested`, `total_current`, plus per-asset/per-class targets and trade flags. This means the slice is primarily aggregation, template, CSS, and test work rather than schema migration.

## Goals / Non-Goals

**Goals:**

- Re-shape the patrimônio aggregate payload so templates can render the new grouped table without ad-hoc math in Jinja.
- Keep one shared column-definition source for widths, sorting keys, and formatting semantics so header/totals/rows stay aligned.
- Preserve existing inline-edit and trade-toggle flows while fitting them into the new column order.
- Keep `Compra`, `Venda`, and `Moeda` behavior unchanged even if surrounding columns move.
- Update spec/test coverage so the new table contract becomes stable and regression-resistant.

**Non-Goals:**

- No schema migration or seed format change unless implementation proves a missing persisted value; that becomes follow-up slice, not scope creep.
- No new dashboard top-level metrics beyond existing `Investido`, `Valor atual`, `Ganho`.
- No change to rebalance solver, quote provider, import workflow semantics, or profile/family access rules.
- No redesign of add-asset modal layout outside support changes needed for inline edit/sort helpers.

## Decisions

### D-F15.1 — Drive table structure from expanded aggregate rows, not template-local calculations

`routes/pages.py` will compute the new per-asset fields (`avg_price`, `gain_value`, `gain_pct`, `class_deviation`, `portfolio_target_pct`, `portfolio_deviation`, and quantity semantics) before render, and the Jinja/Alpine layer will consume pre-shaped values/keys.

Rationale: the current table already depends on server-shaped aggregate rows. Extending the payload keeps rounding/sign logic consistent across profile and family modes and avoids duplicating math in Jinja plus Alpine.

Alternatives considered:

- Compute gain/deviation entirely in template filters — rejected; too much duplicated formatting/sign logic.
- Compute everything client-side in Alpine — rejected; worsens initial render determinism and testability.

### D-F15.2 — Keep one visible `Ganho` column backed by two internal layout cells

The table contract will treat `Ganho` as one operator-facing column, but implementation may use two subcells/subcolumns (absolute and percent) with collapsed internal borders or grid layout so alignment and numeric formatting remain stable.

Rationale: owner wants visual simplicity without giving up precise alignment. Internal split solves both.

Alternatives considered:

- Render gain as one text node (`R$ X (Y%)`) in one cell — rejected; poor numeric alignment and harder styling.
- Split into two visible columns (`Ganho R$`, `Ganho %`) — rejected; violates approved mockup.

### D-F15.3 — Replace flat class-header pills with grouped class totals row bound to same width tokens as asset rows

The old `.class-section-header` alignment contract will evolve into a row that aligns class totals against the redesigned asset-table columns using the same shared width variables. Group labels (`Classe`, `Carteira`) live in the table header; totals row occupies the same column grid.

Rationale: old contract assumed one header line with sparse cells. New grouped model needs an explicit totals row so the operator can scan total/class/asset values vertically.

Alternatives considered:

- Keep the old pill header and only rename columns — rejected; cannot express grouped `Classe` / `Carteira` contract cleanly.
- Render class totals as first `<tbody>` row only — rejected; loses collapsed-state visibility contract.

### D-F15.4 — Sorting remains local to each class section, but every visible metric gets an explicit key and type

The existing `classSection` Alpine component will keep sort state per class section. Each visible data column gets declared sort metadata (text or numeric) so asc/desc toggling is deterministic. Default sort should reflect the owner-approved initial reading order rather than legacy `class asc then alvo % classe asc`.

Rationale: per-class local sorting preserves the current section ownership model and avoids cross-section row leakage. Explicit metadata is simpler than hard-coded switch statements spread across helpers.

Alternatives considered:

- Global sort across all class tables — rejected; breaks the sectioned dashboard model.
- Preserve legacy default sort even after column redesign — rejected; mismatched with new reading order.

### D-F15.5 — Formatting rules are declarative per column family, not per call site

Formatting helpers will be organized around value families: money by currency (`BRL`, `USD`), percentages with one decimal, rounded absolute values, and sign-aware deltas. Template cells should call the matching helper rather than embedding `toLocaleString` options inline.

Rationale: the redesign adds many numeric cells with different display rules. Centralizing formatting reduces drift and makes test expectations crisp.

Alternatives considered:

- Inline `toLocaleString`/`toFixed` per cell — rejected; high duplication and rounding drift risk.

### D-F15.6 — Use sign-state tokens and Material Symbols arrows already in repo for `Ganho` and `Desvio`

Positive/negative states will reuse existing status-color vocabulary (`--positive`, `--negative`) and Material Symbols arrow glyphs rather than inventing new icon assets.

Rationale: F12 already landed Material Symbols; this slice should reuse them and keep sign semantics consistent with existing UI.

Alternatives considered:

- Pure color without icon — rejected; owner explicitly requested icon+color.
- Emoji or SVG-only indicators — rejected; inconsistent with repo icon system.

## Risks / Trade-offs

- Default sort expectation may break current tests and user muscle memory → mitigate by codifying new default in spec/e2e and updating all selectors in same slice.
- Family mode may not have meaningful portfolio/class targets for every row → mitigate by specifying neutral formatting/placeholder rules during apply if target is absent.
- Quantity semantics currently equal sum of `Position.qty`, not row count → mitigate by documenting this in tests and avoiding reuse of legacy `position_count` label for displayed quantity.
- Currency formatting for `USD` rows may reveal mixed-currency totals edge cases → mitigate by keeping portfolio/class totals on current persisted totals and only varying displayed per-asset currency prefix where row currency is `USD`.

## Migration Plan

1. Extend aggregate builders in `routes/pages.py` with new row fields and class total metadata.
2. Replace legacy grouped-header/table markup in `_patrimonio_class_section.html` and supporting Alpine helpers in `_patrimonio_add_asset_modal.html`.
3. Update CSS variable map, grouped headers, sign states, and merged `Ganho` styling in `app.css`.
4. Update portfolio header `Ganho` rendering to match split-value/sign-state contract.
5. Refresh integration, BDD, and e2e coverage for sorting, formatting, alignment, and collapsed-state behavior.
6. Run `opsx list --specs`, task-based tests, and `refresh-for-test` before declaring apply complete.

Rollback: revert implementation commit. No schema change means rollback is file-only.

## Open Questions

- Family aggregate target columns likely need placeholders because merged cross-profile rows do not always have a meaningful single target. Resolve during apply and capture in delta spec if needed.
- `US$` exact formatting style (`US$ 1.234` vs `US$ 1,234.5`) should follow existing PT-BR numeric separators with currency prefix unless owner says otherwise.
