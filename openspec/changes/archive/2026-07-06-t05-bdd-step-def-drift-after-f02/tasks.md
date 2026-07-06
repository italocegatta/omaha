## 1. Alias map no step def

- [x] 1.1 Em `tests/bdd/step_defs/common_steps.py`, declarar
      `STEP_CLICK_ALIASES: dict[str, tuple[str, ...]]` no topo
      do módulo (acima de `click_button`) com as duas entradas
      descritas em `design.md` D-T05.1: `+ Nova classe` →
      `('[data-testid="empty-state-create-class"]',
      '[data-testid="new-class-modal-submit"]')` e `+ Novo
      ativo` → `('[data-testid="dashboard-add-asset-open"]',)`.
      Cada entrada com comment inline citando F02 como slice
      de origem (conforme requirement "Aliases are documented
      inline" do spec `bdd-step-def-aliases`).

- [x] 1.2 No corpo de `click_button` (após o signature atual,
      antes do loop de `candidates`), inserir o alias-lookup
      block: se `label in STEP_CLICK_ALIASES`, iterar a tupla
      com o mesmo two-phase visibility filter usado para os
      candidatos default. Se nenhum alias selector casar,
      cair para a sequência default (não substituir).

- [x] 1.3 Verificar que `click_button` continua importável
      (`python -c "from tests.bdd.step_defs.common_steps import click_button"`)
      e que o signature é byte-idêntico ao pré-T05 (mesma
      decorator `@when(parsers.parse('clico em "{label}"'))`,
      mesmo `def click_button(page: Page, label: str)`).

## 2. Reescrita do vocabulário Gherkin

- [x] 2.1 Em `tests/bdd/features/class_crud.feature:65`, trocar
      `clico em "+ Nova classe"` por `clico em "Nova Classe"`.

- [x] 2.2 Em `tests/bdd/features/profile_sharing.feature:17`,
      `:21`, `:37`, trocar `clico em "+ Nova classe"` por
      `clico em "Nova Classe"`. (3 step calls, mesmo padrão.)

- [x] 2.3 Conferir que `rg "\+ Nova classe" tests/bdd/` retorna
      0 hits após as 4 reescritas (sanity check: nenhum
      step call sobreviveu).

## 3. Verificação de aceite

- [x] 3.1 Rodar `task test-bdd` e confirmar: 47 pass + 4 fail
      (baseline R04 archive) → 49 pass + 2 skip. As 4 falhas
      que somem são exatamente os 4 step calls reescritos
      (verificar com `--collect-only` + `pytest -k "duplicate_class_name or profile_sharing"`).

- [x] 3.2 Rodar `task test-unit` e `task test-integration` —
      zero regressão (step def não toca módulos de produção).
      Baseline esperado: 271 pass / 2 skip unit; 369 pass /
      2 skip integration (mesmos números do R04 archive).

- [x] 3.3 Rodar `task test-e2e` — 42 pass / 5 fail pre-existentes
      (chromium stalls T01 follow-up) sem regressão T05
      (T05 não toca e2e).

- [x] 3.4 Rodar `task lint` (ruff + prek) — verde. T05 não
      adiciona imports novos (`dict` e `tuple` já são
      builtins), então a chance de regressão de lint é zero,
      mas o gate roda por convenção.

- [x] 3.5 Rodar `openspec validate t05-bdd-step-def-drift-after-f02
      --json` e confirmar `valid: true`. Resolver issues
      antes de arquivar.

## 4. Spec consolidation + delivery

- [x] 4.1 Sincronizar a spec `bdd-step-def-aliases` (1 ADDED
      requirement, 3 scenarios) em
      `openspec/specs/bdd-step-def-aliases/spec.md` via
      `openspec-sync-specs` (auto no archive, ou manual
      conforme necessário). Conferir que
      `openspec list --specs` mostra o id
      `bdd-step-def-aliases` com `requirementCount: 1`
      após o sync.

- [x] 4.2 Atualizar `openspec/roadmap.md` slice T05:
      `Status: Ready` → `Spec Proposed` (após este `apply`:
      `Applying` → `Applied` → `Archived`); mover entry para
      `## Compacted history` com summary do apply (4 step
      calls reescritos + alias map introduzido +
      49 pass / 2 skip BDD), data de archive, e referência
      ao `Post-implementation reality check` template.

- [x] 4.3 Adicionar entry em
      `## Post-implementation reality check` da roadmap
      (T05 block) após o archive: what changed from original
      plan, unexpected issues (provavelmente: nenhuma, mas
      documentar mesmo se vazio), follow-up needed.

- [x] 4.4 Rodar `refresh-for-test` skill se algum byte de
      runtime code foi tocado. Para T05 isso NÃO é o caso
      (apenas test-tooling + Gherkin), mas o smoke de
      `task test-bdd` já cumpre o gate de delivery (PRD §4.9
      é "para apply que toca runtime code"; T05 não toca,
      mas o smoke BDD é o equivalente para test-tooling).
