# broker-csv-number-parsing Specification (delta)

Delta spec for `broker-csv-number-parsing` capability. Adds 1
requirement covering the new `Total investido` / `Total atual`
columns introduced by `broker-csv-import-totals`. No existing
requirement changes.

## ADDED Requirements

### Requirement: Parser aplica a mesma heurística BR/US/R$/quotes às colunas de total

A função `_parse_brazilian_number` MUST ser usada para parsear os
valores das colunas `Total investido` e `Total atual` quando
presentes no CSV. As regras existentes (BR-milhar com `.` sozinho,
US-decimal fallback, prefixo `R$`, aspas, sentinel `-`) MUST se
aplicar identicamente a essas colunas.

#### Scenario: Total atual BR-milhar com R$ parseado para Decimal

- **WHEN** célula contém `"R$ 8.658,02"` (linha VT do fixture `tests/posicao_italo.csv`)
- **THEN** `_parse_brazilian_number("R$ 8.658,02")` retorna `Decimal("8658.02")`

#### Scenario: Total investido com aspas e R$

- **WHEN** célula contém `'"R$ 8.153,44"'` (linha VT do fixture `tests/posicao_italo.csv`)
- **THEN** `_parse_brazilian_number('"R$ 8.153,44"')` retorna `Decimal("8153.44")`

#### Scenario: Total atual em US-decimal

- **WHEN** célula contém `"8658.02"` (corretora US-style sem R$, sem vírgula)
- **THEN** `_parse_brazilian_number("8658.02")` retorna `Decimal("8658.02")`
