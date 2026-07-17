## 1. Diagnóstico

- [ ] 1.1 Inspecionar CSS computado da linha de totais no browser (F12 → Elements)
- [ ] 1.2 Comparar font-size efetivo de `.class-totals-row td` vs linhas de ativos
- [ ] 1.3 Identificar se herança vem de `.class-totals-label` ou outro seletor

## 2. Correção CSS

- [ ] 2.1 Adicionar `font-size: inherit` em `.class-totals-row td` (app.css:1807)
- [ ] 2.2 Verificar se `.class-totals-label` precisa de isolamento (se necessário, adicionar `font-size` explícito nas células de valores)
- [ ] 2.3 Testar em diferentes resoluções (mobile, desktop)

## 3. Validação

- [ ] 3.1 Abrir `/patrimonio` e verificar linha de totais visualmente
- [ ] 3.2 Comparar com linhas de ativos — fonte deve ser igual (0.9rem)
- [ ] 3.3 Rodar `uv run task test-unit` para garantir sem regressão
