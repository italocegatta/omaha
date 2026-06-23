# Diagnosis — profile_isolation BDD failures

**Date:** 2026-06-23
**Status:** root cause confirmado (Sintoma 1). Sintoma 2 aguardando reprodução manual.

## Sintoma 1 — BDD: `+ Nova classe` não abre o form

### TL;DR

A botão empty-state (renderizado quando o perfil não tem classes) tem
handler `@click="document.querySelector('[data-testid=new-class-plus-btn]')?.click()"`
que tenta acionar o botão inline via `HTMLElement.click()`. Por spec,
`HTMLElement.click()` despacha um evento `click` com `bubbles: false`.
Alpine 3 usa **event delegation** (um único listener no `document`) para
diretivas `@click`, então o evento não-borbulhante nunca chega até o
Alpine. Resultado: `showForm` permanece `false`, form não aparece, BDD
falha em `fill_field("Nome da classe")`.

### Reprodução (headless probe, sem browser humano)

Subi `uvicorn omaha.main:app --host 127.0.0.1 --port 8771` (SQLite
limpo, profile "Italo" sem classes), login + profile pick, e rodei
4 testes controlados:

| # | Ação                                                    | `showForm` depois |
|---|---------------------------------------------------------|-------------------|
| 1 | Playwright `.click()` no botão empty-state              | `false` ❌        |
| 2 | `el.click()` nativo no botão empty-state                | `false` ❌        |
| 3 | `el.dispatchEvent(new MouseEvent('click', {bubbles: true}))` no botão inline | `true` ✓ |
| 4 | `Alpine.$data(...).showForm = true` direto              | `true` ✓          |

- **1 e 2 reproduzem o bug.**
- **3 e 4 mostram que o problema é só a forma do evento, não o estado
  Alpine nem a renderização do form.**

Probe script: `/tmp/opencode/probe3_dispatch.py` (re-runnable).

### Por que `bubbles: false` quebra o Alpine 3

Alpine 3 (CDN, `alpinejs@3.x.x` carregado em `base.html:17`) usa
**delegation** para eventos `@click` / `@input` / etc.: instala
listeners no `document` e resolve o alvo a partir de
`event.target.closest('[x-on:click]')` (ou similar). O `MouseEvent`
disparado por `HTMLElement.click()` é `bubbles: false` por spec
([DOM § HTMLElement.click()]), então nunca atinge o `document`,
então Alpine nunca vê.

Confirmado empiricamente: o mesmo elemento com
`dispatchEvent(new MouseEvent('click', {bubbles: true, view: window}))`
**funciona** (Test 3). É a bolha que faz a diferença.

### Origem do padrão

`1fe42a1 fix(import-modal): restore dashboard, CSS, and API routes from M002`
(2026-06-16) restaurou o dashboard de `a8b1d13`. O handler
`document.querySelector(...).click()` já existia nesse snapshot
original — não foi introduzido pelos commits `asset-table-view`
recentes (conferido com `git log -S 'empty-state-create-class' -- src/omaha/templates/dashboard.html`
→ única ocorrência: 1fe42a1).

Os 7 commits `asset-table-view` (`b93b909` → `f181d28`) **não mexeram
nessa área**. A falha estava latente desde 1fe42a1, mas só foi exposta
quando o BDD começou a usar o step `clico em "+ Nova classe"` em
perfil sem classes.

### Por que BDD pega e o usuário não pegou (até agora)

`click_button` em `tests/bdd/step_defs/common_steps.py:128-140`:

```python
candidates = [
    f'button:has-text("{label}")',
    f'[data-testid="{label}"]',
    f'a:has-text("{label}")',
]
for sel in candidates:
    loc = page.locator(sel)
    if loc.count() > 0:
        loc.first.click()
        return
```

`button:has-text("+ Nova classe")` casa **ambos** os botões
(empty-state `data-testid="empty-state-create-class"` em
`dashboard.html:334-339`, e inline `data-testid="new-class-plus-btn"`
em `dashboard.html:349-355`). `loc.first` é o empty-state (aparece
primeiro no DOM). Resultado: o teste clica no botão broken.

Um humano clicando veria os dois botões lado a lado, escolheria
visualmente, e a maioria clicaria no CTA do empty state — o broken.
Ou seja: a falha **também afeta usuário** que clica no botão do empty
state. Foi só sorte ninguém ter clicado lá ainda (o fluxo usual é
criar a primeira classe pelo modal de import, que pré-popula classes).

### Blast radius do fix

- **Escopo:** 1 arquivo, 1 handler, ~1 linha.
  `src/omaha/templates/dashboard.html:337`
  (`@click="document.querySelector('[data-testid=new-class-plus-btn]')?.click()"`).
