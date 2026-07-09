## Why

O plano de rebalanceamento hoje mostra valores de compra e venda em reais, mas
não informa quantas unidades isso representa para ativos negociados em bolsa.
Sem esse número, operador precisa calcular manualmente a ordem. O gap fica
maior em ativos em USD, porque o valor de movimentação vem em BRL enquanto o
ticker atual está cotado em dólar.

## What Changes

1. Adicionar coluna `Qtd` no plano de rebalanceamento logo após `Venda`.
2. Preencher `Qtd` apenas para ativos com negociação em bolsa; ativos não
   negociáveis continuam sem quantidade operacional.
3. Calcular `Qtd` a partir do valor de compra ou venda dividido pelo preço atual
   do ticker.
4. Para ativos em `USD`, converter o valor de compra/venda de BRL para USD antes
   da divisão, usando a mesma base de cotação já resolvida no plano.
5. Estender contrato de wire/template para transportar quantidade calculada sem
   alterar endpoint nem persistência.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rebalance-page`: tabela de ativos passa a renderizar coluna `Qtd` após
  `Venda`, preenchida apenas quando ativo for negociável e houver preço atual
  apto para cálculo.
- `rebalance-route`: `RebalanceAssetPlanRow` passa a expor quantidade calculada
  para compra/venda quando possível, incluindo conversão BRL->USD antes da
  divisão para ativos dolarizados.

## Impact

- `src/omaha/rebalance/` — cálculo e mapeamento da quantidade operacional por
  ativo.
- `src/omaha/templates/_rebalance_plan.html` — nova coluna `Qtd` na tabela.
- `tests/test_rebalance_page.py`, `tests/test_rebalance_route.py` e possíveis
  testes de glue/schema — cobertura para cálculo BRL e USD.
- Nenhuma migration, novo endpoint, ou nova dependência externa.
