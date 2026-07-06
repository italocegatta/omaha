## 1. Routes & templates scaffold

- [ ] 1.1 Update `src/omaha/routes/pages.py`: add `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos`; remove `/dashboard` and `/rebalance` (404, no alias). All routes gate with `require_user` + `require_active_profile` per project standard.
- [ ] 1.2 `git mv templates/dashboard.html templates/patrimonio.html` to preserve history.
- [ ] 1.3 Create `templates/rentabilidade.html` (stub: heading "Em construção" + body "Esta página será preenchida em uma fatia futura.").
- [ ] 1.4 Create `templates/proventos.html` (stub: same shape as rentabilidade).
- [ ] 1.5 Verify no other template imports `_sidebar.html` (`rg "_sidebar.html" src/omaha/templates/` returns zero hits before deletion).

## 2. Top nav + base.html

- [ ] 2.1 Rewrite `templates/base.html`: remove sidebar slot; add `<nav class="tab-nav" data-testid="app-tab-nav">` with four `<a class="tab-nav__btn" data-testid="app-tab-btn-{slug}">` items (Patrimônio | Rebalanceamento | Rentabilidade | Proventos); add `app-tab-btn--active` class + `aria-current="true"` on the active tab; add profile picker (`data-testid="app-profile-picker"`) + `Sair` button to the right.
- [ ] 2.2 Active tab detection: derive from `request.url.path` server-side (Jinja context), set the `--active` modifier only on the matching tab.

## 3. patrimonio.html

- [ ] 3.1 Render `patrimonio-portfolio-header` element (`data-testid="patrimonio-portfolio-header"`) at the top of body with three labelled sub-elements (`Investido`, `Valor atual`, `Ganho`). Values come from existing per-profile aggregation logic in the route handler (no new DB queries).
- [ ] 3.2 Migrate action triggers (`Importar CSV`, `+ Classe`, `+ Ativo`) from `_sidebar.html` to the top of `patrimonio.html` body, aligned right. Preserve `data-testid` (`dashboard-import-btn`, `dashboard-add-asset-open`, `empty-state-create-class`).
- [ ] 3.3 Keep all existing class-section cards, edit-in-place behaviour, onboarding empty state. Verify `×` delete button still renders per `dashboard-inline-editing`.

## 4. rebalance.html

- [ ] 4.1 Remove per-card nav row (`← Dashboard` link + `Plano de aporte` label). The top nav replaces it.
- [ ] 4.2 Move aporte input + `Rebalancear` button from sidebar slot to the top of the body (above the plan area). Form posts to `/rebalanceamento`.
- [ ] 4.3 Update form error testid from `sidebar-form-error` to `rebalance-form-error` (in-body).
- [ ] 4.4 Drop the `BUILDER_WARNING` chip from the warnings panel (`D5`): keep `<code>` + PT-BR body text only.

## 5. CSS

- [ ] 5.1 Add `.tab-nav`, `.tab-nav__btn`, `.tab-nav__btn--active` classes in `src/omaha/static/app.css`. Active tab uses `--accent` (fern, `oklch(0.42 0.09 150)`); inactive uses `--ink` text, no fill.
- [ ] 5.2 Remove `.app-sidebar*`, `.sidebar-wordmark`, `.app-header-hamburger`, `.app-header-left` rules. Confirm no orphan selectors via `rg` in `app.css`.

## 6. Specs & docs

- [ ] 6.1 Update `openspec/PRD.md §5.3`: rewrite to reflect 4 tabs top-level + Rebalanceamento as dedicated route (`D8`). Same PR as the rest.
- [ ] 6.2 Update `DESIGN.md §Component inventory`: annotate `Tab nav` component with tokens `--accent` / `--ink` / `--bg` (`D2`).
- [ ] 6.3 Verify `openspec/specs/dashboard-inline-editing/spec.md` is unchanged (`D4`). Only spot-check that `×` delete testids are referenced.

## 7. Tests

- [ ] 7.1 Update `tests/e2e/` selectors that reference `data-testid="app-sidebar"`, `data-testid="sidebar-wordmark"`, `data-testid="app-header-hamburger"`, `data-testid="rebalance-form"` (in sidebar context), `data-testid="sidebar-form-error"`. Replace with top-nav / in-body equivalents.
- [ ] 7.2 Update `tests/bdd/step_defs/_workflows.py` `given` steps that hardcode `/dashboard` or `/rebalance`. Replace with `/patrimonio` / `/rebalanceamento`.
- [ ] 7.3 Add BDD scenarios for top nav: visit `/patrimonio`, assert `app-tab-btn-patrimonio` carries `aria-current="true"`; click `app-tab-btn-rebalanceamento`, assert URL is `/rebalanceamento`.
- [ ] 7.4 Add BDD scenario for stub pages: visit `/rentabilidade`, assert body contains "Em construção"; same for `/proventos`.
- [ ] 7.5 Add e2e scenario: legacy `/dashboard` returns 404; legacy `/rebalance` returns 404.
- [ ] 7.6 Run `task test-unit`, `task test-integration`, `task test-e2e`, `task test-bdd`. All must be green before `apply` exit.

## 8. Verify & archive (apply gate)

- [ ] 8.1 Run `uv run openspec validate f02-top-level-tab-nav-and-patrimonio --json` after implementation; resolve any failures.
- [ ] 8.2 Run `uv run opsx list --specs` to confirm spec health.
- [ ] 8.3 Run `uv run task refresh` to restart dev server with new layout, then visually verify all four tabs in browser.
- [ ] 8.4 Delegate to `openspec-archive-change` to move `f02-top-level-tab-nav-and-patrimonio` to `openspec/changes/archive/`. `dashboard-sidebar` spec deprecates + archives in the same flow.
- [ ] 8.5 Update `openspec/roadmap.md`: F02 status `Applying → Applied → Archived`; progress log updated.
