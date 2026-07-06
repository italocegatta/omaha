## Why

`task test-integration` roda contra `src/omaha/rebalance/` (engine,
solver, glue) e fecha em ~10–40 ms com testes que verificam
invariantes grossos (soma 100%, residual ≥ 0, status optimal). Cobertura
de linha está em ~92% (T02 baseline), mas cobertura de linha não
garante que o teste distingue um bug real de um `pass` — um teste que
afirma `result is not None` passa tanto para a função correta quanto
para uma função quebrada. O solver é o domínio crítico do produto
(PRD §4.4: CVXPY 2-phase LP, RBRX11 B.1/B.2 fixes, trade-control flags,
policy cascade) e é onde um regresso silencioso tem custo maior. O
slice adiciona **mutation testing** como gate estrutural: introduz
falhas sintéticas no código e exige que a suíte de testes quebre para
cada uma. Testes que sobrevivem a todas as mutações são sinal de
asserção frouxa (mesmo padrão que `unit-test-effectiveness` ataca em
outro nível).

## What Changes

- **Adiciona `mutmut` (v3) como dev-dependency** em `pyproject.toml`
  (grupo `dev`). `mutmut3` é a forma atual do projeto upstream —
  pytest-cov já está no mesmo grupo, então a adição cabe no padrão
  existente.
- **Adiciona bloco `[tool.mutmut]` em `pyproject.toml`** que
  configura `source_paths`, `only_mutate` (escopo = 2 arquivos:
  `solver.py` + `validation.py`), `also_copy` (dependências que
  mutmut precisa copiar para `mutants/` no momento do run — sem
  isso, a collection pytest falha em
  `tests/scripts/test_reset_both_profiles.py` que faz
  `from scripts.reset_both_profiles import main`). Config via
  pyproject é a forma idiomática do mutmut3 — não usa CLI flags.
- **`pytest_add_cli_args_test_selection`** na config restringe
  a stats phase aos testes **unit** de rebalance
  (`tests/test_rebalance_constants.py` + `engine_regression.py` +
  `policy.py` + `postprocessing.py` + `solver.py` +
  `validation.py`). Esses testes cobrem o CVXPY LP e os 11
  checks de entrada sem depender de TestClient/DB, o que
  permite rodar mutmut's trampoline sem precisar de Alembic +
  TestClient setup no `mutants/` cwd.
- **Adiciona `task mutation`** que invoca `uv run mutmut run` (mutmut
  lê o bloco `[tool.mutmut]` no startup). Output em `mutants/<path>.meta`
  JSON files.
- **Adiciona `task mutation-report`** que roda
  `python -m scripts.mutation_report` — agrega os `.meta` JSONs em
  counts por status + `killed_share`. Não roda mutation — só lê o
  cache.
- **Adiciona `task mutation-baseline`** que escreve `.mutmut-baseline`
  (arquivo versionado) com 7 linhas (`killed=`, `survived=`,
  `no_tests=`, `timeout=`, `skipped=`, `killed_share=`,
  `generated_at=` UTC ISO-8601). Comparação futura via `diff`.
- **Limiar de aceitação registrado no roadmap** (não como `fail_under`
  no gate ainda — ver D-T03.2): qualquer regressão de mutation
  score é discutida caso a caso (não é gate rígido — é sinal).
- **Sem mudança em `src/omaha/rebalance/`**: o slice não conserta
  mutants sobreviventes. Se a execução inicial revelar mutants que o
  time reconhece como "test gap", isso vira follow-up slice (provável
  prefixo `R` ou `T`), não entra no T03. Mutation testing é infra —
  não é refator.
- **Sem migration, sem mudança em runtime.** `only_mutate` isola o
  mutator a dois arquivos. CI/coverage (`task coverage`) e rotation
  engine continuam intocados.

## Capabilities

### New Capabilities

- `rebalance-mutation-testing`: define como o projeto usa mutation
  testing como ferramenta de auditoria estrutural do solver. Cobre
  o escopo de arquivos mutados (apenas
  `src/omaha/rebalance/{solver,validation}.py`, sem alastrar
  para o resto do pacote), a forma do harness (`task mutation` +
  `task mutation-report` + `task mutation-baseline`), e o signal
  que ele produz (mutation score = killed / (killed + survived),
  sem `no_tests` no denominador). **Não** torna o mutation score
  um gate rígido — explicita a baseline como sinal e a decisão de
  promoção a gate como owner-separada (a la `fail_under` em
  coverage, que T02 também deixou de fora).

