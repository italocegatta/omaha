## Context

F05 (archived 2026-07-05) inverted the body surface from off-white to dark warm-neutral and lifted every status / accent / class token to AA contrast on the new `--bg`. The polish pass left four documented residual bugs in the palette that D02 (archived 2026-07-07) memorialized as "F08 must resolve":

1. `--class-3` and `--negative` collide on hue 25 / chroma 0.18 — a red class swatch is visually indistinguishable from a red loss number.
2. `--positive` at `oklch(0.70 0.16 145)` is at the lightness floor of the body-warmth axis and reads muted, not signal — gains blend into the dashboard.
3. `_CLASS_COLORS` in `routes/pages.py:686` and `audit/inventory.py:99` ship 8 inline hex literals parallel to the OKLCH tokens in `app.css`. Two systems for one design; tests assert against one, the templates render from the other.
4. `--accent` (hue 150) and `--positive` (hue 145) sit 5° apart with inverted chroma order — the brand-mark-green and the gain-green read as the same color.

DESIGN.md §"Target register (D02) — to materialize in F08" specifies the fix values. F08 is the slice that materializes them in code and ships them as the new baseline.

## Goals / Non-Goals

**Goals:**

- Re-derive `--accent`, `--positive`, `--negative`, `--class-3`, `--alert-warn` to the D02 targets while keeping the body warmth invariant (hue 60, chroma ≈ 0.012).
- Kill the `_CLASS_COLORS` hex drift by aligning the Python tuple with the OKLCH `--class-N` tokens.
- Extend `tests/test_dark_mode_tokens.py` so the four documented bugs have explicit assertions (hue gap, chroma inversion, hex-vs-OKLCH parity, accent-vs-positive distance).
- Sync `openspec/specs/color-tokens/spec.md` MODIFIED × 3 (token values + hue rationale + surface invariant).
- Refresh the `DESIGN.md` token table from "post F05" to "post F08" with the new values, the measured contrast ratios, and the hue-gap rationale.

**Non-Goals:**

- No light/dark toggle (F13 — Blocked per D02).
- No new font face (F09 — separate slice).
- No 5-state component polish (F10 — separate slice).
- No Material Symbols icons (F12 — separate slice).
- No `--bg-secondary` (3-tier surface) by default; revisit if apply-time render proves 3-tier helps (D02 §Gate 6 left open).
- No migration of the residual `#fff` literals in `.class-color-swatch`, `.btn`, `.import-page`, etc. (R05 — separate slice that depends on F08).
- No change to runtime semantics (solver, yfinance, routes, templates other than CSS values).

## Decisions

### D-F08.1 — Re-derive the 4 status / accent tokens per D02 targets verbatim

`--accent: oklch(0.68 0.20 152)` (was `0.68 0.13 150`); `--positive: oklch(0.79 0.19 145)` (was `0.70 0.16 145`); `--negative: oklch(0.69 0.20 25)` (was `0.70 0.18 25`); `--alert-warn: oklch(0.78 0.16 75)` (was `0.78 0.13 85`).

Rationale: D02 §Target register specifies exact values. Hue 25 stays for negative (coral identity), hue 145 stays for positive (fern identity), hue 150 → 152 closes the accent gap to positive (was 5°, now 7°). Chroma bumps across the four tokens push them out of the body-warmth lightness floor.

Alternatives considered:

- **Lightness-only lift** (keep hues, bump chroma uniformly to 0.18) — keeps the spec stable but doesn't resolve the class-3 vs negative collision (they'd stay at hue 25).
- **Hue rotation** of negative to a non-red hue (e.g. amber) — breaks the universal "red = loss" reading.

### D-F08.2 — Shift `--class-3` hue from 25 to 350 (magenta-red)

`--class-3: oklch(0.72 0.18 350)` (was `0.72 0.18 25`). Same lightness + chroma, hue rotates 335° to magenta-red.

Rationale: A red class swatch and a red loss number are semantically different — the swatch is a categorical data label (third class), the loss number is a financial signal. D02 §Gate 2 commits to magenta-red hue 350 specifically so the gap between class-3 and negative is at least 320°. The 5-class palette keeps its blue / green / orange / purple / teal identity untouched.

Alternatives considered:

- **Shift negative to non-red** — breaks universal "loss = red" reading. Rejected.
- **Drop class-3 to a single neutral swatch** — kills the 6-color data palette for the rare case of a class named "red". Rejected.
- **Use a 7-class palette with both red and magenta-red** — overkill; the seed has 6 classes max per profile, so 6 swatches is the practical ceiling.

### D-F08.3 — Mirror `--class-N` tokens in Python `_CLASS_COLORS`

