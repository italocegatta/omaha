## Context

Tabela de patrimônio exibe colunas "Atual", "Alvo", "Desvio" nos grupos "Classe" e "Carteira". Formatação atual usa 0 casas decimais via `formatPctRounded(value)` e `formatDeviationPp(value)`. Funções JS já aceitam parâmetro opcional `decimals` (default 0) — implementado em F28/R33. Template não passa o parâmetro, então sempre usa 0.

## Goals / Non-Goals

**Goals:**
- Atualizar chamadas `x-text` no template para passar `decimals=1` nos grupos Classe e Carteira
- Manter backward compatible — outras chamadas (Ganho, Qtd) continuam com 0 casas

**Non-Goals:**
- Alterar funções JS (já suportam)
- Mudar CSS, layout ou colunas fora de Classe/Carteira
- Alterar formatação de moeda ou quantidade

## Decisions

**D1: Template-only change.** Funções `formatPctRounded` e `formatDeviationPp` já aceitam `decimals`. Mudança é só adicionar `, 1` nas chamadas x-text do template. Alternativa: criar funções separadas `formatPct1d` — rejeitada por desnecessário.

**D2: Escopo das chamadas afetadas.** Apenas colunas Classe (Atual, Alvo, Desvio) e Carteira (Atual, Alvo, Desvio) — tanto na linha de totais quanto nas linhas de ativos. Coluna Ganho (`formatPctRounded(a.gain_pct)`) mantém 0 casas.

**D3: Desvio na linha de totais (Classe).** Quando `classDeltaMessage` não existe e `|classDeviationPctClass| >= 0.0001`, `formatDeviationPp(classDeviationPctClass, 1)` exibe com 1 casa decimal.

## Risks / Trade-offs

- **Risco mínimo**: mudança é pontual no template, funções JS já testadas com parâmetro `decimals`
- **Trade-off**: 1 casa decimal pode parecer "muito preciso" para valores grandes (ex: 45.3%), mas melhora leitura para valores pequenos (ex: 0.7% vs 1%)
