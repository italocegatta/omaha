## Context

The Omaha platform currently has eleven Playwright e2e tests
(`tests/e2e/test_s01_inline_edit.py` through
`test_s10_asset_table.py`, plus `test_s06_full_journey.py`). They
drive a real chromium against a live uvicorn on
`127.0.0.1:8765` backed by `data/test_e2e.db`, and they share a
manual `_wipe_classes_for("Italo")` fixture that nukes the test
profile's classes + assets + import previews between tests. The
tests are individually correct but collectively miss two classes of
regressions:

1. **DOM-vs-store drift.** The modal-import select-binding fix
   (`openspec/changes/archive/2026-06-16-fix-import-modal-select-binding/`)
   was originally protected only by reading the Alpine store; the
   "select.value === suggestion" DOM check was added in a follow-up
   commit after a manual UI session surfaced the regression. A test
   that exercises the *user-visible flow* (`upload → click option →
   read the rendered <option selected>`) would have caught it
   earlier.
2. **Combinatorial gaps.** No single existing test walks the full
   `login → profile → 2 classes → 4 assets (imported) → patch
   class target → patch asset target → read derived portfolio %`.
   The closest, `test_s06_full_journey.py`, covers the import half
   but uses 5 classes + 48 tickers and never asserts on derived
   percentages. Refactors that touch class-target PATCH or
   asset-target PATCH have no full-flow regression guard.

Stakeholders: Italo (operator), Ana Livia (viewer), the dashboard
template, the CSV import route, and the target-pct PATCH routes.
External surfaces: none (BDD suite runs in CI, not against the
production stack).

## Goals / Non-Goals

**Goals:**

- Add a BDD e2e suite that captures the seven required scenario
  groups in PT-BR Gherkin and executes them in a real browser
  against the live uvicorn.
- Parametrize every stage-touching scenario over both seeded
  profiles (`Italo` and `Ana`) so per-profile data isolation is
  exercised in every flow.
- Disable (not delete) the old `tests/e2e/test_s*.py` files; the
  directory's shared `conftest.py` is preserved and reused.
- One full happy-path scenario walks every stage in order on a
  fresh DB; combinatorial coverage is achieved by combining stages
  across the seven scenario groups.
