## 1. Atualizar contrato de produto

- [x] 1.1 **Target:** `openspec/PRD.md`, `§4.13 Testes — entrega só vale com suíte verde e sem máscara` (ou subseção documental imediatamente adjacente). **Change:** de contrato que define gates de teste sem fronteira explícita de uso mobile para texto que declara, em frases separadas, (a) Omaha não possui caso de uso mobile atual, (b) testes de browser mobile não são requisito da aceitação corrente, (c) desktop/browser continua fronteira obrigatória, e (d) ausência de requisito mobile não prova suporte mobile. **Preserve:** todos os parágrafos atuais de §4.13, I10 `maintenance-suspended`, `uv run task test`, seis lanes, comandos individuais, cobertura, duração `<=300s`, receipts, cleanup, fail-fast e aceitação browser. **Acceptance:** PRD contém quatro distinções mensuráveis sem wording que autorize remoção ou passe falso. **Test file/scenario:** nenhum arquivo de teste; cenário documental “operador lê §4.13 e distingue uso mobile, requisito de aceitação e suporte técnico”. **Focused taskipy command:** `uv run task lint` (planejado para Apply; esta proposta não o executa). **Independent oracle:** `git diff -- openspec/PRD.md` contém somente hunk documental dentro do escopo permitido e `git diff --check` passa.

## 2. Preservar contratos operacionais

- [x] 2.1 **Target:** `openspec/changes/d07-delimitar-escopo-mobile-no-contrato-de-produto/specs/test-suite-quality/spec.md` e os contratos-fonte `tests/PERFORMANCE.md`, `tests/AUDIT.md`, `openspec/specs/test-suite-quality/spec.md`, `openspec/specs/dev-tasks/spec.md` e `openspec/specs/visual-regression-baseline/spec.md`, nos símbolos listados em `design.md`. **Change:** manter delta com cenários verificáveis para desktop/browser obrigatório, mobile browser fora da aceitação corrente sem alegar suporte, mobile cases versionados/runnable e proibição de máscara; não editar contratos-fonte nesta gate. **Preserve:** comandos `uv run task test*`, população/audit, lanes, cobertura, histórico T32 e contratos de viewport exatamente como estão. **Acceptance:** delta usa `## ADDED Requirements` e cada cenário cobre uma fronteira mensurável; nenhum teste, baseline, marker, skip, xfail, retry, lane ou cobertura muda. **Test file/scenario:** nenhum arquivo de teste alterado; cenários do próprio delta “caso mobile versionado continua runnable” e “falha desktop/browser continua bloqueante”. **Focused taskipy command:** `uv run task lint` (planejado para Apply; não executar suíte de implementação). **Independent oracle:** `openspec validate "d07-delimitar-escopo-mobile-no-contrato-de-produto" --type change --strict` passa; `git status --short` e allow-list confirmam que apenas `openspec/PRD.md` além dos artefatos D07 pode mudar; os cinco contratos-fonte e `tests/` não aparecem como modificados.

## 3. Validar dossier e fronteira de mudança

- [x] 3.1 **Target:** `openspec/changes/d07-delimitar-escopo-mobile-no-contrato-de-produto/` e allow-list de aplicação futura. **Change:** validar presença e coerência de `proposal.md`, `design.md`, `tasks.md` e `specs/test-suite-quality/spec.md`; nenhum código será implementado nesta slice. **Preserve:** delta não vira sync de spec estável nesta gate, ausência de arquivo runtime/teste alterado e escopo futuro restrito a `openspec/PRD.md`. **Acceptance:** os quatro artefatos existem; proposta explicita ausência de caso de uso mobile, não-requisito de browser mobile, fronteira desktop/browser e política integral sem máscara; design contém code map, fluxo, decisões, riscos e não-escopos; tasks permanecem executáveis e sem escopo inventado. **Test file/scenario:** nenhum test file; cenário de aceitação “change dossier completo e allow-list sem arquivos fora do dossier”. **Focused taskipy command:** `uv run task lint` (planejado para Apply/Review; esta gate não executa testes de implementação). **Independent oracle:** `openspec status --change "d07-delimitar-escopo-mobile-no-contrato-de-produto" --json` retorna `isComplete: true`, `openspec validate "d07-delimitar-escopo-mobile-no-contrato-de-produto" --type change --strict` passa, `git diff --check` passa e glob exato lista somente `proposal.md`, `design.md`, `tasks.md` e `specs/test-suite-quality/spec.md` no dossier.

