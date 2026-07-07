## Why

The F05 dark-mode palette swap (archived 2026-07-05) and D02 design-register decision (archived 2026-07-07) chose Status Invest maximal as the visual register but stopped short of materializing the typography half of that decision. Today the dashboard still loads Source Serif 4 as the display face (`<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@600&display=swap">`) and `body` carries only `font-feature-settings: "tnum"` — two of the four feature-settings D02 specified are still missing (`cv01`, `ss01`, `ss02`).

D02 §Gate 3 settled the open question: display face = **Red Hat Display 700+** (sans, not serif). D02 §Typography also specified the Inter variable body with `tnum, cv01, ss01, ss02` to disambiguate tabular figures (`tnum`), the 1/serif base (`cv01`), open 6/9 (`ss01`), and zero/O (`ss02`). F09 is the slice that materializes both halves in code.

## What Changes

- Swap the display face in `src/omaha/templates/base.html` from Source Serif 4 (serif) to **Red Hat Display 700+** (sans). Google Fonts URL gains `Red+Hat+Display:wght@700;800`; the Source Serif 4 family is removed.
- Extend the body `font-feature-settings` declaration in `src/omaha/static/app.css` from `"tnum"` to `"tnum", "cv01", "ss01", "ss02"` so the Inter variable body picks up tabular figures + the 1/serif base + open 6/9 + zero/O disambiguation.
- Update the existing `font-family: "Source Serif 4", ...` declarations in `app.css` (currently applied to `.portfolio-stat-value`, `.profile-name`, `.tab-nav__btn`, etc.) to `font-family: "Red Hat Display", "Inter", ...` so the visual register is consistent across the portfolio hero and the active tab.
- Sync `DESIGN.md` §Typography to reflect the new display face + the four feature-settings, demote the §"Target register (D02)" red hat reference to historical once F09 lands.
- Add `openspec/specs/typography-tokens/spec.md` — new capability describing the display face + body feature-settings + the Google Fonts loading contract (so future palette/typography work has a single source of truth).

## Capabilities

### New Capabilities

- `typography-tokens`: the runtime typography contract — display face is Red Hat Display 700+ (sans, not serif), body is Inter variable with `tnum, cv01, ss01, ss02` feature-settings, font loading is a single Google Fonts `<link>` in `base.html` declaring both families, no serif fallback in the font-family chain, and any future change to display face or feature-settings must be reflected in both `base.html` and `app.css` together.

### Modified Capabilities

(none — no existing typography capability to modify; `color-tokens` already landed the palette half in F08 archive)

## Impact

- `src/omaha/templates/base.html` — Google Fonts `<link>` URL extended with `Red+Hat+Display:wght@700;800`, Source Serif 4 family dropped.
- `src/omaha/static/app.css` — `body` rule gains `font-feature-settings: "tnum", "cv01", "ss01", "ss02"`; all `font-family: "Source Serif 4", ...` chains swapped to `font-family: "Red Hat Display", "Inter", ...`.
- `DESIGN.md` — §Typography rewritten to name Red Hat Display as the display face and Inter variable as the body with all four feature-settings.
- `openspec/specs/typography-tokens/spec.md` — new spec (5 ADDED requirements: display face is Red Hat Display 700+, body feature-settings include `tnum, cv01, ss01, ss02`, Google Fonts URL is the single font source, no serif in the display chain, body and display stay synchronized via `base.html` + `app.css` pair).

No runtime logic change. Solver, rebalance engine, yfinance provider, routes, templates other than `base.html`, Alembic migrations, and the entire Python backend stay untouched. Single domain = visual surface; cap-1 Applying inside the visual queue (F08 + F09 + F10 + F12 can co-exist, but F09 alone if the critical-area cap is read as "visual surface").
