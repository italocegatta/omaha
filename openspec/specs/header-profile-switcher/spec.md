# header-profile-switcher Specification

## Purpose
TBD - created by archiving change direct-landing-with-header-profile-switcher. Update Purpose after archive.
## Requirements
### Requirement: The header renders a profile chip with every profile as an option

The header (rendered by `templates/base.html`) SHALL render a
profile chip for every authenticated page. The chip SHALL be a
native `<select>` inside a `<form method="post">`. The `<select>`
SHALL list every `Profile` row in the database (ordered by
`display_order` ascending), with the currently-active profile
marked via the HTML `selected` attribute.

#### Scenario: Chip lists all profiles
- **WHEN** an authenticated user loads any page with the header
- **THEN** the rendered HTML contains exactly one `<select>`
  inside `form.profile-switcher`
- **AND** that `<select>` contains one `<option>` per `Profile`
  row in the DB (in `display_order` order)
- **AND** the `<option>` for `session["active_profile_id"]` has
  the `selected` attribute

#### Scenario: Chip's selected option matches the active profile
- **WHEN** an authenticated user holds a session with
  `active_profile_id=X` and loads the dashboard
- **THEN** the rendered HTML's chip shows profile X's name as the
  displayed selection (server-rendered `selected` attribute; no
  client-side race)

#### Scenario: Switching profiles submits the select route
- **WHEN** the user picks a different option from the chip's
  `<select>`
- **THEN** the parent form's `action` attribute is rewritten to
  `/profiles/{new_id}/select` (client-side, before submit)
- **AND** the form is submitted (POST) → the server binds
  `active_profile_id` to the new profile → the user lands back on
  `/` with the dashboard re-rendered for the new profile

### Requirement: Any logged-in user can switch to any profile

`POST /profiles/{profile_id}/select` SHALL bind the requested
profile to the session regardless of which `User` owns it. The
prior per-user ownership check (`profile.user_id != session
user_id` → 404) SHALL be removed.

#### Scenario: Ana switches to Italo's profile
- **WHEN** Ana is logged in (session `user_id` = Ana's id) and
  posts `POST /profiles/{italo_profile_id}/select`
- **THEN** the response is 303 to `/`
- **AND** `session["active_profile_id"]` = Italo's profile id

#### Scenario: Non-existent profile id returns 404
- **WHEN** any logged-in user posts
  `POST /profiles/{nonexistent_id}/select`
- **THEN** the response is 404 (no profile row to bind)

### Requirement: The header shows a viewer label when viewer != owner

The system MUST render a muted viewer label (the viewer's
`username`) immediately before the profile chip when
`session["user_id"]` differs from `active_profile.user_id`.
When the two ids match, the viewer label MUST be omitted (the
chip alone identifies the portfolio).

#### Scenario: Viewer label shows when Ana views Italo
- **WHEN** Ana is logged in and `active_profile_id` points to
  Italo's profile
- **THEN** the rendered header includes the text "Ana" in a muted
  element (`--ink-muted`) before the profile chip
- **AND** the chip displays "Italo" as the active selection

#### Scenario: Viewer label hidden when Ana views her own portfolio
- **WHEN** Ana is logged in and `active_profile_id` points to
  Ana's own profile
- **THEN** the rendered header does NOT include a separate
  viewer label (the chip "Ana" alone is sufficient)

### Requirement: The logout form wears the .logout-form class

The `<form>` that posts to `/logout` SHALL carry
`class="logout-form"`. The historical misnomer
`class="profile-switcher"` on this form SHALL be removed. The
`.profile-switcher` class is reserved for the new header chip.

#### Scenario: Logout form selector matches .logout-form
- **WHEN** the rendered header HTML is inspected
- **THEN** the form whose `action="/logout"` carries
  `class="logout-form"`
- **AND** no element with `class="profile-switcher"` exists in
  the header except the new chip form

### Requirement: The dashboard h1 profile-name element is removed

The dashboard template SHALL NOT render an `<h1>` with class
`profile-name` or any element carrying the `data-testid="profile-name"`
attribute. The serif treatment (Source Serif 4 via
`.profile-stat-value`) stays on the portfolio header values.

#### Scenario: Dashboard has no profile-name heading
- **WHEN** an authenticated user loads `/`
- **THEN** the rendered HTML contains no element with
  `data-testid="profile-name"`
- **AND** no `<h1>` with `class="profile-name"` exists
- **AND** the portfolio header still renders with the Source
  Serif 4 treatment on `.portfolio-stat-value`

### Requirement: The empty-state copy uses third-person register

The dashboard's empty-state copy SHALL read
"Esta carteira ainda não tem classes" (third-person, portfolio-
neutral) instead of "Você ainda não tem classes" (second-person,
viewer-specific).

#### Scenario: Empty state copy survives viewer switch
- **WHEN** Ana is logged in and views Italo's empty dashboard
- **THEN** the empty-state copy reads
  "Esta carteira ainda não tem classes"
- **AND** no occurrence of the old "Você ainda não tem classes"
  copy remains in the rendered HTML

