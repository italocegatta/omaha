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
mantido). Body warmth mantido (hue 60 warm-neutral, chroma ≈ 0.012)
— calor migra para accent/coral/amber/magenta, não para o body
cinza.

Product — family portfolio app. Design serves the function. The dashboard
is the most important surface; the editors and import flow are functional
back-of-house.

## Color strategy

**Inverted to dark warm-neutral. Target register: Status Invest
maximal (D02).**

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

### Target register (D02) — to materialize in F08

D02 elegeu **Status Invest maximal** como register a perseguir. F08 é
a fatia que materializa em CSS os tokens correspondentes. Até o
archive de F08, este doc mantém a tabela "Tokens (current — post F05)"
como verdade operativa; valores finais chegam com F08 landa.

Diretrizes (targets, não prescritivas — F08 deriva números exatos):

- **Accent**: emerald `oklch(0.68 0.20 152)` — punch + chroma up vs
  current `0.68 0.13 150`. Separa "marca" de "ganho".
- **Positive**: fern-leaning `oklch(0.79 0.19 145)` — mais chroma
  (signal legível em body escuro) vs current `0.70 0.16 145`.
- **Negative**: coral `oklch(0.69 0.20 25)` — chroma up vs current
  `0.70 0.18 25`; mantemos hue 25 (coral).
- **Class-3 hue destino: 350 magenta-red.** Separa classe 3 de
  `--negative` por hue gap de 325° (categoria de ativo ≠ sinal de
  perda). Drift atual: class-3 está em hue 25 (mesmo de negative).
- **Warning**: amber `oklch(0.78 0.16 75)` — substitui
  `oklch(0.70 0.12 85)`. Hue shift leve + chroma up.
- **Surface**: warm-neutral dark, hue 60, chroma ~0.012 mantido.
- **Bugs a resolver em F08** (4 itens da sessão 2026-07-06):
  1. colisão `--class-3` vs `--negative` (ambos hue 25 chroma 0.18).
  2. `--positive` sem punch (L 0.70 → 0.74-0.78 para "data signal"
     legível em body escuro).
  3. `_CLASS_COLORS` Python hex drift vs CSS OKLCH
     (swatch usa inline hex, CSS tem token OKLCH paralelo).
  4. `--accent` vs `--positive` ambiguidade cromática (hue gap 5°
     + chroma invertido — verde de marca vs verde de ganho
     indistinguíveis).
- Adiciona `--bg-secondary` se 3-tier surface (D02 ficou em aberto —
  default é manter 2-tier; F08 decide com base em render).
- Tokens de classe re-derivados em OKLCH (mata o hex drift).

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
| Portfolio header    | `patrimonio.html`      | `--ink` on `--surface`; gain `--positive` / `--negative` | Invested / current / gain. The hero. Wrapped by `data-testid="patrimonio-portfolio-header"` (F02 D3). Red Hat Display 700+ via `.portfolio-stat-value` (F09). tnum ativo. |
| Patrimonio actions  | `patrimonio.html`      | `--ink` on `--surface`; primary hover `--accent`    | Right-aligned top-of-body button row carrying the legacy sidebar triggers (``Importar CSV`` / ``+ Novo ativo`` / ``+ Nova classe``). Testids preserved verbatim. Icons Material Symbols per catalog (F12). |
| Class section       | `patrimonio.html`      | `--ink` on `--surface`; swatch `--class-{1..6}`     | Swatch + name + compare bar + asset list. Sticky `thead` em tabela de assets (F10). |
| Compare bar         | `patrimonio.html`      | target `--border-strong`; current `--accent`; over-target accent + `--positive` | Três fills stacked (D02 §Gate 1). Animation 0→400ms on load. |
| Asset row           | `patrimonio.html`      | `--ink` on `--surface`; pct `--muted`; progress `--accent`; hover `--bg-hover` | Name + value + pct + progress bar. `tr:hover` bg lift per F10. |
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

## Migration path

### D02 (design register decision) — gate resolvido 2026-07-07

Decisão de register não toca código — materializa-se nas fatias da
frente visual:

- **F08** (palette overhaul v2) — re-deriva tokens per SI maximal
  (4 bugs concretos: colisão `--class-3` vs `--negative`,
  `--positive` sem punch, `_CLASS_COLORS` hex drift, ambiguidade
  `--accent` vs `--positive`). Toca em `app.css :root` +
  `routes/pages.py::_CLASS_COLORS` +
  `tests/test_dark_mode_tokens.py` + `color-tokens` spec delta.
- **F09** (typography refresh) — Red Hat Display 700+ portfolio
  header + Inter variable `tnum, cv01, ss01, ss02`. Toca em
  `base.html` Google Fonts URL + `app.css` font-family chain +
  `DESIGN.md` §Typography já reescrita.
- **F10** (component state language + table pattern) — 5-state
  feedback (idle/hover/focus/disabled/error) + sticky `<thead>` +
  hover row bg lift + total row emphasis + action column
  só-on-hover + section dividers + `::selection` + autofill
  override + eyebrow labels. 10 templates × 8 elementos × 5
  estados = ~40 micro-decisões. Pode rodar em paralelo com F08/F09
  (cap 2 Applying).
- **F12** (Material Symbols icons) — catalog definido em D02
  §Iconography acima. Toca em `base.html` Google Fonts URL +
  `app.css` `.icon--sm/md/lg` + 5 templates parciais.
- **F11 / F13** — Blocked por decisão D02 (sidebar reintroduce
  bloqueada; light/dark toggle bloqueada). Permanecem no roadmap
  como histórico com nota formal.

Todas as 4 fatias materializam invariantes documentadas aqui
(maior fatia em volume = F10). Tokens finais chegam com F08
archive — tabela "Tokens (current — post F05)" desta doc
permanece como verdade operativa até lá.

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
