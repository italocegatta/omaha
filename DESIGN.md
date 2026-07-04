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

### Tokens (current — post Phase 2)

OKLCH throughout. Values below match the current `app.css` `:root`
block. The Phase 1 audit found contrast failures in two class swatches
and hardcoded `color: #fff` on delete-confirm buttons; Phase 2 corrects
those and adds status-ink tokens. Ratios are computed against the
paired background noted in the "Pair" column and re-verified by
`tests/test_phase02_tokens.py`.

| Token              | Value (OKLCH)             | Pair (background) | Contrast | WCAG   | Role                                        |
|--------------------|---------------------------|-------------------|----------|--------|---------------------------------------------|
| `--bg`             | `oklch(0.975 0.003 60)`   | `--ink`           | 16.85:1  | AAA    | Body. True off-white, chroma ≈ 0. NOT cream.|
| `--surface`        | `oklch(1.0 0 0)`          | `--ink`           | 21:1     | AAA    | Cards, modals, popovers. Slightly lifted.   |
| `--surface-sunk`   | `oklch(0.96 0.003 60)`    | `--ink`           | 16.21:1  | AAA    | Form wells, input strips, table header.     |
| `--ink`            | `oklch(0.20 0.01 60)`     | `--bg`            | 16.85:1  | AAA    | Primary text, headings. Not pure black.     |
| `--ink-muted`      | `oklch(0.50 0.01 60)`     | `--bg`            | 5.59:1   | AA     | Secondary text, labels, captions.           |
| `--border`         | `oklch(0.90 0.005 60)`    | `--bg`            | n/a      | —      | Hairline borders (decorative).              |
| `--border-strong`  | `oklch(0.82 0.008 60)`    | `--bg`            | n/a      | —      | Card outer (decorative).                    |
| `--accent`         | `oklch(0.42 0.09 150)`    | `--bg`            | 7.54:1   | AAA    | Single accent. Reads as "the household's mark". |
| `--accent-ink`     | `oklch(0.98 0.005 150)`   | `--accent`        | 7.67:1   | AAA    | Text on `--accent` fill.                    |
| `--positive`       | `oklch(0.52 0.13 145)`    | `--bg`            | 4.84:1   | AA     | Gain, valid total, success.                 |
| `--positive-ink`   | `oklch(0.98 0.005 145)`   | `--positive`      | 4.92:1   | AA     | Text on `--positive` fill (e.g. import summary). |
| `--negative`       | `oklch(0.50 0.18 25)`     | `--bg`            | 6.13:1   | AA     | Loss, invalid total, error.                 |
| `--negative-ink`   | `oklch(0.98 0.005 25)`    | `--negative`      | 6.21:1   | AA     | Text on `--negative` fill (delete-confirm). |
| `--error-bg`       | `oklch(0.95 0.03 25)`     | `--error-fg`      | 6.88:1   | AA     | Inline error feedback background.           |
| `--error-fg`       | `oklch(0.45 0.15 25)`     | `--error-bg`      | 6.88:1   | AA     | Inline error feedback foreground.           |
| `--color-focus`    | `#2563eb`                 | `--bg`            | 4.81:1   | AA     | Focus ring (2px outline + 2px offset).      |
| `--fg`             | `var(--ink)`              | —                 | alias    | —      | Legacy alias (D-05).                        |
| `--muted`          | `var(--ink-muted)`        | —                 | alias    | —      | Legacy alias (D-05).                        |

> **Phase 2 corrections**
> * `--class-4` corrected from `#ef6c00` (2.87:1) → `oklch(0.53 0.13 50)` (5.16:1) on `--bg`.
> * `--class-6` corrected from `#00838f` (4.21:1) → `oklch(0.52 0.10 200)` (4.89:1) on `--bg`.
> * `--error-bg` / `--error-fg` converted from hex to OKLCH (no contrast regression).
> * `--negative-ink` and `--positive-ink` added so status text on filled
>   backgrounds does not have to hardcode `#fff` or `#000`.
> * `color: #fff` removed from `.class-delete-confirm-yes` and
>   `.dashboard-asset-delete-confirm-yes`; both now use `var(--negative-ink)`.

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
Contrast is measured against `--bg`; slots 1, 2, 3, 5 stay in hex as
the migration source until the full palette is committed to OKLCH.

| Slot  | OKLCH / hex (current `app.css`)        | Contrast vs `--bg` | Role                                    |
|-------|----------------------------------------|--------------------|-----------------------------------------|
| 1     | `#0a66c2` (target `oklch(0.50 0.14 250)`) | 5.29:1 (AA)     | Deep blue (replaces `#0a66c2` brand-ish)|
| 2     | `#2e7d32` (target `oklch(0.50 0.13 145)`) | 4.77:1 (AA)     | Deep green (close to `--accent` but distinct) |
| 3     | `#c62828` (target `oklch(0.50 0.18 25)`)  | 5.23:1 (AA)     | Deep red (matches `--negative`)         |
| 4     | `oklch(0.53 0.13 50)` (was `#ef6c00`)      | 5.16:1 (AA)     | Burnt orange (not tangerine). Phase 2 fix. |
| 5     | `#6a1b9a` (target `oklch(0.42 0.12 300)`) | 8.73:1 (AAA)    | Deep plum (not vibrant purple)          |
| 6     | `oklch(0.52 0.10 200)` (was `#00838f`)    | 4.89:1 (AA)     | Deep teal (not cyan). Phase 2 fix.       |

The 7th+ class cycles via the existing `nth-of-type(6n+N)` rules in
`app.css`. Slots 1, 2, 3, 5 remain hex (with the OKLCH target noted
for the next migration pass) — Phase 2 only changed slots that were
failing the 4.5:1 body-text threshold.

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

