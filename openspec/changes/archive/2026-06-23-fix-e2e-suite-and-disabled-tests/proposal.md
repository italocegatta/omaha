## Why

`tests/e2e/_disabled/` contém 10 arquivos (38 test functions,
3873 linhas) que estão desabilitados desde a migração de
single-user `family` para multi-user `Italo`+`Ana` (commit
`35bf15d`) e a correção de M002 (`a8b1d13`). A suíte e2e
inteira é RED porque os helpers de login assumem o usuário
`family` que não existe mais, e a infraestrutura
`tests/e2e/conftest.py` ainda roda mas não tem nenhum teste
ativo para coletar.

O `M002_RESSALVA_DIAGNOSIS.md` documenta a análise: o bug é
nos test helpers, não na produção. O fix mecânico
(`family` → `Italo`, drop `assert startswith("#")`, deletar
`test_inline_edit_blocks_when_sum_neq_100`) destrava a
maioria. Mas o rework completo precisa também:

- `test_s01_inline_edit.py:test_inline_edit_blocks_when_sum_neq_100`
  codifica o bug removido pelo change
  `fix-inline-edit-off-100-blocking` (D006) — deve ser
  **deletado** (não atualizado) e substituído pelo cenário
  inverso (off-100 é aceito) que o change BDD já cobre.
- Outros testes podem ter drift de testid/selectors
  acumulados (e.g. a migração de `Minha Categoria` →
  import modal binding).

## What Changes

- Mover os 10 arquivos de `tests/e2e/_disabled/` para
  `tests/e2e/` (re-habilitar a coleta).
- Em `tests/e2e/_disabled/test_s04_user_journey.py:190`,
  trocar `page.fill(SELECTORS["login_user"], "family")` por
  `"Italo"`.
- Em `tests/e2e/_disabled/test_s05_user_journey.py:333-334`,
  dropar a asserção `assert v.startswith("#")` e
  `assert len(v) in (4, 7)` (hex-only checks) — manter só o
  `assert v, f"--class-{k} token is empty..."` (string-vazia
  check que cobre ambos hex e oklch).
- Em `tests/e2e/_disabled/test_s01_inline_edit.py`,
  **deletar** o test
  `test_inline_edit_blocks_when_sum_neq_100` (codifica
  comportamento bugado que foi removido por
  `fix-inline-edit-off-100-blocking`). O cenário BDD
  "Inline edit off-100 é aceito (D006)" cobre a direção
  oposta.
- Rodar a suíte e corrigir o que quebrar.

## Capabilities

### Modified Capabilities

- `e2e-rework`: nova capability trackeia o rework
  incremental. Primeiro passo: re-habilitar a suíte.

## Impact

- **Tests**: 10 arquivos movidos, 1 test deletado (codifica
  bug), ~2 linhas de helpers corrigidas. ~38 test
  functions re-habilitadas.
- **Produção**: zero.
- **CI**: a suíte e2e volta a rodar no pipeline. Pode
  falhar em testes com drift de selectors; esses vão
  exigir investigação adicional (escopo deste change).
