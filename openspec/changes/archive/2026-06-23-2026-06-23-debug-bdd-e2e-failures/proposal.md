## Why

`task test-bdd` reportou 2 falhas em
`profile_isolation.feature` (retrospectiva de
`fix-bdd-workflow-reuse-gaps` rejeitou fixar como
pre-existing). Em paralelo, o usuário testou manualmente
a interface e identificou um bug na **inclusão da % alvo
da classe** (não conseguimos reproduzir automatizado
porque o teste BDD que cobre esse path está no mesmo
estado quebrado). Esta change abre uma spike de
investigação para mapear os erros que estão impactando
os testes e2e, identificando as causas raiz antes de
qualquer fix.

Estado atual da suíte BDD:

```
test-bdd: 35 passed, 2 failed
```

Falhas idênticas em ambos os cenários:

```
FAILED tests/bdd/test_scenarios.py::test_italo_classes_invisible_to_ana
  AssertionError: campo 'Nome da classe' não encontrado
  @ tests/bdd/step_defs/common_steps.py:125 (fill_field)

FAILED tests/bdd/test_scenarios.py::test_ana_classes_invisible_to_italo
  AssertionError: campo 'Nome da classe' não encontrado
  @ tests/bdd/step_defs/common_steps.py:125 (fill_field)
```

Ambos falham em
`tests/bdd/features/profile_isolation.feature` no step
inline `E preencho o campo "Nome da classe" com "RF Pós"`
logo após `E clico em "+ Nova classe"`.

## Estado atual da investigação

### Sintoma 1 — BDD: generic `fill_field` race vs Alpine `x-show`

**Onde:** `tests/bdd/step_defs/common_steps.py:107-131`
(`fill_field`). O step usa 6 selectors em ordem, com
`wait_for(state="visible", timeout=5000)` no primeiro
match de `count() > 0`:

```python
for sel in selectors:
    loc = page.locator(sel)
    if loc.count() > 0:
        try:
            loc.first.wait_for(state="visible", timeout=5000)
            loc.first.fill(value)
            return
        except Exception:
            continue
raise AssertionError(f"campo {label!r} não encontrado")
```

Para `label="Nome da classe"`, o selector preferido é
`[data-testid="new-class-name-input"]` (via
`_PT_LABEL_TO_TESTID_SLUG["Nome da classe"]`). O
elemento existe no DOM (data-testid renderizado sempre,
independente de `x-show="showForm"`). Quando o form
está fechado (`showForm=false`), o input tem
`display:none` do Alpine. O `wait_for(state="visible")`
time-out em 5s e a próxima iteração tenta outros
selectors — todos falham.

**Hipótese A (mais provável):** O botão
`+ Nova classe` clicado pelo step `click_button` é o do
**empty state** (linha 334-339 do template), NÃO o do
container inline (linha 349-355). O botão empty-state
tem `@click="document.querySelector('[data-testid=new-class-plus-btn]')?.click()"`
que deveria disparar o click programático no botão real.
Mas Playwright's `.click()` em um botão com `@click`
handler Alpine deveria funcionar — exceto se o Alpine
não inicializou (caso o `alpine:init` ainda não correu).

**Hipótese B:** Alpine `x-show` toggle leva mais que
5s para propagar (pouco provável — Alpine é síncrono).

**Hipótese C:** O click chega no botão mas o handler
Alpine falha silenciosamente (e.g. `showForm` é shadowed
por outra variável).

### Sintoma 2 — Manual: bug na inclusão da % alvo da classe

**Reportado pelo usuário** durante teste manual da
interface após `task serve`. Sintoma exato ainda não
documentado (não consegui reproduzir programaticamente
por causa do Sintoma 1 — o teste que alcançaria esse
path morre antes).

**Caminhos candidatos para "% alvo da classe":**

1. **Inline create form** (`+ Nova classe` → nome + %).
   Esse é o path que o teste `profile_isolation.feature`
   exercita. O bug pode estar no `save()` de
   `newClassForm` em
   `src/omaha/templates/dashboard.html:1326-1373`:
   ```javascript
   body: JSON.stringify({ name: self.name, target_pct: self.targetPct })
   ```
   `self.targetPct` é string (de `<input type="number">`
   via `x-model`). O backend
   (`src/omaha/routes/classes.py:360-370`) chama
   `_parse_pct(str(raw_pct))` que aceita string. Mas se
   o usuário submeter com o campo vazio,
   `raw_pct` vira `""` → `_parse_pct` retorna `None` →
   422 sem detail descritivo.

2. **Inline edit (% existente)** — R12
   (`src/omaha/templates/dashboard.html:95-115`):
   click no span `Alvo X%` vira input. Edita → blur
   PATCH. O `commitEditClassPct` em `:950` valida
   0-100 localmente, depois PATCH. Pode ter regressão
   no R12 após `0897305` que moveu `assetTable`
   methods pra `classSection`.

