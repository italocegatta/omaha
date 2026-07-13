## Context

`/patrimonio` já tem tabela de ativos sortable e inline-editable, mas o chrome ainda é diferente de `/rebalanceamento`: header/body não têm a mesma leitura de shell, não há filtro por coluna, e a ordenação não está espelhada no mesmo padrão de interação do rebalance. A mudança é só de UI/Alpine/CSS; não toca rota, banco, seed, nem cálculo.

## Goals / Non-Goals

**Goals:**
- Espelhar UX da tabela de rebalance na tabela de ativos de patrimônio.
- Adicionar filtro por coluna no header, local à classe atual, exceto em `Preço médio` e `Qtd`.
- Manter ordenação determinística e consistente com rebalance.
- Preservar inline edit, delete, add-asset, trade toggles e `data-testid` existentes.

**Non-Goals:**
- Formatação numérica nova.
- Toggle de emoji para compra/venda.
- Mudança de dados, API, rota, seed ou solver.

## Decisions

1. **Reusar `classSection()` como único estado da tabela.**
   - Mantém sort, filtro, inline edit e delete no mesmo escopo Alpine.
   - Evita prop drilling ou componente filho só para filtros.
   - Alternativa rejeitada: novo componente por tabela. Custo maior, mais chance de drift com inline edit.

2. **Copiar padrão de interação do rebalance para headers filtráveis.**
    - Column model com `sortKey`, `filterKind`, `openFilter`, `headerFilters` e `headerRangeFilters`; `Preço médio` e `Qtd` expõem somente `sortKey`.
   - Categorical columns usam multi-select; numéricas usam range.
   - Alternativa rejeitada: busca textual genérica. Não espelha rebalance e não resolve leitura rápida por coluna.

3. **Filtro 100% client-side.**
   - Sem query params, sem novo endpoint, sem round-trip.
   - Mantém tabela isolada por classe e preserva contrato atual de página.
   - Alternativa rejeitada: filtro server-side. Tocaria rota/contexto e ampliaria slice.

4. **Ordenação com tie-break determinístico.**
   - Clique em header alterna asc/desc.
   - Empates quebram por nome do ativo, depois id estável.
   - Garante que `sortBy()` não “embaralhe” linha igual quando filtro muda.

5. **CSS segue shell do rebalance.**
   - Reaproveitar classes e tokens de shell/header/body já existentes no stylesheet.
   - Se precisar de alias em patrimônio, alias curto sobre mesmo token; sem segunda linguagem visual.
   - Alternativa rejeitada: copiar bloco novo inteiro. Mais drift, mais manutenção.

## Risks / Trade-offs

- [Header chrome alonga tabela] → manter `table-layout: fixed`, shell com overflow horizontal e widths atuais.
- [Filtros competem com clicks de sort/edit] → isolar clique com `@click.stop` nos botões/painéis e manter state por classe.
- [Visual parity quebra alinhamento com header stats] → não mexer em numeric format/sizing; revalidar com screenshot/collapse checks.
- [Muita UI no header] → usar painel compacto e padrão único de botões para não duplicar affordance.

## Migration Plan

1. Atualizar partial de patrimônio com metadata de colunas, sort/filter state e header controls.
2. Ajustar CSS para shell/header/body parity com rebalance.
3. Atualizar testes de browser/screenshot para sort + filter + visual shell.
4. Se precisar reverter, voltar template/CSS; não há migração de dados ou rollback de DB.

## Open Questions

- None.
