# PRD: Omaha — Gestão de Investimentos Familiares

> Documento canônico de orientação. Fonte de verdade para identidade do
> produto, modelo de dados, regras de operação e horizonte de evolução.
> Detalhamento de cada capacidade vive em `openspec/specs/<area>/spec.md`.
> Estado de execução das próximas fatias vive em `openspec/roadmap.md`.
> Identidade de voz e anti-referências vivem em `PRODUCT.md`. Sistema
> visual (tokens, tipografia, espaçamento, elevação) vive em `DESIGN.md`.

**Última revisão:** 2026-07-03.

---

## 1. Identidade

### 1.1 Propósito

**Abrir o app, ver onde o portfólio está, confiar nos números, fechar a aba.**

Operacional. Prosa canônica (incluindo anti-referências e princípios de
design) vive em `PRODUCT.md`.

Omaha é um ledger privado de portfólio familiar, self-hosted. O sistema existe
para que a família enxergue a distribuição atual dos investimentos por classe,
o desvio em relação ao alvo e o ganho consolidado, sem terceirizar o número
para nenhuma corretora ou serviço externo.

### 1.2 Usuários

Tabela compacta para leitura rápida. Contexto humano completo em
`PRODUCT.md` §Users.

| Perfil       | Papel          | Uso                                                                             |
|--------------|----------------|---------------------------------------------------------------------------------|
| **Italo**    | Operador       | Importa CSV da corretora, edita classes e ativos, gerencia backup, mantém nginx/certificados. |
| **Ana Livia**| Visualizadora  | Acessa para conferir distribuição e ganho. Não muta estado.                     |

Os dois compartilham uma senha familiar única. Cada perfil tem dados isolados
em todas as rotas e todas as tabelas — `cross-profile-sharing` é um
comportamento do sistema, não um vazamento.

### 1.3 Contexto de uso

- Residência única, self-hosted, exposto via LAN.
- O cliente nunca é o próprio servidor. O servidor é a máquina de dev. Bind
  `--host 0.0.0.0` é não-negociável.
- Acesso a partir de laptops e celulares da rede doméstica via URL LAN
  descoberta por `bash scripts/print_lan_url.sh`. Endereço atual
  canônico: `http://192.168.1.6:8000` (histórico `192.168.1.7`).
- Sem multi-tenant, sem escala pública, sem marketing surface.
- Velocidade e correção importam. A página pode ser pequena.

### 1.4 Idioma e moeda

- **Idioma UI:** Português (PT-BR). Templates e copy em português;
  identificadores e código em inglês.
- **Moeda:** BRL (R$). Suporte a `currency_code` por ativo (`BRL`, `USD`)
  com `CHECK ck_asset_currency_code` no schema.
- **Formato numérico na entrada:** CSV de corretora usa decimal brasileiro
  (`1.234,56`). Banco e seeds usam decimal plano (`1234.56`).
  `_parse_brazilian_number` trata `.` como separador de milhar quando sozinho.

### 1.5 Não-objetivos

Explicitamente fora do escopo atual. Não construir, não propor:

- Modo escuro (registro de produto é off-white).
- Cor de destaque configurável.
- Multi-tenant, signup público, OAuth, MFA.
- Painel administrativo além dos dois perfis familiares.
- Sincronização com APIs de corretora em tempo real (apenas yfinance para
  cotação, com TTL e cache).
- Mobile app nativo (web responsiva basta).
- Integração bancária / open finance.

---

## 2. Capacidades

Cada capacidade abaixo tem spec canônico em `openspec/specs/<slug>/spec.md`.
Esta seção apenas lista e agrupa — nenhum comportamento é definido aqui.

### 2.1 Inventário por área

| Área             | Specs (link em `openspec/specs/`)                                                                                                                                                                                                                                                                                                                       |
|------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Auth & perfis**| `profile-landing`, `header-profile-switcher`, `cross-profile-sharing`                                                                                                                                                                                                                                                                                    |
| **Classes**      | `class-section-totals`, `asset-allocation-alerts`, `dashboard-inline-editing`                                                                                                                                                                                                                                                                            |
| **Ativos**       | `asset-class-quote-kind`, `asset-trade-flags`                                                                                                                                                                                                                                                                                                            |
| **Posições**     | `broker-csv-import-totals`, `broker-csv-number-parsing`, `import-modal`, `import-class-auto-suggest`, `import-class-color-via-css-class`, `import-modal-class-binding`, `import-position-totals`                                                                                                                                                                |
| **Dashboard**    | `dashboard-sidebar`                                                                                                                                                                                                                                                                                                                                      |
| **Cotações**     | `quote-provider` (yfinance `.SA`), `quote-cache` (TTL em tabela `quotes`), `quote-refresh` (loop `asyncio`)                                                                                                                                                                                                                                              |
| **Rebalance**    | `rebalance-data-bridges` (ORM → solver), `rebalance-engine` (CVXPY), `rebalance-route` (`POST /api/rebalance`), `rebalance-page` (`GET /rebalance`)                                                                                                                                                                                                       |
| **Tema visual**  | `color-tokens` (pares de tokens com contraste WCAG AA)                                                                                                                                                                                                                                                                                                    |
| **Dados**        | `data-driven-seed` (CSV triplet via `scripts/seed_from_csv.py`), `seeded-state` (`db-reset` popula Italo + Ana)                                                                                                                                                                                                                                          |
| **Qualidade**    | `route-test-alignment`, `test-suite-quality`, `unit-test-effectiveness`, `e2e-rework`, `e2e-fixture-isolation`, `bdd-workflow-reuse`, `dev-tasks`, `prek-hooks`                                                                                                                                                                                            |

