## Why

Filtros da tabela de patrimônio (dashboard) estão quebrados. Três causas raiz:

1. **Teleport (já corrigido):** `teleport=true` foi adicionado a todas as 14 chamadas `filter_controls()`. Painéis movidos para `<body>` sem coordenadas de posicionamento. → Corrigido: teleport removido, overflow ajustado, stub `filterPanelStyle` removido.

2. **Race condition na importação dinâmica (pendente):** `_patrimonio_add_asset_modal.html:1464-1469` usa `import().then()` assíncrono para carregar `table-filters.js` e `table-formatters.js`. O Alpine init (`classSection()`) pode executar **antes** do `window.__tableFilters` estar disponível. Quando isso acontece, TODAS as operações de filtro (`toggleFilterPanel`, `filterActive`, `clearFilter`, `filteredAssets`, etc.) silenciosamente não fazem nada — retornam `undefined` ou `false` sem erro.

3. **Falta de fallbacks inline (pendente):** Os métodos de filtro em `classSection` dependem inteiramente de `window.__tableFilters`. Se o import falha ou é lento, não há fallback. A página rebalance tem funções inline completas (`rebalance.html:152-254`) que funcionam independentemente do import. Patrimonio precisa do mesmo padrão.

4. **`openFilter` vazio (pendente):** `openFilter: {}` (linha 774) não tem chaves pré-populadas. Rebalance inicializa todas as colunas com `false` (`rebalance.html:348-356`). Sem chaves, `x-show="openFilter[column.key]"` pode ter comportamento imprevisível.

Página rebalance funciona perfeitamente porque: (a) usa `<script type="module">` síncrono, (b) tem fallbacks inline completos, (c) pré-popula `openFilter`.

## What Changes

### Já feito (partial fix):
- ~~Remover `teleport=true` de todas as 14 chamadas `filter_controls()`~~ ✓
- ~~Alterar `.portfolio-table-shell` para `overflow: visible`~~ ✓
- ~~Remover stub `filterPanelStyle`~~ ✓

### Ainda pendente:

1. **Importação estática:** Trocar `import().then()` dinâmico (linhas 1464-1469) por `<script type="module">` síncrono no final do template, idêntico ao padrão de `rebalance.html:529-534`.

2. **Fallbacks inline em classSection:** Adicionar fallbacks completos para TODOS os métodos de filtro, seguindo o padrão de `rebalance.html:152-254`:
   - `toggleFilterPanel` — com fallback inline (não só `if (tf)`)
   - `filterActive` — com fallback inline
   - `clearFilter` — com fallback inline
   - `filteredAssets` (getter) — com fallback inline via `_computeFilteredRows`
   - `rangeBounds` — já tem `_rangeBoundsInline`, mas o método principal ainda depende de `tf`
   - `rangeStep` — já tem `_rangeStepInline`, mas o método principal ainda depende de `tf`
   - `ensureRangeBounds` — com fallback inline
   - `clampRangeMin` — com fallback inline
   - `clampRangeMax` — com fallback inline
   - `rangeFillStyle` — já tem fallback inline parcial
   - `formatRangeValue` — já tem fallback inline parcial
   - `_computeFilteredRows` — novo, fallback inline para filteredAssets

3. **Pré-popular `openFilter`:** Trocar `openFilter: {}` por objeto com todas as chaves de colunas setadas para `false`, como `rebalance.html:348-356`.

## Capabilities

### New Capabilities

Nenhuma. Correção de bug, não adiciona funcionalidade.

### Modified Capabilities

- `patrimonio-filtros`: Filtros de tabela voltam a funcionar corretamente. Requisito existente de filtros funcionais na tabela de patrimônio é restaurado.

## Impact

- `src/omaha/templates/_patrimonio_add_asset_modal.html` — importação estática, fallbacks inline, openFilter pré-populado
- Nenhuma mudança de API, dependência, ou schema
