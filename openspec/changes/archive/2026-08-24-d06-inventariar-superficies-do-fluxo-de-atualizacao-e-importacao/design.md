## Context

D06 é gate de escopo para uma alteração browser-visible posterior. Explore já concluiu inventário técnico; owner fechou quatro decisões em 2026-08-24. Esta change registra origem, fronteiras e contrato para Apply, sem alterar código, banco, rotas ou testes agora.

### Code map

| Fonte | Símbolo/superfície | Papel no fluxo atual |
|---|---|---|
| `src/omaha/templates/_patrimonio_actions.html` | `section[data-testid="patrimonio-actions"]`; `{% if view == 'profile' %}` | Renderiza ações de perfil real, inicializa `patrimonioSync` com `myprofit_sync` e mantém `Importar CSV` como ação adjacente. Ramo `else` renderiza atualmente botão sync disabled/read-only em `Família`. |
| `src/omaha/templates/_patrimonio_actions.html` | `dashboard-sync-btn`, `dashboard-import-btn`, `patrimonio-notifications` | Botão real chama `$store.patrimonioSync.start()`; import chama `$store.importModal.openModal()`; outlet renderiza cards do store via `x-for`. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `Alpine.store('importModal')` | Controla upload, `hydratePreview`, `openPreview`, assignments, `previewError`, review Step 2, `Cancelar`, `Confirmar importação` e commit explícito. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `Alpine.store('patrimonioSync')` | Máquina client-side idle/loading/success/error: `init`, `start`, `schedulePoll`, `poll`, `setError`, `showNotification`, `resetAfterReview`; entrega preview MyProfit ao modal existente. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` | `data-testid="import-modal-overlay"`; Step 1/Step 2 | Modal único preserva upload manual, triagem/revisão, assignments editáveis, expiração e confirmação. |
| `src/omaha/routes/pages.py` | `_common_context`, `_render_patrimonio`, `_resolve_view_mode` | Resolve perfil real versus sentinel `Família`; fornece `view`, `read_only`, `myprofit_sync` e `myprofit_sync_error`. GET não inicia job nem abre modal. |
| `src/omaha/routes/imports.py` | `_require_sync_profile`, `start_myprofit_sync`, `get_myprofit_sync_status`, `MyProfitSyncService.status_for_profile` | Limite server-side: `Família` recebe 409 antes de side effects; perfil real recebe job 202 e status sanitizado; preview succeeded reutiliza contrato de import sem mutação. |
| `src/omaha/routes/imports.py` | `preview_from_blob`, `_build_preview_response`, `PreviewBlobError` | Limite de preview manual/background, serialização de `preview_id`, triagem, classes e erros de upload/parse. Não pertence às quatro remoções. |
| `tests/e2e/test_patrimonio_sync_action.py` | `TestPatrimonioSyncAction` | Oracle browser do action strip, cards lifecycle, polling, erros, handoff para review, cancelamento e `Família`. Contém literais D06-04/D06-06/D06-12 que Apply deverá substituir por ausência/assertivas preservadas. |
| `tests/e2e/test_import_modal.py` | `TestS04ImportModal` | Oracle do upload manual, Step 2, triagem, review e commit. Deve continuar provando modal e confirmação, sem depender dos cards removidos. |
| `tests/test_myprofit_sync_jobs.py` | contratos de `MyProfitSyncService` | Oracle server-side de job, isolamento, status, preview handoff e ausência de mutação. Não é superfície UI e não deve ser reescrito para remover copy. |

### Explore inventory evidence

| ID | Observação no código/teste | Decisão owner |
|---|---|---|
| D06-03 | Ramo `else` de `_patrimonio_actions.html` (`data-testid="dashboard-sync-btn"`, label `Atualizar posição`, disabled, `aria-disabled="true"`) mostra sync em `Família`. | Remover/hide somente esse botão em `Família`; não criar substituto. |
| D06-04 | `patrimonioSync.init()` chama `showNotification('Pronto para atualizar posição.', 'status')`; e2e fixa copy em `tests/e2e/test_patrimonio_sync_action.py`. | Remover/hide card idle. Preservar inicialização de estado e erros iniciais sanitizados. |
| D06-06 | `patrimonioSync.start()` chama `showNotification('Atualizando posição...', 'status')`; e2e fixa card loading. | Remover/hide card loading. Preservar botão real, estado loading, bloqueio de duplicata e polling. O label separado `Atualizando...` do botão não é alvo desta decisão. |
| D06-12 | `patrimonioSync.poll()` chama `showNotification('Atualização concluída. Revise posições antes de confirmar', 'success')` antes de `importModal.openPreview(...)`; e2e fixa card success. | Remover/hide card success. Preservar `Revisar posições`, assignments, `Cancelar` e confirmação explícita. |

### Current relevant flow

1. **Entrada de página:** operador autenticado acessa `/patrimonio`; `pages.py` resolve active profile. Perfil real recebe `view='profile'`, `owner` e estado MyProfit sanitizado. Sentinel `Família` entra em `view='family'`/read-only.
2. **Ação real:** template renderiza `dashboard-sync-btn`; click chama `patrimonioSync.start()`. Store faz `POST /api/myprofit/sync`, recebe `202` com `job_id`, agenda polling de `GET /api/myprofit/sync/{job_id}` e mantém `state='loading'` até terminal.
3. **Terminal success:** status `succeeded` precisa carregar preview válido (`preview_id`, `auto_matched`, `unmatched`, `asset_classes`); store hidrata `$store.importModal`, abre `import-modal-overlay` no Step 2 e não chama commit.
4. **Terminal/error boundaries:** `failed`/`expired`, start inválido, poll HTTP failure, payload malformado e timeout paramétrico terminam com erro sanitizado no Patrimônio; não abrem modal. `pages.py` pode apresentar erro anterior sanitizado em real profile. `Família` é rejeitada server-side por `_require_sync_profile` e não deve emitir start/poll client-side.
5. **Import manual:** `dashboard-import-btn` abre Step 1; seleção chama `POST /api/import/preview`; `hydratePreview` carrega triagem/assignments no Step 2. `Cancelar`, fechar e `Reenviar` continuam disponíveis conforme origem/estado. `commit()` é único limite de mutação e faz `POST /api/import/commit`.
6. **Preview expiry:** markup mostra `Sessão expirada. Reenvie o arquivo.` quando `importModal.previewError` é true. No código inspecionado, `previewError` é inicializado/resetado para false e não há atribuição observável para true; trigger efetivo permanece desconhecido.

### Boundary conditions

- D06 remove quatro superfícies visuais exatas, não estados internos, endpoints, timers, job expiry, safe errors ou review.
- `Atualizar posição` continua em perfis reais; `Importar CSV` continua em perfis reais e segue abrindo mesmo modal.
- `Família` não recebe botão de sync; read-only/mutation guard server-side permanece.
- Sucesso continua significando preview aberto para revisão, não commit automático.
- Erros de upload, commit, job, poll e expiração permanecem visíveis quando já pertencem às superfícies existentes.
- Literais PT-BR são contratuais; não substituir por copy genérica nem remover cards de erro por associação ampla com `patrimonio-notifications`.

## Goals / Non-Goals

**Goals:**

- Fixar inventário Explore e decisões D06-03, D06-04, D06-06 e D06-12 para Apply.
- Alterar, em Apply posterior, somente presença do botão Família e os três cards/copies lifecycle listados.
- Provar ausência das quatro superfícies, presença da ação real, preservação de erros sanitizados, modal, review, assignments e commit explícito.
- Manter `previewError` como nota bounded, sem escolher trigger ou inventar comportamento.

**Non-Goals:**

- Não implementar nesta gate.
- Não alterar `src/omaha/routes/imports.py`, `src/omaha/routes/pages.py`, API, connector, worker, job status, timeout, parser, preview payload, import commit, migration, seed ou DB.
- Não alterar/reabrir F67, T36, F68, F63, T31, F65 ou F60.
- Não remover `Importar CSV`, modal de review, triagem, controles, `Cancelar`, `Reenviar`, confirmação, mensagens de erro ou sync action de perfis reais.
- Não resolver trigger de `previewError`, não aumentar timeout e não reinterpretar pergunta truncada do owner; timeout pertence a T36/F68.

## Decisions

### 1. Delta somente em `patrimonio-position-sync-action`

O capability é único owner de botão Família e notificações do sync. `import-modal`, `myprofit-sync-job` e contratos de rotas permanecem estáveis: modal/review/commit e job/preview/error boundaries são preservados. Delta spec modifica apenas requisitos diretamente conflitantes.

**Alternativa rejeitada:** criar delta em `import-modal` para registrar ausência de card sync. Isso diluiria ownership e sugeriria mudança no contrato do modal, que não foi decidida.

### 2. Remoção cirúrgica por origem e copy

Apply deverá retirar somente o botão do ramo Família e as emissões dos três cards `status`/`success` nomeados. Outlet e funções de notificação permanecem porque errors sanitizados continuam necessários. State machine, `data-sync-state`, disabled loading e polling permanecem para não transformar remoção de feedback em alteração de job.

**Alternativa rejeitada:** remover `patrimonio-notifications` inteiro ou `showNotification`. Isso removeria erros preservados e violaria escopo.

### 3. Review permanece output de sucesso

Após `succeeded` com preview válido, `openPreview(preview, 'patrimonio-sync')` continua abrindo Step 2. Ausência de D06-12 não significa ausência de review, diff/triagem, `Cancelar` ou confirmação.

**Alternativa rejeitada:** substituir card success por novo banner/toast ou fechar automaticamente o modal. Owner decidiu remover superfície, não criar outra.

### 4. `previewError` fica explicitamente bounded

D06 registra apenas markup, store fields e branch observados. Apply não deve adicionar trigger, alterar API de expiração ou inferir que qualquer erro de sync deve setar `previewError`. Nova decisão exige slice/escopo próprio.

**Alternativa rejeitada:** “corrigir” estado não alcançável durante D06. Isso seria comportamento especulativo fora do inventário.

### 5. Owner validation é gate pós-Apply

Depois de Apply, owner deve validar browser rendering do perfil real e da seleção `Família` antes de Review/Applied. A validação deve confirmar ausência exata das quatro superfícies e presença de todos os fluxos preservados. `refresh-for-test` pertence à entrega browser-visible após Apply, não à Propose.

## Change map

| Arquivo/símbolo futuro | De → para | Razão |
|---|---|---|
| `src/omaha/templates/_patrimonio_actions.html` — ramo `{% else %}` de `patrimonio-actions` | Botão Família `dashboard-sync-btn` disabled/read-only com `Atualizar posição` → nenhum botão sync renderizado em `Família`; demais contratos da página intactos | D06-03; evitar affordance de ação em visão agregada read-only. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` — `patrimonioSync.init` | `init` emite card `Pronto para atualizar posição.` em estado idle → não emite esse card; inicialização e erro inicial sanitizado permanecem | D06-04; remover feedback desnecessário sem apagar error surface. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` — `patrimonioSync.start` | `start` emite card `Atualizando posição...` → não emite esse card; state loading, button disabled, POST e polling permanecem | D06-06; preservar operação e bloqueio de duplicata. |
| `src/omaha/templates/_patrimonio_add_asset_modal.html` — `patrimonioSync.poll` success | success emite card `Atualização concluída. Revise posições antes de confirmar` → abre review diretamente sem card; `openPreview` e commit boundary permanecem | D06-12; revisão existente é feedback/ação essencial. |
| `tests/e2e/test_patrimonio_sync_action.py` — cenários lifecycle/Família | Asserts de três literals e presença Família → asserts de ausência dos cards/literals e ausência do botão Família, mais asserts de erros, polling e review preservados | Oracle independente para quatro decisões. |
| `tests/e2e/test_import_modal.py` — `TestS04ImportModal` | Fluxo manual/review/commit atual → mesma cobertura, sem dependência de notificações sync | Provar import surface preservada. |
| `tests/test_myprofit_sync_jobs.py` — contratos F59 | Sem mudança comportamental | Guardar API/job/preview/no-mutation; não é alvo de copy UI. |
| `src/omaha/routes/imports.py` e `src/omaha/routes/pages.py` | Sem mudança | Preservar limites de autorização, perfil, safe errors e preview contract. |

## Risks / Trade-offs

- **Aplicação remove todos cards por engano** → Mitigar por asserts de erro sanitizado (`failed`/`expired`/poll/start), revisão success e diff de arquivo limitado a emissões D06.
- **Família continua exibindo affordance via seletor legado** → Mitigar com browser/HTML oracle que procura zero `dashboard-sync-btn` e zero literal `Atualizar posição` na área Família, sem remover opção de profile switcher.
- **Sucesso sem card parece falha** → Mitigar provando `import-modal-overlay` visível, Step 2, triagem editável e ausência de `POST /api/import/commit` antes de confirmação.
- **Loading feedback removido indevidamente do botão** → Mitigar distinguindo D06-06 (`Atualizando posição...` card) de label separado `Atualizando...` do `dashboard-sync-btn`, que fica fora da decisão.
- **Preview error trigger recebe implementação especulativa** → Mitigar com teste de não-regressão do branch existente e nota bounded; não adicionar atribuição a `previewError` nesta slice.
- **Testes F60 antigos falham por expectativas de copy** → Atualizar somente expectativas que provam superfícies D06; manter cenários de polling, safe errors, no-commit, cancel e real profile.
- **Regressão server-side ou DB** → Não tocar routes/jobs/DB; `tests/test_myprofit_sync_jobs.py` permanece oracle focused.

## Migration Plan

Propose cria somente este dossier e delta spec; nenhum runtime migration ocorre.

Apply posterior, se autorizado pelo roadmap, deve:

1. Ler este `design.md`, `proposal.md`, delta spec e `tasks.md`; confirmar mudança somente nos símbolos listados.
2. Aplicar as quatro remoções sem reescrever máquina de estados, endpoints ou modal.
3. Atualizar testes focados para provar ausência/preservação.
4. Rodar comandos taskipy focados declarados em `tasks.md`; não rodar `uv run task test` nesta gate solicitada.
5. Para runtime browser-visible, executar `refresh-for-test` e produzir recibo antes de reportar delivery.
6. Pausar para owner validation browser antes de Review. Rollback remove somente edits D06 em templates/testes/delta; não restaura nem toca DB.

## Open Questions

- **Bounded, não bloqueante para D06:** qual caminho efetivo, se algum, atribui `true` a `$store.importModal.previewError`? O código inspecionado só inicializa/reseta `false`; D06 não decide trigger nem comportamento.
- Nenhuma decisão owner de D06 está aberta. Timeout e interpretação da pergunta truncada continuam fora deste change e pertencem a T36/F68.

## Implementation Decisions

### Apply — lifecycle cards removed without changing sync state machine

- **Context:** removing the three lifecycle notification emissions must not
  leave an old safe error card visible when operator starts a new sync.
- **Decision:** `init` keeps only the existing initial failed/expired error
  emission; `start` clears notifications directly, then preserves loading,
  request, polling, and disabled state; successful `poll` opens review without
  notification. `showNotification` remains unchanged for sanitized errors.
- **Impact:** idle/loading/success have zero `patrimonio-notification` cards;
  failed/expired/start/poll/malformed-preview errors retain one safe card;
  no route, preview, commit, timer, or modal contract changes.
- **Evidence:** mapped symbols in
  `src/omaha/templates/_patrimonio_add_asset_modal.html:1993-2241`, D06-04,
  D06-06, D06-12, and focused server contract result `19 passed`.

### Apply — Família oracle observes attached empty action section

- **Context:** after D06-03 removes the only Família action, the server still
  renders `section[data-testid="patrimonio-actions"]` with
  `data-sync-state="disabled"`; CSS hides this empty section. The initial
  browser oracle waited for `visible` and failed before checking absence.
- **Decision:** wait for the exact section to be `attached`, then assert zero
  sync button and zero `Atualizar posição` literal. Do not add Família import
  assertions: `Importar CSV` remains a real-profile action, not a Família
  action.
- **Impact:** test oracle matches rendered DOM and D06 scope without changing
  template behavior or adding a Família replacement surface.
- **Evidence:** focused E2E progression: first run `8 passed, 1 failed` on
  visibility wait; second run isolated stale Família import expectation;
  final run `9 passed in 37.16s`.

### Apply — owner-authorized refresh delivery receipt

- **Authorization:** owner explicitly authorized on 2026-08-24 the bounded
  restart of pre-existing Omaha uvicorn PID 1692 / PGID 1689 listening on
  port 8000. Authorization excluded `data/portfolio.db` mutation, DB deletion,
  and unrelated process action.
- **Process action:** preflight matched PID 1692 to the Omaha worktree,
  command `uvicorn omaha.main:app --host 0.0.0.0 --port 8000`, PGID 1689, and
  listener `0.0.0.0:8000`. Refresh sent `kill -TERM 1692` only; no pattern
  kill and no PGID kill. Old PID/listener exited, then exact refresh launcher
  started `OMAHA_SKIP_STARTUP=1 uv run uvicorn omaha.main:app --host 0.0.0.0
  --port 8000` from this worktree. New launcher PID 67038 / PGID 67038 and
  listener child PID 67046 served port 8000.
- **DB protection:** no `db-migrate`, `db-reset`, `db-clear-assets`, seed,
  delete, or other DB write ran. `data/portfolio.db` remained mode 644, size
  282624, inode 241846, mtime `2026-08-24 02:04:11.700521292 -0300`; final
  SHA-256 was
  `5c4865639a718627275dbd12db08550810a6b780b5257ce9f210660fc605f159`.
- **Delivery receipt:** LAN URL from `bash scripts/print_lan_url.sh` was
  `http://192.168.1.8:8000`; `curl -fsS "$URL/healthz"` returned
  `{"status":"ok","db":"ok","service":"omaha","version":"0.1.0"}`.
  Read-only profile counts were Italo `6/47/46`, Ana `5/43/42`, and Família
  `0/0/0` for classes/assets/positions; aggregate `11/90/88`. Authenticated
  dashboard smoke counted `RF Din` 5. Counts are pre-existing and were not
  normalized because D06 forbids DB mutation.
- **Live rendering evidence:** Família action strip had zero
  `dashboard-sync-btn` and zero `Atualizar posição`; real profile rendered
  sync/import actions; real page had zero D06-04, D06-06, and D06-12 literals.
  Prior focused browser evidence remains authoritative for review, modal,
  sanitized-error, confirmation, and no-commit behavior.
- **Ownership receipt:** complete ledger at
  `/tmp/opencode/d06-refresh-ownership-ledger-20260824T-continuation.md`.
  Exact launcher and cookie paths were bounded-cleaned; new Omaha server and
  its log remain intentionally active for LAN owner validation.
