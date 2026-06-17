# 2.1 /assets and /api/assets callers

## Resolves: design §OQ3 (callers outside the test suite)

## Search
```
git grep -n "/assets" src/omaha/ scripts/
```

## Results

### GET /assets
- `src/omaha/routes/assets.py:87` — the handler itself (the
  candidate for retirement).
- `src/omaha/templates/assets.html` — the page template, only
  referenced by the route above. Once the route is gone, this
  template is orphaned (but still on disk; future polish slice
  may prune it).

### POST /assets (form-encoded)
- `src/omaha/routes/assets.py:122` — handler.
- `src/omaha/templates/assets.html:18` — `<form id="asset-form" action="/assets" method="post">`.
  This template is dead once the GET /assets route retires.

### POST /api/assets (JSON)
- `src/omaha/routes/assets.py:226` — handler.
- `src/omaha/templates/dashboard.html:922` — `fetch('/api/assets', ...)`. **Live caller.**

### PATCH /api/assets/{id}
- `src/omaha/routes/assets.py:343` — handler.
- `src/omaha/templates/dashboard.html:828` — `fetch('/api/assets/' + id, {method:'PATCH',...})`. **Live caller.**

### DELETE /api/assets/{id}
- `src/omaha/routes/assets.py:421` — handler.
- `src/omaha/templates/dashboard.html:986` — `fetch('/api/assets/' + id, ...)`. **Live caller.**

### POST /assets/{id}/delete
- `src/omaha/routes/assets.py:456` — handler.
- `src/omaha/templates/assets.html:45` — form button. **Dead
  once the GET /assets route retires.**

### scripts/
No callers.

## Decision inputs

- GET /assets: no live callers (template orphans). Safe to retire.
- PATCH /api/assets/{id}: live caller is the dashboard inline
  editor. **The route is load-bearing** — confirming §OQ2 will be
  resolved by the dashboard template grep (see 07-dashboard-patch-url.md).
- POST /assets (form), POST /assets/{id}/delete: dead but the
  route docstring explicitly preserves them ("a future polish
  slice may prune them"). Out of scope for this change.