### Modified Capabilities

_Nenhuma._ O slice não toca requirement-level de `rebalance-engine`,
`rebalance-data-bridges`, `unit-test-effectiveness` nem
`test-suite-quality`. Mutation testing é uma camada meta sobre
esses testes, não os modifica.

## Impact

**Arquivos tocados (6):**

- `pyproject.toml` — `dev` dependency group ganha `mutmut>=3.0,<4`;
  `[tool.taskipy.tasks]` ganha 3 entries (`mutation`,
  `mutation-report`, `mutation-baseline`); `[tool.mutmut]` block
  novo (`source_paths`, `only_mutate`, `also_copy`).
- `.gitignore` — acrescen `.mutmut-cache/` e `mutmut-*.json` (outputs
  do runner; cache é o estado mutado entre runs).
- `scripts/mutation_report.py` (novo) — agrega `.meta` JSONs em
  counts + killed_share.
- `scripts/mutation_baseline.py` (novo) — escreve `.mutmut-baseline`.
- `openspec/specs/rebalance-mutation-testing/spec.md` (novo) — 4
  ADDED requirements.
- `openspec/roadmap.md` — slice status
  `Ready` → `Spec Proposed` → `Applying` → `Applied` → `Archived`
  + entry no compacted history.

**Arquivo NÃO existe (`data_bridges.py`):** o slice text da roadmap
mencionava `engine.py` + `data_bridges.py`, mas o package
rebalance atualmente tem `solver.py` (CVXPY LP) + `validation.py`
(11-input-check, detém "soma 100%") como o par canônico para
mutation testing. `engine.py:cvxpy_solver` é só um shim de
tradução DataFrame → dataclass-list que só é exercitado via
TestClient+DB (rota `/api/rebalance`); `glue.py:run_rebalance`
também é TestClient-only. Os unit tests em
`tests/test_rebalance_*.py` cobrem diretamente `solver.py` (via
`simulate_rebalance`) e `validation.py` (via
`_validate_rebalance_inputs`) sem precisar de DB. **Escolha final
do escopo: `solver.py` + `validation.py`** — preserva a semântica
do slice text (auditoria estrutural do CVXPY solver + sua bridge
de validação) e dá ao trampoline do mutmut3 cobertura via
unit tests.

**Fora de escopo (registrado para não esticar o slice):**

- Conserto de mutants sobreviventes identificados na baseline —
  vira follow-up R/T slice separado. O T03 entrega o sinal, não a
  correção.
- Mutação de `src/omaha/rebalance/{engine,glue,policy,
  postprocessing,builders}.py`. Esses módulos cobrem lógica
  complementar e mereceriam uma slice dedicada se o time decidir
  ampliar (engine + glue precisam do setup TestClient+DB; os
  demais são auxiliares ao solver central).
- Promoção de mutation score a gate (`fail_under`). Decisão
  owner-separada, mesmo padrão T02.
- CI integration do `task mutation`. Mutation testing é lento
  (10+ minutos para `solver.py`); não cabe no workflow `ci.yml`
  de T02 sem decisão owner sobre paralelismo/cache de mutants.

**Verificação de aceite:**

- `task mutation` roda verde (zero erro de harness — mutant-id
  counter incrementa, killed/survived counters reportam números,
  não crash de pytest collection).
- `task mutation-baseline` produz arquivo `.mutmut-baseline`
  legível.
- `task test-unit` + `task test-integration` + `task test-bdd` +
  `task coverage` sem regressão.
- `task lint` (ruff + prek) verde — `pyproject.toml` parseável.
- `openspec validate t03-mutation-testing-rebalance-engine`
  retorna `valid: true`.

**Critical-area mark:** sim (PRD §4.4 + roadmap §Parallelism). O
slice **instala infra de auditoria** sobre um domínio crítico —
não roda o solver nem toca `solver.py` / `validation.py` em
runtime. Não há risco de quebrar invariantes do solver. Respeita
cap 1 Applying (T03 é o único slice T em Applying no momento).
