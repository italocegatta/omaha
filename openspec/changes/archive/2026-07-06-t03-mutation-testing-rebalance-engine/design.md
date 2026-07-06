## Context

`task test-integration` (~369 pass) cobre o solver de rebalance em
~10–40 ms por cenário, mas cobertura de linha está estagnada em ~92%
(T02 baseline) e não distingue um teste robusto de um `assert result
is not None`. O solver é o domínio crítico (PRD §4.4 lista
explicitamente `auth` + `rebalance solver` + `cotação yfinance` como
os 3 onde cap 1 Applying vale). Especificamente, `solver.py` e
`validation.py` concentram o contrato:

- `solver.py:simulate_rebalance` — Implementação canônica do
  solver CVXPY (2-phase LP, RBRX11 B.1/B.2 fixes, policy cascade).
  Entrada: `setup` + `position` + `contribution` + `market_price_lookup`.
  Saída: `RebalancePlan` nativo (DataFrames 31/13 colunas + dict 28-key
  metrics). **Este é o arquivo que precisa de auditoria de assertions**
  — qualquer regresso aqui impacta o output do produto.
- `validation.py:_validate_rebalance_inputs` — Implementação dos
  11 checks de entrada (incluindo "soma de pesos-alvo = 100%" e
  limites de classe). Detém o invariant mais importante do produto
  (alocação total).
- `engine.py:cvxpy_solver` — Shim de tradução DataFrame →
  dataclass-list (v1 wire format). Exercitado apenas via
  `glue.run_rebalance` (rota `/api/rebalance`); não está no caminho
  dos unit tests.
- `glue.py:run_rebalance` — Orquestração completa do pipeline
  (DB → solver → wire format). Exercitada via TestClient
  (integration tests), não via unit tests.

Mutation testing insere falhas sintéticas (uma por vez) no código e
mede quantas dessas falhas a suíte de testes detecta ("kill rate").
Um mutation score de 80% numa codebase significa: para 100 falhas
sintéticas inseridas, 80 produzem pelo menos um teste vermelho. As
20 restantes são testes frouxos — exatamente o sinal que queremos
expor no solver.

`task coverage` já existe (T02), `task lint` existe, `task
mutation` ainda **não**. Nenhuma das ferramentas atuais
(`pytest-cov`, `taskipy`) cobre o nível "o teste **detecta** o
bug?" — só cobre "o teste **roda** o código?".

## Goals / Non-Goals

**Goals:**

- Disponibilizar mutation testing como ferramenta local via
  `task mutation`, scope restrito a `solver.py` + `validation.py`
  para o primeiro ciclo.
- Capturar uma baseline mutada inicial (`.mutmut-baseline`) que
  serve de referência para regressões futuras.
- Fornecer leitura humana do resultado via `task mutation-report`
  (HTML + summary textual).
- Cobrir a integração como spec leve (`rebalance-mutation-testing`)
  com requirements verificáveis — sem acoplar o score a um gate
  rígido automaticamente.

**Non-Goals:**

- Não consertar mutants sobreviventes identificados na baseline —
  vira slice de follow-up se/quando o time priorizar.
- Não mutar outros arquivos de `src/omaha/rebalance/` (solver,
  policy, postprocessing, builders, validation) nesse slice.
- Não promover o score a gate rígido (`fail_under`) — decisão
  owner-separada, mesmo padrão de T02 com `coverage fail_under`.
- Não adicionar `task mutation` ao workflow CI — timing
  proibitivo (10+ min para `engine.py`) sem decisão owner sobre
  paralelismo/cache.
- Não alterar suítes de teste existentes — mutation testing é
  camada meta sobre o que já existe.

## Decisions

### D-T03.1 — Mutator tool: `mutmut` (v3) sobre `cosmic-ray`

`mutmut>=3.0` foi escolhido sobre alternativas:

- **Alternativa A — `mutmut` (escolhida):** mutator line-based
  simples, escrito sobre `pytest`, integração com collection
  existente, cache via `.mutmut-cache/`. CLI `mutmut run` + `mutmut
  report` + `mutmut html` cobrem o ciclo completo. Pequeno footprint
  (1 dep transitiva de infra). Mutações: AOR (substituir ops
  aritméticos), ROR (substituir ops de comparação), COR (constantes),
  SOD (statement deletion), CRUD — suficiente para o escopo
  restrito.
- **Alternativa B — `cosmic-ray`:** mutator mais sofisticado
  (tracing bytecode, mutation operators avançados tipo MRO), mas
  config mais pesada (`python -m cosmic-ray new-config` + DB
  sqlite de harness) e overhead de tracing que não se justifica
  em 2 arquivos. Setup mais lento e curva de aprendizado maior.