Total: **34 specs**, todos estáveis (todos os `OpenSpec changes` foram
arquivados e sincronizados).

### 2.2 Modelo de dados

Entidades canônicas e relações de alto nível. Schema autoritativo em
`src/omaha/models.py` (SQLAlchemy 2.0 + Alembic):

```
User                 id, password_hash
 └─< Profile         id, user_id, name, display_order, active

Profile
 ├─< AssetClass     id, profile_id, name, target_pct, display_order, quote_kind ∈ {auto,manual,none}
 │   └─< Asset       id, class_id, name, target_pct, display_order,
 │                    buy_enabled, sell_enabled, currency_code ∈ {BRL,USD}
 │       └─< Position id, asset_id, broker_ticker, qty, avg_price, current_price,
 │                       total_invested, total_current
 └─> QuoteCache      asset_id FK→asset, price, currency, fetched_at  (TTL por quote_kind)
```

Invariantes em produção:

- `sum(target_pct)` dentro de uma classe = 100.
- `sum(target_pct)` entre classes de um perfil = 100.
- Posição não-negociável usa sentinela `qty=1, avg=total_investido,
  cur=total_atual` (ver `data/seed/README.md`).
- Totais do CSV de corretora entram **verbatim** no banco — sem recomputo.

### 2.3 Pipeline de dados

```
Corretora (CSV BR)                       Resolved server-side / LAN
    │                                              │
    ▼                                              ▼
scripts/seed_from_csv.py ──seed──▶ data/portfolio.db ──serve──▶ uvicorn 0.0.0.0:8000
    ▲                              (SQLite, alembic)              │
    │                                                             ├──▶ /dashboard  (perfil ativo)
    └──────── snapshot (scripts/snapshot_to_csv.py) ◀─────────────┤
                                                                  ├──▶ /rebalance  (CVXPY plan)
                                                                  ├──▶ /importar   (modal fluxo)
                                                                  └──▶ /api/import/preview + commit
```

Loop de cotação (`asyncio` background):

```
QuoteProvider.yfinance(.SA suffix)
    └─▶ QuoteCache (DB-backed, freshness TTL)
            └─▶ rebalance.MarketPriceLookup adapter
                    └─▶ CVXPY solver
```

---

## 3. Stack & Operação

### 3.1 Stack

| Camada        | Tecnologia                                              |
|---------------|---------------------------------------------------------|
| Backend       | FastAPI + SQLAlchemy 2 + Pydantic V2 + Alembic           |
| Banco dev     | SQLite (`data/portfolio.db`)                            |
| Banco prod    | Postgres (compose `prod.yml`)                           |
| Frontend      | Jinja2 + Alpine.js (sem build step) + CSS vanilla        |
| Fonte         | Inter (UI sans) + Source Serif 4 (display, dashboard)    |
| Testes        | pytest (unit/integration/bdd) + Playwright (e2e)         |
| Lint          | ruff + prek (`pre-commit` / `pre-push` / `commit-msg`)   |
| Runner        | taskipy (`uv run task <name>`)                          |
| Deploy        | Docker Compose + nginx + certbot                        |
| Package mgr   | `uv` (`uv sync`)                                         |

### 3.2 Subdomínios no código

| Caminho                      | Responsabilidade                                                                 |
|------------------------------|----------------------------------------------------------------------------------|
| `src/omaha/main.py`          | App factory; lifespan roda `alembic upgrade head` + `omaha.seed`                 |
| `src/omaha/routes/`          | `pages`, `auth`, `classes`, `assets`, `imports`, `quotes`, `rebalance`, `health` |
| `src/omaha/quotes/`          | cache DB-backed, provider abstraction + yfinance, loop `asyncio`                 |
| `src/omaha/rebalance/`       | solver CVXPY, data bridges (ORM → solver), glue, validação, post-processamento   |
| `src/omaha/audit/`           | parser CSS, resolvedor de cor, inventário, relatório de contraste                |
| `src/omaha/templates/`       | Jinja2 — `base`, `dashboard`, `_sidebar`, `rebalance`, `login`, etc.              |
| `src/omaha/static/app.css`   | Único bundle CSS (72K). Tokens em `:root`.                                       |
| `src/omaha/seed.py`          | Idempotente. Cria **apenas** usuários + perfis. Não toca ativos/posições.        |
| `scripts/seed_from_csv.py`   | Único caminho para criar `AssetClass` / `Asset` / `Position`. CSV triplet em `data/seed/`. |