Token references use the names from the `:root` table above. "Bg"
means the body surface; "surface" means the lifted card surface;
"text" means the foreground color paired with that surface.

| Component           | Where                  | Tokens (fg / bg)                                    | Notes                                  |
|---------------------|------------------------|-----------------------------------------------------|----------------------------------------|
| App header          | `base.html`            | `--ink` on `--surface`; tab ink `--ink-muted`; tab hover / active `--ink`; tab active underline `--accent` | Logo on the left, top tab nav center, profile chip + signout on the right. Flat. |
| Profile picker      | `profile-switcher` select (`base.html`) | `--ink` on `--surface`; hover border `--accent`     | Native `<select>` chip in the header. Wraps every profile in the DB. |
| Tab nav             | `base.html`            | inactive tab `--ink-muted` on `--surface`; active tab `--ink` on `--surface` with `--accent` 2px underline | 4 tabs (Patrimônio / Rebalanceamento / Rentabilidade / Proventos). Active state via server-rendered `tab-nav__btn--active` modifier + `aria-current="true"`. Reuses the existing `--accent` token (no new color). |
| Login               | `login.html`           | `--ink` on `--surface`; error `--error-fg` on `--error-bg` | Single field, single button, error inline. |
| Portfolio header    | `patrimonio.html`      | `--ink` on `--surface`; gain `--positive` / `--negative` | Invested / current / gain. The hero. Wrapped by `data-testid="patrimonio-portfolio-header"` (F02 D3). |
| Patrimonio actions  | `patrimonio.html`      | `--ink` on `--surface`; primary hover `--accent`    | Right-aligned top-of-body button row carrying the legacy sidebar triggers (``Importar CSV`` / ``+ Novo ativo`` / ``+ Nova classe``). Testids preserved verbatim. |
| Class section       | `patrimonio.html`      | `--ink` on `--surface`; swatch `--class-{1..6}`     | Swatch + name + compare bar + asset list. |
| Compare bar         | `patrimonio.html`      | target `--border-strong`; current `--accent`       | Two stacked fills: target (gray) and current (accent). |
| Asset row           | `patrimonio.html`      | `--ink` on `--surface`; pct `--muted`; progress `--accent` | Name + value + pct + progress bar.     |
| Class table         | `classes.html`         | `--ink` on `--surface`; total `--positive` / `--negative` | Editable rows, percent total at bottom. |
| Asset editor        | `assets.html`          | `--ink` on `--surface`; remove hover `--error-fg` on `--error-bg` | Per-class sections, inline add/remove. |
| Class delete confirm | `patrimonio.html`     | `--negative-ink` on `--negative`                    | Inline confirm; cancel `--ink` on `--surface`. |
| Asset delete confirm | `patrimonio.html`     | `--negative-ink` on `--negative`                    | Inline confirm; cancel `--ink` on `--surface`. |
| Rebalance form      | `rebalance.html`       | `--ink` on `--surface`; submit `--accent-ink` on `--accent`; inline error `--error-fg` on `--error-bg` | In-body form (F02 D9 — no sidebar slot). Input + submit on a single row. |
| Rebalance plan      | `_rebalance_plan.html` | `--ink` on `--surface`; per-metric typography `--muted` | Card grid + sortable asset table + category summary + warnings list (F02 D5: no chip — `<code>` + body). |
| Stub page           | `rentabilidade.html` / `proventos.html` | `--ink` on `--surface`; secondary `--muted`; border `--border-strong` dashed | F02 stub card. Single heading + one body line. F03 / F04 replace. |
| Import form         | `import.html`          | `--ink` on `--surface`; submit `--accent-ink` on `--accent` | File picker, single submit.            |
| Review table        | `import_review.html`   | `--ink` on `--surface`; matched summary `--positive-ink` on `--positive` (tinted via color-mix) | Auto-matched summary + unmatched select. |
| Import error        | `import.html`          | `--error-fg` on `--error-bg`                        | Inline error block (reuses `.error`).  |
| Empty state         | various                | `--ink` on `--surface`; secondary `--muted`         | Single line, a link if actionable.     |
| Error message       | various                | `--error-fg` on `--error-bg`                        | Inline, top of form. No toast.         |

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

### Phase 2 (palette corrections) — current

The Phase 2 change set is small and reversible:

1. `:root` block in `app.css`:
   * `--class-4` → `oklch(0.53 0.13 50)` (replaces `#ef6c00`)
   * `--class-6` → `oklch(0.52 0.10 200)` (replaces `#00838f`)
   * `--error-bg` → `oklch(0.95 0.03 25)` (replaces `#fde8e8`)
   * `--error-fg` → `oklch(0.45 0.15 25)` (replaces `#8a1f1f`)
   * `--negative-ink: oklch(0.98 0.005 25)` (new)
   * `--positive-ink: oklch(0.98 0.005 145)` (new)
2. `.class-delete-confirm-yes` and `.dashboard-asset-delete-confirm-yes`
   swap `color: #fff` for `color: var(--negative-ink)`.
3. Legacy aliases (`--fg`, `--muted`) are unchanged.
4. `tests/test_phase02_tokens.py` re-derives every contrast ratio from
   the live `app.css`; passing the test is the contract.

For any future token change, the migration is:

1. Update the value in `:root` (or a component-scoped override).
2. Run `uv run pytest tests/test_phase02_tokens.py
   tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x`
   to confirm all pairs still meet their documented minimum.
3. Update the "Tokens (current)" table in this document with the new
   value and the new measured contrast.
4. If a component changes which token it consumes, update the
   component inventory table and the call site in the same commit.

Rollback: `git checkout HEAD -- src/omaha/static/app.css` reverts the
Phase 2 token changes. The new test file is reverted separately.

### Polish pass (planned)

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
