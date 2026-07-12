## Why

Add-asset modal and header profile selector still read cramped on dark surface. Small controls, native number chrome, and low-contrast field treatment make frequent input work harder than needed.

## What Changes

- Widen add-asset modal slightly on desktop; keep full-width mobile fallback.
- Increase legibility of modal inputs with stronger contrast and cleaner spacing.
- Remove native number steppers from modal numeric inputs while keeping keyboard stepping.
- Left-align profile-switcher option text so `Família` reads as normal selectable option, not centered chip.
- No API, data, or backend behavior changes.

## Capabilities

### New Capabilities

- `dashboard-form-legibility`: dashboard header/modal form surfaces, input contrast, spinner-free numeric fields, and left-aligned profile selector presentation.

### Modified Capabilities

- None.

## Impact

- `src/omaha/templates/_patrimonio_add_asset_modal.html`
- `src/omaha/templates/base.html` (profile switcher block currently lives here)
- `src/omaha/static/app.css`
- Browser visuals, screenshot baselines, and selector expectations for compact form surfaces
- No route, model, or API contract changes