### 3.3 Tarefas taskipy canônicas

Tabela operacional completa em `pyproject.toml`. Atalhos mais usados:

| Comando                      | Função                                                                     |
|------------------------------|----------------------------------------------------------------------------|
| `task serve`                  | `uvicorn --host 0.0.0.0 --port 8000 --reload`                              |
| `task test`                   | suite completa (unit + integration + e2e + bdd)                            |
| `task test-unit`              | só rápidos (`pytest -m unit`)                                              |
| `task test-integration`       | DB + TestClient + audit                                                    |
| `task test-e2e`               | Playwright (sem marker; coletado por path)                                 |
| `task test-bdd`               | pytest-bdd (`tests/bdd/`)                                                  |
| `task check`                  | `lint && test-unit` — CI gate                                              |
| `task db-migrate`             | `alembic upgrade head`                                                     |
| `task db-reset`               | wipe + reseed **ambos** perfis (Italo + Ana), populados para delivery      |
| `task db-clear-assets`        | apaga **apenas** ativos (mantém classes) — usar quando o usuário pede import-from-scratch |
| `task db-seed`                | seed idempotente de family + profiles (sem assets)                         |
| `task db-seed-from-csv`       | aplica o CSV triplet (`reset` destrutivo)                                   |
| `task db-snapshot`            | DB → CSV (ver `scripts/snapshot_to_csv.py`)                                |
| `task backup`                 | snapshot SQLite para `./backups/`                                          |
| `task lint`                   | `prek run --all-files`                                                     |
| `task format`                 | `ruff format .`                                                            |
| `task secret-key`             | gera `SECRET_KEY` aleatório                                                |

**Regra:** sempre `task <name>`. Nunca digitar o comando cru.
A razão vive na §4.8.

### 3.4 Backup & restore

| Modo       | Comando                    | O que faz                                                              |
|------------|----------------------------|------------------------------------------------------------------------|
| Snapshot   | `task backup`              | `sqlite3.Connection.backup` para `./backups/<timestamp>.db` (sem lock) |
| Cold       | `bash scripts/snapshot…`   | dump literal                                                          |
| Restore    | `task db-reset`            | wipe + reseed CSV                                                     |
| Round-trip | `task db-snapshot`         | DB → CSV (lossless para ativos/posições/totais)                        |
| Compose    | `task prod-down`           | **preserva** o volume `omaha-data`. Use `-- -v` para wipe.             |

### 3.5 Configuração (`.env`)

| Variável                      | Default / locked                | Notas                                                                  |
|-------------------------------|---------------------------------|------------------------------------------------------------------------|
| `ADMIN_PASSWORD`              | **`distendidos`** (locked)      | Senha familiar compartilhada. Não rotacionar sem aprovação do owner.    |
| `TEST_ADMIN_PASSWORD`          | distinta em fixtures             | Constant usada em `tests/conftest.py`, `tests/e2e/conftest.py`, `tests/bdd/conftest.py`. |
| `SECRET_KEY`                  | `task secret-key`               | Aleatório. Sem default em produção.                                    |
| `DATABASE_URL`                | `data/portfolio.db`             | Postgres em `prod.yml`.                                                |
| `LAN_BIND`                    | `0.0.0.0`                       | hard-coded no `task serve`. Não substituir por `127.0.0.1`.            |
| `OMAHA_BR_NUMBER_FORMAT`      | `1.234,56`                      | Decimal brasileiro para o parser CSV.                                  |

---

## 4. Regras de Ouro (operational invariants)

Estas regras são vinculantes. Toda sessão de agente lê §4 antes de propor
mudar qualquer coisa abaixo. São as invariantes que definem como o sistema
é construído — não são sugestões.

### 4.1 Senha da família — locked

`ADMIN_PASSWORD` é a senha compartilhada por Italo e Ana Livia e gating de
login em ambos os perfis. Valor canônico: **`distendidos`**. Não rotacionar.

Aplica-se a:

- `.env` e `.env.example` — manter `ADMIN_PASSWORD=distendidos`.
- `README.md` Quick start e qualquer onboarding doc.
- Schema de `.env` Quick start — não oferecer passo "set your own password".
- Fixtures de teste — usar `TEST_ADMIN_PASSWORD` separado, já cabeado em
  `tests/conftest.py`, `tests/e2e/conftest.py`, `tests/bdd/conftest.py`,
  nunca reutilizar o valor familiar.

Rotação exige editar esta seção + `.env.example` + `README.md` + `.env` em
um único commit e avisar o owner antes do merge.

### 4.2 Acesso de rede — bind `0.0.0.0` obrigatório

