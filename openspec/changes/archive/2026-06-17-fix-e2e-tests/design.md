## Context

9 e2e Playwright tests failing. Need root-cause diagnosis: environment (no browser/server), flakiness, or real regressions.

## Goals / Non-Goals

**Goals:**
- All 9 failing tests diagnosed
- Fix applied per root cause
- Green run with `task test-e2e`

**Non-Goals:**
- Não adicionar novos testes
- Não refatorar testes existentes

## Decisions

- **Diagnóstico first** — rodar cada teste isoladamente com `pytest -v -k` para capturar traceback real. Decidir correção por caso.
- **Marcadores flaky** — se for flaky (intermitente), adicionar `@pytest.mark.flaky` ou estabilizar com retry/wait.
- **Fixture de setup** — verificar se S04/S06 falham por seed data ausente (regressão pós multi-user seed).

## Risks / Trade-offs

- [Medium] Se forem regressões reais, escopo pode crescer — dependerá do diagnóstico.
