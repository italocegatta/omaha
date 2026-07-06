## Context

O repo omaha tem `task coverage` funcional (`uv run pytest --cov=src/omaha --cov-report=term-missing`) e `pytest-cov>=6.0` em deps, mas **não tem CI** — `ls -la .github/workflows/` retorna `No such file or directory`. Sem pipeline cabeado, regressões de cobertura passam invisíveis. Este slice introduz o workflow mínimo + amarra o cabo XML que o driver de coverage consome, sem fechar o "fail-under gate" (decisão separada — owner-driven).

Auditoria pré-slice (verificada via `bash`):
- `pytest-cov>=6.0` em `[project.dependencies]` de `pyproject.toml:31` (já em deps).
- Task `coverage` em `[tool.taskipy.tasks]` de `pyproject.toml:182` com `pytest --cov=src/omaha --cov-report=term-missing`.
- `reports/` directory existe no repo (vazio); `.gitignore` precisa checar se já cobre.
- Nenhum `.github/` directory existe — CI é genuinamente novo.

## Goals / Non-Goals

**Goals:**
- Workflow GitHub Actions mínimo que dá sinal verde/vermelho em PR.
- Integração de `pytest-cov` com o coverage driver via XML em `reports/coverage.xml`.
- Cache de `uv` para acelerar runs subsequentes.
- Manter `task coverage` como comando local útil (term-missing + XML coexistem).

**Non-Goals:**
- `--cov-fail-under` gate (threshold policy é decisão de owner — slice separada quando owner definir floor).
- E2E job no CI (Playwright + uvicorn-paralelo travam em runners compartilhados; out of scope).
- Audit integration job (`tests/audit_integration` é separado e roda em pipeline dedicado).
- Multi-OS matrix (Ubuntu only — fastest signal; Windows/macOS fica para slice futura se owner exigir).
- Cache de `node_modules` ou Playwright browsers — repo é Python-only.

## Decisions

### D-T02.1 — Único workflow `ci.yml`, não múltiplos por job

Criar **um** workflow (`ci.yml`) com múltiplos jobs (`lint`, `test-unit`, `test-integration`, `test-bdd`, `coverage`) em vez de workflows separados (`lint.yml`, `unit.yml`, etc.). Razão: GitHub Actions tem um único badge verde por workflow; consolidar em `ci.yml` dá uma única superfície de status no README. Trade-off: jobs compartilham o mesmo trigger matrix; aceitável porque todos os jobs compartilham a mesma trigger (`push`/`pull_request`).

**Alternativa considerada:** workflow por job com `workflow_call` reuseable. Rejeitada — overengineering para um projeto de uma equipe só; adiciona camada de indireção sem ganho.

### D-T02.2 — Coverage roda como job separado, não dentro de `test-unit`

`coverage` é um **job** distinto que depende de `test-unit` + `test-integration` via `needs:`. Razão: re-executar pytest dentro do coverage é caro (2x tempo), mas `pytest-cov` produz o XML durante a execução dos testes — re-rodar tudo separado permite cachear o resultado dos testes puros sem o `--cov` overhead. Trade-off: o coverage step re-roda `pytest --cov=src/omaha --cov-report=xml:reports/coverage.xml`; aceita-se o custo de uma duplicação para desacoplar os dois signals.

**Alternativa considerada:** rodar `--cov` dentro de `test-unit` direto. Rejeitada — polui o output do `task test-unit` local (que hoje é usado como gate de pre-push via prek) com o term-missing do cov, e força o report XML mesmo em dev local. Separar jobs preserva `task test-unit` puro.

### D-T02.3 — XML em `reports/coverage.xml`, não em `coverage.xml` na raiz

Artefato vai para `reports/coverage.xml` em vez de `coverage.xml` no repo root. Razão: `reports/` já existe no repo (vazio, aguardando uso); concentrar artefatos de cobertura em `reports/` deixa o root limpo. `actions/upload-artifact@v4` usa o path relativo ao runner working directory.

**Alternativa considerada:** usar `coverage.xml` na raiz. Rejeitada — padrões de repo (ver `DESIGN.md` section sobre "report directories") preferem subdirs nomeados.

### D-T02.4 — Sem `--cov-fail-under` neste slice

`pytest-cov` é invocado **sem** `--cov-fail-under=N`. O report XML é produzido e uploaded, mas a cobertura não bloqueia o merge. Razão: o floor de cobertura é uma decisão de política do owner (qual %? absoluto ou por módulo? aplicado em `src/omaha` inteiro ou só nos módulos críticos?). Sem decisão explícita do owner, adicionar `--cov-fail-under=80` é arbitrário. Documentado em `ci-coverage-pipeline` spec (requirement "Coverage is informational, not a fail-under gate") para sinalizar que isso é intencional.

**Alternativa considerada:** adicionar `--cov-fail-under=70` como floor conservador. Rejeitada — vai gerar fricção em PRs pequenos mesmo sem regressão real (cobertura pode oscilar 1-2% por ruído de arquivos novos).

### D-T02.5 — `addopts` em `[tool.pytest.ini_options]` ganha `--cov-report=xml:reports/coverage.xml`