- **Alternativa C — `mut.py`:** mutator baseado em AST,
  dependência de `python-Levenshtein` em algumas versões, sem
  cache entre runs, mutações menos granulares. Comunidade
  menor.

`mutmut` ganha por footprint, curva e integração nativa com
`pytest collection`. Trade-off aceito: `mutmut` é AST-based e não
captura mutações de bytecode que `cosmic-ray` pegaria (e.g.
constant folding tricks). Para o domínio isolado (2 arquivos de
solver), o trade-off é favorável.

### D-T03.2 — Sem `fail_under` rígido na primeira execução

Padrão alinhado com `task coverage` em T02 (que também ficou sem
`fail_under`). Razões:

1. O primeiro `task mutation` numa codebase nunca-exercitada
   produz mutation score imprevisível — estabelecer a baseline é
   parte do output do slice, não pré-requisito dele.
2. Gate rígido num primeiro slice cria pressão artificial para
   "passar agora" e mata a utilidade do tool (o time conserta
   mutants para green em vez de consertar testes frouxos).
3. Decisão de gate é owner-separada: requer entender a
   distribuição survived/killed por região do código, saber
   quais mutants sobreviventes são "test gap" vs "mutant
   equivalente" (mutação que produz mesmo output que o original).
4. T02 documenta o mesmo princípio para `coverage`: manter a
   ferramenta como signal, gate é decisão posterior.

Sinal é exposto via `task mutation-report`. Promoção a gate fica
para slice posterior se owner decidir.

### D-T03.3 — Scope: 2 arquivos isolados, não o pacote inteiro

`only_mutate` é `["src/omaha/rebalance/solver.py",
"src/omaha/rebalance/validation.py"]` (configuração em
`[tool.mutmut]` no `pyproject.toml`, não CLI flag — mutmut3
não expõe `--paths-to-mutate`; usa só config). Razões:

- `solver.py` (21K) + `validation.py` (8.4K) concentram a
  lógica do contrato "soma 100% / class limits / trade flags".
- Ambos são cobertos pela suíte **unit** em
  `tests/test_rebalance_*.py` (especificamente
  `test_rebalance_solver.py`, `test_rebalance_engine_regression.py`,
  `test_rebalance_validation.py`, `test_rebalance_constants.py`,
  `test_rebalance_policy.py`, `test_rebalance_postprocessing.py`),
  o que permite que `pytest_add_cli_args_test_selection` scope
  a stats phase sem depender de TestClient/DB integration.
- Outros arquivos (`engine.py`, `glue.py`, `policy.py`,
  `postprocessing.py`, `builders.py`) são ou shims dependentes
  de TestClient+DB (glue) ou auxiliares (`builders`) — adicionar
  esses módulos num primeiro slice exige extender
  `pytest_add_cli_args_test_selection` para a suíte integration,
  o que requer Alembic + TestClient setup em `mutants/` cwd
  (workaround do mutmut3.x não suporta limpo).
- Escopo restrito mantém `task mutation` em tempo razoável
  (~5–15 min para `solver.py` + `validation.py`), compatível
  com iteração local.
- Extensão para outros arquivos fica como decisão futura; se
  owner quiser cobrir o solver inteiro, vira nova slice com
  baseline própria.

**Note (path correction):** o slice text original da roadmap
mencionava `engine.py` + `data_bridges.py`, mas o package
rebalance atualmente expõe `solver.py` + `validation.py` como
o par canônico. `engine.py:cvxpy_solver` é só um shim de
tradução DataFrame → dataclass-list (v1 wire format) que só é
chamado via `glue.run_rebalance`; `glue.run_rebalance` é
chamado via TestClient. Os unit tests que cobrem o CVXPY LP
chamam `simulate_rebalance` (de `solver.py`) diretamente, então
mutações ali são detectáveis. **Escolha preserva a semântica
do slice text** (auditoria estrutural do solver + sua bridge
de validação) — apenas atualiza os paths concretos para os que
realmente têm cobertura de unit tests pronta para trampoline.

### D-T03.4 — `--tests-dir=tests` (não `--runner=pytest`)

`mutmut3` aceita `--tests-dir=<dir>` que mapeia para `--rootdir=<dir>`
do `pytest collection`. Apontar para `tests/` (raiz) é mais
permissivo que passar `--runner="pytest -xvs"` e respeita a
collection global do projeto (markers, fixtures compartilhadas,
`_INTEGRATION_PREFIXES`). Trade-off: rodar mutações executa a
collection completa do `tests/`, o que é mais lento que um
subconjunto — mas é também o setup mais fiel à realidade
(qualquer teste novo no repo passa a ser candidato natural a
"kill this mutant").

