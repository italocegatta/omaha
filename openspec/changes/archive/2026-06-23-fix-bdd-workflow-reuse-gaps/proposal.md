## Why

Retrospectiva da change `bdd-workflow-reuse-helpers`
(archive/2026-06-23) encontrou 12 gaps entre o que a change
prometeu e o que ficou em código. Esta change fecha os 10
gaps corrigíveis hoje (1-10). Os 2 restantes (#11-12 —
racing Alpine em `create_two_default_classes` /
`add_one_asset`) ficam para spike separado porque o suite
passa hoje e exigiria mexer nos templates `dashboard.html`
(fora do escopo "BDD only" desta change).

Gaps em ordem de severidade:

- **#1 — Cenário órfão (funcional).** A scenario
  `class_crud.feature::Inline add + PATCH class target` está
  definida no `.feature` (linhas 48-55) mas não tem
  `@scenario(...)` em `test_scenarios.py`. Suite roda 17
  testes em vez de 18 — regressão silenciosa introduzida
  durante a refatoração.
- **#2 — `switch_profile` é dead code (auto-violação do
  spec).** Workflow + wrapper + carve-out regex
  `troquei para o perfil` existem para um caso que nunca
  materializou: 0 cenários usam. `profile_isolation.feature`
  usa steps inline (carve-out). Spec exige "≥2 cenários com
  tendência de crescimento"; 0 < 2.
- **#3 — `create_four_assets` viola o spec (1 caller só).**
  Usado por exatamente 1 cenário
  (`asset_crud.feature::Manual add 4 ativos não-igual por
  classe`). Spec diz ≥2; 1 < 2. Decisão: deletar o
  workflow + wrapper, inlinear as 4 chamadas
  `_w_one_asset` no único caller (ganha 2 linhas Gherkin
  no único cenário que perde o wrapper, mas elimina god
  workflow órfão).
- **#4 — AGENTS.md contradiz spec/README.** Spec, README,
  proposal dizem "≥2 cenários com tendência". AGENTS.md
  linha 203 adiciona "≥3 cenários totais" — não está em
  nenhum outro artefato.
- **#5 — design.md §Decisão 1 stale.** Mostra código do
  snapshot editor (`POST /classes`) que foi retirado pelo
  S02/T07 (endpoint agora 302 → /). Implementação real é
  loop de `create_one_class` (inline add form). Docstring
  em `_workflows.py:206-211` foi atualizada, design.md não.
- **#6 — design.md §Decisão 5 + proposal "8 steps" é
  enganoso.** Refatoração não removeu as 8 ações — escondeu
  atrás de 1 wrapper. Redução de 38.2% nas linhas Gherkin
  veio do encolhimento do `.feature`, não da remoção de
  trabalho de UI.
- **#7 — `add_one_asset` docstring/design assumption
  drift.** Proposta §O que muda descreve como "per-class
  `+ Ativo` button". Implementação real: 1 botão global
  (`dashboard-add-asset-open`) no topo de Distribuição +
  `<select>` picker de classe. Docstring em
  `_workflows.py:245-250` está correta, design.md não.
- **#8 — `_w_default_classes_pct` hardcoded a "RF Pós" e
  "RF Dinâmica".** Step text literal; só `p1`/`p2`
  parametrizados. Wrapper não reusa para cenários com
  nomes diferentes. Dataclass `ClassSpec` é geral,
  wrapper não.
- **#9 — `_w_four_assets` sem variante parametrizada.** Se
  não deletarmos (#3), falta `_w_four_assets_pct` para
  simetria com o caso de 2 classes. Decisão casada com #3.
- **#10 — `test_carve_out_files_use_inline_steps` regex
  hardcoded.** `WRAPPER_REGEXES` lista só 2 entradas
  manuais. Se nova workflow com carve-out for adicionada,
  teste passa vacuosamente a menos que alguém atualize o
  dict manualmente.

Gaps #11-12 (Alpine timing em `create_one_class` loop
state coupling + `add_one_asset` modal-init race) ficam
fora do escopo — suite passa, contract tests não cobrem,
e corrigir exigiria mexer em `dashboard.html` (template
change, não BDD-only).

## What Changes

- Re-bind cenário órfão em `test_scenarios.py`.
- Deletar `switch_profile` workflow + wrapper + entrada
  `WRAPPER_REGEXES` + regex carve-out da documentação.
- Deletar `create_four_assets` workflow + wrapper;
  inlinear 4 chamadas `_w_one_asset` no único caller.
- Sincronizar texto do threshold em AGENTS.md com
  spec/README/proposal.
- Reescrever §Decisão 1 do design.md para refletir o
  loop inline-add (snapshot editor retirado).
- Reescrever §Decisão 5 + proposal §O que muda para
  distinguir "redução de linhas Gherkin" de "redução de
  trabalho de UI".
