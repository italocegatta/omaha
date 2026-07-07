## 1. Font loading

- [x] 1.1 Add Material Symbols Outlined `<link rel="stylesheet">` to `src/omaha/templates/base.html` `<head>` (URL `https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined`)
- [x] 1.2 Verify `fonts.gstatic.com` preconnect already present (reused from F09) — add if missing

## 2. CSS hooks

- [x] 2.1 Add `.icon` base rule to `src/omaha/static/app.css` (Material Symbols Outlined font-family + line-height: 1 + display: inline-block + font-feature-settings "liga")
- [x] 2.2 Add `.icon--sm` (16px), `.icon--md` (20px), `.icon--lg` (24px) size modifiers
- [x] 2.3 Verify `color: inherit` cascade (no hardcoded color in `.icon` rules) per D-F12.4

## 3. Templates — action buttons

- [x] 3.1 `_patrimonio_actions.html` — add `add` icon to "Nova classe" button (`.icon .icon--md`, aria-hidden)
- [x] 3.2 `_patrimonio_actions.html` — add `add_circle` icon to "Novo ativo" button
- [x] 3.3 `_patrimonio_actions.html` — add `upload` icon to "Importar CSV" button
- [x] 3.4 `base.html` — add `logout` icon to "Sair" action

## 4. Templates — confirmations and warnings

- [x] 4.1 `_patrimonio_class_section.html` — add `close` icon to per-class × delete button + delete confirm
- [x] 4.2 `_rebalance_plan.html` — add `warning` icon to warning `<li>` items
- [x] 4.3 `_patrimonio_add_asset_modal.html` — add `close` icon to 3 modal close buttons (add-asset / new-class / import)

## 5. Templates — toggles and status

- [x] 5.1 `_patrimonio_class_section.html` — replace `▸` chevron glyph with `expand_more` icon (CSS rotation preserved via existing `.class-chevron--open` rule)
- [x] 5.2 `import_review.html` — add `check_circle` to matched `<li>` + `help` to unmatched `<td>`

## 6. Templates — login (decorative)

- [x] 6.1 `login.html` — skipped per D-F12.6 (no catalog icon matches `Entrar` semantically; decorative-only and not test-gated)

## 7. Test scaffold

- [x] 7.1 Create `tests/test_iconography_tokens.py` with assertions for font URL in `base.html`, CSS hooks in `app.css`, template markup, DESIGN.md catalog presence (24 assertions)
- [x] 7.2 Extend `tests/conftest.py::_UNIT_FILES` allow-list with `test_iconography_tokens` per PRD §4.6
- [x] 7.3 Run `task test-unit` — 337 passed / 2 skipped (vs F10 baseline 284; +53: 24 new iconography + 29 R06 archive tests now in allow-list via `test_db_snapshot.py` / `test_db_mutations.py` / `test_admin_recovery.py`)

## 8. Documentation sync

- [x] 8.1 Verify `DESIGN.md §Iconography` lists all 10 catalog names verbatim (D02 archived content; revalidated by `test_design_md_iconography_lists_catalog_name` parametrized over 10 names)
- [x] 8.2 Add "Extension path" subsection noting out-of-catalog requests require new OpenSpec change + fix the catalog URL (was `css2?family=Material+Symbols+Outlined`; corrected to `icon?family=Material+Symbols+Outlined`)

## 9. Spec verification

- [x] 9.1 Run `openspec validate f12-material-symbols-icons --json` — `valid: true`
- [x] 9.2 Run `openspec validate --specs` — same 8 pre-existing failures (broker-csv-*, dashboard-*, import-*), no F12 regression

## 10. Delivery

- [x] 10.1 Run `task lint` (prek + ruff format/check) — green
- [x] 10.2 Run `task test-integration` — 369 passed / 2 skipped (no regression vs F10 archive baseline)
- [x] 10.3 Run `task test-bdd` — 51 passed (regression caught + fixed: `tests/bdd/step_defs/dashboard_steps.py::section_text` now strips `.icon` descendants before `inner_text()` read so Material Symbols ligatures don't pollute substring assertions)
- [x] 10.4 `refresh-for-test` smoke: server `0.0.0.0:8000` healthy; `db-reset` italo=6/48/47 ana=6/52/52; login Italo + select profile → `/patrimonio` renders Material Symbols URL in `<head>` + 1× logout (Sair) + 1× upload (Importar CSV) + 1× add_circle (Novo ativo) + 1× add (Nova Classe) + 6× expand_more chevrons (one per class section); 5× "RF Din" classes seeded
- [x] 10.5 Update roadmap slice F12 to `Applied`