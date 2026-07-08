# Design

Working visual system for Omaha. This is a **living** doc: it captures the
direction the polish pass is aiming for, not a final, frozen spec. The CSS in
`src/omaha/static/app.css` is the current state; the polish pass evolves it
toward the targets below.

## Register

**Status Invest maximal, sidebar não reintroduzida.** Decisão owner
2026-07-07 (D02 archived; memorial em `PRD.md` §4.10). Referência
primária: investidor.statusinvest.com.br — pacote maximal: dados
densos, sticky/hover/total em tabelas, dividers hairlines, eyebrow
labels, compare bar, accents vivos. Top nav F02 (4 tabs) permanece;
o maximalismo se materializa dentro das superfícies, não em nova
chrome lateral. Sem light/dark toggle (dark-only D-F05.10
mantido). F14: body Catppuccin Frappe cool blue-gray (hue ~274,
replacing hue 60 warm-neutral). Accent teal hue 184.6. Class
palette 6-color Catppuccin Frappe-derived. Surface elevation
hierarchy: --surface-elevated / --surface / --surface-sunk.
Class headers: tinted bg + 2px solid class-color border. Angular
borders (4px). Trade toggle: Liberado green / Bloqueado red.

Product — family portfolio app. Design serves the function. The dashboard
is the most important surface; the editors and import flow are functional
back-of-house.

## Color strategy

**Inverted to Catppuccin Frappe cool blue-gray. Target register: Status Invest
maximal (D02).**

The body surface is Catppuccin Frappe cool blue-gray (`oklch(0.329 0.032 274.8)`,
hue ~274), replacing the previous warm brown (hue 60). The Frappe variant
provides better visual hierarchy through surface elevation: body sinks to
`--bg`, cards lift to `--surface` (+0.131 lightness), form wells sink to
`--surface-sunk` (-0.043), and portfolio header lifts to `--surface-elevated`
(+0.066). No `box-shadow` is reintroduced to compensate — the register stays
flat. The accent shifts from emerald (hue 152) to teal (hue 184.6) to match
the Catppuccin Frappe accent palette.

Inverting is not introducing ornamentation. No gradient, no glow, no
glassmorphism, no transition between themes. F05 is the new default;
no toggle, no `prefers-color-scheme` media query — those would belong
to a future slice if the owner asks for a light-mode option.

### Target register (D02)

Status Invest maximal (D02 archived 2026-07-07). Tokens derivados
em F08 — tabela "Tokens (current)" abaixo é a verdade operativa.
F14: Catppuccin Frappe swap (hue 60 → hue ~274). Accent teal hue
184.6. Class palette 6-color Catppuccin Frappe-derived. Surface
elevation hierarchy: --surface-elevated / --surface / --surface-sunk.
Class headers: tinted bg (30% class-color) + 2px solid border-bottom.
Angular borders (4px). Trade toggle: Liberado green / Bloqueado red.
`_CLASS_COLORS` Python OKLCH end-to-end (sem hex drift).

### Tokens (current)

OKLCH throughout. All pairs measured against `--bg` and verified by
`tests/test_dark_mode_tokens.py`. Catppuccin Frappe cool blue-gray
palette (hue ~274). `color-scheme: dark`; no `prefers-color-scheme`.

