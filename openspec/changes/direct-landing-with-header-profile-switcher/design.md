## Context

Two-operator family portfolio app. Today the post-login flow
forces every operator through a `GET /profiles` picker page
before the dashboard renders; the picker only shows profiles
the logged-in user owns; cross-profile viewing is impossible
because `POST /profiles/{id}/select` enforces
`profile.user_id == session user_id` (404 otherwise). The
profile identity shows in two places: a muted "Perfil: X"
header cell and a serif "Bem-vindo, X" dashboard h1.

The change collapses the picker, makes any profile selectable
by any logged-in user, binds the landing profile to the
logged-in user's own first profile, and exposes a header chip
that drives cross-profile switches. The dashboard's h1 welcome
text goes away; the serif treatment survives on the portfolio
header numerics.

No DB migration. `Profile.user_id` stays as the post-login
landing key and as an audit-trail field; it no longer gates
cross-profile viewing.

## Goals / Non-Goals

**Goals:**
- One click from login to dashboard; no intermediate page.
- Header chip lists every profile; switching is one click.
- Viewer identity visible when viewer ≠ owner.
- Existing visual register preserved (off-white body, deep
  fern accent, Source Serif 4 on numerics, Inter for UI).
- No Alpine x-for races (server-rendered options).
- All existing tests updated to the new flow; no test
  references the picker page after this change.

**Non-Goals:**
- Per-user authorization (the family password is shared).
- Multi-family / multi-tenant support.
- Mobile-first redesign (desktop polish first; mobile media
  query ships but is not the visual priority).
- Renaming or restyling the existing class color palette.
- DB migration (no schema change).
- Cross-profile audit log entries (the viewer is visible in
  the header but not currently written to the audit trail).

## Decisions

### D1 — Native `<select>` with server-rendered options

The chip is a plain HTML `<select>` inside a `<form
method="post">`. Options render server-side (no `<template
x-for>`). On change, a 1-line `onchange` handler rewrites the
form's `action` to `/profiles/{value}/select` and calls
`form.submit()`.

**Why not Alpine.** The AGENTS.md select-binding gotcha
(`x-init $nextTick` + `x-effect` to fight the inner-template
race) only matters when options render via `<template
x-for>`. Server-rendered options have no race. Native
`<select>` is the boring honest answer; an Alpine popover
would risk the "AI-generated" feel flagged by the
`frontend-design` skill.

**Why not a popover menu.** A custom popover (Alpine
`x-show` panel with click-outside-to-close, focus trap,
keyboard nav, transition animation) is ~60 lines of JS and
CSS for a control that the native `<select>` already provides
in 6 lines. Reserve the budget.

### D2 — Canonical landing = `Profile.user_id == session.user_id`, first by display_order

`POST /login` runs:

```python
profile = (
    db.query(Profile)
    .filter(Profile.user_id == user.id)
    .order_by(Profile.display_order)
    .first()
)
request.session["active_profile_id"] = profile.id
```

**Why not literal `profile.name == user.username`.** The
seed happens to match (Italo user owns "Italo" profile;
Ana user owns "Ana" profile), but a future operator who
renames a profile should still land on their own profile.
`user_id` is the stable key; `display_order` provides the
deterministic "which one" rule when a user owns more than
one (future-proofing; today each user owns exactly one).

**Why not keep username-field-out-of-routing.** The user
explicitly chose: "login as Italo → Italo's profile; login
as Ana → Ana's profile." Username is therefore routing-
relevant. Keeping the field also preserves the audit-trail
"who said they were" signal at login time.

### D3 — Drop the `profile.user_id != user.id` 404 check on `POST /profiles/{id}/select`

`select_profile` becomes:

```python
profile = db.get(Profile, profile_id)
if profile is None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
request.session["active_profile_id"] = profile.id
```

**Why.** The new contract is "any logged-in user can view
any profile." The ownership check is the only thing
preventing it. A non-existent id still 404s; a real id
(owned by anyone) binds.

**Collateral change.** Every per-profile ownership gate in
`routes/classes.py`, `routes/assets.py`, `routes/imports.py`
(≈5 functions: `_existing_assets_for_profile`, `_load_preview`,
`_validate_class_ownership`, `asset_class.profile_id !=
profile.id` checks) loosens from "must belong to the user" to
"must belong to the active profile." The viewer-vs-owner
distinction is no longer security-relevant.

### D4 — Header right cell: viewer label + chip + logout

```html
<div class="app-header-right">
  {% if viewer.id != owner.id %}
    <span class="viewer-label" data-testid="viewer-label">{{ viewer.username }}</span>
  {% endif %}
  <form class="profile-switcher" method="post"
        data-testid="profile-switcher-form"
        id="profile-switcher-form">
    <select name="profile_id"
            data-testid="profile-switcher"
            onchange="this.form.action='/profiles/'+this.value+'/select'; this.form.submit()">
      {% for p in profiles %}
        <option value="{{ p.id }}" {% if p.id == owner.id %}selected{% endif %}>
          {{ p.name }}{% if p.id == owner.id %} ✓{% endif %}
        </option>
      {% endfor %}
    </select>
  </form>
  <form class="logout-form" method="post" action="/logout">
    <button type="submit">Sair</button>
  </form>
</div>
```

The chip's `<select>` carries the `current-state ✓` glyph in
the option label so the user sees what they have when they
open the menu. The viewer label is muted (`--ink-muted`,
0.85rem) and hidden when redundant.

**Why ✓ not •.** In a 2-item menu, the bolder glyph reads
as a definite "checked" state. `•` (dot) reads as a marker,
not a selection — better when the menu is long and the dot
is the only differentiator. With 2 items, ✓ wins on legibility.

