## 1. Coverage configuration in pyproject.toml

- [x] 1.1 Add `[tool.coverage.run]` block with `source = ["src/omaha"]` to `pyproject.toml`
- [x] 1.2 Add `[tool.coverage.report]` block with `exclude_lines` for `pragma: no cover`, `if __name__ == "__main__":`, `raise NotImplementedError`, `if TYPE_CHECKING:`
- [x] 1.3 Add `addopts = "--cov=src/omaha --cov-report=xml:reports/coverage.xml"` to existing `[tool.pytest.ini_options]` block (do NOT remove existing `markers` / `addopts` content — extend only)
- [x] 1.4 Verify `task coverage` still produces term-missing + XML output locally (`uv run task coverage` then `ls reports/`)
- [x] 1.5 Verify `pytest --cov=src/omaha` (without `task coverage`) also produces XML (proves `addopts` global works)

## 2. .gitignore update

- [x] 2.1 Add `reports/coverage.xml` to `.gitignore` (preserve the existing `coverage/` entry — distinct entry for the new artifact path)
- [x] 2.2 Confirm `reports/` directory is committed empty — **resolved**: `reports/` already tracked with `.gitkeep` + `contrast_audit.html` committed; no action needed.

## 3. Workflow file creation

- [x] 3.1 Create `.github/workflows/ci.yml` with `name: ci`, triggers `push` (branches: `[main]`) + `pull_request` (branches: `[main]`)
- [x] 3.2 Add single job `lint` running `ruff check src tests alembic` + `ruff format --check src tests alembic` on `ubuntu-latest` with Python 3.12 (from `.python-version`) + `actions/setup-python@v5` with `cache: "uv"`
- [x] 3.3 Add job `test-unit` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-unit`
- [x] 3.4 Add job `test-integration` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-integration` with `timeout-minutes: 15`
- [x] 3.5 Add job `test-bdd` (needs: lint) running `uv sync --frozen --extra dev` then `uv run task test-bdd` with `timeout-minutes: 15`
- [x] 3.6 Add job `coverage` (needs: test-unit, test-integration) running `mkdir -p reports` then `uv run pytest -m "unit or integration" -q --ignore=tests/e2e/_disabled` (addopts provides `--cov` flags) then `actions/upload-artifact@v4` with name `coverage-report` and path `reports/coverage.xml`

## 4. Local verification

- [x] 4.1 Run `uv run task test-unit` locally — **271 passed / 2 skipped** (matches R04 baseline)
- [x] 4.2 Run `uv run task test-integration` locally — **369 passed / 2 skipped** (matches R02/R03/R04 baseline)
- [x] 4.3 Run `uv run task test-bdd` locally — **51 passed** (matches T05 baseline)
- [x] 4.4 Run `uv run task coverage` locally — **640 passed / 4 skipped / 92% line coverage**, `reports/coverage.xml` is Cobertura-compatible (`<coverage version=... line-rate="0.9163" ...>` + `<package name=...>` + `<class filename=...>` structure)
- [x] 4.5 Run `uv run pytest tests/test_seed.py::test_seed_creates_user_and_profiles --cov=src/omaha` (single test) — XML written, no term-missing bloat
- [x] 4.6 Run `ruff check src tests alembic` + `ruff format --check src tests alembic` — both green (All checks passed / 156 files already formatted)

## 5. CI verification — DEFERRED per owner 2026-07-06

Owner decision (`mensagem direta 2026-07-06`): "eu não quero usar o github actions por enquanto. como o desenvolvimento ainda está local, não precisamos dele agora. será util no futuro." — GH Actions fica como infraestrutura dormente no repo (workflow file commitado mas não exercitado). Slice fechada em estado "applied locally + workflow file in repo, CI verification deferred".

Tentativa de verificação executada antes da decisão de pausar (5 runs, registro preservado para reuso futuro):