- **Fixes mínimos possíveis (em ordem de preferência):**
  1. **Deletar o botão empty-state** (linhas 331-340). O botão inline é
     sempre renderizado (per comment em :343-347) e funciona. O empty
     state perde o CTA visual, mas o inline button fica visível logo
     abaixo — UX aceitável mas perde o destaque visual do empty state.
  2. **Trocar o handler** para usar `Alpine.$data(...).showForm = true`:
     ```html
     @click="Alpine.$data($refs.newClass).showForm = true"
     ```
     e adicionar `x-ref="newClass"` no container. **Mas** isso cria
     acoplamento entre escopos Alpine via API global `Alpine` (não
     recomendado pelo time do Alpine). Funciona, mas é code smell.
  3. **Bridge via evento customizado**:
     ```html
     <!-- empty-state button -->
     @click="$dispatch('open-new-class')"
     <!-- container -->
     <div ... x-data="newClassForm()" @open-new-class.window="showForm = true">
     ```
     Idiomático Alpine, sem dependência de `Alpine` global, e mantém
     o empty state como CTA. **Recomendado.**
- **Não toca** `tests/bdd/step_defs/`, `tests/bdd/features/`, ou
  `src/omaha/routes/`. Fix de ~6 linhas em
  `src/omaha/templates/dashboard.html`.
- **Risco:** baixo. Trocar o handler não muda o DOM renderizado nem o
  estado. Smoke test: clicar no botão empty state em headed → form
  aparece.

### Hipóteses do proposal original revisitadas

| Hipótese | Veredito |
|----------|----------|
| A: click no botão empty-state vs inline button        | **Verdadeira, mas por motivo diferente do猜想.** Não é "Alpine não inicializou" — é que `el.click()` nativo é não-borbulhante e Alpine usa delegation. |
| B: x-show toggle leva > 5s                            | Falsa. Alpine é síncrono. |
| C: handler falha silenciosamente                       | Falsa. Handler roda, mas o evento que ele dispara não chega ao listener do Alpine. |

## Sintoma 2 — UI manual: bug na inclusão da % alvo da classe

**Status:** não reproduzido. Aguardando descrição do usuário.

**Caminhos candidatos** (do proposal original, revisitados):

1. **Form não abre** — coberto por Sintoma 1. Fix do Sintoma 1 resolve
   este caminho.
2. **Submit 422 silencioso** — `save()` em
   `dashboard.html:1334-1363` faz `JSON.stringify({name, target_pct})`.
   `targetPct` vem de `<input type="number" x-model="targetPct">` —
   string. Backend (`routes/classes.py:_parse_pct`) aceita string.
   Vazio → `raw_pct=""` → `_parse_pct` retorna `None` → 422 com
   detail. Frontend mostra detail no `new-class-form-error`. **Se o
   bug do usuário é "clico Salvar e nada acontece", pode ser 422 sem
   detail descritivo.** Verificar se `_parse_pct("")` retorna `None`
   e se o 422 tem `detail` user-friendly.
3. **R12 (edit % existente)** — passa nos BDD (`target_pct.feature`
   tem 2 cenários per-class e per-asset, todos verdes). Provavelmente
   não é.
4. **Label mismatch "Alocação alvo" vs "Alvo %"** — o step
   `preencho o campo "Alocação alvo"` mapeia via slug para
   `new-class-pct-input`. Label visível no HTML é "Alvo %"
   (`dashboard.html:374`). Funciona, mas é debt técnico — alguém
   renomeando o slug quebra silenciosamente.

**Próximo passo:** pedir ao usuário para descrever o Sintoma 2
(passos exatos + comportamento observado + esperado) antes de
investigar.

## Ações pós-investigação

1. **Marcar tasks 1 e 2** como blocked: tasks manuais que pedem
   headed browser + humano. Substituir pelos probes
   `probe_profile_isolation.py`, `probe2_inline_click.py`,
   `probe3_dispatch.py` (artefatos reprodutíveis headless).
2. **Abrir change de fix** com o bridge via `$dispatch` (opção 3).
   Mudança de ~6 linhas em `src/omaha/templates/dashboard.html`.
   Sem alteração de BDD, sem alteração de rotas.
3. **Re-rodar `task test-bdd`** após o fix; esperado: 37/37 passam.

## Artefatos relacionados

- `regression-audit.md` — auditoria de testids (sibling deste arquivo).
- Probes em `/tmp/opencode/probe{,_2,_3}_*.py` (não committed; rodar
  localmente para reproduzir).