**Why hide viewer when redundant.** The chip already shows
"Ana" when Ana views Ana's own portfolio. A second "Ana"
label is visual noise; the session user_id is implicit from
the chip text. When viewer ≠ owner, the label is the only
"you are Ana" signal — that's when it earns its place.

### D5 — Logout form class rename `profile-switcher` → `logout-form`

`base.html:35` carries `class="profile-switcher"` on the
logout form. `app.css:196-199` styles that selector. Rename
both. The new chip form picks up `class="profile-switcher"`
honestly.

**Cost.** 1 template line + 1 CSS selector rename. Zero test
coupling (grep survey: no test greps `.profile-switcher`).

**Why now and not as a separate change.** The misnomer is
one rename away from correctness; deferring forces the new
chip to invent a fresh name AND carry the historical lie.
Cheaper to fix together.

### D6 — Dashboard h1 removal; serif treatment migrates to portfolio numerics

`dashboard.html:4`'s `<h1 class="profile-name" data-testid="profile-name">Bem-vindo, {{ profile.name }}</h1>`
is deleted. The serif treatment at `app.css:158`
(`.profile-name, .portfolio-stat-value { font-family: "Source Serif 4"... }`)
shrinks to just `.portfolio-stat-value`. The visual hero
becomes the portfolio header values (R$ 1.000 / R$ 1.100 /
R$ 100), which were already serif.

**Why remove the h1 instead of repurposing it.** The user
chose the header chip for the switcher. Keeping the h1 as a
non-clickable hero adds chrome that says nothing new
("Bem-vindo, Italo" when you're already inside the dashboard
for Italo is repetitive). Removing it lets the data own the
top of the page.

**Empty-state copy edit.** The dashboard's "Você ainda não
tem classes" becomes "Esta carteira ainda não tem classes"
so the third-person register survives when viewer ≠ owner.

### D7 — BDD workflow `login_and_pick_profile` shrinks to `login_and_land`

```python
def login_and_land(page, live_url, profile, password="test-password"):
    page.goto(f"{live_url}/login")
    page.fill('input[name="username"]', profile)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_url(re.compile(r"/$"), timeout=5000)
```

The picker click + `/profiles` wait disappear. The carve-out
shrinks from `login.feature + profile_isolation.feature` to
just `login.feature`'s "Login fail — senha errada" scenario
(wrong-password still asserts the user is NOT on `/profiles`
or `/`).

The other 5 `.feature` files (`asset_crud`, `class_crud`,
`import`, `target_pct`, `derived_display`) inherit the new
flow through the workflow without touching their `.feature`
text.

**`profile_isolation.feature` → `profile_sharing.feature`.**
Both scenarios flip: instead of asserting "Ana doesn't see
Italo's classes," they assert "Ana sees Italo's classes
after switching via the chip." The Gherkin steps change in
place (no need to delete + re-add; the file is rewritten).

## Risks / Trade-offs

- **Dropping `user_id`-based ownership on mutations.** Every
  per-profile guard in classes/assets/imports relaxes. A
  logged-in Ana can now mutate Italo's portfolio. This is
  the explicit new contract — but the audit log doesn't yet
  record "viewer X mutated profile Y." If audit fidelity
  matters later, a separate change adds the
  `active_profile.user_id` + `session.user_id` to the audit
  record. **Mitigation**: this change does not promise audit
  fidelity; document the gap in `profile_sharing` spec.

- **Pasted / hand-crafted form posts.** A power user can
  craft `POST /profiles/999/select` to switch to any profile
  id, including ids from other families (single-tenant
  today, but defensible in multi-tenant future). The 404 on
  non-existent ids is the only guard. **Mitigation**: the
  app is single-tenant by design; the threat model does not
  include adversarial form crafting. Note as a follow-up if
  the app ever ships multi-tenant.

- **Test-suite maintenance surface.** ~12 test files reference
  `/profiles` + the picker step. The mechanical edit is
  straightforward but spread out; one careless file leaves a
  broken integration test behind. **Mitigation**: the
  `tests/conftest.py::_INTEGRATION_PREFIXES` allow-list
  surfaces the breakage via `task test-integration` (the
  broad-fanout run catches misses the per-file run misses).

- **Mobile header density.** At <480px, the new chip + viewer
  label + sair + nav = 4 cells in a `gap: 1.5rem` row. Cramped.
  **Mitigation**: ship desktop-first; add a `@media (max-width:
  480px)` rule that stacks into 2 rows (logo + chip on row 1,
  nav + sair on row 2). Mark as a follow-up if it slips.

- **`<select>` on iOS.** Native `<select>` on iOS Safari opens
  the system picker wheel — not the dropdown menu desktop
  browsers show. This is platform-correct but visually
  inconsistent with the styled chip. **Mitigation**: accept
  it. Styling the wheel is out of scope; the chip's idle
  state still matches the desktop register.

- **Profile rename breaks `display_order` landing rule.** If
  an operator renames "Italo" to "Papaia" but the seed still
  has display_order=0 for that profile, the landing still
  works (`user_id`-based). If they re-order via drag-and-drop
  (not yet implemented), landing still works. **Mitigation**:
  no current surface for re-order; future drag-and-drop must
  preserve the rule.

## Migration Plan

No DB migration. No data backfill. The dev DB picks up the
new behavior on next `uv run task serve`. The prod DB picks
up the new behavior on next deploy.

`uv run task db-reset` after the change applies cleanly:
the seed still creates Italo + Ana users with their
matching profiles; the new `POST /login` flow picks the
right profile per user.

Rollback = revert the commit. No data shape changes.

## Open Questions

None blocking. Two nice-to-haves deferred:
- Audit log entry: "viewer=X mutated profile=Y."
- Mobile-first header redesign (chip + nav + sair + viewer
  in 2 rows <480px).
