# Handoff: POC → Official Rebalance Table

Este documento consolida as diferenças entre a tabela POC (`/teste`) e a tabela oficial (`/rebalanceamento`), para que outro desenvolvedor replique as melhorias na oficial.

---

## 1. Estrutura das colunas (declarativa)

A POC define colunas como um array JavaScript dentro do Alpine component. **Não há markup duplicado** — todo o `<thead>` e `<tbody>` são renderizados via `x-for`.

```js
columns: [
  { key: 'action',         type: 'enum',      label: 'Ação',       sortKey: 'action' },
  { key: 'category_name',  type: 'enum',      label: 'Classe',     sortKey: 'category_name' },
  { key: 'asset_name',     type: 'enum',      label: 'Ativo',      sortKey: 'asset_name' },
  { key: 'current_value',  type: 'range',     label: 'Atual',      sortKey: 'current_value',  fractionDigits: 0 },
  { key: 'target_value',   type: 'range',     label: 'Alvo',       sortKey: 'target_value',   fractionDigits: 0 },
  { key: 'deviation',      type: 'composite', label: 'Desvio',     sortKey: 'deviation_value',
    ranges: [
      { key: 'deviation_value', label: 'Valor (R$)',  fractionDigits: 0 },
      { key: 'deviation_pct',   label: 'Percentual',  format: 'deviationPp' },
    ]},
  { key: 'projected_value', type: 'range',    label: 'Projetado',  sortKey: 'projected_value' },
  { key: 'operation',       type: 'composite', label: 'Operação',  sortKey: 'operation',
    cellFormat: 'operation', panelAlign: 'left',
    ranges: [
      { key: 'buy_amount',  label: 'Compra (R$)' },
      { key: 'sell_amount', label: 'Venda (R$)'  },
    ]},
]
```

### Propriedades de coluna

| Propriedade  | Tipo     | Obrigatória | Descrição |
|-------------|----------|-------------|-----------|
| `key`       | string   | sim | Identificador único. Usado para `data-testid`, `openFilter[key]`, `headerRangeFilters[key]`. |
| `type`      | `'enum'` / `'range'` / `'composite'` | sim | Determina o tipo de filtro e renderização. |
| `label`     | string   | sim | Texto exibido no cabeçalho. |
| `sortKey`   | string   | sim | Chave usada para ordenação. Para `operation`, usa função especial (`operationSignedValue`). |
| `fractionDigits` | int | não | Casas decimais para `formatBRL`. |
| `ranges`    | array    | só composite | Sub-filtros do painel. |
| `cellFormat`| `'operation'` | não | Formatação customizada da célula. |
| `panelAlign`| `'left'` / `'right'` | não | Para onde o painel abre em relação ao ícone. Padrão `'right'`. |
| `format`    | string   | só sub-range | `'deviationPp'` para formatar como percentual. |

---

## 2. Tipos de coluna e filtro

### `type: 'enum'`
Filtro multi-select com checkboxes. Valores extraídos do `asset_plan` via `uniqueHeaderValues()`.

- Estado: `headerFilters[column.key]` → `string[]`
- Todo panel inclui opção "Todas"/"Todos" que limpa a seleção.

### `type: 'range'`
Slider duplo (min/max) com range natural dos dados.

- Estado: `headerRangeFilters[column.key]` → `{ min: number|null, max: number|null }`
- Valores inicializados com bounds dos dados ao abrir o painel.

### `type: 'composite'`
Painel com múltiplos sliders (ex.: Desvio → Valor R$ + Percentual; Operação → Compra + Venda).

- Estado reusa `headerRangeFilters` com as chaves dos sub-ranges.
- `panelAlign` deve ser `'left'` para a última coluna, evitando que o painel saia da viewport.

---

## 3. Estado Alpine component

