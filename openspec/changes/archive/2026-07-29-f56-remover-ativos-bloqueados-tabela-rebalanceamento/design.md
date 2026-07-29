## Context

O pipeline de rebalanceamento tem 4 camadas:

1. **Solver** (`solver.py`, `policy.py`) — CVXPY optimizer, não deve ser alterado
2. **Postprocessing** (`postprocessing.py`) — constrói DataFrame 31-col, category_plan, metrics, warnings
3. **Engine** (`engine.py`) — traduz DataFrame → dataclass list (`RebalanceAssetPlanRowNative`)
4. **Glue** (`glue.py`) — traduz dataclass → Pydantic wire format (`RebalanceAssetPlanRow`)

Ativos com `buy_enabled=False AND sell_enabled=False` hoje aparecem na tabela como "Manter" com zero em todas as colunas monetárias. O `restriction_note` já marca esses ativos como "ativo travado no setup" (postprocessing.py:385-386).

O gap atual: `RebalanceAssetPlanRowNative` (solver_stub.py) tem `buy_enabled` mas NÃO tem `sell_enabled`. O `engine.py` não passa `sell_enabled` na tradução. O `glue.py` não filtra.

## Goals / Non-Goals

**Goals:**
- Remover da tabela de ativos ativos bloqueados (buy_enabled=False AND sell_enabled=False)
- Manter category_plan, metrics, warnings e waterfall charts inalterados
- Manter o solver e policy intocados

**Non-Goals:**
- Alterar o solver ou policy
- Filtrar do category_plan ou metrics
- Adicionar indicador visual de "ativos ocultos" (v1 não precisa)
- Alterar o schema Pydantic `RebalanceAssetPlanRow`

## Decisions

### Decisão 1: Filtrar em `glue.py` (camada de display)

**Escolha:** Filtrar no loop que constrói `asset_plan` em `glue.py:run_rebalance()`.

**Alternativas consideradas:**
- **Filtrar em `engine.py`**: Rejeitado — engine é tradução fiel, não filtro de display.
- **Filtrar em `postprocessing.py`**: Rejeitado — afetaria metrics (trade_count, restriction_count) e category_plan.
- **Filtrar no template (client-side)**: Rejeitado — dados ainda trafegam no wire, complexidade desnecessária no Alpine.

**Rationale:** `glue.py` é o adaptador display — transforma dados nativos em wire format. Filtrar aqui mantém o solver intocado e o template simples. O `category_plan` já foi calculado no postprocessing com todos os ativos, então os cards de resumo ficam corretos.

### Decisão 2: Adicionar `sell_enabled` ao `RebalanceAssetPlanRowNative`

**Escolha:** Adicionar campo `sell_enabled: bool = True` ao dataclass em `solver_stub.py` e passar no `engine.py`.

**Rationale:** O campo já existe no DataFrame do solver (31 colunas). O engine precisa propagar para o glue poder filtrar. Default `True` mantém compatibilidade com fixtures existentes do stub.

### Decisão 3: Não alterar schema Pydantic

**Escolha:** `RebalanceAssetPlanRow` não recebe `buy_enabled`/`sell_enabled`. O filtro acontece antes da criação do objeto Pydantic.

**Rationale:** O wire format v1 não expõe flags de controle — são concern do setup, não do plano. Manter o schema limpo.

## Risks / Trade-offs

- **[Risco] Fixture do stub não tem `sell_enabled`** → Mitigação: default `True` no dataclass; fixture existente funciona sem alteração. Atualizar fixture se quiser testar o filtro com o stub.
- **[Risco] Métricas não batem com contagem de linhas da tabela** → Mitigação: métricas são calculadas no postprocessing com todos os ativos. A tabela mostra menos linhas por design. Documentar no spec que métricas refletem o plano completo.
- **[Trade-off] Restriction note "ativo travado no setup" fica órfão** → Ativos bloqueados não aparecem mais na tabela, então o restriction_note nunca é visto para esses ativos. Aceitável — o note existia para explicar o "Manter", que agora é invisível.
