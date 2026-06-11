# Design

Working visual system for Omaha. This is a **living** doc: it captures the
direction the polish pass is aiming for, not a final, frozen spec. The CSS in
`src/omaha/static/app.css` is the current state; the polish pass evolves it
toward the targets below.

## Register

Product — family portfolio app. Design serves the function. The dashboard
is the most important surface; the editors and import flow are functional
back-of-house.

## Color strategy

**Restrained, with one committed accent.**

The body surface is a true off-white, not a cream. The current `#fafaf7`
falls in the warm-neutral band the rest of the AI-default landscape
occupies; we move off it. Warmth, when it appears, lives in the accent and
in a small amount of intentional texture on the surface — not in the
background tint. The accent is one color, used at ≤10% of the surface,
committed.

### Tokens (target)

OKLCH throughout. Values below are the polish-pass targets; the current
`app.css` uses hex equivalents and will be migrated.

| Token             | OKLCH                     | Hex (current→target) | Role                                           |
|-------------------|---------------------------|----------------------|------------------------------------------------|
| `--bg`            | `oklch(0.975 0.003 60)`   | `#fafaf7` → off-white | Body. True off-white, chroma ≈ 0. NOT cream.   |
| `--surface`       | `oklch(1.0 0 0)`          | `#fff`               | Cards, modals, popovers. Slightly lifted.      |
| `--surface-sunk`  | `oklch(0.96 0.003 60)`    | `#fcfcfb` → drop     | Form wells, input strips, table header.        |
| `--ink`           | `oklch(0.20 0.01 60)`     | `#1a1a1a`            | Primary text, headings. Not pure black.        |
| `--ink-muted`     | `oklch(0.50 0.01 60)`     | `#6b6b6b`            | Secondary text, labels, captions.              |
| `--border`        | `oklch(0.90 0.005 60)`    | `#d8d8d3`            | Hairline borders, table dividers.              |
| `--border-strong` | `oklch(0.82 0.008 60)`    | `#e0e0e0`            | Card outer (when no shadow is used).           |
| `--accent`        | `oklch(0.42 0.09 150)`    | `#0a66c2` → deep fern| Single accent. Reads as "the household's mark".|
| `--accent-ink`    | `oklch(0.98 0.005 150)`  | —                    | Text on `--accent` fill.                        |
| `--positive`      | `oklch(0.52 0.13 145)`    | `#2e7d32`            | Gain, valid total, success.                    |
| `--negative`      | `oklch(0.50 0.18 25)`     | `#c62828`            | Loss, invalid total, error.                    |

### Accent rationale

A deep, slightly desaturated fern green (`hue 150`, not `hue 145` of the
positive color). It reads as garden, home, growth — not as "money green"
(which is the crypto / price-ticker lane) and not as a luxury forest
(which would need to be near-black at very low chroma). The class-2 swatch
stays in the same family but is visibly distinct from the accent so the
accent does not collide with class data.

### Class swatches (6-color data palette)

Distinct, well-spaced, reads as data — not as brand. Order matters:
swatch 1 is the first class on the dashboard, swatch 2 the second, etc.

| Slot  | OKLCH                    | Role                                    |
|-------|--------------------------|-----------------------------------------|
| 1     | `oklch(0.50 0.14 250)`   | Deep blue (replaces `#0a66c2` brand-ish)|
| 2     | `oklch(0.50 0.13 145)`   | Deep green (close to `--accent` but distinct) |
| 3     | `oklch(0.50 0.18 25)`    | Deep red (matches `--negative`)         |
| 4     | `oklch(0.62 0.15 50)`    | Burnt orange (not tangerine)            |
| 5     | `oklch(0.42 0.12 300)`   | Deep plum (not vibrant purple)          |
| 6     | `oklch(0.52 0.10 200)`   | Deep teal (not cyan)                    |

The 7th+ class cycles via the existing `nth-of-type(6n+N)` rules in
`app.css`. The hex values currently in CSS (`#0a66c2`, `#2e7d32`, etc.)
are the migration source.

## Typography

**One family, multiple weights, with one serif display exception on the
dashboard heading only.**

- **UI sans**: `Inter` (self-hosted, with system fallback). Currently the
  app uses `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
  sans-serif`; Inter is a clean upgrade with consistent metrics and good
  tabular figures. Fall back to system if the font file is not loaded.
- **Display serif (dashboard only)**: `Source Serif 4` (or `IBM Plex
  Serif`) for the portfolio-header values and the "Italo" / "Ana Livia"
  profile name. Used at most twice on the dashboard. NOT used in the
  editors, NOT used on login, NOT used on the import flow. Serif in a
  product register must be surgical or it reads as luxury.
- **Numerics**: tabular figures (`font-feature-settings: "tnum"`) on
  every number, percentage, and currency value. Spreadsheet look.

### Scale

Body 16px / 1.55 line-height. Body line length capped at 65ch where
possible (the dashboard naturally stays under 60ch at 760px max-width).

| Role                | Size  | Weight | Letter-spacing       | Notes                          |
|---------------------|-------|--------|----------------------|--------------------------------|
| Display (h1)        | clamp(1.75rem, 3vw, 2.5rem) | 600 | -0.02em | `text-wrap: balance`   |
| Section heading (h2)| 1.1rem | 600    | -0.005em             |                                |
| Body                | 1rem  | 400    | 0                    |                                |
| Label / caption     | 0.78rem | 500 | 0.04em uppercase     | Reserved for class labels      |
| Numeric (display)   | 1.4rem | 600   | -0.01em, tnum        | Portfolio header values        |
| Numeric (inline)    | 0.92rem | 500 | tnum                 | Asset rows                     |

