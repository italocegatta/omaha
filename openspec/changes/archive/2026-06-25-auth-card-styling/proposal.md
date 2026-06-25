## Why

`/login` and `/profiles` lost their centred card layout when
`dashboard-action-sidebar` deleted the `main { max-width: 640px;
margin: 2rem auto; padding: 0 1.5rem; }` rule (the dashboard now
ships its own `.dashboard-card` / `.dashboard` grid). The auth
pages fall through to zero margin and feel amputated on a 1920px
monitor.

## What Changes

- `/login` and `/profiles` wrap their content in a new
  `<div class="auth-card">` element.
- New `.auth-card` CSS rule: `max-width: 480px; margin: 4rem auto;
  padding: 2rem 2.25rem; --surface; 1px border; 8px radius`. Mirrors
  the dashboard-card aesthetic from dashboard-action-sidebar
  (DESIGN.md "cards are flat with 1px solid var(--border)").
- Auth-card scoped input + button styles for focus ring + accent
  fill (mirrors `.new-class-input` / `.btn` focus pattern).

No new route, no migration, no spec delta beyond a CSS-only touch-up.

## Capabilities

<!-- No spec delta: the auth-card is pure CSS + template markup. -->

## Impact

- `src/omaha/templates/login.html` — wraps content in `.auth-card`.
- `src/omaha/templates/profiles.html` — wraps content in `.auth-card`.
- `src/omaha/static/app.css` — adds `.auth-card` rule set.
