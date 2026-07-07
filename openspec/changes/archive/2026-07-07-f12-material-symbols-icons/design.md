## Context

D02 (archived 2026-07-07) memorialized the SI maximal register and explicitly catalogued 10 Material Symbols icons as part of the visual system. DESIGN.md §Iconography was rewritten to "Material Symbols, scoped" with the catalog committed but no implementation landing. The current UI still uses textual glyphs (`×`, `−`, `▾`, `▶`, `+`) which is typographically weak and inconsistent with the post-D02 visual language already shipping (F09 Red Hat Display + F10 5-state feedback). F12 closes the implementation gap.

Critical-area: visual surface — cap 1 Applying (per roadmap §Parallelism). F12 touches no auth, no DB, no solver, no yfinance.

## Goals / Non-Goals

**Goals:**

- Material Symbols Outlined font loaded once via Google Fonts in `base.html`.
- 10-icon catalog (per D02) is the canonical scope; out-of-catalog use requires a new OpenSpec change.
- 4 CSS hooks (`.icon`, `.icon--sm`, `.icon--md`, `.icon--lg`) with `currentColor` for natural palette inheritance.
- 7 templates + partials updated to use icons in documented sites.
- `tests/test_iconography_tokens.py` covers font URL + hooks + catalog scope; PRD §4.6 allow-list extended.

**Non-Goals:**

- Self-hosting Material Symbols (Google Fonts default; same pattern as F09 Inter).
- Animated icons / Material Symbols variable axis (F12 uses Outlined only).
- Icon set expansion (any new icon is a follow-up OpenSpec change).
- Theme switcher icons for F13 (F13 is Blocked; icons here are dark-only).
- Stroke-based SVG icons (D02 replaced that pattern).

## Decisions

### D-F12.1 — Google Fonts CDN, not self-host

Same default as F09 typography refresh. Self-host is a follow-up if owner wants offline-first or to dodge a CDN dep. CDN URL pattern: `<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined">` with preconnect for `fonts.gstatic.com` (already preconnected for Inter/Red Hat Display).

Alternatives: self-host via `npm install material-symbols` + copy `woff2` to `static/fonts/`. Rejected: build pipeline doesn't have a frontend bundler; would require adding one just for this.

### D-F12.2 — Catalog scoped at 10 icons

Per D02 §Iconography. Icons: `add`, `add_circle`, `upload`, `logout`, `close`, `warning`, `expand_more`, `expand_less`, `check_circle`, `help`. Out-of-catalog use requires opening a new OpenSpec change (proposal.md "Impact" lists extension as the natural follow-up path).

Alternatives: catalog open-ended. Rejected: no guardrail prevents visual drift; 10 is the documented set D02 committed.

### D-F12.3 — `.icon` base class + 3 size modifiers

Pattern:
```css
.icon { font-family: "Material Symbols Outlined"; font-weight: normal; font-style: normal; line-height: 1; letter-spacing: normal; text-transform: none; display: inline-block; white-space: nowrap; word-wrap: normal; direction: ltr; font-feature-settings: "liga"; -webkit-font-smoothing: antialiased; }
.icon--sm { font-size: 16px; }
.icon--md { font-size: 20px; }
.icon--lg { font-size: 24px; }
```

`.icon` always required; size modifiers optional. If none specified, defaults to body text size (Material Symbols intrinsic sizing). Reason: cascading tokens keep specificity flat.

Alternatives: size baked into one class (`.icon-sm`, `.icon-md`, `.icon-lg`). Rejected: requires N×3 combinations instead of `.icon .icon--md` pairing — adds selector noise.

### D-F12.4 — `currentColor` for theming

`.icon` sets `color: inherit` implicitly via Material Symbols default; theming comes from parent text color. No hardcoded color in `.icon` rules. Works with F05 dark palette + F10 5-state color tokens automatically.

### D-F12.5 — Icon markup via `<span class="icon icon--md" aria-hidden="true">add</span>`

Material Symbols font uses text ligatures — the inner text IS the icon name. Pattern is consistent with Material's own docs. `aria-hidden="true"` because:
- Adjacent button text already labels the action (`+ Classe` button already says "Nova classe").
- Decorative-only icons would otherwise create duplicate screen-reader output.
- Spec rules: see `dashboard-inline-editing` which already references icon semantics for delete buttons.

Alternatives: `<i class="material-icons">add</i>` (Material's legacy class). Rejected: Outlined variant uses different class; Material 3 docs prefer `<span>`.

### D-F12.6 — Login button icon is decorative-only (no test gate)

F12 adds a leading icon to login submit for visual consistency. Test scope excludes login (per slice Notes: "opcional"). If icon is omitted in apply, no spec failure — login template is not in the `tests/conftest.py::_UNIT_FILES` iconography test.

### D-F12.7 — Test gating by font URL presence, not pixel render

`tests/test_iconography_tokens.py` asserts:
- `base.html` contains `Material+Symbols+Outlined` in `<link>` tag.
- `app.css` contains `.icon`, `.icon--sm`, `.icon--md`, `.icon--lg` selectors with documented font-size values.
- 7 templates contain the documented `class="icon ..."` patterns matching their documented sites (per slice "Files" list).
- DESIGN.md §Iconography lists all 10 catalog names verbatim.

Pixel rendering is captured by F08/F09/F10 visual smoke (no automated pixel test in this slice). Adding Playwright pixel test for icons is scope creep — T06 visual regression baseline already covers this in the future.

## Risks / Trade-offs

- **Google Fonts CDN dependency** → already a dep via F09; not a new risk. CDN unreachable in dev → icons render as tofu (□) but page still functions. Mitigation: preconnect already in place.
- **Catalog scope rigidity** → 10 icons is small; if owner requests a new icon (e.g., `download`, `delete_sweep`), it requires a new OpenSpec change. Mitigation: slice Notes records "out-of-catalog use requires new OpenSpec change" so future requests are routed correctly.
- **Material Symbols Outlined visual weight differs from Inter** → font swap inside a button can change button height by 1-2px. Mitigation: `.icon` rule sets `line-height: 1` + `display: inline-block` so vertical metrics are stable; visual smoke in `task serve` confirms.
- **License attribution** → Material Symbols is Apache 2.0; F12 doesn't add a `NOTICE` file because the font ships from Google Fonts and attribution lives in DESIGN.md §Iconography (D02 already added a one-liner). No new exposure.

## Migration Plan

F12 is a non-breaking visual addition. No migration steps. Rollback = revert the 7 template + partial changes + `base.html` link removal + CSS block removal; tests catch missing catalog. No DB changes, no runtime data migration.

## Open Questions

None at propose time. Owner decisions from D02 fully resolve catalog + variant.