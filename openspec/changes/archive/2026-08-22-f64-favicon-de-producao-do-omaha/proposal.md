## Why

Omaha currently has no production favicon, so browser tabs and bookmarks lack a
stable product identifier. F64 adds the owner-approved geometric Omaha mark at
the browser sizes where recognition matters, using the existing dark-only,
teal-accent visual direction.

## What Changes

- Add one production SVG favicon at `src/omaha/static/favicon.svg`.
- Integrate one shared `<link rel="icon">` reference in
  `src/omaha/templates/base.html`, inherited by every page using the base
  template.
- Define acceptance for browser discovery, SVG rendering at 16px and 32px,
  dark-palette contrast, and owner validation of actual browser rendering after
  review and before finalize. The owner-approved written direction is the
  pre-Apply gate; no preview example is required.
- Keep implementation limited to the favicon asset and shared head integration.

## Capabilities

### New Capabilities

- `production-favicon`: Provides Omaha production favicon asset and shared head
  discovery contract for browser tabs and bookmarks.

### Modified Capabilities

None.

## Impact

- Runtime files: `src/omaha/static/favicon.svg` and
  `src/omaha/templates/base.html` only.
- Existing FastAPI static serving at `/static/` serves the SVG; no route or
  server change is required from current code evidence.
- Focused tests will inspect the shared head reference and SVG structure,
  plus mandatory browser-rendered 16px/32px evidence during Apply. No
  full-suite run is planned at proposal time.
- Non-goals: app logo redesign, alternate favicon candidates, manifest/PWA
  work, preview server/files, UI palette changes, and page-specific favicon
  links.
