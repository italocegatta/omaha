## Context

A tabela de patrimônio tem cabeçalhos agrupados com `colspan="3"` para "Classe" e "Carteira" (template: linhas 109-110). A borda inferior (`border-bottom: 1px solid var(--table-border-strong)` em `.rebalance-table-th`) é contínua entre os dois grupos, sem separação visual.

HTML atual:
```html
<tr class="asset-table-group-row">
  <th colspan="3" class="data-table-th rebalance-table-th">Classe</th>
  <th colspan="3" class="data-table-th rebalance-table-th">Carteira</th>
</tr>
```

## Goals / Non-Goals

**Goals:**
- Criar separação visual clara entre os grupos "Classe" e "Carteira"
- Manter a borda inferior, mas quebrá-la entre os dois grupos
- Usar abordagem CSS que não dependa de mudanças HTML significativas

**Non-Goals:**
- Mudar a estrutura da tabela ou número de colunas
- Alterar o comportamento de ordenação ou filtros
- Modificar o conteúdo dos cabeçalhos

## Decisions

1. **Usar classes CSS nos `<th>` do grupo** — Adicionar classes `rebalance-table-th--group-end` (no "Classe") e `rebalance-table-th--group-start` (no "Carteira") para estilizar individualmente.

2. **Aplicar bordas laterais como separador:**
   - `rebalance-table-th--group-end`: `border-right: 2px solid var(--accent)` (verde da marca)
   - `rebalance-table-th--group-start`: `border-left: 2px solid var(--accent)`
   - Essas bordas criam um "corte" visual na borda contínua

3. **Alternativa considerada e rejeitada:** Gap/padding entre os grupos — Rejeitado porque pode quebrar o alinhamento do `table-layout: fixed` e causar saltos visuais.

4. **Alternativa considerada e rejeitada:** Remover borda inferior e usar apenas fundo de cor diferente — Rejeitado porque a borda é importante para separar cabeçalhos do conteúdo.

## Risks / Trade-offs

- **Risco baixo:** Ajuste CSS + HTML mínimo (2 classes), sem impacto em comportamento
- **Trade-off:** Borda vertical pode parecer "pesada" — usar cor `--accent` (verde) para manter consistência com a marca
- **Rollback:** Remover as duas classes e regras CSS
