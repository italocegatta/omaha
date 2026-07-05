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

**Inverted to dark warm-neutral. Register unchanged.**

The body surface is a dark warm-neutral (`oklch(L≈0.18 hue≈60 chroma≈0.01)`),
NOT pure black (`oklch(0 0 0)`) and NOT cold blue-gray (the GitHub-dark
register). Hue 60 is preserved from the previous light palette so the
warmth that used to live in the accent and on the body tint now lives
in the accent and in **lightness lifts** on the surface layers: cards
lift via `+0.04` on `--surface`, form wells sink via `-0.03` on
`--surface-sunk`. No `box-shadow` is reintroduced to compensate — the
register stays flat (the "cards are flat or shadowed, never both" rule
holds). The accent remains one committed color (fern-green, hue 150)
but its lightness is lifted (`L≈0.68`) so it carries on the dark
background without losing its brand voice.

Inverting is not introducing ornamentation. No gradient, no glow, no
glassmorphism, no transition between themes. F05 is the new default;
no toggle, no `prefers-color-scheme` media query — those would belong
to a future slice if the owner asks for a light-mode option.

### Tokens (current — post F05)

OKLCH throughout, calibrated against the dark `--bg`. Values match
the current `app.css` `:root` block. F05 lifted every previous
token's lightness (where required) to maintain WCAG 2.1 AA on the
new background; hues are preserved for the warm family (60 / 150 /
145 / 25) so the warmth reads consistently. Ratios in the "Contrast"
column are measured against the noted "Pair" background and re-
verified by `tests/test_dark_mode_tokens.py`.

| Token              | Value (OKLCH)             | Pair (background) | Contrast | WCAG   | Role                                        |
|--------------------|---------------------------|-------------------|----------|--------|---------------------------------------------|
| `--bg`             | `oklch(0.18 0.01 60)`     | `--ink`           | 13.6:1   | AAA    | Body. Dark warm-neutral. NOT pure black.    |
| `--surface`        | `oklch(0.22 0.012 60)`    | `--ink`           | 12.3:1   | AAA    | Cards, modals, popovers. Lift via claridade. |
| `--surface-sunk`   | `oklch(0.15 0.01 60)`     | `--ink`           | 15.1:1   | AAA    | Form wells, input strips, table header.     |
| `--ink`            | `oklch(0.94 0.005 60)`    | `--bg`            | 13.6:1   | AAA    | Primary text, headings. Not pure white.     |
| `--ink-muted`      | `oklch(0.65 0.01 60)`     | `--bg`            | 5.5:1    | AA     | Secondary text, labels, captions.           |
| `--border`         | `oklch(0.30 0.008 60)`    | `--bg`            | n/a      | —      | Hairline borders (decorative).              |
| `--border-strong`  | `oklch(0.38 0.01 60)`     | `--bg`            | n/a      | —      | Card outer (decorative).                    |
| `--accent`         | `oklch(0.68 0.13 150)`    | `--bg`            | 5.3:1    | AA     | Single accent. Lightness-lifted.            |
| `--accent-hover`   | `oklch(0.74 0.13 150)`    | `--bg`            | 6.6:1    | AAA    | Accent on hover (slightly lifted).          |
| `--accent-ink`     | `oklch(0.18 0.01 60)`     | `--accent`        | 5.5:1    | AA     | Text on `--accent` fill.                    |
| `--positive`       | `oklch(0.70 0.16 145)`    | `--bg`            | 7.6:1    | AAA    | Gain, valid total, success. Lightness-lifted. |
| `--positive-ink`   | `oklch(0.18 0.01 60)`     | `--positive`      | 7.7:1    | AAA    | Text on `--positive` fill (dark on lifted). |
| `--negative`       | `oklch(0.70 0.18 25)`     | `--bg`            | 5.4:1    | AA     | Loss, invalid total, error. Lightness-lifted. |
| `--negative-ink`   | `oklch(0.18 0.01 60)`     | `--negative`      | 5.5:1    | AA     | Text on `--negative` fill (dark on lifted). |
| `--error-bg`       | `oklch(0.30 0.04 25)`     | `--error-fg`      | 5.4:1    | AA     | Inline error feedback background (sunk red). |
| `--error-fg`       | `oklch(0.80 0.10 25)`     | `--error-bg`      | 5.4:1    | AA     | Inline error feedback foreground (lifted). |
| `--color-focus`    | `oklch(0.65 0.15 250)`    | `--bg`            | 3.2:1    | 3:1 UI | Focus ring (2px outline + 2px offset).      |
| `--fg`             | `var(--ink)`              | —                 | alias    | —      | Legacy alias (D-05).                        |
| `--muted`          | `var(--ink-muted)`        | —                 | alias    | —      | Legacy alias (D-05).                        |

