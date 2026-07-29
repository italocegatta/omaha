## 1. CSS token re-derivation (`app.css :root`)

- [x] 1.1 Re-derive `--accent` to `oklch(0.68 0.20 152)` (was `0.68 0.13 150`)
- [x] 1.2 Re-derive `--accent-hover` to `oklch(0.74 0.20 152)` (preserve lightness lift pattern)
- [x] 1.3 Re-derive `--positive` to `oklch(0.79 0.19 145)` (was `0.70 0.16 145`)
- [x] 1.4 Re-derive `--negative` to `oklch(0.69 0.20 25)` (was `0.70 0.18 25`)
- [x] 1.5 Re-derive `--class-3` to `oklch(0.72 0.18 350)` (was `0.72 0.18 25`) — magenta-red hue shift
- [x] 1.6 Re-derive `--alert-warn` to `oklch(0.78 0.16 75)` (was `0.78 0.13 85`)
- [x] 1.7 Verify `--bg`, `--surface`, `--surface-sunk`, `--ink`, `--ink-muted`, `--border`, `--border-strong`, `--color-focus`, `--error-bg`, `--error-fg`, `--positive-ink`, `--negative-ink`, `--accent-ink` stay untouched (body warmth invariant)
- [x] 1.8 Add `/* F08 corrections (over F05) */` block comment under the `:root` block documenting the per-token deltas (mirror F05 pattern)

## 2. Python `_CLASS_COLORS` tuple alignment

- [x] 2.1 Replace the 8 hex literals in `src/omaha/routes/pages.py:686` with OKLCH strings mirroring `--class-1..8` post-F08 values
- [x] 2.2 Replace the 8 hex literals in `src/omaha/audit/inventory.py:99` with the same OKLCH strings
- [x] 2.3 Verify `src/omaha/routes/imports.py:411` continues to consume `_CLASS_COLORS` from `routes.pages` (no change needed beyond tuple content)
- [x] 2.4 Add `import` for OKLCH parser if the test assertions need it (optional — string equality may suffice)

## 3. Test extension (`tests/test_dark_mode_tokens.py`)

- [x] 3.1 Add assertion: `--class-3` hue ≥ 320° distant from `--negative` hue (post-F08: 350 vs 25, gap 325°)
- [x] 3.2 Add assertion: `--positive` lightness ≥ 0.74 (post-F08: 0.79)
- [x] 3.3 Add assertion: `lightness(--positive) > lightness(--accent)` (post-F08: 0.79 > 0.68)
- [x] 3.4 Add assertion: `hue(--positive) - hue(--accent) ≥ 6°` (post-F08: 145 vs 152, gap 7°)
- [x] 3.5 Add parity assertion: `_CLASS_COLORS[2]` (Python tuple) parses to the same OKLCH as `--class-3` (kills the hex-vs-OKLCH drift)
- [x] 3.6 Add parity assertion: all 8 `_CLASS_COLORS[i]` entries parse to valid OKLCH strings (zero hex literals remaining)
- [x] 3.7 Audit `tests/test_audit_color_resolver.py` for hex-vs-OKLCH assertions; update any that reference the old hex literals (no update needed — `test_apply_brightness_channels` uses `#0a66c2` as arbitrary input for the brightness function, not as an assertion on `_CLASS_COLORS`)

## 4. Spec sync (`openspec/specs/color-tokens/spec.md`)

- [x] 4.1 Promote the delta MODIFIED × 3 from `openspec/changes/f08-palette-overhaul-v2/specs/color-tokens/spec.md` into the canonical spec file at `openspec/specs/color-tokens/spec.md` (already done during initial archive 2026-07-07 — delta was synced to `openspec/specs/color-tokens/spec.md` with 3 MODIFIED requirements + Purpose section)
- [x] 4.2 Verify the 3 requirements retain their Purpose + scenario shape (no ADDED, no REMOVED)
- [x] 4.3 Run `openspec validate color-tokens --json` to confirm `valid: true` post-sync (run 2026-07-07; returns `valid: true` with 1 INFO non-blocking about requirement text length)

## 5. DESIGN.md sync

- [x] 5.1 Rename §"Tokens (current — post F05)" to §"Tokens (current — post F08)"
- [x] 5.2 Update the token table with the new OKLCH values + re-measured contrast ratios against `--bg` (accent 5.3→7.1, accent-hover 6.6→8.8, accent-ink 5.5→7.1, positive 7.6→10.4, positive-ink 7.7→10.4, negative 5.4→6.2, negative-ink 5.5→6.2; --alert-warn added as 9.2:1)
- [x] 5.3 Update the §"Class swatches" table: swatch 3 changes from `oklch(0.72 0.18 25)` to `oklch(0.72 0.18 350)` (contrast 6.0→6.9); document the hue gap rationale
- [x] 5.4 Add `## F08 corrections (over F05)` block under the token table mirroring the F05 block pattern
- [x] 5.5 Update §"Accent rationale" to reflect the D02 register (positive L > accent L signal hierarchy)
- [x] 5.6 Demote §"Target register (D02)" block to historical once F08 lands (becomes part of migration path)

## 6. Render verification

- [ ] 6.1 Run `task lint` (ruff + prek hooks)
- [ ] 6.2 Run `task test-unit` (271 pass / 2 skip baseline — new assertions must close, no regression)
- [ ] 6.3 Run `task test-integration` (369 pass / 2 skip baseline — no regression)
- [ ] 6.4 Run `openspec validate f08-palette-overhaul-v2 --json` — confirm `valid: true`
- [ ] 6.5 Run `refresh-for-test` skill: server `0.0.0.0:8000`, `db-reset` produces baseline (italo=6/48/47, ana=6/52/52), `/patrimonio` renders without console errors
- [ ] 6.6 Smoke-render the dashboard and verify visually: red class swatch (slot 3) reads as magenta-red, distinct from any loss number; gain numbers sit at L 0.79 fern-green, distinguishable from accent emerald; compare bar fills read cleanly on `--surface`

## 7. Archive

- [ ] 7.1 Run `openspec archive f08-palette-overhaul-v2 --yes` to move the change folder into `openspec/changes/archive/2026-07-XX-f08-palette-overhaul-v2/` and sync the spec delta
- [ ] 7.2 Confirm `openspec list --specs` shows `color-tokens` requirementCount updated (8 pre-F08 → post-F08 same shape, 3 MODIFIED)
- [ ] 7.3 Update `openspec/roadmap.md` F08 slice: status → `Archived`; mark all 4 progress gates (Proposed / Applying / Applied / Archived)
- [ ] 7.4 Document any post-implementation reality-check deltas in the F08 slice body (what changed, unexpected issues, follow-ups — T06 + R05 may depend on F08 landing)
