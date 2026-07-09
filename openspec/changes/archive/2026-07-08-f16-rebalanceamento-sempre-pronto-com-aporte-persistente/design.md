## Context

Current rebalance flow is stateless from the page point of view. `GET /rebalanceamento` renders either empty state or a placeholder, and `POST /rebalanceamento` computes a plan only for that response. The submitted aporte is not stored anywhere durable inside the running app, so moving through `/patrimonio`, importing CSV, editing targets, or simply revisiting the page loses the operator's working value even though the underlying data changed.

This slice needs cross-page continuity but does not need database persistence. PRD and roadmap both constrain this state to the lifetime of the running app/session: restart goes back to zero, and no new model/seed/migration should appear.

## Goals / Non-Goals

**Goals:**

- Preserve one current aporte value per active profile for the logged-in session.
- Render a rebalance plan by default for populated profiles, using `0` when no aporte exists yet.
- Recompute the plan from live DB state on each rebalance page render so CSV imports, class edits, asset edits, and target changes show up automatically.
- Keep zero-classes and family/sentinel safety behavior intact.
- Keep page and JSON route contribution semantics aligned around finite-float validation and zero-default omission.

**Non-Goals:**

- No database column, seed-path, or migration for aporte or plan snapshots.
- No background rebalance cache, job queue, or persisted serialized plan object.
- No change to solver math, quote-provider policy, or rebalance result schema beyond omitted-contribution defaulting.
- No attempt to make aporte survive logout, browser/session destruction, or app restart.

## Decisions

### D-F16.1 - Persist only contribution, not full plan

Store only the current aporte in session state, keyed by active profile id. The plan itself is recomputed from DB and quotes on each render.

Rationale: the plan is derived data and would go stale after every portfolio mutation. Persisting only the small operator input keeps session payload tiny and guarantees fresh results without invalidation bookkeeping.

Alternatives considered:

- Persist full `RebalancePlanResponse` in session - rejected; stale after any mutation and too large for cookie-backed session storage.
- Persist contribution in database - rejected; roadmap explicitly scopes persistence to app/runtime lifetime only.

### D-F16.2 - Materialize on GET instead of showing placeholder for populated profiles

`GET /rebalanceamento` will resolve the active profile's stored contribution (or `0` when absent), run rebalance immediately, and render the plan when the profile has at least one class. Empty-state remains only for zero-class profiles.

Rationale: this is the smallest change that makes rebalance "always ready" and automatically refreshed after any patrimonio mutation.

Alternatives considered:

- Keep placeholder and only prefill the input - rejected; still requires another click and does not satisfy "sempre pronto".
- Add front-end auto-submit on page load - rejected; extra client complexity for behavior the server can render directly.

### D-F16.3 - Normalize omitted/blank contribution to zero at both HTML and JSON boundaries

The HTML flow will treat an empty aporte field as `0`. The JSON route will treat an omitted `contribution` field as `0`. Explicit non-finite values remain invalid.

Rationale: page and API contracts should not disagree about the zero-default meaning of "no aporte provided yet".

Alternatives considered:

- Keep HTML-only zero default and leave JSON at 422 - rejected; creates needless contract drift.
- Treat blank/omitted as validation error and fake zero only on GET - rejected; inconsistent operator experience.

### D-F16.4 - Recalculation after mutations comes from fresh render, not mutation-hook recompute

Mutation endpoints in classes/assets/imports do not need to compute or persist new plans directly. They only need to leave the stored aporte untouched. Whenever the operator lands on `/rebalanceamento`, the page recomputes from current DB state.

Rationale: most mutation routes already redirect or re-render existing pages. Avoiding cross-route rebalance side effects keeps scope smaller and preserves one source of truth for plan materialization.

Alternatives considered:

- Recompute plan inside every mutation route - rejected; cross-cutting duplication and higher risk of drift.
- Add a shared global cache invalidation layer - rejected; overbuilt for session-lifetime state.

### D-F16.5 - Profile switch preserves values independently per profile

Session state is a mapping keyed by profile id, so switching from one portfolio to another does not overwrite the first profile's aporte. Returning to that profile restores its last value and recomputes the corresponding plan.

Rationale: active profile is already a session concept, and per-profile memory matches operator expectation when comparing portfolios.

Alternatives considered:

- One global aporte shared across all profiles - rejected; leaks operator intent between unrelated portfolios.

## Risks / Trade-offs

- Extra solver run on every `GET /rebalanceamento` -> Mitigation: limit to populated profiles only; empty-state remains cheap.
- Session float serialization drift -> Mitigation: normalize through one helper and store plain JSON-safe numeric values.
- Stored contribution may outlive major quote drift within same session -> Mitigation: recompute from current DB/quotes every render, so only operator input is reused.
- Omitted-contribution API change may affect callers expecting 422 -> Mitigation: spec delta and route tests must codify new zero-default behavior explicitly.

## Migration Plan

1. Add session helpers for reading/writing per-profile aporte state.
2. Update `GET /rebalanceamento` and `POST /rebalanceamento` to use the helper and render from computed plan.
3. Adjust rebalance request parsing/schema so omitted JSON contribution defaults to `0`.
4. Update template/tests/specs for always-materialized behavior.
5. Run `openspec list --specs` before moving to apply.

Rollback: revert change files. No schema/data migration means rollback is code-only.

## Open Questions

- Whether the input should render literal `0` when no explicit aporte exists yet, or render blank while the server still computes with zero. Proposal assumes visible `0` is acceptable because it matches the active plan.
- Whether the rebalance page should surface a subtle "atualizado com último aporte" affordance after cross-page return. Not required for this slice unless implementation shows operator ambiguity.