Letter-spacing floor: nothing tighter than -0.04em on display. The current
CSS has no display letter-spacing declared; the polish pass sets -0.02em
on h1 only and leaves the rest at default.

## Spacing

8px base. The dashboard uses generous vertical rhythm:

- Section-to-section: 24px
- Card inner padding: 20px (down from 32px on the class editor)
- Form field gap: 12px
- Table row vertical padding: 8px

## Radius

Cards: 10px (down from 8px current, well below the 12-16px ceiling).
Buttons / inputs: 6px. Pills / chips: 999px (only where actually pill-
shaped, like the import status badge).

No element gets a 24-32-40px radius. The class editor's 8px cards and
8px buttons are within range; the only intentional rounded shape above
12px is the small `3px` on the class color swatch.

## Elevation

**One rule:** cards are flat or shadowed, never both.

- Dashboard class sections: flat with `1px solid var(--border)`. No
  shadow. The "card" affordance is the border + spacing, not a drop
  shadow.
- Editor cards (class editor, asset editor, import review): flat with
  `1px solid var(--border-strong)`. The current `0 1px 3px rgba(0,0,0,0.05)`
  is removed — the soft shadow paired with a 1px border is the ghost-
  card tell the skill flags.
- Modal / popover: `0 4px 8px rgba(0,0,0,0.08)`. Used only when a layer
  needs to read as above the page.

## Iconography

None required for the polish pass. The current app uses no icons
(`x` and `−` are text characters, not icon font). The compare bar and
the per-asset progress bar are pure CSS. If a future surface needs an
icon, use stroke-based monochrome SVG at 1.5px stroke and 18-20px
viewport; never filled / duotone / colored icons.

## Motion

Conservative. All transitions ≤ 200ms, `cubic-bezier(0.16, 1, 0.3, 1)`
(quint-out). Used at three specific moments only:

1. The compare-bar fill animates from 0% to its final width over 400ms
   on dashboard load. Single time, on the only page that matters.
2. The per-asset progress bar fills over 300ms, staggered 40ms per
   asset, capped at 8 assets per class (then snaps to final state).
3. Form submit buttons get a `0.96` scale + 100ms transition on `:active`
   for tactile feedback.

Everything else is instant. No hover transitions on cards. No fade-in
on page load (the page is already visible, transitions pause on hidden
tabs and headless renderers, reveal animations that gate visibility
ship blank pages — do not do it).

### Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Components (initial inventory)

| Component           | Where                  | Notes                                  |
|---------------------|------------------------|----------------------------------------|
| App header          | `base.html`            | Logo, nav, profile, signout. Flat.     |
| Profile picker      | `profiles.html`        | Two large buttons. Quiet, no marketing.|
| Login               | `login.html`           | Single field, single button, error inline. |
| Portfolio header    | `dashboard.html`       | Invested / current / gain. The hero.   |
| Class section       | `dashboard.html`       | Swatch + name + compare bar + asset list. |
| Compare bar         | `dashboard.html`       | Two stacked fills: target (gray) and current (accent). |
| Asset row           | `dashboard.html`       | Name + value + pct + progress bar.     |
| Class table         | `classes.html`         | Editable rows, percent total at bottom. |
| Asset editor        | `assets.html`          | Per-class sections, inline add/remove. |
| Import form         | `import.html`          | File picker, single submit.            |
| Review table        | `import_review.html`   | Auto-matched summary + unmatched select. |
| Empty state         | various                | Single line, a link if actionable.     |
| Error message       | various                | Inline, top of form. No toast.         |

## Anti-patterns (this project, named)

When the polish pass encounters one of these, the right move is to
rewrite the element, not patch it:

- `border-left` or `border-right` > 1px on any list item, card, or
  callout. The current CSS does not have this; preserve that.
- Gradient text via `background-clip: text`. None currently; preserve.
- Ghost cards (`1px border + drop-shadow ≥ 16px blur`). The current
  shadow is `0 1px 3px` which is below the threshold; the polish
  pass removes shadows from cards entirely and uses the border alone.
- Side-stripe alerts. The error and empty-state elements use full-
  width backgrounds, not left stripes.
- Eyebrow labels (small uppercase tracked text above every section).
  The dashboard h2 is the only section heading; no eyebrow above it.
  Section labels on the class table are the only "small uppercase"
  text, and they are table column headers (a real, semantic role),
  not section eyebrows.

## Migration path

1. Update `:root` tokens in `app.css` to the OKLCH values above. Keep
   the class-color hex values inline (they are migration source) until
   the swatch palette is committed.
2. Remove `box-shadow` from `.class-editor`, `.asset-editor`,
   `.import-page`, `.import-review`, and `.class-section`. Replace
   with a single 1px border.
3. Migrate the body bg away from `#fafaf7` to the new off-white.
4. Introduce `font-feature-settings: "tnum"` on numeric data; add
   `text-wrap: balance` on h1 elements; add the `prefers-reduced-motion`
   media query.
5. Add the compare-bar and per-asset progress fill animations.
6. Add the Source Serif 4 / IBM Plex Serif display face, scoped to
   `.portfolio-header` and `.profile-name` only.

The polish command drives this end-to-end.
