## Why

A correção do row-pin (asset mantém a posição visual após PATCH)
foi implementada no change `fix-inline-edit-off-100-blocking`
(tarefa 5.x do tasks.md) mas só tem cobertura via browser test
ad-hoc (`/tmp/browser_diag.py`) executado uma vez contra o DB
de dev. Sem cenário BDD no repositório, qualquer regressão no
`_pinFrozen` (ex: alguém remove a chamada em `sortedAssets`)
passa silenciosa até alguém testar manualmente.

## What Changes

- Adicionar 1 cenário BDD em
  `tests/bdd/features/asset_crud.feature` (ou `target_pct.feature`,
  a definir após inspeção) que prova o row-pin: criar classe +
  3 ativos com `target_pct` 10/20/30, editar o ativo de topo
  para 80, assert que a linha dele continua sendo a primeira
  do sort e mostra "80.00%".
- Adicionar 1 step em `tests/bdd/step_defs/` para asserir a
  posição ordinal do ativo dentro da classe
  (`o ativo "Alpha" é o 1º da classe "RF Test"`).
- Sem mudança em produção.

## Capabilities

### Modified Capabilities

- `dashboard-inline-editing`: novo cenário "Row pin preserva a
  posição visual do ativo editado" — codifica o contrato que o
  client cumpre (linha estável após PATCH bem-sucedido).

## Impact

- **BDD**: +1 cenário (~15 linhas) + 1 step novo (~10 linhas).
  Usa os workflows existentes em
  `tests/bdd/step_defs/_workflows.py` (`create_one_class`,
  `add_one_asset`).
- **Produção**: zero.
- **Tests integração**: zero. Cobertura fica no BDD (browser real).
