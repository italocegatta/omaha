# I04 — Limpar drift lint repo-wide

## What

Corrigir 25 diagnósticos `ruff` ativos no repositório que escaparam durante
slices anteriores. O hook `pre-push` foi regularizado em I03, mas os erros
preexistentes bloqueiam o gate de entrega.

## Why

Sem esta limpeza, cada push falha no hook `lint`. O preenchimento é
puramente mecânico: sem relaxamento de regras, sem mudança de configuração,
sem alteração de comportamento de produto.

Todos os 25 diagnósticos são auto-fixáveis ou requerem quebra de linha /
remoção de chave duplicada — zero impacto semântico.

## Non-goals

- Não alterar regras `ruff` em `pyproject.toml`.
- Não alterar comportamento de produto (runtime, template, modelo, rota).
- Não adicionar/remover testes.
- Não tocar arquivos fora da lista de 14 com erro ativo.
- Não renomear hooks `pre-push` ou tocar `prek.toml` / CI.

## Scope

### Included (25 diagnostics, 14 files)

| Categoria | Regra | Contagem | Arquivos |
|---|---|---|---|
| Import sorting | I001 | 6 | `tests/bdd/conftest.py`, `tests/bdd/step_defs/dashboard_steps.py`, `tests/bdd/step_defs/target_steps.py`, `tests/e2e/conftest.py`, `tests/test_real_csv_flow.py`, `tests/test_seed_from_csv.py` |
| Unused import | F401 | 1 | `src/omaha/rebalance/validation.py` (`import math`) |
| Line too long | E501 | 12 | `src/omaha/routes/assets.py` (3), `tests/bdd/step_defs/asset_steps.py` (1), `tests/bdd/step_defs/dashboard_steps.py` (1, 144→100), `tests/bdd/step_defs/target_steps.py` (3), `tests/e2e/test_asset_crud.py` (2), `tests/e2e/test_class_crud.py` (1), `tests/e2e/test_class_section_alignment.py` (1) |
| `setattr` → assignment | B010 | 3 | `tests/e2e/conftest.py` (linhas 138, 426, 427) |
| `try/except/pass` → `contextlib.suppress` | SIM105 | 1 | `tests/e2e/conftest.py` (linha 180) |
| Duplicate dict key | F601 | 1 | `tests/e2e/selectors.py` (chave `rebalance_contribution_input` duplicada) |
| Unused variable | F841 | 1 | `tests/e2e/test_asset_table.py` (`table_width`) |

### Excluded (explicit)

- Qualquer arquivo sem erro ativo no baseline.
- Regras `ruff` desabilitadas ou ausentes.
- `ruff.toml` / `pyproject.toml` config.
- CI pipelines, `prek.toml`, hooks.

## Verification

1. `uv run task lint` — zero erros.
2. `uv run prek run --stage pre-push` — hook `lint` passa.