O app de dev é **sempre** acessado de outra máquina na LAN. O dev host é
servidor, não cliente. Default do `uvicorn` (`127.0.0.1`) está **errado** —
torna o app inalcançável para o cliente.

Regras:

1. **Bind `--host 0.0.0.0` sempre.** Nunca `127.0.0.1`, nunca `localhost`.
   Comando de dev canônico:
   `uv run uvicorn omaha.main:app --host 0.0.0.0 --port 8000`
   (ou `task serve`).
2. **Reportar o IP da LAN, nunca `localhost`.** URL canônica atual:
   `http://192.168.1.6:8000`. Descobrir com
   `bash scripts/print_lan_url.sh`. Se o IP mudar, re-detectar com
   `ip -4 addr | grep inet` e usar o da LAN/Tailscale. Nunca escrever
   `http://localhost:8000` ou `http://127.0.0.1:8000` em chat, doc ou
   instrução para humano.
3. **README §Network access é a fonte de verdade** para bind + endereço.
   Ler antes de qualquer instrução "start the app".

### 4.3 Seed via CSV — único caminho de criação de ativos/posições

A criação automatizada/agent-driven de linhas em **`AssetClass`**, **`Asset`**
e **`Position`** é permitida **apenas** via o caminho CSV em `data/seed/`,
consumido por `scripts/seed_from_csv.py` (taskipy: `db-seed-from-csv` /
`db-seed-diff` / `db-seed-upsert` / `db-reset`). Seed literal/hardcoded,
scripts ad-hoc, demo wiring e mudanças em `openspec/changes/` que burlem o
caminho CSV são proibidos.

`src/omaha/seed.py` cria **apenas** usuários + perfis. Está correto como
está. Não estender para seed de ativos/posições.

Por quê: ativos e posições refletem holdings reais. Seed hardcoded polui a
visão do usuário e quebra os invariantes de "soma 100". O caminho CSV é a
fronteira controlada: edições vão por um único arquivo, validável,
diff-able. Seed inline burla validação e quebra o invariante da corretora
ser fonte de verdade.

Quando aplicar:

- Editar `src/omaha/seed.py` — manter user+profile only.
- Adicionar/modificar ativos ou posições em código — usar o caminho CSV.
  Nova coluna em `Asset`/`Position` exige `OpenSpec change`.
- Smoke scripts que criem ativos/posições — proibidos (a não ser via
  `seed_from_csv.py`).
- Carregar fixtures em testes é ok (escopo próprio).

**Default test-readiness state**: ambos perfis populados (Italo: 6 classes
+ 48 ativos + 47 posições; Ana: 6 classes + ~40 ativos + ~43 posições).
Produzido por `task db-reset`. Se o usuário pedir explicitamente uma
superfície sem ativos para testar o fluxo de import do zero, usar
`task db-clear-assets` em vez de `db-reset`.

### 4.4 Alpine `<select>` + dynamic `<template x-for>` — binding gotcha

Para um `<select>` cujas opções são renderizadas por um `<template x-for>`
interno, o two-way bind **DEVE** ser:

```html
<select x-init="$nextTick(() => { const a = <bound-expr>; if (a) $el.value = a.<id-field> ?? ''; })"
        x-effect="(() => { const a = <bound-expr>; if (a) $el.value = a.<id-field> ?? ''; })()"
        @change="<bound-expr>.<id-field> = $event.target.value">
  <option value="">Selecione...</option>
  <template x-for="ac in <options-array>" :key="ac.id">
    <option :value="ac.id" x-text="ac.name"></option>
  </template>
</select>
```

Por quê:

- `x-model` em `<select>` não re-sincroniza `select.value` quando as opções
  mudam. Re-sincroniza só quando a expressão ligada muda. Quando o
  `<template x-for>` adiciona a `<option>` correspondente **depois** que o
  `x-model` já rodou, o select fica no placeholder (`value=""`).
- `x-effect` sozinho é insuficiente no render inicial: não há mudança
  reativa entre o mount do `<select>` e a render do template interno.
  Dispara uma vez, antes das opções existirem, e nunca mais porque o valor
  não mudou.
- `$nextTick` em `x-init` adia a atribuição `select.value = X` para o
  próximo microtask, que roda **depois** do Alpine processar o
  `<template x-for>`. A essa altura a `<option>` existe, e a atribuição
  cola.
- `x-effect` cobre o caso em que o valor ligado muda depois (ex.: override
  do usuário via `@change` dispara re-render).
- `@change` mantém a source-of-truth property em sync depois do pick manual.

Referência viva: `src/omaha/templates/dashboard.html:510` (auto-matched)
e `:553` (unmatched). PR aberta anterior usou `x-model` e falhou; ver
spec `import-modal-class-binding`.

### 4.5 Import preview response ↔ Alpine template sync

