## MODIFIED Requirements

### Requirement: family mode is read-only

The rendered family page SHALL remain read-only. When the active profile is the
Família sentinel (or `?view=household` is on the querystring for backward
compat), it SHALL keep the `Atualizar posição` action visible but
disabled/read-only.

- **WHEN** the active profile is the Família sentinel (or
  `?view=household` is on the querystring for backward compat)
- **THEN** the rendered page keeps the `Atualizar posição` action visible but
  disabled/read-only
- **AND** the `+ Classe`, `+ Ativo`, and `Importar CSV` mutation action buttons
  remain disabled, hidden, or otherwise unavailable according to their existing
  Família contract
- **AND** the inline class-edit affordances (rename class, retarget
  percentage, delete class) are absent or disabled
- **AND** every mutation endpoint (`POST /classes`,
  `POST /api/assets`, `DELETE /api/assets/{id}`,
  `PATCH /api/assets/{id}`, `POST /import`) returns `409 Conflict`
  with a JSON error body naming `"reason": "household_read_only"`
  while the family view is active
- **AND** `POST /api/myprofit/sync` and
  `GET /api/myprofit/sync/{job_id}` reject the Família boundary with the same
  family-read-only reason before credential, connector, browser, file, or
  preview side effects
- **AND** `POST /rebalanceamento` returns the same 409

#### Scenario: family mode is visibly read-only for synchronization

- **WHEN** the active profile is the Família sentinel
- **THEN** `Atualizar posição` is rendered with a disabled/read-only state
- **AND** activating the control does not issue a synchronization request
- **AND** the import review modal does not open

#### Scenario: family mode blocks synchronization at server boundary

- **WHEN** a caller requests `POST /api/myprofit/sync` or polls
  `GET /api/myprofit/sync/{job_id}` while Família is active
- **THEN** the response is `409 Conflict` with
  `{"reason": "household_read_only"}`
- **AND** no credential lookup, browser launch, network navigation, file
  download, job lookup, or preview mutation occurs
