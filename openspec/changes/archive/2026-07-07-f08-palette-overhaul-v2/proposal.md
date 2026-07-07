## Why

The F05 dark-mode palette swap (archived 2026-07-05) inverted `--bg` from off-white to dark warm-neutral but left four concrete palette bugs documented in the 2026-07-06 redesign session:

1. **Class-3 vs negative collision** — both sit at hue 25 / chroma 0.18, so a red class swatch and a loss number are chromatically indistinguishable.
2. **Positive without punch** — `--positive: oklch(0.70 0.16 145)` sits at the body-warmth lightness floor and reads as muted dark-green rather than a "data signal" — gains blend into the dashboard.
3. **Python hex drift in `_CLASS_COLORS`** — `routes/pages.py:686` still ships 8 inline hex literals (`#0a66c2`, `#2e7d32`, `#c62828`, ...) while `app.css` carries the parallel OKLCH tokens. Two systems for one design.
4. **Accent vs positive hue ambiguity** — hue gap of 5° (accent hue 150, positive hue 145) plus inverted chroma order means brand-mark-green and gain-green read as the same color.

D02 (archived 2026-07-07) chose Status Invest maximal as the register to pursue and memorialized the fix targets in DESIGN.md §"Target register (D02) — to materialize in F08". F08 is the slice that materializes the D02 decision in code.

## What Changes

- Re-derive `:root` color tokens in `src/omaha/static/app.css` per the D02 target register: emerald `--accent: oklch(0.68 0.20 152)`, fern-leaning `--positive: oklch(0.79 0.19 145)`, coral `--negative: oklch(0.69 0.20 25)`, amber `--alert-warn: oklch(0.78 0.16 75)`, class-3 hue shifted to **350 magenta-red** to resolve the collision with `--negative`.
- Replace the 8 hex literals in `_CLASS_COLORS` (`src/omaha/routes/pages.py:686`) with OKLCH strings that mirror the `--class-N` tokens, killing the dual-system drift.
- Update `tests/test_dark_mode_tokens.py` to assert the new token values, the class-3 / negative hue gap (≥ 320°), and the accent / positive chroma inversion (positive chroma > accent chroma).
- Add `--bg-secondary` (3-tier surface) if the D02 "default = manter 2-tier" is revisited; default is keep 2-tier (no token added unless apply-time render proves 3-tier helps).
- Sync `DESIGN.md` §"Tokens (current — post F05)" table from "post F05" labels to "post F08" with new OKLCH values, hue-gap rationale, and contrast ratios re-measured against the dark `--bg`.
- Sync `openspec/specs/color-tokens/spec.md` requirements to the re-derived token values (MODIFIED × 3 — same shape, new numbers; no ADDED / REMOVED).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `color-tokens`: re-derive the 3 existing requirements against the new D02 register — body warmth invariant preserved (hue 60, chroma ≈ 0.012), class swatches resolve the hue-3 vs negative collision, accent / positive pair gains hue gap and chroma inversion, all pairs stay ≥ AA contrast on the dark `--bg`.

## Impact

- `src/omaha/static/app.css` — `:root` block (14 tokens re-derived; `--alert-warn` shifts to amber 0.78/0.16/75; `--class-3` hue 25 → 350).
- `src/omaha/routes/pages.py` — `_CLASS_COLORS` tuple (8 inline hex → 8 inline `oklch(...)` strings mirroring `--class-1..8`).
- `src/omaha/routes/imports.py` — line 52 imports `_CLASS_COLORS`; no behavioural change beyond the color string itself.
- `src/omaha/audit/inventory.py` — line 99 has its own `_CLASS_COLORS` literal (parity drift with `routes/pages.py`); align with the canonical tuple.
- `tests/test_dark_mode_tokens.py` — assertions extended for new values, hue gap, chroma inversion.
- `tests/test_audit_color_resolver.py` — may need update if it asserts specific hex values from the old palette.
- `openspec/specs/color-tokens/spec.md` — delta `MODIFIED` × 3 (token values, hue rationale, surface invariant).
- `DESIGN.md` — §"Tokens (current — post F05)" → §"Tokens (current — post F08)" with new numbers; §"Target register (D02)" block demoted to historical once F08 lands.

No runtime logic change. Solver, rebalance engine, yfinance provider, routes, templates other than CSS, and Alembic migrations stay untouched. Single domain = visual surface; cap-1 Applying inside the visual queue (F08 + F09 + F10 + F12 can co-exist, but F08 alone if the critical-area cap is read as "visual surface").