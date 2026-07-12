## 1. Table integration

- [x] 1.1 Replace rebalance asset-plan table markup with F27's eight-column declarative `columns` model and `x-for` rendering for `<thead>` and `<tbody>`.
- [x] 1.2 Port POC Alpine state/helpers into official rebalance component: sort state, per-column filters, formatting, and filtered row computation.
- [x] 1.3 Wire PT-BR labels, `data-testid` / `data-asset-key` hooks, and filter-panel controls into official `/rebalanceamento` template.

## 2. Theme and cleanup

- [x] 2.1 Align `src/omaha/static/app.css` with POC table styles using app tokens for header actions, filter panels, sliders, badges, and cell alignment.
- [x] 2.2 Remove stale hardcoded table/filter markup and unused state from rebalance templates.

## 3. Verification

- [x] 3.1 Update rebalance page tests for column count, row hooks, sort order, per-column filters, and translated action labels.
- [x] 3.2 Run focused rebalance/unit/e2e coverage and fix regressions.
