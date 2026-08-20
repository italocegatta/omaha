# T32 — Revisar política de poda seletiva sob teto de testes

## Why

PRD §4.13 exige suíte completa verde, teto absoluto de 300 segundos e
preservação de testes, cobertura e lanes; ao mesmo tempo, T32 precisa definir
como tratar redundância de baixo valor sem transformar poda em falso verde.
Hoje não existe política operacional única para parametrizações, exemplos,
snapshots ou asserts redundantes, nem registro mínimo para provar que contrato
comportamental continua protegido.

## What Changes

- Formalizar política seletiva, versionada e auditável para propor poda de um
  node/caso, nunca de uma suíte inteira.
- Exigir classificação por node/caso e categoria (parametrizado, exemplo,
  snapshot ou assert redundante/baixo valor), contrato protegido, cobertura
  substituta, economia medida, owner e data.
- Exigir que qualquer poda futura preserve contrato comportamental, não use
  `skip`, `skipif`, `xfail`, `pytest.skip`, `pass` vazio, placeholder ou
  decisão tomada durante timeout.
- Manter o gate canônico, população aceita e cobertura protegida. Casos
  owner-aprovados permanecem versionados no arquivo de teste, recebem o marker
  explícito `t32_pruned` com justificativa de priorização, e ficam fora apenas
  da lane bloqueante padrão.
- Registrar decisão e evidências antes de Apply; Apply atualiza somente os
  casos aprovados, manifesto/auditoria, performance e contrato da suíte.

## Authorized scope expansion — 2026-08-19

The repository owner explicitly expanded this Apply to two bounded remediation
tracks: (A) optimize test-harness scheduling, resource isolation, and teardown
so canonical `uv run task test` is green within the hard 300-second wall-clock
ceiling; and (B) normalize stale `Owner-approved coverage removals` wording in
`tests/AUDIT.md` while retaining the 12 versioned T32 cases outside only the
standard blocking lane. No test, lane, marker, skip, xfail, or coverage
contract may change beyond the already approved 12 `t32_pruned` visual cases.

This expansion authorizes no timeout-based decision, deselection, masking,
pruning, production/runtime DB change, unrelated refactor, archive, commit, or
push. If safe harness remediation cannot produce one green canonical run within
300 seconds, Apply stops with profiling evidence and blocker details.

The expanded policy also authorizes versioned importance governance for every
collected node/case (`critical`, `high`, `normal`, `low`). Active count is
current-state telemetry, not contract. Only a deterministic pre-run forecast
may select lowest-importance cases when measured or prior-known cost requires
it; within-ceiling forecasts select no new case. Selected cases remain runnable
through the named expanded lane with rationale, owner/date, protected contract,
replacement coverage, and cost evidence.

Review reconciliation record (`t32.v5`, repository owner, 2026-08-19) adds two
existing normal-classification, low-value unit checks to governing evidence and
expanded schedule: `tests/test_dark_mode_tokens.py::test_class_swatches_against_bg[1]`
(0.847s; Class-1 token contrast against `--bg`; replacement: remaining
class-swatch cases plus CSS token audit) and
`tests/test_dark_mode_tokens.py::test_negative_ink_on_negative_passes_aa`
(0.786s; negative status ink contrast; replacement: status-ink siblings plus
CSS token audit). This reconciles evidence only; it adds no test or pruning.

## Capabilities

### New Capabilities

Nenhuma. Política pertence à capacidade existente de qualidade da suíte.

### Modified Capabilities

- `test-suite-quality`: definir governança para poda seletiva versionada sob o
  teto de 300 segundos, sem enfraquecer o contrato de entrega de PRD §4.13.

## Impact

- Artefatos OpenSpec e delta de `test-suite-quality` nesta change.
- Manifesto/auditoria, documentação de performance, configuração da lane e
  especificação serão atualizados juntos.
- Nenhuma alteração de produção ou comportamento de aplicação. Expanded visual
  baselines may be generated only from the isolated test DB and retained after
  explicit case-by-case review.

## Owner decision record

- **Decision:** approved pruned cases remain versioned and auditable, with an
  explicit `t32_pruned` prioritization rationale; standard blocking suite
  excludes only those approved cases.
- **Owner:** repository owner.
- **Date:** 2026-08-19.
- **Scope:** 12 visual snapshot cases listed in `tests/AUDIT.md` T32 register.
- **Authoritative locations:** `openspec/roadmap.md` T32 progress log and
  `tests/AUDIT.md` T32 selective-pruning register.
