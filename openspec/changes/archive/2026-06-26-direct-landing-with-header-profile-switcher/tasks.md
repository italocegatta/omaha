## 1. Routes + auth flow

- [x] 1.1 `src/omaha/routes/auth.py` — `POST /login` binds `active_profile_id` to the logged-in user's first profile (by `display_order`) before the 303 to `/`.
- [x] 1.2 `src/omaha/routes/pages.py` — delete `GET /profiles` route + `profiles_list` view; drop `user.profiles` access from the routes module.
- [x] 1.3 `src/omaha/routes/pages.py` — loosen `POST /profiles/{id}/select`: drop the `profile.user_id != user.id` 404 check; non-existent id still 404s.
- [x] 1.4 `src/omaha/routes/pages.py` — `GET /` redirects to `/login` (not `/profiles`) when no active profile resolves; clears stale `active_profile_id`.

## 2. Header chip + viewer label (base.html)

- [x] 2.1 `src/omaha/templates/base.html` — rename logout form `class="profile-switcher"` → `class="logout-form"`.
- [x] 2.2 `src/omaha/templates/base.html` — add `form.profile-switcher` chip with native `<select>` (server-rendered options, `selected` on active, `✓` glyph on current, `onchange` rewrites form action + submits).
- [x] 2.3 `src/omaha/templates/base.html` — render `<span class="viewer-label" data-testid="viewer-label">{{ viewer.username }}</span>` before the chip when `viewer.id != owner.user_id`; omit when they match.
- [x] 2.4 `src/omaha/templates/base.html` — Jinja context now expects `profiles` (all profiles) + `viewer` (current User) + `owner` (active Profile) on every authenticated render.

## 3. Dashboard h1 removal + empty-state copy

- [x] 3.1 `src/omaha/templates/dashboard.html` — delete `<h1 class="profile-name" data-testid="profile-name">Bem-vindo, {{ profile.name }}</h1>`.
- [x] 3.2 `src/omaha/templates/dashboard.html` — empty-state copy: "Você ainda não tem classes" → "Esta carteira ainda não tem classes".

## 4. Stylesheet (app.css)

- [x] 4.1 `src/omaha/static/app.css` — rename selector `header.app-header form.profile-switcher button` → `header.app-header form.logout-form button`.
- [x] 4.2 `src/omaha/static/app.css` — shrink `.profile-name, .portfolio-stat-value { font-family: Source Serif 4... }` to just `.portfolio-stat-value` (drop `.profile-name` selector).
- [x] 4.3 `src/omaha/static/app.css` — add `.profile-switcher` chip rules (~30 lines): select border / padding / radius / hover / focus; option `✓` glyph inherits from default option styling; viewer-label rule (`--ink-muted`, 0.85rem).
- [x] 4.4 `src/omaha/static/app.css` — `@media (max-width: 480px)` rule: stack header into 2 rows (logo + chip on row 1, nav + sair on row 2); hide nav inline below 480px if needed.

## 5. Picker template removal

- [x] 5.1 `git rm src/omaha/templates/profiles.html`.

## 6. Integration tests (TestClient)

- [x] 6.1 `tests/test_auth.py` — flip 4 assertions: `POST /login` redirects to `/` (not `/profiles`); `GET /` after login renders dashboard (no picker); `POST /logout` flow unchanged; stale-profile case redirects to `/login`.
- [x] 6.2 `tests/test_e2e.py` — flip login-redirect step (`/profiles` → `/`); drop the `/profiles` page assertion.
- [x] 6.3 `tests/test_pages_routes.py` — `_login_and_select` helper drops the explicit `POST /profiles/{id}/select` (login already binds); assert the landing profile matches the username.
- [x] 6.4 `tests/test_imports_routes.py` — replace `_profile_id_for(client, name)` regex on `/profiles` HTML with a direct DB lookup (`db.query(Profile).filter(Profile.name == name).first()`).
- [x] 6.5 `tests/test_assets_*.py`, `tests/test_classes_*.py`, `tests/test_real_csv_flow.py`, `tests/test_import_commit.py`, `tests/test_import_preview.py`, `tests/test_import_get_preview.py`, `tests/test_quote_routes.py`, `tests/test_classes_delete.py` — simplify `_login_and_select_profile` helpers (drop the `POST /profiles/{id}/select` step; rely on login auto-bind). Profile id lookup goes via DB, not the picker page.
- [x] 6.6 `tests/test_assets_e2e.py` — `test_add_assets_blocked_when_class_not_in_profile` flips: cross-profile asset-class access now SUCCEEDS (the asset lands under the active profile), not 422. Repurpose or delete the test.
- [x] 6.7 `tests/test_assets_patch_legacy.py` — `test_patch_asset_cross_profile_404` flips: a PATCH against another profile's asset while that profile IS the active one now returns 200 (no 404). The test's premise no longer applies; repurpose to assert "PATCH asset.id that belongs to active profile succeeds."
- [x] 6.8 Run `uv run task test-integration` — confirms no test still references `/profiles` or asserts the picker step.

## 7. E2E (Playwright)

- [x] 7.1 `tests/e2e/test_user_journey.py` — `_login_and_select_italo` drops the `wait_for_url(/profiles)` + picker click; asserts `wait_for_url(/$)` directly.
- [x] 7.2 `tests/e2e/test_import_user_journey.py` — same in `_login_and_select_italo`.
- [x] 7.3 `tests/e2e/test_full_journey.py` — same (uses SELECTORS["profile_picker"]; the `form.profile-picker` selector can be removed since the picker page is gone).
- [x] 7.4 `tests/e2e/test_user_journey_rebalance.py` — inherits via `_login_and_select_italo` import.
- [x] 7.5 Run `uv run task test-e2e` — confirms the e2e journey lands on `/` after login.

