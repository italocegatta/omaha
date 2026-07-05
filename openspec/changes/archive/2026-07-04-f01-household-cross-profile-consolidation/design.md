## Context

Hoje o `/patrimonio` (canônico pós-`F02`) sempre renderiza o **perfil ativo** (`session["active_profile_id"]`). O header oferece um `<select>` (`header-profile-switcher`) que troca o perfil e a `spec cross-profile-sharing` permite ao operador ver e mutar qualquer perfil que ele possua. Falta uma terceira granularidade: enxergar a soma de **todos** os perfis do `viewer` (`User.profiles`).

A granularidade household é o que a persona Operadora (`PRD §1.2`) precisa para responder à pergunta "quanto a família tem investido como um todo?", sem alternar manualmente o chip e somar mentalmente o card `patrimonio-portfolio-header` de cada perfil. Sobe sem quebrar o isolamento per-profile — o agregado só lê `Position` rows onde `AssetClass.profile_id IN (profile.id for profile in viewer.profiles)`.

A spec base (`cross-profile-sharing`) já cobre os contratos de quem-pode-ver-quem. F01 adiciona apenas o modo de leitura household — não mexe em isolamento, não expõe fronteiras `User`, e não introduz um terceiro perfil oculto.

## Goals / Non-Goals

**Goals:**

- Adicionar `view=household` (querystring) em `GET /patrimonio` que re-renderiza o card `patrimonio-portfolio-header` somando todos os perfis do viewer
- Manter `/patrimonio` (per-profile) como default e byte-equivalente ao comportamento atual
- Toggle `Casa` no header ao lado do profile picker — form HTML padrão, sem Alpine
- Modo household é read-only: `+ Classe`, `+ Ativo`, `Importar CSV`, edição inline, e o botão `Rebalancear` somem ou ficam `disabled`; mutações API retornam `409`
- Reusar `portfolio_aggregates(...)` forma de soma via nova função `household_aggregates(...)`; sem nova rota, sem nova tabela

**Non-Goals:**

- Não criar tabela nova de "household" nem snapshot agregado persistido
- Não introduzir `view` em outras rotas (`/rebalanceamento` etc.) nesta fatia — escopo é `/patrimonio` apenas
- Não mexer em isolamento `User`-a-`User` — F01 é intra-User
- Não introduzir toggle estilo "casa" no mobile ou animações: a UI é o chip discreto `Casa`
- Não escrever testes e2e novos (Playwright) aqui — esses são cobertos em `T01` (BDD+e2e 100% green); F01 cobre integration + BDD step drift

## Decisions

### Decision 1. URL strategy: `?view=household` querystring (not new route)

**Por quê**: o conteúdo do `/patrimonio` é o mesmo template com um branch — não justifica rota dedicada. Mantém `/patrimonio` como URL canônica que já está arquivada pelo `F02 D1`. Toggle como `<form method="get">` que submete `?view=household` ou remove o parâmetro para voltar ao per-profile.

**Alternativas**: `/patrimonio/casa` como rota separada (recusado — duplica o template, dois lugares para manter). Cookie de sessão (recusado — quebra deep-link, operator pode querer mandar o link da casa a outra pessoa — sem mand, então não há motivo para persistir). Rejected.

### Decision 2. Toggle no header, à esquerda do profile picker

**Por quê**: a ação "ver casa" é uma operação sobre o conjunto de perfis que o viewer possui, então mora **no header** (com o resto da navegação de identidade) e não no body de `/patrimonio`. Profile picker + household toggle formam a "persona" do operador; tabs (`F02`) formam a navegação entre produtos. Mesma separação funciona.

**Alternativas**: botão no canto-superior-direito do body, perto do card `patrimonio-portfolio-header` (recusado — confunde com ação "do produto", e só funciona em `/patrimonio`, não em outras tabs). Dropdown no profile chip (recusado — esconde, deveria ser discoverable). Rejected.

### Decision 3. Read-only no modo household

**Por quê**: rebalance é por perfil (`rebalance-engine` resolve cobertura por classe dentro do perfil ativo). Soma cross-profile não tem semântica natural para o solver (qual perfil recebe o aporte? cada um proporcionalmente? rateio? — fora de escopo). Mutações de classe/ativo importam posições para o perfil ativo — colapsar isso no agregado cria ambiguidade. Por isso: desabilitado, com 409 API e botões ocultos/disabled na UI.

**Alternativas**: oferecer "importar CSV para todos os perfis" no modo household (recusado — escopo vira dois imports paralelos, fora do PRD §4.3 e do caminho CSV). Permitir rebalance cross-profile (recusado — sumidouro de decisões de produto, sem sinal claro do owner). Rejected.

### Decision 4. Toggle oculto quando viewer tem 1 perfil

**Por quê**: quando o viewer só tem um perfil, "casa" == "perfil"; mostrar o toggle seria ruído. Reduz surface da UI em casos onde não agrega valor. Edge case do test (`/patrimonio?view=household` é harmless) documentado na spec.

### Decision 5. `household_aggregates` é função-espelho, não generalização de `portfolio_aggregates`

