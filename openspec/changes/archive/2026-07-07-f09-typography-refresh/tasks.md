## 1. Sync DESIGN.md

- [x] 1.1 Update `DESIGN.md` §Typography to declare Red Hat Display 700+ as the display face and Inter variable as the body with the four feature-settings (`tnum, cv01, ss01, ss02`) — already aligned post-D02; F09 framed as "current = sans display" + 4-selector scope
- [x] 1.2 Mark the §"Target register (D02) — to materialize in F08/F09" typography portion as resolved for F09 (keep F08 palette portion as still-resolved-then-archived) — line 176 updated from "F09 materializa; até lá, o current é serif" → "F09 archived 2026-07-07 — current = sans display"
- [x] 1.3 Update §Component inventory to reference the new display selectors (`font-family: "Red Hat Display"`) and body (`font-family: "Inter"` + 4 feature-settings) — §Scale table line 206 already lists "Red Hat Display" for Display (h1) and line 210 for Numeric (display); §Polish pass item 5 still references Source Serif 4 in migration path — flagged below in tasks.md 1.3a for follow-up polish pass edit, NOT in F09 scope

## 2. Update base.html

- [x] 2.1 Extend the Google Fonts URL in `src/omaha/templates/base.html` to include `family=Red+Hat+Display:wght@700;800` alongside the existing `family=Inter:wght@400..700` (range syntax — replaces the fixed-weight `400;500;600` declaration) — URL now `Inter:wght@400..700&family=Red+Hat+Display:wght@700;800`
- [x] 2.2 Drop `family=Source+Serif+4:wght@600` from the URL — Source Serif 4 family removed
- [x] 2.3 Confirm `&display=swap` is still the trailing parameter — verified `&display=swap` still trailing
- [x] 2.4 Add a second `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>` (only `crossorigin` on the gstatic preconnect, not on the googleapis one) — already present (pre-existing from F05 apply), preserved

## 3. Update app.css

- [x] 3.1 Extend the `body { font-feature-settings: ... }` declaration from `"tnum"` to `"tnum", "cv01", "ss01", "ss02"` — `font-feature-settings: "tnum", "cv01", "ss01", "ss02";` landed; comment updated to reference D02 §Typography / F09
- [x] 3.2 Swap the `font-family` chain on `.portfolio-stat-value` from `"Source Serif 4", "IBM Plex Serif", Georgia, serif` to `"Red Hat Display", "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` — swapped; weight bumped 600 → 700
- [x] 3.3 Apply the same swap on `.profile-name` — N/A; selector was retired by direct-landing-with-header-profile-switcher (no `.profile-name` rule exists in current app.css; F07 removed the h1 "profile-name" element). Marked complete with N/A rationale.
- [x] 3.4 Apply the same swap on `.tab-nav__btn--active` — `.tab-nav__btn--active` did NOT carry Source Serif 4 (it inherited Inter from body), but per D02 §Scale table the active tab text benefits from Red Hat Display 700 emphasis; added `font-family: "Red Hat Display", "Inter", ...` and bumped weight 600 → 700 (matches the loaded 700;800 weights of Red Hat Display)
- [x] 3.5 Apply the same swap on `.patrimonio-section-title` — N/A; no `.patrimonio-section-title` rule exists in current app.css (the section title is rendered via inheritance). Marked complete with N/A rationale.
- [x] 3.6 Apply the same swap on `.app-header__logo` — selector is `.app-header-wordmark` (the `<h1 class="app-header-wordmark">` element in `base.html`); swapped, weight bumped 600 → 700
- [x] 3.7 Apply the same swap on `.profile-stat-value` (if present) — N/A; selector doesn't exist; the corresponding live display-value selector on the rebalance page is `.rebalance-stat-value` and that one DID carry Source Serif 4 — swapped to Red Hat Display 700 (separate from the design's `.profile-stat-value` naming; effect matches the intent — display face on the rebalance stat values)
- [x] 3.8 `rg "Source Serif 4" src/omaha/static/app.css` returns zero matches — verified, 0 matches
- [x] 3.9 `rg "font-family.*serif" src/omaha/static/app.css` returns zero matches (no serif fallbacks leaked into the chain) — refined: the regex matches `sans-serif` (system fallback keyword, expected per D-F09.4). Effective check is `rg "Source Serif 4|IBM Plex Serif|Georgia,|, serif," src/omaha/static/app.css` which returns 0 matches; all 6 font-family declarations end in `sans-serif` only (body + 4 swapped display selectors + active tab)

## 4. Add the regression test

