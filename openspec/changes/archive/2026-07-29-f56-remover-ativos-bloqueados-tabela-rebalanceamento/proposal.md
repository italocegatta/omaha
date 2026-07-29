## Why

Ativos com compra E venda bloqueadas (`buy_enabled=False` AND `sell_enabled=False`) aparecem na tabela de ativos do `/rebalanceamento` como "manter" — contribuem ruído visual sem nenhuma informação útil. O operador vê linhas que sempre mostram "Manter R$ 0" e nenhuma ação possível. Remover essas linhas da tabela reduz clutter e melhora a legibilidade do plano.

## What Changes

- Filtrar da tabela de ativos (asset_plan) qualquer ativo onde `buy_enabled == False AND sell_enabled == False`
- O filtro é **apenas na camada de exibição** — o solver, métricas, category_plan e waterfall charts NÃO são alterados
- Ativos com pelo menos um lado habilitado (buy OU sell) permanecem visíveis
- O `restriction_note` existente em `postprocessing.py` já marca esses ativos como "ativo travado no setup" — isso pode ser aproveitado

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rebalance-page`: Novo requisito — ativos bloqueados (buy_enabled=False AND sell_enabled=False) SHALL NOT aparecer na tabela de ativos. Category summary cards e waterfall charts permanecem inalterados.

## Impact

- `src/omaha/rebalance/solver_stub.py` — adicionar campo `sell_enabled` ao `RebalanceAssetPlanRowNative`
- `src/omaha/rebalance/engine.py` — passar `sell_enabled` no `_translate_asset_plan()`
- `src/omaha/rebalance/glue.py` — filtrar ativos bloqueados ao construir a lista `asset_plan`
- `src/omaha/templates/rebalance.html` — sem alteração (filtro é server-side)
- Testes existentes do rebalance podem precisar de ajuste se verificam contagem de linhas
