## MODIFIED Requirements

### Requirement: Revisão e commit de import (Step 2)

The modal SHALL render Step 2 as up to four mutually exclusive review sections
labelled `Novos`, `Ausentes`, `Alterados`, and `Inalterados`, in exactly that
order whenever the sections contain rows. Each rendered section SHALL include
its row count. Rows SHALL retain incoming values as primary display and preserve
editable class/trade/currency controls and hidden `broker_ticker` assignment
keys. Empty sections SHALL NOT render; changed rows SHALL carry field-diff
cues while unchanged rows SHALL carry none. The existing explicit confirmation
remains the sole commit boundary.

The fixed section order SHALL apply after manual `Importar CSV`, successful
`Atualizar posição` handoff, local/mock preview hydration, and legacy payload
fallback. The order SHALL NOT depend on JSON key order, producer, or the order
in which rows arrive. Existing deterministic ordering within each group,
four-way F65 classification, compatibility arrays, values, controls, and
timeout behavior SHALL remain unchanged.

O modal SHALL exibir:
- Resumo de linhas auto-matched (data-testid="import-matched-summary")
- Tabela de linhas unmatched (data-testid="import-unmatched-table") com dropdowns de classe
- Botão "Confirmar importacao" (data-testid="import-confirm-btn")

Ao confirmar, DEVE fazer POST /api/import/commit com os assignments e recarregar
a página.

#### Scenario: Mixed F65 batch uses fixed section order

- **WHEN** a valid preview contains non-empty `new`, `absent`, `changed`, and
  `unchanged` groups in any payload key order
- **THEN** visible section headers are exactly `Novos`, `Ausentes`,
  `Alterados`, `Inalterados` in that order
- **AND** each row remains in its original F65 group with its original count

#### Scenario: Empty groups remain hidden

- **WHEN** one or more F65 groups contain zero rows
- **THEN** no section, heading, count, table, or placeholder is rendered for
  those groups
- **AND** remaining non-empty sections keep fixed relative order

#### Scenario: Manual and sync hydration share order

- **WHEN** the same mixed-batch preview is hydrated after manual upload or
  successful MyProfit `Atualizar posição` handoff
- **THEN** both flows render identical section order, counts, rows, controls,
  and hidden assignment keys without navigation or automatic commit

#### Scenario: Local and legacy hydration remain reviewable

- **WHEN** local/mock hydration or a valid legacy payload lacks additive
  `triage` data
- **THEN** existing compatibility arrays remain reviewable through the current
  fallback and visible sections use `Novos`, `Ausentes`, `Alterados`,
  `Inalterados` order where non-empty
- **AND** no row is fabricated as unchanged or absent and no commit occurs
  before explicit confirmation

#### Scenario: Review inventory and deterministic row order are preserved

- **WHEN** any non-empty section renders
- **THEN** its existing row values, eight production columns, class/trade/currency
  controls, diff cues, and hidden `broker_ticker` assignment identity remain
  available
- **AND** rows retain existing deterministic case/accent-insensitive
  name/ticker order within that section

#### Scenario: Confirmation remains explicit

- **WHEN** operator reviews ordered triage rows and has not activated
  `Confirmar`
- **THEN** no commit request or portfolio mutation occurs

#### Scenario: Sessão expirada mostra estado de erro

- **WHEN** preview expirou (previewError = true)
- **THEN** modal exibe mensagem "Sessão expirada. Reenvie o arquivo."
- **AND** botão "Reenviar" volta para step 1

#### Scenario: Commit bem-sucedido recarrega dashboard

- **WHEN** usuário confirma import com assignments válidos
- **THEN** modal faz POST /api/import/commit
- **AND** em caso de sucesso, recarrega a página (window.location.reload())
- **AND** dashboard exibe os novos ativos com posições
