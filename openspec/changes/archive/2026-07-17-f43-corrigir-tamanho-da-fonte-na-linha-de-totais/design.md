## Context

A tabela de patrimônio usa `table-layout: fixed` com `font-size: 0.9rem` definido em `.asset-table` (app.css:1254). A linha de totais da classe (`.class-totals-row`) herda esse valor, mas o label "Total da classe" (`.class-totals-label`) tem `font-size: 0.75rem` (app.css:1818), criando uma assimetria visual.

CSS relevante:
```css
.asset-table { font-size: 0.9rem; }           /* linha 1254 */
.class-totals-row td { font-weight: 600; }    /* linha 1807 */
.class-totals-label { font-size: 0.75rem; }   /* linha 1818 */
```

## Goals / Non-Goals

**Goals:**
- Alinhar tamanho da fonte da linha de totais com o padrão da tabela
- Manter hierarquia visual (label menor é intencional, mas valores devem ser 0.9rem)
- Garantir que não há herança indesejada entre células

**Non-Goals:**
- Mudar o tamanho do label "Total da classe" (0.75rem é intencional para uppercase/letter-spacing)
- Alterar largura de colunas (escopo de F44)
- Modificar conteúdo ou comportamento da linha de totais

## Decisions

1. **Manter `.class-totals-label` em 0.75rem** — O label é intencionalmente menor para criar hierarquia visual com uppercase + letter-spacing. Não alterar.

2. **Adicionar `font-size: inherit` em `.class-totals-row td`** — Garantir que células de valores herdem explicitamente o 0.9rem da tabela, evitando qualquer herança indesejada do label ou outros seletores.

3. **Alternativa considerada e rejeitada:** Remover `font-size: 0.75rem` de `.class-totals-label` — Rejeitado porque o label menor é um padrão visual consistente com headers de seção na tabela.

## Risks / Trade-offs

- **Risco baixo:** Ajuste CSS puro, sem impacto em comportamento ou testes
- **Trade-off:** Label menor vs. valores maiores — hierarquia visual mantida intencionalmente
- **Rollback:** Reverter uma linha de CSS se o resultado não for satisfatório
