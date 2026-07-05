## Why

Hoje o `header-profile-switcher` + a spec `cross-profile-sharing` provêm "qualquer operador pode ver qualquer perfil" e "qualquer operador pode mutar o portfólio do perfil ativo". Falta o terceiro nível: enxergar a **casa** (Italo + Ana Livia somados) sem perder o isolamento per-profile.

Hoje, para responder "quanto a família tem investido?", o operador precisa abrir o chip, alternar para o outro perfil, ler o card `patrimonio-portfolio-header`, somar mentalmente, e repetir a cada classe/atributo que quiser comparar. Operação manual, fácil de errar, e que escala mal quando os perfis passam de 2. PRD §1.2 ratifica que os dois perfis compartilham "privilégios equivalentes" — a granularidade "casa" é uma derivada, não um vazamento (`cross-profile-sharing` é comportamento, não vazamento).

Subir a granularidade "household" como modo de leitura do `/patrimonio` destrava a pergunta "como a família está alocada?" sem mexer em isolamento de dados.

## What Changes

- **Modo de leitura household** no `/patrimonio`: querystring `?view=household` (ou rota dedicada `/patrimonio/casa`, decidir no `design.md`) troca o contexto do template do perfil-ativo para a soma dos dois perfis familiares.
- **Card `patrimonio-portfolio-header` aceita modo household** sem alterar contrato de per-profile: as três métricas (`Investido`, `Valor atual`, `Ganho`) refletem a soma das posições de todos os perfis do `viewer`. Cobertura do delta: nova req na spec `cross-profile-sharing`; sem nova spec.
- **Toggle no header** (`templates/base.html`): chip de perfil mantém o `<select>` existente; adiciona-se um link/checkbox `Casa` ao lado que liga/desliga o modo household. Toggle vive **dentro** do bloco `{% if viewer and owner %}` ao lado do profile picker, à direita dele, antes do botão `Sair`.
- **Read-only**: o modo household é **somente leitura**. Botões `+ Classe`, `+ Ativo`, `Importar CSV`, edição inline de classes, e o toggle `Rebalancear` ficam desabilitados (ou ocultos) quando `view=household`. A rebalance opera por perfil (escopo do slice `rebalance-engine`).
- **Footer/chip de status**: enquanto household estiver ativo, o header mostra um chip `Casa` discreto (mesmo registro visual dos chips existentes em `DESIGN.md`) perto do profile picker; click no chip volta para `view=profile`.
- **`src/omaha/routes/pages.py`**: novo handler (e/ou extensão do `_render_patrimonio`) que carrega `AssetClass` + `Asset` + `Position` para **todos** os perfis familiares (`User.profiles` em vez de só `active_profile`); calcula agregados via nova função `household_aggregates(...)` espelhada de `portfolio_aggregates(...)`. Reuso da mesma forma de soma (Decimal, sem `qty * price` por linha — `broker-csv-import-totals` invariante).
- **Sem migração de DB**. Sem mudança em `scripts/seed_from_csv.py` ou `data/seed/`. Sem alteração em CSV triplet.
- **`PRD §5.3`** registra a entrada como entregue (atualmente lista F como "consolidação cross-profile").

**Não-Breaking**: `cross-profile-sharing` continua determinando quem-pode-ver-quem; o modo household é leitura adicional. `/patrimonio` (per-profile) é o default e mantém o comportamento existente byte-a-byte.

## Capabilities

### Modified Capabilities

- `cross-profile-sharing`: nova requirement sobre o modo household (read-only, agregado cross-profile). Cobre toggle UI, renderização do card no modo household, e desabilitação de mutações quando `view=household`. Sem mexer em isolamento per-profile — o agregado é só de leitura e nunca atravessa fronteiras `User`.

### Unchanged Capabilities (citado para contexto)

- `header-profile-switcher`: o chip existente continua funcionando como está; F01 só adiciona o toggle ao lado, sem alterar contrato nem testids.
- `patrimonio-portfolio-header`: contrato atual é "três métricas para o perfil ativo". F01 adiciona um cenário ao `cross-profile-sharing` que diz "quando `view=household`, as três métricas refletem a soma dos perfis do viewer". Sem delta aqui — a spec do card não muda.
- `dashboard-inline-editing`, `class-section-totals`, `asset-allocation-alerts`: nada.
- `rebalance-page`, `rebalance-route`, `rebalance-engine`: não tocam o toggle household — rebalance é per-profile, sempre.

## Impact

- **Rotas**: `src/omaha/routes/pages.py` ganha um branch ou rota para o modo household. `_render_patrimonio` ou ganha um parâmetro `view: str = "profile"`, ou `/patrimonio/casa` vira rota independente que reusa o mesmo template + helper. Decisão no `design.md`.
- **Templates**: `templates/base.html` ganha o toggle `Casa` ao lado do profile picker; `templates/patrimonio.html` ganha um branch `{% if view == 'household' %}` que troca contexto e desabilita ações (mesma estrutura de classe de CSS, classe nova `.is-read-only` se necessário).
- **Funções novas**: `household_aggregates(...)` em `src/omaha/routes/pages.py`, espelho de `portfolio_aggregates(...)` mas recebe `list[AssetClass]` de **todos** os perfis do viewer (não só o ativo). Mesma assinatura de retorno (`{"portfolio": ..., "classes": ...}`); sem nova tabela.
- **CSS**: poucas regras novas em `src/omaha/static/app.css` — `.household-toggle`, `.app-header__household-chip`, `.is-read-only[data-read-only]`. Sem tocar em tokens.
- **Tests**: novos cenários em `tests/integration/test_pages_patrimonio.py` (ou arquivo equivalente) cobrindo `?view=household`: card renderiza soma dos dois perfis, botões de mutação disabled, BDD step em `tests/bdd/features/profile_sharing.feature` ganha cenário "Ana visualiza a casa como agregado".
- **Sem deps externas**. Stack continua: FastAPI + Jinja2 + Alpine.js.
