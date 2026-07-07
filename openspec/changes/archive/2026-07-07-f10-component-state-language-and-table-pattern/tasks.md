## 1. Pre-audit + capture baseline

- [ ] 1.1 Run `rg -n "outline.*none|outline.*0" src/omaha/static/app.css` and document any pre-existing outline suppressions that need `:focus-visible` override
- [ ] 1.2 Run `bash scripts/print_lan_url.sh` and capture before-screenshots of `/patrimonio`, `/classes`, `/rebalanceamento`, `/import`, `/import_review`, `/login` (manual — no test harness; T06 captures automated baselines later)

## 2. CSS — 5-state vocabulary + table pattern + extras

- [ ] 2.1 Add 5-state base classes in `src/omaha/static/app.css`: `.is-interactive` (idle/hover/focus transitions), `.is-disabled` (cursor + opacity + ink-muted), `.is-error` (error-fg + error-bg + inline message styling)
- [ ] 2.2 Add `:focus-visible` global rule with `outline: 2px solid var(--color-focus); outline-offset: 2px` (overrides per-element `outline: none`)
- [ ] 2.3 Add hover styles for buttons and tabs: `tr:hover td`, `.btn:hover`, `.tab-nav__btn:hover` with `background: var(--bg-hover)` transition `80ms ease`
- [ ] 2.4 Add `prefers-reduced-motion: reduce { *, *::before, *::after { transition: none !important; animation: none !important } }` global override
- [ ] 2.5 Add `.table-sticky-header thead { position: sticky; top: 0; background: var(--surface-sunk); z-index: 1 }` for top-level page tables only
- [ ] 2.6 Add `tr:hover td { background: var(--bg-hover) }` and `.row-actions { opacity: 0; transition: opacity 80ms ease }` + `.tr:hover .row-actions { opacity: 1 }`
- [ ] 2.7 Add mobile breakpoint `@media (max-width: 768px) { .row-actions { opacity: 1 } }` so action column is always visible on small viewports
- [ ] 2.8 Add `.table-total { font-weight: 600; border-top: 2px solid var(--border-strong) }` for total row emphasis
- [ ] 2.9 Add `td.is-numeric, th.is-numeric { text-align: right; font-variant-numeric: tabular-nums }` for tabular numerics
- [ ] 2.10 Add `.section-divider { border-top: 1px solid var(--border); margin: 24px 0; background: transparent }`
- [ ] 2.11 Add `::selection { background: var(--accent); color: var(--accent-ink) }` global
- [ ] 2.12 Add `:-webkit-autofill, :-webkit-autofill:hover, :-webkit-autofill:focus { -webkit-text-fill-color: var(--ink); -webkit-box-shadow: 0 0 0 1000px var(--surface) inset; box-shadow: 0 0 0 1000px var(--surface) inset }`
- [ ] 2.13 Add `.label-xs { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--ink-muted); font-weight: 600 }`
- [ ] 2.14 Add `.input-prefix-wrap { display: flex; align-items: stretch; border: 1px solid var(--border); border-radius: 4px; background: var(--surface) } .input-prefix { padding: 0 12px; display: flex; align-items: center; background: var(--surface-sunk); color: var(--ink-muted); border-right: 1px solid var(--border); border-radius: 4px 0 0 4px }`

## 3. Templates — minimal `aria-*`/`title` additions (no DOM structure change)

