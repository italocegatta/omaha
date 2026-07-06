## ADDED Requirements

### Requirement: Rentabilidade page exposes portfolio returns over fixed windows

O sistema MUST expor a página top-level `/rentabilidade` (autenticada)
que mostra o retorno do portfólio atual em **6 janelas fixas**
ancoradas em `now()`: 1M (mês corrente), 3M, 6M, 12M, YTD (1º de jan
até hoje), All-time (desde `min(imported_at)` do perfil).

Para cada janela o sistema MUST calcular e exibir:

- **`invested`**: soma cumulativa de `qty * avg_price` para posições
  cuja `Position.imported_at <= as_of` da janela (apenas posições
  ativas no corte).
- **`current`**: soma de `qty * quote_price(ativo, as_of)` usando a
  cotação aplicável na data de corte (cache de `Quote` com
  carry-forward de D-F03.2; fallback em `Position.current_price` se
  ativo nunca foi cotado).
- **`gain`**: `current - invested`.
- **`gain_pct`**: `gain / invested * 100` quando `invested > 0`;
  `null` quando `invested == 0` (sem divisão por zero).

A página MUST renderizar:

1. Hero card no topo reusando `patrimonio-portfolio-header`
   (Investido / Valor Atual / Ganho) com janela `all-time`.
2. Tabela "Por janela" listando as 6 janelas com colunas: Janela /
   Investido / Valor Atual / Ganho / %.
3. Tabela "Por classe (All-time)" listando cada `AssetClass` com
   Investido / Valor Atual / Ganho / %.
4. Tabela "Série mensal" com até 12 pontos mensais (default), colunas
   Data / Investido / Valor Atual / Ganho / %.

Página MUST ser acessível via a tab `Rentabilidade` em `base.html`
(tab nav criada em F02) e MUST respeitar `Cache-Control: no-store`
na resposta HTML autenticada (mesma convenção do resto da app).

#### Scenario: Perfil com posições calcula 6 janelas corretamente
- **GIVEN** perfil "Italo" com 6 classes, 12 ativos e 12 posições
  importadas em `imported_at = 2024-03-15` e cotações yfinance em
  cache para todos os ativos com `fetched_at` no mês corrente
- **WHEN** o operador logado acessa `GET /rentabilidade` autenticado
- **THEN** a página renderiza 200 com `Cache-Control: no-store`
- **AND** a tabela "Por janela" lista 6 linhas: 1M / 3M / 6M / 12M /
  YTD / All-time
- **AND** a linha "All-time" tem `as_of = 2024-03-15` (data do
  primeiro aporte) e valores consistentes com
  `sum(qty*avg_price)` / `sum(qty*current_price)` em `now()`
- **AND** cada linha numérica é formatada como moeda brasileira
  (`R$ 1.234,56`) sem casas decimais quando inteiro, com 2 casas
  quando fracionário

#### Scenario: Janela sem posições ativas retorna linha vazia
- **GIVEN** perfil "Ana" recém-criado sem nenhuma posição
  (`Position` rows inexistentes)
- **WHEN** operador acessa `GET /rentabilidade`
- **THEN** a tabela "Por janela" renderiza 6 linhas todas com
  `invested = 0`, `current = 0`, `gain = 0`, `gain_pct = null`
- **AND** a tabela "Por classe" renderiza apenas a mensagem
  "Nenhuma classe cadastrada"

#### Scenario: Série mensal cobre os 12 meses anteriores
- **GIVEN** perfil com `imported_at = 2024-06-15` e cotações em
  cache cobrindo pelo menos os últimos 6 meses
- **WHEN** operador chama `GET /api/rentabilidade/series` autenticado
- **THEN** o endpoint retorna JSON com `points: [12 entries]` para
  os 12 meses mais recentes (incluindo o mês atual)
- **AND** cada entry tem shape
  `{date: "YYYY-MM-01", invested, current, gain, gain_pct, as_of}`
- **AND** `gain_pct` é `null` nas datas anteriores a `imported_at`
- **AND** `invested` é 0 nas datas anteriores a `imported_at` mesmo
  se houve cotações para outros perfis

### Requirement: Rentabilidade endpoints serve summary and series JSON

O sistema MUST expor dois endpoints JSON autenticados para alimentar
a página `/rentabilidade`:

- `GET /api/rentabilidade/summary` retorna
  `{as_of: ISO, windows: [...6 janelas...], classes: [...per
  classe...], quote_stale_assets: [asset_id, ...]}`.
- `GET /api/rentabilidade/series?window=<int|all>` (default `12`)
  retorna
  `{as_of: ISO, points: [{date, invested, current, gain,
  gain_pct}, ...]}`.

Profile resolvido a partir do `active_profile` da sessão (NÃO do
querystring), mesma convenção de `/api/rebalance`. Mutações não
existem (sem POST/PATCH/DELETE nessa rota).

Refresh de cotação reusa `POST /api/quotes/refresh` existente (sem
novo endpoint). Botão "Atualizar cotações" na página MUST chamar o
serviço de cotação e re-renderizar ambas as tabelas via Alpine AJAX.

#### Scenario: Summary retorna janelas + classes + stale flag
- **GIVEN** perfil autenticado com 6 classes e cotações em cache
- **WHEN** operador chama `GET /api/rentabilidade/summary`
- **THEN** resposta 200 com JSON contendo `as_of`, `windows` (length
  6), `classes` (length 6) e `quote_stale_assets` (array)