## Estratégia de testes e evidência

- Natureza da slice: documentação/contrato; não há teste de implementação,
  alteração de test file, mudança de runtime ou refresh-for-test.
- Validação focada planejada: `uv run task lint`, sem `uv run task test` como
  parte da proposta. Apply/Review devem registrar se comando foi executado e
  resultado; ausência de suíte canônica não pode ser reportada como verde.
- Evidência obrigatória: diff/name-only com allow-list, `git diff --check`,
  `openspec status --change "d07-delimitar-escopo-mobile-no-contrato-de-produto" --json`,
  `openspec validate "d07-delimitar-escopo-mobile-no-contrato-de-produto" --type change --strict`,
  e inspeção textual dos quatro critérios de aceitação.
- Não permitido para fechar D07: `skip`, `skipif`, `xfail`, `pytest.skip`, retry,
  remoção/desativação de testes, lanes ou cobertura, sync/alteração de specs
  estáveis fora do delta, ou criação de requisito mobile não suportado pela
  evidência.

## Execution Evidence

### Apply initial — 2026-08-24

- Preflight: `openspec/PRD.md` §4.13, `tests/PERFORMANCE.md`, `tests/AUDIT.md`,
  stable test-suite/dev-task/visual contracts, roadmap, config, and D07 dossier
  inspected before edit. Application boundary confirmed as one PRD hunk; no
  runtime, test, stable-spec, config, roadmap, or environment change authorized.
- Worktree boundary before apply: pre-existing `openspec/roadmap.md` modified;
  D07 dossier untracked and owner-provided. Neither is owned by this apply
  pass.
- Ownership ledger registration for focused validation run
  `D07-apply-initial-lint-20260824T142048-0300`: wrapper will emit exact PID/PGID
  and start timestamp immediately before `uv run task lint`; owner is
  `D07/d07-delimitar-escopo-mobile-no-contrato-de-produto` apply agent. No
  process, port, log, temporary path, or test DB resource is used before that
  registration.
- `uv run task lint` -> passed. All prek hooks passed, including `pytest-unit`;
  no product/runtime/test source changed.
- Ledger receipt `D07-apply-initial-lint-20260824T142048-0300`: child process
  PID `135886`, process group PGID `135886`, owner evidence = wrapper printed
  run identity/PID/PGID before `exec uv run task lint`, started
  `2026-08-24T14:21:10-03:00`, ended `2026-08-24T14:21:40-03:00`, status
  `exited`, classification `owned-cleaned`; observed result = lint passed and
  wrapper/group exited. No port, log, temporary path, or test DB resource was
  observed. Cleanup result = idempotent no-op; already exited/absent. No
  foreign or pre-existing resource was touched.
- Final no-temp documentation validation receipt
  `D07-apply-initial-final-doc-validation-2-20260824T142600-0300`: child process
  PID `138935`, process group PGID `138935`, owner evidence = wrapper printed
  run identity/PID/PGID before commands, started `2026-08-24T14:25:43-03:00`,
  ended `2026-08-24T14:25:48-03:00`, status `exited`, classification
  `owned-cleaned`; `openspec status` returned `isComplete: true`, strict
  `openspec validate` passed, `git diff --check` passed, and allow-list/status
  output showed only expected pre-existing roadmap plus PRD and D07 dossier.
  No port, log, temporary path, or test DB resource was used. Cleanup result =
  idempotent no-op; process/group already exited/absent. No foreign resource
  was touched.
- Acceptance evidence: PRD §4.13 now states four separate boundaries — no
  current mobile use case, mobile browser tests outside current product
  acceptance, mandatory desktop/browser acceptance, and no inference of mobile
  support. Same hunk preserves I10, canonical and six individual commands,
  coverage, `<=300s`, receipts, cleanup, fail-fast, and browser acceptance.
  Versioned mobile cases remain runnable; failure masking and desktop/browser
  regression suppression are explicitly prohibited.
