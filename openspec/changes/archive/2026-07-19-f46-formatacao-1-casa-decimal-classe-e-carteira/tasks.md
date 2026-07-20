## 1. Template — Classe group (totals row)

- [ ] 1.1 Atualizar `formatDeviationPp(classDeviationPctClass)` para `formatDeviationPp(classDeviationPctClass, 1)` na linha de totais (Classe / Desvio, data-testid="class-total-deviation-class")

## 2. Template — Carteira group (totals row)

- [ ] 2.1 Atualizar `formatPctRounded(classCurrentPct)` para `formatPctRounded(classCurrentPct, 1)` (Carteira / Atual, data-testid="class-total-current-pct-portfolio")
- [ ] 2.2 Atualizar `formatPctRounded(classTargetPct)` para `formatPctRounded(classTargetPct, 1)` (Carteira / Alvo, data-testid="class-target-pct-view")
- [ ] 2.3 Atualizar `formatDeviationPp(classPortfolioDeviationPct)` para `formatDeviationPp(classPortfolioDeviationPct, 1)` (Carteira / Desvio, data-testid="class-total-deviation-portfolio")

## 3. Template — Classe group (per-asset rows)

- [ ] 3.1 Atualizar `formatPctRounded(a.current_pct_class)` para `formatPctRounded(a.current_pct_class, 1)` (Classe / Atual, data-testid="asset-current-pct-class")
- [ ] 3.2 Atualizar `formatPctRounded(a.target_pct)` para `formatPctRounded(a.target_pct, 1)` em ambos os spans (botão editável + span read-only) (Classe / Alvo, data-testid="asset-target-pct-class")
- [ ] 3.3 Atualizar `formatDeviationPp(a.class_deviation_pct)` para `formatDeviationPp(a.class_deviation_pct, 1)` (Classe / Desvio, data-testid="asset-class-deviation")

## 4. Template — Carteira group (per-asset rows)

- [ ] 4.1 Atualizar `formatPctRounded(a.current_pct_total)` para `formatPctRounded(a.current_pct_total, 1)` (Carteira / Atual, data-testid="asset-current-pct-total")
- [ ] 4.2 Atualizar `formatPctRounded(a.target_pct_total)` para `formatPctRounded(a.target_pct_total, 1)` em ambos os spans (botão editável + span read-only) (Carteira / Alvo, data-testid="asset-target-pct-total")
- [ ] 4.3 Atualizar `formatDeviationPp(a.portfolio_deviation_pct)` para `formatDeviationPp(a.portfolio_deviation_pct, 1)` (Carteira / Desvio, data-testid="asset-portfolio-deviation")

## 5. Verificação

- [ ] 5.1 Rodar `task test-unit` para garantir que nenhum teste existente quebrou
- [ ] 5.2 Verificar visualmente no browser que Classe e Carteira exibem 1 casa decimal
