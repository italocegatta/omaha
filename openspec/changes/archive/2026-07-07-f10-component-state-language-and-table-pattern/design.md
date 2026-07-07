## Context

D02 archived 2026-07-07 memorializou o register visual **Status Invest
maximal, sidebar NÃO** em PRD §4.10 + DESIGN.md §Register + §Color
strategy + §Components. Como parte do gate §Gate 1 ("maximal inclui
..."), D02 §Iconography + §Components catalogou:

1. **Vocabulário 5-state** (idle/hover/focus/disabled/error) com pares
   fg/bg documentados para inputs, buttons, tabs e table rows.
2. **Table pattern upgrade**: sticky `<thead>`, hover row bg lift, total
   row emphasis, action column só-on-hover, numerics tabular.
3. **Extras**: section dividers hairline, `::selection`, form autofill
   override, eyebrow labels, compare bar pattern, rebalance warnings
   border-left 4px, form R$ prefix.

Hoje (pré-F10) o front tem tokens de cor (F05 + futuras adições F08)
mas falta consistência em feedback de estado: cada template reinventa
hover/focus à sua maneira; ações em tabela ficam visíveis o tempo
todo, poluindo a leitura; headers de tabela somem no scroll; tabs não
têm affordance clara de "active".

F09 já aplicou Red Hat Display 700+ em 5 seletores + Inter feature-
settings completos. F08 foi archived como **proposal-only** (sem
implementação) — slice preserva o delta mas a paleta atual segue
tokens F05. F10 não depende do apply de F08: implementa com tokens
existentes (post-F05).

F11 + F13 promoted a Blocked (D02 §Gate 4 sidebar NÃO, §Gate 5 light/dark
toggle NÃO). F10 + F12 são as duas fatias de polish visual que sobraram
do front logado em PRD §5.3.

## Goals / Non-Goals

**Goals:**

- Implementar 5-state vocabulary (idle/hover/focus/disabled/error) em
  **todos** os elementos interativos: inputs (`login.html`, `import.html`,
  `rebalance.html`, modais em `_patrimonio_add_asset_modal.html`),
  buttons (CTA em `patrimonio_actions`, submit em forms), tabs
  (`.tab-nav__btn` em `base.html`), table rows (`.class-table` em
  `classes.html`, `.asset-table` em `_patrimonio_class_section`).
- Aplicar table pattern upgrade nos 3 lugares com tabela:
  `classes.html` (tabela de classes), `_patrimonio_class_section.html`
  (asset list), `assets.html` (asset editor rows) — sticky `<thead>`,
  hover row bg lift, total row emphasis, action column só-on-hover,
  numerics tabular + right-align.
- Adicionar extras D02: section dividers hairline (entre portfolio
  header / classes summary / distribution em `patrimonio.html` +
  partials), `::selection` global em `--accent`, form autofill override
  em Chromium/WebKit, eyebrow labels `.label-xs` em section labels,
  form R$ prefix em aporte (`rebalance.html`).
- Atualizar `DESIGN.md` §Component inventory para cross-link a nova
  spec `component-state-language`; §Anti-patterns reforçando "action
  column sempre visível" como forbidden.

**Non-Goals:**

- Não tocar em paleta/tokens (escopo F08, archived proposal-only).
  F10 reusa os tokens F05 existentes — se F08 for reativado no futuro,
  contraste continua valendo (pares fg/bg mantêm hue + lightness family).
- Não introduzir light/dark toggle (F13 Blocked, D02 §Gate 5).
- Não reintroduzir sidebar (F11 Blocked, D02 §Gate 4).
- Não trocar fonts (F09 archived + applied).
- Não adicionar icons (F12 separado — mantém o catálogo D02).
- Não tocar em `src/omaha/rebalance/` / solver CVXPY / cotação
  yfinance / seed CSV / auth (todos fora do escopo visual).

## Decisions

- **D-F10.1 — 5-state via CSS puro, sem JS.** Focus visible via
  `:focus-visible` (não `:focus`) — mouse click não dispara ring,
  teclado sim. Mantém acessibilidade sem JS handler. Disabled via
  `aria-disabled="true"` + classe `.is-disabled` (sem `<button disabled>`
  para permitir tooltips explicativos). Error via classe `.is-error`
  + texto inline `.input-error-message` abaixo do input.

  **Alternativas**: JS handler para focus/blur events — descartado
  porque `:focus-visible` é nativo, testável via Playwright
  `page.keyboard.press('Tab')`, e não adiciona JS state.

- **D-F10.2 — Sticky `<thead>` com `position: sticky; top: 0;
  background: var(--surface-sunk); z-index: 1`.** Funciona em scroll
  vertical da página sem JS observer. `surface-sunk` (não `surface`)
  para contraste contra `surface` das rows — header sempre lê como
  "elevação diferente das rows".

  **Risco**: tabelas dentro de modais com scroll próprio podem ter
  `top: 0` conflito. Mitigação: aplicar `.table-sticky-header` apenas
  em tabelas fora de modal (`.class-table`, `.asset-table`).

- **D-F10.3 — Hover row bg lift via `tr:hover td { background: var
  (--bg-hover) }`.** Sem transition agressivo (`transition: background
  80ms ease`). Afeta toda row, não só cell com hover — feedback
  coerente ao mouse atravessar a row.

  **Alternativa**: hover por cell individual (`td:hover { ... }`) —
  descartado porque gera "stripe effect" quando mouse atravessa
  colunas; inconsistente com row-hover de Material Design / SI.

- **D-F10.4 — Action column só-on-hover via `.row-actions { opacity: 0;
  transition: opacity 80ms ease } .tr:hover .row-actions { opacity: 1
  }`.** Mantém tabela limpa quando idle; revela delete/edit no hover
  (padrão Material Tables / SI position edit).

  **Atenção**: `prefers-reduced-motion: reduce` zera o transition
  (inline override por D-F10.8).

- **D-F10.5 — Total row emphasis via `<tr class="table-total">` com
  `font-weight: 600; border-top: 2px solid var(--border-strong)`.**
  Border 2px (não 1px) garante separação clara entre rows individuais
  e total. `border-strong` (não `border`) para contraste WCAG AA em
  dark surface.

  **Aplicação**: classes.html (total % row no fim), `_patrimonio_class_
  section.html` (subtotal per class no fim de cada section).

- **D-F10.6 — Numerics tabular via `font-variant-numeric: tabular-nums`
  global em `<td>` + right-align via `td.is-numeric { text-align:
  right }`.** Sem JavaScript. Colunas com `class="col-pct"` ou
  `class="col-money"` ganham `.is-numeric` automaticamente. Header
  numérico também segue `text-align: right` via `<th class="col-...">`.

- **D-F10.7 — Section dividers via `<hr class="section-divider">` com
  `border-top: 1px solid var(--border); margin: 24px 0; background:
  transparent`.** Não usa `<hr>` default (border-bottom + double border
  feio). Aplicar entre portfolio header / classes summary / distribution
  em `patrimonio.html` + entre sections principais em `rebalance.html`.

- **D-F10.8 — `::selection { background: var(--accent); color: var
  (--accent-ink) }` global.** Cor do highlight legitima copy-paste
  com marca visual. Adicionar `prefers-reduced-motion: reduce { *,
  *::before, *::after { transition: none !important; animation: none
  !important } }` para acessibilidade de motion.

- **D-F10.9 — Form autofill override via `:-webkit-autofill,
  :-webkit-autofill:hover, :-webkit-autofill:focus { -webkit-text-fill-
  color: var(--ink); -webkit-box-shadow: 0 0 0 1000px var(--surface)
  inset; box-shadow: 0 0 0 1000px var(--surface) inset }`.** Chromium/
  WebKit pintam autofill com amarelo/blue default — override garante
  consistência visual com tokens.

- **D-F10.10 — Eyebrow labels via `<div class="label-xs">` (uppercase,
  0.04em tracking, `--ink-muted`, font-size 0.75rem).** Reservado para
  section labels acima de totals/stats (não para body text). Não
  trocar por `<small>` — semântica de "eyebrow" não existe em HTML5.

- **D-F10.11 — Form R$ prefix via `<span class="input-prefix">R$</span>`
  dentro de `<label class="input-prefix-wrap">`.** CSS only (`flex`
  row + input border-left flat). Browser quirks em `::before` com
  `content` em `<input>` são o motivo do span wrapper (D02 §Extras).
  Aplicar em aporte do `/rebalanceamento` (F02 D9 form).

- **D-F10.12 — Sem nova spec além de `component-state-language`.**
  A spec já captura o vocabulário 5-state + table pattern + extras
  num único lugar; specs runtime existentes
  (`cross-profile-sharing`, `patrimonio-portfolio-header`,
  `rebalance-page`, `header-profile-switcher`, etc.) seguem com seus
  próprios requisitos — F10 só adiciona **apresentação visual**
  consistente em superfícies que elas descrevem. Spec
  `design-register-decision` (D02) já memorializa a decisão de
  register; F10 não mexe nela.

## Risks / Trade-offs

- **Risco: regressão visual em e2e (T01 pre-existing chromium stalls
  + novos asserts visuais).** Mitigação: F10 não introduz novos e2e
  tests (o cap visual está em T06 — depende de F08+F09+F10 aplicados).
  Render diff via `task serve` + inspeção manual em
  `bash scripts/print_lan_url.sh`.

- **Risco: 5-state focus ring pode conflitar com `outline: none` em
  classes existentes (e.g. `.tab-nav__btn`).** Mitigação: pre-audit
  em `rg -n "outline.*none|outline.*0" src/omaha/static/app.css`
  antes do apply; consolidar via `:focus-visible`.

- **Risco: action column só-on-hover esconde delete/edit em mobile
  (no hover, só tap).** Mitigação: mobile breakpoint
  (`@media (max-width: 768px) { .row-actions { opacity: 1 } }`)
  mostra sempre em telas pequenas. Padrão Material Tables / SI.

- **Risco: sticky `<thead>` em tabela dentro de `<dialog>` com
  scroll próprio não funciona.** Mitigação: aplicar `.table-sticky-
  header` apenas em `.class-table` (fora de modal) e `.asset-table`
  (fora de modal). Modais de add/edit não ganham sticky — seu scroll
  é interno, sem necessidade.

- **Risco: `font-variant-numeric: tabular-nums` em Red Hat Display
  700+ pode reduzir legibilidade de números grandes.** Mitigação:
  F09 archive já validou tnum em Red Hat Display 700+ como tabular;
  sem regressão esperada. Smoke pré-apply renderiza portfolio header.

- **Risco: `section-divider` adiciona vertical space entre blocos —
  se usado em excesso pode quebrar densidade da info.** Mitigação:
  aplicar em 3 lugares: portfolio header / classes summary /
  distribution em `patrimonio.html`. Outros blocos continuam sem
  divider (espaço em branco já cumpre papel).

- **Trade-off: 5-state + table pattern + extras = ~150 LOC de CSS
  novo + ~10 templates tocados (mínimo, só `aria-*` quando
  faltar).** Estimativa 4-6h. Comparável a F09 (Red Hat Display
  nos 5 seletores — 2h).

## Migration Plan

Apply em uma única passagem:

1. `app.css` ganha ~150 LOC de regras 5-state + table pattern + extras.
2. Templates recebem apenas `aria-*`/`title` quando faltar (mínimo).
3. `DESIGN.md` §Component inventory ganha linha cross-link para
   `component-state-language`; §Anti-patterns ganha entry "action
   column sempre visível" forbidden.
4. Smoke: `task test-unit` 271 pass / 2 skip (sem regressão —
   F09 baseline); `task test-integration` 369 pass / 2 skip (sem
   regressão); `task lint` verde; `bash scripts/print_lan_url.sh`
   + inspecionar 10 páginas em viewport 1440×900 + mobile 375×667.
5. Rollback: revert do PR + `task db-reset` não é necessário (sem
   migration, sem seed change).

Sem CI block: T06 (visual regression) é slice separada, depende
de F08+F09+F10 aplicados. F10 archive não exercita T06.

## Open Questions

- Nenhum no momento. D02 resolve as decisões de register; F10 é
  pura materialização. Pontos ambíguos resolvidos in-slice:
  - mobile breakpoint para action column = 768px (D-F10);
  - sticky thead não aplica em modais (D-F10.2);
  - eyebrow labels reservados para totals/stats (D-F10.10);
  - form R$ prefix em aporte do rebalance (D-F10.11).
