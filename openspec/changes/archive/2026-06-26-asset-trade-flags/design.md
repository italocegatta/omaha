## Context

A foundation column do plano de rebalance (Fase 1, Gap A do
`.planning/REBALANCE_PLAN.md`). Solver CVXPY do projeto
`investing` exige `buy_enabled[i]` / `sell_enabled[i]` como
hard locks e `currency_code` para resolução de cotação. Sem
eles, o builder de `PortfolioSetup` (Gap E, Fase 2) não
consegue popular as colunas que o solver espera.

Side effect: o importador broker-side (S04) não traz buy/sell/
currency porque o broker não publica esses metadados. O modal
de review do import precisa expor os 3 campos com defaults
para o usuário ajustar antes do commit.

Conventions seguidas:
- Alembic migrations: hand-written (matching 0001-0006 + 0014-0015
  style), `revision`/`down_revision` chain, `batch_alter_table`
  para ADD CONSTRAINT (SQLite limitation).
- `tests/conftest.py` `_INTEGRATION_PREFIXES` é o source of truth
  pra tagging; novos testes DB-hitting precisam ser adicionados.
- `data/seed/` CSV triplet é a única fonte de verdade de asset /
  position; nenhum seed inline ou hardcoded.

## Goals / Non-Goals

**Goals:**
- Adicionar `buy_enabled`, `sell_enabled`, `currency_code` ao
  modelo `Asset`.
- Migration Alembic 0016 com backfill seguro (`server_default`)
  + CHECK constraint em `currency_code` (`BRL` ou `USD`).
- PATCH / POST endpoints estendidos com body unificado
  (target_pct + 3 campos novos).
- CSV seed: header estendido + parser + dataclass atualizados.
- UI dashboard: toggle inline por linha (sem bulk por classe).
- UI import: 3 controles novos no modal de review.
- Tests cobrindo migration, defaults, CHECK, endpoints, UI e2e.

**Non-Goals:**
- Solver CVXPY (Fase 4 do plano, change separada).
- Builder de `PortfolioSetup` (Fase 2 / Gap E, change separada).
- Adapter `MarketPriceLookup` (Fase 2 / Gap G, change separada).
- Bulk toggle por classe (decisão owner: fora, só per-asset).
- Conversão USD→BRL no solver (Fase 4).
- Adicionar EUR/GBP/CNY ao CHECK (migration trivial quando
  precisar).
- Pydantic schema `AssetBase`/`AssetPatch` (rotas usam `dict`,
  consistente com padrão atual).
- CVXPY dependency em `pyproject.toml` (Fase 4).

## Decisions

### D1. Defaults TRUE / TRUE / BRL (inversão de DD#3 do plano)

Plano original §DD#3 propunha `buy_enabled=False`,
`sell_enabled=False` como defaults (opt-in explícito por ativo).
Decisão owner 2026-06-26: reverter para `True/True/BRL` (opt-out).

Razões:
- 48 assets × 2 flags = 96 cliques pra destravar antes do
  primeiro rebalance. Atrito operacional inviável.
- Herdados maturity-locked (RDB/CDB/Tesouro Selic) — usuário
  pode flipar pra `sell_enabled=false` explicitamente após ver
  o plano de rebalance sugerir venda.
- Trader BR típico sabe o que está fazendo; opt-in assume
  iniciante, omaha não é produto pra iniciante.

Trade-off aceito: usuário pode perder uma venda involuntária
numa primeira execução. Mitigação: review no modal de aporte
(Fase 3) mostra o plano antes de "executar" (na v1 é só
visualização).

### D2. CHECK constraint em `currency_code`

Adotar `batch_alter_table` + `create_check_constraint("ck_asset_currency_code",
"currency_code IN ('BRL', 'USD')")`. Mesma técnica do
`quote_kind` na migration 0014.

Razões:
- Allowlist explícito: valores fora do enum viram `IntegrityError`
  no DB em vez de string solta downstream.
- CHECK paralelo ao de `quote_kind` (asset_classes) — coerência
  interna do schema.
- Adicionar moeda nova (EUR, GBP, BTC) é migration trivial
  (`drop CHECK + add CHECK`).

### D3. PATCH body único (não 4 endpoints)

`PATCH /api/assets/{id}` aceita body com mix dos 4 campos:
`target_pct`, `buy_enabled`, `sell_enabled`, `currency_code`.

Razões:
- Coerente com padrão atual: PATCH já existe pra `target_pct`.
  Estender body é trivial; 4 endpoints separados = ruído.
- 1 round-trip = UX melhor pra toggle inline na tabela.
- Idempotência: PATCH é PUT-like semanticamente (set, não append).
- Validator per-field: campo ausente = noop; campo presente
  com valor inválido = 422 com `detail` específico.

### D4. CSV legacy = hard fail (não backward-compat)

Header antigo (sem as 3 colunas) vira `abort()` no
`scripts/seed_from_csv.py`, mesmo padrão do `quote_kind`.

Razões:
- Força migração explícita dos CSVs em disco.
- Sem auto-upgrade silencioso com defaults — divergência entre
  CSV e DB é surja garantida.
- Único inconvenience: `db-migrate` seguido de
  `db-seed-upsert` em instância com CSV antigo quebra.
  Mitigação: atualizar fixtures + `data/seed/*.csv` na mesma
  change.

### D5. Toggle inline por ativo (sem bulk por classe)

Owner decidiu: bulk toggle por classe = fora de escopo. UI
mostra botão pequeno por linha (toggle clicável) na tabela
de ativos.

