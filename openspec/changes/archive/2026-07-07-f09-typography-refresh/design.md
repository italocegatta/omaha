## Context

F05 (dark-mode palette, archived 2026-07-05) re-derived the `:root` color tokens against a dark warm-neutral `--bg` but left typography untouched. The current `base.html` Google Fonts URL is:

```
https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@600&display=swap
```

— Inter at fixed weights 400/500/600 for body and `Source Serif 4` 600 for the display face. `app.css` carries ~6 `font-family: "Source Serif 4", "IBM Plex Serif", Georgia, serif;` declarations targeting `.portfolio-stat-value`, `.profile-name`, `.tab-nav__btn`, `.patrimonio-section-title`, `.app-header__logo`, and the `.profile-stat-value` selector. The body carries only `font-feature-settings: "tnum"` — the three stylistic sets D02 specified (`cv01`, `ss01`, `ss02`) are not enabled.

D02 (archived 2026-07-07) settled two open questions that unblock this slice:

- **D02 §Gate 3** — display face = Red Hat Display (sans, **not** serif). The serif vs sans debate is closed; Source Serif 4 must leave the build.
- **D02 §Typography** — body uses Inter with `tnum, cv01, ss01, ss02` feature-settings. `tnum` keeps numbers tabular, `cv01` renders 1 with a serif base, `ss01` keeps 6 and 9 open, `ss02` distinguishes 0 from O.

`DESIGN.md §Typography` (current) still describes Source Serif 4 as the display face and lists only `tnum` in the body feature-settings. The DESIGN.md `§"Target register (D02)"` block is the source of truth for what F09 ships.

No runtime logic touches this slice. The change is bounded to one HTML file (`base.html`), one CSS file (`app.css`), one markdown doc (`DESIGN.md`), and one new test file (`tests/test_typography_tokens.py`). Visual surface = cap-1 Applying inside the visual queue (F08/F09/F10/F12 co-exist up to cap 2 global, cap 1 inside the visual queue).

## Goals / Non-Goals

**Goals:**

- Materialize D02 §Gate 3 + §Typography in code: display face = Red Hat Display 700+, body = Inter variable with all four feature-settings.
- Keep the runtime unchanged (no Python, no SQL, no route, no template logic).
- Land a single source of truth for typography (`openspec/specs/typography-tokens/spec.md`) so future palette/typography work doesn't drift.
- Surface a low-cost regression test (`tests/test_typography_tokens.py`) that pins the contract — next time someone edits `base.html` or `app.css` the assertions catch a reintroduction of Source Serif 4.

**Non-Goals:**

- Color-token work (F08 archive covers that — separate slice).
- Component state vocabulary (F10 Ready — separate slice).
- Material Symbols icons (F12 Ready — separate slice).
- Light/dark toggle (F13 Blocked — out of scope).
- Self-hosting fonts via `static/fonts/` (D-F09.1 below — deferred to a future owner-driven slice; Google Fonts is the default for now).
- Loading additional weight axes of Red Hat Display (D-F09.3 below — 700 + 800 covers the hero numerals and the active tab; 400 not needed).

## Decisions

### D-F09.1 — Stay on Google Fonts (no self-host)

The current build already uses `<link rel="stylesheet" href="https://fonts.googleapis.com/css2?…">`. Self-hosting Red Hat Display + Inter variable would require (a) downloading the WOFF2 files into `src/omaha/static/fonts/`, (b) generating a `@font-face` block in `app.css`, (c) adding a prek check that the static files exist, and (d) handling `font-display: swap` + `unicode-range` subsetting manually. The cost/benefit doesn't justify the change for a 4-slice visual redesign that already accepts Google Fonts as the default. **Decision:** keep Google Fonts for F09. Re-evaluate self-hosting in a future owner-driven slice if the project needs offline support or stricter CSP.

**Alternative considered:** `<link rel="preload" as="font">` for the WOFF2 files served by Google Fonts — measurable but marginal LCP win, adds complexity to the `<head>` and ties the build to the exact Google Fonts URL. Deferred.

### D-F09.2 — Load Inter as a variable font

