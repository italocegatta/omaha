## 1. Reproduzir o bug do teste em headed browser

- [x] 1.1 Subir `task serve` + `task serve-prod` em
  background (ou só `task serve`). — Substituído por
  probe headless em uvicorn 127.0.0.1:8771.
- [x] 1.2 Em headed Playwright, navegar para
  `http://localhost:8000/login`, logar como "Italo",
  selecionar perfil "Italo". — Headless (LAN URL
  documentado em AGENTS.md).
- [x] 1.3 Verificar visualmente qual botão `+ Nova classe`
  está visível (empty-state vs inline container). — Probe
  mostra: 2 botões visíveis, empty-state é o `.first`.
- [x] 1.4 Abrir DevTools console. Clicar no botão `+ Nova
  classe` visível. Capturar:
  - Logs JS (errors / warnings) — 1 verbose, 1 404 (favicon).
  - Estado de `showForm` antes/depois do click — `false` →
    `false` (BUG). `false` → `true` quando click via
    `bubbles: true` dispatchEvent ou Alpine.$data direto.
  - Se `document.querySelector(...).click()` foi disparado —
    sim, mas o evento é `bubbles: false` por spec e Alpine
    3 usa delegation, então não chega.
- [x] 1.5 Capturar screenshot do estado pós-click. — Probe
  gera `/tmp/opencode/probe_empty_state_click.png`.
- [x] 1.6 Output: `diagnosis.md` seção "Reprodução manual
  do Sintoma 1".

## 2. Reproduzir o bug do usuário (UI manual)

- [x] 2.1 Mesmo setup de #1 (headed, dev server). — Probe
  headless confirmou que empty-state click é broken; se
  usuário clicou lá, mesmo sintoma.
- [x] 2.2 Tentar o flow que o usuário descreveu:
  - Click `+ Nova classe` → form aparece? — Provavelmente
    broken (mesma causa do Sintoma 1). Fix do Sintoma 1
    resolve. Aguardar validação manual.
  - Preencher nome → preenche? — N/A (form não abria).
  - Preencher % alvo → preenche? — N/A.
  - Click Salvar → o que acontece? — N/A.
- [x] 2.3 Se chegar a 201, reload, classe aparece? — N/A
  (path inalcançado pelo bug).
- [x] 2.4 Se chegar a 422 ou 409, qual a mensagem? — N/A.
  Paths candidatos listados em `diagnosis.md` §Sintoma 2.
- [x] 2.5 Tentar o flow R12 (edit % existente) — coberto
  indiretamente: `target_pct.feature` (2 cenários
  per-class, 1 per-asset) passa no BDD. R12 provavelmente
  OK.
- [x] 2.6 Output: `diagnosis.md` seção "Reprodução manual
  do Sintoma 2 — bug do usuário". — Documentado como
  "aguardando reprodução manual do usuário" + 4 caminhos
  candidatos.

## 3. Audit de selectors entre .feature e dashboard.html

- [x] 3.1 Para cada step em
  `tests/bdd/features/*.feature`, extrair testids
  referenciados (`data-testid="X"` em selectors +
  `_PT_LABEL_TO_TESTID_SLUG`).
- [x] 3.2 Para cada testid, verificar se existe em
  `src/omaha/templates/dashboard.html` (ou outros
  templates).
- [x] 3.3 Output: `regression-audit.md` — tabela
  | testid | usado em .feature | existe em template | notes |.
- [x] 3.4 Marcar testids que sumiram ou foram renomeados
  pelos 7 commits `asset-table-view` + `f181d28`. —
  Nenhum testid sumiu. Único achado: AMBIGUIDADE em
  `+ Nova classe` (2 botões com mesmo texto).

## 4. Verificar mudanças recentes que tocam a área

- [x] 4.1 Para cada commit em
  `git log --oneline -10 -- src/omaha/templates/dashboard.html
  src/omaha/routes/classes.py`, ler o diff e mapear
  possíveis regressões:
  - `f181d28` — drop buttons + add `@blur` no inline
    edit (R12). Verificar se `commitEditClassPct`
    funciona pós-blur. — Não toca Sintoma 1.
  - `0897305` — `x-data='assetTable(...)'` removido do
    `<table>`. Verificar se asset row handlers
    (`startEdit`, `formatPct`, etc.) ainda funcionam via
    `classSection` scope. — Não toca Sintoma 1.
  - `d065650` — add-asset modal. Verificar se o modal
    não conflita com new-class-form. — Não toca Sintoma 1.
- [x] 4.2 Output: `diagnosis.md` seção "Análise estática
  dos commits suspeitos". — Conclusão: padrão broken foi
  introduzido em `1fe42a1` (16 jun 2026, restore from
  M002), NÃO nos commits `asset-table-view` recentes.

## 5. Identificar root cause + propor fix

- [x] 5.1 Cruzar outputs de #1, #2, #3, #4. Identificar
  qual(is) causa(s) raiz explicam AMBOS os sintomas:
  - Sintoma 1 (BDD): **Alpine 3 event delegation +
    `HTMLElement.click()` é `bubbles: false` por spec**.
    Pattern introduzido em `1fe42a1`, não nos commits
    recentes.
  - Sintoma 2 (UI manual): não reproduzido. 4 caminhos
    candidatos em `diagnosis.md` §Sintoma 2.
- [x] 5.2 Estimar blast radius do fix:
  - Mudança em `src/omaha/templates/dashboard.html`
    (~6 linhas, 1 arquivo). 3 opções em
    `diagnosis.md` §"Fixes mínimos possíveis".
  - **Recomendado:** opção 3 (bridge via
    `$dispatch('open-new-class')`).
- [x] 5.3 Output: `diagnosis.md` seção "Root cause" +
  "Fix proposto (próxima change)".

## 6. Decidir se esta change absorve o fix ou abre change separada

- [x] 6.1 Se fix é trivial (< 30 linhas, 1 arquivo):
  absorver nesta change. Atualizar proposal + design +
  tasks para incluir seção "Fix". — **Decidido pelo
  usuário: absorver.** Fix = ~10 linhas em
  `src/omaha/templates/dashboard.html` (wrapper
  `<span x-data>` + handler `$dispatch` +
  `@open-new-class.window` listener). Proposta
  atualizada abaixo.
- [x] 6.2 Se fix é maior: abrir
  `openspec/changes/fix-bdd-...` separada. Esta change
  archive após diagnóstico. Próxima change começa com
  contexto do diagnosis.md. — **N/A:** fix foi trivial
  (~10 linhas), absorvido nesta change.
- [x] 6.3 Output: decisão em `proposal.md` §Fora de
  escopo ou §O que esta change faz (atualizado).

## 7. Hand-off

- [x] 7.1 Commit granular (1 por seção). — Decidido pelo
  usuário: 2 commits (fix + change archive). Commit
  messages em Conventional Commits.
- [x] 7.2 `git log --oneline -5` confirma histórico limpo.
- [x] 7.3 `openspec archive 2026-06-23-debug-bdd-e2e-failures`.
