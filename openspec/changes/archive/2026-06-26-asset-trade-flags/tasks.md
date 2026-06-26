# Tasks

Ordem de execução reflete dependências: schema → modelo → CSV →
routes → UI → tests → fixtures → doc. Cada task é verificável
isoladamente.

## 1. Migration Alembic

- [x] 1.1 Criar `alembic/versions/0016_asset_trade_flags.py`
      com `revision="0016_asset_trade_flags"`,
      `down_revision="1c73065cff10"`, docstring seção
      Schema/Why/Downgrade (estilo 0014).
- [x] 1.2 `upgrade()`: `batch_alter_table("assets")` +
      `add_column(buy_enabled Boolean NOT NULL,
      server_default="1")` + `add_column(sell_enabled Boolean
      NOT NULL, server_default="1")` + `add_column(currency_code
      String(8) NOT NULL, server_default="BRL")` +
      `create_check_constraint("ck_asset_currency_code",
      "currency_code IN ('BRL', 'USD')")`.
- [x] 1.3 `downgrade()`: drop CHECK → drop 3 colunas (ordem
      reversa).
- [x] 1.4 Verificar `uv run alembic upgrade head` + `alembic
      downgrade -1` em DB limpo (round-trip).

## 2. Modelo ORM

- [x] 2.1 `src/omaha/models.py:183-247`: adicionar 3 colunas
      Mapped à classe `Asset`:
      `buy_enabled: Mapped[bool]` (default True),
      `sell_enabled: Mapped[bool]` (default True),
      `currency_code: Mapped[str]` (default "BRL",
      `mapped_column(String(8), nullable=False,
      server_default="BRL")`).
- [x] 2.2 Atualizar docstring de `Asset` mencionando Fase 1 do
      rebalance + defaults + CHECK.

## 3. CSV Seed — Header + Dataclass + Parser

- [x] 3.1 `scripts/seed_from_csv.py:59`: estender
      `ASSET_HEADER = ("class_name", "name", "target_pct",
      "display_order", "buy_enabled", "sell_enabled",
      "currency_code")`.
- [x] 3.2 Estender `AssetRow` dataclass (linha 79-86) com 3
      campos novos.
- [x] 3.3 `load_assets()` (linha 173-207): parsear `_bool`
      (aceita "true"/"false"/"1"/"0"/"" → bool) e validar
      `currency_code` ∈ `{"BRL", "USD"}` se presente (no v2
      header legacy é hard fail, mas parser precisa estar
      pronto pro header novo).
- [x] 3.4 `_wipe_profile` / `run_reset` (linha 372-431): passar
      `buy_enabled=a.buy_enabled`, etc., ao `Asset(...)`.
- [x] 3.5 `run_upsert` (linha 511-540): detectar diff nos 3
      campos e fazer update; imprimir "updated: {class}/{name}
      buy=X sell=Y cur=Z" se mudou.
- [x] 3.6 `run_diff` (linha 674-705): emitir nas linhas
      "would-update" se algum dos 3 mudou.

## 4. CSV Seed — Arquivos de dados

- [x] 4.1 `data/seed/italo_assets.csv`: adicionar 3 colunas no
      header. Preencher por linha:
      - Herdados (RDB/CDB/Tesouro Selic/IPCA/Renda+): True, True, BRL
      - FII/Ações: True, True, BRL
      - IVVB11/HTEK11/NUCL11: True, True, BRL (BDR cotado em R$)
      - IAU/IVV/QQQ/SMH/TFLO/VNQ/VT: True, True, USD (NYSE/Nasdaq ETFs)
      - BTC: True, True, BRL
      - (owner decision after delivery: NYSE/Nasdaq-listed ETFs →
        USD mesmo quando comprados via Avenue; o design.md original
        marcava tudo BRL, mas o solver Fase 2+ precisa da moeda
        subjacente, não da moeda de settlement)
- [x] 4.2 `data/seed/ana_assets.csv`: idem.
- [x] 4.3 `data/seed/README.md`: atualizar linha 22 (header
      table) + nota sobre defaults + nota sobre hard fail de
      header legacy.