Razões:
- Reduz superfície da change (sem novo endpoint
  `PATCH /api/classes/{id}/flags`).
- Toggle individual casa com modelo "opt-out" (D1).
- Bulk pode entrar em change futura se fricção aparecer.

### D6. Import modal: 3 controles novos

Modal de review (dashboard.html) ganha por linha:
- Toggle "Compra" (checkbox).
- Toggle "Venda" (checkbox).
- Select "Moeda" (`BRL` / `USD`).

Defaults por linha:
- Auto-matched (asset pré-existe): valor atual do
  `Asset.buy_enabled` / `sell_enabled` / `currency_code`.
- Unmatched (asset será criado): `True / True / BRL`.

Usuário pode flipar antes do commit. Commit propaga os 3 campos
no upsert (`auto_matched` → update, `unmatched` → create).

Razões:
- Broker CSV não traz buy/sell/currency.
- Sem controles no modal, `POST /import/commit` falharia (NOT NULL
  sem valor default no handler atual).
- Auto-matched puxar valor atual do asset garante continuidade
  operacional (não reseta toggle do usuário em re-import).

### D7. currency_code por ativo, não por classe (mantido do plano)

`AssetClass` continua sem `currency_code`. Cada `Asset` carrega
o seu. Decisão original do plano §DD#2 mantida.

Razões (já documentadas no plano):
- Mesma classe pode ter BRL (PETR4) e USD (AAPL) — não cabe
  na classe.
- `IVVB11/HTEK11/NUCL11` (BDRs) são cotados em BRL apesar de
  referenciar índice USD.
- BTC em Cripto é cotado em BRL na precificação do broker.

### D8. Migration id = 0016_asset_trade_flags

Sequence-based (não timestamp-based). `down_revision =
"1c73065cff10"` (head atual = `position_totals`).

Razões:
- Mantém convenção dos últimos numericos (0014, 0015).
- Timestamp-based (`2026_06_26_xxxx`) foi exceção, não padrão.

## Schema

```sql
-- alembic/versions/0016_asset_trade_flags.py (upgrade)

ALTER TABLE assets ADD COLUMN buy_enabled BOOLEAN NOT NULL DEFAULT 1;
ALTER TABLE assets ADD COLUMN sell_enabled BOOLEAN NOT NULL DEFAULT 1;
ALTER TABLE assets ADD COLUMN currency_code VARCHAR(8) NOT NULL DEFAULT 'BRL';

-- via batch_alter_table (SQLite rejeita ADD CONSTRAINT direto):
ALTER TABLE assets ADD CONSTRAINT ck_asset_currency_code
  CHECK (currency_code IN ('BRL', 'USD'));
```

## Defaults por tipo de ativo (seed)

```
┌─────────────────────────────┬────────────┬─────────────┬──────────────┐
│ Tipo                        │ buy_enabled│ sell_enabled│ currency_code│
├─────────────────────────────┼────────────┼─────────────┼──────────────┤
│ Herdado (RDB/CDB/Tesouro)   │ True       │ True        │ BRL          │
│ Tradeable BR (FII/Ações)    │ True       │ True        │ BRL          │
│ BDR/ETF BR-listed (IVVB11…) │ True       │ True        │ BRL          │
│ Internacional (IAU, IVV…)   │ True       │ True        │ BRL          │
│ Cripto (BTC)                │ True       │ True        │ BRL          │
└─────────────────────────────┴────────────┴─────────────┴──────────────┘
```

Nota: tudo BRL no seed. Diferenciação USD/BRL pode vir via UI
quando o usuário tiver ativos USD legítimos (ex: AAPL via
Avenue). Default BRL cobre o seed atual onde todos os tickers
US são comprados via Avenue e cotados em R$.

## Risks / Trade-offs

- **D1 (defaults TRUE):** primeira execução do rebalance pode
  propor venda de ativo maturity-locked. Mitigação: modal de
  aporte (Fase 3) mostra plano antes de "executar"; usuário
  ajusta flags via toggle inline antes de aceitar.
- **D2 (CHECK):** adicionar moeda nova = migration nova. Aceito:
  mudança de currency universe é rara e merece migration.
- **D4 (hard fail CSV):** esquecer de atualizar fixture quebra
  CI. Mitigação: rodar `task db-seed-diff` antes do PR como
  smoke check.
- **D6 (import modal delta):** aumenta escopo de Gap A (plano
  original não cobria). Aceito: é requisito funcional —
  sem isso, import quebra.
- **Migration backfill:** row pré-existente lê
  `True/True/BRL` (server_default). Sem migração de dados.
- **UI toggle:** linha com toggle disabled enquanto PATCH em
  flight (UX), não otimistic update.
- **CSV parser:** legacy CSVs em outras instâncias (não Italo/
  Ana) precisam ser atualizados manualmente. Não é caso dessa
  change (só Italo/Ana).

## Out of Scope

- CVXPY dependency + solver (Fase 4).
- Builders de `PortfolioSetup` e Position frame (Fase 2 / Gaps E+F).
- Adapter `MarketPriceLookup` (Fase 2 / Gap G).
- Rota `POST /api/rebalance` (Fase 3 / Gap D).
- Modal de aporte + UI de resultados (Fase 3+5 / Gap C).
- Bulk toggle por classe (decisão owner: fora).
- Conversão USD→BRL no solver (Fase 4).
- Pydantic schema `AssetBase`/`AssetPatch` (rotas usam `dict`).
- EUR/GBP/CNY como moeda válida (migration trivial futura).
