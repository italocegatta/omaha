# I04 — Limpar drift lint repo-wide — Design

## Approach

Fixa em duas passadas, depois verifica.

### Passada 1 — Auto-fix (mecânico)

```bash
uv run ruff check --fix src/ tests/
```

Cobre 10 diagnósticos:
- **I001** (6): reordena blocos de import.
- **F401** (1): remove `import math` morto.
- **B010** (3): converte `setattr(item, attr, val)` → `item.attr = val`.
- **SIM105** (1): converte `try/except TimeoutExpired/pass` → `with contextlib.suppress(...)`.
- **F841** (1): remove assignment morto de `table_width`.

Após `--fix`, rodar `uv run ruff check src/ tests/` para confirmar que só
restam E501 + F601.

### Passada 2 — Long lines (E501) + duplicate key (F601)

Quebrar 12 E501 mantendo legibilidade:

| Arquivo | Estratégia |
|---|---|
| `src/omaha/routes/assets.py:650` | f-string continua após `detail=`, quebra no operador `or` |
| `src/omaha/routes/assets.py:668` | f-string mesma estratégia, quebra no `.` do método chain |
| `src/omaha/routes/assets.py:673` | assinatura longa: quebra `Decimal \| None` em linhas separadas |
| `tests/bdd/step_defs/asset_steps.py:59` | f-string template: quebrar parâmetro `f"..."` após `,` |
| `tests/bdd/step_defs/dashboard_steps.py:107` | 144 chars: quebrar seletor concatenado em partes com `f"..."` |
| `tests/bdd/step_defs/target_steps.py:89,125,155` | template string longa: quebrar após `{` abertura, indentar argumento |
| `tests/e2e/test_asset_crud.py:153,225` | f-string com `querySelectorAll`: quebrar parâmetro após `,` |
| `tests/e2e/test_class_crud.py:384` | idem |
| `tests/e2e/test_class_section_alignment.py:266` | `querySelector` chain: quebrar no `.` |

F601: remover a linha 153 duplicada em `tests/e2e/selectors.py` (chave
`rebalance_contribution_input` já declarada; manter a primeira).

### Passada 3 — Verificação

```bash
uv run task lint
uv run prek run --stage pre-push
```

Ambos devem sair com exit code 0 sem erros.

## Anti-patterns

- Não usar `# noqa` para esconder erro — corrigir a fonte.
- Não quebrar string em metade de palavra-chave de query selector.
- Não reformatar linha que já está dentro do limite (overengineering).
- Não mover imports para fora do bloco `from __future__ import annotations`.
