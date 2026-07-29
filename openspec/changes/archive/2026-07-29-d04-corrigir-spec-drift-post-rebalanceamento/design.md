## Context

F52 (commit `054f320`, archived 2026-07-28) introduced
POST/Redirect/GET on `POST /rebalanceamento` and made submitted
thresholds ephemeral (design D13, owner-approved). The code
(`src/omaha/routes/pages.py::post_rebalanceamento` /
`get_rebalanceamento`) and the tests already implement that contract.
F52's delta only modified the two chart requirements of
`rebalance-page`; the POST requirement and the parameter-bar threshold
wording were never synced, so the stable spec contradicts the live
behavior. D04 is a spec-text-only correction.

## Goals / Non-Goals

**Goals:**
- Make `openspec/specs/rebalance-page/spec.md` match the live POST
  contract: 303 PRG on success, 200 + `form_error` on validation
  failure, ephemeral thresholds (GET recomputes with defaults).

**Non-Goals:**
- No code, template, static, seed, migration, or test changes —
  behavior is already correct and test-locked.
- No re-documentation of the PRG rationale — F52 design D13 owns it;
  the spec references it.
- No changes to other requirements (`GET /rebalanceamento`,
  `Rebalance inputs submit plan on Enter`, `Threshold gate affects
  rendered execution suggestions`) — they make no false 200/round-trip
  claims.

## Decisions

**D1 — Keep requirement headings byte-identical.** `MODIFIED`
requirements are matched by heading at sync; renaming
`POST /rebalanceamento renders the plan` would need a `RENAMED` delta
and reference churn for zero behavioral value. The corrected body +
scenarios state the 303→GET flow explicitly; the heading stays as the
stable identifier.

**D2 — Also fix `Compact parameter bar` (same root cause).** Its text
("The rendered plan SHALL reflect the submitted thresholds") and its
"Threshold fields submit with the form" scenario claim a threshold
round-trip that no longer exists: thresholds are consumed by the
POST-time computation, then discarded; the redirect's GET recomputes
with `1000.0` / `1.0` (F52 D13). Leaving it would keep a direct
contradiction in the same spec. The fix states the ephemeral contract
once and points at the POST requirement + D13 instead of duplicating
the rationale.

**D3 — Scenarios mirror the test lock.** Scenarios split the POST
assertion (303 + `Location: /rebalanceamento`, no rendered plan) from
the follow-up GET assertion (200, plan rendered, defaults restored),
matching `test_post_rebalanceamento_success_redirect_renders_plan_with_default_thresholds`
(httpx TestClient, no auto-redirect).

## Risks / Trade-offs

- [Heading "renders the plan" reads looser than the new contract] →
  accepted: sync-match stability beats a rename; body is normative and
  explicit about 303→GET.
- [Ephemeral thresholds surprise users who edit thresholds then POST] →
  pre-existing owner-accepted trade-off (F52 D13); D04 only documents
  it in the stable spec. No UX change.
- [Drift elsewhere] → audited: GET requirement, Enter-submit, and
  threshold-gate requirements contain no POST-200 or round-trip claim;
  left untouched.