| Token              | Value (OKLCH)             | Pair (background) | Contrast | WCAG   | Role                                        |
|--------------------|---------------------------|-------------------|----------|--------|---------------------------------------------|
| `--bg`             | `oklch(0.329 0.032 274.8)` | `--ink`           | ~5.8:1   | AA     | Body. Catppuccin Frappe base.               |
| `--surface`        | `oklch(0.46 0.037 273.0)`  | `--ink`           | ~4.5:1   | AA     | Cards, modals, popovers. Lift via claridade. |
| `--surface-sunk`   | `oklch(0.286 0.028 274.4)` | `--ink`           | ~6.5:1   | AAA    | Form wells, input strips, table header.     |
| `--surface-elevated` | `oklch(0.395 0.034 275.9)` | `--ink`         | ~5.2:1   | AA     | Portfolio header (lifted over --bg). F14.    |
| `--ink`            | `oklch(0.92 0.04 273.3)`   | `--bg`            | ~5.8:1   | AA     | Primary text, headings.                     |
| `--ink-muted`      | `oklch(0.80 0.04 274.5)`   | `--bg`            | ~4.0:1   | AA-lrg | Secondary text, labels, captions.           |
| `--border`         | `oklch(0.521 0.039 274.0)` | `--bg`            | n/a      | —      | Hairline borders (decorative).              |
| `--border-strong`  | `oklch(0.58 0.04 274.0)`   | `--bg`            | n/a      | —      | Card outer (decorative).                    |
| `--accent`         | `oklch(0.783 0.073 184.6)` | `--bg`            | ~5.5:1   | AA     | Single accent. F14: teal Catppuccin Frappe. |
| `--accent-hover`   | `oklch(0.84 0.073 184.6)`  | `--bg`            | ~7.0:1   | AAA    | Accent on hover (lifted).                   |
| `--accent-ink`     | `oklch(0.20 0.02 274)`     | `--accent`        | ~5.5:1   | AA     | Text on `--accent` fill.                    |
| `--positive`       | `oklch(0.812 0.107 133.4)` | `--bg`            | ~6.0:1   | AAA    | Gain, valid total, success. Catppuccin green. |
| `--positive-ink`   | `oklch(0.20 0.02 274)`     | `--positive`      | ~6.0:1   | AAA    | Text on `--positive` fill (dark on lifted). |
| `--negative`       | `oklch(0.717 0.124 19.4)`  | `--bg`            | ~4.2:1   | AA-lrg | Loss, invalid total, error. Catppuccin red. |
| `--negative-ink`   | `oklch(0.20 0.02 274)`     | `--negative`      | ~4.2:1   | AA-lrg | Text on `--negative` fill (dark on lifted). |
| `--error-bg`       | `oklch(0.35 0.06 19.4)`    | `--error-fg`      | ~5.0:1   | AA     | Inline error feedback background (sunk red). |
| `--error-fg`       | `oklch(0.80 0.10 19.4)`    | `--error-bg`      | ~5.0:1   | AA     | Inline error feedback foreground (lifted).  |
| `--alert-warn`     | `oklch(0.844 0.08 83.5)`   | `--bg`            | ~7.0:1   | AAA    | Amber warning. Catppuccin Frappe amber.     |
| `--color-focus`    | `oklch(0.742 0.104 265.7)` | `--bg`            | ~4.5:1   | 3:1 UI | Focus ring. Matches --class-1 blue.         |
| `--fg`             | `var(--ink)`              | —                 | alias    | —      | Legacy alias (D-05).                        |
| `--muted`          | `var(--ink-muted)`        | —                 | alias    | —      | Legacy alias (D-05).                        |


### Accent rationale

Teal (`oklch(0.783 0.073 184.6)`, hue 184.6, chroma 0.073) is the
Catppuccin Frappe accent. F14 swaps from emerald (hue 152, chroma
0.20) to teal (hue 184.6, chroma 0.073) to match the Frappe
palette. The teal sits at lightness 0.783 — above positive (0.812)
in hue distance but below it in lightness, so the brand mark and
gain-green stay visually distinct. `--positive` at hue 133.4 (green)
and `--accent` at hue 184.6 (teal) have a 51° hue gap — well above
the 6° minimum invariant.

The class-2 swatch is lavender (hue 311.7) — distinct from both
accent and positive. Class-3 is teal (same as accent) — intentional
reuse of the brand color as a class identity.

### Class swatches (8-color data palette)

Catppuccin Frappe-derived OKLCH palette. F14 replaces the previous
hue 60 warm-neutral class colors. Each slot is OKLCH end-to-end in
both `app.css` and the Python `_CLASS_COLORS` tuple. Contrast is
measured against the dark `--bg`; all six primary slots reach AA
(≥ 4.5:1). Slots 7-8 extend the palette with muted blue-gray tones.