`_build_preview_response` em `src/omaha/routes/imports.py` monta os
dicionários `auto_matched` e `unmatched` consumidos pelo Alpine store
`$store.importModal` em `dashboard.html`. **Qualquer campo acrescentado
nesses dicionários precisa estar no JSON** que `/api/import/preview`
retorna (campos `invested`, `current_value`, etc.).

Template renderiza via `row.current_value` / `row.invested` no laço
`<template x-for="(row, i) in $store.importModal.autoMatched">`. Se o
servidor não emitir o campo, `row.current_value` vira `undefined` →
`Number(undefined)` = `NaN` → `formatBRL` mostra `R$ 0,00`.

Disparadores:

- Nova coluna em `Position` → atualizar `_raw_to_dict` + `_dict_to_raw` +
  UPSERT SQL + `_build_preview_response`.
- Novo campo exibido no modal de revisão → incluir nos dicionários
  `auto_matched`/`unmatched` em `_build_preview_response`.
- Mudança no template que lê `row.X` → garantir que
  `_build_preview_response` emite `X` no JSON.

Referência: `src/omaha/routes/imports.py:_build_preview_response`,
`tests/` (`test_import_*`), `src/omaha/templates/dashboard.html`.

### 4.6 Test marker — allowlist explícito, não pattern matching

`tests/conftest.py::pytest_collection_modifyitems` particiona a suite via
duas listas:

- **`_INTEGRATION_PREFIXES`** — prefixos de path para arquivos que batem
  em DB, TestClient ou pipeline de audit. ~40 prefixos hoje (S02/S03/S04 +
  famílias T0*).
- **`_UNIT_FILES`** — basenames de arquivos para o conjunto pequeno de
  testes puros (audit, parsers, validators, dockerfile, logging).
- `tests/e2e/*.py` — sem marker, rodam em `task test-e2e`.
- `tests/audit_integration/*.py` — `@pytest.mark.integration`.
- `tests/bdd/` — cenários pytest-bdd a partir dos `.feature`. Marker `bdd`.
  Roda serial (sem xdist — race no autouse `clean_seeded_profiles` que
  compartilha SQLite session-scoped).
- `pytestmark` module-level vence a regra de path.

Qualquer `tests/test_*.py` que bate em DB/TestClient mas **não** está em
`_INTEGRATION_PREFIXES` emite warning `UnknownTestPath`. O warning é o
sinal de drift futuro: se você adicionar `tests/test_t07_*.py` que bate
em DB, **deve** adicionar o prefixo a `_INTEGRATION_PREFIXES` — caso
contrário o arquivo vira silenciosamente `unit` e polui o subset.

Quando aplicar:

- Novo `tests/test_*.py` que bate em DB / TestClient → adicionar prefixo
  em `_INTEGRATION_PREFIXES` em `tests/conftest.py`.
- Novo teste puro sob `tests/` → adicionar basename em `_UNIT_FILES`.
- PR review de novo arquivo de teste → verificar marker assignment.

### 4.7 BDD workflows — extração por tendência

Workflows BDD vivem em `tests/bdd/step_defs/_workflows.py`. Regra de
extração: **≥2 cenários com tendência de crescimento**. Carve-out
per-workflow documentado em
`openspec/changes/bdd-workflow-reuse-helpers/design.md` Decisão 2 —
`login.feature` e `profile_isolation.feature` ficam intactos para o wrapper
de login.

Contrato enforçado por `tests/bdd/test_workflow_contracts.py` (ceiling de
10 workflows, wrappers delegam, carve-out). Spec operacional em
`tests/bdd/README.md`. BDD roda serial — não adicionar `pytest-xdist`.

### 4.8 Taskipy — `task <name>` em vez de raw commands

Tarefas vivem em `pyproject.toml` sob `[tool.taskipy.tasks]`. `use_vars =
true` significa que `{app_target}` e amigos são expandidos — chaves
literais em comandos devem ser escritas como `{{}}`.

**Regra:** preferir `task <name>` (ou `uv run task <name>` com venv
ativada) sobre digitar o comando cru. Razões:

- `task serve` sempre faz bind correto (`0.0.0.0`). Sem ele, é fácil
  esquecer `--host` e cair no `127.0.0.1` silencioso (ver §4.2).
- Novas tarefas são adicionadas em `pyproject.toml` e ficam disponíveis
  imediatamente. Comandos raw queimam ciclos re-derivando flags.

Quando aplicar: start/stop do dev server, qualquer teste, lint, format,
coverage, qualquer operação de DB, Docker/prod, first-time setup
(`install`, `install-e2e`, `prek-install`).

Gotchas:

- `task serve` bloqueia foreground — para trabalho paralelo, background
  com `nohup ... &` ou `serve-prod` em terminal destacado.
- `docker compose -f prod.yml down` **preserva** o volume nomeado
  `omaha-data`. Apenas `down -v` apaga DB.