```js
{
  plan: {},                     // asset_plan do backend
  sortKey: 'category_name',
  sortDir: 'asc',
  displayRows: [],
  columns: [...],               // modelo declarativo (acima)
  headerFilters: {},            // { category_name: ['RF', 'RV'], action: [], ... }
  openFilter: {},               // { action: false, current_value: false, ... }
  headerRangeFilters: {},       // { current_value: { min: null, max: null }, ... }
}
```

### Funções-chave

| Função | Descrição |
|--------|-----------|
| `formatCell(row, column)` | Renderiza a célula baseada no tipo da coluna. Usa `formatBRL`, `formatDeviationCombined`, `formatOperation`. |
| `cellClass(row, column)` | Classes CSS da célula. |
| `cellInnerClass(column)` | `'rebalance-action-badge'` para action/operation. |
| `filterActive(column)` | True se filtro da coluna está em uso. |
| `toggleFilterPanel(key)` | Abre/fecha painel, fecha outros, inicializa bounds para range/composite. |
| `clearFilter(key)` | Limpa filtro da coluna. |
| `rangeBounds(key)` | Computa min/max da série no asset_plan. |
| `rangeFillStyle(key)` | Estilo CSS inline para preenchimento do slider dual. |
| `operationSignedValue(row)` | Valor com sinal para ordenação de operação (buy positivo, sell negativo). |
| `pocSortFn(key, dir)` | Factory de função de comparação. Usa `operationSignedValue` para 'operation'. |

---

## 4. Alinhamento das células

Na POC, todas as células e cabeçalhos devem estar alinhados à esquerda:

```css
.poc-rebalance-page .rebalance-table-th,
.poc-rebalance-page .rebalance-asset-cell,
.poc-rebalance-page .rebalance-asset-cell--num {
  text-align: left;
}
```

Isso sobrescreve o `text-align: right` padrão de `.rebalance-asset-cell--num`.

---

## 5. Posicionamento do painel de filtro

A classe que controla a âncora do painel usa `panelAlign` no modelo:

```css
.rebalance-filter-panel--right {
  left: calc(100% - 0.5rem);   /* canto esquerdo alinhado ao canto direito do th */
  right: auto;
}
.rebalance-filter-panel--left {
  left: auto;
  right: 0.5rem;               /* canto direito alinhado ao canto direito do th */
}
```

- **Padrão (`panelAlign: 'right'` )**: painel abre à direita do th, não tapa a coluna.
- **Última coluna (`panelAlign: 'left'` )**: painel abre à esquerda do th, fica dentro da viewport.

---

## 6. CSS relevante para replicar

Todos os estilos estão em `src/omaha/static/app.css`:

| Seletor | Propósito |
|---------|-----------|
| `.rebalance-table-th--has-filter` | Padding-right para acomodar ícones. |
| `.rebalance-header-actions` | Wrapper absoluto dos botões. |
| `.rebalance-header-filter-btn` | Botão do funil. |
| `.rebalance-header-clear-btn` | Botão X. |
| `.rebalance-filter-panel--header` | Painel dropdown (scrollbar customizada, sombra, borda). |
| `.rebalance-filter-range` → `.rebalance-range-slider` | Slider dual (track, fill, thumbs triangulares). |
| `.rebalance-action-badge--buy` / `--sell` / `--hold` | Cores dos badges de ação. |
| `.rebalance-deviation--pos` / `--neg` | Cores de desvio positivo/negativo. |

### Scrollbar customizada
```css
.rebalance-filter-panel--header {
  scrollbar-width: thin;
  scrollbar-color: var(--border-strong) transparent;
}
.rebalance-filter-panel--header::-webkit-scrollbar { width: 5px; }
.rebalance-filter-panel--header::-webkit-scrollbar-track { background: transparent; }
.rebalance-filter-panel--header::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 3px; }
.rebalance-filter-panel--header::-webkit-scrollbar-thumb:hover { background: var(--ink); }
```

---

## 7. Funções de formatação que precisam existir no component

