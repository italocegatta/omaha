## Context

F64 is a bounded browser-identity slice. `src/omaha/static/` is already
mounted at `/static` by `create_app`, and `StaticCacheControlMiddleware`
already applies the shared static-asset cache policy. `base.html` is the
shared Jinja parent for login and application pages, but its `<head>` has no
favicon link. No `src/omaha/static/favicon.svg` currently exists.

### Code map

- `src/omaha/templates/base.html:<head>` (lines 3–30): shared document head;
  current CSS, font, Alpine, and `head_extra` links establish the insertion
  point for one global favicon link. Child templates inherit this head.
- `src/omaha/static/favicon.svg`: absent today; target production static
  asset. It must be self-contained because browser favicon loading does not
  inherit page CSS variables.
- `src/omaha/main.py::create_app` (static mount around lines 256–260): mounts
  package static directory at `/static`; existing boundary serves the new SVG
  without route changes.
- `src/omaha/middleware.py::StaticCacheControlMiddleware`: applies
  `Cache-Control: no-cache` to `/static/*`; favicon follows existing asset
  freshness behavior without middleware changes.
- `src/omaha/routes/pages.py::_templates` and page `TemplateResponse` calls:
  application pages use the shared Jinja environment; no page route needs a
  favicon-specific change.
- `DESIGN.md:58–98` (current tokens) and `DESIGN.md:218–263` (iconography):
  canonical dark-only register, `--bg`, teal `--accent`, no ornament, and no
  ad-hoc icon expansion. F64 uses the palette direction but is not a Material
  Symbols catalog addition.
- `tests/test_iconography_tokens.py` and `tests/test_pages_routes.py`: existing
  patterns for source-contract assertions and static `TestClient` responses;
  they are inspection references, not files to modify for F64.
- `tests/e2e/conftest.py::live_url` and `tests/e2e/conftest.py::page`: existing
  isolated Chromium/server fixtures for browser discovery and in-memory
  rasterization checks; no new preview server or committed image is needed.

### Current relevant flow

1. Browser requests an HTML page rendered from a template extending
   `base.html`.
2. `base.html` emits stylesheet/font/script links, but currently emits no
   `rel="icon"` link.
3. Browser therefore has no Omaha favicon to discover.
4. `/static` is already served from `src/omaha/static/` by FastAPI
   `StaticFiles`; static responses pass through the existing no-cache
   middleware.

Boundary conditions: SVG is a standalone image, so CSS custom properties from
`app.css` cannot be relied on; all required colors and geometry must be inside
the asset. All pages inheriting `base.html`, including `/login` and the
authenticated pages, must receive the same reference. Page-specific
`head_extra` content must remain additive and must not become favicon wiring.

## Goals / Non-Goals

**Goals:**

- Deliver one self-contained production SVG with fixed `viewBox="0 0 32 32"`.
- Render a text-free geometric “O” made from clear ledger-like linear rails,
  with sufficient negative space to survive 16px rasterization.
- Use dark background mapped to DESIGN.md `--bg` and teal mark mapped to
  DESIGN.md `--accent`; encoded SVG colors must achieve at least 4.5:1
  contrast and remain stable without page CSS.
- Add exactly one shared favicon discovery link in `base.html`.
- Keep browser rendering legible at 16px and structurally intact at 32px.

**Non-Goals:**

- No app logo/wordmark redesign, header branding change, or UI palette change.
- No alternate favicon candidates, fallback PNG/ICO, emoji, or reduced
  wordmark.
- No manifest, PWA metadata, Apple touch icon, theme-color, or install prompt
  work.
- No page-specific favicon links, route changes, static-serving changes,
  preview server, committed preview files, animation, gradients, or external
  SVG references.
- No edits to `DESIGN.md`, `app.css`, roadmap, or existing capability specs.

## Decisions

### 1. Add one SVG asset and one shared link

`favicon.svg` is the sole production candidate. `base.html` will add one
`<link rel="icon" type="image/svg+xml" href="/static/favicon.svg">` in the
existing `<head>`. This uses the already-mounted static boundary and ensures
all `base.html` children receive identical discovery behavior. Alternatives
rejected: per-page links (drift), inline data URI (harder cache/debug
boundary), and PNG/ICO variants (extra candidates outside approved scope).

### 2. Use token-derived explicit SVG colors