| Slot  | OKLCH (current `app.css`)            | Contrast vs `--bg` | Role                                    |
|-------|---------------------------------------|--------------------|-----------------------------------------|
| 1     | `oklch(0.742 0.104 265.7)`            | ~4.5:1 (AA)        | Blue (Catppuccin Frappe primary).       |
| 2     | `oklch(0.765 0.111 311.7)`            | ~4.8:1 (AA)        | Lavender (Catppuccin Frappe secondary). |
| 3     | `oklch(0.783 0.073 184.6)`            | ~5.5:1 (AA)        | Teal (= accent, Catppuccin Frappe).     |
| 4     | `oklch(0.812 0.107 133.4)`            | ~6.0:1 (AAA)       | Green (Catppuccin Frappe success).      |
| 5     | `oklch(0.844 0.08 83.5)`              | ~7.0:1 (AAA)       | Amber (Catppuccin Frappe warning).      |
| 6     | `oklch(0.717 0.124 19.4)`             | ~4.2:1 (AA-lrg)    | Red (Catppuccin Frappe danger).         |
| 7     | `oklch(0.65 0.04 274)`                | ~3.5:1             | Muted blue-gray (7th cycle slot).       |
| 8     | `oklch(0.70 0.03 274)`                | ~4.0:1             | Slate (8th cycle slot).                 |

The 7th+ class cycles via the existing `nth-of-type(6n+N)` rules in
`app.css`. All eight slots are OKLCH end-to-end; the matching
`_CLASS_COLORS` tuple in Python mirrors the same values.

## Typography

**Inter variable body + Red Hat Display 700+ nas superfícies
proeminentes de dados.** Decisão D02 (archived 2026-07-07) substitui
o display serif (Source Serif 4 / IBM Plex Serif) por **sans**
display — register maximalista lê fintech-pro em sans, não em serif.
**F09 archived 2026-07-07 — current = sans display.** Source Serif 4
retired do build; app.css carrega Red Hat Display em 4 seletores
(`.portfolio-stat-value`, `.app-header-wordmark`,
`.empty-state-step-number`, `.rebalance-stat-value`) + body Inter
variable com `tnum, cv01, ss01, ss02`. Spec `typography-tokens`
captura o contrato.

- **UI sans**: `Inter` (Google Fonts, com system fallback). Already
  on the system; upgrade para variable + feature-settings completos:
  - `tnum` — tabular figures (já tem).
  - `cv01` — 1 com base serif (estilo humanist).
  - `ss01` — open digits 6/9.
  - `ss02` — zero/O disambiguation.
  Defaults preservados se a variable não carregar.
- **Display sans**: `Red Hat Display` 700+, sans. Aplicada em
  portfolio header (Investido / Valor Atual / Ganho), hero numerals
  de outras superfícies, totals de tabela. Substitui o Source Serif
  4 do plano anterior — sans reads mais maximalista. Self-host é
  owner-decided (default: Google Fonts, mesmo pattern atual).
- **Numerics**: tabular figures (`font-feature-settings: "tnum"`) em
  todos os números, percentuais, e currency values. Spreadsheet look
  mantido.
- **Display + tnum convive**: Red Hat Display 700+ tem `tnum` ativo
  por padrão, então tnum em portfolio header funciona sem override
  (verificar no F09 antes de shipping — se fraco, abrir `font-
  feature-settings: "tnum"` adicional no `.portfolio-stat-value`).

### Scale

Body 16px / 1.55 line-height. Body line length capped at 65ch where
possible (the dashboard naturally stays under 60ch at 760px max-width).
Display sizes preenchem mais superfície (per SI maximal).

| Role                | Size  | Weight | Letter-spacing       | Notes                          |
|---------------------|-------|--------|----------------------|--------------------------------|
| Display (h1)        | clamp(1.75rem, 3vw, 2.5rem) | 700 | -0.02em | Red Hat Display; `text-wrap: balance` |
| Section heading (h2)| 1.1rem | 600    | -0.005em             |                                |
| Body                | 1rem  | 400    | 0                    | Inter variable                 |
| Label / caption     | 0.78rem | 500 | 0.04em uppercase     | Reserved for class labels; eyebrow labels per component inventory |
| Numeric (display)   | 1.4rem | 700   | -0.01em, tnum        | Red Hat Display; portfolio header values |
| Numeric (inline)    | 0.92rem | 500 | tnum                 | Inter; asset rows              |

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