**Por quê**: a forma da resposta (`{"portfolio": {...}, "classes": [...]}`) bate byte-a-byte para que o template `patrimonio.html` consuma a mesma estrutura com um branch (`{% if view == 'household' %} ...`). Generalizar a função para aceitar `Iterable[AssetClass]` é tentador mas aumenta blast radius — refator com `T03` mutation testing ou um `R0X` dedicado. F01 prefere duplicação mínima com invariante explícita.

**Alternativas**: generalizar `portfolio_aggregates(list[AssetClass])` para `portfolio_aggregates(iterable_of_classes)` + flag `scope` (recusado — explode blast radius e arrasta audit pipeline). Rejected.

### Decision 6. Não mexer em `routes/classes.py`, `routes/assets.py`, `routes/imports.py` no apply

**Por quê**: a `spec cross-profile-sharing` já exige que as mutações respeitem `active_profile_id`. Adicionar gate "household_read_only" nesses handlers é uma camada a mais — mas é contratualmente declarada na nova req. Decisão: gate é aplicado via **dependency injection** num helper novo (`require_profile_writable`) que todas as rotas de mutação passam a usar. Isso mantém a mudança concentrada no apply e testável de forma isolada.

**Alternativas**: checagem inline `if household: raise 409` em cada handler (recusado — duplica, fácil de esquecer numa nova rota futura). Middleware FastAPI (recusado — mágico demais para um único modo de leitura). Rejected.

## Risks / Trade-offs

- **Toggle exposto em todas as páginas autenticadas**: o form é nativo, sem JS, e o botão só submete de volta para `/patrimonio?view=household`. Em outras tabs (ex. `/rebalanceamento`), o click leva à tab Patrimônio no modo casa — isso é aceitável (uma ação explícita do operador).
- **Performance**: a query que carrega `AssetClass → Asset → Position` para todos os perfis do viewer pode ser pesada com 2 perfis seed (já funciona) e degrada com perfis adicionais. Mitigação: o eager-load atual já usa `selectinload`; o agregado reutiliza a mesma estratégia. Se virar gargalo, `R03` (extract quote provider adapter) já é precedido por auditoria de queries — ponto de captura fica nos testes de integration existentes.
- **Testes e2e + BDD drift**: o toggle é novo e o seletor `data-testid="household-toggle"` precisa ser inventário. `T01` cobre; mas este slice precisa pelo menos (a) atualizar o seletor inventory em `tests/e2e/selectors.py`, e (b) adicionar uma BDD scenario em `profile_sharing.feature`. T05 (`BDD step-def drift after F02`) é o precedente — não acumula aqui, vai pro tracking natural do roadmap.
- **Class colors per-profile**: `portfolio_aggregates` usa a paleta `_CLASS_COLORS` por **índice de posição** na lista. No agregado household, classes com mesmo nome em perfis distintos vão colidir de cor. Decisão: ok por ora — o agregado é analítico, não operacional. Adicionar **dedup por `(class_name, profile_id)`** se virar reclamação; cabe em F01 ou fica para um `R0X`.

## Migration Plan

1. **Apply gate 2**:
   - Adicionar helper `household_aggregates(...)` espelhado em `src/omaha/routes/pages.py`.
   - Adicionar branch `view=household` em `GET /patrimonio` e `_render_patrimonio`.
   - Adicionar `require_profile_writable` dependency em `src/omaha/auth.py` (ou novo arquivo `src/omaha/auth_household.py`).
   - Aplicar `require_profile_writable` em `routes/classes.py`, `routes/assets.py`, `routes/imports.py`.
   - Adicionar `<form data-testid="household-toggle" method="get" action="/patrimonio">` em `templates/base.html` ao lado do profile picker (renderizado quando `len(profiles) >= 2`).
   - Adicionar classes `.app-header__household-chip`, `.is-read-only` em `src/omaha/static/app.css` (tokens existentes — sem novos).
   - Adicionar branch `{% if view == 'household' %}` em `templates/patrimonio.html` para o card, classes e ações.
   - Atualizar `PRD §5.3` (linha de F-slices concluídas) marcando F01 como entregue.
2. **Validation gate**:
   - `openspec validate f01-household-cross-profile-consolidation --json` retorna `valid: true`.
   - `task test-integration` cobre o aggregator e as 5 rotas de mutação em modo household.
   - `task test-bdd` cobre o step em `profile_sharing.feature`.
3. **Archive gate 3**:
   - `openspec-archive-change`: change vai para `openspec/changes/archive/2026-07-04-f01-.../`. Delta spec consolida em `openspec/specs/cross-profile-sharing/spec.md` (estado final contém 6 requirements).
   - Rollback: reverter o PR; sem migração de DB.

## Open Questions

- O toggle `Casa` deve aparecer em **todas** as tabs (Patrimônio, Rebalanceamento, etc.) ou só em `/patrimonio`? Hipótese: aparece em todas (decisão 2), mas confirmar com user na review do PR.
- Querystring ou path segment? Decisão 1 fechou como querystring (`?view=household`) — fica registrado pra caso o owner prefira revisar.