The current URL uses fixed weights (`Inter:wght@400;500;600`). Variable fonts (one WOFF2 covering a continuous weight axis) are the recommended way to load Inter on the web today and have full feature-settings registry support. **Decision:** swap the URL to `Inter:wght@400..700` (the `..` syntax is Google Fonts' range syntax). This adds a 700 weight (handy for active tabs and bold callouts) without doubling the request count.

**Alternative considered:** keep fixed weights and just add `cv01, ss01, ss02` to the body — the four feature-settings do work on Inter's static weights (they're in Inter's OpenType feature registry). Rejected because variable gives us a cleaner URL, full feature-settings support, and a free extra weight.

### D-F09.3 — Red Hat Display weights: 700 + 800 only

D02 said "700+" — meaning 700 is the minimum, 800 is the maximum. Loading `400;500` of Red Hat Display is overkill because Red Hat Display only renders the hero numerals and the active tab text (two CSS selectors today). **Decision:** load `Red+Hat+Display:wght@700;800`. The 700 weight is the default for `.portfolio-stat-value` and active tabs; 800 is reserved for the portfolio hero's primary number if visual rhythm needs more presence (per `font-weight: 700 | 800` toggle in CSS).

**Alternative considered:** load the full variable range `wght@400..900`. Rejected as over-scope; can extend later if a new component demands it.

### D-F09.4 — Drop Source Serif 4 entirely from the build

Source Serif 4 currently appears in (a) the Google Fonts URL and (b) ~6 `font-family` declarations in `app.css`. The D02 register change is **sans display, not serif**. **Decision:** remove Source Serif 4 from the URL AND replace every `font-family: "Source Serif 4", ...` chain with `font-family: "Red Hat Display", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;`. The Inter fallback keeps the rendering readable while Google Fonts is still warming up.

**Alternative considered:** keep Source Serif 4 in the URL "just in case". Rejected because leaving dead font references makes future audits harder and the D02 §Gate 3 decision is explicit.

### D-F09.5 — Apply Red Hat Display to display-only selectors; body stays Inter

The 6 display selectors in `app.css` (`.portfolio-stat-value`, `.profile-name`, `.tab-nav__btn--active`, `.patrimonio-section-title`, `.app-header__logo`, `.profile-stat-value`) all flip to `Red Hat Display`. Body text (`<body>`, `<p>`, `<label>`, `<button>`, `<input>`, `.btn`, etc.) keeps `Inter`. Card body copy and table cells inherit Inter from body — no per-component overrides needed.

**Alternative considered:** apply Red Hat Display to `h1` / `h2` for consistency — rejected because the current build uses `.patrimonio-section-title` (a custom class) and there are no raw `<h1>` / `<h2>` in templates today. Reuse the existing class names rather than introduce element selectors.

### D-F09.6 — Add `preconnect` to `fonts.gstatic.com`

Google Fonts serves the CSS from `fonts.googleapis.com` and the actual font files (WOFF2) from `fonts.gstatic.com`. The current `base.html` only preconnects to `fonts.googleapis.com`. **Decision:** add a second `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` (the `crossorigin` attribute is required for font fetches because the browser uses CORS for the WOFF2 response).

**Alternative considered:** keep the single preconnect — works in practice, but loses ~50–100ms on the first paint of large numerals. With the visual redesign putting Red Hat Display on the portfolio hero, the LCP is exactly the hero numeral. Adding the preconnect is cheap and observable.

### D-F09.7 — `display=swap` is already set; keep it

The current URL ends in `&display=swap`. `font-display: swap` lets the browser render body text immediately in the system fallback while the WOFF2 loads, then swap. **Decision:** keep `display=swap`. No FOIT (flash of invisible text) risk for the body; the hero numeral will briefly render in `Inter` until Red Hat Display swaps in, which is acceptable and visually coherent (both are sans).

**Alternative considered:** `display=optional` — would render system fallback only and skip the swap if the font hasn't loaded by the LCP deadline. Rejected because the existing tests + monitoring are calibrated against the swap pattern; changing the default adds a class of issues not worth the marginal LCP win.

### D-F09.8 — Test coverage via a new `tests/test_typography_tokens.py`

The existing `tests/test_dark_mode_tokens.py` covers color tokens (WCAG pairs, contrast ratios, OKLCH bodies). Extending it to typography would mix two concerns. **Decision:** create a separate `tests/test_typography_tokens.py` with the following assertions:

1. The Google Fonts URL in `base.html` contains `family=Red+Hat+Display:wght@700;800`.
2. The Google Fonts URL in `base.html` does **not** contain `family=Source+Serif+4`.
3. The Google Fonts URL in `base.html` ends in `&display=swap`.
4. `<link rel="preconnect" href="https://fonts.googleapis.com">` is present.
5. `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` is present.
6. The `body` selector in `app.css` declares `font-feature-settings` with all four values: `tnum`, `cv01`, `ss01`, `ss02` (substring match, order-insensitive).
7. `app.css` contains **zero** `font-family: "Source Serif 4"` declarations (regex search).
8. `app.css` declares `font-family: "Red Hat Display"` on at least the 6 known display selectors.

Test file goes into `tests/test_typography_tokens.py` (unit marker; no DB). `tests/conftest.py::_UNIT_FILES` is extended to include the new file (per PRD §4.6 — explicit allow-list, no pattern matching).

**Alternative considered:** merge the typography assertions into `tests/test_dark_mode_tokens.py` — rejected because the two test files would then have to share imports for `Path` to `app.css` and `base.html` and would drift apart as the design evolves. Two separate files, one concern each.

## Risks / Trade-offs

- **[Risk] Google Fonts outage or rate limit renders the dashboard with system fallback only.** → Mitigation: D-F09.4 keeps Inter as the first non-display fallback, so the page is still readable (sans body + system-fallback numerals). The hero numeral may look slightly different from the design target during an outage, but no content is lost. Self-hosting (deferred per D-F09.1) would eliminate this risk entirely; revisit if the project ships offline.
- **[Risk] Variable font load + extra `preconnect` slightly increases the `<head>` weight.** → Mitigation: the URL change is a net reduction (one variable WOFF2 instead of three fixed-weight WOFF2s); the second `preconnect` adds one DNS + TLS handshake (~100–200ms one-time cost, amortized). Total `<head>` payload goes from ~3.5KB to ~3.2KB CSS + 1 extra `<link>` tag.
- **[Risk] Red Hat Display doesn't ship `tnum` for tabular figures in 700 weight.** → Mitigation: the hero numerals are tabular by virtue of being in a fixed-width layout (the `.portfolio-stat-value` has `min-width` set in the partial); the visual rhythm survives even without `tnum` on the display face. Verify with a browser render before archiving; if tabular figures break, scope the `font-feature-settings` to the display selectors as well (D-F09.5 escape hatch).
- **[Risk] F09 lands before F08 and the new palette changes contrast assumptions for Red Hat Display's numerals.** → Mitigation: Red Hat Display was designed against light backgrounds; against the dark `--bg` of F05 the white numerals stay at high contrast regardless of the F08 palette adjustments (accent / positive / negative are status colors, not body text). No F08 dependency; F09 can land in parallel with F08 / F10 / F12.
- **[Trade-off] Single global feature-settings on `body` vs. per-component overrides.** → Choosing global means the four feature-settings apply everywhere (including body text where `cv01` slightly changes the "1" glyph). This is intentional — D02 specified `cv01` for the body, not for specific components. Per-component overrides would add 4× the surface area to maintain.

## Migration Plan

Apply order:

1. **Sync docs first** — update `DESIGN.md` §Typography (Red Hat Display + 4 feature-settings), mark §"Target register (D02) — to materialize in F08/F09" as resolved for F09 portion.
2. **Update `src/omaha/templates/base.html`** — extend Google Fonts URL with `Red+Hat+Display:wght@700;800`, drop `Source+Serif+4`, add second `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`.
3. **Update `src/omaha/static/app.css`** — extend `body` `font-feature-settings` to include `cv01`, `ss01`, `ss02`; swap every `font-family: "Source Serif 4", ...` chain for `font-family: "Red Hat Display", "Inter", ...` fallback chain.
4. **Add `tests/test_typography_tokens.py`** — 8 assertions per D-F09.8; register in `tests/conftest.py::_UNIT_FILES`.
5. **Add `openspec/specs/typography-tokens/spec.md`** — 5 ADDED requirements per the proposal's Capabilities section.
6. **Verify** — `task test-unit` (must include the new test file) + `task test-integration` + `task test-bdd`; visual smoke via `refresh-for-test` (open `/patrimonio`, confirm hero numeral renders in Red Hat Display).

Rollback: single PR revert (the only files touched are `base.html`, `app.css`, `DESIGN.md`, the new test file, `conftest.py`, the new spec). No migration / data-shape change.

## Open Questions

None blocking. Two deferred items, neither required for F09:

- **Self-hosting Red Hat Display + Inter** — deferred per D-F09.1; revisit if owner asks for offline support or stricter CSP.
- **Red Hat Display 400 / 500 / 600 weights** — deferred per D-F09.3; add to the URL if a future slice needs lighter display text.
