## Context

`/rebalanceamento` renders class summary cards from Alpine `displayCategories`, computed in `rebalance.html:_computeCategories()`. Today it copies `plan.category_plan` and sorts by `category_name` (`rebalanceCategorySortFn`, default `categorySortKey: 'category_name'`). Server payload already carries a `display_order`-sorted category plan, but the client discards it. No UI control invokes `sortByCategory`/`sortIndicatorCategory`; they are dead surface.

Owner normative order: `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`.

## Goals / Non-Goals

**Goals:**
- Cards render in owner normative order on page load, independent of server payload order.
- Deterministic fallback for classes absent from the normative map.
- Remove dead category-sort code created for a UI that does not exist.
- Keep change surgical: no schema, solver, CSS, card content, waterfall, asset table, or metric changes.

**Non-Goals:**
- Changing `AssetClass.display_order` or seed CSVs (that is F54, patrimônio).
- Making rebalance cards consume server `display_order` (may be revisited later; not this slice).
- Adding user-facing card sorting or reordering controls.
- Changing `RebalanceCategoryPlanRow` fields.

## Decisions

### D1 — Fixed JS name→position map

Use a constant ordered array in `rebalance.html`:

```js
var CATEGORY_DISPLAY_ORDER = ['RF Pós', 'RF Dinâmica', 'FII', 'Ações', 'Internacional', 'Cripto'];
```

Comparator returns `index(a) - index(b)`. Owner chose this over respecting payload order because it produces the visible effect immediately and does not depend on F54 seed renumbering.

Alternatives considered:
- Respect server `display_order` in payload: rejected for this slice because current seed order is not normative and F54 owns seed renumbering for patrimônio.
- Add `display_order` to category schema: explicitly forbidden by roadmap; schema stays 7 fields.

### D2 — Fallback for unknown classes

Unknown class names receive index `CATEGORY_DISPLAY_ORDER.length` and tie-break by `category_name.localeCompare`. This puts unlisted classes at the end in stable alphabetical order.

Rationale: current seeded profiles have exactly the six listed classes, but UI/import can create new classes; rendering must remain deterministic and not drop them.

### D3 — Remove dead category sort state

Remove `categorySortKey`, `categorySortDir`, `sortByCategory`, `sortIndicatorCategory`, and `rebalanceCategorySortFn`. Grep confirms no template or test invokes them as UI behavior. `_computeCategories()` remains and applies the normative comparator.

Alternative: keep functions but change default key — rejected because it leaves unused code and implies a sorting affordance that does not exist.

### D4 — Test proof

Order is client-side Alpine behavior. TestClient renders template source but does not execute Alpine. Therefore:
- Integration test asserts the normative comparator contract is present in rendered JS (constant order array and `_computeCategories` using it), following existing source-assertion pattern in `tests/test_rebalance_page.py`.
- Add/extend an e2e Playwright check that reads rendered `data-testid="rebalance-class-card-<name>"` DOM order after Alpine init, when a seeded or fixture plan contains the normative classes.

Visual baseline `rebalance-plan` must be regenerated because card positions move.

## Risks / Trade-offs

- [Client map diverges from future server order] → F54 may renumber seed `display_order`; if later desired, a follow-up can replace map with payload order. This slice documents the map as the source of truth for rebalance cards.
- [E2E adds runtime] → keep assertion minimal, reuse existing rebalance e2e page setup; if harness cannot seed all six classes deterministically, fall back to source-contract assertion plus manual refresh-for-test verification.
- [Unknown class ordering surprise] → explicit fallback end+alphabetical; spec encodes it.
- [Visual snapshot diff] → expected; regenerate only `rebalance-plan` baseline and inspect for unrelated diffs.
