## 1. Migration Alembic (`alembic/versions/0016_add_position_totals.py`)

- [x] 1.1 `src/omaha/models.py:283-295` — adicionar colunas `total_invested` e `total_current` (`Numeric(18, 4)`, nullable=True, sem default) ao model `Position`. Manter colunas legadas (`qty`, `avg_price`, `current_price`) intactas.
- [x] 1.2 `alembic/versions/0016_add_position_totals.py` — migration Alembic com `op.add_column("positions", sa.Column("total_invested", sa.Numeric(18, 4), nullable=True))` e idem para `total_current`. Downgrade remove as duas colunas.
- [x] 1.3 Rodar `uv run task db-migrate` — aplica a migration contra `data/portfolio.db`. Verificar via `sqlite3 data/portfolio.db ".schema positions"` que as 2 colunas novas existem, nullable, sem default.

## 2. Parser (`src/omaha/csv_import.py`)

- [x] 2.1 `src/omaha/csv_import.py:64-90` (label constants) — adicionar `_KNOWN_TOTAL_INVESTED_LABELS = ("total investido", "total aplicado", "valor aplicado", "valor investido")` e `_KNOWN_TOTAL_CURRENT_LABELS = ("total atual", "valor atual", "saldo atual", "valor de mercado")`.
- [x] 2.2 `src/omaha/csv_import.py:110-130` (dataclass `RawPosition`) — adicionar `total_invested: Decimal | None = None` e `total_current: Decimal | None = None`.
- [x] 2.3 `src/omaha/csv_import.py:133-150` (dataclass `ColumnMap`) — adicionar `total_invested: int | None = None` e `total_current: int | None = None`.
- [x] 2.4 `src/omaha/csv_import.py:480-510` (`_detect_columns`) — adicionar detecção dos dois novos labels via mesmo padrão de substring match usado em `_KNOWN_CUR_LABELS`. Set `ColumnMap.total_invested` / `total_current` com o índice da coluna encontrada, ou `None` se nenhum label match.
- [x] 2.5 `src/omaha/csv_import.py:337-410` (`_parse_data_row`) — quando `col_map.total_invested` / `total_current` não são None, parsear a célula via `_parse_brazilian_number` e atribuir ao `RawPosition`. Quando são None, deixar os campos como None (sem fallback `qty × price`).

## 3. Commit endpoint (`src/omaha/routes/imports.py`)

- [x] 3.1 `src/omaha/routes/imports.py:502-510` (UPSERT SQL no endpoint `commit_import`) — adicionar `total_invested` e `total_current` à lista de colunas do INSERT e ao `ON CONFLICT ... DO UPDATE SET`. Os parâmetros `:total_invested` / `:total_current` recebem `str(rp.total_invested)` ou `None` (passa SQL NULL quando RawPosition tem None).
- [x] 3.2 `src/omaha/routes/imports.py:76-95` (`_raw_to_dict` e `_dict_to_raw`) — incluir `total_invested` / `total_current` (como string ou None) na serialização round-trip do `raw_json` para o `ImportPreview`.

## 4. Dashboard calc (`src/omaha/routes/pages.py`)

- [x] 4.1 `src/omaha/routes/pages.py:201-216` — substituir `asset_invested += qty * avg` e `asset_current += qty * cur` por `asset_invested += pos.total_invested or ZERO` e `asset_current += pos.total_current or ZERO`. **Não** multiplicar nada. Linha com `total_invested IS NULL` contribui `0`.

## 5. Template (`src/omaha/templates/dashboard.html`)

- [x] 5.1 `src/omaha/templates/dashboard.html:631` e `:686` — substituir `formatBRL(Number(row.qty) * Number(row.current_price), 0)` por `formatBRL(row.current_value, 0)` e idem para o `row.invested`. Remover a multiplicação JS; backend já entrega o valor pronto.

## 6. Testes

- [x] 6.1 `tests/test_csv_import.py` — adicionar `test_total_invested_and_current_parsed` cobrindo: (a) linha com `R$ 8.658,02` → `Decimal("8658.02")`; (b) linha com aspas → `Decimal("8153.44")`; (c) linha sem coluna → `None` (sem fallback).
- [x] 6.2 `tests/test_csv_import.py` — adicionar `test_csv_without_total_columns` cobrindo CSV mínimo (sem `Total investido` / `Total atual` no header): todos os `RawPosition.total_invested` / `total_current` são `None`.
- [x] 6.3 `tests/test_real_csv_flow.py::TestParseRealCsv` — adicionar método `test_parse_real_csv_total_columns_populated`: para os 48 ativos do fixture `tests/posicao_italo.csv`, assert que `RawPosition.total_invested` e `total_current` são `Decimal` não-None e que o `sum(rp.total_invested for rp in result)` é próximo de `Decimal("1017614.61")` (footer do CSV, dentro de tolerância de R$ 0,01).
- [x] 6.4 `tests/test_real_csv_flow.py` — adicionar `test_portfolio_total_matches_csv_footer`: rodar end-to-end (preview + commit) e assert que o `portfolio.total_invested` e `portfolio.current_value` retornados pelo dashboard API são `Decimal("1017614.61")` e `Decimal("1101357.67")` byte-a-byte.

## 7. Validação + delivery

- [x] 7.1 `openspec validate broker-csv-import-totals --json` — `valid: true, issues: []`.
- [x] 7.2 `uv run task lint` — verde.
- [x] 7.3 `uv run task test-unit` — verde 150/150.
- [x] 7.4 `uv run task test-integration` — verde 229/229.
- [x] 7.5 `uv run task test-e2e` — 30/35 passed, 5 pre-existing failures (``profile-name`` selector never existed in template — not a regression).
- [x] 7.6 `uv run task db-reset` — dev DB populated: Italo=6 classes/48 assets/47 positions, Ana=6/46/43, all 90 positions with totals.
- [x] 7.7 Manual smoke: `uv run task serve`, then import `tests/posicao_italo.csv` via dashboard modal; verified footer matches CSV.
- [x] 7.8 Report — done.
