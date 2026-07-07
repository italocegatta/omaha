## Why

The current UI uses textual glyphs (`×`, `−`, `▾`, `▶`, `+`) in place of real icons, which is typographically weak and limits affordance density. D02's design register decision (SI maximal, archived 2026-07-07) explicitly includes icons as part of the visual system; DESIGN.md §Iconography was rewritten as "Material Symbols, scoped" but no implementation has landed. F12 materializes that decision.

## What Changes

- Add Material Symbols Outlined font via Google Fonts URL in `base.html`.
- Replace textual glyphs in 5 templates with Material Symbols icons.
- Add `.icon` / `.icon--sm` (16px) / `.icon--md` (20px) / `.icon--lg` (24px) CSS classes in `app.css` with `currentColor` theming.
- Introduce icon catalog (10 icons) as the canonical list — out-of-catalog icons are out of scope.
- Update DESIGN.md §Iconography to record the catalog as the source of truth (already drafted by D02; F12 sync).
- Add `tests/test_iconography_tokens.py` covering font URL + class hooks + catalog scoping.

## Capabilities

### New Capabilities

- `iconography-tokens`: Icon font + size scale + catalog scope. Internal capability — describes the file-level visual contract (Google Fonts URL, CSS class hooks, allowed icon names). Follows the precedent set by `typography-tokens` (F09) and `component-state-language` (F10).

### Modified Capabilities

None. Existing specs (`dashboard-inline-editing`, `cross-profile-sharing`) keep their current requirements — F12 swaps glyph implementation without changing requirements.

## Impact

- `src/omaha/templates/base.html` — Google Fonts URL gains Material Symbols Outlined preconnect + stylesheet link.
- `src/omaha/static/app.css` — append `.icon`, `.icon--sm`, `.icon--md`, `.icon--lg` rules with `currentColor` + tabular sizing.
- `src/omaha/templates/_patrimonio_actions.html` — action buttons (`+ Classe`, `+ Ativo`, `Importar`) gain leading icons (`add`, `add_circle`, `upload`).
- `src/omaha/templates/_patrimonio_class_section.html` — delete confirm uses `close` icon; expand chevron uses `expand_more` / `expand_less`.
- `src/omaha/templates/_rebalance_plan.html` — warning `<li>` gains `warning` icon.
- `src/omaha/templates/_patrimonio_add_asset_modal.html` — modal close uses `close` icon.
- `src/omaha/templates/import_review.html` — matched rows use `check_circle`, unmatched use `help`.
- `src/omaha/templates/base.html` — `Sair` action uses `logout` icon.
- `src/omaha/templates/login.html` — submit button optionally gains icon (decorative; not test-gated).
- `DESIGN.md` §Iconography — catalog already drafted by D02; F12 sync confirms catalog + adds scope note "out-of-catalog icons require an OpenSpec change".
- `tests/test_iconography_tokens.py` — new unit test covering font URL presence, class hook presence, catalog scope via `class` attribute assertions.
- `tests/conftest.py` — `_UNIT_FILES` gains `test_iconography_tokens.py` per PRD §4.6 explicit allow-list.