Adicionar `addopts = "--cov=src/omaha --cov-report=xml:reports/coverage.xml"` ao bloco existente de `[tool.pytest.ini_options]`. Razão: garante que `pytest --cov` direto (sem `task coverage`) já produza o XML — útil em CI e em debug local. **Cuidado:** `task coverage` continua passando `--cov-report=term-missing` explicitamente, então o term-missing também sai (múltiplos `--cov-report` são cumulativos no `pytest-cov`). Trade-off: tests locais rápidos (`pytest -x tests/test_x.py`) agora rodam o cov machinery — overhead de ~1s. Aceitável.

**Alternativa considerada:** omitir `addopts` e depender exclusivamente do `task coverage`. Rejeitada — `pytest-cov` precisa de configuração em algum lugar canônico; `addopts` é o lugar padrão. Sem `addopts`, devs rodando `pytest` direto perdem o sinal de cobertura.

### D-T02.6 — `[tool.coverage.run]` com `source = ["src/omaha"]`

Adicionar bloco `[tool.coverage.run]` com `source = ["src/omaha"]`. Razão: sem isso, `pytest-cov` mede tudo (tests, scripts, alembic) e o número de cobertura fica distorcido para baixo (scripts de seed não são "código de produto"). `source` filtra para `src/omaha/` apenas.

**Alternativa considerada:** medir tudo. Rejeitada — alembic migrations e scripts têm cobertura estrutural diferente (não são unidades testáveis por `pytest`); inflar o denominador esconde regressões reais em `src/omaha`.

### D-T02.7 — Sem `fail_under` em `[tool.coverage.report]`

`[tool.coverage.report]` ganha `exclude_lines` (pragma `pragma: no cover`, `if __name__ == "__main__":`, etc.) mas **não** `fail_under`. Coerente com D-T02.4 — gate de threshold é decisão owner.

### D-T02.8 — `actions/setup-python@v5` com `cache: "uv"`

Setup usa `actions/setup-python@v5` com `python-version-file: ".python-version"` + `cache: "uv"`. Razão: pin Python 3.12 (matching `.python-version`); cache `uv` é built-in do setup-python v5 e reutiliza `~/.cache/uv` entre runs. Sem secrets necessários.

**Alternativa considerada:** `astral-sh/setup-uv@v4` action. Considerada equivalente mas adiciona uma action externa; manter `setup-python` reduz a superfície.

### D-T02.9 — Workflow não roda `task test-e2e`

Sem job para `tests/e2e/`. Razão: e2e usa Playwright + chromium + servidor dev paralelo; em runners compartilhados do GitHub Actions o paralelismo uvicorn+chromium trava intermitentemente (mesma classe de problema que `test_user_journey_rebalance.py` flake reportada em T01 follow-up). E2E permanece como gate local (`task test-e2e`).

## Risks / Trade-offs

- **Workflow adiciona tempo ao PR.** PRs vão rodar lint+unit+integration+BDD em CI; estimado 5-8 min por PR. Mitigação: cache de `uv` corta ~30s; jobs paralelos (lint || unit || integration) cortam mais; BDD serial é o gargalo. Se ficar lento, próximo slice paraleliza os 3 jobs de test e usa matrix.

- **Coverage re-roda pytest.** Coverage job duplica ~30-60s de pytest para gerar o XML. Mitigação: cache de `uv` + pytest incremental; aceitável dado o signal independente que dá. Alternativa seria rodar `--cov` em `test-integration` direto, mas isso polui o output.

- **BDD serial pode estourar timeout.** BDD suite roda serial (PRD §4.7) e tem 51 cenários; ~3-4 min. GitHub Actions default timeout é 6h, mas vale setar `timeout-minutes: 15` no job para falhar rápido se travar.

- **`pytest-cov` overhead em `pytest` direto.** Com `addopts` global, devs rodando `pytest -k foo tests/test_x.py` pagam ~1s extra. Mitigação: pouco relevante para o uso real (CI é o consumidor primário do XML); trade-off consciente.

- **Sem matrix multi-OS.** Só Ubuntu. Se owner quiser Windows/macOS, slice futura. Não bloqueia o objetivo deste slice.

- **Reports/ directory pode conflitar com outros artefatos.** Hoje vazio, mas se futuro slice usar `reports/` para algo além de coverage (e.g. relatórios de auditoria), convém subdividir (`reports/coverage/`). Documentado no spec como "concentra artefatos de cobertura em `reports/`"; se virar diretório multi-purpose, refator.

## Migration Plan

Linear e aditiva — sem migração de dados nem rollback elaborado.

1. Adicionar `.github/workflows/ci.yml` (workflow).
2. Editar `pyproject.toml`: adicionar `[tool.coverage.*]` e `addopts` em `[tool.pytest.ini_options]`.
3. Verificar `.gitignore` cobre `reports/` (e adicionar se faltar).
4. Push para branch `feat/t02-coverage-report-in-ci` — workflow dispara.
5. Confirmar primeiro run verde em Actions tab; baixar artifact `coverage-report` e validar que `reports/coverage.xml` é Cobertura-compatible (XML bem-formado, `<coverage line-rate=...>` presente).
6. Marcar slice `Applied` no roadmap após PR merge.

Rollback: deletar `.github/workflows/ci.yml` + reverter `pyproject.toml` + merge. Sem estado persistente.

## Open Questions

- **Q1 — Onde o driver de coverage vive?** GitHub tem 1st-party code coverage via `github/codeql-action`, mas exige o `coverage` action + token `GITHUB_TOKEN` com permissão `checks: write`. Para este slice, basta `actions/upload-artifact@v4` e o owner decide depois se pluga em algum driver externo (Codecov, Coveralls). Documentar no spec que o upload é genérico.
