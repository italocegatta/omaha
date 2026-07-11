# test-rebalance-table-poc Specification

## Purpose

Define o contrato da página de teste isolada `GET /teste` que renderiza a tabela de rebalanceamento legada (11 colunas, sortable, filtrável) com dados reais do perfil ativo. Serve como playground para desenvolvimento iterativo de melhorias visuais sem afetar a rota de produção `/rebalanceamento`.

## Requirements

### Requirement: GET /teste retorna a página de teste com tabela de rebalanceamento

O sistema SHALL expor `GET /teste` que retorna HTTP 200 com o template `rebalance_table_poc.html` renderizado. O template SHALL estender `base.html` e conter a tabela de ativos do plano de rebalanceamento.

Auth segue o padrão do projeto: `require_user` + `require_active_profile`. Usuário não autenticado SHALL ser redirecionado para `/login` (303).

#### Scenario: Usuário autenticado com perfil ativo vê a página de teste

- **WHEN** o usuário está autenticado com um perfil ativo que possui classes e ativos
- **AND** `GET /teste` é chamada
- **THEN** a resposta é HTTP 200
- **AND** o corpo contém o template `rebalance_table_poc.html`
- **AND** a tabela de ativos (`data-testid="poc-asset-table"`) está presente com dados do `RebalancePlanResponse`

#### Scenario: Usuário não autenticado é redirecionado para /login

- **WHEN** `GET /teste` é chamada sem sessão válida
- **THEN** a resposta é HTTP 303 com `Location: /login`

#### Scenario: Perfil ativo sem classes renderiza tabela vazia

- **WHEN** o perfil ativo tem zero `AssetClass` rows
- **AND** `GET /teste` é chamada
- **THEN** a resposta é HTTP 200
- **AND** a tabela de ativos contém zero linhas no `<tbody>`

### Requirement: Rota não tem side effects

A rota SHALL ser stateless: não persiste aporte, não modifica a sessão, não altera o banco de dados. A chamada a `run_rebalance` usa `contribution=0` com thresholds default.

#### Scenario: Sessão não é modificada após GET /teste

- **WHEN** `GET /teste` é chamada
- **THEN** nenhuma chave de sessão é adicionada, removida ou alterada além do que existia antes da requisição

### Requirement: Tabela tem 11 colunas visíveis

O sistema SHALL renderizar a tabela de ativos com exatamente 11 colunas `<th>` no `<thead>`: Classe, Ativo, Valor atual, Alvo, Desvio (R$), Desvio (%), Compra, Venda, Qtd, Projetado, Ação.

Cada linha `<tr>` no `<tbody>` SHALL ter o atributo `data-asset-key` com o valor `asset_key` do wire format.

#### Scenario: Cabeçalho tem 11 colunas

- **WHEN** a página renderiza com plano populado
- **THEN** `<thead>` contém exatamente 11 elementos `<th>`
- **AND** os textos são: Classe, Ativo, Valor atual, Alvo, Desvio (R$), Desvio (%), Compra, Venda, Qtd, Projetado, Ação

#### Scenario: Linhas têm data-asset-key

- **WHEN** a página renderiza com `asset_plan` contendo 3 ativos
- **THEN** cada `<tr>` no `<tbody>` tem o atributo `data-asset-key` igual ao `asset_key` do respectivo ativo

### Requirement: Tabela é sortável por coluna

O sistema SHALL tornar a tabela sortável por clique nos `<th>`. Clique alterna `asc → desc → asc` na mesma coluna. Ordem padrão é a ordem nativa do solver.

#### Scenario: Clique em coluna ordena ascendente

- **WHEN** o usuário clica no `<th>` "Valor atual"
- **THEN** as linhas são reordenadas por `current_value` ascendente
- **AND** o `<th>` clicado mostra indicador `↑`

#### Scenario: Segundo clique no mesmo `<th>` ordena descendente

- **WHEN** o usuário clica duas vezes no `<th>` "Valor atual"
- **THEN** as linhas são reordenadas por `current_value` descendente
- **AND** o `<th>` mostra indicador `↓`

### Requirement: Filtro multi-select por Classe