- **Run 1 (commit `99fcc5c`):** falhou em `lint/Setup Python` — `actions/setup-python@v5` não aceita `cache: "uv"` (só pip/pipenv/poetry). Fix: trocar por `astral-sh/setup-uv@v4` + `actions/cache@v4` keyed em `hashFiles('uv.lock')`.
- **Run 2 (commit `d232f19`):** falhou em `lint/Setup Python` — `astral-sh/setup-uv@v4` não aceita `python-version-file`, só `python-version` (string). Fix: hardcode `python-version: "3.12"`.
- **Run 3 (commit `07c7f46`):** falhou em `lint/Install dependencies` — `uv sync --extra dev` retorna `Extra 'dev' is not defined`. As dev deps estão em `[dependency-groups]` (PEP 735), não em `[project.optional-dependencies]`. Fix: `--extra dev` → `--group dev`.
- **Run 4 (commit `e9df2d5`):** progresso: **lint ✓** + **test-unit ✓**. Falhou em `test-integration/Run integration tests` + `test-bdd/Run BDD tests` — CI runner não tem DB. 6 failed + 28 errors (`sqlite3.OperationalError: no such table: positions`). 1 BDD failure (`test_import_happy_auto_match[Ana]`, pre-existing flake). Fix: adicionar step `Reset database` (`uv run task db-reset`) nos 3 jobs.
- **Run 5 (commit `bac8b47`):** falhou em `Reset database` — `RuntimeError: SECRET_KEY is not set`. Fix: injetar `SECRET_KEY` + `ADMIN_PASSWORD` env vars direto no step (CI-only, não toca produção).

Estado pós-run 5: workflow rodando mas ainda não validado end-to-end. Owner decidiu pausar antes de prosseguir com nova rodada.

### Reactivation path (se owner retomar GH Actions no futuro)

(a) Re-rodar push para disparar nova Actions run — última versão do workflow file (commit `bac8b47`) deve passar com os fixes aplicados. (b) Investigar BDD flake `test_import_happy_auto_match[Ana]` separadamente (pre-existente, fora do escopo T02). (c) Considerar adicionar cache de `~/.cache/uv` como fallback se `actions/cache@v4` falhar. (d) Adicionar step explícito `actions/checkout@v4` (já existe) e garantir `permissions: contents: read` (já existe).

Não rodar `openspec-propose` para retomar — change archive preserva todos os artifacts. Mover folder de volta para `openspec/changes/t02-coverage-report-in-ci/` e validar.

- [ ] 5.1 Push branch — **pausado** (5 pushes já feitos direto em main durante tentativa de verificação)
- [ ] 5.2 Open PR — **N/A** (push direto em main, sem PR)
- [ ] 5.3 Confirm all 5 jobs pass — **pausado em run 5** (lint + test-unit verdes; test-integration + test-bdd + coverage pendentes pós db-reset/env fix)
- [ ] 5.4 Download `coverage-report` artifact — **não exercitado** (coverage job não chegou a rodar end-to-end)
- [ ] 5.5 Confirm workflow run time < 10 min — **não exercitado**

## 6. Roadmap + spec sync

- [x] 6.1 Update `openspec/roadmap.md` slice T02 block `Progress` — `Proposed: done 2026-07-06` + `Applying: done 2026-07-06` + `Applied: done 2026-07-06` + `Archived: pending` (arquivamento em curso)
- [x] 6.2 Verify `openspec validate t02-coverage-report-in-ci --json` returns `valid: true` — confirmed
- [x] 6.3 Verify `openspec list --specs` shows new capability `ci-coverage-pipeline` — confirmed (41 total / 0 errors)

## 7. Session summary — o que ficou no repo

**Mantido (úteis localmente, exercitam imediatamente):**
- `pyproject.toml`: `[tool.coverage.run]` + `[tool.coverage.report]` + `addopts` + `task coverage` reescrito (`-m "unit or integration"` + `--cov-report=xml:...`). `task coverage` roda em 3 min com 92% line coverage + `reports/coverage.xml` Cobertura-compatible.
- `.gitignore`: `reports/coverage.xml` + `reports/.coverage`. Defensivo, evita commits acidentais de artifacts de cov.

**Mantido (dormente, "útil no futuro" per owner):**
- `.github/workflows/ci.yml`: workflow file commitado. Não exercitado ativamente (owner pausou verificação). Servirá como ponto de partida quando GH Actions voltar a ser prioridade.

**Documentado mas não executado:**
- CI verification end-to-end (5 jobs todos verdes). 5 runs foram tentados, progresso registrado em §5 acima; última versão do workflow (commit `bac8b47`) tem os fixes acumulados mas não foi exercitada até o fim.