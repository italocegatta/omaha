## Context

A aplicação hoje serve conteúdo autenticado num layout "logo + side panel + conteúdo":

- `templates/base.html` carrega logo + (futura) top nav stub + slot de sidebar + `{% block content %}`
- `templates/_sidebar.html` carrega wordmark serif + 3 botões de ação (`Importar CSV`, `+ Novo ativo`, `+ Nova classe`) + form de rebalance + drawer mobile off-canvas
- `templates/dashboard.html` renderiza header `patrimonio-portfolio-header` implícito + cards de classe + onboarding card
- `templates/rebalance.html` renderiza form de aporte + botão `Rebalancear` no **slot da sidebar** (extraído do mesmo include), mais o plano + tabelas + warnings

Esse arranjo tem três limitações:

1. **Layout confunde dois produtos.** O form de rebalance fica disponível em toda página autenticada (incluindo a dashboard), misturando o ato de "ver patrimônio" com "rebalancear". O owner quer separar (`D8`: PRD §5.3 reescrito, Rebalanceamento como rota própria top-level).
2. **Não escala.** Quando `F03` (Rentabilidade) e `F04` (Proventos) entrarem, sidebar precisa crescer — sidebar de botões não comporta navegação top-level.
3. **Spec `dashboard-sidebar` virou dívida técnica.** Descreve um componente que vai sair; precisa ser deprecada antes de virar legado (`D7`).

Stack continua a mesma: FastAPI + Jinja2 + Alpine.js (sem JS framework novo); `app.css` com classes Tailwind-like utilitárias; tokens em `oklch()` via `color-tokens`; PT-BR na UI.

## Goals / Non-Goals

**Goals:**

- Top nav com 4 tabs (Patrimônio | Rebalanceamento | Rentabilidade | Proventos) persistente em todas as páginas autenticadas
- Side panel removido sem substituto (sem drawer mobile, sem off-canvas)
- Rotas top-level PT-BR: `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos` (slugs `D1`)
- Stubs "Em construção" em `/rentabilidade` e `/proventos` para que a tab nav apareça completa e clicável (`D6`)
- Botões `Importar CSV` / `+ Classe` / `+ Ativo` migram para o topo do body de `/patrimonio`, alinhados à direita
- Card `patrimonio-portfolio-header` vira spec formal (`D3`)
- Spec `dashboard-sidebar` deprecada e movida para archive no fluxo do apply (`D7`)
- Spec `rebalance-page` reescrita: form de aporte + `Rebalancear` no body, sem slot lateral (`D9`)
- PRD §5.3 + `DESIGN.md §Component inventory` refletem a nova arquitetura

**Non-Goals:**

- Implementar `Rentabilidade` e `Proventos` de fato — só stubs. `F03` e `F04` cuidam disso depois.
- Trocar tema visual, palette ou tokens. `F05` (dark mode) é outro slice.
- Adicionar dark mode toggle, animações complexas, ou novo framework JS.
- Renomear rotas existentes de API (`/api/*`) — só rotas de página.
- Migrar `_sidebar.html` para um componente reutilizável — `_sidebar.html` é deletado, não portado.
- Manter alias de `/dashboard` ou `/rebalance` — quebra explícita (decisão do owner).

## Decisions

### D1. Slugs PT-BR definitivos: `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos`

**Por quê**: copy é PT-BR; URLs seguem a mesma língua para reduzir carga cognitiva (decisão do owner no grill 2026-07-03). `/rebalance` legado sai sem alias — qualquer redirect automático esconde bugs em testes e2e. `D1` registrado.

**Alternativas**: manter `/dashboard` (recusa owner — não bate com PRD §1). Alias `/dashboard → /patrimonio` (recusa owner — esconde quebra). Rejected.

### D2. Tab ativa usa `--accent` (token existente)

**Por quê**: `color-tokens` já define `--accent` (`oklch(0.42 0.09 150)`, fern) como o "ponto de cor" do produto. Reusar mantém paleta coerente e não requer `R03` (extract quote provider) nem expansão de `DESIGN.md`. Tab inativa usa `--ink` no texto, sem fill. `D2` registrado.

**Alternativas**: criar `--tab-active-bg` novo (rejected — adiciona token sem motivo). Usar `--ink` invertido com fill (`--bg`) (recusado — fica igual a body e tab some). Border-bottom 2px com `--accent` (considerado — escolhido underline com `--accent`, não fill).

### D3. `patrimonio-portfolio-header` vira spec, mas `class-section-totals` permanece intocado

**Por quê**: o componente já existe implicitamente em `dashboard.html` (parcial com 3 métricas: Investido / Valor Atual / Ganho). `DESIGN.md §Component inventory` já o descreve como "Portfolio header — Invested / current / gain. The hero.". Formalizar a spec reduz drift; `class-section-totals` é classe-nível, não perfil-nível — granularidade diferente, fica separado.

**Alternativas**: tentar fundir `patrimonio-portfolio-header` e `class-section-totals` num único spec (rejected — escopos diferentes: um é o hero do perfil, outro é o resumo da classe). Refatorar o card enquanto vira spec (out of scope — `R04` é a fatia de partialização).

