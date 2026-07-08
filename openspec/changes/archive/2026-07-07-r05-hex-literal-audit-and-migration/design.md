## Context

F08 fixed core palette semantics, but residual pre-dark-mode literals still live in `src/omaha/static/app.css`: 9 shared UI surfaces still paint `#fff`, and 8 import-preview class chips still derive from inline hex values instead of the post-F08 token palette. DESIGN.md already records both as polish-pass backlog, so this slice is mechanical cleanup inside visual layer, not new product behavior.

## Goals / Non-Goals

**Goals:**

- Remove remaining hardcoded white surfaces from shared dashboard CSS where dark-mode tokens already express intended elevation.
- Add derived `--class-N-tint` tokens so import-preview class chips stay aligned with `--class-N` palette on dark `--surface`.
- Replace inline hex-based `color-mix(...)` chip rules with token-backed tints.
- Mark DESIGN.md polish-pass items 1-2 as delivered and sync `color-tokens` spec delta.

**Non-Goals:**

- No palette re-derivation of core tokens (`--accent`, `--positive`, `--negative`, `--class-N`). F08 remains source of truth.
- No template, route, auth, seed, or data-model changes.
- No new visual-baseline harness; T06 owns screenshot coverage.
- No attempt to remove every hex literal repo-wide; scope is residual runtime CSS called out in DESIGN.md polish pass.

## Decisions

### D-R05.1 — Shared white surfaces collapse to existing elevation tokens

Selectors still using `background: #fff` move to `var(--surface)` unless the selector already represents a sunken well, in which case it keeps `var(--surface-sunk)`. This keeps R05 mechanical: no new elevation vocabulary, only removal of stale light-mode literals.

Alternatives considered:

- Keep white for form controls to maximize affordance. Rejected: on current dark body these sites read as accidental islands, not intentional contrast.
- Introduce a new `--surface-contrast` token. Rejected: overkill for residual cleanup; D02/F08 deliberately stayed on 2-tier surface.

### D-R05.2 — Tint tokens derive from `--class-N`, not duplicated color literals

Add `--class-1-tint` through `--class-8-tint` in `:root`, each defined as `color-mix(in srgb, var(--class-N) 38%, var(--surface))`. Import-preview chip rules then reference `var(--class-N-tint)`.

Rationale: the tint is derivative data, not a second palette. Keeping formula in token layer means any future class-color adjustment automatically propagates to preview chips without reintroducing hex-vs-token drift.

Alternatives considered:

- Keep literal `color-mix(... #hex ...)` rules. Rejected: exactly drift bug R05 exists to remove.
- Hardcode tinted OKLCH values. Rejected: duplicates derivation math in 8 places and becomes fragile if `--surface` changes.

### D-R05.3 — Import preview remains 1:1 with current 8-slot class index contract

The preview cell rules stay `.import-class-cell--cls-0` through `--cls-7`, mapped to `--class-1-tint` through `--class-8-tint`. No server-side modulo or index contract changes land in this slice.

Rationale: runtime behavior already expects 8 slots via `_CLASS_COLORS`; R05 only changes how background is sourced.

### D-R05.4 — Verification stays textual, token, and smoke-level

Verification focuses on lint, unit/integration suites, `openspec validate`, and a small runtime smoke after `refresh-for-test`. T06 will own screenshot baselines later, so R05 does not need new image assertions.

## Risks / Trade-offs

- **Risk:** Some white surfaces may have been compensating for low-contrast nested controls. → **Mitigation:** map to `var(--surface)` first, then smoke `/patrimonio` and import flow after `refresh-for-test`.
- **Risk:** `color-mix(... var(--class-N) ...)` may resolve differently across browsers than prior hex literals. → **Mitigation:** formula already exists in runtime CSS today; only source token changes from literal hex to `var(--class-N)`.
- **Risk:** DESIGN.md may drift again if future palette slices land without touching polish-pass notes. → **Mitigation:** convert items 1-2 from future backlog into completed migration notes during apply.
- **Trade-off:** R05 does not add screenshot assertions, so subtle visual regressions still rely on human smoke until T06 lands. → **Acceptable:** T06 is already next in queue and explicitly depends on post-redesign baseline.

## Migration Plan

1. Audit remaining `#fff` and hex-based class tints in runtime CSS.
2. Add `--class-N-tint` tokens under `:root` and replace affected selectors with token references.
3. Update DESIGN.md polish-pass section and `color-tokens` delta spec.
4. Run `task lint`, targeted/unit/integration coverage as needed, `openspec validate r05-hex-literal-audit-and-migration --json`, then `refresh-for-test` smoke.

Rollback: revert CSS/doc/spec changes together. No data migration, no schema change, no persistent state impact.

## Open Questions

- None blocking. If smoke shows a specific control needs stronger separation than `--surface`, handle as explicit selector-level exception during apply instead of inventing a new global token.