- Atualizar §Decisão 1 do design.md para descrever
  corretamente `add_one_asset` (botão global + select
  picker, não per-class).
- Renomear `_w_default_classes_pct` para
  `_w_rf_pos_rf_dinamica_pct` (deixar claro que é
  hardcoded a esses 2 nomes). Documentar alternativa via
  `create_two_default_classes([ClassSpec(...)])` direto
  no workflow para nomes custom.
- Remover `_w_four_assets` (junto com #3) — não há
  variante parametrizada a adicionar.
- Refatorar `test_carve_out_files_use_inline_steps` para
  derivar `WRAPPER_REGEXES` de um marker attribute nas
  próprias workflows (`@carve_out(features=[...,
  regex=...])`) em vez de dict hardcoded.
- Atualizar `tests/bdd/README.md` tabela de workflows
  (remover `switch_profile` e `create_four_assets`).
- Atualizar capability `bdd-workflow-reuse` (delta em
  MODIFIED Requirements) para refletir a remoção e a
  nova estratégia de marker-based carve-out.

## Capabilities

### New Capabilities

(nenhuma)

### Modified Capabilities

- `bdd-workflow-reuse`: remove `switch_profile` workflow e
  remove `create_four_assets` workflow (cada um com 0-1
  callers — auto-violação da regra ≥2 cenários do próprio
  spec). Adota marker-based carve-out enforcement
  (workflows anotadas com `@carve_out(regex=, files=)`)
  em vez de dict hardcoded no contract test. Threshold
  rule unificada como "≥2 cenários com tendência de
  crescimento" (sem qualificação extra "≥3 cenários
  totais").

## Impact

- `tests/bdd/step_defs/_workflows.py` — remove
  `switch_profile` (~25 linhas) e `create_four_assets`
  (~30 linhas). Sobra: 4 workflows + 2 dataclasses + 2
  constantes.
- `tests/bdd/step_defs/common_steps.py` — remove
  `_w_switched_profile` wrapper (~5 linhas).
- `tests/bdd/step_defs/asset_steps.py` — remove
  `_w_four_assets` wrapper (~5 linhas).
- `tests/bdd/step_defs/class_steps.py` — renomeia
  `_w_default_classes_pct` para `_w_rf_pos_rf_dinamica_pct`
  + atualiza decorator regex.
- `tests/bdd/test_workflow_contracts.py` — refatora
  `WRAPPER_REGEXES` para ser derivado de marker attribute
  em cada workflow com carve-out.
- `tests/bdd/features/asset_crud.feature` — único caller
  de `_w_four_assets` ganha 4 linhas (4× `_w_one_asset`).
- `tests/bdd/features/login.feature`,
  `tests/bdd/features/profile_isolation.feature` —
  inalterados (continuam inline por design do carve-out).
- `tests/bdd/test_scenarios.py` — adiciona `@scenario(...)`
  para `class_crud.feature::Inline add + PATCH class
  target`.
- `tests/bdd/README.md` — remove linhas de
  `switch_profile` e `create_four_assets` na tabela;
  adiciona nota sobre marker-based carve-out.
- `AGENTS.md` — ajusta linha 203 para alinhar com
  spec/README/proposal.
- `openspec/changes/archive/2026-06-23-bdd-workflow-reuse-helpers/design.md`
  — corrigido "in-place" (read-only artefato histórico,
  mas o conteúdo referenciado no spec da capability
  precisa refletir a realidade). Decisão: aplicar edits
  no design.md do archive porque é a fonte de verdade
  citada no spec operacional (`tests/bdd/README.md`).
- `openspec/specs/bdd-workflow-reuse/spec.md` — MODIFIED
  Requirements: workflow count ceiling (4 workflows
  restantes) + REMOVED Requirements: switch_profile
  workflow + create_four_assets workflow + carve-out
  hardcoded dict + ADDED Requirements: marker-based
  carve-out enforcement.

Sem mudança em `pyproject.toml`, sem mudança em
backend, sem mudança em templates `dashboard.html`,
sem mudança em `scripts/measure_bdd_reuse.py`.
Risco operacional baixo — suite BDD verde passa a
verde com 18 cenários em vez de 17.

## Fora de escopo

- Alpine timing races em `create_one_class` (form-state
  coupling entre iterações) e `add_one_asset` (modal-init
  race). Suite passa hoje, contract tests não cobrem,
  corrigir exigiria mudar `dashboard.html`. Spike
  separado.
- Generalizar `_w_one_asset` para suportar criação em
  batch via lista (não é o mesmo que loop manual de
  4× — o loop já funciona, só não é "bonito"). Decidido:
  não vale o esforço enquanto só houver 1 caller de
  4-asset.
- Reativar `switch_profile` quando algum cenário
  realmente precisar de mid-test profile switch. Quando
  acontecer, recriar a workflow + wrapper + carve-out
  naquele momento (não agora).
