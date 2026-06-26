# broker-csv-number-parsing Specification

## ADDED Requirements

### Requirement: Parser reconhece BR-milhar com `.` sozinho

A função `_parse_brazilian_number` em `src/omaha/csv_import.py` MUST
parsear células com `.` sozinho em grupos de exatamente 3 dígitos
como **milhares** (convenção BR), strippando todos os pontos antes
de converter para `Decimal`. Cells fora desse padrão MUST cair no
fallback de decimal US (preservar o ponto).

#### Scenario: qty inteira com 3 dígitos pós-ponto → BR-milhar

- **WHEN** célula contém `"2.466"` (qty FIXA11 do fixture)
- **THEN** `_parse_brazilian_number("2.466")` retorna `Decimal("2466")`

#### Scenario: qty inteira com múltiplos grupos de 3 → BR-milhar multi-grupo

- **WHEN** célula contém `"1.234.567"`
- **THEN** `_parse_brazilian_number("1.234.567")` retorna `Decimal("1234567")` (sem crash)

#### Scenario: 8 qty do fixture real parseiam como inteiro × 1000

- **WHEN** `parse_positions` é chamado sobre `tests/posicao_italo.csv`
- **THEN** `FIXA11.qty == Decimal("2466")`, `CPTS11.qty == Decimal("3075")`, `RBVA11.qty == Decimal("1098")`, `RBRX11.qty == Decimal("1797")`, `GMAT3.qty == Decimal("3100")`, `KEPL3.qty == Decimal("1500")`, `WIZC3.qty == Decimal("2100")`, `VAMO3.qty == Decimal("3800")`

### Requirement: Parser cai em US-decimal quando o grupo pós-ponto não tem 3 dígitos

Células com `.` sozinho onde o grupo pós-ponto tem ≠ 3 dígitos MUST
ser parseadas como decimal US (ponto preservado). Garante que
preços em formato `1234.56` continuam funcionando.

#### Scenario: 2 dígitos pós-ponto → US-decimal

- **WHEN** célula contém `"1234.56"`
- **THEN** `_parse_brazilian_number("1234.56")` retorna `Decimal("1234.56")`

#### Scenario: 1 dígito pós-ponto → US-decimal

- **WHEN** célula contém `"1.5"`
- **THEN** `_parse_brazilian_number("1.5")` retorna `Decimal("1.5")`

#### Scenario: 2 dígitos pós-ponto começando com 0 → US-decimal

- **WHEN** célula contém `"0.50"`
- **THEN** `_parse_brazilian_number("0.50")` retorna `Decimal("0.50")`

### Requirement: Parser strippa prefixo `R$` e aspas antes do parse

A função MUST aceitar células com prefixo de moeda (`R$`, case-
insensitive, com ou sem espaço) e com aspas duplas ao redor
(escapadas pelo CSV writer quando a célula contém vírgula).

#### Scenario: prefixo R$ com espaço

- **WHEN** célula contém `"R$ 990,92"`
- **THEN** `_parse_brazilian_number("R$ 990,92")` retorna `Decimal("990.92")`

#### Scenario: aspas duplas ao redor de BR-milhar

- **WHEN** célula contém `'"2.466"'`
- **THEN** `_parse_brazilian_number('"2.466"')` retorna `Decimal("2466")`

#### Scenario: prefixo R$ minúsculo

- **WHEN** célula contém `"r$ 1.234,56"`
- **THEN** `_parse_brazilian_number("r$ 1.234,56")` retorna `Decimal("1234.56")`

### Requirement: Parser trata `-` como zero (sentinel de ativo não-tradeável)

A função MUST retornar `Decimal("0")` quando a célula for exatamente
`-` (sentinel de corretora para ativo não-tradeável). Corretoras
omitem qty/avg/current de CDBs/RDBs no vencimento usando `-`.

#### Scenario: célula igual a `-`

- **WHEN** célula contém `"-"`
- **THEN** `_parse_brazilian_number("-")` retorna `Decimal("0")`

#### Scenario: linha RDB Pós sem qty parseia como qty=0

- **WHEN** CSV contém linha `RDB Pós 100% CDI 01/08/2033,-,-,20000.00,26907.07,...`
- **THEN** `parse_positions` retorna `RawPosition(qty=Decimal("0"), avg_price=Decimal("20000.00"), current_price=Decimal("26907.07"))` para esse ticker

### Requirement: Parser levanta InvalidOperation em input genuinamente mal-formado

Células que não sejam número nem `-` MUST levantar
`InvalidOperation` (sem fallback silencioso). O caller
(`_parse_data_row`) captura a exceção e dropa a linha — log
de linha mal-formada continua visível no summary do import.

#### Scenario: célula de texto sem dígitos

- **WHEN** célula contém `"abc"`
- **THEN** `_parse_brazilian_number("abc")` levanta `InvalidOperation`

#### Scenario: célula vazia

- **WHEN** célula contém `""`
- **THEN** `_parse_brazilian_number("")` levanta `InvalidOperation`