3. **Bug de label "Alocação alvo" vs "Alvo %"** — o
   step de teste usa literal `"Alocação alvo"` mas a
   label no HTML (`:374`) é `"Alvo %"`. O
   `_PT_LABEL_TO_TESTID_SLUG` faz o mapeamento pelo
   label "Alocação alvo" → testid
   `new-class-pct-input`. Isso funciona, mas só prova
   que o map está com alias desatualizado — não é bug
   funcional. Se alguém renomear a slug no map e
   esquecer o feature, quebra. Documentar.

### Código suspeito (mudanças recentes que tocam a área)

```
f181d28 feat(dashboard): 1400px main + Enter-or-blur commit
0897305 fix(asset-table-view): repair table reactivity and selectors after refactor
d065650 feat(asset-table-view): dashboard add-asset modal
d394d64 feat(asset-table-view): sticky alert card + per-class badges
4de6374 feat(asset-table-view): drop collapse machinery, keep groups expanded
302b973 feat(asset-table-view): inline edit for alvo % total with mutual exclusion
6429520 feat(asset-table-view): add assetTable Alpine component with sort
```

`0897305` é o mais suspeito: removeu
`x-data='assetTable(...)'` do `<table>` e moveu tudo
pra `classSection()` scope. Se algum
`@click="startEdit"` no asset row estiver fora do
scope `classSection`, Alpine throws "is not defined" e
o handler morre. Mas isso afetaria asset edit, não
class create. Hipótese secundária.

`f181d28` mexeu no inline edit (drop buttons + add
`@blur`). Pode ter introduzido regressão no R12 class
edit. Verificar se `commitEditClassPct` ainda funciona
depois desse commit.

## O que esta change faz

**Esta change foi aberta como SPIKE (sem fix) mas o
diagnóstico confirmou que o fix é trivial (~10 linhas em
1 arquivo) e o usuário decidiu absorver.** Captura
diagnóstico, regression-audit, e aplica o fix mínimo.

Investiga + corrige:

1. **Por que `+ Nova classe` não abre o form no
   `profile_isolation.feature`?** — **RESOLVIDO.** Root
   cause: empty-state button tem handler
   `@click="document.querySelector(...).click()"` MAS
   (a) o botão está fora de qualquer `x-data` (handler
   Alpine nunca executa — directive ignorada), E (b) o
   handler tentava clonar o click programaticamente via
   `HTMLElement.click()` que é `bubbles: false` por spec,
   então mesmo se executasse, Alpine 3 (event delegation
   no document) nunca veria. **Latent dead code desde
   `1fe42a1` (16 jun 2026).**
2. **O bug de % alvo reportado pelo usuário é o mesmo
   do teste ou outro?** — Provavelmente o mesmo. Form
   não abria → usuário não conseguia chegar no campo %.
   Fix do Sintoma 1 resolve. Aguardar validação manual
   do usuário.
3. **Que outras regressões foram introduzidas pelos
   7 commits `asset-table-view` + `dashboard inline
   edit`?** — **NENHUMA** que toque a área de
   `+ Nova classe`. Ver `regression-audit.md` (70
   testids auditados, 0 missing/renamed). A única
   ambiguidade é a dos 2 botões com mesmo texto,
   co-lateral ao fix.

**Fix aplicado** (em `src/omaha/templates/dashboard.html`):

- Empty-state button wrapper em `<span x-data>` para
  dar scope Alpine ao handler `@click`.
- Handler trocado para `$dispatch('open-new-class')`.
- Container `new-class-container` ganha
  `@open-new-class.window="showForm = true"` para
  receber o evento.
- 0 mudanças em `tests/bdd/`, `tests/`, rotas, ou
  qualquer outro arquivo.

**Sintoma 2 (UI manual bug do usuário)**: não foi
reproduzido programaticamente. Hipótese mais provável:
é o mesmo bug do Sintoma 1. Aguardar validação manual
do usuário. Se Sintoma 2 persistir após este fix, abrir
change separada.

## Capacidades

### Novas capacidades

(nenhuma — investigação apenas)

### Capacidades modificadas

(nenhuma)

## Impacto

**Antes do fix** (SPIKE-only): investigação pura.

**Depois do fix absorvido**:

- `src/omaha/templates/dashboard.html` — ~10 linhas
  alteradas (1 wrapper `<span x-data>`, 1 handler
  `$dispatch`, 1 listener `@open-new-class.window`,
  comentários).
- `openspec/changes/2026-06-23-debug-bdd-e2e-failures/diagnosis.md`
  — root cause confirmado + evidência empírica
  (probes headless reproduzindo o bug).
- `openspec/changes/2026-06-23-debug-bdd-e2e-failures/regression-audit.md`
  — 70 testids auditados, 0 missing, 1 ambiguidade
  (co-lateral ao fix).

Sem mudança em `tests/bdd/`, rotas, fixtures, ou
qualquer outro template.

## Fora de escopo desta change

- ~~Fix propriamente dito (vem depois)~~ — **absorvido nesta change** após decisão do usuário.
- Mudança em test fixtures
- Reativar `create_four_assets` / `switch_profile` (não
  relacionado)
- Investigação do Sintoma 2 (UI manual) — aguardando
  reprodução do usuário para confirmar se mesmo bug.