- Dossier glob lists required `proposal.md`, `design.md`, `tasks.md`, and
  `specs/test-suite-quality/spec.md` (plus existing `.openspec.yaml`); stable
  contracts and `tests/` are unchanged.
- Canonical `uv run task test` not run: docs-only slice and config state
  `maintenance-suspended`; no canonical green result claimed. Focused
  `uv run task lint` passed twice, with its `pytest-unit` hook passing.
- Final no-temp documentation validation registration
  `D07-apply-initial-final-doc-validation-2-20260824T142600-0300`: wrapper will
  emit exact PID/PGID and start timestamp before running status, strict change
  validation, diff check, and allow-list inspection; owner remains current D07
  apply agent. No temporary path, port, log, or test DB resource declared.
- Final documentation validation receipt
  `D07-apply-initial-final-doc-validation-20260824T142500-0300`: child process
  PID `138671`, process group PGID `138671`, owner evidence = wrapper emitted
  run identity before validation commands, started `2026-08-24T14:24:22-03:00`,
  ended at command exit (recorded below), status `exited`, classification
  `owned-cleaned`; `openspec validate` passed, `git diff --check` passed, and
  allow-list/status output matched expected boundaries. The exact temporary
  path `/tmp/d07-status-output.json` was created by this run's status redirect;
  resource was registered here before cleanup as `owned-current-run`, with
  identity and creation evidence from the exact command. No port, log, or test
  DB resource was used; no foreign resource was touched. Cleanup used exact
  bounded removal of this run-created path only. Process ended
  `2026-08-24T14:24:22-03:00`; exact path cleanup ended
  `2026-08-24T14:25:05-03:00`, result `removed_exact_current_run_path`, final
  classification `owned-cleaned`, residue none.
- Final focused-validation ledger registration for
  `D07-apply-initial-final-lint-20260824T142300-0300`: wrapper will emit exact
  PID/PGID and start timestamp immediately before `uv run task lint`; same
  current apply owner. No process, port, log, temporary path, or test DB
  resource is used before registration.
- `uv run task lint` final pass -> passed. All prek hooks passed, including
  `pytest-unit`; no product/runtime/test source changed.
- Ledger receipt `D07-apply-initial-final-lint-20260824T142300-0300`: child
  process PID `137441`, process group PGID `137441`, owner evidence = wrapper
  printed run identity/PID/PGID before `exec uv run task lint`, started
  `2026-08-24T14:23:39-03:00`, ended `2026-08-24T14:24:03-03:00`, status
  `exited`, classification `owned-cleaned`; observed result = lint passed and
  wrapper/group exited. No port, log, temporary path, or test DB resource was
  observed. Cleanup result = idempotent no-op; already exited/absent. No
  foreign or pre-existing resource was touched.

## Review Findings

### Review R1
Scope audit: dossier completeness **pass**; requirements/scenarios **pass**;
design decisions and task coverage **pass**; PRD wording acceptance criteria
**finding**; stable test-suite/dev-task/visual contracts and T32 history
**pass**; bucket, viewport, coverage, masking, and no-test-deletion invariants
**pass**; allow-list **pass**; focused evidence **pass**; canonical test gate
state **pass** (suspended). One contract coherence issue remains open.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**. Owner-
authorized state is `openspec/config.yaml:87-100` and PRD §4.13. All six lanes
(unit, integration, audit integration, e2e, bdd, visual): **NOT RUN —
maintenance-suspended**. Coverage/tests/skips: not collected in this review.
Duration: N/A; 300-second classification: not applicable while suspended.
Focused evidence: apply receipts report `uv run task lint` passed twice,
including `pytest-unit`; review validation passed `openspec validate
"d07-delimitar-escopo-mobile-no-contrato-de-produto" --type change --strict`,
the four-criterion textual audit, dossier allow-list audit, and `git diff
--check`.

