## Context

A tabela de ativos (`_patrimonio_class_section.html`) e a tabela de rebalance (`_rebalance_plan.html`) compartilham tokens R30 (`--table-*`) e classes base (`.data-table-shell`, `.data-table-th`, `.data-table-td`), mas divergem em 5 dimensões visuais. A tabela rebalance é a referência canônica (per `shared-table-pattern` spec). R30-R34 padronizaram CSS de tabela; F29 adicionou toggles emoji; F35 corrigiu cores de toggle. F36 fecha o alinhamento visual restante.

### Estado atual (gap analysis)

| Dimensão | Rebalance (referência) | Asset table (atual) | Gap |
|---|---|---|---|
| **(a) Ícones filtro** | `<span class="material-symbols-outlined">filter_alt</span>` inline no `<th>` | `<span class="icon icon--sm">filter_alt</span>` via macro `_filter_controls.html` | Classe CSS diferente (`.material-symbols-outlined` vs `.icon`). Ambas renderizam o mesmo glifo via font Material Symbols Outlined, mas o wrapper é incompatível. |
| **(b) Teleport filtro** | Inline (sem teleport), painel `position: absolute` dentro do `<th>` | `teleport=true` via `<template x-teleport="body">` + `filterPanelStyle()` | Comportamento intencional: asset table vive dentro de `.class-section-body` com `overflow: hidden`. Teleport é necessário. Validar posicionamento correto. |
| **(c) Formatação desvio** | `formatDeviationPp` → `+X%` / `-X%` (0 decimais, sinal explícito) | `formatPct` → `X.XX%` (2 decimais, sem sinal explícito) para `class_deviation_pct` e `portfolio_deviation_pct` | Precision e sign display divergem. |
| **(d) Visual totais** | Cards de classe com `border-top: 3px` colorida + gradiente | Linha `class-totals-row` com bg `color-mix(surface-sunk 82%)` sem cor da classe | "Total da classe" não tem destaque visual comparável. |
| **(e) Espaçamento cabeçalhos** | `padding: 0.9rem 0.75rem`, `font-size: 0.85rem` | `padding: 0.72rem 0.75rem`, `font-size: 0.84rem`, `--col-ativo: 340px` | Padding menor; coluna ATIVO pode não acomodar nomes longos. |

## Goals / Non-Goals

**Goals:**
- Unificar ícones de filtro/ordenação entre as duas tabelas
- Alinhar formatação de desvio para 0 decimais com sinal explícito
- Transformar "Total da classe" em card visual com cor da classe
- Ajustar espaçamento de cabeçalhos para acomodar todos os nomes de coluna
- Manter filtros funcionais (teleport no asset table é correto e deve ser mantido)

**Non-Goals:**
- Refatorar a arquitetura de filtros (macro vs template inline)
- Alterar o `table-formatters.js` (funções já existem; mudança é no call site)
- Mudar o layout de colunas ou ordem de colunas
- Alterar o rebalance table (ele é a referência)

## Decisions

### Decision 1: Unificar classe CSS do ícone de filtro

**Escolha**: Alterar `_filter_controls.html` para usar `material-symbols-outlined` em vez de `icon icon--sm` no span do ícone de filtro.

**Rationale**: A classe `.icon` em `app.css` define `font-family: "Material Symbols Outlined"` manualmente. A classe nativa `.material-symbols-outlined` do Google Fonts faz a mesma coisa mas é o padrão oficial. O rebalance table já usa o padrão nativo. Unificar elimina CSS duplicado e alinha com a documentação do Google Fonts.

**Alternativa considerada**: Manter `.icon icon--sm` e adicionar CSS para torná-lo visualmente idêntico. Rejeitado: mantém CSS desnecessário e não resolve a raiz.

### Decision 2: Manter teleport=true no asset table

**Escolha**: Nenhuma mudança no posicionamento. O `teleport=true` é correto para o contexto do asset table (f filtros dentro de `overflow: hidden`).