**Material Symbols Outlined (Google Fonts), scoped.** Decisão D02
(archived 2026-07-07) — register SI maximal inclui icons nas
superfícies cobertas; stroke-based SVG ad-hoc do plano anterior fica
deprecado.

- **Font**: `Material Symbols Outlined` (Google Fonts;
  `https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined`).
  Default weight 400, optical size 24px, fill 0.
- **Tamanhos (CSS classes)**:
  - `.icon--sm` 16px — inline com body label.
  - `.icon--md` 20px — botão padrão.
  - `.icon--lg` 24px — hero / empty states.
- **Cor**: herda `currentColor`. Não pintar com `--accent` ou
  palette — icon deve ler como texto. Hover transitions seguem
  table state (cor herdada muda com o estado).
- **Catalog (D02 §Gate 1 + F12 D-F12.2)** — 10 nomes, scoped:
  - `+ Classe` — `add_circle` (em `_patrimonio_actions`).
  - `+ Ativo` — `add_circle` (em `_patrimonio_actions`).
  - `Importar` — `upload` (em `_patrimonio_actions`).
  - `Sair` — `logout` (em `base.html`).
  - Delete confirm — `close` (em `_patrimonio_class_section`).
  - Warning — `warning` (em `_rebalance_plan`).
  - Expand chevron — `expand_more` / `expand_less`
    (em `_patrimonio_class_section`).
  - Modal close — `close` (em `_patrimonio_add_asset_modal`).
  - Import status — `check_circle` (matched) / `help` (unmatched).
  - Theme toggle (se F13 um dia unblock) — `light_mode` / `dark_mode`
    ficam FORA do catalog F12 — entram se/somente se F13 for
    restaurada.
- Fora do catalog: characters textuais `×`, `−`, `▾`, `▶` continuam
  válidos para controle puramente tipográfico.
- Self-host vs Google Fonts é decisão de implementação (D-F12
  default: Google Fonts, mesmo pattern atual).
- **Extension path**: novos icons fora dos 10 nomes catalogados
  requerem nova OpenSpec change (não editar F12 in-place). A nova
  slice adiciona o nome ao catalog via delta spec em
  `openspec/specs/iconography-tokens/spec.md` + entrada aqui em
  DESIGN.md + assertion no `tests/test_iconography_tokens.py`.
  Motivação: 10 cobre a surface atual; drift silencioso sem
  guardrail de teste reintroduziria a fragilidade que o D02
  tentou eliminar.

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

**Vocabulário de estado (5-state feedback) — decisão D02.** Todos os
elementos interativos (inputs, buttons, tabs, table rows) declaram 5
estados. Cada estado tem um par fg/bg documentado e uma affordance
explícita. F10 materializa; até lá, F05 já entrega idle + hover +
disabled implícitos; foco e erro parciais.

| State    | fg                | bg            | Affordance                                              |
|----------|-------------------|---------------|---------------------------------------------------------|
| `idle`   | `--ink`           | `--surface`   | repouso                                                 |
| `hover`  | `--ink`           | `--surface` lifted via `--bg-hover`            | bg lift +1 L step                       |
| `focus`  | `--ink`           | `--surface`   | `outline: 2px solid var(--color-focus); outline-offset: 2px` |
| `disabled` | `--ink-muted`   | `--surface`   | `cursor: not-allowed`; opacity 0.6                       |
| `error`  | `--error-fg`      | `--error-bg`  | inline message below input                              |

**Table pattern upgrade — decisão D02.**

- **Sticky headers**: `<thead>` com `position: sticky; top: 0;
  background: var(--surface-sunk); z-index: 1` — scrolla junto
  com a página, header sempre visível.
- **Hover row bg lift**: `tr:hover td { background: var(--bg-hover)
  }` — feedback tátil sem hover transition agressivo.
- **Total row emphasis**: `<tr class="table-total">` ganha
  `font-weight: 600; border-top: 2px solid var(--border-strong)`.
