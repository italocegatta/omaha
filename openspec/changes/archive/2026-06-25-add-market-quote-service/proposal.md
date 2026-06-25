## Why

O rebalanceamento de carteira precisa de cotações atualizadas para calcular
quantas cotas comprar ou vender por ativo. Hoje, o único preço disponível vem
do CSV do broker (`Position.current_price`) — defasado a cada importação e
inexistente para ativos não cobertos pelo broker (ex: Avenue USD, US ETFs
na conta Avenue). Sem cotação live, o futuro otimizador não tem como operar.

A solução precisa coexistir com dois regimes: ativos negociáveis (Ações, FIIs,
ETFs, BDRs, Cripto, US stocks, FX) onde a cotação live agrega valor, e ativos
de renda fixa / caixa (CDB, RDB, Tesouro Direto, conta em dólar) onde a
cotação live não faz sentido — `Position.current_price` do broker é a fonte
autoritativa. O cache deve ser temporário (sobrevive ao reload do uvicorn,
expira por TTL) e atualizado por um gatilho explícito, não por timer
opaco, para que a futura funcionalidade de otimização controle quando
refrescar sem competir com a UI.

## What Changes

- Adiciona uma tabela `quotes` no schema (`symbol`, `price`, `currency`,
  `fetched_at`) para cachear cotações por símbolo, com TTL configurável
  via env var (espelha o padrão `PREVIEW_TTL_SECONDS`).
- Adiciona uma coluna `quote_kind` enum em `asset_classes` (`auto`,
  `manual`, `none`) para decidir se uma classe tem cotação live, é
  manual, ou usa o preço do broker.
- Adiciona o pacote `yfinance` como dependência runtime (em
  `pyproject.toml`).
- Adiciona uma interface `QuoteProvider` com implementação `YFinanceProvider`
  que cobre BR (`.SA`), US, FX (`BRL=X`), e crypto (`BTC-USD`).
- Adiciona um serviço `QuoteService` em background, iniciado no
  `@app.on_event("startup")`, que roda um loop de refresh com backoff
  exponencial e circuit-breaker para tolerar Yahoo intermitente
  (timeouts, 404s, rate limits) sem derrubar o servidor nem saturar
  o log.
- Adiciona um endpoint interno de gatilho `POST /api/quotes/refresh`
  (sem UI) que o futuro otimizador chamará para forçar refresh antes
  de calcular. O loop em background continua existindo; o gatilho é
  um caminho adicional de atualização.
- Adiciona uma rota de leitura `GET /api/quotes/{symbol}` e
  `GET /api/quotes?symbols=...` para consumidores internos (otimizador,
  futura UI). Não há rota de UI para cotação nesta mudança.
- Adiciona testes unitários e de integração para o adapter yfinance
  (com `yfinance` mockado), para o refresh loop (com ticker fictício
  intermitente), e para o endpoint de gatilho.

**Não inclui** (escopo de mudança futura):
- A UI que mostra cotação por ativo (escopo do S05 / dashboard).
- A funcionalidade de otimização / rebalanceamento em si — o gatilho
  exposto nesta mudança existe para que essa futura mudança o chame.
- Suporte a brapi / AwesomeAPI / outras fontes — fica atrás da
  interface `QuoteProvider` para troca futura sem refactor de schema.

## Capabilities

### New Capabilities

- `quote-cache`: tabela de cotações com TTL, modelo de leitura/escrita,
  e helper de freshness (`is_fresh`). É a única fonte de cotação live
  para o resto da aplicação.
- `quote-provider`: contrato `QuoteProvider` (interface) e a
  implementação `YFinanceProvider` que mapeia símbolos do omaha para
  tickers yfinance (`.SA`, `BRL=X`, `BTC-USD`, US direto). A interface
  permite trocar de provedor sem refactor de quem consome.
- `quote-refresh`: loop em background com resiliência a Yahoo
  intermitente (backoff exponencial, circuit breaker, refresh
  parcial) e o endpoint `POST /api/quotes/refresh` que o futuro
  otimizador usará como gatilho explícito para forçar refresh.
- `asset-class-quote-kind`: enum `quote_kind` em `asset_classes` e
  filtro do `QuoteService` para que apenas classes com `quote_kind =
  auto` tentem cotação live. `manual` e `none` continuam usando
  `Position.current_price` do broker.

### Modified Capabilities

- `import-position-totals`: nenhuma mudança de requisito. O
  `Position.current_price` continua sendo a fonte para ativos
  `quote_kind = none` ou `manual`. O cache de cotações é
  complementar, não substitui.
- `dashboard-inline-editing`: nenhuma mudança de requisito. O
  target % e a edição inline não mudam. A cotação live é exposta
  via nova rota mas não é consumida pela UI nesta mudança.

## Impact

- **Schema**: nova tabela `quotes` (Alembic revision). Nova coluna
  `asset_classes.quote_kind` (Alembic revision). Default seguro
  para a coluna: `none` (forçar opt-in explícito por classe via
  seed / UI).
- **Dependências**: `yfinance>=1.4` adicionado a
  `pyproject.toml` (runtime, não dev). Já temos `httpx` em dev, mas
  yfinance usa `requests` + `curl_cffi` internamente — sem novo
  requirement HTTP.
- **Startup**: novo `asyncio.create_task(...)` no `on_event("startup")`
  em `src/omaha/main.py`. O loop vive na event loop do uvicorn; o
  `yfinance` síncrono é chamado via `asyncio.to_thread`. O loop é
  cancelado no `on_event("shutdown")`.
- **CSV seed path**: a coluna `quote_kind` na classe precisa de um
  default na migration. As classes existentes viram `none`
  (conservador). O user pode flipar para `auto` no editor de classe
  ou diretamente no CSV (`data/seed/{profile}_classes.csv`).
- **Test marker rule** (`tests/conftest.py`): os novos testes do
  `yfinance` adapter (com mock) são unitários (`-m unit`); o teste
  do loop em background e do endpoint de gatilho são de integração
  (`-m integration`). Os novos prefixos `tests/test_quote_*.py`
  devem ser adicionados a `_INTEGRATION_PREFIXES`.
- **Operação**: Yahoo pode ficar fora do ar. O design assume isso:
  refresh parcial é sucesso; falha total não derruba o servidor;
  cache stale serve fallback. O log distingue `info: refreshed 35
  symbols`, `warn: 7 symbols failed`, `error: yfinance unreachable,
  circuit open for 5min`.
- **Sem UI nesta mudança**: rotas são internas (`/api/quotes/*`).
  Nenhuma alteração em `templates/dashboard.html` ou similar.
