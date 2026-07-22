## 1. Diagnóstico completo da suite

- [ ] 1.1 Rodar `uv run task test-unit` e registrar resultado (pass/fail count)
- [ ] 1.2 Rodar `uv run task test-integration` e registrar resultado
- [ ] 1.3 Rodar `uv run task test-e2e` e registrar resultado
- [ ] 1.4 Rodar `uv run task test-bdd` e registrar resultado
- [ ] 1.5 Rodar `uv run task test-visual` (sem flag de update) e registrar resultado
- [ ] 1.6 Catalogar cada falha com classificação: regression, drift, flaky, baseline-stale, production-bug

## 2. Atualização de baselines visuais stale

- [ ] 2.1 Revisar diffs em `tests/visual/results/` para confirmar que 19 falhas são baseline-stale (F41–F47)
- [ ] 2.2 Confirmar que nenhuma falha visual é regressão real (comparar com UI manual se necessário)
- [ ] 2.3 Rodar `UPDATE_VISUAL_BASELINES=1 uv run task test-visual` para regenerar PNGs
- [ ] 2.4 Inspecionar PNGs regenerados em `tests/visual/baselines/` visualmente
- [ ] 2.5 Rodar `uv run task test-visual` sem flag para confirmar que todos passam

## 3. Investigação de flaky BDD

- [ ] 3.1 Rodar `test_blur_empty_class_input_saves_zero` isoladamente (sem xdist) para confirmar que passa
- [ ] 3.2 Rodar múltiplas vezes sob xdist para tentar reproduzir flakiness
- [ ] 3.3 Se reproduzível: identificar causa-raiz (timing, DB isolation, fixture compartilhada)
- [ ] 3.4 Se causa-raiz clara: aplicar fix cirúrgico (retry, fixture isolation, ou ajuste de timing)
- [ ] 3.5 Se não reproduzível: documentar como known flaky no relatório

## 4. Documentação e relatório

- [ ] 4.1 Criar `tests/SUITE_HEALTH.md` com relatório de saúde completo
- [ ] 4.2 Documentar classificação de cada falha (tipo, causa, ação tomada)
- [ ] 4.3 Documentar supersessão de T28 por T27 (`064113c`)
- [ ] 4.4 Documentar que commit `bcb68836` é irresolvível e não deve ser referenciado

## 5. Verificação final

- [ ] 5.1 Rodar suite completa novamente para confirmar estado final
- [ ] 5.2 Verificar que `tests/SUITE_HEALTH.md` está correto e completo
- [ ] 5.3 Verificar que baselines visuais estão atualizados e passam sem flag
- [ ] 5.4 Verificar que BDD flaky está resolvido ou documentado