- **Action column só-on-hover**: `<td class="row-actions">` opacity
  0 idle, `1` no `tr:hover` — sem poluir a tabela quando não está
  em uso.
- **Numerics**: `font-variant-numeric: tabular-nums` global em
  `<td>`; right-align em colunas de moeda/percentual.

**Extras — decisão D02.**

- **Section dividers**: `<hr class="section-divider">` —
  `border-top: 1px solid var(--border)`; margin `24px 0`;
  usado entre blocos em `Patrimônio` (portfolio header / classes
  summary / distribution).
- **`::selection`**: `::selection { background: var(--accent);
  color: var(--accent-ink) }` — copy-paste legitima.
- **Form autofill override**: `:-webkit-autofill { -webkit-text-
  fill-color: var(--ink); box-shadow: 0 0 0 1000px var(--surface)
  inset }` — Chromium/WebKit fill sólido.
- **Eyebrow labels**: `<div class="label-xs">` — uppercase, 0.04em
  tracking, cor `--ink-muted`. Reservado para section labels
  acima de totals/stats.
- **Compare bar pattern**: target vs atual vs over-target — 3 fills
  stacked. Target `--border-strong` (gray), atual `--accent`
  (verde-feto), over-target `accent + mix(--positive)` (verde
  emphasized). Larguras respeitam `current <= target` sem overflow.
- **Rebalance warnings border-left**: `.warning-line { border-left:
  4px solid var(--negative); padding-left: 12px }` — único local
  onde border-left > 1px é permitido (anti-pattern de border-left
  genérico continua valendo).
- **Form R$ prefix**: `<span class="input-prefix">R$</span>` à
  esquerda de inputs numéricos em `Rebalance form` (aporte) e
  campos de moeda similares. CSS only (não input decoration nativo
  por causa de browser quirks).

