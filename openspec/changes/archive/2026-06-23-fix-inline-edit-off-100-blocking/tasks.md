## 1. Removendo guards client-side no editor inline

- [x] 1.1 Em `src/omaha/templates/dashboard.html:966-972`, remover o guard `if (isNaN(parsed) || parsed < 0 || parsed > 100)` do topo de `commitEditClassPct`. Adicionar logo no início da função a guarda de re-entrância `if (this.editingClassPct === false) return;` para impedir que o `@blur` dispare um segundo PATCH após o Enter já ter limpado `editingClassPct`.

- [x] 1.2 Em `src/omaha/templates/dashboard.html:1053-1061`, remover o bloco `if (this.classDeltaMessage !== '') { this.error = this.classDeltaMessage; return; }` do topo de `commitEdit`. A guarda de re-entrância `if (this.editingAssetId === null) return;` (linha 1054) permanece.

- [x] 1.3 Em `src/omaha/templates/dashboard.html:1123-1140`, remover os 3 guards de `commitEditTotal`: range 0-100 (linhas 1126-1130), `classTargetPct <= 0` (linhas 1131-1134), e `newTargetPct < 0 || newTargetPct > 100` (linhas 1136-1139). Adicionar logo no início da função a guarda de re-entrância `if (this.editingTotalAssetId === null) return;`.

- [x] 1.4 Verificar que o servidor (`routes/classes.py:434-447` e `routes/assets.py:367-373`) trata todos os 422 com `detail` user-friendly. Confirmar via grep que cada `r.json().then(body => throw new Error(body.detail))` no client está consumindo o `detail` corretamente (já está nas linhas 985, 1078, 1153).

- [x] 1.5 Confirmar que `classDelta` / `classDeltaMessage` (linhas 846-862) e o `classSum` store (linhas 1399+) continuam computando a soma per-classe em tempo real. Não devem ser removidos — apenas perdem o papel de gate.

## 2. Adicionando cenário BDD para o caso reportado

- [x] 2.1 Em `tests/bdd/features/target_pct.feature`, adicionar (após o cenário "Per-class sum off-100 é aceito (D006)" existente) um novo `Esquema do Cenário: Inline edit off-100 é aceito (D006)`. Setup: classe "RF Pós" 50% + 2 ativos "Tesouro Selic 2029" 40% e "Tesouro IPCA 2029" 40% (soma per-classe 80). Ação: clicar no campo "Alocação alvo da carteira" do ativo "Tesouro Selic 2029", digitar "80", pressionar "Enter" (soma resultante 80+40=120, "Sobra 20%"). Asserts: `a alocação salva do ativo "Tesouro Selic 2029" é "80.00%"` E `a seção "RF Pós" contém 2 ativos`. Cobre Italo + Ana via `Exemplos`.

- [x] 2.2 Rodar `uv run task test-bdd` e confirmar que o cenário novo passa. (Pré-requisito: o servidor de testes BDD e o DB de teste precisam estar funcionais. Se o BDD suite inteiro estiver quebrado por causa do `M002_RESSALVA_DIAGNOSIS.md` apontado, abrir follow-up em vez de tentar fix em escopo deste change.)

## 3. Verificação

- [x] 3.1 Rodar `uv run task lint` para garantir que a remoção dos guards não quebrou formatação ou imports.

- [x] 3.2 Rodar `uv run task test-unit` e `uv run task test-integration` para confirmar zero regressão nos tests que dependem do range per-row 0-100 (ex.: `tests/test_t02_classes_routes.py:341-360` rejeita target_pct negativo ou > 100 com 422 — esses testes não devem mudar de resultado porque o servidor já trata isso).

- [x] 3.3 Verificação manual headed (obrigatória, conforme precedente do `dashboard-width-and-inline-edit`): cobrir via cenário BDD "Inline edit off-100 é aceito (D006)" — Playwright real browser exercita o caso reportado (asset 40→80, soma 120, Enter, valor persiste). Re-entrance guards (`commitEditClassPct`, `commitEdit`, `commitEditTotal`) revisados por leitura de código. Operador optou por pular headed manual nesta sessão; pode rodar `task serve` + checklist depois.

## 4. Finalização

- [x] 4.1 Rodar `openspec validate fix-inline-edit-off-100-blocking` e garantir coerência dos artefatos.

- [x] 4.2 NÃO arquivar esta change nesta sessão — o operador pediu para resolver os tests `_disabled/` em change separada. Após implementar e validar, abrir a change de rework da suíte e2e (`fix-e2e-suite-and-disabled-tests` ou nome similar) e arquivar ambas em conjunto. (Operador pediu sync+archive conjunto das 4 changes em sessão posterior.)

## 5. Follow-up: fix da "linha pula após PATCH" (row-pin)

Descoberto na verificação manual pós-deploy: o `target_pct` da PATCH
muda a posição do ativo no `sortedAssets` (sort default = `target_pct`
asc). O usuário clica numa linha, digita 80, Enter → o ativo pula
para o final da lista. A linha do topo passa a mostrar outro ativo
(o novo menor `target_pct`) e o usuário pensa que "o valor não
persistiu". Browser test em `RF Dinâmica` confirmou: asset 29 (CPTI11)
estava no topo com 10%, mudou para 80%, **saiu da linha 1** apesar
do PATCH ter retornado 200 e o estado Alpine estar correto
(`target_pct: 80`).

Fix: novo par `frozenAssetId` + `frozenIndex` no `classSection`.
`startEdit` / `startEditTotal` capturam o índice atual no sort;
`sortedAssets` re-ordena normalmente e depois re-insere o asset no
`frozenIndex` via `_pinFrozen`. O pin é limpo em `sortBy` (próximo
sort é do usuário) e em `cancelEdit*` (Escape / blur sem PATCH).
**Não** é limpo em PATCH bem-sucedido — senão a linha pula
imediatamente. Browser test pós-fix: asset 29 clicado na linha 1
com 10%, mudou para 80%, **continua na linha 1** mostrando 80.00%.

- [x] 5.1 Adicionar `frozenAssetId`/`frozenIndex` no state de `classSection` em `src/omaha/templates/dashboard.html`.
- [x] 5.2 Implementar `_pinFrozen` (splice do asset no `frozenIndex` após o sort natural) e chamar de `sortedAssets`.
- [x] 5.3 `startEdit` / `startEditTotal` setam o pin com o índice atual; `sortBy`, `cancelEdit`, `cancelEditTotal` limpam.
- [x] 5.4 Browser test E2E confirma que a linha do ativo editado fica visualmente estável após PATCH bem-sucedido.
- [x] 5.5 Reverter as mutações de teste no DB do usuário (7 ativos em `RF Dinâmica` voltaram aos valores originais).
- [x] 5.6 `uv run task lint`, `test-unit` (124), `test-integration` (192), `test-bdd` (37) — todos passam.
- [ ] 5.7 Abrir nova change `fix-asset-row-pin-bdd-coverage` para adicionar cenário BDD que cobre o row-pin (clica, edita, asserts a posição visual da linha não muda). Escopo separado do `_disabled/` rework.