- [ ] 3.1 `src/omaha/templates/base.html`: tabs (`.tab-nav__btn`) get `:focus-visible` ring already via CSS — no template change unless `aria-current` is missing
- [ ] 3.2 `src/omaha/templates/login.html`: add `aria-invalid` / `aria-describedby` only if error path renders (verify by reading the template)
- [ ] 3.3 `src/omaha/templates/_patrimonio_actions.html`: buttons get hover/focus via CSS — no template change
- [ ] 3.4 `src/omaha/templates/_patrimonio_portfolio_header.html`: numerics get `.is-numeric` class on cells (CSS-driven — no template change unless structure adds cells)
- [ ] 3.5 `src/omaha/templates/_patrimonio_distribution.html`: section-divider via CSS class on existing `<hr>` if present
- [ ] 3.6 `src/omaha/templates/_patrimonio_class_section.html`: asset `<table>` (asset list) gets `.table-sticky-header`; `<tr class="row-actions">` for delete; subtotal `<tr class="table-total">` if missing
- [ ] 3.7 `src/omaha/templates/patrimonio.html`: section dividers between portfolio header / classes summary / distribution
- [ ] 3.8 `src/omaha/templates/classes.html`: `<table>` (class list) gets `.table-sticky-header`; total `<tr class="table-total">` already exists (verify), `<tr class="row-actions">` for delete
- [ ] 3.9 `src/omaha/templates/assets.html`: asset editor rows get `<tr class="row-actions">` for remove button; numerics `.is-numeric`
- [ ] 3.10 `src/omaha/templates/rebalance.html`: form R$ prefix in aporte input; section dividers between form / plan / warnings
- [ ] 3.11 `src/omaha/templates/_rebalance_plan.html`: warning `<li>` gets `.warning-line` class for border-left 4px (D02 exception)
- [ ] 3.12 `src/omaha/templates/_rebalance_placeholder.html`: empty-state typography uses eyebrow `.label-xs` above placeholder text
- [ ] 3.13 `src/omaha/templates/import.html`: form inputs get hover/focus via CSS — no template change unless autofill override is needed (verify)
- [ ] 3.14 `src/omaha/templates/import_review.html`: review `<table>` gets `.table-sticky-header` if not already
- [ ] 3.15 `src/omaha/templates/_patrimonio_add_asset_modal.html`: modals do NOT receive sticky-header — verify add-asset-modal table does not have it (intentional, D-F10.2)

## 4. DESIGN.md sync

- [ ] 4.1 Add row to `DESIGN.md` §Component inventory cross-linking the new spec `component-state-language`
- [ ] 4.2 Add entry to `DESIGN.md` §Anti-patterns: "Action column always visible (forbidden — use `.row-actions` opacity 0 / hover 1)"
- [ ] 4.3 Reference the 5-state vocabulary table from `DESIGN.md` §Components explicitly (it already exists at line 331 — confirm it stays the source of truth)

## 5. Verification gate

- [ ] 5.1 `task lint` — ruff + prek hooks all pass on `src/omaha/static/app.css` + modified templates
- [ ] 5.2 `task test-unit` — 271 pass / 2 skip baseline (F09 archive); no new unit tests added (F10 is CSS-driven; visual verification is manual + future T06)
- [ ] 5.3 `task test-integration` — 369 pass / 2 skip baseline (R04 archive); no integration test changes
- [ ] 5.4 `task test-bdd` — 51 pass baseline (T05 archive); no BDD scenario changes
- [ ] 5.5 `openspec validate f10-component-state-language-and-table-pattern --json` returns `valid: true`
- [ ] 5.6 `openspec validate --specs` reports same 38 pass / 8 fail baseline (8 pre-existing failures: broker-csv-*, dashboard-*, import-*) — no F10 regression
- [ ] 5.7 `bash scripts/print_lan_url.sh` returns LAN URL; manually inspect 10 pages in viewport 1440×900 + mobile 375×667:
  - `/login`: input focus ring visible on Tab; autofill override renders surface (test by setting a fake autofill hint)
  - `/patrimonio`: portfolio header `.is-numeric` right-aligned; section dividers visible; action column hidden until hover
  - `/patrimonio?view=household` (Família): same dividers; read-only banner above dividers
  - `/classes`: `<thead>` sticky on scroll; total row bold + 2px border-top; hover row bg lift; action column on hover
  - `/assets`: action column visible on hover; row hover lift
  - `/rebalanceamento`: form R$ prefix visible on aporte input; submit hover/focus; warnings border-left 4px
  - `/import`: form inputs hover/focus; no autofill yellow flash
  - `/import_review`: review table sticky header; action column hover
  - `/rentabilidade` (stub): eyebrow `.label-xs` visible above "Em construção"
  - `/proventos` (stub): same eyebrow
- [ ] 5.8 `task db-reset` produces Italo=6/48/47 + Ana=6/52/52 (R02/F07 baseline unchanged); Família sentinel intacta

## 6. Sync + archive

- [ ] 6.1 Sync spec delta via `openspec sync-specs f10-component-state-language-and-table-pattern` (or manual pre-sync if `--skip-specs` needed) to `openspec/specs/component-state-language/spec.md` — promote `## ADDED Requirements` to `## Requirements`; add Purpose section
- [ ] 6.2 `openspec validate component-state-language --json` returns `valid: true`
- [ ] 6.3 Move folder `openspec/changes/f10-component-state-language-and-table-pattern/` → `openspec/changes/archive/2026-07-07-f10-component-state-language-and-table-pattern/` (or use `openspec archive f10-component-state-language-and-table-pattern --yes`)
- [ ] 6.4 `openspec list --specs` reports new `component-state-language` capability (47 → 48 specs total)