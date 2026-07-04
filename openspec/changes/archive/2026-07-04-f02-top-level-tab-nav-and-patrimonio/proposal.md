## Why

Top-level da aplicação ainda vive num layout de "logo + side panel + conteúdo" (`templates/base.html` + `templates/_sidebar.html` + `templates/dashboard.html` + `templates/rebalance.html`). Esse formato está batendo em três limites concretos:

1. **Patrimônio e Rebalanceamento disputam o mesmo corpo**: o side panel atual carrega o formulário de aporte + botão `Rebalancear` em toda página autenticada, misturando duas responsabilidades de produto que o owner quer separar (`PRD §5.3` diz "Rebalanceamento embutido em Patrimônio"; o mock 2026-07-03 inverte isso e vira referência canônica).
2. **Não há slots para `/rentabilidade` e `/proventos`**: as duas páginas existem como ideia de roadmap (`F03`, `F04`) mas não há navegação para elas. Side panel não escala para 4 destinos.
3. **Card perfil-nível (Investido / Valor Atual / Ganho) só existe como componente implícito**: `DESIGN.md` §Component inventory descreve "Portfolio header — Invested / current / gain. The hero." mas a spec formal nunca foi escrita, então o componente corre risco de drift entre templates.

Substituir o layout por uma **top nav de 4 tabs** (Patrimônio | Rebalanceamento | Rentabilidade | Proventos) persistente em toda página autenticada destrava `F03`/`F04`, formaliza o componente `patrimonio-portfolio-header`, e elimina a `dashboard-sidebar` spec que vira histórico.

## What Changes

- **Top nav com 4 tabs** persistente em todas as páginas autenticadas, via `templates/base.html`. Tab ativa destacada com `--accent` (token existente, `D2`). Profile picker + botão `Sair` à direita.
- **Side panel removido** (`templates/_sidebar.html` deletado; `src/omaha/static/app.css` perde `.app-sidebar*`; sem drawer mobile, sem off-canvas — `D7`).
- **`dashboard.html` renomeado para `patrimonio.html`**; redistribui `Importar CSV` / `+ Classe` / `+ Ativo` no topo do body, alinhados à direita; renderiza o card `patrimonio-portfolio-header` (`D3`).
- **`rebalance.html`** ganha `Rebalancear` + form de aporte no body, sem slot lateral; rebind do novo header; drop chip `BUILDER_WARNING` do painel Avisos (`D5`).
- **Rotas top-level novas**: `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos` (`D1` — slugs PT-BR). Rotas legadas `/dashboard` e `/rebalance` deixam de responder sem alias.
- **Stubs "Em construção"** em `/rentabilidade` e `/proventos` para que a tab nav apareça completa e clicável agora (`D6`); `F03` e `F04` substituem depois.
- **Nova spec `patrimonio-portfolio-header`** descrevendo o card perfil-nível (Investido / Valor Atual / Ganho).
- **Spec `dashboard-sidebar` deprecada** e movida para archive (`D7`).
- **Spec `rebalance-page` reescrita**: form de aporte + botão Rebalancear vivem só no body de `/rebalanceamento`; sem slot lateral, sem drawer mobile (`D9`).
- **`PRD §5.3` reescrito** para refletir 4 tabs top-level + Rebalanceamento como rota própria (`D8`).
- **`DESIGN.md` §Component inventory** anotado com `Tab nav` (tokens `--accent` / `--ink` / `--bg`).

**BREAKING**: rotas `/dashboard` e `/rebalance` deixam de existir. Profile picker + Sair migram para a nova top nav; qualquer redirect legado cai em 404.

## Capabilities

### New Capabilities

- `patrimonio-portfolio-header`: card perfil-nível no topo de `/patrimonio` mostrando Investido, Valor Atual e Ganho (absoluto + percentual). Coexiste com `class-section-totals` (que continua classe-nível). Renderiza em todas as variantes de header atuais (`base.html` já emite o perfil ativo; aqui o componente só consome).

### Modified Capabilities

- `dashboard-sidebar`: deprecada — a sidebar não existe mais no produto, nem off-canvas mobile. Spec vira histórico via `openspec-archive-change` no fluxo do `apply`. Nenhuma req substituta.
- `rebalance-page`: form de aporte + botão `Rebalancear` vivem **apenas** no body de `/rebalanceamento`. Removida a req "Sidebar carries the rebalance form on every authenticated page". Removida qualquer referência a off-canvas mobile. Rota dedicada, sem slot lateral.

### Unchanged Capabilities (citado para contexto)

- `dashboard-inline-editing` (`D4`): o `×` de delete por classe já é coberto aqui ("× delete button is always visible, red on hover" + "Remoção de classe com confirmação"). `F02` só precisa garantir que continua renderizando no header da classe após o rename `dashboard.html` → `patrimonio.html`. Sem delta spec.
- `cross-profile-sharing`, `dev-tasks`, `auth`, `color-tokens`, `csv-seed-pipeline`: nenhuma mudança.

## Impact

- **Templates**: `base.html`, `dashboard.html` (rename → `patrimonio.html`), `rebalance.html` reescritos; `_sidebar.html` deletado; `rentabilidade.html` e `proventos.html` novos (stubs).
- **Rotas**: `src/omaha/routes/pages.py` ganha 4 endpoints top-level e perde `/dashboard` + `/rebalance`.
- **CSS**: `src/omaha/static/app.css` ganha `.tab-nav`, `.tab-nav__btn`, `.tab-nav__btn--active`; perde regras `.app-sidebar*`.
- **Specs**: `openspec/specs/patrimonio-portfolio-header/spec.md` (novo); `openspec/specs/dashboard-sidebar/spec.md` → delta `## REMOVED`; `openspec/specs/rebalance-page/spec.md` → delta de rewrite.
- **PRD**: `openspec/PRD.md §5.3` reescrito para refletir 4 tabs top-level + Rebalanceamento próprio.
- **Design**: `DESIGN.md §Component inventory` anota `Tab nav`.
- **Testes**: smoke visual via `task test-e2e` para a nova top nav; BDD steps em `tests/bdd/step_defs/` para `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos`. Sem mudança em unit/integration já existentes.
- **Sem deps externas novas**. Alpine.js + Tailwind continuam suficientes.
- **Sem migração de DB**. Sem mudança em `scripts/seed_from_csv.py` ou `data/seed/`.