| Component           | Where                  | Tokens (fg / bg)                                    | Notes                                  |
|---------------------|------------------------|-----------------------------------------------------|----------------------------------------|
| App header          | `base.html`            | `--ink` on `--surface`; tab ink `--ink-muted`; tab hover / active `--ink`; tab active underline `--accent` | Logo on the left, top tab nav center, profile chip + signout on the right. Flat. Tabs ganham 5-state feedback (F10). |
| Profile picker      | `profile-switcher` select (`base.html`) | `--ink` on `--surface`; hover border `--accent`     | Native `<select>` chip in the header. Wraps every profile in the DB. Sentinel Família (F07) dentro de `<optgroup>`. |
| Tab nav             | `base.html`            | inactive tab `--ink-muted` on `--surface`; active tab `--ink` on `--surface` with `--accent` 2px underline | 4 tabs (Patrimônio / Rebalanceamento / Rentabilidade / Proventos). Active state via server-rendered `tab-nav__btn--active` modifier + `aria-current="true"`. Reuses the existing `--accent` token. Estados idle/hover/focus per F10. |
| Login               | `login.html`           | `--ink` on `--surface`; error `--error-fg` on `--error-bg` | Single field, single button, error inline. 5-state input feedback (F10). |
| Portfolio header    | `patrimonio.html`      | `--ink` on `--surface-elevated`; gain `--positive` / `--negative` | F14: elevated surface (--surface-elevated). Invested / current / gain. Red Hat Display 700+ via `.portfolio-stat-value` (F09). tnum ativo. |
| Patrimonio actions  | `patrimonio.html`      | `--ink` on `--surface`; primary hover `--accent`    | Right-aligned top-of-body button row carrying the legacy sidebar triggers (``Importar CSV`` / ``+ Novo ativo`` / ``+ Nova classe``). Testids preserved verbatim. Icons Material Symbols per catalog (F12). |
| Class section       | `patrimonio.html`      | `--ink` on `--surface`; header tinted bg (`color-mix 30% class-color`); `border-bottom: 2px solid var(--class-N)`; name `color: var(--class-N)` | F14: tinted header bg + class-colored border-bottom. No swatch square. Sticky `thead` em tabela de assets (F10). |
| Compare bar         | `patrimonio.html`      | target `--border-strong`; current `--accent`; over-target accent + `--positive` | Três fills stacked (D02 §Gate 1). Animation 0→400ms on load. |
| Asset row           | `patrimonio.html`      | `--ink` on `--surface-sunk`; numeric cells `color: var(--ink)` at `font-weight: 600+`; hover `--bg-hover` | F14: sunk table bg, compact rows (0.28rem vertical), high-contrast numbers. `tr:hover` bg lift per F10. |
| Class table         | `classes.html`         | `--ink` on `--surface`; total row `font-weight: 600 + border-top: 2px var(--border-strong)` | Editable rows, percent total at bottom. Sticky `thead` + hover rows per F10. |
| Asset editor        | `assets.html`          | `--ink` on `--surface`; remove hover `--error-fg` on `--error-bg` | Per-class sections, inline add/remove. Action column só-on-hover (F10). |
| Class delete confirm | `patrimonio.html`     | `--negative-ink` on `--negative`                    | Inline confirm; cancel `--ink` on `--surface`. Icon `close` (F12). |
| Asset delete confirm | `patrimonio.html`     | `--negative-ink` on `--negative`                    | Inline confirm; cancel `--ink` on `--surface`. Icon `close` (F12). |
| Rebalance form      | `rebalance.html`       | `--ink` on `--surface`; submit `--accent-ink` on `--accent`; inline error `--error-fg` on `--error-bg` | In-body form (F02 D9 — no sidebar slot). Input + submit on a single row. R$ prefix em aporte (D02 §Gate 1). |
| Rebalance plan      | `_rebalance_plan.html` | `--ink` on `--surface`; per-metric typography `--muted`; warning `border-left: 4px var(--negative) + padding-left: 12px` | Card grid + sortable asset table + category summary + warnings list (F02 D5: no chip — `<code>` + body). Warnings com border-left 4px (único allow per D02). |
| Stub page           | `rentabilidade.html` / `proventos.html` | `--ink` on `--surface`; secondary `--muted`; border `--border-strong` dashed | F02 stub card. Single heading + one body line. F03 / F04 substituem (defer). |
| Import form         | `import.html`          | `--ink` on `--surface`; submit `--accent-ink` on `--accent` | File picker, single submit. Autofill override per F10. |
| Review table        | `import_review.html`   | `--ink` on `--surface`; matched summary `--positive-ink` on `--positive` (tinted via color-mix) | Auto-matched summary + unmatched select. Icons `check_circle` (matched) / `help` (unmatched) per F12. Sticky `thead` per F10. |
| Import error        | `import.html`          | `--error-fg` on `--error-bg`                        | Inline error block (reuses `.error`).  |
| Empty state         | various                | `--ink` on `--surface`; secondary `--muted`         | Single line, a link if actionable.     |
| Error message       | various                | `--error-fg` on `--error-bg`                        | Inline, top of form. No toast.         |
| Section divider     | various (`<hr>`)       | `border-top: 1px solid var(--border)`               | Entre blocos de Patrimônio (F10).       |
| Eyebrow label       | various (`.label-xs`)  | `--ink-muted`                                       | Uppercase 0.04em tracking. Section labels acima de totals. |

> **Vocabulário 5-state + table pattern + extras** (F10 — materializa
> o contrato memorializado por D02 §Components; spec canônica em
> [`openspec/specs/component-state-language/spec.md`](openspec/specs/component-state-language/spec.md)).
> Cobre: 5 estados de feedback (idle/hover/focus/disabled/error) para
> inputs/buttons/tabs/rows, sticky `<thead>` em tabelas top-level,
> hover row bg lift, total row emphasis (`font-weight: 600` +
> `border-top: 2px var(--border-strong)`), action column
> `.row-actions` com `opacity: 0` idle → `1` em `tr:hover`
> (sempre visível em `@media (max-width: 768px)`),
> `::selection { background: var(--accent); color: var(--accent-ink) }`,
> autofill override em `:-webkit-autofill`,
> `.label-xs` para section labels acima de totals,
> `.input-prefix-wrap` + `.input-prefix` para inputs de moeda (R$
> no aporte), `prefers-reduced-motion: reduce` global override,
> `.warning-line` (`border-left: 4px var(--negative) +
> padding-left: 12px` — única exceção ao anti-pattern de
> `border-left > 1px`).