> **F05 corrections (over Phase 2)**
> * `--bg` inverted from `oklch(0.975 0.003 60)` (off-white) →
>   `oklch(0.18 0.01 60)` (dark warm-neutral). Hue 60 preserved;
>   chroma stays ≈ 0.01 to keep neutrality.
> * `--surface` and `--surface-sunk` re-derived around the new `--bg`
>   using lightness deltas instead of relative offset (D-F05.2).
> * `--ink` and `--ink-muted` flipped to light values; lightness
>   calibrated for AA on the dark body.
> * `--accent`, `--positive`, `--negative` lightness-lifted (NOT hue-
>   shifted) so the fern-green / positive-green / coral identities
>   stay readable on dark (D-F05.1, D-F05.3).
> * `--accent-ink`, `--positive-ink`, `--negative-ink` inverted to
>   dark (`oklch(0.18 0.01 60)`) because the fills are now lightness-
>   lifted — dark text on light fill is the AAA combination.
> * `--error-bg` and `--error-fg` re-split: `--error-bg` sinks (red +
>   darkness ≈ 0.30), `--error-fg` lifts (red + lightness ≈ 0.80)
>   per D-F05.7.
> * `--color-focus` converted from `#2563eb` to OKLCH
>   `oklch(0.65 0.15 250)`; hue 250 (blue-foco) preserved, lightness
>   adjusted for ≥3:1 against the dark `--bg` (D-F05.6). The
>   `, #2563eb` hex fallback in `outline: ... var(--color-focus, ...)`
>   rules is removed (the token is now always present).
> * `color-scheme: light dark` → `color-scheme: dark` (D-F05.10).
>   No `prefers-color-scheme` media query is added.

### Accent rationale

