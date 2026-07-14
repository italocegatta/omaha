## Why

Leitura de carteira está densa demais. Números com mais casas do que o necessário ocupam espaço, e ganho dividido em mais de uma célula força varredura visual extra.

## What Changes

- Reduzir formatação monetária e quantitativa para 0 casas decimais nas tabelas afetadas.
- Exceção: quantidade de BTC mostra 3 casas decimais.
- Arredondar percentuais somente nas colunas `Ganho`, `Classe / Atual`,
  `Classe / Alvo`, `Carteira / Atual`, `Carteira / Alvo` e
  `Carteira / Desvio`; demais percentuais mantêm sua precisão existente.
- Unificar coluna de ganho em um único bloco visual com valor absoluto + percentual.
- Ordenar ganho por valor absoluto, não pelo valor bruto com sinal.
- Completar filtros numéricos da tabela de ativos para `Qtd` e `Preço médio`.
- Ajustar CSS das tabelas para manter densidade e legibilidade após consolidação das células.
- Manter labels PT-BR e contratos de interação existentes.

## Capabilities

### New Capabilities

- Nenhuma.

### Modified Capabilities

- `class-section-totals`: atualizar contrato de exibição do ganho na tabela de ativos da seção de classe, incluindo célula única de ganho, ordenação por absoluto e arredondamento mais compacto.
- `rebalance-page`: ajustar contrato de exibição da quantidade na operação para 3 casas em BTC e 0 casas nos demais casos, preservando a tabela compacta.

## Impact

- Templates: `src/omaha/templates/_patrimonio*.html`, `src/omaha/templates/_rebalance*.html`.
- CSS: `src/omaha/static/app.css`.
- UI: carteira e rebalanceamento ficam mais densos, com leitura mais rápida de valores e ganho.
- Testes: cobertura de ordenação e formatação numérica precisa ser atualizada para o novo contrato de apresentação.
