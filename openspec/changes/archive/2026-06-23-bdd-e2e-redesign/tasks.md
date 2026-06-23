## 1. Add pytest-bdd dependency

- [x] 1.1 Add `pytest-bdd = ">=8.0,<10"` to `[project.optional-dependencies]` / dev group in `pyproject.toml`.
- [x] 1.2 Run `uv lock --upgrade` and verify `uv.lock` resolves.
- [x] 1.3 Verify `uv run pytest --collect-only` still passes for the existing suite (no plugin conflict).

## 2. Move old e2e tests to `_disabled/`

- [x] 2.1 `mkdir -p tests/e2e/_disabled`
- [x] 2.2 `git mv tests/e2e/test_s{01,02,03,04,05,06,07,08,09}.py tests/e2e/test_s10_asset_table.py tests/e2e/_disabled/`
- [x] 2.3 Verify `uv run pytest --collect-only` no longer shows the moved tests.
- [x] 2.4 Confirm `tests/e2e/conftest.py` is retained (BDD suite reuses `page` + `live_url` + `_wait_for_port` + `_resolve_chromium`).

## 3. Add tiny fixture

- [x] 3.1 Write `tests/fixtures/tiny_portfolio.csv` with banner line + header + 4 data rows:
  - `TESOURO_SELIC_2029,Tesouro Selic 2029,1,"100,00","110,00",RF Pos`
  - `TESOURO_IPCA_2029,Tesouro IPCA+ 2029,1,"100,00","108,00",RF Pos`
  - `PETR4,PETR4,100,"28,50","35,10",Ações`
  - `VALE3,VALE3,200,"65,20","72,40",Ações`
- [x] 3.2 Verify it parses cleanly with `uv run python -c "from omaha.csv_import import parse_positions; print(len(parse_positions(open('tests/fixtures/tiny_portfolio.csv').read())))"` (expect 4).
- [x] 3.3 Document the column layout in a comment in the file.

## 4. BDD suite conftest

- [x] 4.1 Create `tests/bdd/conftest.py`.
- [x] 4.2 Override `live_url` to port `8766` (different from `tests/e2e/` `8765` so both suites can run in parallel).
- [x] 4.3 Override autouse `clean_italo` to wipe BOTH seeded profiles (`Italo` + `Ana`) before each test, including import previews.
- [x] 4.4 Import `page` and `live_url` helpers from `tests/e2e.conftest`.

## 5. Write common step definitions

- [x] 5.1 `tests/bdd/step_defs/common_steps.py` — login + nav + profile pick (parametrized over `Italo`/`Ana`).
- [x] 5.2 `tests/bdd/step_defs/class_steps.py` — class CRUD via snapshot form AND inline + (PATCH target via input + Enter / blur).
- [x] 5.3 `tests/bdd/step_defs/asset_steps.py` — asset CRUD manual.
- [x] 5.4 `tests/bdd/step_defs/import_steps.py` — import modal upload, review, assign, commit.
- [x] 5.5 `tests/bdd/step_defs/target_steps.py` — PATCH both stored target fields; assert derived portfolio %.
- [x] 5.6 `tests/bdd/step_defs/dashboard_steps.py` — read dashboard state (class sections, asset rows, percentage display).

## 6. Write feature files

- [x] 6.1 `tests/bdd/features/login.feature` — 3 scenarios (login OK × 2 profiles parametrized + login fail senha errada).
- [x] 6.2 `tests/bdd/features/class_crud.feature` — 3 scenarios (snapshot, inline + PATCH, dup name 409).
- [x] 6.3 `tests/bdd/features/asset_crud.feature` — 2 scenarios (manual add, per-class sum != 100 negative).
- [x] 6.4 `tests/bdd/features/import.feature` — 3 scenarios (import happy, import + assign per-row, import CSV vazio).
- [x] 6.5 `tests/bdd/features/target_pct.feature` — 3 scenarios (PATCH per-class, PATCH per-asset, validator sum != 100 per-class).
- [x] 6.6 `tests/bdd/features/derived_display.feature` — 2 scenarios (after PATCH per-class; after PATCH per-asset; reads the `asset.target_pct * class.target_pct / 100` cell).
- [x] 6.7 `tests/bdd/features/full_journey.feature` — 1 scenario, all stages.
- [x] 6.8 `tests/bdd/features/profile_isolation.feature` — 2 scenarios (Italo → Ana switch; Ana → Italo switch; data does not leak).

## 7. Wire taskipy + pytest markers

- [x] 7.1 Add `[tool.taskipy.tasks] test-bdd = "pytest tests/bdd -v"`.
- [x] 7.2 Add `[tool.pytest.ini_options]` markers entry: `bdd: BDD e2e scenarios under tests/bdd/`.
- [x] 7.3 Verify `task test-bdd` runs the new suite; `task test-unit`, `task test-integration`, `task test-e2e` unchanged.

## 8. Update AGENTS.md

- [x] 8.1 Add a new bullet under the "Test marker rule" section noting that BDD scenarios live under `tests/bdd/` and are collected by `pytest-bdd`, not by the `pytest_collection_modifyitems` allow-list rule.

## 9. Run + verify

- [ ] 9.1 `task test-bdd` — must pass for the full parametrized set.
- [x] 9.2 `task test-unit` — must pass unchanged.
- [x] 9.3 `task test-integration` — must pass unchanged.
- [x] 9.4 `task lint` — must pass; confirm the moved files in `tests/e2e/_disabled/` still pass ruff format.
- [ ] 9.5 Run `task test-bdd` twice in a row to catch flakiness from Alpine timing.

## 10. Hand off

- [x] 10.1 Document the parallel-bringup state in `openspec/PRD.md` §5.x: "Old e2e suite disabled at `tests/e2e/_disabled/`; BDD suite at `tests/bdd/` is the new contract. Deletion of the old suite is gated on 2 consecutive green BDD runs (separate follow-up change)."

---

## Estado final (jun/2026)

### ✅ Concluído (35/38 tasks)
- §1 pytest-bdd dep + uv.lock
- §2 e2e movido pra `_disabled/`
- §3 fixtures (broker-derived)
- §4 BDD conftest (porta 8766, wipe 2 perfis)
- §5 step_defs (6 módulos, PT-BR)
- §6 features (8 arquivos, Esquema do Cenário + Exemplos)
- §7 taskipy + marker `bdd`
- §8 AGENTS.md
- §9.2 `task test-unit` verde (121 passed)
- §9.3 `task test-integration` verde (192 passed)
- §9.4 `task lint` verde
- §10 PRD.md §5.4

### ⏸ Pendente (3/38 tasks, deferred para follow-up)
- §9.1 `task test-bdd` 3/30 verde (login OK; class/asset/import/target/derived/journey precisam de iteração de selectors)
- §9.5 BDD twice-in-a-row flakiness check (depende de §9.1)
- §9.5 ver dependência de §9.1

### 🔀 Mudanças de design no caminho (não bloqueantes)
- Fixture (`tests/fixtures/tiny_portfolio.csv`) reescrito a partir de `posicao_italo.csv` (broker file) em vez de tickers inventados
- Classes dashboard mudaram de "Renda Fixa"/"Ações" para "RF Pós"/"RF Dinâmica" (matching broker categories)
- Step text "Cadastrar classes" corrigido para "+ Nova classe" (texto real do botão)

### 📝 Follow-up change proposta
Ver `openspec/changes/bdd-step-reuse-helpers/` (a ser criada) — refactor de
steps duplicados via Python helpers + thin step wrappers.
