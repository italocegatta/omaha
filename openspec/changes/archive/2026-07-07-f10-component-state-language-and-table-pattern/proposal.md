## Why

Front-end interativo da omaha já tem tokens de cor unificados (F05/F08),
mas falta vocabulário explícito de **feedback de estado** e padrão
consistente de **tabela**. Resultado: cada template reinventa hover/focus/
disabled/error à sua maneira, ações em tabela ficam visíveis o tempo todo
poluindo a leitura, e headers de tabela somem no scroll. D02 memorializou
o vocabulário 5-state + table pattern upgrade como parte do register SI
maximal (gate §Gate 1) — este slice materializa.

## What Changes

- Implementar vocabulário 5-state (idle/hover/focus/disabled/error) em
  inputs, buttons, tabs e table rows, conforme tabela documentada em
  DESIGN.md §Components.
- Aplicar table pattern upgrade: `<thead>` sticky, hover row bg lift,
  total row emphasis (`font-weight: 600 + border-top 2px`), action
  column só-on-hover (`opacity: 0` idle → `1` em `tr:hover`), numerics
  tabular + right-align em colunas moeda/percentual.
- Adicionar extras D02: section dividers hairline, `::selection` em
  `--accent`, form autofill override (Chromium/WebKit), eyebrow labels
  `.label-xs`, form R$ prefix em aporte do `/rebalanceamento`.
- Cobrir 10 templates: `base.html`, `login.html`, `patrimonio.html` +
  4 partials (`_patrimonio_actions`, `_patrimonio_portfolio_header`,
  `_patrimonio_class_section`, `_patrimonio_distribution`),
  `classes.html`, `assets.html`, `rebalance.html` + 2 partials
  (`_rebalance_plan`, `_rebalance_placeholder`), `import.html`,
  `import_review.html`. Stubs F02 (`rentabilidade.html` /
  `proventos.html`) ficam para F03/F04 quando reativados.
- Atualizar `DESIGN.md` §Component inventory para apontar a tabela
  5-state como fonte de verdade + §Anti-patterns reforçando "action
  column sempre visível" como forbidden.
- Sem mudança de comportamento observável do ponto de vista de dados:
  todas as modificações são CSS + copy em `aria-*`/`title` quando
  faltar. Nenhum endpoint tocado. Nenhum teste runtime regredirá.

## Capabilities

### New Capabilities

- `component-state-language`: vocabulário de feedback 5-state
  (idle/hover/focus/disabled/error) para inputs/buttons/tabs/rows +
  table pattern (sticky thead, hover row lift, total row emphasis,
  action column só-on-hover, numerics tabular/right-align) + extras
  D02 (section dividers hairline, `::selection`, form autofill
  override, eyebrow labels, form R$ prefix). Internal layout spec —
  descreve o contrato visual que F08/F09/F10 entregam juntos, capturado
  em DESIGN.md §Components.

### Modified Capabilities

Nenhuma. F10 não mexe em requisitos de specs existentes — apenas
implementa o contrato D02 já memorializado em
`design-register-decision`. Specs runtime (`cross-profile-sharing`,
`patrimonio-portfolio-header`, `rebalance-page`, `header-profile-
switcher`, `quote-provider`, etc.) seguem com os mesmos requisitos;
F10 só adiciona apresentação visual consistente em superfícies que
elas já descrevem.

## Impact

- `src/omaha/static/app.css` (estilos 5-state + table pattern +
  extras) — única superfície técnica.
- `src/omaha/templates/base.html`, `login.html`, `patrimonio.html` +
  4 partials, `classes.html`, `assets.html`, `rebalance.html` +
  2 partials, `import.html`, `import_review.html` (apenas classes
  `aria-*`/`title` se faltar affordance textual — mínimo).
- `DESIGN.md` §Component inventory (cross-link para a nova spec) +
  §Anti-patterns (reforçar "action column sempre visível" forbidden).
- Sem dependência nova. Sem migration. Sem mudança de rota. Sem
  mudança de seed. Cap 1 Applying (domínio visual). Pode coexistir
  com F09 (typography refresh) em Applying — ambos mexem em CSS mas
  em camadas diferentes (tokens vs. classes de feedback).