Preflight: review ownership ledger boundary registered before standards/spec
audit. Fields: `resource_kind=review-process/declared-test-resources`,
`resource_id=review R1 process; no PID/PGID, listener, test DB, log, or
declared temporary path launched`, `owner=D07/review`,
`owner_evidence=owner-authorized maintenance-suspended state plus review
boundary`, `started_at=2026-08-24 review start`, `ended_at=review completion`,
`status=inspection-only`, `classification=owned-current-run` for review
process and `absent` for declared test resources, `evidence=docs-only scope;
no canonical runner launch`, `cleanup_result=no-op; no resource touched`.
No foreign, unknown, pre-existing, or contradictory relevant resource was
adopted, killed, deleted, or allowlisted. Runner isolation precondition was
therefore satisfied for this non-launching suspended review.

Postflight: review process ended normally; declared process/listener/test-DB/
temp resources remain `absent`; no cleanup target or residue. Decision:
trusted non-launching postflight.

Verdict: **CHANGES_REQUESTED**

#### R1-F01 — PRD contradicts existing mobile-access context
Status: resolved — remediation 1/2
Severity: high
Requirement/task: D07 proposal “no current mobile use case”; delta
`test-suite-quality` Requirement “Current product acceptance delimits mobile
scope”; task 1.1 preservation/coherence requirement.
Evidence: `openspec/PRD.md:45-52` states current context includes access from
“laptops e celulares”; `openspec/PRD.md:824-828` states Omaha has no current
mobile use case. These statements are not distinguished as network reachability
versus product acceptance/use case, leaving contradictory product contract
semantics.
Required change: in the same PRD-only D07 hunk (or immediately adjacent PRD
wording), explicitly reconcile §1.3 with §4.13 by stating that cellular LAN
reachability is operational context and does not establish a current mobile
product use case or mobile acceptance requirement. Preserve desktop/browser
mandatory acceptance, versioned/runnable mobile cases, all six lanes/commands,
T32 records, viewport contracts, and full no-masking policy. Excluded scope:
no code, tests, stable-spec sync, roadmap, lane, marker, coverage, or viewport
changes.
Acceptance: textual audit finds both PRD statements plus explicit
reachability-versus-product-use-case distinction; `openspec validate
"d07-delimitar-escopo-mobile-no-contrato-de-produto" --type change --strict`
  and `git diff --check` pass; no file outside existing D07 allow-list and PRD
hunk changes.

### Review R2 — remediation 1/2
Scope audit: R1-F01 remediation **pass**; PRD §1.3/§4.13 coherence **pass**;
four D07 wording criteria **pass**; desktop/browser mandatory boundary **pass**;
mobile test executability and no masking **pass**; T32, bucket, coverage,
viewport, performance, audit, and stable-spec contracts **pass**; dossier
completeness/tasks **pass**; changed-file allow-list **pass**; stable spec sync
not required **pass**; no scope drift **pass**; focused evidence and suspension
receipt **pass**. No new blocking finding.

Full suite: `uv run task test` -> **NOT RUN — maintenance-suspended**. Config
state remains owner-authorized at `openspec/config.yaml:87-100`; no duration
claim made. Six lanes: unit, integration, audit integration, e2e, bdd, visual
all **NOT RUN — maintenance-suspended**. Focused apply evidence: `uv run task
lint` passed; strict change validation, diff check, status, and corrected
textual audit passed. Initial review script had one line-wrapping false
negative for the no-support sentence; normalized textual audit passed all six
assertions. This is harness wording, not product failure.

Preflight: review ownership ledger registered before remediation audit. Fields:
`resource_kind=review-process/declared-test-resources`,
`resource_id=review R2 process; no canonical lane PID/PGID, listener, test DB,
log, or declared temp path launched`, `owner=D07/review-remediation1`,
`owner_evidence=owner-authorized maintenance-suspended state plus inspection
boundary`, `started_at=2026-08-24 review start`, `ended_at=review completion`,
`status=inspection-only`, `classification=owned-current-run` for review process
and `absent` for declared test resources, `evidence=docs-only PRD remediation;
canonical suite prohibited by active suspension`,
`cleanup_result=no-op; no resource touched`. No foreign, unknown, pre-existing,
contradictory, or incomplete relevant resource was adopted or cleaned.

