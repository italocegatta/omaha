## Context

Current dark palette (post-F05/F08) uses hue 60 warm-neutral throughout — body, surfaces, borders, ink all share the same hue family. Components blend together; no visual hierarchy between header, class section, and table. The owner validated a mockup (`/mockup` v4) using Catppuccin Frappe (cool blue-gray, hue ~274) that solves these issues via surface elevation, class-colored headers, and angular borders.

PRD §4.10 brand register: "domestic, no ornament" — this change is palette-only + component differentiation, no gradient/glow/glassmorphism.

## Goals / Non-Goals

**Goals:**
- Replace hue 60 warm-neutral tokens with Catppuccin Frappe OKLCH values (hue ~274).
- Differentiate components: elevated portfolio header, tinted class headers, sunk asset tables.
- Compact row density (−50% vertical padding).
- Angular borders (4px instead of 999px pills).
- Trade toggle: success green (Liberado) vs danger red (Bloqueado).
- Numeric cells at weight 600+ for contrast.
- Update DESIGN.md token table and color strategy.

**Non-Goals:**
- No light/dark toggle (dark-only per D-F05.10).
- No new capabilities — palette + component differentiation only.
- No gradient, glow, glassmorphism, or theme transition.
- No layout restructuring — same tab nav, same page structure.
- No changes to rebalance engine, seed, or data logic.

## Decisions

### D1 — Catppuccin Frappe as base palette

Use OKLCH values derived from Catppuccin Frappe (https://catppuccin.com/palette). Hue 274 (periwinkle blue) replaces hue 60 (warm brown) as the dominant hue family.

**Rationale:** Owner validated mockup v4. Cool blue-gray provides better visual hierarchy than warm brown. The Frappe variant (not Mocha/Latte) hits the right lightness range for a dark dashboard.

**Alternative considered:** Custom OKLCH palette — rejected because Catppuccin is a tested, cohesive palette with known contrast relationships.

### D2 — Keep existing token names, map new values

Preserve the current token namespace (`--bg`, `--surface`, `--surface-sunk`, `--ink`, `--ink-muted`, `--border`, `--border-strong`, `--accent`, `--positive`, `--negative`, `--error-bg`, `--error-fg`, `--class-1`..`--class-8`). Add `--surface-elevated` as new token. Do NOT introduce `--primary`, `--secondary`, `--success`, `--danger` — those are mockup-only names.

**Token mapping:**

| Token | Current (hue 60) | New (Catppuccin Frappe) |
|-------|------------------|------------------------|
| `--bg` | `oklch(0.18 0.01 60)` | `oklch(0.329 0.032 274.8)` |
| `--surface` | `oklch(0.22 0.012 60)` | `oklch(0.46 0.037 273.0)` |
| `--surface-sunk` | `oklch(0.15 0.01 60)` | `oklch(0.286 0.028 274.4)` |
| `--surface-elevated` | — | `oklch(0.395 0.034 275.9)` |
| `--ink` | `oklch(0.94 0.005 60)` | `oklch(0.92 0.04 273.3)` |
| `--ink-muted` | `oklch(0.65 0.01 60)` | `oklch(0.80 0.04 274.5)` |
| `--border` | `oklch(0.30 0.008 60)` | `oklch(0.521 0.039 274.0)` |
| `--border-strong` | `oklch(0.38 0.01 60)` | `oklch(0.58 0.04 274.0)` |
| `--accent` | `oklch(0.68 0.20 152)` | `oklch(0.783 0.073 184.6)` |
| `--accent-hover` | `oklch(0.74 0.20 152)` | `oklch(0.84 0.073 184.6)` |
| `--accent-ink` | `oklch(0.18 0.01 60)` | `oklch(0.20 0.02 274)` |
| `--positive` | `oklch(0.79 0.19 145)` | `oklch(0.812 0.107 133.4)` |
| `--negative` | `oklch(0.69 0.20 25)` | `oklch(0.717 0.124 19.4)` |
| `--error-bg` | `oklch(0.30 0.04 25)` | `oklch(0.35 0.06 19.4)` |
| `--error-fg` | `oklch(0.80 0.10 25)` | `oklch(0.80 0.10 19.4)` |
| `--alert-warn` | `oklch(0.78 0.16 75)` | `oklch(0.844 0.08 83.5)` |
| `--color-focus` | `oklch(0.65 0.15 250)` | `oklch(0.742 0.104 265.7)` |
| `--class-1` | `oklch(0.65 0.15 250)` | `oklch(0.742 0.104 265.7)` |
| `--class-2` | `oklch(0.72 0.13 130)` | `oklch(0.765 0.111 311.7)` |
| `--class-3` | `oklch(0.72 0.18 350)` | `oklch(0.783 0.073 184.6)` |
| `--class-4` | `oklch(0.75 0.13 50)` | `oklch(0.812 0.107 133.4)` |
| `--class-5` | `oklch(0.65 0.12 300)` | `oklch(0.844 0.08 83.5)` |
| `--class-6` | `oklch(0.72 0.10 200)` | `oklch(0.717 0.124 19.4)` |
| `--class-7` | `oklch(0.55 0.06 60)` | `oklch(0.65 0.04 274)` |
| `--class-8` | `oklch(0.60 0.02 250)` | `oklch(0.70 0.03 274)` |

**Rationale:** Keeping token names avoids a sweeping rename across templates and Python. The mockup's `--primary`/`--secondary`/`--success`/`--danger` names are mapped to existing tokens.

### D3 — Class header differentiation via tinted bg + border-bottom

Class section headers get `background: color-mix(in srgb, var(--class-N) 30%, var(--bg))` and `border-bottom: 2px solid var(--class-N)`. Remove the swatch square — the class name text carries the color.

**Rationale:** The mockup validated this approach. Tinted header provides class identity without ornament. Swatch square is redundant when the header itself is colored.

### D4 — Asset table uses --surface-sunk

Asset tables get `background: var(--surface-sunk)` for an inset feel. This creates visual hierarchy: portfolio header (elevated) > class section (surface) > table (sunk).

### D5 — Row padding compact

Reduce `.proposto-table td` padding from `0.55rem` to `0.28rem` (−50% vertical). More data density on screen.

### D6 — Angular borders

All pills, toggles, and badges: `border-radius: 999px` → `4px`. Consistent with the angular aesthetic validated in the mockup.

### D7 — Trade toggle differentiation

- Liberado: `background: color-mix(in srgb, var(--positive) 15%, var(--surface))`, `color: var(--positive)`.
- Bloqueado: `background: color-mix(in srgb, var(--negative) 12%, var(--surface))`, `color: var(--negative)`.

Currently Bloqueado is gray (neutral). Change makes restriction visually clear.

### D8 — Number contrast

All numeric cells (`.asset-value`, `.asset-pct`, currency pills) use `--ink` foreground at `font-weight: 600+`. Currently some use `--ink-muted`.

## Risks / Trade-offs

- **Contrast ratios shift significantly.** The new palette has higher lightness values for surfaces. Mitigation: re-derive all contrast ratios, update DESIGN.md token table, update `test_dark_mode_tokens.py` thresholds.
- **Python `_CLASS_COLORS` must sync.** The OKLCH tuple in `routes/pages.py` and `audit/inventory.py` must mirror new `--class-N` values. Mitigation: update both in the same PR.
- **Visual baselines break.** `task test-visual` will fail after the token swap. Mitigation: regenerate baselines in the same PR.
- **8→6 class color gap.** Mockup shows 6 classes; current system has 8. Mitigation: derive class-7 and class-8 from muted Catppuccin Frappe tones (warm-brown and slate equivalents).
