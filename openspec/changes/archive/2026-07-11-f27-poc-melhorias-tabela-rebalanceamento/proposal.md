## Why

F22 (AG Grid Community) foi descartada pelo owner — layout não atendeu expectativa visual. Owner solicita desenvolvimento assistido e iterativo diretamente numa página de teste isolada, sem risco de afetar `/rebalanceamento`, para definir o visual/filtros finais da tabela de rebalanceamento.

## What Changes

- Adicionar rota `GET /teste` auth-protected (`require_user` + `require_active_profile`) em `src/omaha/routes/pages.py`.
- Criar template `src/omaha/templates/test/rebalance_table_poc.html` clonando a tabela legada de ativos do rebalanceamento (11 colunas: Classe, Ativo, Valor atual, Alvo, Desvio R$, Desvio %, Compra, Venda, Qtd, Projetado, Ação) com Alpine sort + multi-select filters (Classe, Ação) + busca por nome.
- Rota chama `run_rebalance(contribution=0)` com thresholds default para o perfil ativo e passa `RebalancePlanResponse` ao template.
- Reutilizar classes CSS existentes (`.rebalance-table-*`, `.rebalance-filter-*`, `.rebalance-asset-*`) de `src/omaha/static/app.css`. Nenhum estilo novo no primeiro apply.
- Sem params bar, sem cards de desvio por classe, sem estados vazios/placeholder. Scaffolding puro.

## Capabilities

### New Capabilities
- `test-rebalance-table-poc`: Página de teste isolada `/teste` que renderiza a tabela de rebalanceamento legada com dados reais do perfil ativo, servindo como playground para desenvolvimento iterativo de melhorias visuais.

### Modified Capabilities
- Nenhuma. As capabilities existentes (`rebalance-page`, `rebalance-route`, `route-test-alignment`) não têm requisitos alterados — a rota `/rebalanceamento` permanece inalterada.

## Impact

- **Código**: Adição em `src/omaha/routes/pages.py` (nova rota GET). Novo template em `src/omaha/templates/test/rebalance_table_poc.html`. Nenhum arquivo existente modificado.
- **Testes**: Novo arquivo `tests/test_rebalance_table_poc.py` (precisa ser registrado em `_INTEGRATION_PREFIXES` no `conftest.py`). Testes existentes de `/rebalanceamento` continuam passando sem alterações.
- **Dependências**: Nenhuma nova dependência.
- **Side effects**: Rota é stateless — não persiste aporte, não modifica sessão, não afeta banco.