## Anti-patterns (this project, named)

When the polish pass encounters one of these, the right move is to
rewrite the element, not patch it:

- `border-left` or `border-right` > 1px on any list item, card, or
  callout. **Única exceção**: warnings de rebalance carregam
  `border-left: 4px solid var(--negative)` (D02 §Gate 1) — sinal
  deve ser visualmente proeminente, e a alternativa (side-stripe
  alert cheia) é pior. Fora de `.warning-line`, a regra se mantém.
- Gradient text via `background-clip: text`. None currently; preserve.
- Ghost cards (`1px border + drop-shadow ≥ 16px blur`). The current
  shadow is `0 1px 3px` which is below the threshold; the polish
  pass removes shadows from cards entirely and uses the border alone.
- Side-stripe alerts. The error and empty-state elements use full-
  width backgrounds, not left stripes.
- Eyebrow labels (small uppercase tracked text above every section).
  The dashboard h2 is the only section heading; no eyebrow acima de
  todo heading. Eyebrow labels são reservados para section labels
  acima de totals/stats (ex: "TOTAL DA CLASSE" em `class section`
  total row) — uso cirúrgico, não ubiquitous.
- **Reintroduzir sidebar.** Decisão D02 (archived 2026-07-07):
  top nav com 4 tabs de F02 é permanente; nenhuma fatia pode
  reintroduzir chrome lateral. F11 (sidebar reintroduce) está
  Blocked no roadmap com nota formal.
- **Adicionar light/dark toggle.** Decisão D02: dark-only é o
  default deliberado (F05 D-F05.10). F13 (light/dark toggle) está
  Blocked; só promove a Ready se owner pedir ativamente.
- **Estado implícito silencioso.** Todo elemento interativo
  precisa de feedback explícito nos 5 estados (idle/hover/focus/
  disabled/error). Botão sem hover bg é silent-failure — reescrever
  com `.btn:hover { background: var(--bg-hover) }` antes de mover.
- **Action column sempre visível.** Coluna de ação em tabela só
  renderiza em `:hover` da linha — tabelas sem poluição visual
  default. Idem buttons destroy/confirm: `close` icon só após
  hover. Padrão F10: `<td class="row-actions">` com
  `opacity: 0` idle → `1` em `tr:hover` (mobile `@media
  (max-width: 768px)` sempre visível).

## Visual Regression

Run `task test-visual` when a change intentionally or accidentally touches
browser-visible UI: templates, `src/omaha/static/app.css`, icon/font loading,
or page-level interaction state. The task runs Playwright screenshots in
`tests/visual/` only; `task test-e2e` remains behavior-focused and does not
collect visual baselines.

Canonical baseline PNGs live in `tests/visual/baselines/` and are committed.
Generated review artifacts live in `tests/visual/results/` and are ignored by
git. Snapshot names encode page/state and viewport (`*-desktop.png`,
`*-mobile.png`) for the `1440x900` and `375x667` matrix.

Every screenshot test asserts structural content first: route markers,
seeded class/table rows, BRL text, modal review tables, or stub markers. This
prevents login redirects, empty DB state, or blank pages from becoming valid
baselines. The comparison threshold is `0.5%` pixel difference in
`tests/visual/conftest.py`.

Intentional visual changes update affected baselines in the same change:

1. Run `UPDATE_VISUAL_BASELINES=1 task test-visual` to rewrite PNGs.
2. Review changed files under `tests/visual/baselines/`.
3. Run `task test-visual` again without the env var to prove committed
   baselines pass.

## Migration path

D02 (2026-07-07) resolved the design register. F08/F09/F10/F12
materialized the register in CSS. F14 (Catppuccin Frappe swap) is
the current dark palette baseline. All historical migrations are
archived in `openspec/changes/archive/`.

### Token change workflow

1. Update value in `app.css :root`.
2. Run `uv run pytest tests/test_dark_mode_tokens.py -x`.
3. Update the "Tokens (current)" table above.
4. Update component inventory if a component's token consumption changed.