Fern green at lightness 0.68 (`oklch(0.68 0.13 150)`, hue 150) carries
on dark warm-neutral without losing its brand voice. The hue stays the
same as the previous Phase 2 accent (`hue 150`, not the positive's `hue
145`) so the "garden, home, growth" reading survives the polarity flip.
The lifted lightness means accent fills read as "the household's mark"
against `--bg` rather than as a generic bright color swatch. The
class-2 swatch is hue-shifted to 130 (D-F05.4) to keep visual distance
from `--positive` at hue 145 — both are green but they sit on opposite
sides of the spectrum so the data-color never reads as a gain-color.

### Class swatches (6-color data palette)

Lightness-lifted variants of the previous swatch hex. Each slot is
now OKLCH end-to-end (the hex migration sources are no longer used
in `app.css`). Contrast is measured against the dark `--bg`; all
six slots reach AA (≥ 4.5:1). Slot 2 carries the new hue-shift to 130
(D-F05.4) — distinct from `--positive` at hue 145.

| Slot  | OKLCH (current `app.css`)            | Contrast vs `--bg` | Role                                    |
|-------|---------------------------------------|--------------------|-----------------------------------------|
| 1     | `oklch(0.65 0.15 250)`                | 5.1:1 (AA)         | Blue (lightness-lifted from `#0a66c2`)  |
| 2     | `oklch(0.72 0.13 130)`                | 7.3:1 (AAA)        | Leaf green (hue-shifted away from `--positive`). D-F05.4. |
| 3     | `oklch(0.72 0.18 25)`                 | 6.0:1 (AA)         | Red (lightness-lifted from `#c62828`)   |
| 4     | `oklch(0.75 0.13 50)`                 | 8.4:1 (AAA)        | Burnt orange (lightness-lifted)         |
| 5     | `oklch(0.65 0.12 300)`                | 5.3:1 (AA)         | Plum (lightness-lifted from `#6a1b9a`)  |
| 6     | `oklch(0.72 0.10 200)`                | 8.9:1 (AAA)        | Teal (lightness-lifted)                  |

The 7th+ class cycles via the existing `nth-of-type(6n+N)` rules in
`app.css`. All six slots are OKLCH end-to-end after F05.

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
means the body surface (dark warm-neutral post-F05); "surface"
means the lifted card surface (lightness `+0.04` over `--bg` post-
F05 — cards lift via claridade, no `box-shadow`); "text" means the
foreground color paired with that surface.

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

### F05 (dark mode palette swap) — current

The F05 change set is a single token-layer rewrite of `:root` in
`app.css`. Hue 60 is preserved on the body warmth axis; every other
token is re-derived against the new dark surface. The set is
reversible by reverting the file.

1. `:root` block in `app.css` — see the "F05 corrections (over Phase 2)"
   block above for the per-token deltas.
2. `color-scheme: light dark` → `color-scheme: dark`. No
   `prefers-color-scheme` media query is added (D-F05.10).
3. The hex fallbacks inside `outline: 2px solid var(--color-focus,
   #2563eb)` are removed — `--color-focus` is now always present.
4. `tests/test_dark_mode_tokens.py` replaces `tests/test_tokens.py`
   (the previous "Phase 2 — PALT-01 / PALT-02" suite). It re-derives
   the dark-mode contract: body warmth, lightness lifts on the
   swatches and status fills, swatch-2 hue-shift, and the pair
   table sourced from the table above.

For any future token change, the migration is:

1. Update the value in `:root` (or a component-scoped override).
2. Run `uv run pytest tests/test_dark_mode_tokens.py
   tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x`
   to confirm all pairs still meet their documented minimum.
3. Update the "Tokens (current)" table in this document with the new
   value and the new measured contrast.
4. If a component changes which token it consumes, update the
   component inventory table and the call site in the same commit.

Rollback: `git checkout HEAD -- src/omaha/static/app.css` reverts the
F05 token changes. The new test file is reverted separately.

### Phase 2 (palette corrections) — historical

Phase 2 (archived `2026-06-16-phase-02-palette`) replaced the pre-token
hex values for `--class-4`, `--class-6`, `--error-bg`, `--error-fg`,
and added `--negative-ink` / `--positive-ink`. F05 supersedes it by
flipping the same tokens for dark mode; the structural migration to
OKLCH that Phase 2 started is now complete (all 6 swatch slots are
OKLCH end-to-end).

### Polish pass (planned)

Post-F05. Out of scope for F05 itself but kept as the residual
backlog — each item below is a future slice candidate.

1. Migrate leftover `background: #fff` literals across `.class-color-
   swatch`, `.btn`, `.import-page`, etc. to `var(--surface)` so
   isolated white islands disappear on the dark body (run
   `grep -nE '#fff|#ffffff' src/omaha/static/app.css` to confirm).
2. Migrate the `color-mix(in srgb, #<hex> 38%, var(--surface))` calls
   in `.import-class-cell--cls-{0..7}` to the lifted `--class-N`
   tokens so the import preview tints read correctly on dark
   `--surface`.
3. Add `font-feature-settings: "tnum"` on numeric data; add
   `text-wrap: balance` on h1 elements; add the `prefers-reduced-motion`
   media query.
4. Add the compare-bar and per-asset progress fill animations.
5. Add the Source Serif 4 / IBM Plex Serif display face, scoped to
   `.portfolio-header` and `.profile-name` only.

The polish command drives this end-to-end.
