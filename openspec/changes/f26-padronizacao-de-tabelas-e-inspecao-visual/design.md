## Context

Dashboard has 3 table families that share visual contracts but use different partials and CSS blocks: Patrimônio asset tables in `_patrimonio_class_section.html`, Rebalance plan tables in `_rebalance_plan.html`, and import review tables in `_patrimonio_add_asset_modal.html`. Current `app.css` still carries page-specific table rules, so small spacing or font edits can leave one family tighter or typographically different than others.

The visible symptom in this slice is table drift: headers feel cramped, and labels like `Atual` can render with a different rhythm than neighboring cells. Existing visual coverage already snapshots the pages, but it needs explicit table-heavy states so wrap, overflow, and type mismatch stay obvious in review.

## Goals / Non-Goals

**Goals:**
- Unify shared table rhythm: header padding, cell padding, wrapping, numeric alignment, and text weight.
- Keep existing selector contracts and alignment behavior intact.
- Expand visual coverage so table-heavy states fail loudly on wrap, overflow, or typographic drift.
- Preserve current e2e geometry/alignment tests; use them as guardrails, not replacements for screenshots.

**Non-Goals:**
- No route, API, model, or seed changes.
- No new component library or table framework.
- No redesign of non-table browser surfaces.
- No loosening of existing alignment contracts to make screenshots easier.

## Decisions

### 1. Use shared CSS rhythm, not per-cell exceptions

Table families SHALL converge on shared `app.css` rules for typographic rhythm and spacing, with page-specific selectors only for unique columns or controls.

**Why:** page-local inline styles or one-off overrides are what create font and crowding drift.

**Alternatives considered:**
- Inline per-cell styling. Rejected: hard to audit and impossible to keep consistent across families.
- Separate style rules per page. Rejected: duplicates the same contract in 3 places.

### 2. Keep visual inspection in Playwright baselines

The canonical table regression signal SHALL stay in `tests/visual/`, with existing desktop/mobile screenshot baselines expanded for dense table states.

**Why:** wrap, overflow, and type rhythm are visual problems; computed-style assertions miss the actual browser result.

**Alternatives considered:**
- Add only e2e DOM assertions. Rejected: they do not show cramped headers or overflow.
- Add a separate one-off screenshot harness. Rejected: current visual suite already owns baseline review and update flow.

### 3. Preserve alignment contracts while changing table styling

Existing alignment coverage stays authoritative, especially the class-section/header-to-table contracts. Styling changes must pass current geometry tests rather than weakening them.

**Why:** this slice is about readability, not moving columns.

**Alternatives considered:**
- Loosen alignment tolerances. Rejected: would hide real regressions.

### 4. Use table-heavy fixture states for regression visibility

Visual snapshots SHALL use dense enough data to surface wrap and header crowding on both desktop and mobile.

**Why:** empty or sparse tables can hide the exact regressions this slice targets.

**Alternatives considered:**
- Keep only current light snapshots. Rejected: too easy to miss cramped headers and font drift.

## Risks / Trade-offs

- [Risk] Font/padding changes churn baselines → [Mitigation] update affected PNGs in same change and review both viewports.
- [Risk] Shared CSS selectors may affect more table families than intended → [Mitigation] keep overrides scoped and verify affected tables with focused screenshots.
- [Risk] Dense mobile states can become noisy → [Mitigation] use readable fixture density, not ultra-small text, and verify both desktop/mobile baselines.
- [Risk] Visual drift could be real or intentional → [Mitigation] keep e2e geometry checks and visual diffs both green before close.

## Migration Plan

1. Normalize shared table rules in `src/omaha/static/app.css`.
2. Adjust affected template partials only where stable anchors or structure are needed.
3. Expand table-heavy visual snapshots in `tests/visual/test_snapshots.py`.
4. Regenerate `tests/visual/baselines/*.png` for desktop and mobile.
5. Run visual suite plus targeted table/alignment e2e checks.
6. If drift is intentional, keep the updated baselines; if not, revert CSS/markup and regenerate.

## Open Questions

- None after current audit. Existing table families already expose enough structure to build dense visual states without new runtime dependencies.
