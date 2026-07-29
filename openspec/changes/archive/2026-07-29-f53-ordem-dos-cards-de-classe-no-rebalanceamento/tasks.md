## 1. Implement normative card order

- [x] 1.1 Add a fixed `CATEGORY_DISPLAY_ORDER = ['RF Pós', 'RF Dinâmica', 'FII', 'Ações', 'Internacional', 'Cripto']` constant in `src/omaha/templates/rebalance.html`
- [x] 1.2 Add a comparator that sorts by normative index and puts unknown classes after mapped classes, alphabetically by `category_name`
- [x] 1.3 Make `_computeCategories()` sort `displayCategories` with the new comparator instead of `rebalanceCategorySortFn`
- [x] 1.4 Remove dead category-sort surface: `categorySortKey`, `categorySortDir`, `sortByCategory`, `sortIndicatorCategory`, and `rebalanceCategorySortFn`, after confirming no template/test uses them
- [x] 1.5 Verify no schema, route, solver, CSS, card shell, waterfall, asset-table, or metrics code changed

## 2. Tests

- [x] 2.1 Add/adjust integration assertion in `tests/test_rebalance_page.py` proving the rendered page contains the normative order contract (constant + comparator wiring) and no dead category-sort identifiers
- [x] 2.2 Add/extend e2e coverage to assert rendered `data-testid="rebalance-class-card-<name>"` DOM order when a plan contains normative classes; if deterministic six-class fixture is infeasible, assert available subset order and record limitation
- [x] 2.3 Run focused tests: `task test-unit`, relevant integration test file, and touched e2e test
- [x] 2.4 Run lint (`task lint` or repo hook equivalent) and confirm clean

## 3. Visual baseline and delivery

- [x] 3.1 Regenerate only the affected visual baselines (`rebalance-plan` and `rebalance-form`) with `UPDATE_VISUAL_BASELINES=1` plus the visual task/test, then rerun visual without update to confirm green
- [x] 3.2 Inspect visual diff to confirm only card order moved (no unrelated style/content changes)
- [x] 3.3 Run `refresh-for-test` and emit the PRD §4.9 delivery receipt
- [x] 3.4 Run spec verification gate (`openspec validate --strict` / repo spec check) before archive
