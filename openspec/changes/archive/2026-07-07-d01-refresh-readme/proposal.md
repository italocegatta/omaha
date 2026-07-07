## Why

`README.md` ficou defasado após a onda F01-F07 + R-slice + T-slice recente. Defasagens concretas:

- "Live quotes, BRL/USD conversion, and rebalancing are deferred to milestone M002" — rebalancing já é shipped (rebalance CVXPY estável desde 2026-06-29); quotes já fluem via yfinance.
- "Click **Importar CSV** in the sidebar" — side panel foi REMOVIDA em F02; botões migraram para o topo do body de `/patrimonio`.
- Lista de templates inclui `dashboard.html` (renomeado para `patrimonio.html` em F02) e `_sidebar.html` (deletado em F02).
- "Project specs" aponta para `.gsd/` — estrutura antiga; o source-of-truth atual é `openspec/` (PRD.md, roadmap.md, specs/, changes/).
- Falta menção a Família sentinel como peer no profile-switcher (F07).
- Falta menção ao dark mode (F05).
- Falta menção ao tab nav de 4 itens (F02).
- Rotas mencionadas como `/dashboard` (legacy) — atuais são `/patrimonio`, `/rebalanceamento`, `/rentabilidade`, `/proventos`.
- "DB reset" mostra "Italo RF2" como fixture — foi removido em F07; baseline atual é Italo=6/48/47, Ana=6/52/52 + Família sentinel.
- `task db-snapshot` ainda descrito em flow de dev (R02 transformou `scripts/seed_from_csv.py` em package; atualizar a referência).

I01 + I02 vão adicionar novas seções ("Operação / Backup scheduler" e "Operação / TLS renewal") que supersedem o host-cron block e o step manual de certbot; D01 foca no resto da desatualização.

## What Changes

- Reescrever a intro (`# Omaha` + descrição + Quick Start) para refletir o estado pós-F-slice.
- Atualizar a tabela de tasks (`Development tasks`) com `test-bdd`, `test-integration`, `mutation` (T03) e qualquer task nova que tenha landado.
- Reescrever `Production deploy`: step manual de certbot substituído por referência a I02 (scheduled renewal).
- Reescrever `Backup & restore`: bloco de host-cron removido (I01 supersede).
- Reescrever `Testing the app`: dashboard URL é `/patrimonio`, não `/`; sem sidebar; botões no topo; Família é peer no profile-switcher; baseline counts atualizados.
- Reescrever `Project layout`: tree reflete partials + Família sentinel + I01/I02 services.
- Reescrever `Project specs`: aponta para `openspec/` (PRD, roadmap, specs/, changes/), não `.gsd/`.

## Capabilities

### New Capabilities

Nenhuma. D01 é doc-only — não cria nova capability.

### Modified Capabilities

Nenhuma. Specs existentes não mudam; só a doc externa.

## Impact

- `README.md` (reescrita de múltiplas seções; +200/-100 linhas estimadas).
- Sem mudança em `src/omaha/**`, `tests/**`, `openspec/specs/**`, scripts.
- AGENTS.md referencia o README em alguns pontos (Network access); não precisa mudar.