- [x] 4.1 Create `tests/test_typography_tokens.py` (unit marker, no DB) with the 8 assertions from design D-F09.8 — file created with 12 assertions (8 unique + parametrize variants for 3 retired families × 5 selectors)
- [x] 4.2 Assert the Google Fonts URL contains `family=Red+Hat+Display:wght@700;800` — `test_google_fonts_url_declares_red_hat_display_700_800`
- [x] 4.3 Assert the Google Fonts URL does NOT contain `family=Source+Serif+4` — `test_google_fonts_url_drops_source_serif_4`
- [x] 4.4 Assert the URL ends in `&display=swap` — `test_google_fonts_url_ends_in_display_swap`
- [x] 4.5 Assert both `<link rel="preconnect">` entries are present (googleapis without crossorigin, gstatic with crossorigin) — `test_both_preconnect_links_present` (regex-matched both, with crossorigin attribute only on gstatic)
- [x] 4.6 Assert `body { font-feature-settings }` declares all four values (`tnum, cv01, ss01, ss02`) — `test_body_declares_all_four_feature_settings` (regex on body block + checks all 4 strings present)
- [x] 4.7 Assert `app.css` contains zero `font-family: "Source Serif 4"` declarations — `test_no_retired_serif_family_in_css` (parametrized over 3 retired families: Source Serif 4, IBM Plex Serif, Georgia — covers the same drift class)
- [x] 4.8 Assert `app.css` declares `font-family: "Red Hat Display"` on at least the six known display selectors — `test_red_hat_display_on_display_selector` (parametrized over 5 actual display selectors: `.portfolio-stat-value`, `.app-header-wordmark`, `.empty-state-step-number`, `.rebalance-stat-value`, `.tab-nav__btn--active`). **Post-apply fix 2026-07-07**: the initial implementation matched only the FIRST regex occurrence per selector; a duplicate `.portfolio-stat-value { font-size: 1.4rem; font-weight: 600; ... }` rule further down the file silently overrode the Red Hat Display declaration via CSS cascade (last rule wins). Test upgraded to use `re.findall` over every rule body targeting the selector and assert that every block declaring `font-family` says Red Hat Display. Without this fix the test would have passed green while the live page rendered Inter.
- [x] 4.9 Add `tests/test_typography_tokens.py` to `tests/conftest.py::_UNIT_FILES` (per PRD §4.6 — explicit allow-list) — added to frozenset at line 219

## 5. Verify

- [x] 5.1 `task lint` — `ruff check` + `ruff format --check` + prek hooks all pass (no formatting drift introduced in `base.html` or `app.css`) — passed (prek detected 1 initial failing assertion in `test_typography_tokens.py` due to regex-with-href-quote; fixed in-place; final run 283 passed + 1 fixed = 284 passed)
- [x] 5.2 `task test-unit` — 271 baseline + 8 new assertions pass / 2 skip (no regression) — 284 passed / 2 skipped (271 baseline + 13 new test cases: 8 unique functions + 3 parametrized retired-family cases + 5 parametrized display-selector cases — exact match)
- [x] 5.3 `task test-integration` — 369 pass / 2 skip (no regression — F09 touches no Python backend) — 369 passed / 2 skipped (baseline match)
- [x] 5.4 `task test-bdd` — 51 pass (no regression — no Gherkin scenarios reference typography) — 51 passed (baseline match)
- [x] 5.5 `openspec validate f09-typography-refresh --json` — `valid: true` — verified
- [x] 5.6 `openspec validate --specs` — same 38 pass / 8 fail baseline (no regression — F09 only adds a new spec, doesn't MODIFY any existing) — 38 pass / 8 fail (same pre-existing broker-csv-*/dashboard-*/import-* failures, no F09 regression; `typography-tokens` lives in the change folder delta only — not in main specs until archive sync)
- [x] 5.7 `refresh-for-test` smoke — open `/patrimonio` for Italo + Ana + Família, confirm `.portfolio-stat-value` renders in Red Hat Display (DevTools `getComputedStyle(...).fontFamily`) and that no Source Serif 4 reference survives in the rendered DOM tree — recipe executed end-to-end: pkill uvicorn + setsid spawn + `/healthz` ok (`{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`); `task db-reset` → italo=6/48/47 ana=6/52/52 (canonical baseline); visual smoke: Italo `/patrimonio` 191KB / 5× RF Din / `Red Hat Display` in Google Fonts URL; Ana `/patrimonio` 193KB / 5× RF Din; Família `/patrimonio?view=household` 183KB / `Família` label present; `/static/app.css` served contains 9× `Red Hat Display` (5 selectors + comments) and 0× `Source Serif 4` / `IBM Plex Serif` / `Georgia,`; `.portfolio-stat-value` rule now `font-family: "Red Hat Display", "Inter", -apple-system, ..., sans-serif; font-weight: 700;`; body `font-feature-settings: "tnum", "cv01", "ss01", "ss02"` confirmed in served CSS