### D4. `dashboard-inline-editing` fica intocado, só verifica que `×` continua renderizando após o rename

**Por quê**: spec já cobre "× delete button is always visible (discreet by default, red on hover)" + "Remoção de classe com confirmação". `F02` não muda contrato. O rename `dashboard.html → patrimonio.html` é puramente cosmético.

### D5. Drop chip `BUILDER_WARNING` do painel Avisos

**Por quê**: o chip duplica a informação — o `<code>` no início do `<li>` já carrega o código. Mantendo só o `<code>` em monospace e a mensagem PT-BR como body text, o painel fica mais limpo. Aplica-se a qualquer `<li>` com código de aviso do solver. `D5` registrado.

### D6. Stubs "Em construção" agora, conteúdo real depois

**Por quê**: se a tab nav aparece com 3 links funcionando e 1 quebrado (`/rentabilidade` 404), o owner não consegue avaliar a navegação completa. Stubs curtos (heading "Em construção" + body "Esta página será preenchida em uma fatia futura.") garantem que a tab nav aparece completa no screenshot do grill.

### D7. `dashboard-sidebar` sai do active set

**Por quê**: sidebar não existe mais no produto. Sem drawer mobile, sem off-canvas. Spec vira histórico; archive via `openspec-archive-change` no fluxo do apply de `F02`. Não há substituto (não há mais nada off-canvas). `D7` registrado.

### D8. PRD §5.3 reescrito no mesmo PR

**Por quê**: divergência resolvida no mock 2026-07-03. Texto atual "Rebalanceamento embutido em Patrimônio" → reescrito para "4 tabs top-level: Patrimônio | Rebalanceamento | Rentabilidade | Proventos". Mesma mudança de copy + mesmo PR do `propose`. `D8` registrado.

### D9. `rebalance-page` rewrite

**Por quê**: req "Sidebar carries the rebalance form on every authenticated page" deixa de existir (não há mais sidebar). Form de aporte + botão `Rebalancear` vivem só no body de `/rebalanceamento`. Spec passa a descrever: rota dedicada (`/rebalanceamento`), form no body, sem slot lateral, sem drawer mobile. `D9` registrado.

**Sobre a req "Header navigation row on the rebalance page"** (com link `← Dashboard` e label `Plano de aporte`): também removida. A top nav global substitui — não há mais navegação por-card dentro do body. Removida sem substituto.

## Risks / Trade-offs

- **Quebra de testes e2e existentes** (`tests/e2e/` espera `data-testid="app-sidebar"`, `data-testid="sidebar-wordmark"`, `data-testid="app-header-hamburger"`, `data-testid="rebalance-form"`) → Mitigação: roda `task test-e2e` no apply; e2e suite precisa de update em batch dentro do mesmo PR. `T01` cobre isso depois, mas o subset do `F02` precisa ser corrigido no apply.
- **BDD steps em `tests/bdd/step_defs/_workflows.py`** referenciam `/dashboard` e `/rebalance` em `given` steps → Mitigação: substituir pelas novas rotas no apply, em batch.
- **Redirects silenciosos** (HTTP 301/302 de `/dashboard → /patrimonio`) esconderiam testes quebrados → Mitigação: 404 explícito. Owner pediu quebra visível.
- **`tokens.css` ou `--accent` mudar entre apply de `F02` e `F05`** (dark mode) → Mitigação: `F02` reusa o token existente sem alteração; se `F05` inverter palette, a tab nav inverte junto, sem custo extra.
- **Specs ficam grandes** (4 capabilities tocadas) → Mitigação: delta + REMOVED + NEW separados por arquivo; archive consolida no `archive/` final.
- **`_sidebar.html` deletado quebra import em qualquer partial esquecido** → Mitigação: `rg "_sidebar.html"` no apply antes de remover; se sobrar referência, ajustar no mesmo PR.

## Migration Plan

1. **Apply (gate 2)**:
   - Rename `dashboard.html` → `patrimonio.html` mantendo git history (`git mv`)
   - Reescrever `base.html` (top nav, sem slot sidebar)
   - Reescrever `patrimonio.html` (header novo + botões no topo do body)
   - Reescrever `rebalance.html` (form no body)
   - Criar `rentabilidade.html`, `proventos.html` (stubs)
   - Deletar `_sidebar.html`
   - Atualizar `routes/pages.py` (rotas novas + remoção legadas)
   - Atualizar `app.css` (`.tab-nav*` + remover `.app-sidebar*`)
   - Atualizar `DESIGN.md`, `PRD.md §5.3`
2. **Archive (gate 3)**:
   - `dashboard-sidebar` → archive via `openspec-archive-change`
   - `rebalance-page` e `patrimonio-portfolio-header` → archive (junto)
3. **Rollback**: reverter o PR (todas as mudanças estão no mesmo commit por causa do scope). Não há migração de DB.

## Open Questions

Nenhuma no momento — todas as decisões D1-D9 estão fechadas pelo grill 2026-07-03. Próximas ambiguidades possíveis (escopo de F03/F04, fontes de dados de proventos) ficam fora deste `F02`.
