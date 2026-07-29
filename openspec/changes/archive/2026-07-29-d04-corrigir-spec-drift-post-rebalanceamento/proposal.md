## Why

F52's PRG fix (commit `054f320`) changed `post_rebalanceamento` so the
success path returns `RedirectResponse("/rebalanceamento", 303)`
(POST/Redirect/GET) instead of rendering the plan directly with HTTP
200, and made submitted thresholds ephemeral (only the aporte survives
the redirect). The code and tests already follow this contract, but
`openspec/specs/rebalance-page/spec.md` was never updated — it still
says POST "re-renders" with 200 / "no redirect" and that "the rendered
plan SHALL reflect the submitted thresholds". Spec-text-only fix; no
behavior changes.

## What Changes

- Correct requirement `POST /rebalanceamento renders the plan`: success
  (finite contribution, including blank→0, zero, and negative) SHALL
  return HTTP 303 See Other to `/rebalanceamento`; the browser follows
  with GET, which renders the plan from the persisted aporte and the
  default thresholds. Validation failures (non-finite contribution,
  malformed thresholds, solver `RebalanceValidationError`) still render
  the page directly with HTTP 200 + inline `form_error`.
- Correct requirement `Compact parameter bar`: thresholds are ephemeral
  form state — submitted with the POST and consumed by the POST-time
  computation, but NOT persisted; after the redirect the GET recomputes
  with defaults `1000` / `1` and the inputs re-render at defaults. Only
  the aporte round-trips (per-profile, in session).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `rebalance-page`: POST success contract (200 render → 303 PRG → GET
  renders) and the ephemeral-thresholds correction in the parameter bar
  requirement.

## Impact

- Spec text only: `openspec/specs/rebalance-page/spec.md` (via delta +
  sync at archive).
- No code, template, static, seed, or test changes — the live behavior
  is already correct and locked by
  `tests/test_rebalance_page.py::test_post_rebalanceamento_success_redirect_renders_plan_with_default_thresholds`.
- PRG rationale + ephemeral-thresholds trade-off already documented in
  F52 design D13; this change only brings the stable spec in line.
