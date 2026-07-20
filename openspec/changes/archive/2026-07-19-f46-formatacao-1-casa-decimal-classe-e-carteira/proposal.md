## Why

Colunas "Atual", "Alvo", "Desvio" nos grupos "Classe" e "Carteira" da tabela de patrimônio arredondam para 0 casas decimais. Percentuais como 12.7% viram 13% — perda de precisão que dificulta leitura e comparação. Formatação com 1 casa decimal (ex: 12.7%) melhora granularidade sem poluir visual.

## What Changes

- Passar `1` como segundo argumento para `formatPctRounded()` e `formatDeviationPp()` em todas as chamadas `x-text` dos grupos "Classe" e "Carteira" (totais e per-asset rows)
- Funções JS já aceitam parâmetro `decimals` — nenhuma alteração no código JS necessário
- Linha de totais da classe: Atual/Alvo continuam como `—` (Classe) ou com 1 casa decimal (Carteira), Desvio com 1 casa decimal em ambos os grupos

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `shared-table-formatters`: atualizar spec para documentar que `formatPctRounded` e `formatDeviationPp` aceitam parâmetro `decimals` (default 0)
- `class-section-totals`: atualizar spec para refletir que percentuais nos grupos Classe e Carteira usam 1 casa decimal

## Impact

- `src/omaha/templates/_patrimonio_class_section.html` — 14 chamadas `x-text` precisam de `, 1` adicionado
- `src/omaha/static/table-formatters.js` — sem alterações (funções já suportam)
- Nenhum CSS, layout ou código não-relacionado é afetado
