# Design — F40 Bug template tabelas ativos patrimonio

## Context

A tabela de ativos em `/patrimonio` (`_patrimonio_class_section.html`) sofreu
múltiplas refatorações (R30 shared table base, F32 visual parity, F28 rounding,
F29 emoji toggle). Três bugs visuais persistem, todos com causa raiz identificada
e soluções testadas na sessão 2026-07-16.

## Goals / Non-Goals

**Goals:**
- Coluna Ativo: texto longo quebra linhas dentro da célula
- Colunas de desvio/percentual exibem conteúdo corretamente
- Painel de filtros abre ao clicar no ícone em todas as colunas

**Non-Goals:**
- Alterar layout/estrutura da tabela (colgroup, colunas)
- Mudar comportamento de filtros (apenas visibilidade do painel)
- Refatorar componentes Alpine.js além do necessário
- Alterar tabela de rebalanceamento
- Reintroduzir coluna Moeda (removida intencionalmente no commit 1c0b0fc)

## Decisions

### D1 — Word-break na coluna Ativo

**Decisão:** adicionar regra CSS específica para `.asset-table td:first-child`
com `white-space: normal` e `overflow-wrap: break-word`.

**Por que não `word-break: break-all`:** quebra palavras em pontos arbitrários,
piora legibilidade.

**Por que `td:first-child` e não todas as td:** outras colunas (Qtd, Preço,
Ganho) contêm valores numéricos curtos que não precisam de wrap. Manter
`white-space: nowrap` nelas preserva alinhamento.

### D2 — Overflow do painel de filtros

**Decisão:** trocar `overflow: hidden` por `overflow: visible` em `.asset-table th`.

**Por que não teleport:** o macro `filter_controls` já suporta `teleport=true`,
mas requer cálculo de posição absoluta no viewport via JS. Mais complexo
sem benefício para este caso.

**Por que não `overflow: clip`:** CSS novo, suporte incompleto. `visible`
resolve sem risco.

**Risco:** header text overflow? Mitigado por `white-space: nowrap` que já
previne wrap do texto do header.

### D3 — Conteúdo ausente nas colunas

**Decisão:** adicionar método `formatDeviationPp` standalone no componente
`classSection`, delegando a `window.__tableFormatters` com fallback inline.

**Causa raiz identificada:**
- Template chama `formatDeviationPp(...)` em 4 pontos
- Método NÃO existia no scope do componente Alpine
- Método existia apenas no módulo assíncrono `table-formatters.js`
- Alpine avaliava a expressão, não encontrava, retornava `undefined`
- Resultado: células vazias silenciosamente

**Por que não mover a chamada para `window.__tableFormatters`:**
seria mais invasive — mudaria o template em 4 pontos. Adicionar o método
no componente é 1 mudança pontual.

## Risks

- **[Mitigado] Remover `overflow: hidden` pode causar header overflow**
  → `white-space: nowrap` já previne. Testado OK.
- **[Mitigado] Bug 2 pode ter causa no backend**
  → Investigado: dados existem no Alpine scope. O problema era só a função.

## Incidente 2026-07-16

Apply agent sobrescreveu commit `1c0b0fc` do usuário ao tentar implementar
estes fixes. Lição documentada em PRD §4.14: fix cirúrgico = troca pontual,
nunca reescrever código funcional.

## Test strategy

- `uv run task test-unit` (434+ tests)
- `uv run task lint`
- Browser: visual inspection dos 3 bugs
- Diff review: confirmar APENAS as 3 adições (~17 linhas)
