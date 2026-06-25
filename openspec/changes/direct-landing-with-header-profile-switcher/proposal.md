## Why

The login flow today forces every operator through a dedicated
`GET /profiles` picker page (templates/profiles.html) before the
dashboard renders, even though only two profiles exist and only
the logged-in user can pick among theirs. The picker adds a
round-trip on every login, prevents a logged-in user from peeking
at the other family member's portfolio, and buries the profile
identity in two places (a small "Perfil: X" header cell + a
large "Bem-vindo, X" dashboard h1). The family wants to log in
and land directly on their own dashboard, then switch to the
other person's portfolio from inside the dashboard header.

## What Changes

- **`POST /login`** sets `active_profile_id` to the logged-in
  user's first profile (by `display_order`) and redirects 303
  straight to `/`. The `/profiles` picker page is removed.
  **BREAKING**: the `/profiles` route is deleted; the picker
  template is deleted.
- **`POST /profiles/{id}/select`** loses its per-user
  ownership check — any logged-in user can switch to any
  profile. The header chip drives this route.
- **Header (base.html)** adds a profile chip built around a
  native `<select>`. The chip lists every profile in the DB
  (not just the logged-in user's); switching rewrites the
  form action client-side and submits. The currently-selected
  option carries a `✓` glyph.
- **Header (base.html)** adds a muted viewer label
  ("Ana") before the chip when `session.user_id !=
  active_profile.user_id`. Hidden when they match.
- **Dashboard (dashboard.html)** removes the
  `h1.profile-name` "Bem-vindo, X" element. The serif
  treatment (Source Serif 4) stays on `.portfolio-stat-value`
  via app.css:158 — the visual hero migrates to the portfolio
  header values without any CSS change.
- **Logout form (base.html)** is renamed from
  `class="profile-switcher"` to `class="logout-form"` to free
  the class name. The matching CSS selector at app.css:196-199
  is renamed. The misnomer was a pre-existing bug; this change
  corrects it as a side effect.
- **Empty-state copy** in dashboard.html rewrites
  "Você ainda não tem classes" → "Esta carteira ainda não tem
  classes" so the third-person register survives when viewer
  ≠ owner.
- **BDD `login.feature`** flips: `Esquema do Cenário: Login +
  profile pick OK` becomes `Login + dashboard direto`. The
  picker click step disappears; the dashboard step verifies
  the landing profile's name on the chip instead of the h1.
- **BDD `profile_isolation.feature`** is repurposed and
  renamed to `profile_sharing.feature`. Both scenarios flip
  to assert the new contract: Ana logs in, switches to
  Italo's profile, and sees Italo's seeded classes on the
  dashboard. The "isolation" guarantee the old feature
  asserted is explicitly inverted.

## Capabilities

### New Capabilities
- `profile-landing`: post-login routing + canonical landing
  profile selection + removal of the `/profiles` picker.
- `header-profile-switcher`: the header chip affordance +
  viewer label + server-rendered switcher options.
- `cross-profile-sharing`: dashboard data is visible to any
  logged-in user regardless of profile ownership (replaces
  the implicit `cross-profile-isolation` guarantee).

### Modified Capabilities
<!-- No existing spec captures profile selection or
     cross-profile isolation today — checked
     `openspec/specs/`: no `profile-*` or
     `cross-profile-*` spec exists. All three capabilities
     are net-new. -->

## Impact

- **Routes** (`src/omaha/routes/auth.py`, `pages.py`):
  login redirect target flips; `/profiles` GET route deleted;
  `/profiles/{id}/select` POST ownership check loosened.
- **Templates** (`src/omaha/templates/`):
  `profiles.html` deleted; `base.html` gains chip + viewer
  label + `.logout-form` rename; `dashboard.html` loses h1,
  empty-state copy edit.
- **Stylesheet** (`src/omaha/static/app.css`):
  `.profile-switcher` selector renamed to `.logout-form`;
  new `.profile-switcher` chip rules (~30 lines, hover,
  focus, option glyph, mobile breakpoint at 480px).
- **Tests** (~12 files in `tests/`): the `/profiles`
  intermediate-step assertions in `test_auth.py`,
  `test_e2e.py`, `test_pages_routes.py`,
  `test_imports_routes.py` flip; the
  `_login_and_select_profile` helpers in
  `test_assets_*.py`, `test_classes_*.py`,
  `test_real_csv_flow.py`, `test_import_*.py`,
  `test_quote_routes.py` simplify (drop the explicit
  `/profiles/{id}/select` POST); the
  `_profile_id_for(client, name)` regex helper in
  `test_imports_routes.py` swaps to a direct DB read.
- **E2E (Playwright)** in `tests/e2e/test_user_journey.py`,
  `test_import_user_journey.py`, `test_full_journey.py`,
  `test_user_journey_rebalance.py`:
  `_login_and_select_italo` drops the `wait_for_url(/profiles)`
  + picker click.
- **BDD**: `tests/bdd/step_defs/_workflows.py`
  `login_and_pick_profile` simplifies to `login_and_land`
  (drops picker click + `/profiles` wait); the carve-out
  shrinks to the `Login fail — senha errada` scenario in
  `login.feature`. `login.feature` schema flips; the
  remaining `.feature` files inherit the new workflow.
  `profile_isolation.feature` renamed to
  `profile_sharing.feature` with inverted assertions.
- **No DB migration**: `Profile.user_id` stays — it remains
  useful as the post-login canonical-profile lookup key and
  as an audit-trail field for "who owns this profile." It
  no longer gates cross-profile viewing.