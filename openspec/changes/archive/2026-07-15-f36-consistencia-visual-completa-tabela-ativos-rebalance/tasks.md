## 1. Ícones de filtro — unificar componente Material Symbols

- [ ] 1.1 Alterar `_filter_controls.html`: trocar classe `icon icon--sm` por `material-symbols-outlined` no span do ícone de filtro (linha 22) e no span do ícone de clear (linha 29)
- [ ] 1.2 Verificar que os ícones renderizam corretamente em ambos os contextos (asset table com teleport + rebalance table inline)
- [ ] 1.3 Verificar que `data-testid` dos botões de filtro não mudou

## 2. Formatação de desvio — 0 decimais com sinal explícito

- [ ] 2.1 Em `_patrimonio_class_section.html`, linha 145: trocar `formatPct(classDeviationPctClass)` por `formatDeviationPp(classDeviationPctClass)` na célula de desvio da classe (totals row)
- [ ] 2.2 Em `_patrimonio_class_section.html`, linha 278: trocar `formatPct(a.class_deviation_pct)` por `formatDeviationPp(a.class_deviation_pct)` na célula de desvio da classe (asset rows)
- [ ] 2.3 Em `_patrimonio_class_section.html`, linha 327: trocar `formatPctRounded(a.portfolio_deviation_pct)` por `formatDeviationPp(a.portfolio_deviation_pct)` na célula de desvio da carteira (asset rows)
- [ ] 2.4 Em `_patrimonio_class_section.html`, linha 191: trocar `formatPctRounded(classPortfolioDeviationPct)` por `formatDeviationPp(classPortfolioDeviationPct)` na célula de desvio da carteira (totals row)
- [ ] 2.5 Verificar formatação visual: desvio positivo mostra `+X%`, negativo mostra `-X%`, zero mostra `0%`

## 3. Espaçamento de cabeçalhos

- [ ] 3.1 Em `app.css`: aumentar `--col-ativo` de `340px` para `360px` (seção F15, linha ~1770)
- [ ] 3.2 Em `app.css`: aumentar padding de `.asset-table th, .asset-table td` de `0.72rem` para `0.82rem` (linha ~1876)
- [ ] 3.3 Verificar que todos os cabeçalhos de coluna (incluindo sub-headers Classe/Carteira) cabem sem truncamento em viewport 1440px+
- [ ] 3.4 Verificar que a tabela não causa scroll horizontal indesejado em viewport 1440px

## 4. "Total da classe" — card visual com cor da classe

- [ ] 4.1 Em `app.css`: adicionar estilos para `.class-totals-row td` com `border-left: 3px solid` usando variável de cor da classe
- [ ] 4.2 Em `app.css`: adicionar background com `color-mix(in srgb, var(--class-color) 8%, var(--surface))` na linha de totais
- [ ] 4.3 Em `app.css`: estilizar `.class-totals-label` com cor da classe e font-weight 700
- [ ] 4.4 Implementar a propagação da cor da classe para a linha de totais via nth-of-type ou data-attribute (mesma lógica do header)
- [ ] 4.5 **BLOQUEADO**: validar cor e opacidade com owner antes de implementar

## 5. Validação visual e testes

- [ ] 5.1 Testar resize: viewport 1440px, 1024px, 768px, 480px — verificar que filtros, formatação e totais ficam corretos
- [ ] 5.2 Testar filter popup: abrir/fechar filtro em cada coluna do asset table — verificar posicionamento via teleport
- [ ] 5.3 Testar ordenação: clicar em cada header para ordenar — verificar que formatação de desvio mantém formato `+X%` / `-X%`
- [ ] 5.4 Testar contraste: verificar que o card de totais tem contraste suficiente (WCAG AA) com a cor da classe
- [ ] 5.5 Verificar que testes e2e existentes não quebram (filtros, formatação numérica)
