## Why

M002 foi fechado em 2026-06-12 com `needs-attention`: uma regressão e2e em
`test_s05_user_journey.py` ficou sem diagnóstico, e `test_s06_full_journey.py` —
o teste escrito especificamente para travar o fix do import-modal
(`a8b1d13 fix(import-modal): select binding + seed rule + openspec sync`) e o
`suggest_class_id` (`a8b1d13` é descendente de `35bf15d`) — nunca foi executado
em browser real. O conftest do e2e (`tests/e2e/conftest.py:185`) hard-coda
`/usr/bin/chromium-browser`, que não existe neste host (Ubuntu 26.04, sem
binário do Playwright em `~/.cache/ms-playwright/`); logo, **nenhum teste
`tests/e2e/` roda hoje**, e os 87 testes de import + 229 totais reportados
na ressalva §5.2 do PRD são apenas unit/integration, não full-browser.

O fix mais recente do projeto toca exatamente o código que S06 cobre:
- `import-modal-class-binding`: Alpine `<select>` com `<template x-for>` —
  corrigido com padrão `x-init $nextTick` + `x-effect` no `dashboard.html:510`
  e `:553`.
- `import-class-auto-suggest`: `suggested_class_id` populado no preview
  server-side para casar categoria do CSV com classes do perfil.

Sem rodar S06 num browser real, não temos prova de que esses dois fixes
(compromissos críticos do M002) funcionam ponta-a-ponta com o CSV real
do Italo (`posicao_italo.csv` — 8 categorias distintas, exercita os 3
caminhos do `suggest_class_id`).

## What Changes

- **Infra de teste**: tornar `tests/e2e/conftest.py` resiliente à ausência de
  `/usr/bin/chromium-browser` — apontar para o binário já instalado pelo
  Playwright em `~/.cache/ms-playwright/chromium-1226/chrome-linux64/chrome`
  (265 MB, presente neste host após `playwright install chromium --with-deps`),
  com env var `E2E_CHROMIUM_PATH` para override. Manter `/usr/bin/chromium-browser`
  como fallback terciário. Atualizar `README.md` §Tests com o setup real.
- **Verificação S06**: executar `pytest tests/e2e/test_s06_full_journey.py -v`
  — teste já existe (480 linhas, escrito para o fix `a8b1d13`), cobre o
  loop crítico `login → criar 5 classes → upload posicao_italo.csv → assert
  suggested_class_id por categoria → commit → dashboard`.
- **Diagnóstico S05**: rodar `pytest tests/e2e/test_s05_user_journey.py -v`
  para confirmar/reproduzir a regressão listada em M002 ressalva §5.1.
  Sem e2e rodando, a ressalva fica perpétua.
- **Sem mudança de código de produção**: nenhum arquivo em `src/omaha/`
  é tocado. Esta change é exclusivamente setup + verificação. Se S06
  falhar, abre-se change separada para o fix.

## Capabilities

### New Capabilities

Nenhuma. Esta change não introduz capacidade nova — é verificação de
capacidades já existentes.

### Modified Capabilities

- `import-class-auto-suggest`: adicionar cenário E2E real-browser
  (`Scenario: Importação ponta-a-ponta com posicao_italo.csv completa
  com `suggested_class_id` correto por categoria`), já que o teste
  `test_s06_full_journey.py` valida o pipeline completo contra o CSV
  real (não apenas o cenário de integração `sample_broker.csv`).
- `import-modal-class-binding`: adicionar cenário E2E real-browser
  (`Scenario: Seletor de classe no modal de import préseleciona a
  classe sugerida pelo servidor após upload de CSV real`), exercitando
  o padrão `x-init $nextTick` + `x-effect` em `dashboard.html:510` com
  opções populadas server-side.

## Impact

- `tests/e2e/conftest.py`: tornar path do chromium configurável
  (env var `E2E_CHROMIUM_PATH`, default para o binário do Playwright).
- `README.md` §Tests: atualizar a frase "needs Playwright + a one-time
  `playwright install chromium`" para incluir o passo concreto
  (`uv run playwright install chromium --with-deps`) e nota sobre o
  fallback.
- Setup já feito: chromium 1226 + headless-shell em
  `~/.cache/ms-playwright/chromium-1226/` e
  `~/.cache/ms-playwright/chromium_headless_shell-1226/`. Total ~450 MB
  + libs do sistema via `--with-deps`. Reaproveitável em re-runs.
- Suite e2e: passa de "broken in this environment" para "runs end-to-end
  against real chromium". Reduz a ressalva M002 de 2 itens (regressão S05
  + 2 gaps) para potencialmente 0.
- Sem mudança de produção (`src/omaha/`), sem migration, sem mudança de
  schema, sem mudança de API.