- `db-clear-assets` é wipe de ativos. **`db-reset` é o reseed completo** —
  roda `scripts/reset_both_profiles.py` para Italo + Ana em uma
  invocação.

### 4.9 Delivery finalization — use `refresh-for-test` skill

Rode a checklist inteira antes de reportar **qualquer** mudança
browser-visível como done — incluindo patches de follow-up e layout fix,
não apenas a entrega inicial. **Use a skill `refresh-for-test`** — ela
dona da receita (restart uvicorn → smoke `/healthz` → pick DB task →
verify row counts → visual dashboard check → report LAN URL + DB state)
e usa as tarefas taskipy (`db-migrate` / `db-reset` / `db-clear-assets` /
`db-seed`) pela tabela abaixo.

**Regra:** a receita roda inteira após cada mudança browser-visível. Um
patch de follow-up que "só arruma CSS" ainda precisa de:

1. `task db-reset` (DB pode ter sido wipado durante teste empty-state — e
   geralmente foi).
2. Restart uvicorn (Jinja pode servir bytes stale sem reload; CSS
   definitivamente precisa de request fresca).
3. Smoke `curl $URL/healthz`.
4. Verificar que a página renderizada contém nomes de classe seeded
   (`curl -b cookie "$URL/" | grep -c "RF Din"`).
5. Reportar LAN URL + DB row counts na mensagem final.

**Skip de qualquer passo = delivery failure.** O usuário abre a URL, vê
dashboard vazio (porque o DB foi wipado durante o próprio teste do
agente), e conclui que a feature está quebrada. Se a receita parece
redundante, rode-a mesmo assim.

**Rule of thumb:** default para delivery = **populado** (`db-reset` →
Italo: 6 classes + 48 ativos + 47 posições) a menos que o usuário tenha
pedido explicitamente uma superfície sem ativos.

| Tipo de mudança                             | Tarefa                           |
|---------------------------------------------|----------------------------------|
| Migração / model edit                       | `task db-migrate`                |
| Default — populado, pronto para teste       | `task db-reset`                  |
| Usuário pediu explicitamente import do zero | `task db-clear-assets`           |
| Só mudou camada de seed / config            | `task db-seed`                   |

### 4.10 Register de produto — domestic, sem ornamento

Regras vinculantes, destiladas de `PRODUCT.md` §Brand Personality +
§Anti-references (que é a fonte canônica de voz). Mudanças precisam de
aprovação do owner.

- **Domestic, personal, lived-in.** Não premium (sem oxblood, sem dourado).
  Não playful (sem ilustrações, sem mascot). Mais perto de um Moleskine
  bem usado do que de fintech app.
- Voz: terceira pessoa, matter-of-fact, PT-BR. Sem exclamação. Sem
  "Welcome back!". Sem marketing copy em lugar nenhum.
- Dashboard é vista doméstica, não portfolio dashboard. Quando Ana Livia
  não tem posições, o empty state diz quietamente que a conta existe e
  nada está nela.
- Cor de body é off-white verdadeiro, não creme/sand/bege. Calor vive no
  accent (verde-feto dessaturado, hue 150), nunca no tint do fundo.
- Sem ícones. Sem gradient text. Sem side-stripe alerts. Sem eyebrow acima
  de todo heading. Cards são flat ou shadowed, nunca ambos.

---

## 5. Trabalho em Curso e Horizonte

### 5.1 Estado atual (snapshot)

- **Zero `OpenSpec changes` ativos.** Os 21+ já-arquivados em
  `openspec/changes/archive/` cobriram: paleta visual, import modal
  revertido + binding corrigido, rebalance infra (CVXPY + rota + página),
  dashboard consolidado, profile switcher, BDD workflow reuse, CSV seed
  driven, e mais.
- **34 specs em `openspec/specs/`, todos estáveis** (todos os changes
  foram arquivados e sincronizados via `opsx-sync-specs`).
- **`test-suite`:** 4 subsets (`unit`, `integration`, `bdd`, `e2e`) com
  gates independentes em `pyproject.toml`.
- **Trajetória recente (último mês):** dominada por rebalance infra
  (solver CVXPY abandonando o stub, rota, página, glue, data bridges).
  Antes disso: dashboard consolidado, BDD workflow reuse, CSV seed
  driven, profile switcher.

Sistema em modo **estabilizar**. Próximo passo é escolhido pelo roadmap
(§5.4) ou por demanda direta do owner — não há backlog obrigatório.

### 5.2 Onda recente (já arquivada, contexto)

Agrupada por tema, não exaustiva. Ver `openspec/changes/archive/` para
proposal/design/tasks completos.

