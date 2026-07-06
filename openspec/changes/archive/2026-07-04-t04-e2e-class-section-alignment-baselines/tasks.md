## 1. CSS fix

- [x] 1.1 Extend `.class-section-header` `grid-template-columns` in
  `src/omaha/static/app.css` from 8 → 11 columns, mirroring the
  asset-table `<colgroup>`. Existing `--col-*` variables cover
  the new cols (Compra / Venda / Moeda added during T01
  verification).
- [x] 1.2 Update the comment block on `.class-section-header`
  with the F02 rationale so the next author knows the
  three-place dependency (`:root` + `<colgroup>` nth-child +
  header `grid-template-columns`).

## 2. Verification

- [x] 2.1 Run `uv run pytest tests/e2e/test_class_section_alignment.py`
  from a clean `data/test_e2e.db` state. All five scenarios
  (Valor / Alvo-Total / Atual-Total / Sobra-Falta / visible-
  when-collapsed) MUST pass with `abs(delta) <= 1 px`.
- [x] 2.2 Run `uv run task lint` to confirm no CSS lint regressions.
- [x] 2.3 Run `uv run task test-e2e` over the full e2e suite to
  confirm no other scenario drifted as a side-effect of the
  CSS change.