O sistema SHALL prover um filtro multi-select para Classe. Quando nenhuma classe está selecionada, todas as classes são exibidas. Quando uma ou mais classes são selecionadas, apenas ativos dessas classes aparecem.

#### Scenario: Filtrar por classe exibe apenas ativos da classe selecionada

- **WHEN** o operador seleciona apenas a classe "Renda Fixa"
- **THEN** apenas ativos com `category_name = "Renda Fixa"` são visíveis na tabela

#### Scenario: Nenhuma classe selecionada exibe todas

- **WHEN** nenhuma classe está selecionada no filtro
- **THEN** todos os ativos do plano são visíveis

### Requirement: Filtro multi-select por Ação

O sistema SHALL prover um filtro multi-select para Ação (Comprar/Vender/Manter). Funciona com a mesma lógica do filtro de Classe.

#### Scenario: Filtrar por ação exibe apenas ativos com aquela ação

- **WHEN** o operador seleciona apenas "Comprar" no filtro de ação
- **THEN** apenas ativos com `action = "buy"` são visíveis

### Requirement: Busca por nome do ativo

O sistema SHALL prover um campo de busca textual que filtra ativos por `asset_name` (case-insensitive).

#### Scenario: Busca por nome filtra ativos

- **WHEN** o operador digita "PETR" no campo de busca
- **THEN** apenas ativos cujo `asset_name` contém "PETR" (case-insensitive) são visíveis

#### Scenario: Filtros combinam com AND

- **WHEN** classe "Renda Fixa" está selecionada **AND** ação "Comprar" está selecionada **AND** busca está vazia
- **THEN** apenas ativos que satisfazem TODOS os critérios são visíveis

### Requirement: Tabela usa classes CSS existentes

O sistema SHALL reutilizar as classes CSS existentes definidas em `src/omaha/static/app.css` para a tabela de rebalanceamento legada. Nenhum novo estilo CSS SHALL ser adicionado no primeiro apply.

Classes obrigatórias por elemento:
- Tabela: `.rebalance-table`
- Células de cabeçalho: `.rebalance-table-th`, `.rebalance-table-th--num`, `.rebalance-table-th-label`, `.rebalance-table-th-indicator`
- Células de dados: `.rebalance-asset-cell`, `.rebalance-asset-cell--num`, `.rebalance-asset-cell--action`
- Linhas: `.rebalance-asset-row`, `.rebalance-asset-row--buy`, `.rebalance-asset-row--sell`, `.rebalance-asset-row--neutral`
- Badge de ação: `.rebalance-action-badge`, `.rebalance-action-badge--buy`, `.rebalance-action-badge--sell`, `.rebalance-action-badge--hold`
- Filtros: `.rebalance-filter-bar`, `.rebalance-filter-group`, `.rebalance-filter-trigger`, `.rebalance-filter-panel`, `.rebalance-filter-option`, `.rebalance-filter-search`

#### Scenario: Tabela usa classes CSS legadas

- **WHEN** a página renderiza
- **THEN** o elemento `<table>` tem classe `rebalance-table`
- **AND** as células de cabeçalho numérico têm classe `rebalance-table-th--num`
- **AND** as células de dados numéricos têm classe `rebalance-asset-cell--num`
- **AND** a célula de ação tem classe `rebalance-asset-cell--action`
- **AND** badges de ação têm classe `rebalance-action-badge--{buy|sell|hold}`

### Requirement: Coluna Ação renderiza badges traduzidos

O sistema SHALL renderizar a coluna Ação com badges no mesmo formato da página de produção: `Comprar` (badge verde), `Vender` (badge vermelho), `Manter` (badge neutro).

#### Scenario: Badge Comprar

- **WHEN** um ativo tem `action = "buy"`
- **THEN** a célula Ação mostra badge com texto "Comprar" e classe `rebalance-action-badge--buy`

#### Scenario: Badge Vender

- **WHEN** um ativo tem `action = "sell"`
- **THEN** a célula Ação mostra badge com texto "Vender" e classe `rebalance-action-badge--sell`

#### Scenario: Badge Manter

- **WHEN** um ativo tem `action = "hold"`
- **THEN** a célula Ação mostra badge com texto "Manter" e classe `rebalance-action-badge--hold`
