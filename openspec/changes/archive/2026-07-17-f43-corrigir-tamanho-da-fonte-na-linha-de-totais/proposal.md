## Why

A linha de totais da classe na tabela de patrimônio apresenta formatação visual inconsistente com o resto da tabela. O tamanho da fonte dos valores (Ganho, Posição, percentuais) parece menor que o das linhas de ativos, prejudicando a legibilidade e a hierarquia visual da informação.

## What Changes

- Ajustar CSS para alinhar o tamanho da fonte da linha de totais com o padrão da tabela
- Garantir que `.class-totals-row td` herde corretamente o `font-size: 0.9rem` de `.asset-table`
- Revisar se `.class-totals-label` (0.75rem) está causando herança indesejada para células vizinhas

## Capabilities

### New Capabilities

Nenhuma nova capacidade — é correção visual de UI existente.

### Modified Capabilities

Nenhuma capacidade com mudança de requisito. Apenas ajuste de apresentação.

## Impact

- Arquivo: `src/omaha/static/app.css`
- Seletores afetados: `.class-totals-row td`, possivelmente `.class-totals-label`
- Sem mudança de comportamento, backend, ou testes
- Sem breaking changes
