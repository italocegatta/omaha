## Why

Os cards de classe do `/rebalanceamento` aparecem hoje em ordem alfabética porque `_computeCategories()` ordena `plan.category_plan` por `category_name` via `localeCompare`. O owner definiu uma ordem normativa de leitura (`RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`) e quer vê-la imediatamente, sem depender da renumeração server-side do seed (F54).

## What Changes

- Renderizar os cards de classe do resumo de rebalanceamento na ordem fixa `RF Pós, RF Dinâmica, FII, Ações, Internacional, Cripto`.
- Implementar a ordem como mapa nome→posição no JavaScript da página, aplicado sobre `displayCategories`.
- Definir fallback explícito: classe não listada vai para o final, ordenada alfabeticamente entre si.
- Remover estado/funções de ordenação de cards que ficam mortos após a ordem fixa (`categorySortKey`, `categorySortDir`, `sortByCategory`, `sortIndicatorCategory`, `rebalanceCategorySortFn`), pois não há controle de UI que os invoque.
- Adicionar teste comportamental assertindo a ordem posicional dos cards e atualizar baseline visual `rebalance-plan`.
- NÃO alterar schema (`RebalanceCategoryPlanRow` continua com exatamente 7 campos), payload server-side, CSS, conteúdo dos cards/waterfall, tabela por ativo, métricas globais ou solver.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `rebalance-page`: adiciona requisito de ordem normativa dos class summary cards e remove a ordenação client-side por nome/numérico dos cards.

## Impact

- Código: `src/omaha/templates/rebalance.html` (sort helper e estado Alpine dos cards).
- Template: `src/omaha/templates/_rebalance_plan.html` somente se necessário para remover amarrações mortas; loop `x-for="c in displayCategories"` permanece.
- Testes: `tests/test_rebalance_page.py` (nova assertion/teste de ordem), `tests/visual/test_snapshots.py` baseline `rebalance-plan`.
- Sem impacto em API, DB, seed, solver, rotas ou dependências.
