## Context

`/patrimonio` já carrega tabela densa em `classSection` e helpers JS locais. Hoje `Ganho` aparece em duas células, a ordenação usa valor bruto assinado, e algumas quantidades ainda exibem casas demais para leitura rápida. Em `/rebalanceamento`, `trade_quantity` ainda tem precisão maior do que a necessidade visual atual.

Slice pede só polimento de apresentação. Sem mudança em modelo, solver, rotas ou payloads.

## Goals / Non-Goals

**Goals:**
- Compactar leitura numérica em `/patrimonio` e `/rebalanceamento`.
- Unificar ganho em uma leitura única: valor absoluto + percentual.
- Ordenar ganho por magnitude absoluta.
- Manter exceção de BTC com 3 casas em quantidade.

**Non-Goals:**
- Não mudar schema, seed, API, solver, ou cálculo de posições.
- Não alterar ações, permissões, ou selectors fora da tabela afetada.
- Não criar novo componente compartilhado ou dependência externa.

## Decisions

1. **Rounding fica em formatter client-side.**
   - Racional: mudança é só de exibição; valor bruto segue íntegro em JSON/contexto.
   - Alternativa: arredondar no backend/Jinja. Rejeitada porque mistura apresentação com dado canônico e espalha lógica.

2. **`Ganho` vira célula única visível.**
   - Racional: reduz largura e leitura em uma passada, sem depender de duas colunas paralelas.
   - Alternativa: manter duas subcolunas e só apertar espaçamento. Rejeitada porque não entrega densidade pedida.

3. **Ordenação de ganho usa `abs(gain_value)`.**
   - Racional: magnitude é o sinal visual mais útil para revisão.
   - Alternativa: manter ordenação com sinal ou usar percentual. Rejeitada porque prioriza direção, não impacto.

4. **BTC recebe branch de precisão isolado no formatter.**
   - Racional: único caso explicitamente pedido; evita generalização prematura.
   - Alternativa: tabela genérica de precisão por ativo/moeda. Rejeitada por excesso de escopo.

5. **CSS segue só em `app.css`.**
   - Racional: table density e alinhamento são contrato visual; não precisam novo primitive.
    - Alternativa: criar novo sistema de layout de tabela. Rejeitada porque custo > benefício para slice.

6. **Percentuais arredondados usam helper dedicado.**
   - Racional: `formatPct` mantém duas casas para células fora do contrato;
     `formatPctRounded` é chamado somente pelas seis colunas pedidas.

7. **Filtros de Qtd e Preço médio reutilizam modelo de range existente.**
   - Racional: mantém paridade com rebalanceamento sem criar estado paralelo.

## Risks / Trade-offs

- **Risco:** perda de leitura de valores pequenos com 0 casas → **Mitigação:** manter dado bruto no payload e cobrir com testes de formatação.
- **Risco:** ordenação por magnitude pode surpreender quem espera sinal → **Mitigação:** indicador de ordenação continua no cabeçalho e testes fixam comparator.
- **Risco:** exceção BTC pode ser esquecida em novo formatter → **Mitigação:** centralizar branch em helper único e cobrir com caso dedicado.

## Migration Plan

Sem migração de banco ou rota. Deploy direto de templates/CSS/JS.

Rollback: revert diff do slice. Como mudança é presentation-only, rollback não exige dados novos nem tarefa de limpeza.

## Open Questions

Nenhuma.