| Tema                       | Changes representativos                                                                                                         |
|----------------------------|---------------------------------------------------------------------------------------------------------------------------------|
| **Rebalance infra**        | `2026-06-26-rebalance-infra`, `…-rebalance-route`, `…-rebalance-page`, `…-rebalance-data-bridges`                                |
| **CSV seed**               | `…-csv-driven-asset-seed`, `…-add-db-snapshot`                                                                                  |
| **Dashboard**              | `…-dashboard-width-and-inline-edit`, `…-dashboard-inline-edit-friction`, `…-consolidated-totals`, `…-header-profile-switcher` |
| **Auth & landing**         | `…-direct-landing-with-header-profile-switcher`, `…-auth-card-styling`                                                          |
| **Import modal**           | `…-restore-import-modal`, `…-modify-import-positions-modal`, `…-fix-asset-table-ui-bugs`                                       |
| **Bugfix / correção**      | `…-fix-br-number-parser`, `…-fix-bdd-workflow-reuse-gaps`, `…-fix-route-test-failures`, `…-fix-e2e-tests`                       |
| **Tema visual**            | `…-execute-phase-02-palette`, `…-investigate-import-class-color`                                                                |
| **Qualidade**              | `…-review-unit-tests-effectiveness`, `…-add-dev-tasks`                                                                          |
| **Plumbing do OpenSpec**   | `…-verify-m002-fix-s06-real-browser`, `…-split-prek-push-bdd-from-blocking-gate`                                                |

### 5.3 Horizonte — candidate next slices

Sem compromisso. Cada item é semente para uma fatia em
`openspec/roadmap.md` quando for escolhida. Prefixo (`F`/`R`/`T`/`D`/`I`)
indica o kind sugerido:

- **F — multi-broker CSV adapter.** Suportar outra corretora além da já
  parseada (provavelmente BTG/Modal) com `quote_kind=manual` e mapeamento
  explícito no `seed_from_csv.py`.
- **F — consolidação cross-profile.** Vista household agregada (soma dos
  dois perfis) sem quebrar isolamento per-profile. Spec base já vive em
  `cross-profile-sharing`.
- **F — histórico de movimentações.** Ledger de eventos (compra, venda,
  aporte, rendimento) por ativo. Sem spec ainda.
- **F — snapshot visual do dashboard.** Exportar dashboard para
  imagem/PDF shareable. Doméstico, sem ornamento.
- **F — dashboard mobile layout refinement.** Tabelas de ativos
  responsivas para celular (hoje o layout é desktop-first).
- **F — dark mode.** Explicitamente fora de escopo em §1.5. Listado
  apenas porque aparece em `REQUIREMENTS.md` legacy; descartar.
- **F — rebalance "what-if" incremental.** Validar cenários before/after
  sem mover dinheiro. Base: `rebalance-engine` + `rebalance-page`.
- **R — extrair `quote_provider` adapter para pacote.** Se
  `yfinance` for trocado, hoje há só um impl. Daria para injetar mais
  providers.
- **R — split `templates/dashboard.html` em partials.** Hoje é monolith
  de ~1600 linhas. Partials já existe (`_sidebar.html`,
  `_rebalance_*`); estender.
- **T — BDD e2e suite a 100% green.** Spec `e2e-rework` está estável mas
  ainda com selectors pendentes; o `bdd-workflow-reuse-helpers`
  documenta o caminho.
- **T — coverage report no CI.** `task coverage` existe; falta cabo no
  pipeline.
- **T — mutation testing do rebalance engine.** Solver é crítico.
- **I — agendamento automático de backup.** `task backup` existe; nenhum
  cron/certbot.timer está cabeado para ele.
- **I — TLS cert renewal automation.** Certbot está configurado em
  `nginx/` mas renovação é manual.
- **D — refresh do README para refletir surface atual.** Em particular,
  a seção "Network access" e o bloco de features.

### 5.4 Ponteiro para o roadmap

Próxima camada de planejamento: **`openspec/roadmap.md`**. Esta PRD é a
documentação canônica de **o que** o sistema é e **como** ele opera. O
roadmap documenta **qual fatia** entra em execução agora e seu ciclo de
vida (`Ready → Spec Proposed → Applying → Applied → Archived` + `Blocked`).

Quando o owner decidir atacar qualquer item de §5.3, o fluxo é:

1. Owner descreve o feature intent.
2. Agente cria **uma** fatia em `openspec/roadmap.md` com id, prefix e
   título, e status `Ready`.
3. Agente delega `openspec-propose` passando o `Candidate OpenSpec change id`
   exato do roadmap → cria `openspec/changes/<change-id>/`.
4. Avança para `Applying`, depois `Applied`, depois `Archived`. Status é
   atualizado no roadmap a cada gate.
5. Verificação spec roda após cada gate (`openspec/config.yaml`
   `openspec_roadmap`).

---

## 6. Workflow de Mudanças (resumo operacional)

### 6.1 Status model

```
Ready ─▶ Spec Proposed ─▶ Applying ─▶ Applied ─▶ Archived
                                              │
                                              └─▶ Blocked (em qualquer ponto, com motivo)
```

