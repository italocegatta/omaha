## Context

O merge `849749f` (merge milestone/M002 → main) resolveu conflito em `dashboard.html`
mantendo a versão da main antiga (`62f2b2b`, 288 linhas) em vez da versão do branch M002
(`b160a43`, 1281 linhas). O commit `a8b1d13` aplicou o fix de select binding sobre a
versão M002 e representa o estado correto.

O conteúdo M002 perdido inclui: modal de import (upload CSV + review + commit), botão
"Importar CSV", edição inline de target % de classes, CRUD de ativos no dashboard,
seções colapsáveis, total da soma de classes, e Alpine stores `classSum` + `importModal`.

## Goals / Non-Goals

**Goals:**

- Restaurar `dashboard.html` para o estado funcional correto (versão M002 + fix a8b1d13)
- Garantir que o modal de import, botão "Importar CSV", e demais funcionalidades M002
  estejam operacionais
- Verificar que CSS e testes estão consistentes com a versão restaurada

**Non-Goals:**

- Não modificar o design ou comportamento existente das funcionalidades M002
- Não criar novas features — apenas restaurar o que foi perdido
- Não alterar rotas de backend (já estão corretas)

## Decisions

### Decision: Restaurar dashboard.html de a8b1d13 (não de b160a43)

O commit `a8b1d13` já contém o fix de select binding (`x-init $nextTick` + `x-effect`)
aplicado sobre a versão M002. É o estado mais correto e completo — restaurar dele
elimina a necessidade de reaplicar o fix manualmente.

### Decision: Verificar diff também em app.css

Parte do CSS do modal de import pode ter sido definida em commits no branch M002
(`fb03d08` adicionou 214 linhas em app.css). A versão atual de app.css pode ou não
conter esse CSS. Verificar com `git diff a8b1d13 HEAD -- src/omaha/static/app.css`.

### Decision: Não mexer em testes de backend

As rotas `/import` e `/import/review` já redirecionam para `/` e continuam funcionando.
Os testes de API (`test_s04_*`) já testam os endpoints de import via JSON. Apenas
verificar se os testes e2e (`test_s04_*`, `test_s06_*`) passam após restauração.

## Risks / Trade-offs

- **[Restauração incompleta]** O CSS do modal pode não estar presente no HEAD atual de
  `app.css`. Se estiver faltando, será necessário restaurar também.
  → Mitigação: verificar diff do CSS antes de implementar.

- **[Regression em inline editing]** A versão restaurada inclui Alpine store `classSum`
  que referência `$store.classSum.register()`. A versão atual do dashboard não tem
  esse store. É only additive (store que não existia antes passa a existir), sem risco
  de conflito.

- **[Testes e2e quebrados]** Os testes `test_s04_*` e `test_s06_*` esperam o modal
  funcional. Se falharem mesmo com o dashboard correto, pode ser problema de setup
  (chromium path, seed data).
  → Mitigação: rodar `uv run pytest tests/e2e/test_s04_user_journey.py -v` como
    smoke test após restauração.
