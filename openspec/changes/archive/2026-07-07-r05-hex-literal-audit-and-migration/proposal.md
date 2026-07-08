## Why

F05 inverted body from off-white to dark warm-neutral, and F08 re-derived core palette tokens, but `app.css` still carries two pre-dark-mode leftovers: hardcoded `background: #fff` surfaces and 8 import-preview tints mixed from inline hex values. On dark body these sites render as isolated white islands or over-saturated class chips, so residual cleanup now has higher leverage than new visual work.

## What Changes

- Replace remaining `background: #fff` / `#ffffff` UI surfaces in `src/omaha/static/app.css` with token-backed surfaces (`var(--surface)` unless a specific sunk/lifted surface is required).
- Introduce explicit class-tint tokens (`--class-1-tint` ... `--class-8-tint`) derived from the post-F08 `--class-N` palette for dark-surface import preview chips.
- Rebind `.import-class-cell--cls-{0..7}` to the class-tint tokens instead of mixing inline hex literals.
- Update `DESIGN.md` polish-pass notes so residual items 1-2 become delivered behavior instead of future backlog.
- Sync `openspec/specs/color-tokens/spec.md` with one added requirement covering the tint-token family and its dark-surface use.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `color-tokens`: add derived `--class-N-tint` tokens for import-preview chips so class color surfaces stay token-driven and legible on the dark `--surface`.

## Impact

- `src/omaha/static/app.css` — residual `#fff` surfaces and `.import-class-cell--cls-*` tint rules migrate to design tokens.
- `openspec/specs/color-tokens/spec.md` — delta `ADDED` requirement for `--class-N-tint` token family and import-preview usage.
- `DESIGN.md` — polish-pass backlog items 1-2 move from planned to done; migration notes describe the tint-token layer.

No route, model, seed, auth, solver, or provider behavior changes.