| Transição        | Quem move                         | O que atualiza                                            |
|------------------|-----------------------------------|-----------------------------------------------------------|
| Pick slice       | humano ou agente                   | nada                                                      |
| Change criado    | `openspec-propose`                | status `Spec Proposed`, `Spec link` apontando ao change  |
| Aplicação início | `openspec-apply-change`           | status `Applying`                                         |
| Validado         | durante apply                     | status `Applied`, comandos de validação listados          |
| Arquivado        | `openspec-archive-change`         | status `Archived`, path archive + data                    |
| Bloco            | manual                            | status `Blocked`, questão aberta                          |

### 6.2 Prefixos de fatia

| Prefixo | Uso                                                                  |
|---------|----------------------------------------------------------------------|
| `F`     | Feature visível ao usuário ou alteração de comportamento de API      |
| `R`     | Refactor estrutural sem mudança de comportamento                     |
| `T`     | Testes, cobertura, harness de confiabilidade                         |
| `D`     | Documentação, runbook, suporte de spec                                |
| `I`     | CI, build, tooling, ambiente                                         |
| Blocked | `Blocked` como status, não prefixo                                   |

Numerar sequencialmente dentro do prefixo (`F01`, `R02`, …).

Mudar título de uma fatia antes de executar exige renomear o
`Candidate OpenSpec change id` para o novo slug kebab — manter alinhado
1:1 entre heading, change folder e archive path.

### 6.3 Paralelismo

- **Múltiplas fatias em `Spec Proposed`:** permitido.
- **Global cap:** no máximo **2** fatias em `Applying` simultaneamente.
- **Critical-area cap:** no máximo **1** fatia em `Applying` em domínios
  críticos (autenticação, importação, rebalance solver, backup).
- **Atomicidade de `next`:** cada execução move uma única transição de
  uma única fatia.

### 6.4 Spec verification gate (mandatório)

Entre `propose`/`apply`/`archive`, rodar o comando de verificação de spec
do repo e corrigir issues antes de continuar:

- após `openspec-propose` → verificar antes de `openspec-apply-change`
- após `openspec-apply-change` → verificar antes de `openspec-archive-change`
- após `openspec-archive-change` → verificar antes de escolher próxima fatia

Falha na verificação → parar, resolver, re-rodar, continuar.

### 6.5 Skills de OpenSpec CLI

| Skill                       | Quando                                                            |
|-----------------------------|-------------------------------------------------------------------|
| `openspec-roadmap`          | bootstrap/atualizar `openspec/roadmap.md`                        |
| `openspec-propose`          | fatia `Ready` → cria change em `openspec/changes/<id>/`          |
| `openspec-apply-change`     | implementar change aprovado                                       |
| `openspec-archive-change`   | ao concluir                                                       |
| `openspec-verify-change`    | validar implementação vs artefatos antes de arquivar             |
| `openspec-sync-specs`       | sincronizar delta spec → main spec (sem arquivar)                |

`openspec-roadmap` **orquestra** as outras. Não as substitui.

---

## 7. Glossário (domínio)

| Termo                | Significado                                                                                          |
|----------------------|------------------------------------------------------------------------------------------------------|
| **Perfil**           | Container de dados financeiros por pessoa (`italo`, `ana`). Isolado por usuário logado.               |
| **Classe**           | Categoria macro do ativo (`RF Dinâmica`, `Ações`, `FII`, `Cripto`, …). Tem `target_pct` no perfil.    |
| **Ativo**            | Item individual dentro de uma classe. Tem `target_pct` dentro da classe.                              |
| **Posição**          | Quantidade + preço de um ativo em uma corretora específica. Totais entram verbatim.                   |
| **Alvo**             | Percentual alvo da classe dentro do portfólio. Soma 100 entre classes do mesmo perfil.                |
| **Cotação**          | Preço de mercado do ativo. Cache DB-backed com TTL; provider `yfinance` com suffix `.SA`.            |
| **Quote kind**       | `auto` (refresh), `manual` (edita o número), `none` (cache estático).                                 |
| **Rebalance**        | Cálculo CVXPY que produz plano de compra/venda para zerar o desvio das classes em relação ao alvo.    |
| **Seed**             | Carga inicial de dados. `seed.py` cobre user+profile; `seed_from_csv.py` cobre classes+ativos+posições. |
| **Snapshot**         | DB → CSV (lossless). Espelha o round-trip do parser de corretora.                                     |
| **Backup**           | Cópia física do SQLite via `sqlite3.Connection.backup` para `./backups/`.                              |
| **Slice**            | Uma unidade de trabalho no roadmap. 1:1 com um `OpenSpec change`.                                     |
| **Spec**             | Documento canônico de uma capacidade em `openspec/specs/<slug>/spec.md`.                              |
| **OpenSpec change**  | Conjunto de artefatos (`proposal.md`, `design.md`, `tasks.md`, delta spec) em `openspec/changes/<id>/`.|
| **Worktree**         | Pasta de trabalho git isolada. Usada em sandbox para mudanças grandes.                                |