## 5. Routes — Asset CRUD

- [x] 5.1 `src/omaha/routes/assets.py:206-317`
      `post_api_asset`: aceitar `buy_enabled`, `sell_enabled`,
      `currency_code` opcionais no body. Defaults: True, True,
      "BRL". Validar `currency_code` se presente.
- [x] 5.2 `src/omaha/routes/assets.py:320-382`
      `patch_asset`: aceitar body com mix dos 4 campos
      (`target_pct`, `buy_enabled`, `sell_enabled`,
      `currency_code`). Validação per-field. Body vazio → 422.
- [x] 5.3 Adicionar helpers `_parse_bool` e `_parse_currency`
      (estilo `_parse_pct`).
- [x] 5.4 `src/omaha/routes/assets.py:102-203` form-encoded
      `POST /assets` (legacy): aceitar form fields
      `buy_enabled`, `sell_enabled`, `currency_code` com
      defaults True/True/BRL.

## 6. Routes — Import preview/commit

- [x] 6.1 `src/omaha/routes/imports.py:_build_preview_response`
      (linha 373+): incluir `buy_enabled`, `sell_enabled`,
      `currency_code` em cada item de `auto_matched` e
      `unmatched`. Para auto-matched, ler do `Asset` atual.
      Para unmatched, defaults True/True/BRL.
- [x] 6.2 `src/omaha/routes/imports.py` commit handler:
      propagar os 3 campos no upsert (auto-matched →
      `Asset.buy_enabled = X`; unmatched → `Asset(...
      buy_enabled=X, sell_enabled=Y, currency_code=Z)`).
- [x] 6.3 `AssignmentItem` / `CommitRequest` Pydantic
      (imports.py:347+): adicionar 3 campos opcionais.
- [x] 6.4 Validar `currency_code` no commit (rejeitar != BRL/USD
      com 422).

## 7. Aggregates — Dashboard data

- [x] 7.1 `src/omaha/routes/pages.py:163-323`
      `portfolio_aggregates()`: no dict de cada asset
      (linha 217 do template: `class_data.assets.append(...)`),
      incluir `buy_enabled`, `sell_enabled`, `currency_code`.

## 8. UI — Dashboard tabela

- [x] 8.1 `src/omaha/templates/dashboard.html:187-330`: adicionar
      2 colunas novas no `<thead>` da tabela de ativos:
      "Compra", "Venda". Adicionar badge de moeda na linha
      (pode ser na coluna Ativo ou nova coluna "Moeda" —
      decidir durante implementação).
- [x] 8.2 Para cada asset row (linha 214-329): toggle clicável
      por linha. Click → PATCH `/api/assets/{id}` com o campo
      alterado. Visual: badge verde (liberado) / cinza (bloqueado).
- [x] 8.3 Estado durante PATCH em flight: toggle disabled
      (não optimística). Re-fetch via Alpine reatividade após
      200.
- [x] 8.4 Alpine store: estender objeto `a` no store do
      dashboard com `buy_enabled`/`sell_enabled`/`currency_code`.

## 9. UI — Import modal

- [x] 9.1 `src/omaha/templates/dashboard.html:600-700` (modal
      de review): adicionar 3 colunas na review table
      (auto-matched + unmatched).
- [x] 9.2 Toggle "Compra" + toggle "Venda" + select "Moeda"
      por linha.
- [x] 9.3 Alpine store `$store.importModal.assignments`: cada
      item ganha `buy_enabled`, `sell_enabled`, `currency_code`.
      Default no open: puxar do asset atual (auto-matched) ou
      True/True/BRL (unmatched).
- [x] 9.4 Bind: select de moeda segue padrão `x-init $nextTick`
      + `x-effect` (regra AGENTS.md Alpine binding gotcha).
- [x] 9.5 Submit do commit: enviar os 3 campos junto com
      `asset_id` / `class_id` / `qty` / etc.

## 10. Tests — Migration + Model