### D-T03.5 — `.mutmut-baseline` capturado em arquivo committed

`task mutation-baseline` roda `task mutation`, canaliza stdout para
`.mutmut-baseline` (formato textual legível gerado por `mutmut
results` + parse), e commita o arquivo. Futuras execuções podem
comparar contra esse baseline via `diff .mutmut-baseline
.mutmut-cache/mutmut-report.txt` ou equivalente. Não é um gate
automático — é só uma referência versionada.

Mesmo padrão do `.pre-commit-config.yaml` ser commitado: artefato
de ferramenta é versionado para reprodutibilidade.

### D-T03.6 — Output em `.mutmut-cache/` (gitignored)

`mutmut` cria `.mutmut-cache/` automaticamente. `.gitignore`
acrescenta esse path + `mutmut-*.json`. Sem `.gitkeep` — a
existência do diretório é efeito da primeira execução do
`task mutation`. Runtime intacto (não há backend que dependa
do diretório existir de antemão).

### D-T03.7 — Sem extensão ao CI existente

Workflow `.github/workflows/ci.yml` (T02) **não** ganha job de
mutation. Razões:

1. Mutation testing é O(mutants × test_time). Para 2 arquivos
   com ~150–300 mutants cada e `tests/test-integration` em ~30s,
   tempo de execução estimado: 150–300 min por run de CI.
2. Não há cache de mutants válidos entre runs — cada push
   rebusca todos.
3. Paralelismo via matrix seria possível, mas adiciona
   complexidade que não se justifica para um signal sem gate
   (D-T03.2).

Slice entrega a ferramenta local. Integração CI é decisão
owner-separada quando a baseline estiver estável e o time
quiser promover o score a gate.

## Risks / Trade-offs

- **Risk — baseline inicial ruim desencoraja uso** → Mitigation:
  `task mutation-report` produz HTML navegável por arquivo/função;
  baseline inclui contagem survived/killed/no_tests com links
  diretos. O time consegue ler o report sem entender a CLI do
  `mutmut`. README-like summary aparece no fim do baseline file.

- **Risk — `mutmut3` ainda em churn upstream (2024–2025)** →
  Mitigation: pin `mutmut>=3.0,<4` em `pyproject.toml`. Sem
  breaking changes aceitas sem revisão manual. Se a major v4
  quebrar, slice de migração separado.

- **Risk — primeira execução lenta gera atrito** → Mitigation:
  documentar tempo esperado no `task mutation` help text + ADR
  no roadmap slice (já está nas Notes). Time pode rodar em
  background durante outras tarefas.

- **Risk — suíte de testes tem `assert result is not None` frouxo**
  → Mitigation: **esse é o ponto**. Se a baseline revelar
  mutants sobreviventes, isso vira input para follow-up slice
  (provável `R` ou `T` separado que adiciona assertion tightness
  baseado no report do `mutmut`). T03 entrega o sinal, o fix
  fica fora.

- **Trade-off — mutmut AST vs cosmic-ray bytecode** → aceito em
  D-T03.1. Para o domínio isolado, AST é suficiente. Se
  futuramente precisarmos de mutações a nível de constante folding
  ou bytecode optimization, slice separado pode trocar para
  `cosmic-ray`.

## Migration Plan

Não há migração de dado ou dependência de runtime. O slice é
puramente aditivo:

1. **`pyproject.toml`:** adicionar `mutmut>=3.0,<4` ao
   `[dependency-groups].dev` (mesmo grupo que tem `pytest`,
   `pytest-cov`, `prek`, etc.). Adicionar 3 entries em
   `[tool.taskipy.tasks]`.
2. **`.gitignore`:** acrescen `.mutmut-cache/` e `mutmut-*.json`.
3. **Primeira execução local:** `task mutation` roda ~5–15 min,
   gera `.mutmut-cache/`. `task mutation-baseline` captura a
   baseline em `.mutmut-baseline`. Baseline é committed no
   mesmo PR.
4. **Rollback:** se o tool tiver problema imediato,
   `uv remove mutmut` + reverter entries de `[tool.taskipy.tasks]`
   + reverter `.gitignore`. Nenhum teste, migration ou runtime
   tocado — rollback é literalmente remover dep + 3 lines de
   task config.

## Open Questions

- **Q1 — Mutant scoring: percentagem killed/total ou killed/(killed+survived)?**
  `mutmut` reporta ambos. Spec usa `killed / (killed + survived)`
  por ser o número mais útil (exclui `no_tests`, que é falso
  negativo do harness). Decisão owner se preferir o outro.
  Resposta proposta: documentação no baseline file explica os
  três números e sua leitura.
