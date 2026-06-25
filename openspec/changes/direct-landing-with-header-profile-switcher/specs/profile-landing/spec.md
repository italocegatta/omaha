## ADDED Requirements

### Requirement: Login lands directly on the operator's own dashboard

The system SHALL set `active_profile_id` to the logged-in user's
own first profile (by `display_order` ascending) on every
successful `POST /login`, and redirect 303 to `/`. The system
SHALL NOT render an intermediate profile picker.

#### Scenario: Login as Italo lands on Italo's dashboard
- **WHEN** a user posts valid credentials with `username="Italo"`
- **THEN** the response is a 303 redirect to `/`
- **AND** `session["active_profile_id"]` equals the `Profile.id`
  whose `user_id` matches the logged-in user and which has the
  lowest `display_order`

#### Scenario: Login as Ana lands on Ana's dashboard
- **WHEN** a user posts valid credentials with `username="Ana"`
- **THEN** the response is a 303 redirect to `/`
- **AND** `session["active_profile_id"]` equals the `Profile.id`
  whose `user_id` matches the logged-in user and which has the
  lowest `display_order`

#### Scenario: Login with invalid credentials re-renders the form
- **WHEN** a user posts credentials that fail bcrypt verification
- **THEN** the response is 200 with the login template re-rendered
- **AND** the session contains no `user_id` and no
  `active_profile_id`

#### Scenario: Re-login clears stale active profile
- **WHEN** a logged-in user posts valid credentials again (any
  username)
- **THEN** the session's `active_profile_id` is replaced with the
  freshly-computed landing profile (not carried over from the
  prior session)

### Requirement: The /profiles picker page is removed

The system SHALL NOT expose a `GET /profiles` route. The template
`templates/profiles.html` SHALL be removed. Any bookmarked link to
`/profiles` SHALL redirect to `/`.

#### Scenario: /profiles returns 404
- **WHEN** an authenticated user requests `GET /profiles`
- **THEN** the response is 404

#### Scenario: Bookmark to /profiles does not break
- **WHEN** an authenticated user follows a stale bookmark to
  `/profiles`
- **THEN** the response is a 404 (acceptable: the route no longer
  exists; the user has no valid reason to reach it from the UI)

### Requirement: Stale session falls back to login

The system SHALL treat a session that has `user_id` but no
resolvable `active_profile_id` (missing, deleted, or pointing to
a profile whose `user_id` no longer matches) by clearing the
stale key and redirecting to `/login`.

#### Scenario: Stale active_profile_id after profile deletion
- **WHEN** an authenticated user holds a session with
  `active_profile_id` pointing to a row that was deleted
- **THEN** `GET /` clears `active_profile_id` and redirects 303
  to `/login`
- **AND** a subsequent `POST /login` re-establishes a fresh
  landing profile

#### Scenario: Empty session with no active_profile_id
- **WHEN** an authenticated user holds a session with no
  `active_profile_id` (e.g., after the picker-page removal)
- **THEN** `GET /` redirects 303 to `/login`

### Requirement: The login form keeps the username field

The login form SHALL render an `input[name=username]` field (blank
by default; no `value` attribute carries state across requests).
The form SHALL continue to require `username` + `password`.

#### Scenario: Username field renders blank
- **WHEN** a user opens `GET /login`
- **THEN** the username `input` has no `value` attribute (or has
  `value=""`) — never carries a prior session's username

#### Scenario: Login submission still validates the username
- **WHEN** a user posts `username=""` with a valid password
- **THEN** the response is 200 with the form re-rendered and an
  error message (no `User` row matches an empty username)