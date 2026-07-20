## Context

Tabela de patrimônio no dashboard (`_patrimonio_class_section.html`) usa macro compartilhada `filter_controls()` de `_filter_controls.html`. Filtros estavam completamente quebrados por três motivos:

1. **Teleport (corrigido):** `teleport=true` adicionado a 14 chamadas `filter_panel()`. Painéis movidos para `<body>` sem posicionamento. Corrigido: teleport removido, overflow ajustado, stub removido.

2. **Importação dinâmica com race condition:** `_patrimonio_add_asset_modal.html:1464-1469` carrega `table-filters.js` via `import().then()` assíncrono. O `classSection()` Alpine init pode executar antes de `window.__tableFilters` existir. Quando isso acontece, `toggleFilterPanel`, `filterActive`, `clearFilter`, `filteredAssets` silenciosamente falham — `if (!tf) return;` em cada método.

3. **`openFilter` vazio:** `openFilter: {}` (linha 774) não pré-popula chaves. Rebalance (`rebalance.html:348-356`) inicializa todas com `false`. Sem chaves, `x-show` pode ter comportamento indefinido.

Página rebalance funciona porque: (a) `<script type="module">` síncrono no final do template, (b) fallbacks inline completos para todos os filtros (`rebalance.html:152-254`), (c) `openFilter` pré-populado.

## Goals / Non-Goals

**Goals:**
- Eliminar race condition na importação de `table-filters.js` e `table-formatters.js`
- Garantir que filtros funcionem mesmo se o módulo JS não carregar (fallbacks inline)
- Pré-popular `openFilter` com todas as chaves de colunas
- Alinhar padrão de importação com `rebalance.html` (referência funcional)

**Non-Goals:**
- Não alterar lógica de filtros (enum, range, composite)
- Não alterar macro `filter_controls()` — ela já suporta inline
- Não alterar página rebalance
- Não adicionar novos filtros ou colunas
- Não alterar os 3 itens já corrigidos (teleport, overflow, stub)

## Decisions

### D1: Importação estática via `<script type="module">` (em vez de `import().then()`)

**Escolha:** Trocar `import().then()` dinâmico por `<script type="module">` síncrono no final do template, como `rebalance.html:529-534`.

**Alternativa considerada:** Manter `import().then()` e adicionar retry/polling. Rejeitada porque:
- Complexidade desnecessária — módulo estático resolve 100% do problema
- `<script type="module">` é defer por spec — executa após parse do HTML, antes de DOMContentLoaded
- Padrão já funciona em rebalance (mesma stack Alpine + Jinja)

### D2: Fallbacks inline completos em classSection

**Escolha:** Cada método de filtro em `classSection` terá implementação inline completa, seguindo `rebalance.html:152-254`.

**Padrão:** `var tf = window.__tableFilters; if (tf) return tf.method(...); /* fallback inline */`

**Alternativa considerada:** Delegar tudo para `table-filters.js` e confiar no import. Rejeitada porque:
- Se import falha (network, CDN), filtros ficam 100% quebrados
- Fallbacks inline são ~100 linhas de JS — baixo custo, alta resiliência
- Mesmo padrão já existe em rebalance e funciona

### D3: Pré-popular `openFilter` com todas as chaves

**Escolha:** Inicializar `openFilter` com todas as chaves de colunas setadas para `false`.

**Rationale:** `rebalance.html:348-356` faz isso. Alpine precisa das chaves existentes para `x-show="openFilter[column.key]"` e `@click.outside` funcionarem corretamente. Objeto vazio `{}` pode causar reatividade inconsistente.

## Risks / Trade-offs

**[Risk] Duplicação de lógica de filtros** → Fallbacks inline duplicam `table-filters.js`. Mitigação: mesma duplicação existe em rebalance e é aceita como trade-off de resiliência. `table-filters.js` continua sendo o path primário; fallback só ativa se módulo não carregou.

**[Risk] Importação estática pode atrasar render** → `<script type="module">` é defer, não bloqueia. Mesmo padrão em rebalance não causa problemas. Módulos são pequenos (<5KB).

## Migration Plan

Sem migração. Mudança é template JS only. Deploy junto com próximo commit.