- **AND** `windows[*]` tem shape
  `{label: "1M|3M|6M|12M|YTD|All", invested, current, gain,
  gain_pct}`
- **AND** `classes[*]` tem shape
  `{class_id: int, name: str, invested, current, gain, gain_pct}`
- **AND** ativos com `Quote.fetched_at` > 30 dias atrás aparecem em
  `quote_stale_assets`

#### Scenario: Series com window=12 retorna 12 pontos mensais
- **GIVEN** perfil autenticado com cotações históricas dos últimos 12
  meses
- **WHEN** operador chama `GET /api/rentabilidade/series?window=12`
- **THEN** resposta 200 com `points` de length 12
- **AND** o primeiro ponto tem `date` 11 meses antes do mês atual
- **AND** o último ponto tem `date` no primeiro dia do mês atual

#### Scenario: Series sem autenticação retorna 401
- **WHEN** cliente chama `GET /api/rentabilidade/summary` sem cookie
  de sessão
- **THEN** resposta 401 (gate `require_user` aplicado)

#### Scenario: Series com window=all inclui todo o histórico
- **GIVEN** perfil com `imported_at = 2020-01-15` e cotações cobrindo
  2020-2025
- **WHEN** operador chama `GET /api/rentabilidade/series?window=all`
- **THEN** resposta 200 com `points` incluindo 60+ entries mensais
  desde jan/2020 até o mês atual
- **AND** todos os pontos anteriores a `2020-01-15` têm
  `invested = 0` e `gain_pct = null`

### Requirement: Rentabilidade page honors household read-only mode

The system MUST calcular janelas + classes sobre a agregação
**cross-User** full-join por nome quando o modo Família está
ativo (querystring `?view=household` ou sentinel bind via F07),
usando a mesma invariante de F06 / `family_aggregates` em
`routes/pages.py`.

The system MUST omitir a coluna `target_pct` em qualquer tabela
quando `view == "family"` (D-F06.3 — alocação-alvo cross-User é
ambígua).

The system MUST rejeitar toda mutação via 409
`household_read_only` quando o gate `require_profile_writable`
disparar; mutações inexistentes nesta página não exigem novos
endpoints.

The system MUST mostrar banner read-only quando o modo Família
está ativo (mesmo banner já existente em `patrimonio.html` para
F06).

#### Scenario: Modo Família agrega cross-User
- **GIVEN** Família (sentinel bind) ativa com 2 perfis reais (Italo +
  Ana) cada um com classes "Renda Fixa" próprias e ativos distintos
- **WHEN** operador chama `GET /api/rentabilidade/summary?view=household`
- **THEN** resposta 200 com `classes[*]` length 6 (não 12) — "Renda
  Fixa" colapsa em 1 linha somando investido/valor de ambos
- **AND** os valores de "Renda Fixa" são a soma das duas classes (um
  por perfil)
- **AND** nenhum item de `classes[*]` tem campo `target_pct`

#### Scenario: Modo Família omite target_pct em todas as tabelas
- **WHEN** operador renderiza `/rentabilidade?view=household` no
  template
- **THEN** a tabela "Por classe" renderiza sem coluna `Alvo %`
- **AND** a tabela "Por janela" renderiza sem coluna `Alvo %`
- **AND** a tabela "Série mensal" renderiza sem coluna `Alvo %`
- **AND** banner read-only aparece no topo com texto PT-BR
  informativo

### Requirement: Carry-forward quote lookup avoids zero-fill in series

The system MUST usar a **última cotação conhecida** (data anterior
mais próxima com `Quote.fetched_at <= as_of`) quando uma janela de
tempo (ou ponto da série mensal) não tem cotação para um dado ativo
na data de corte.

The system MUST listar o identificador do ativo em
`quote_stale_assets` quando o carry-forward usou cotação com mais de
30 dias de defasagem em relação à data de corte da janela.

The system MUST usar `Position.current_price` como último valor
conhecido (caso degenerado de `quote_kind='manual'`) quando a
posição tem `Position.current_price` setada mas nenhuma `Quote` row.

#### Scenario: Ativo sem quote no mês usa última cotação conhecida
- **GIVEN** perfil com ativo "PETR4" com Quote em
  `fetched_at = 2024-09-15` e nenhuma `Quote` row posterior
- **WHEN** operador chama `GET /api/rentabilidade/series?window=12`
  com `now()` em 2025-08
- **THEN** todos os pontos mensais de 2025-01 a 2025-08 para PETR4
  usam a cotação de 2024-09-15 (carry-forward)
- **AND** `asset_id` de PETR4 aparece em `quote_stale_assets` na
  resposta do endpoint

#### Scenario: Ativo com quote atualizada recentemente não é stale
- **GIVEN** perfil com ativo "VALE3" com Quote em
  `fetched_at = 2025-08-01` (5 dias atrás)
- **WHEN** operador chama o endpoint `summary` com `now()` em
  2025-08-06
- **THEN** `asset_id` de VALE3 NÃO aparece em `quote_stale_assets`

#### Scenario: Posição com quote_kind manual entra como current_price
- **GIVEN** perfil com ativo "Imóvel X" com `Quote` rows vazias e
  `Position.current_price = 800_000.00`
- **WHEN** operador chama `summary`
- **THEN** o valor de mercado de "Imóvel X" usa `current_price`
- **AND** o ativo NÃO aparece em `quote_stale_assets` (não é stale;
  é manual por design)
