## Context

`tests/e2e/_disabled/` tem 3873 linhas em 10 arquivos,
desabilitados desde a migração de seed multi-user
(`35bf15d feat(phase-02): palette contrast fixes, multi-user
seed, openspec infra`) e a correção de M002 (`a8b1d13`).

A `tests/e2e/conftest.py` ainda inicializa o dev server +
chromium mas não coleta nenhum teste. A suíte e2e como um
todo é silenciosamente inativa: `task test-e2e` roda o
conftest setup, abre o browser, fecha o browser, e sai com
0 testes coletados.

`M002_RESSALVA_DIAGNOSIS.md` documenta 3 fixes mecânicos
para destravar a suíte:

1. `tests/e2e/test_s04_user_journey.py:190` —
   `page.fill(SELECTORS["login_user"], "family")` →
   `"Italo"`.
2. `tests/e2e/test_s05_user_journey.py:333-334` — drop
   `assert v.startswith("#")` e `assert len(v) in (4, 7)`.
3. Re-rodar suíte e investigar o que ainda falhar.

Adicionalmente, o `test_s01_inline_edit.py:418` tem
`test_inline_edit_blocks_when_sum_neq_100` que codifica o
bug removido pelo change
`fix-inline-edit-off-100-blocking`. Esse test deve ser
deletado, não atualizado.

## Goals / Non-Goals

**Goals:**
- Re-habilitar a suíte e2e: mover arquivos, aplicar fixes
  mecânicos, deletar o test que codifica bug.
- Tornar a suíte utilizável no CI (não precisa passar 100%
  imediatamente — drift de selectors é esperado e tratado
  iterativamente).

**Non-Goals:**
- Reescrever a suíte e2e do zero.
- Cobrir lacunas que o BDD já cobre (e.g. visual polish,
  cenários de import modal — já cobertos por BDD + unit).
- Migrar para pytest-playwright (a suíte usa sync API
  manual via `tests/e2e/conftest.py`; migração é
  refactor maior).

## Decisions

### D1. Mover `_disabled/*` para `tests/e2e/` direto

Não criar uma pasta intermediária. A `_disabled/` é hoje
um diretório de quarentena que ninguém monitora — mover os
arquivos para o destino correto força visibilidade.

### D2. Fix mecânico do login: `family` → `Italo`

Match exato com o que `M002_RESSALVA_DIAGNOSIS.md`
recomenda. Não refatorar helpers em mudança maior.

### D3. Drop das asserções hex-only em `test_s05_user_journey.py`

`--class-4` e `--class-6` foram convertidos para
`oklch(...)` em `35bf15d` para melhor contraste. O test
original só checava o formato hex. Manter a asserção
`assert v, ...` (string não-vazia) cobre ambos os formatos.

### D4. Deletar `test_inline_edit_blocks_when_sum_neq_100`

Esse test existe **apenas** para verificar o bug que o
change `fix-inline-edit-off-100-blocking` removeu
(D006). Manter esse test seria codificar a regressão
como feature. O cenário BDD "Inline edit off-100 é aceito
(D006)" (adicionado naquele change) cobre a direção
oposta.

### D5. Erros de drift → follow-up, não bloqueia

Tests que falharem por drift de selectors (e.g. testid
mudou, classe CSS mudou) ficam como tarefas adicionais
neste change. Não são bloqueadores para o archive do
change — o objetivo é re-habilitar a suíte, não
garantir 100% green.

## Risks / Trade-offs

- **Re-habilitar suite quebrada expõe o ruído**: a suíte
  inteira pode ter drift acumulado. Tratar como trabalho
  iterativo.
- **CI noise**: `task test-e2e` passa de 0 testes para
  30+, com possíveis flakes pré-existentes. Mitigado
  pelo mesmo flake-rate que afeta BDD (test isolation
  robusta no conftest).

## Open Questions

_Nenhuma — o escopo é mecânico._
