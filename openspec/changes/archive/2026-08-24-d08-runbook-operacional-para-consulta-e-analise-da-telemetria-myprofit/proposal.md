## Why

T38 established bounded `myprofit_telemetry` events, but its runbook does not
yet give an operator one reproducible path from authoritative stdout discovery
through rotated-log collection, `job_id` tracing, read-only job-row
correlation, and weekly error analysis. D08 closes that documentation gap
before T38 finalization without changing runtime behavior.

## What Changes

- Complete `docs/runbooks/myprofit-sync-telemetry.md` with authoritative
  stdout/log discovery for development and the existing production Compose
  `web` service, including text and JSON envelope extraction.
- State the exact telemetry message shape, finite event dimensions, bounded
  `job_id` extraction, validation/rejection rules, and safe collection copy.
- Add rotation and retention procedure: inventory available segments, record
  coverage, never reconstruct missing lines, and emit
  `insufficient-evidence` when the four-to-eight-week window is unavailable.
- Add read-only `myprofit_sync_jobs` correlation using existing
  `job_id`, profile ownership, status, error fields, and lifecycle timestamps;
  prohibit writes, inferred time joins, and dependence on long-term job-row
  retention.
- Define terminal classification: `succeeded`, `failed`, and `expired`, with
  incomplete/missing terminal evidence kept separate from failure and with
  the UI local-limit signal treated as observation, not server timeout.
- Add executable weekly procedure for four to eight weeks or four to eight
  real runs per week, with explicit denominators, error rates, invalid/missing
  records, top `domain/stage/code` factors, and escalation threshold.

## Capabilities

### New Capabilities

None. D08 operationalizes documentation for the existing T38
`myprofit-sync-observability` capability; it does not introduce runtime
behavior or a new stable contract.

### Modified Capabilities

- `myprofit-sync-observability`: clarify the existing runbook requirement with
  authoritative stdout discovery, exact event extraction, read-only
  `myprofit_sync_jobs` correlation, retention/rotation gaps, and explicit
  terminal/UI-limit classification. This is a documentation contract only; it
  does not change runtime telemetry behavior.

## Impact

- Documentation: one existing file,
  `docs/runbooks/myprofit-sync-telemetry.md`.
- Evidence sources: existing `omaha` stdout logger, configured JSON/text
  formatter, and existing `myprofit_sync_jobs` rows queried read-only.
- No runtime files, API, model, schema, migration, logger configuration,
  timeout, retry, retention mechanism, external service, UI, DB write, T38
  artifact, stable spec, roadmap, or config changes.
- Validation is documentation-contract and command/procedure review only; no
  live connector, credential, raw exception, CSV, sensitive URL, or product
  database mutation is needed.
