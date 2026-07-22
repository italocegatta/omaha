## Context

Suite de testes do omaha tem 4 lanes (unit, integration, e2e, bdd) + visual regression. Após ciclo F41–F47 (mudanças visuais na tabela de patrimônio) e T27 (correção de 5 integration tests), baselines visuais ficaram stale e há 2 testes BDD flaky sob xdist. T28 foi proposto para corrigir 18 testes mas commit `064113c` (T27) já cobriu os problemas — T28 está parcialmente obsoleto.

Estado atual da suite (exploração):
- **Unit**: 452 passed, 0 failed ✅
- **Integration**: 377 passed, 0 failed ✅
- **E2E**: 49 passed, 0 failed ✅
- **BDD**: 51 passed, 2 flaky ⚠️ (`test_blur_empty_class_input_saves_zero[Italo]` e `[Ana]`)
- **Visual**: ~20 total, 19 failures (baselines stale) ⚠️

## Goals / Non-Goals

**Goals:**
- Diagnóstico completo e documentado de todas as falhas atuais da suite.
- Atualização segura de baselines visuais stale com verificação antes de aceitar.
- Investigação de flaky BDD — correção apenas se reproduzível e causa-raiz clara.
- Documentar supersessão de T28 por T27.

**Non-Goals:**
- Nenhuma alteração em código de produção (`src/`).
- Não duplicar correções já feitas por T27 (`064113c`).
- Não corrigir falhas que sejam cobertas por T28 se T28 for retomado.
- Não alterar configuração de CI/CD ou hooks.
- Não reestruturar suite de testes.
- Não confiar em commit `bcb68836` (referência antiga do roadmap, irresolvível).

## Decisions

### D1 — Baseline refresh via variável de ambiente

**Decisão**: Usar `UPDATE_VISUAL_BASELINES=1 uv run pytest tests/visual/` para regenerar PNGs stale.

**Rationale**: Comando padrão do pytest-playwright/screenshot testing. Alternativa considerada: regenerar manualmente um por um — rejeitada por ser propensa a erro e lenta.

**Processo seguro**:
1. Rodar testes visuais sem flag para ver diff atual.
2. Revisar falhas — confirmar que são drift de baseline (F41–F47), não regressão real.
3. Rodar com `UPDATE_VISUAL_BASELINES=1` para regenerar.
4. Inspecionar PNGs gerados visualmente (ou via diff de arquivo).
5. Commit separado com mensagem clara sobre baseline refresh.

### D2 — BDD flaky: investigar antes de corrigir

**Decisão**: Investigar `test_blur_empty_class_input_saves_zero` em isolamento primeiro. Se passar isolado (como relatado), o problema é isolamento de DB/timing sob xdist — abordar com retry ou fix de fixture, não reescrever teste.

**Rationale**: Teste passa em isolamento → não é bug de produção. Flakiness sob xdist é padrão conhecido (T23.1 já corrigiu problema similar). Alternativa considerada: marcar como `@pytest.mark.flaky` — rejeitada por mascarar problema real.

### D3 — T28: documentar supersessão, não duplicar

**Decisão**: Não implementar correções de T28 nesta fatia. Documentar que T27 `064113c` já cobre os issues propostos por T28. Se T28 for retomado, deve ser re-scoped.

**Rationale**: Evitar duplicação de esforço e conflitos de merge. T28 está `Spec Proposed` — owner pode retomar se necessário.

### D4 — Diagnóstico como deliverable principal

**Decisão**: Criar relatório de saúde (`tests/SUITE_HEALTH.md` ou seção em `tests/AUDIT.md`) documentando classificação de cada falha.

**Rationale**: Transparência para owner sobre estado real da suite. Facilita decisões futuras sobre priorização.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Baseline refresh aceita regressão visual real como "stale" | Revisar diffs antes de aceitar; comparar com screenshots manuais se dúvida |
| BDD flaky não reproduzível → não corrigível | Documentar como known flaky; não marcar como flaky decorator sem investigar |
| T28 retomado → conflito com mudanças desta fatia | Escopo desta fatia é mínimo (baselines + flaky); conflito improvável |
| Commit `bcb68836` irresolvível → perda de contexto histórico | Aceitar perda; contexto suficiente em roadmap e commits recentes |

## Migration Plan

1. Rodar suite completa, registrar resultados.
2. Classificar falhas por tipo.
3. Atualizar baselines visuais (se aprovado).
4. Investigar BDD flaky (se reproduzível).
5. Documentar relatório de saúde.
6. Commit com baselines + relatório.
7. Atualizar roadmap (T29 → Applied).

Rollback: `git revert` do commit — baselines voltam ao estado anterior, relatório removido.

## Open Questions

- Owner quer que T28 seja formalmente deprecado/fechado, ou apenas documentado como obsoleto?
- Baselines devem ser commitadas no mesmo commit do relatório, ou separados?