- PT-BR `.feature` files. Literal user-typed text appears in the
  scenario steps (e.g. "Quando eu preencho o campo Nome da classe
  com 'Renda Fixa'") so the BDD docstring doubles as a manual
  test script the operator can follow.
- Target assertions cover both stored PATCH endpoints
  (`PATCH /api/classes/{id}` for per-class-of-portfolio;
  `PATCH /api/assets/{id}` for per-asset-of-class) AND the derived
  display (`asset.target_pct * class.target_pct / 100`) on the
  dashboard.
- New suite runs in under 90 seconds for the full parametrized set.

**Non-Goals:**

- Deleting old e2e tests in this change. They are disabled and
  retained until the new suite is green for two consecutive runs;
  deletion is a follow-up change.
- Replacing the audit / contrast tooling under
  `tests/audit_integration/`. That tooling is not user-flow
  coverage; it is a static-analysis CLI. Out of scope.
- Replacing unit tests for models, parsers, validators. The
  test-suite-quality spec
  (`openspec/specs/test-suite-quality/spec.md`) covers those and is
  not in scope.
- Adding new `data-testid` attributes to the dashboard. The BDD
  step definitions reuse the existing selectors from the old
  `tests/e2e/test_s*.py` files (moved to `_disabled/`).
- Adding a `.feature` file in English. PT-BR matches the UI
  language and the user's request that the scenario text mirror
  what the operator types.
- Live-reload / dev-server-mode BDD runs. The suite drives the
  same `_wipe_classes_for("Italo")` + `_wipe_classes_for("Ana")`
  fixture the old suite uses, against the same per-test SQLite
  file. No production-stack coupling.
- Multi-profile parallel runs in CI. Parametrization is
  sequential over the two seeded profiles.

## Decisions

### Framework: pytest-bdd (Gherkin `.feature`)

**Why pytest-bdd:** the user asked for "anotação padrão de BDD",
which the project interprets as Gherkin. pytest-bdd gives PT-BR
`.feature` files with reusable step definitions, scenario outlines
for the dual-profile parametrization, and pytest-native fixtures
(reusing `live_url` + `page` from `tests/e2e/conftest.py`).
`pytest-bdd` is the lightest Gherkin-on-pytest option; the
alternatives (`pytest-bdd-ng`, `radish`, `behave`) either require
outside-pytest runners or carry a non-trivial plugin surface.

**Alternatives considered:**

- `pytest` docstring-style Given/When/Then (no plugin): keeps the
  dep footprint small, but loses the Gherkin parser, the
  outline-with-examples, and the step-reuse engine. The user
  specifically asked for "anotação padrão", which the project
  reads as "the artifact a non-coder reads". `.feature` files win.
- `behave`: requires a separate runner and does not interop with
  pytest fixtures. The shared `page` and `live_url` fixtures are
  too valuable to give up.
- No `.feature` files, only step-defined scenarios via
  `scenarios()`: pytest-bdd supports this, but loses the Gherkin
  surface that makes the suite diff-reviewable in PRs.

### Directory layout: `tests/bdd/`

**Why a new dir, not `tests/e2e/features/`:** the old `tests/e2e/`
suite has 11 files and a 280-line conftest. Co-locating BDD
features inside `tests/e2e/` would force every BDD step to dodge
the autouse `clean_italo` fixture (which wipes Italo's classes
between tests and is what the old suite relies on). A fresh
`tests/bdd/` tree gets its own conftest that overrides the wipe to
both seeded profiles and runs both wipes per test.

**Shared helpers stay in `tests/e2e/conftest.py`:** `_wait_for_port`
and `_resolve_chromium` are reused via `from tests.e2e.conftest
import page, live_url`. The BDD suite's own conftest only adds
profile-aware wipes, BDD-specific port, and the `pytest_bdd`
scenario glue.

### Old e2e tests: rename to `_disabled/`

**Why not `@pytest.mark.skip`:** the conftest autouse fixtures
(`clean_italo`) would still run, and the DB writes from a skipped
test could leak across the new BDD suite's tests via the shared
`data/test_e2e.db`. Moving to `tests/e2e/_disabled/` stops
pytest's default collection entirely; pytest only collects files
under `tests/e2e/` whose name matches `test_*.py` and whose path
starts with the rootdir.

**Why not delete:** the user explicitly asked to disable, not
delete, until the new suite is green. Deletion is a separate
follow-up change gated on the new suite passing twice.

### Tiny fixture: 4-row CSV at `tests/fixtures/tiny_portfolio.csv`

**Why a new file, not inline `io.StringIO`:** the import route
parses the upload by file path (multipart form-data → temp file on
disk), and the dashboard modal's `set_input_files` requires a real
path. Inline `io.StringIO` would couple the BDD step definition to
the parser's text-input contract and would diverge from the
production code path the family uses. A 200-byte fixture file is
trivial to maintain and matches the user's "2 classes × 2 assets"
constraint exactly.

**Header shape:** the fixture must parse cleanly through
`omaha.csv_import.parse_positions`. The existing
`tests/fixtures/sample_broker.csv` shows the header layout (banner
row + `Codigo,Ativo,Quantidade,Preco Medio,Preco Atual,Minha
Categoria`); the tiny fixture mirrors it with 4 data rows split 2
+ 2 by `Minha Categoria`. Categories chosen to be unmatched by the
newly created classes so the modal's manual-assignment path is
exercised.

### Parametrization: `@scenario` with shared `pytest.mark.parametrize`

**Why not Scenario Outline + Examples tables:** Gherkin's
Examples tables would force a 2× duplication of every scenario
body. pytest-bdd supports `@pytest.mark.parametrize` on the test
function the scenario is bound to, which is more readable in PR
diff and reuses the single canonical scenario body. The profile
name is injected via a `params` fixture that the steps read.

### Scenario inventory (one feature per group)

Each group lives in its own `.feature` file so a future change can
add scenarios without rewriting the others. Combinatorial coverage
is achieved by letting one scenario span multiple stages (e.g.
`full_journey.feature` walks login → profile → classes → import →
patch → derived display).

| Feature file              | Scenarios                                                         | Stages combined                          |
|---------------------------|-------------------------------------------------------------------|------------------------------------------|
| `login.feature`           | Login OK (×2 profiles), Login fail senha errada                   | login + profile pick                     |
| `class_crud.feature`      | Snapshot 2 classes, Inline add + PATCH target, Negative dup name | classes                                   |
| `asset_crud.feature`      | Manual add 2 ativos em cada classe, Negative sum != 100          | classes → assets manual                  |
| `import.feature`          | Import 4-row CSV happy, Import + assign, Import CSV vazio (neg)  | classes → import → assets                |
| `target_pct.feature`      | PATCH per-class, PATCH per-asset, Validação sum != 100 per-class | classes → assets → target PATCH          |
| `derived_display.feature` | Derivado portfolio % após PATCH em ambos stored                   | classes → assets → PATCH ambos → display |
| `full_journey.feature`    | Tudo em ordem (login → import → targets → derivado)              | all stages                               |
| `profile_isolation.feature` | Italo cria → Ana não vê; Ana cria → Italo não vê               | profile pick → classes → switch profile  |

The full-journey scenario is the single regression guard: if any
stage breaks, this scenario fails and the CI banner names the
stage by its step name.

### Sample scenario (full_journey.feature)

```gherkin
# language: pt-BR
Funcionalidade: Jornada completa do operador em uma única sessão
  Como Italo, operador da carteira
  Eu quero configurar 2 classes com 2 ativos cada via interface
  Para validar que o fluxo login → classe → ativo → alvo → derivado
  funciona de ponta a ponta

  Contexto:
    Dado que o servidor de testes do BDD está no ar
    E que o banco de dados de teste foi inicializado com a senha compartilhada
    E que os perfis "Italo" e "Ana" existem e estão sem classes e sem ativos

  Cenário: Jornada completa via modal de importação (perfil "Italo")
    Dado que estou na página "/login"
    Quando eu preencho o campo "username" com "Italo"
    E preencho o campo "password" com "test-password"
    E clico em "Entrar"
    Então estou na página "/profiles"
    Quando eu clico no botão do perfil "Italo"
    Então estou na página "/"
    E o dashboard mostra o nome do perfil "Italo"
    E o dashboard mostra a mensagem de estado vazio

    Quando eu clico em "Cadastrar classes"
    E preencho o campo "Nome da classe" com "Renda Fixa"
    E preencho o campo "Alocação alvo" com "60"
    E clico em "Adicionar linha"
    E preencho o campo "Nome da classe" com "Ações"
    E preencho o campo "Alocação alvo" com "40"
    E clico em "Salvar"
    Então o dashboard mostra 2 seções de classe
    E a seção "Renda Fixa" mostra "60%"
    E a seção "Ações" mostra "40%"

    Quando eu abro o modal "Importar posições"
    E seleciono o arquivo "tiny_portfolio.csv"
    E clico em "Enviar"
    Então o modal mostra 4 linhas não correspondidas
    Quando eu atribuo "Renda Fixa" ao ticker "TESOURO_SELIC_2029"
    E atribuo "Renda Fixa" ao ticker "TESOURO_IPCA_2029"
    E atribuo "Ações" ao ticker "PETR4"
    E atribuo "Ações" ao ticker "VALE3"
    E clico em "Confirmar importação"
    Então o dashboard mostra 4 linhas de ativos
    E a seção "Renda Fixa" contém 2 ativos
    E a seção "Ações" contém 2 ativos

    Quando eu clico no campo "Alocação dentro da classe" do ativo "TESOURO_SELIC_2029"
    E digito "60"
    E pressiono "Enter"
    Então a alocação salva do ativo "TESOURO_SELIC_2029" é "60%"
    E a alocação salva do ativo "TESOURO_IPCA_2029" é "40%"
    E a alocação salva do ativo "PETR4" é "50%"
    E a alocação salva do ativo "VALE3" é "50%"

    Quando eu clico no campo "Alocação alvo da carteira" da classe "Renda Fixa"
    E digito "70"
    E pressiono "Tab"
    Então a alocação salva da classe "Renda Fixa" é "70%"
    E a alocação salva da classe "Ações" é "30%"

    Então o derivado "TESOURO_SELIC_2029" na carteira é "42,0%"
    E o derivado "TESOURO_IPCA_2029" na carteira é "28,0%"
    E o derivado "PETR4" na carteira é "15,0%"
    E o derivado "VALE3" na carteira é "15,0%"
```

The literal user-typed text appears in every `Quando eu preencho...`
step, satisfying the user's "ver o texto de inserção de cada
informação na descrição do test".

## Risks / Trade-offs

- **[pytest-bdd version drift]** → pin in `pyproject.toml` and let
  `uv.lock` resolve. If the plugin is unmaintained upstream,
  fallback is to migrate to `pytest-bdd-ng` or docstring-style
  Given/When/Then; the Gherkin parser is the only hard dependency.
- **[Old e2e tests silently rot in `_disabled/`]** → the user
  explicitly chose this for a parallel-bringup window. The new
  suite is gated as "green for 2 consecutive runs" before the old
  is deleted (separate change). Lint still runs on the old files
  via the unchanged `prek.toml` ruff configuration; a follow-up
  cleanup change handles deletion.
- **[BDD suite flakiness from Alpine timing]** → the existing
  S04/S06 e2e suite has 2 pre-existing flaky tests
  (`openspec/PRD.md` §5.2); the new suite inherits the same Alpine
  `x-init $nextTick` pattern that
  `openspec/changes/archive/2026-06-16-fix-import-modal-select-binding/`
  fixed. Step definitions use `page.wait_for_function` with a
  generous timeout (10s for modal transitions, 15s for full
  upload → review transitions) and fall back to the
  `_debug_dump` helper from `tests/e2e/_disabled/test_s06_full_journey.py`
  on the first failure of any new scenario.
- **[Parametrization doubles scenario count]** → 8 scenarios × 2
  profiles = 16 top-level scenarios, ≈90s wall. Acceptable per the
  90s budget; if it exceeds, the dual-profile parametrization can
  be moved to a `pytest.mark.slow` marker and excluded from the
  default `task test-bdd` run.
- **[PT-BR `.feature` file encoding]** → Gherkin is UTF-8 and
  pytest-bdd parses PT-BR `Funcionalidade` / `Cenário` / `Dado` /
  `Quando` / `Então` keywords natively. No locale config needed.
- **`tests/e2e/conftest.py` import creates a `tests/e2e/_disabled`
  collection chain]** → pytest only collects `test_*.py` files
  matching its rootdir pattern. The new `tests/bdd/conftest.py`
  imports `from tests.e2e.conftest import page, live_url`; this
  reuses the helpers without re-running the autouse
  `clean_italo` fixture, because the import is at module scope and
  pytest-bdd scenarios do not pick up the autouse from a different
  rootdir.

## Open Questions

- **Disable vs delete vs `@pytest.mark.skip`:** resolved as
  `_disabled/` directory move. Confirm if a stub `pytest.ini`-level
  `--ignore=tests/e2e/_disabled` is preferred (cheaper to revert;
  same effect).
- **Per-scenario `pytest.mark.parametrize` vs Scenario Outline:**
  resolved as `parametrize`. Confirm if the team prefers the
  Gherkin-native outline for any specific scenario (e.g. login
  is a clean outline candidate since it has only one stage).
- **Full-journey target %, locale formatting:** the dashboard
  renders percentages as PT-BR locale ("42,0%"). The derived
  assertion uses the same formatting. If the rendering locale
  drifts to en-US ("42.0%") the assertion needs to track it.
  Out of scope for this change; flag if it surfaces in CI.
- **Cleanup of old e2e tests:** separate follow-up change after
  the new suite is green for 2 consecutive runs. Not in this
  change's tasks list.