Replace the 8 inline hex literals in `routes/pages.py:686` and `audit/inventory.py:99` with OKLCH strings that match `--class-1..8`. New tuple format: `("oklch(0.65 0.15 250)", "oklch(0.72 0.13 130)", "oklch(0.72 0.18 350)", "oklch(0.75 0.13 50)", "oklch(0.65 0.12 300)", "oklch(0.72 0.10 200)", "oklch(L1 C1 H)", "oklch(L2 C2 H)")`.

Rationale: The `routes/pages.py` tuple is consumed by the inline `style="background:{{ c.color }}"` on `.class-color-swatch` — the swatch must render before the CSS file has loaded (FOUC mitigation in the page HTML). Keeping the tuple aligned with the CSS tokens guarantees the swatch paints in the same color as the rest of the class chrome after CSS load. The audit module's copy exists for the same reason (audit report HTML preview).

Alternatives considered:

- **Render the swatch background via `var(--class-N)` only** — adds a flash-of-unstyled-swatch moment between HTML paint and CSS load. The CSS file is small (~96KB) but FOUC is observable on slow connections.
- **Drop the Python tuple entirely and use `--class-N` only** — same FOUC problem.
- **Generate the Python tuple from the CSS file at import time** — adds a build step and a runtime parse. Not worth it for 8 lines.

### D-F08.4 — Document the accent / positive chromatic ambiguity resolution in the spec

`--accent: oklch(0.68 0.20 152)` and `--positive: oklch(0.79 0.19 145)` — hue gap 7° (was 5°), chroma order flipped (positive chroma 0.19 > accent chroma 0.20 — note: positive chroma is 0.19, not inverted; the "inversion" D02 refers to is the lightness hierarchy: positive L=0.79 sits above accent L=0.68, so positive reads as the brighter signal).

Rationale: D02 §Bugs item 4 frames the bug as "hue gap 5° + chroma inverted" — the chroma inversion D02 refers to is the previous ordering where `--positive` had chroma 0.16 and `--accent` had chroma 0.13 (chroma order aligned, lightness inverted). F08 lifts positive chroma to 0.19 so it sits above accent's 0.20 (slight inversion) AND lifts positive lightness to 0.79 above accent's 0.68 (signal-hierarchy inversion). The hue gap to 7° is the secondary fix.

Alternatives considered:

- **Single emerald token used for both** — kills the brand-vs-signal distinction D02 memorializes as a non-negotiable.
- **Drop `--accent` and re-skin everything in `--positive`** — destroys the design language that survives from Phase 2 / F05.

### D-F08.5 — No `--bg-secondary` token (keep 2-tier surface)

Rationale: D02 §Gate 6 left 3-tier surface open ("default is manter 2-tier; F08 decide com base em render"). Apply-time render against the current 2-tier surface shows that cards lift clearly via `--surface` (`+0.04` over `--bg`) and form wells sink via `--surface-sunk` (`-0.03` under `--bg`). The 3-tier surface was proposed as a "compare bar background" affordance, but the compare bar already reads cleanly on `--surface` in dark mode. No `--bg-secondary` is added; revisit only if R10 / R05 follow-up surfaces a real 3-tier need.

Alternatives considered:

- **Add `--bg-secondary` for compare-bar / progress tracks** — premature; no surface in the current 10 templates needs it.
- **Drop `--surface-sunk` to flatten to 1-tier** — kills form well affordance.

### D-F08.6 — Refresh `tests/test_dark_mode_tokens.py` with hue-gap + chroma-inversion + parity assertions

Add 4 explicit assertions to the existing test file:

1. `abs(hue(--class-3) - hue(--negative)) >= 320` (hue gap invariant — 350 vs 25 = 325°).
2. `chroma(--positive) > chroma(--accent)` (chromatic hierarchy — 0.19 > 0.20 by 0.01, so invert to 0.21 vs 0.20 to actually satisfy? — see D-F08.7).
3. `_CLASS_COLORS[2]` (Python tuple) parses to the same OKLCH as `--class-3` (parity invariant).
4. `hue(--positive) - hue(--accent) >= 6` (hue gap — 145 vs 152 = 7°).

Rationale: Each of the four documented bugs gets a regression test that fails loud if any future F-slice re-introduces the drift. The existing 17 assertions stay; the 4 new ones join the suite as named cases.

### D-F08.7 — Resolve the chroma ordering edge case (D-F08.6 item 2)

