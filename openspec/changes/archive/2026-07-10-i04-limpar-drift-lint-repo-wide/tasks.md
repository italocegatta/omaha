# I04 — Limpar drift lint repo-wide — Tasks

## Progress

- [x] Task 1: Auto-fix diagnostics mecânicos
- [x] Task 2: Quebrar linhas longas em `src/omaha/routes/assets.py`
- [x] Task 3: Quebrar linhas longas em BDD step definitions
- [x] Task 4: Quebrar linhas longas em e2e tests + fix chave duplicada
- [x] Task 5: Verificar lint zero + hook pre-push

## Task 1: Auto-fix diagnostics mecânicos

Rodar `ruff check --fix` para corrigir todos os diagnósticos auto-fixáveis:

- I001 (import sort) — 6 files
- F401 (unused `import math`) — `validation.py`
- B010 (`setattr` → assignment) — 3 ocorrências em `conftest.py`
- SIM105 (`try/except/pass` → `contextlib.suppress`) — `conftest.py`
- F841 (unused `table_width`) — `test_asset_table.py`

```bash
uv run ruff check --fix src/ tests/
uv run ruff check src/ tests/
```

Segundo comando confirma que só restam E501 + F601.

## Task 2: Quebrar linhas longas em `src/omaha/routes/assets.py`

Corrigir 3 E501:

1. Linha 650: quebrar f-string do `detail=` após o `or`.
2. Linha 668: quebrar f-string do `detail=` após o `f"..."` operador.
3. Linha 673: quebrar assinatura do método — cada `Decimal | None` em linha própria.

## Task 3: Quebrar linhas longas em BDD step definitions

Corrigir 5 E501:

1. `tests/bdd/step_defs/asset_steps.py:59` — f-string do `wait_for_function`.
2. `tests/bdd/step_defs/dashboard_steps.py:107` — 144 chars, quebrar seletor.
3. `tests/bdd/step_defs/target_steps.py:89,125,155` — 3x template strings.

## Task 4: Quebrar linhas longas em e2e tests + fix chave duplicada

Corrigir 4 E501:

1. `tests/e2e/test_asset_crud.py:153,225` — 2x f-strings `wait_for_function`.
2. `tests/e2e/test_class_crud.py:384` — 1x f-string.
3. `tests/e2e/test_class_section_alignment.py:266` — 1x `querySelector` chain.

F601 fix:
4. `tests/e2e/selectors.py:153` — remover linha duplicada de
   `rebalance_contribution_input`.

## Task 5: Verificar lint zero + hook pre-push

```bash
uv run task lint
uv run prek run --stage pre-push
```

Ambos zero. Se falhar, voltar para a task específica e corrigir.
