## 1. Aggregator (routes/pages.py)

- [x] 1.1 Add `household_aggregates(asset_classes: list[AssetClass]) -> dict[str, Any]` to `src/omaha/routes/pages.py`. Mirror of `portfolio_aggregates(...)` — same shape (`{"portfolio": ..., "classes": [...]}`, same Decimal invariants, same `broker-csv-import-totals` rule of summing `Position.total_invested` / `Position.total_current` directly). Module-level `_CLASS_COLORS` index assignment unchanged.
- [x] 1.2 Helper `household_asset_classes(db: DbSession, viewer: User) -> list[AssetClass]` eager-loads `AssetClass → Asset → Position` for every `Profile` whose `user_id == viewer.id`, ordered by `Profile.display_order` then `AssetClass.display_order`. Same `selectinload` strategy as `_render_patrimonio`.
- [x] 1.3 Helper `require_profile_writable(request: Request) -> None` in `src/omaha/auth.py`. Reads `request.session.get("view_mode")` (or querystring-equivalent — see 2.1); raises `HTTPException(409, "household_read_only")` when household mode is active. Logged as audit no-op (no I/O).

## 2. Routes & querystring handling

- [x] 2.1 Extend `GET /patrimonio` (and `/`, which already aliases) to parse `?view=household` from `request.query_params`. Pass `view="profile"` (default) or `view="household"` into `_render_patrimonio`.
- [x] 2.2 Extend `GET /` (alias of `/patrimonio`) similarly. Either alias the body or share the helper — avoid duplication.
- [x] 2.3 `_render_patrimonio(...)` gains a `view: str = "profile"` parameter. Branches:
  - `view == "household"` → uses `household_asset_classes(...)` + `household_aggregates(...)`. Sets context flag `read_only=True`.
  - `view == "profile"` → existing path unchanged, byte-equivalent.
- [x] 2.4 Same branching on `GET /` if `_render_patrimonio` is the shared renderer.

## 3. Mutation endpoints adopt `require_profile_writable`

- [x] 3.1 `src/omaha/routes/classes.py`: `POST /classes` and `PATCH /classes/{id}` (and any other mutation endpoints in this file) gain `Depends(require_profile_writable)`. Verify behavior unchanged when `view != "household"`.
- [x] 3.2 `src/omaha/routes/assets.py`: same — `POST /api/assets`, `PATCH /api/assets/{id}`, `DELETE /api/assets/{id}`.
- [x] 3.3 `src/omaha/routes/imports.py`: `POST /import` (preview + commit endpoints).
- [x] 3.4 `src/omaha/routes/rebalance.py`: `POST /api/rebalance`. Also (per Decision 3) household mode disables the `/rebalanceamento` page-side form — render `form_inert=True` when context `read_only=True`.
- [ ] 3.5 Verify with `task test-integration` that all five mutation endpoints still pass their existing tests when `view=profile`. Verify 409 contract (shape: `{"reason": "household_read_only"}`) with new test.

## 4. Header toggle (templates/base.html)

- [x] 4.1 Add `<form method="get" action="/patrimonio" data-testid="household-toggle" class="household-toggle">` inside `app-header-right`. Renders inside the same `{% if viewer and owner %}` block, between the profile switcher form and the logout form.
- [x] 4.2 Form renders only when `viewer.profiles | length >= 2`. Hidden input `name="view" value="household"` so `GET /patrimonio?view=household` is the submit target.
- [x] 4.3 Submit button reads `Casa` (PT-BR, capitalised like `Sair`). Class `.app-header__household-chip` — visual register matches existing tokens (`DESIGN.md` §Component inventory).
- [x] 4.4 When `request.url.path == '/patrimonio'` and `view == 'household'`, the toggle swaps to a "retornar" affordance that submits to `/patrimonio` (no querystring) — same form, hidden input removed, button text `Perfil`. Single form, two states.

## 5. Patrimonio template read-only branch

- [x] 5.1 `templates/patrimonio.html` adds `{% set view = view|default('profile') %}` at top of `{% block content %}`. Wrap the action triggers (`Importar CSV`, `+ Classe`, `+ Ativo`) in `{% if view == 'profile' %}` so they don't render in household mode.
- [x] 5.2 Wrap the inline-edit affordances (`dashboard-inline-editing` selectors) similarly — `disabled` attribute when `read_only=True`, or omit entirely.
- [x] 5.3 Add a small note at top of the household-mode render: "Visão agregada — somente leitura" (PT-BR, register domestic).
- [x] 5.4 Card `patrimonio-portfolio-header` (post-`F02`) renders unchanged — its data is filled by the aggregator returned by `household_aggregates(...)`.

## 6. CSS

- [x] 6.1 Add `.household-toggle` and `.app-header__household-chip` in `src/omaha/static/app.css`. Existing tokens (`--accent`, `--ink`, `--ink-muted`, `--bg`).
- [x] 6.2 Add `.is-read-only` rule for the action area: subdued chrome indicating disabled state.
- [x] 6.3 Verify no orphan selectors via `rg "\.app-sidebar|\.sidebar-" src/omaha/static/app.css/` (already zero post-F02 — sanity check).

## 7. Specs & docs

- [x] 7.1 Update `openspec/PRD.md §5.3`: remove the candidate slice "consolidação cross-profile" line; record F01 as delivered (link to archive path).
- [x] 7.2 Update `openspec/specs/cross-profile-sharing/spec.md` via the delta in this change folder — verify the delta is the only ADDED Requirements block; no MODIFIED/REMOVED.
- [x] 7.3 No update to `header-profile-switcher` (Decision 2). No update to `patrimonio-portfolio-header` (per `proposal.md`).

## 8. Tests

- [x] 8.1 `tests/integration/test_pages_patrimonio.py` (or new file `test_household_aggregate.py`): assert `?view=household` returns 200 with `patrimonio-portfolio-header` showing summed totals; assert `?view=profile` returns byte-equivalent to the previous response (snapshot or per-row diff). Use the existing `conftest.py` BOTH profiles seeded.
- [x] 8.2 Mutation tests: 5 cases (one per endpoint), each asserts 409 + JSON body `{"reason": "household_read_only"}` when `view=household`. Endpoints unchanged when `view=profile`.
- [x] 8.3 BDD: add scenario in `tests/bdd/features/profile_sharing.feature` — "Ana visualiza a casa como agregado"; asserts card `patrimonio-portfolio-header` values match sum of both profiles.
- [x] 8.4 Toggle visibility: integration test asserts `len(viewer.profiles) == 1` → toggle absent from rendered HTML.
- [x] 8.5 Run `task test-unit`, `task test-integration`, `task test-bdd`. All green before apply exit. (e2e may be deferred to T01, see design §Risks.)

## 9. Verify & archive

- [x] 9.1 `uv run openspec validate f01-household-cross-profile-consolidation --json` returns `valid: true`. Run `uv run openspec validate --specs --json` to confirm no regression in other specs.
- [x] 9.2 `uv run task refresh` restarts dev server with household toggle visible; manual smoke: visit `/patrimonio?view=household`, confirm card sums, mutation buttons absent, BDD step `clico em "Casa"` from `tests/bdd/step_defs/common_steps.py` works.
- [x] 9.3 Delegate to `openspec-archive-change` to move the change to `openspec/changes/archive/2026-07-04-f01-.../` and consolidate the delta into `openspec/specs/cross-profile-sharing/spec.md`.
- [x] 9.4 Update `openspec/roadmap.md`: F01 status `Applying → Applied → Archived`; F01 removed from Recommended Execution Order (already done at `Spec Proposed`); `Compacted history` slot opens for the next archive cycle.