- [x] 10.1 Novo arquivo `tests/test_assets_trade_flags.py`
      (integração). Adicionar path a `_INTEGRATION_PREFIXES`
      em `tests/conftest.py:152-183` (regra AGENTS.md).
- [x] 10.2 Test: `alembic upgrade head` adiciona 3 colunas com
      defaults corretos.
- [x] 10.3 Test: row pré-existente lê `True/True/BRL` após
      upgrade.
- [x] 10.4 Test: insert com `currency_code="EUR"` viola CHECK
      → `IntegrityError`.
- [x] 10.5 Test: `Asset()` com defaults omitidos lê
      `True/True/BRL`.
- [x] 10.6 Test: `Asset(buy_enabled=False, ...)` aceita
      override explícito.

## 11. Tests — Routes

- [x] 11.1 Em `tests/test_assets_trade_flags.py`:
      - PATCH `{"buy_enabled": false}` → 200, persiste.
      - PATCH `{"currency_code": "EUR"}` → 422.
      - PATCH `{"target_pct": "50", "buy_enabled": false}` →
        200, ambos persistem.
      - PATCH body vazio → 422.
      - POST sem `buy_enabled` → 201, asset criado com
        `buy_enabled=True`.
      - POST com `currency_code="USD"` → 201, asset criado
        com `currency_code="USD"`.
      - Cross-profile id → 404.

## 12. Tests — Seed CSV

- [x] 12.1 Atualizar `tests/fixtures/tiny_portfolio.csv` (e
      qualquer outro CSV de asset em tests/fixtures/) com
      header novo + 3 colunas.
- [x] 12.2 `tests/test_seed_from_csv.py`: fixtures inline
      ganham header novo. Atualizar strings literais.
- [x] 12.3 Test: CSV com header legado (4 colunas) → `abort`
      com exit code 1.
- [x] 12.4 Test: CSV com `currency_code="EUR"` → `abort`.
- [x] 12.5 Test: `run_reset` popula as 3 colunas a partir do
      CSV.
- [x] 12.6 Test: `run_upsert` detecta diff nos 3 campos.
- [x] 12.7 Test: `run_diff` emite `would-update` quando flag/
      currency muda.

## 13. Tests — Import

- [x] 13.1 `tests/test_import_preview.py`: assertion dos 3
      campos em cada item de `auto_matched`/`unmatched`. Para
      auto-matched, valor é o do asset atual.
- [x] 13.2 `tests/test_import_commit.py`: commit propaga os 3
      campos (auto-matched → update do asset; unmatched →
      create com defaults).
- [x] 13.3 Test: commit rejeita `currency_code="EUR"` no body
      com 422.

## 14. Tests — Update existentes

- [x] 14.1 `tests/test_assets_model.py`: estender assertion de
      colunas pra incluir `buy_enabled`, `sell_enabled`,
      `currency_code`.
- [x] 14.2 `tests/test_db_reset_both_profiles.py`: rodar
      `db-reset` e verificar row counts dos 3 campos (todos
      True/True/BRL).
- [x] 14.3 `tests/test_assets_e2e.py`: e2e do toggle inline
      (Playwright). Clicar toggle → PATCH → estado visível.
- [x] 14.4 Auditar `tests/test_assets_post.py` e
      `tests/test_assets_patch_legacy.py`: garantir que nenhum
      teste assume defaults antigos.

## 15. Doc + Smoke

- [x] 15.1 `data/seed/README.md`: atualizar linha 22 (header
      table) + nota sobre defaults + nota sobre hard fail.
- [x] 15.2 Smoke: `uv run task db-migrate` em DB limpo → 0
      erros.
- [x] 15.3 Smoke: `uv run task db-reset` → CSV novo carrega
      sem erros → 48 assets Italo + 46 assets Ana.
- [x] 15.4 Smoke: `uv run task db-seed-diff` → sem diff
      (idempotente).
- [x] 15.5 Smoke: `uv run task check` (lint + test-unit)
      passa.
- [x] 15.6 Smoke: `uv run task test-integration` passa.
- [x] 15.7 Smoke: `uv run task test-file
      tests/test_assets_trade_flags.py` passa.
