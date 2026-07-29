## 1. Audit table surfaces

- [ ] 1.1 Review `_patrimonio_class_section.html`, `_rebalance_plan.html`, and `_patrimonio_add_asset_modal.html` to map every visible table/header variant and its stable `data-testid` anchors.
- [ ] 1.2 Audit table-related rules in `src/omaha/static/app.css` (`asset-table`, `rebalance-table`, `import-review-table`) for duplicate typography, padding, wrapping, and width overrides.

## 2. Normalize shared table styling

- [ ] 2.1 Refactor shared table header/body rules in `src/omaha/static/app.css` so headers, numeric cells, and labels like `Atual` inherit one table rhythm.
- [ ] 2.2 Remove or narrow page-specific overrides that create cramped headers or mixed font rendering across table families.

## 3. Expand visual inspection

- [ ] 3.1 Update `tests/visual/test_snapshots.py` so table-heavy states stay the canonical visual gate for desktop and mobile table review.
- [ ] 3.2 Add or tighten focused e2e checks in `tests/e2e/` for table header geometry/readability where screenshots alone are too coarse.

## 4. Regenerate baselines and verify

- [ ] 4.1 Regenerate affected `tests/visual/baselines/*.png` files and inspect diffs for wrap, overflow, and font drift.
- [ ] 4.2 Run `uv run task test-visual` and targeted table/alignment e2e tests until green.
- [ ] 4.3 Confirm spec health after the visual updates and prepare slice for `Spec Proposed` roadmap status.
