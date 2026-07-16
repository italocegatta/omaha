## Why

A tabela de ativos (`_patrimonio_class_section.html`) e a tabela de rebalanceamento (`_rebalance_plan.html`) divergem em 5 dimensões visuais apesar de compartilharem os tokens R30. O operador percebe inconsistência ao alternar entre as duas telas: ícones de filtro diferentes, formatação numérica discrepante (desvio com 2 decimais vs 0), cabeçalho "Total da classe" sem destaque visual, e espaçamento de colunas que não acomoda todos os nomes. F36 alinha as duas tabelas para que a experiência visual seja coerente.

## What Changes

- **Ícones de filtro/ordenação**: unificar o componente de ícone Material Symbols no asset table para usar o mesmo padrão `material-symbols-outlined` do rebalance table (ambos já usam `filter_alt`; a diferença é a classe CSS do wrapper)
- **Posicionamento do filtro**: validar que o `teleport=true` no asset table (necessário por causa do `overflow: hidden` no `.class-section-body`) produz posicionamento equivalente ao inline do rebalance; ajustar `filterPanelStyle()` se necessário
- **Formatação classe/desvio**: alinhar `class_deviation_pct` e `portfolio_deviation_pct` no asset table para usar 0 casas decimais com sinal explícito (formato `+X%` / `-X%`), igual ao rebalance table
- **Visual "Total da classe"**: transformar a linha de totais em card destaque com cor da classe (proposta de cor a ser validada pelo owner antes de implementar)
- **Espaçamento cabeçalhos**: ajustar largura da coluna "ATIVO" e/ou tamanho de fonte dos cabeçalhos para acomodar todos os nomes de coluna sem truncamento

## Capabilities

### New Capabilities

- `asset-table-visual-consistency`: alinhamento visual completo entre tabela de ativos e tabela de rebalanceamento em ícones, filtros, formatação, cabeçalho e espaçamento

### Modified Capabilities

- `shared-table-formatters`: requisito de formatação de desvio muda — `class_deviation_pct` e `portfolio_deviation_pct` devem usar 0 casas decimais com sinal explícito (padrão `formatDeviationPp`)
- `shared-filter-panel`: requisito de ícone muda — ambas as tabelas devem usar `material-symbols-outlined` como classe do wrapper do ícone de filtro

## Impact

- **Templates**: `_patrimonio_class_section.html` (cabeçalhos, linha de totais, ícones de filtro)
- **CSS**: `app.css` (estilos da linha de totais, espaçamento de cabeçalhos, possivelmente tokens de cor para card de totais)
- **JS**: `table-formatters.js` (sem mudança — as funções `formatPct` e `formatDeviationPp` já existem; mudança é no call site do template)
- **Testes**: e2e/BDD que verificam `data-testid` de filtros e formatação numérica podem precisar de ajuste
