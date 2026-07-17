## 1. Diagnóstico

- [ ] 1.1 Inspecionar larguras atuais das colunas no browser (F12 → Elements → computed)
- [ ] 1.2 Identificar colunas com espaço desperdiçado vs colunas comprimidas
- [ ] 1.3 Calcular soma total das larguras atuais

## 2. Ajuste CSS

- [x] 2.1 Aumentar `--col-ativo` de 205px para 250px (app.css:1691)
- [x] 2.2 Reduzir `--col-position` de 130px para 110px (app.css:1695)
- [x] 2.3 Reduzir `--col-class-current` de 100px para 80px (app.css:1697)
- [x] 2.4 Reduzir `--col-class-target` de 110px para 90px (app.css:1698)
- [x] 2.5 Reduzir `--col-portfolio-current` de 110px para 90px (app.css:1700)
- [x] 2.6 Reduzir `--col-portfolio-target` de 110px para 90px (app.css:1701)
- [x] 2.7 Reduzir `--col-class-deviation` de 100px para 90px (app.css:1699)
- [x] 2.8 Reduzir `--col-portfolio-deviation` de 100px para 90px (app.css:1702)

## 3. Validação

- [ ] 3.1 Abrir `/patrimonio` e verificar largura das colunas visualmente
- [ ] 3.2 Verificar se nomes longos de ativos ficam mais legíveis
- [ ] 3.3 Verificar se colunas de percentuais não ficaram apertadas demais
- [ ] 3.4 Testar em mobile (responsividade)
- [x] 3.5 Rodar `uv run task test-unit` para garantir sem regressão
