## 1. Verify spec wording against live code

- [x] 1.1 Re-read `post_rebalanceamento` and `get_rebalanceamento` in
  `src/omaha/routes/pages.py` and confirm the contract the delta
  describes: success → `RedirectResponse("/rebalanceamento", 303)`
  with the aporte persisted in session; blank → `0`; non-finite /
  non-numeric contribution, malformed threshold, and
  `RebalanceValidationError` → HTTP 200 render with `form_error`;
  GET recomputes with `DEFAULT_MIN_DEVIATION_VALUE=1000.0` /
  `DEFAULT_MIN_DEVIATION_PCT=1.0`.
- [x] 1.2 Confirm the test lock
  `tests/test_rebalance_page.py::test_post_rebalanceamento_success_redirect_renders_plan_with_default_thresholds`
  asserts 303 + `Location: /rebalanceamento` + GET renders the plan
  with default thresholds (no code change — reference only).

## 2. Apply the delta to the stable spec (spec text only)

- [x] 2.1 Replace `### Requirement: POST /rebalanceamento renders the
  plan` in `openspec/specs/rebalance-page/spec.md` with the delta
  version (heading byte-identical; 303 PRG success scenarios, 200
  error scenarios, ephemeral-thresholds paragraph).
- [x] 2.2 Replace `### Requirement: Compact parameter bar` with the
  delta version (ephemeral-thresholds wording; renamed round-trip
  scenario → "Submitted thresholds are ephemeral across the POST
  redirect").
- [x] 2.3 Diff the stable spec after sync: exactly two requirements
  changed; no other requirement references POST 200 or threshold
  round-trip.

## 3. Validate

- [x] 3.1 `openspec validate d04-corrigir-spec-drift-post-rebalanceamento --strict`
  passes.
- [x] 3.2 Confirm zero non-spec files touched (`git status` shows only
  `openspec/` paths).
