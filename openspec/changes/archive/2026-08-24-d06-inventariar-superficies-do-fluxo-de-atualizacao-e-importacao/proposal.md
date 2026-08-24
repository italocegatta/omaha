## Why

O fluxo de `Atualizar posição` mistura ação, notificações transitórias e revisão de importação. O inventário Explore confirmou quatro superfícies owner-decididas como desnecessárias ou inadequadas: botão em `Família` e três notificações de ciclo de vida. Registrar decisão agora evita que F67/T36/F68 interpretem ou alterem superfícies fora desse limite.

## What Changes

- Formaliza inventário técnico do fluxo manual e MyProfit, da renderização do Patrimônio ao preview/review.
- **BREAKING** para contrato visual do sync: em perfil `Família`, não renderizar o botão `Atualizar posição` (D06-03).
- **BREAKING** para feedback transitório: não renderizar `Pronto para atualizar posição.` (D06-04), `Atualizando posição...` (D06-06) ou `Atualização concluída. Revise posições antes de confirmar` (D06-12).
- Mantém ação de sincronização e seu fluxo em perfis reais, erros sanitizados, modal `Revisar posições`, assignments editáveis e confirmação explícita.
- Registra `previewError` como nota bounded: inventário identifica estado de sessão expirada, mas não decide nem especula sobre novo trigger.

## Capabilities

### New Capabilities

Nenhuma. D06 é slice de inventário e decisão; não introduz runtime capability.

### Modified Capabilities

- `patrimonio-position-sync-action`: restringe feedback transitório às superfícies preservadas, remove a affordance de sync em `Família` e mantém erro/revisão/ação real.

## Impact

- Contrato futuro para `src/omaha/templates/_patrimonio_actions.html` e para o store `patrimonioSync` em `src/omaha/templates/_patrimonio_add_asset_modal.html`.
- `src/omaha/routes/imports.py` e `src/omaha/routes/pages.py` permanecem limites de API/contexto a preservar; nenhuma rota, job, parser, preview ou commit muda nesta proposta.
- Evidência de Apply deverá usar `tests/e2e/test_patrimonio_sync_action.py`, `tests/e2e/test_import_modal.py` e `tests/test_myprofit_sync_jobs.py`, sem full suite nesta gate.
- Nenhuma alteração em F67, T36, F68, F63, T31, F65, F60 ou em dados/DB.