**Rationale**: O rebalance table não tem `overflow: hidden` nos pais, então inline funciona. O asset table vive dentro de `.class-section-body` que colapsa. Teleport é a solução correta. Validar apenas que `filterPanelStyle()` posiciona corretamente em todos os viewports.

### Decision 3: Formatação de desvio — usar formatDeviationPp

**Escolha**: Nos templates do asset table, trocar `formatPct(a.class_deviation_pct)` e `formatPctRounded(a.portfolio_deviation_pct)` por `formatDeviationPp()` para as colunas de desvio.

**Rationale**: `formatDeviationPp` já existe em `table-formatters.js` e é usado pelo rebalance table. Produz `+X%` / `-X%` com 0 decimais e sinal explícito — mais legível para desvios. `formatPct` com 2 decimais é excessivo para desvio percentual.

**Impact**: Mudança no call site do template (2 linhas), não no formatter.

### Decision 4: "Total da classe" como card com cor da classe

**Escolha**: Transformar a `class-totals-row` em um card visual com:
- `border-left: 3px solid` usando a cor da classe (via CSS variable `--class-color` já existente)
- Background com `color-mix(in srgb, var(--class-color) 8%, var(--surface))`
- Label "TOTAL DA CLASSE" em bold com a cor da classe
- Padding levemente maior para efeito de card

**Cor proposta**: usar a cor da classe já disponível via `--class-N` tokens (mesma paleta do header). O owner validará a cor antes da implementação.

**Alternativa considerada**: usar `border-top` como os cards de classe do rebalance. Rejeitado: a linha de totais é uma `<tr>`, não um card independente; `border-left` é mais adequado para uma linha de tabela.

### Decision 5: Espaçamento de cabeçalhos

**Escolha**: Aumentar `--col-ativo` de `340px` para `360px` e padding de `th` de `0.72rem` para `0.82rem` para alinhar com o rebalance table.

**Rationale**: O padding menor no asset table (`0.72rem`) vs rebalance (`0.9rem`) causa inconsistência visual. Aumentar para `0.82rem` é um meio-termo que melhora o espaçamento sem exceder o rebalance. Ajustar `--col-ativo` garante que nomes longos cabeçam.

## Risks / Trade-offs

- **[Risco] Testes e2e quebram por mudança de classe CSS do ícone** → Mitigação: `data-testid` nos botões de filtro não muda; apenas a classe CSS do span interno. Testes que selecionam por `.icon` dentro do filtro precisarão de ajuste.
- **[Risco] formatDeviationPp muda comportamento visual** → Mitigação: mudança é de 2 decimais para 0 decimais com sinal explícito. Validação visual em resize + filter popup + ordenação.
- **[Risco] Cor do card "Total da classe" precisa validação do owner** → Mitigação: proposta de cor será apresentada ao owner antes de implementar. Task de implementação fica bloqueada até validação.
- **[Trade-off] Aumento de --col-ativo reduz espaço para outras colunas** → Mitigação: tabela tem `overflow-x: auto` no shell; colunas extras rolam horizontalmente em telas pequenas.

## Migration Plan

1. Implementar mudanças CSS/HTML em ordem: (a) ícones → (c) formatação → (e) espaçamento → (d) totais
2. (b) teleport: apenas validação, sem mudança de código
3. Testar em viewport desktop (1440px+) e mobile (480px)
4. Verificar filtros (enum + range), ordenação, formatação numérica
5. Rollback: cada dimensão é independente; reverter uma não afeta as outras

## Open Questions

- **Cor do card "Total da classe"**: proposta usa cor da classe via `--class-N` tokens. Owner precisa validar se a opacidade do background (8%) e o border-left (3px) estão adequados.
- **Resize behavior**: após aumento de `--col-ativo`, verificar se a tabela cabe em 1440px sem scroll horizontal.
