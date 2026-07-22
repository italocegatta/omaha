## Why

Suite completa de testes tem falhas residuais após ciclo intenso de mudanças visuais (F41–F47) e correções de testes (T27). Falhas não são diagnosticadas de forma abrangente — algumas são baselines visuais stale, outras são flaky sob xdist, e o status real da suite não está documentado. T28 foi proposto mas está parcialmente obsoleto (T27 commit `064113c` já cobre os problemas propostos). Esta fatia faz diagnóstico completo primeiro, correção depois, sem duplicar trabalho existente.

## What Changes

- Rodar suite completa (unit, integration, e2e, bdd, visual) e catalogar resultado de cada lane.
- Classificar cada falha: regressão recente, drift de assertion, bug de produção, flaky, baseline stale.
- Atualizar baselines visuais stale (19 PNGs desatualizados após F41–F47) com processo seguro de verificação/aprovação.
- Investigar flaky BDD `test_blur_empty_class_input_saves_zero` (Italo/Ana) — somente corrigir se reproduzível e causa-raiz identificada.
- Documentar que T28 está parcialmente obsoleto (T27 `064113c` cobre issues propostas).
- Nenhuma mudança de código de produção esperada — apenas testes e baselines.

## Capabilities

### New Capabilities

- `test-suite-health-report`: Relatório de saúde da suite de testes com classificação de cada falha por tipo (regressão, drift, flaky, baseline stale, bug de produção). Documenta estado atual e ações tomadas.

### Modified Capabilities

- `visual-regression-baseline`: Baseline PNGs precisam ser regenerados para refletir UI pós-F41–F47. Processo de aprovação seguro (diff visual antes de aceitar).

## Impact

- **Testes**: Apenas arquivos em `tests/` — nenhum código de produção alterado.
- **Baselines visuais**: PNGs em `tests/visual/baselines/` serão regenerados.
- **BDD**: Possível ajuste em `tests/bdd/test_scenarios.py` se flaky for reproduzível.
- **Documentação**: `tests/AUDIT.md` ou relatório similar pode ser criado/atualizado.
- **Risco**: Mínimo — mudanças limitadas a testes e baselines. Rollback trivial (reverter commit).
- **T28**: Marcar como obsoleto/documentar supersessão por T27.