- `formatBRL(value, fractionDigits?)` — `style: 'currency', currency: 'BRL'`.
- `formatDeviationPp(v)` — `'+4%'` ou `'-2%'` (0 casas decimais).
- `formatDeviationCombined(row)` — `'R$ 1.299 (+15%)'`.
- `formatOperation(row)` — `'Comprar R$ 1.299 (31)'` ou `'Manter'`.
- `formatQuantity(value, assetName)` — 0 casas, 4 se BTC.
- `actionLabel(action)` — `'Comprar'` / `'Vender'` / `'Manter'`.

---

## 8. Ordenação das colunas

O clique no `<th>` chama `sortBy(column.sortKey)`. Para colunas numéricas, compara como número. Para text, localeCompare. Para `'operation'`, usa `operationSignedValue(row)`:

```js
var operationSignedValue = function (row) {
  if (row.action === 'buy') return Number(row.buy_amount) || 0;
  if (row.action === 'sell') return -(Number(row.sell_amount) || 0);
  return 0;
};
```

Isso faz "Comprar" ser positivo e "Vender" negativo.

Indicador: `▲` ascendente, `▼` descendente.

---

## 9. Scaffolding para replicar na tabela oficial

### Passo 1 — Template
Substituir o `<thead>` e `<tbody>` hardcoded por:
```html
<template x-for="column in columns" :key="column.key">
  <th class="rebalance-table-th rebalance-table-th--has-filter"
      :class="column.type !== 'enum' ? 'rebalance-table-th--num' : ''"
      :data-testid="'poc-asset-th-' + column.key"
      @click="sortBy(column.sortKey)">
    <span class="rebalance-table-th-label" x-text="column.label"></span>
    <span class="rebalance-table-th-indicator" x-text="sortIndicator(column.sortKey)"></span>
    <div class="rebalance-header-actions">
      <button class="rebalance-header-filter-btn" ...>
        <span class="material-symbols-outlined">filter_alt</span>
      </button>
      <button class="rebalance-header-clear-btn" ...>
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>
    <!-- x-if type enum / range / composite -->
  </th>
</template>
```

### Passo 2 — JS
Copiar o objeto do Alpine component (`pocRebalancePage` → renomear) e adaptar:
- `plan` → dados da API.
- `columns` → ajustar keys conforme os campos do modelo.
- Verificar se `asset_plan` contém as mesmas chaves.
- Se a tabela oficial usa nomes de campo diferentes, mapear.

### Passo 3 — CSS
Copiar todos os seletores com prefixo `.rebalance-` para o contexto oficial. Garantir que as variáveis CSS (`--surface`, `--accent`, `--ink`, `--border-strong`, `--ink-muted`) existam no tema.

### Passo 4 — Testes
- Verificar `data-testid` gerados dinamicamente.
- Testes de contagem de colunas devem verificar o array `columns` no JS, não tags HTML estáticas.
- Testes de filtros devem verificar classes de infraestrutura, não `data-testid` específicos.

---

## 10. Variáveis CSS usadas (tema Catppuccin Frappe)

| Variável         | Valor aproximado |
|-----------------|------------------|
| `--surface`     | Base escura      |
| `--accent`      | `oklch(0.783 0.073 184.6)` (verde) |
| `--ink`         | Texto principal  |
| `--ink-muted`   | `oklch(0.80 0.04 274.5)` |
| `--border-strong` | Borda destaque |
| `--border`      | Borda sutil      |
| `--negative`    | `oklch(0.717 0.124 19.4)` (vermelho) |

---

## Referências

- Template POC: `src/omaha/templates/test/rebalance_table_poc.html`
- CSS: `src/omaha/static/app.css` (seções a partir da linha ~3075)
- Testes: `tests/test_rebalance_table_poc.py`
- Rota: `src/omaha/routes/pages.py` (`/teste` → `test_rebalance_poc`, `/rebalanceamento` → `rebalance`)
