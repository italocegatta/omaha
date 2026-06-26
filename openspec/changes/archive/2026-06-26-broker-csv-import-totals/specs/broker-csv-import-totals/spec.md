# broker-csv-import-totals Specification

## ADDED Requirements

### Requirement: Parser extrai `Total investido` e `Total atual` do CSV

A função `parse_positions` em `src/omaha/csv_import.py` MUST extrair
os valores das colunas `Total investido` e `Total atual` quando
presentes no CSV, populando `RawPosition.total_invested` e
`RawPosition.total_current` como `Decimal`. Quando a coluna não
está presente no header, os campos MUST ser `None` (sem cálculo
interno, sem fallback).

#### Scenario: linha com Total investido e Total atual em formato BR

- **WHEN** CSV contém linha `VT,10.9,...,R$ 8153.44,...,R$ 8658.02`
- **THEN** `RawPosition.total_invested == Decimal("8153.44")` e `RawPosition.total_current == Decimal("8658.02")`

#### Scenario: linha com prefixo `R$` e aspas

- **WHEN** CSV contém linha `"VT","10,9",...,"R$ 8.153,44",...,"R$ 8.658,02"`
- **THEN** `RawPosition.total_invested == Decimal("8153.44")` e `RawPosition.total_current == Decimal("8658.02")`

#### Scenario: CSV sem coluna de total

- **WHEN** CSV não tem colunas `Total investido` / `Total atual` no header
- **THEN** `RawPosition.total_invested is None` e `RawPosition.total_current is None` (sem fallback para cálculo)

#### Scenario: label alternativo `Total aplicado`

- **WHEN** CSV usa `Total aplicado` no header em vez de `Total investido`
- **THEN** `_detect_columns` mapeia a coluna corretamente e `RawPosition.total_invested` é populado

### Requirement: Commit endpoint persiste `total_invested` e `total_current` na tabela positions

O endpoint `POST /api/import/commit` MUST gravar os valores de
`RawPosition.total_invested` e `RawPosition.total_current` nas
respectivas colunas `positions.total_invested` e
`positions.total_current` (Numeric 18,4 nullable). Quando o valor é
`None`, a coluna gravada MUST ser SQL `NULL`.

#### Scenario: commit com totais presentes

- **WHEN** `RawPosition.total_invested = Decimal("8153.44")` e `total_current = Decimal("8658.02")`
- **THEN** a linha em `positions` tem `total_invested = 8153.44` e `total_current = 8658.02`

#### Scenario: commit sem totais (CSV de corretora que não publica)

- **WHEN** `RawPosition.total_invested = None` e `total_current = None`
- **THEN** a linha em `positions` tem `total_invested IS NULL` e `total_current IS NULL`

#### Scenario: re-import sobrescreve totais via ON CONFLICT

- **WHEN** segunda chamada a `/api/import/commit` para o mesmo `(asset_id, broker_ticker)` com totais diferentes
- **THEN** a linha em `positions` tem os novos `total_invested` / `total_current` (UPSERT idempotente)

### Requirement: Dashboard exibe totais diretamente do CSV sem multiplicação

A view `routes/pages.py` MUST calcular `invested` e `current_value`
por asset somando `pos.total_invested` e `pos.total_current`
diretamente. Posição com `total_invested = NULL` ou `total_current =
NULL` MUST contribuir `Decimal('0')` para a soma. **Nenhuma
multiplicação `qty × price` em nenhuma camada** (parser, commit,
dashboard calc, template).

#### Scenario: portfolio total confere com footer do CSV byte-a-byte

- **WHEN** `parse_positions` é chamado sobre `tests/posicao_italo.csv` e o resultado passa por `/api/import/commit`
- **THEN** `portfolio.total_invested == Decimal("1017614.61")` e `portfolio.current_value == Decimal("1101357.67")` (igual ao footer `R$ 1.017.614,61` / `R$ 1.101.357,67`)

#### Scenario: posição sem total (legada ou CSV sem coluna)

- **WHEN** posição tem `total_invested IS NULL` e `total_current IS NULL`
- **THEN** a soma do asset recebe `Decimal('0')` para essa posição (não recomputa `qty × price`)

#### Scenario: template renderiza `row.invested` / `row.current_value` sem JS math

- **WHEN** dashboard HTML é renderizado para um asset
- **THEN** a célula `Total atual` exibe `row.current_value` (valor vindo do backend) sem operação `Number(row.qty) * Number(row.current_price)` no template
