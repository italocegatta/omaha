## Purpose

Exibição do **Total atual** de cada posição na tabela de revisão do modal de import, calculado como `qty * current_price` e formatado como moeda brasileira sem casas decimais.

## Requirements

### Requirement: Total atual exibido por linha, 0 casas decimais

A tabela de revisão do modal de import (tanto a seção "Ativos existentes na carteira" quanto "Novos ativos") MUST exibir, em cada linha, o **Total atual** calculado como `qty * current_price`, formatado como moeda brasileira SEM casas decimais (`R$ 3.250`, não `R$ 3.250,00`). O cálculo DEVE usar o `current_price` retornado pelo endpoint `/api/import/preview` (já presente na resposta atual).

#### Scenario: Linha auto-matched mostra Total atual

- **WHEN** a tabela `data-testid="import-existing-table"` renderiza uma linha com `qty = 100` e `current_price = "32.50"`
- **THEN** a célula da coluna "Total atual" dessa linha exibe `R$ 3.250` (arredondamento HALF_UP de 3250.0, sem casas decimais)

#### Scenario: Linha unmatched mostra Total atual

- **WHEN** a tabela `data-testid="import-unmatched-table"` renderiza uma linha com `qty = 10` e `current_price = "150.00"`
- **THEN** a célula da coluna "Total atual" dessa linha exibe `R$ 1.500` (sem casas decimais)

#### Scenario: Total atual arredonda HALF_UP

- **WHEN** a linha tem `qty = 3` e `current_price = "10.70"`
- **THEN** o Total atual é exibido como `R$ 32` (3 × 10.70 = 32.10, arredondado HALF_UP para inteiro mais próximo)

#### Scenario: Total atual recalcula sem concatenar strings

- **WHEN** o backend expõe o `current_price` como string numérica válida no payload `auto_matched[i]` e `unmatched[i]`
- **THEN** o frontend faz `Number(qty) * Number(current_price)` sem multiplicar strings brutas como bigint (evita concatenação)