Postflight: review process ended normally; declared process/listener/test-DB/
temp resources remain `absent`; cleanup not applicable/no-op; no residue.
Runner isolation decision: trusted non-launching review; canonical launch was
correctly suppressed by maintenance suspension.

Verdict: **APPROVED**

Open findings: none. R1-F01 is resolved by `openspec/PRD.md:824-830`, which
explicitly defines cellphone LAN access as operational reachability, separates
it from mobile product use case and mobile acceptance, retains desktop/browser
as mandatory, and denies any inference of mobile technical support.

#### Resolution R1-F01 — Remediation 1/2 — 2026-08-24

- Changed only `openspec/PRD.md`, symbol `§4.13` product/viewport boundary:
  added explicit wording that technical cellphone access to the LAN URL is
  operational household-network reachability, not a mobile product use case or
  current mobile acceptance requirement.
- Preserved `§1.3` LAN context, mandatory desktop/browser acceptance, versioned
  and runnable mobile cases, six lanes and individual commands, T32 records,
  viewport contracts, I10 suspension, coverage, receipts, cleanup, fail-fast,
  and full no-masking policy. No code, tests, stable specs, roadmap, config, or
  unrelated PRD section changed.
- First validation registration
  `D07-remediation1-doc-validation-20260824T$(date +%H%M%S%z)`:
  `resource_kind=process_group`, `resource_id=140184`,
  `owner=D07/d07-delimitar-escopo-mobile-no-contrato-de-produto apply-remediation1`,
  `owner_evidence=wrapper registration emitted before validation children`,
  `started_at=2026-08-24T14:33:28-03:00`,
  `ended_at=2026-08-24T14:33:52-03:00`, `status=exited`,
  `classification=owned-cleaned`. Evidence: lint, strict validation,
  `git diff --check`, and status passed; textual audit exited 1 because its
  first assertion expected different line wrapping. Diagnosis was validation
  harness wording, not PRD content. `cleanup_result=idempotent no-op;`
  wrapper/group exited; no port, log, temporary path, or test DB used.
- Corrected validation registration
  `D07-remediation1-doc-validation-20260824T143444-0300`:
  `resource_kind=process_group`, `resource_id=141460`,
  `owner=D07/d07-delimitar-escopo-mobile-no-contrato-de-produto apply-remediation1`,
  `owner_evidence=wrapper registration emitted before validation children`,
  `started_at=2026-08-24T14:34:44-03:00`,
  `ended_at=2026-08-24T14:35:08-03:00`, `status=exited`,
  `classification=owned-cleaned`. Evidence: `uv run task lint` passed;
  `openspec validate "d07-delimitar-escopo-mobile-no-contrato-de-produto" --type change --strict`
  passed; `git diff --check` passed; `openspec status ... --json` returned
  `isComplete: true`; textual audit passed reachability/use-case/acceptance
  distinction. `cleanup_result=idempotent no-op;` wrapper/group exited; no
  port, log, temporary path, or test DB used.
- Canonical suite: `uv run task test` **NOT RUN — maintenance-suspended**.
- Acceptance result: R1-F01 reachability-versus-product-use-case contradiction
  resolved in PRD-only hunk; changed-file allow-list remains PRD plus this
  remediation evidence in D07 `tasks.md`.
- Final validation registration
  `D07-remediation1-final-validation-20260824T143559-0300`:
  `resource_kind=process_group`, `resource_id=142706`,
  `owner=D07/d07-delimitar-escopo-mobile-no-contrato-de-produto apply-remediation1`,
  `owner_evidence=wrapper registration emitted before final validation
  children`, `started_at=2026-08-24T14:35:59-03:00`,
  `ended_at=2026-08-24T14:36:22-03:00`, `status=exited`,
  `classification=owned-cleaned`. Evidence: `uv run task lint`, strict
  change validation, `git diff --check`, status, textual audit, status-short,
  and diff-name audit all passed. `cleanup_result=idempotent no-op;`
  wrapper/group exited; no port, log, temporary path, or test DB used.
