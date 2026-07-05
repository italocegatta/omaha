# f03-rentabilidade-page

## Why

A página `/rentabilidade` foi introduzida em F02 como stub "Em construção"
para fechar a top-nav de 4 tabs. Hoje não há nenhuma superfície na app que
mostre **evolução temporal** do portfólio: Patrimônio mostra o instantâneo
atual, Rebalanceamento mostra desvio em relação ao alvo, Import traz CSV
novo. O owner precisa enxergar **quanto rendeu** num horizonte (1M/3M/6M
/12M/YTD/All) e **como variou** mês a mês desde o primeiro aporte
(grão mensal, simples).

A agregação é viável sem dados novos: `Position.imported_at` (quando o
ativo entrou no portfólio via CSV) + `Quote.fetched_at`/`price` (cache
de cotação com TTL; histórico acumulado desde o primeiro refresh)
permitem reconstruir o valor investido cumulativo e o valor de mercado
ao longo do tempo. Cobertura de quote history é parcial (só datas em que
o refresh rodou) — o carry-forward da última cotação conhecida cobre os
buracos sem introduzir dados sintéticos.

## What Changes

- Substituir `templates/rentabilidade.html` (atualmente stub F02) por
  página real que renderiza tabela **Por janela** (1M / 3M / 6M / 12M /
  YTD / All) + tabela **Por classe (All-time)** + série mensal resumida
  em `<table>`.
- Adicionar handler `GET /rentabilidade` em
  `src/omaha/routes/pages.py` substituindo o stub atual; reusa o
  pipeline de `require_user` + `require_active_profile` +
  `require_profile_writable` (read-only no modo Família) já estabelecido
  por F02/F06/F07.
- Adicionar `src/omaha/routes/rentabilidade.py` com dois endpoints:
  - `GET /api/rentabilidade/series?profile=<id>&window=<months|all>`
    → `{points: [{date, invested, current_value, gain, gain_pct}, …]}`,
    grão mensal, do `min(imported_at)` até `now()`.
  - `GET /api/rentabilidade/summary?profile=<id>`
    → `{windows: [{label, invested, current, gain, gain_pct}], classes:
    [{class_id, name, invested, current, gain, gain_pct}], as_of: ISO}`
    para popular as tabelas.
- Modo Família (querystring `?view=household` ou sentinel Família
  bind via F07) calcula série + summary sobre os agregados cross-User
  full-join por `name` (mesmos invariantes de F06); `target_pct`
  continua suprimido (alocação-alvo cross-User é ambígua — D-F06.3).
- Sem biblioteca de chart; série renderiza como `<table>` simples de
  pontos mensais (PRD §1.5: "página pode ser pequena").
- Cobertura de refresh de cotação: se algum mês não tem quote, usar a
  última cotação conhecida (carry-forward); documentar como decisão
  D-F03.2.

## Capabilities

### New Capabilities
- `rentabilidade`: contrato da página `/rentabilidade` + endpoints
  `/api/rentabilidade/{series,summary}`. Define: (a) shape do payload,
  (b) janelas suportadas (1M/3M/6M/12M/YTD/All), (c) granularidade da
  série (mensal), (d) comportamento do modo Família,
  (e) comportamento do carry-forward de quote, (f) gate
  `require_profile_writable` aplicado.

### Modified Capabilities
- `rebalance-data-bridges`: se durante o apply houver reaproveitamento de
  agregação de posições (ex.: helper `positions_by_class` exportado), o
  delta descreve o que mudou e por quê. Mantém wire shape existente.
  Provavelmente não é necessário (verificar no design).

## Impact

- **Rotas:** `src/omaha/routes/pages.py` (handler da página),
  `src/omaha/routes/rentabilidade.py` (novo), nenhum endpoint existente
  alterado.
- **Templates:** `src/omaha/templates/rentabilidade.html` (substitui
  stub), `src/omaha/templates/base.html` (sem mudança — tab nav já
  existe e já marca `/rentabilidade` como ativa).
- **CSS:** `src/omaha/static/app.css` (regras `.rentabilidade-hero`,
  `.rentabilidade-windows-table`, `.rentabilidade-classes-table`,
  `.rentabilidade-series-table`); reusa tokens existentes
  (`--accent`, `--ink`, `--bg`, `--paper`); sem adição de token novo.
- **Modelos:** zero mudança em `src/omaha/models.py`. A página lê
  `Position.qty/avg_price/imported_at` e `Quote.fetched_at/price`.
- **Tests:**
  - `tests/test_rentabilidade_summary.py` (novo, unit): cenãrios de
    agregação de summary por janela e classe a partir de dados
    sintéticos em memória (sem DB).
  - `tests/test_rentabilidade_series.py` (novo, unit): cenários de
    reconstrução da série mensal via `imported_at` cumulativo +
    carry-forward de quote.
  - `tests/integration/test_rentabilidade_route.py` (novo): GET
    `/rentabilidade` autenticado renderiza as 3 tabelas; modo Família
    renderiza agregação cross-User; mutações em modo Família retornam
    409 `household_read_only` (gate reusado, sem retrabalho).
  - `tests/bdd/features/rentabilidade.feature` (novo): cenário
    "Operador vê rentabilidade por janela e por classe" + cenário
    "Modo Família agrega rentabilidade cross-User".
  - `tests/conftest.py`: adicionar prefixos `test_rentabilidade_*` em
    `_INTEGRATION_PREFIXES` (regra §4.6 / AGENTS.md).
- **Templates auxiliares:** nenhum. Sem partial novo.
- **Domínio crítico:** **não toca solver CVXPY nem provider de cotação
  yfinance**. Lê cache de `Quote` mas não chama o provider em runtime.
  Cap de Applying = 1, mas sem contenção (F06/F07/R02 etc. já
  archived).

## Non-goals

- Sem gráfico visual (line chart / candlestick). Decisão deliberada —
  PRD §1.5 + §4.10 orientam minimalismo. Tabela mensal basta para a
  primeira versão; chart vira slice dedicada se owner pedir (F-slot
  futuro).
- Sem snapshot diário explícito de portfolio. A reconstrução é
  derivada dos dados existentes (`Position` + `Quote` history); se a
  densidade de quote se mostrar insuficiente para uma janela útil
  (>30% dos meses sem quote), isso vira problema separado de dados
  (não desta fatia).
- Sem comparação contra índice (CDI, Ibovespa, etc.).
- Sem cálculo de TWR (time-weighted return) — apenas retorno
  absoluto nominal e variação percentual simples. TWR/MWR é domínio
  que pode entrar em fatia futura de qualidade.
- Sem exportar CSV da série.
- Sem real-time refresh automático; refresh manual via botão "Atualizar
  cotações" reusando `QuoteService` se/ quando owner clicar.

## Validation

- `task test-unit` verde, incluindo os 2 novos arquivos.
- `task test-integration` verde com prefixos adicionados em
  `_INTEGRATION_PREFIXES`.
- `task test-bdd` verde; cenários novos em
  `tests/bdd/features/rentabilidade.feature` passam.
- `task test-e2e` verde para smoke da página (sem novos selectors de
  chart porque não há chart).
- `openspec validate f03-rentabilidade-page` → `valid: true`.
- Smoke via `refresh-for-test`: abrir `/rentabilidade` no LAN URL,
  conferir 3 seções (hero, janelas, classes) e que modo Família
  renderiza o agregado cross-User.
