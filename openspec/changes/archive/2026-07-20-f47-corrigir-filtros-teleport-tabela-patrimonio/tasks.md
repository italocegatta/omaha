## 1. Reverter teleport nas chamadas filter_controls ✓

- [x] 1.1 Remover `teleport=true` de todas as 14 chamadas `filter_controls()` em `_patrimonio_class_section.html`
- [x] 1.2 Verificar que `align='left'` foi preservado nas colunas buy, sell, e portfolio-deviation

## 2. Corrigir overflow CSS ✓

- [x] 2.1 Alterar `.portfolio-table-shell` em `app.css` de `overflow-x: auto; overflow-y: hidden` para `overflow: visible`

## 3. Limpar código morto ✓

- [x] 3.1 Remover stub `filterPanelStyle: function () { return ''; }` de `_patrimonio_add_asset_modal.html`

## 4. Importação estática de módulos

- [x] 4.1 Trocar `import('/static/table-formatters.js').then(...)` e `import('/static/table-filters.js').then(...)` (linhas 1464-1469) por `<script type="module">` no final do template, como `rebalance.html:529-534`:
  ```
  import * as formatters from '/static/table-formatters.js';
  import * as filters from '/static/table-filters.js';
  window.__tableFormatters = formatters;
  window.__tableFilters = filters;
  ```
- [x] 4.2 Remover o bloco `import().then()` de dentro do `alpine:init` listener (linhas 1463-1470)

## 5. Fallbacks inline em classSection

- [x] 5.1 Adicionar `_computeFilteredRows` inline fallback em `classSection` (seguir `rebalance.html:228-254`, adaptar para patrimonio columns)
- [x] 5.2 Reescrever `toggleFilterPanel` para ter fallback inline (seguir `rebalance.html:203-213`)
- [x] 5.3 Reescrever `filterActive` para ter fallback inline (seguir `rebalance.html:192-202`)
- [x] 5.4 Reescrever `clearFilter` para ter fallback inline (seguir `rebalance.html:214-227`)
- [x] 5.5 Reescrever `ensureRangeBounds` para ter fallback inline (seguir `rebalance.html:162-166`)
- [x] 5.6 Reescrever `clampRangeMin` para ter fallback inline (seguir `rebalance.html:167-172`)
- [x] 5.7 Reescrever `clampRangeMax` para ter fallback inline (seguir `rebalance.html:173-178`)
- [x] 5.8 Garantir que `filteredAssets` getter use `_computeFilteredRows` como fallback quando `tf` não disponível
- [x] 5.9 Garantir que `rangeBounds`, `rangeStep`, `rangeFillStyle`, `formatRangeValue` mantêm fallbacks inline existentes (já parciais)

## 6. Pré-popular openFilter

- [x] 6.1 Trocar `openFilter: {}` (linha 774) por objeto com todas as chaves de colunas setadas para `false`: `name`, `buy`, `sell`, `currency`, `qty`, `avg-price`, `gain`, `position`, `position-deviation`, `class-current`, `class-target`, `class-deviation`, `portfolio-current`, `portfolio-target`, `portfolio-deviation`

## 7. Verificação

- [ ] 7.1 Executar `refresh-for-test` e verificar que filtros da tabela de patrimônio funcionam (abrem, filtram, limpam)
- [ ] 7.2 Verificar que filtros funcionam em cold load (sem cache, módulo pode não ter carregado ainda)
- [ ] 7.3 Verificar que painéis de filtro não são clipped pelo container da tabela
- [ ] 7.4 Verificar que buy/sell mantêm `align='left'`