## 8. BDD (workflow + features)

- [x] 8.1 `tests/bdd/step_defs/_workflows.py` — `login_and_pick_profile` → `login_and_land`: drops picker click + `wait_for_url(/profiles)`; asserts `wait_for_url(/$)` directly. Update docstring + `data-testid` comments.
- [x] 8.2 `tests/bdd/step_defs/_workflows.py` — `@carve_out` decorator shrinks: `files=frozenset({"login.feature"})` (was `{"login.feature", "profile_isolation.feature"}`); `step_regex` unchanged.
- [x] 8.3 `tests/bdd/features/login.feature` — flip `Esquema do Cenário: Login + profile pick OK` to `Login + dashboard direto`: drops "clico no botão do perfil" step; replaces "estou na página '/profiles'" with "estou na página '/'"; asserts the landing profile name shows on `[data-testid="profile-switcher"]` (the chip).
- [x] 8.4 `git mv tests/bdd/features/profile_isolation.feature tests/bdd/features/profile_sharing.feature`; rewrite both scenarios to assert the new contract (Ana sees Italo's classes after switching; Italo sees Ana's classes after switching).
- [x] 8.5 `tests/bdd/step_defs/common_steps.py` — `clico no botão do perfil` step (`form.profile-picker button`) can be removed OR repurposed to "clico na opção do perfil X no header" (`select.profile-switcher option:has-text("X")`); pick removal if `login.feature` no longer references the step.
- [x] 8.6 Run `uv run task test-bdd` — confirms scenarios flip + workflow contracts still hold.

## 9. Visual + manual verification

- [x] 9.1 `uv run task db-reset` — confirm seed creates Italo + Ana users + their profiles AND populates BOTH from CSV triplets (Italo: 6 classes / 48 assets / 47 positions; Ana: 6 classes / 40 assets / 43 positions — exact counts may shift with future CSV edits, but both must be > 0 for each layer).
- [x] 9.2 `uv run task serve` — manual browser pass: login as Italo → land on `/` showing Italo's dashboard; chip reads "Italo ✓"; logout works.
- [x] 9.3 Manual browser pass: login as Ana → land on `/` showing Ana's dashboard (NOT the empty-state copy); chip reads "Ana ✓"; switch to Italo via chip → reloads showing Italo's classes; viewer label "Ana" appears next to chip.
- [x] 9.4 Manual browser pass: switch back to Ana via chip → reloads showing Ana's classes; viewer label disappears (chip alone identifies the portfolio).
- [x] 9.5 Mobile (resize browser <480px): header stacks; chip remains tappable; nav + sair accessible.
- [x] 9.6 `uv run task check` (lint + test-unit) + `uv run task test-integration` — green.

## 10. Delivery

- [x] 10.1 Run `refresh-for-test` skill (or `uv run task db-reset` + manual `/healthz` + `uv run task serve` restart) before reporting done.
- [x] 10.2 Report LAN URL + DB state to the user; confirm both Italo and Ana profiles are visible from either login AND both dashboards render populated (not empty-state).

## 11. Dual-profile seed delivery (`db-reset` covers Ana too)

- [x] 11.1 `scripts/reset_both_profiles.py` — new wrapper that opens one `SessionLocal()`, calls `run_reset(db, "italo", ...)` then `run_reset(db, "ana", ...)` in order, prints per-profile `classes=… assets=… positions=…` lines, exits non-zero if either profile's validation fails (so the failure is scoped to the failing profile; the other profile's earlier data remains intact).
- [x] 11.2 `pyproject.toml:db-reset` — point the taskipy task at `scripts.reset_both_profiles.py` (drop `--profile italo --mode reset` flag from the current `seed_from_csv` invocation). Help text reflects "wipe + reseed BOTH profiles (Italo + Ana)".
- [x] 11.3 `pyproject.toml:db-seed-from-csv`, `db-seed-diff`, `db-seed-upsert` — keep the single-profile `seed_from_csv.py --profile italo …` default (back-compat for callers that only want one profile); the Ana variant is reachable via `task db-seed-from-csv -- --profile ana`. Document this in the help text.
- [x] 11.4 Add `tests/scripts/test_reset_both_profiles.py` — unit test that monkey-patches `run_reset` to capture calls; asserts the wrapper invokes it twice with `("italo", ...)` then `("ana", ...)`, prints per-profile counts, and exits non-zero when one profile's `run_reset` raises.
- [x] 11.5 Add `tests/integration/test_db_reset_both_profiles.py` (or extend the existing `tests/test_db_reset.py`) — integration test that runs `scripts.reset_both_profiles.py` against a fresh SQLite, then asserts both profiles have `AssetClass` rows summing to 100, `Asset` rows per class summing to 100, and at least one `Position` row.
- [x] 11.6 `AGENTS.md` "Delivery finalization" table — update the default-row bullet to read "Italo + Ana (both populated: classes + assets + positions)" and update the `Italo: 6 classes + 48 assets + 47 positions` example to the two-profile tuple. Keep the carve-out for `db-clear-assets`.
- [x] 11.7 `README.md` "Network access" / "Quick start" — if the README mentions row counts or DB state for the dev DB, update the example to mention both profiles.
- [x] 11.8 Manual sanity check — `uv run task db-reset` on a clean DB; SQL: `SELECT p.name, COUNT(DISTINCT ac.id) classes, COUNT(DISTINCT a.id) assets, COUNT(DISTINCT pos.id) positions FROM profiles p LEFT JOIN asset_classes ac ON ac.profile_id = p.id LEFT JOIN assets a ON a.asset_class_id = ac.id LEFT JOIN positions pos ON pos.asset_id = a.id GROUP BY p.id ORDER BY p.display_order;` — confirm two rows, both with non-zero counts.
