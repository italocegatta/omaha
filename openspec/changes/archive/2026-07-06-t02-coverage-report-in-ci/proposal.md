## Why

`task coverage` (`uv run pytest --cov=src/omaha --cov-report=term-missing`) já existe e o `pytest-cov>=6.0` já está em deps, mas o repo **não tem CI**: não existe `.github/workflows/`. Sem um pipeline cabeado, mudanças de cobertura ficam invisíveis — não há sinal verde/vermelho que avise quando um PR derruba linhas testadas. O slice amarra o cabo: introduz o workflow mínimo (lint + unit + integration + BDD + e2e stubs + coverage driver) e produz o artefato XML que o driver de coverage consome.

## What Changes

- Adiciona `.github/workflows/` com 1 workflow (`ci.yml`) que dispara em `push` (branches principais) e `pull_request` (qualquer PR contra main).
- Adiciona bloco `[tool.coverage.*]` + `--cov-report=xml:reports/coverage.xml` em `pyproject.toml` sob `[tool.pytest.ini_options]` para que `task coverage` produza o artefato XML consumível pelo driver.
- Workflow roda os gates na ordem: lint (ruff check + ruff format --check) → unit (`task test-unit`) → integration (`task test-integration`) → BDD (`task test-bdd`).
- Coverage roda apenas como report (`--cov-report=xml`), **não** como gate (`--cov-fail-under` fica de fora do escopo deste slice — quality gate de threshold é decisão separada).
- Cache de `uv` (`~/.cache/uv`) entre runs para acelerar.

## Capabilities

### New Capabilities

- `ci-coverage-pipeline`: descreve o workflow GitHub Actions do projeto (quais jobs rodam, em que ordem, quais tasks disparam) e a integração do `pytest-cov` com o driver de coverage via artefato XML.

### Modified Capabilities

_Nenhuma._ Este slice é tooling-only — não toca requirements de produto nem de runtime. Specs existentes (e.g. `prek-hooks`, `test-suite-quality`) descrevem gates locais; `ci-coverage-pipeline` descreve o equivalente em CI.

## Impact

- `.github/workflows/ci.yml` (novo) — workflow GitHub Actions.
- `pyproject.toml` — bloco `[tool.coverage.*]` (run_include, report.exclude_lines, etc.) + entry `[tool.pytest.ini_options]` ganha `addopts = "--cov=src/omaha --cov-report=xml:reports/coverage.xml"` que complementa (não substitui) o `term-missing` da task `coverage`.
- `reports/` — diretório de artefatos XML; já existe no repo mas está vazio (verificado via `ls -la`). Não precisa de `.gitkeep` — `pytest-cov` cria o arquivo se o diretório existir; CI usa `actions/upload-artifact@v4` para fazer upload.
- `tests/` — não tocado.
- Runtime (`src/omaha/**`) — não tocado.

Sem mudança de comportamento observável para o dev local além do XML extra em `reports/coverage.xml` quando rodar `task coverage`.