The SVG will encode explicit sRGB-compatible values derived from DESIGN.md's
current `--bg` (`oklch(0.329 0.032 274.8)`) and `--accent`
(`oklch(0.783 0.073 184.6)`) tokens. External SVG rendering cannot resolve
`app.css` variables, and explicit values preserve favicon behavior in browser
tabs, bookmarks, and direct `/static/favicon.svg` requests. Implementation
must verify the selected encoded pair against the canonical token intent and
the ≥4.5:1 contrast requirement; it must not alter the source CSS tokens.

### 3. Prefer filled, aligned rails over fine strokes

The mark will use a 32px coordinate grid, integer-aligned filled geometry, a
dark opaque canvas, and a teal compound “O” built from parallel orthogonal or
chamfered ledger rails. No text, tiny counters, hairlines, or decorative
detail may carry recognition. Filled geometry avoids stroke-width and
device-pixel ambiguity during 16px rasterization. The owner-approved written
direction remains the visual authority and is the pre-Apply gate. No mock,
static preview, or browser preview example is required before Apply.

### 4. Validate contract and browser output separately

Focused source/static tests will assert exact shared-link uniqueness, SVG
structure, intrinsic viewBox, forbidden content, static response, and palette
contrast. A focused Playwright test during Apply will load an existing test
page, verify favicon discovery, rasterize the asset at 16px and 32px in memory,
and assert non-empty dark/teal output without generating committed preview
files. After review, and before finalize, owner validation of the actual
browser rendering at both sizes is mandatory; pixel heuristics do not replace
that validation.

## Change map

| File / symbol | From | To | Reason |
|---|---|---|---|
| `src/omaha/static/favicon.svg` (new asset) | File absent; no production favicon bytes | Self-contained 32px SVG with opaque dark canvas and one teal geometric ledger-rail “O”, no text/animation/external refs | Provide ownable, scalable browser mark that survives 16px rendering |
| `src/omaha/templates/base.html:<head>` | Head has no favicon discovery link | One exact `rel="icon"` SVG link to `/static/favicon.svg`; existing links and `head_extra` remain unchanged | Make favicon discoverable on every inherited page without page drift |

No other production, static, template, documentation, roadmap, manifest, or
test-support integration is intended. Focused test files listed in `tasks.md`
are validation additions only and do not expand runtime scope.

## Risks / Trade-offs

- **[Risk]** A visually attractive mark may collapse into a generic blob at
  16px. **Mitigation:** integer-aligned filled rails, mandatory browser
  16px/32px raster checks during Apply, and owner validation after review.
- **[Risk]** SVG color syntax or CSS-variable use may fail in favicon contexts.
  **Mitigation:** self-contained sRGB-compatible fills, no external styles,
  direct static response test, and browser load test.
- **[Risk]** Multiple inherited or page-specific links could create browser
  candidate ambiguity. **Mitigation:** source test requires exactly one F64
  favicon link in `base.html` and checks child templates do not add links.
- **[Risk]** Favicon cache behavior could hide a deployed replacement.
  **Mitigation:** reuse existing `/static/` middleware behavior; no bespoke
  cache policy or server change.
- **[Risk]** Scope may drift into branding or PWA work. **Mitigation:** exact
  two-file runtime change map and explicit non-goals; review rejects unrelated
  files.

## Migration Plan

No data or schema migration. Apply adds asset and shared link atomically;
rollback removes those two runtime changes. Existing routes and static mount
remain unchanged. Before Apply, the owner-approved written direction is the
only approval gate; no preview example is required. During Apply, browser
rendering at 16px and 32px must be recorded. After review, owner must validate
that actual rendering at both sizes before finalize; without that validation,
change remains blocked from finalize.

## Open Questions

None blocking proposal. Exact rendered geometry is bounded by this design and
the approved written direction. Browser rendering remains mandatory focused
Apply evidence, followed by owner validation after review and before finalize.

## Implementation Decisions

- **Explicit sRGB asset colors:** `--bg` and `--accent` resolve to `#303446`
  and `#81c8be` for standalone SVG rendering. This preserves token intent
  without depending on page CSS variables. Evidence: `coloraide` conversion
  from the documented OKLCH values and independent WCAG luminance check in
  `tests/test_production_favicon.py` measure 6.41:1 contrast.
- **Single even-odd filled rail path:** the mark uses one integer-aligned
  compound path over an opaque rect, avoiding stroke/device-pixel ambiguity
  while retaining a continuous geometric O at 16px and 32px. Evidence:
  `src/omaha/static/favicon.svg` contains only the root, canvas rect, and mark
  path; browser raster assertions cover both sizes.
