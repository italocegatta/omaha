# asset-trade-flags

## Why

The CVXPY-based portfolio rebalance algorithm (Fase 2+ do plano
`.planning/REBALANCE_PLAN.md`) requer três campos por ativo que o
modelo `Asset` ainda não carrega:

- `buy_enabled[i]` — hard lock no solver; impede que a Fase 1/2
  aloque compras no ativo.
- `sell_enabled[i]` — hard lock no solver; impede que vendas
  drenem o ativo abaixo do target.
- `currency_code` — chave de resolução de cotação e (futuro)
  conversão USD→BRL na Fase 4.

Sem esses campos, o builder de `PortfolioSetup` (Gap E) não
consegue popular as colunas que o solver espera, e o rebalance
fica bloqueado na fundação.

Decisão paralela: importar um extrato da corretora (S04) não traz
informação de buy/sell/currency — o broker não publica. O modal de
review precisa expor os 3 campos com defaults para o usuário
ajustar antes do commit.

## What Changes

Adicionar 3 colunas ao `Asset` (`buy_enabled`, `sell_enabled`,
`currency_code`) + UI de toggle inline na tabela de ativos + 3
controles novos no modal de review do import + extensão do
`PATCH /api/assets/{id}` para aceitar as flags e a moeda + CSV
seed com header estendido.

Defaults (decisão owner 2026-06-26): `buy_enabled=True`,
`sell_enabled=True`, `currency_code="BRL"`. Inverte DD#3 do
plano original — opt-out > opt-in para reduzir atrito operacional
(48 cliques por rebalance seria inviável).

## Capabilities

### New Capabilities

- `asset-trade-flags`: campos por ativo que controlam quais
  operações o rebalance solver está autorizado a executar e em
  qual moeda o ativo é cotado. Defaults conservadores revertidos
  para liberais (`True/True/BRL`) por decisão de owner; toggle
  por ativo individual (sem bulk por classe).

### Modified Capabilities

- `import-modal`: 3 controles novos (toggle compra, toggle venda,
  select moeda) na review de auto-matched e unmatched, com
  defaults `True/True/BRL` que o usuário pode ajustar antes do
  commit.

## Impact

- **Modelo**: `src/omaha/models.py` ganha 3 colunas Mapped na
  classe `Asset`.
- **Migration nova**: `alembic/versions/0016_asset_trade_flags.py`
  (revisa `1c73065cff10`, head atual). Adiciona 3 colunas + CHECK
  constraint em `currency_code` via `batch_alter_table`.
- **CSV seed**: `data/seed/italo_assets.csv` + `ana_assets.csv`
  ganham 3 colunas no header (`buy_enabled`, `sell_enabled`,
  `currency_code`). Header legado vira `abort()` no parser.
- **Parser**: `scripts/seed_from_csv.py` estende `ASSET_HEADER`,
  `AssetRow` dataclass, e `load_assets()`.
- **Routes**: `src/omaha/routes/assets.py` — `POST /api/assets`
  aceita defaults opcionais, `PATCH /api/assets/{id}` aceita
  body com mix dos 4 campos (target_pct + 3 novos) com
  validação per-field.
- **Import routes**: `src/omaha/routes/imports.py`
  `_build_preview_response()` emite `buy_enabled`, `sell_enabled`,
  `currency_code` em cada `auto_matched`/`unmatched`; commit
  handler propaga para o `Asset` (auto-matched) ou usa no
  upsert (unmatched → create).
- **Import modal**: `src/omaha/templates/dashboard.html` ganha
  3 controles novos na review table; Alpine store
  `$store.importModal` estendido.
- **Dashboard tabela**: `src/omaha/templates/dashboard.html` ganha
  2 colunas novas (Compra / Venda) com toggle clicável por linha;
  badge de moeda na coluna Ativo ou nova coluna "Moeda".
- **Aggregates**: `portfolio_aggregates()` em
  `src/omaha/routes/pages.py` propaga os 3 campos no dict
  `class_data.assets` para que o template Jinja renderize.
- **Fixtures**: `tests/fixtures/tiny_portfolio.csv` (e qualquer
  outro CSV de asset usado por testes) precisa do header novo.
- **Tests novos**: `tests/test_assets_trade_flags.py` cobrindo
  migration + defaults + CHECK + PATCH/POST bodies + auth. Adicionar
  o prefixo a `_INTEGRATION_PREFIXES` em `tests/conftest.py` (regra
  AGENTS.md).
- **Tests atualizados**: `tests/test_assets_model.py` estende
  assertion de colunas; `tests/test_seed_from_csv.py` ganha
  fixtures e cenários para as 3 colunas; `tests/test_import_commit.py`
  e `tests/test_import_preview.py` ganham assertions dos 3 campos.
- **Doc**: `data/seed/README.md` documenta o header novo e a
  decisão de defaults.
- **Sem mudança** em `pyproject.toml` (CVXPY entra na Fase 4,
  fora do escopo desta change).