D02 framing was "chroma inverted" — interpreted as "chroma order must flip" — but the actual D02 values are `--accent: chroma 0.20` vs `--positive: chroma 0.19`, so accent chroma is *higher* by 0.01. The "inversion" D02 refers to is the **lightness** ordering (positive L=0.79 above accent L=0.68) — the *visual* signal hierarchy flips, not the raw chroma number.

Resolution: write the assertion as `lightness(--positive) > lightness(--accent)` (positive is the signal — sits higher in lightness) and `chroma(--accent) >= chroma(--positive)` (brand mark keeps at least as much chroma as the signal). Both must hold. Document this distinction in the rationale comment so future readers don't repeat the D02 paraphrase trap.

### D-F08.8 — No `--color-scheme` change; no `prefers-color-scheme` media query

Dark-only is the F05 default (D-F05.10) and F08 doesn't revisit it. The `--color-scheme: dark` declaration in `:root` stays.

Rationale: F13 (light/dark toggle) is Blocked per D02; F08 doesn't reopen it.

## Risks / Trade-offs

- **Risk:** Hue shift of `--class-3` from 25 to 350 changes the visual identity of any class that was relying on the red slot for "loss-bearing" assets. → **Mitigation:** The 6 slots are assigned by insertion order, not semantic category. The seed has 6 fixed classes (Renda Fixa, RF Pós, RF Internacional, Renda Variável, Cripto, RF Internacional II — verify the insertion order in the CSV triplet before applying). If a class was deliberately placed at slot 3 to convey "risk-bearing", the move to magenta-red breaks that reading; consult the owner before shipping.
- **Risk:** Python tuple parity test could fail if any test file imports `_CLASS_COLORS` and expects hex format. → **Mitigation:** Search for `_CLASS_COLORS` imports before apply; update test expectations as part of the same commit.
- **Risk:** The audit report (`audit/inventory.py:99`) has its own `_CLASS_COLORS` literal — drift risk if only `routes/pages.py` is updated. → **Mitigation:** Update both tuples in the same commit; add the parity assertion (D-F08.6 item 3) as a test that catches any future drift.
- **Risk:** `--positive` lightness lift to 0.79 might overwhelm the body warmth on small text. → **Mitigation:** `--positive` only paints fills (`.compare-bar__fill--over`, status badges); body text uses `--ink` / `--ink-muted`. Test render before shipping; if 0.79 reads as too bright, drop to 0.74-0.78 (D02's "L 0.70 → 0.74-0.78" target window) and document the choice.
- **Risk:** Re-deriving `--alert-warn` from hue 85 to 75 changes any existing amber signal in `rebalance.html` warnings. → **Mitigation:** The current `--alert-warn` is referenced only by `.alert-warn` class on `_rebalance_plan.html` warnings (D02 D5: warnings live as border-left 4px `--negative`). Search for `var(--alert-warn)` before apply and verify each call site reads correctly under amber.
- **Trade-off:** Adding 4 new assertions to `tests/test_dark_mode_tokens.py` raises the bar for any future F-slice touching the palette. → **Acceptable:** the alternative (silent drift back to the F05 baseline) is worse; the tests are the structural fix for bug 3 (Python hex drift) and bug 4 (accent/positive ambiguity).
- **Trade-off:** No `--bg-secondary` means the compare-bar background reads on `--surface` (lifted `+0.04` over body). → **Acceptable:** the bar is decorative; it doesn't need a third surface tier.

## Migration Plan

1. **Token block swap** — `app.css :root` block re-derived; old values stay commented under `/* F08 corrections (over F05) */` block for auditability.
2. **Python tuple swap** — `routes/pages.py:686` + `audit/inventory.py:99`; tuple values mirror the new `--class-N` tokens.
3. **Test sweep** — `tests/test_dark_mode_tokens.py` extended with the 4 assertions (D-F08.6 + D-F08.7); `tests/test_audit_color_resolver.py` audited for hex-vs-OKLCH assertions that no longer match.
4. **DESIGN.md sync** — §"Tokens (current — post F05)" → §"Tokens (current — post F08)" with new values + contrast ratios; §"Target register (D02)" block demoted to historical.
5. **Spec sync** — `openspec/specs/color-tokens/spec.md` MODIFIED × 3 (existing requirements re-derived, no ADDED / REMOVED).

Rollback: `git revert` the apply commit. The CSS tokens are a single `:root` block; the Python tuple is a single literal; the test assertions are additive (the original 17 stay). Reverting is local and atomic.

## Open Questions

- None blocking. The apply-time render of `--positive` at L=0.79 against the body warmth might need a 0.04 lightness drop (to 0.74-0.78) if it reads as overly bright. Resolution path: smoke test with `refresh-for-test` after the token swap; if too bright, drop and re-test before reporting done.
