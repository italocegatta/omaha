# Plano de Implementação: Rebalanceamento de Carteira

> Este documento consolida a análise de lacunas entre o algoritmo de
> rebalanceamento de referência (projeto `investing`,
> `src/portfolio_rebalancing/domain/rebalancing.py`) e o estado atual
> do Omaha. Serve como guia para as próximas OpenSpec change proposals.
>
> Cada fase abaixo deve virar uma ou mais changes. A ordem respeita
> dependências técnicas.

## Sumário executivo

**Objetivo:** Portar o algoritmo de rebalanceamento hierárquico em 2
fases (CVXPY) do projeto `investing` para o Omaha, adaptando o design
para a arquitetura web (FastAPI + Alpine.js + SQLite) e preenchendo as
lacunas de modelo, UI e infraestrutura.

**Algoritmo de referência:**
`~/github/investing/docs/portfolio-rebalance-algorithm-reference.md`
(1126 linhas, commit `ca867ba`).

**Pipeline do algoritmo:**

```
PortfolioSetup (categories + assets com target_weights, buy/sell_enabled, currency_code)
  + Position (current_value por asset_key)
  + Contribution (R$)
  + MarketPriceLookup (live quotes)
  → CVXPY Phase 1 (alocação por categoria)
    → CVXPY Phase 2 (distribuição intra-categoria)
      → Policy cascade (contribution-only → overweight-sales → full-sales)
        → Pós-processamento (clamp, overspend, min-trade)
          → RebalancePlan (asset_plan 31 cols, category_plan 13 cols, metrics ~28 chaves)
```

## Design Decisions

Decisões globais (escopo do plano inteiro):

| # | Decisão | Valor |
|---|---|---|
| 1 | "Aplicar" o rebalance = **executar o otimizador e exibir o plano** | Não executa ordens reais. O usuário vê o plano e age manualmente na corretora. |
| 2 | `currency_code` por **ativo**, não por classe | Cada `Asset` tem sua própria moeda (BRL/USD). A `AssetClass` não carrega moeda. |
| 3 | Default `buy_enabled` / `sell_enabled` = **False** | Conservador: ativos importados/herdados começam bloqueados. Usuário opt-in explícito. |

Decisões da Fase 2 (`rebalance-infra` — data bridges + adapter
`MarketPriceLookup`). Detalhes completos + alternativas rejeitadas em
`openspec/changes/rebalance-infra/design.md`:

| # | Decisão | Valor |
|---|---|---|
| 4 | Colisão cross-class de `Asset.name` | `groupby("asset_key").first()` + warning por colisão nomeando ambos `AssetClass`. Zero migration, casa com `_validate_rebalance_inputs` do solver. Trade-off: dashboard mostra as duas linhas; solver trata como uma; warning expõe o shadow no modal. |
| 5 | `BRL=X` entra via `QuoteService._collect_symbols`, não no request path | Append automático sempre que existir algum `Asset.currency_code == "USD"`. Cache fica quente, latência da rota inalterada. Trade-off: `BRL=X` pode estar até 15 min stale (TTL do cache); aceitável para portfolio familiar — modal exibe "Cotação de HH:MM". |
| 6 | Builder emite coluna `quote_kind` extra (não usada pelo solver) | `assets["quote_kind"] = AssetClass.quote_kind`. Solver ignora colunas desconhecidas (CVXPY lê só named vars). Single source of truth, `get_quotes(assets)` continua sendo a única assinatura. |
| 7 | Classe vazia com `target_pct > 0` emite warning, não erro | Builder retorna warnings list; solver roda. Modal renderiza o warning; operador decide se adiciona ativos ou zera o target. Trade-off: o solver pode alocar caixa residual; warning torna o motivo visível. |
| 8 | Refactor de `portfolio_aggregates` é privado + duplicação deliberada nos builders | Extraído `_compute_class_totals(assets)` em `routes/pages.py`. Os builders de rebalance **não** importam o helper — re-implementam o mesmo loop (~20 linhas) em `rebalance/builders.py`. ~20 linhas de duplicação é mais barato que o blast radius de três test files + audit pipeline. |

## Lacunas vs Estado Atual

### FASE 1 — Fundação de Dados (pré-requisito de tudo)

#### Gap A: Modelo `Asset` — faltam `buy_enabled`, `sell_enabled`, `currency_code`

**Problema:** O solver usa `buy_enabled[i]` e `sell_enabled[i]` como hard
locks. Sem esses campos, o otimizador não sabe o que pode comprar/vender.
`currency_code` é necessário para resolução de símbolo de cotação e
conversão USD→BRL.

**O que existe hoje:**

```python
class Asset(Base):
    id, asset_class_id, name, target_pct, display_order, created_at
    # Sem buy_enabled, sell_enabled, currency_code
```

**O que precisa existir:**

```python
class Asset(Base):
    id, asset_class_id, name, target_pct, display_order, created_at
    buy_enabled: Mapped[bool]       # default False
    sell_enabled: Mapped[bool]      # default False
    currency_code: Mapped[str]      # "BRL" ou "USD", default "BRL"
```

**Artefatos a criar:**
- Migration Alembic (add columns, server_default para valores existentes)
- `data/seed/*_assets.csv`: adicionar colunas `buy_enabled`, `sell_enabled`, `currency_code`
- `scripts/seed_from_csv.py`: atualizar parser do CSV para as novas colunas
- `tests/conftest.py` / fixtures: atualizar factory defaults
- `Asset` Pydantic schema: expor os novos campos

#### Gap B: UI para toggles de trade

**Problema:** Sem interface para o usuário ver e alterar `buy_enabled` /
`sell_enabled`, os defaults `False` congelam todos os ativos.

**O que precisa existir:**
- Indicador visual por ativo na tabela do dashboard (ícone/coluna "Compra",
  "Venda")
- Toggle (checkbox ou botão) para alternar cada flag
- Bulk toggle por classe (ex: "liberar compra/venda para todos ativos desta
  classe")
- `PATCH /api/assets/{id}` estendido para aceitar `buy_enabled` e
  `sell_enabled` no body (hoje só aceita `target_pct`)
- Opcional: coluna na tabela de ativos mostrando se está bloqueado

### FASE 2 — Infraestrutura do Rebalance (constrói sobre Fase 1)

#### Gap E: Builder de `PortfolioSetup` a partir do ORM

**Problema:** O algoritmo espera um dataclass `PortfolioSetup(categories:
DataFrame, assets: DataFrame)` com colunas específicas. Hoje os dados
estão espalhados em tabelas SQL com escala 0-100 (percentuais) vs 0-1
(frações) que o algoritmo espera.

**Necessário:**
- Função `build_setup_from_db(profile_id) → PortfolioSetup` no novo
  módulo `src/omaha/rebalance/setup.py`
- Mapeamento de colunas com conversão de escala:

| Coluna `setup.assets` (algoritmo) | Origem ORM | Conversão |
|---|---|---|
| `asset_key` | `Asset.name.casefold()` | direto |
| `asset_name` | `Asset.name` | direto |
| `category_name` | `AssetClass.name` | direto |
| `category_key` | `AssetClass.name.casefold()` | direto |
| `currency_code` | `Asset.currency_code` | **Gap A** |
| `buy_enabled` | `Asset.buy_enabled` | **Gap A** |
| `sell_enabled` | `Asset.sell_enabled` | **Gap A** |
| `target_weight` (0..1) | `Asset.target_pct * AssetClass.target_pct / 10000` | escala |
| `target_weight_in_category` (0..1) | `Asset.target_pct / 100` | escala |
| `asset_order` | `Asset.display_order` | direto |

#### Gap F: Builder de Position DataFrame

**Problema:** O algoritmo espera um DataFrame de posição agregado por
`asset_key` com `current_value`, `invested_value`, `quantity`. Hoje
`portfolio_aggregates()` já faz computação similar mas o output é dict
aninhado do dashboard, não DataFrame.

**Necessário:**
- Função `build_position_frame(profile_id) → pd.DataFrame` no módulo
  `src/omaha/rebalance/position.py`
- Agregar por `asset_key`: sum `total_current`, sum `total_invested`, sum `qty`
- Calcular `current_weight = current_value / total_current_value`

#### Gap G: Adapter `MarketPriceLookup` sobre `QuoteService`

**Problema:** O algoritmo depende de um Protocol `MarketPriceLookup`
com método `get_quotes(assets: DataFrame) → DataFrame`. O Omaha tem
`QuoteService` + `QuoteCache` com interface diferente (chaveada por
`broker_ticker`, devolve `QuoteWithFreshness`).

**Necessário:**
- Classe `OmahaMarketPriceLookup` que implementa o Protocol
- Mapeamento `asset_key → broker_ticker` (pega o primeiro `Position` do `Asset`)
- Consulta `QuoteCache.get_many(symbols)`
- Retorna DataFrame no formato esperado:
  `asset_key, quote_symbol, quote_price, quote_currency, quote_timestamp, quote_status, usdbrl_rate`
- Fallback: se `quote_kind == "none"`, usar `Position.current_price` como
  `quote_price` com status `"not-requested"`.

### FASE 3 — Trigger + Rota (constrói sobre Fase 2)

#### Gap C: UI de aporte

**Problema:** Não há botão/campo para o usuário iniciar o rebalance.

**Necessário:**
- Quarto botão no sidebar: "Aportar" ou "Rebalancear"
- Modal de aporte com:
  - Campo `valor do aporte (R$)`
  - Botão "Calcular" → chama `POST /api/rebalance`
- Modal de resultados com:
  - Tabela de ordens (comprar/vender/manter) por ativo
  - Projeção por classe
  - Métricas: desvio atual vs projetado, caixa residual, política aplicada
  - Warnings (se houver)
- Alpine store `$store.rebalanceModal`

#### Gap D: Rota `POST /api/rebalance`

**Problema:** Não existe endpoint de rebalance.

**Necessário:**
- Novo roteador `src/omaha/routes/rebalance.py`
- Request schema: `{contribution: float}`
- Response schema: `RebalancePlanResponse` com versão serializável das
  31 colunas de `asset_plan`, 13 de `category_plan`, metrics dict, warnings list
- Lógica:
  1. Carregar `AssetClass` + `Asset` + `Position` do perfil ativo
  2. Construir `PortfolioSetup` (Gap E)
  3. Construir Position frame (Gap F)
  4. Construir `MarketPriceLookup` (Gap G)
  5. Executar solver (Fase 4)
  6. Retornar `RebalancePlan` como JSON
- Erro: se perfil não tem dados de posição, retornar 400 com mensagem

### FASE 4 — Motor de Otimização CVXPY (constrói sobre Fase 2)

#### Gap H: Algoritmo de rebalanceamento

**Problema:** O motor não existe. É a implementação do algoritmo em si.

**Necessário:**
- Novo módulo `src/omaha/rebalance/` com:
  - `constants.py` — transcrição literal das constantes da Seção 4 do
    documento de referência. Atenção máxima a unidades (R$ vs adimensional).
  - `models.py` — `PortfolioSetup`, `RebalancePlan` dataclasses
  - `solver.py` — implementação CVXPY:
    - `_build_category_phase1_model()` → Phase 1 LP
    - `_build_intra_category_model()` → Phase 2 LP
    - `_solve_intra_category()` → loop de min-trade enforcement
  - `policy.py` — cascata de políticas:
    - `_solve_hierarchical_policy()`
    - `_evaluate_contribution_only_solution()`
    - `_evaluate_progressive_sales_stage_solution()`
  - `postprocessing.py` — pós-processamento:
    - `_clamp_projected_values_to_target_side()`
    - `_reduce_buy_overspend()`
    - `_build_restriction_note()`
    - `_build_category_plan()`
    - `_build_plan_metrics()` (~28 chaves)
    - `_build_plan_warnings()`
  - `market_prices.py` — Protocol + adapters (junto com Gap G)
  - `validation.py` — `_validate_rebalance_inputs()` com 11 checks
- Testes: portar fixtures do Apêndice D e regressões do Apêndice B
- Dependência Python: adicionar `cvxpy` ao `pyproject.toml`

### FASE 5 — Resultados na Interface (constrói sobre Fase 3 + Fase 4)

**Necessário:**
- Tabela de ordens no modal de resultados:
  - Colunas: ativo, classe, valor atual, alvo, compra R$, venda R$, projetado, ação
  - Destaque visual para compras vs vendas
- Cards de métricas:
  - Desvio atual vs projetado (por ativo e por categoria)
  - Caixa residual
  - Política aplicada + motivo de fallback (se aplicável)
  - Total a comprar / vender
- Gráfico de barras comparando alocação atual vs projetada (opcional)
- Botão "Fechar" (apenas descarta o modal — o plano é informativo)

## Mapa de Dependências

```
Fase 1 (Gaps A+B) ──────────────────────┐
                                         │
                    Fase 2 (Gaps E+F+G) ◄┘ (precisa de buy_enabled/sell_enabled/currency_code)
                                         │
              ┌──────────────────────────┤
              │                          │
              v                          v
      Fase 3 (Gaps C+D)         Fase 4 (Gap H)
              │                          │
              └──────────┬───────────────┘
                         │
                         v
                 Fase 5 (Resultados UI)
```

**Nota:** Fase 3 e Fase 4 são paralelizáveis *se* a Fase 2 estiver
completa. Fase 3 depende da Fase 4 apenas para o fluxo completo
(botão "Calcular" → solver → resultados). Dá para construir o modal
com dados mockados enquanto o motor não fica pronto.

## Ordem de OpenSpec Changes Sugerida

| # | Change | Fase | Gaps | Descrição | Status |
|---|---|---|---|---|---|
| 1 | `asset-trade-flags` | 1 | A, B | Modelo + migration + seeds + UI toggles + PATCH estendido | ✅ archived 2026-06-26 |
| 2 | `rebalance-infra` | 2 | E, F, G | Builders (setup, position), adapter MarketPriceLookup | ✅ archived 2026-06-26 |
| 3a | `rebalance-route` | 3 | C, D | POST /api/rebalance + Pydantic schemas + glue + solver stub | 🟢 apply-ready (`openspec/changes/rebalance-route/`) |
| 3b | `rebalance-engine` | 4 | H | Motor CVXPY + constantes + validação + policy cascade | 🔴 não iniciada |
| 4 | `rebalance-page` | 3b/5 | — | Página `/rebalance` + sidebar "Rebalancear" + Alpine store + tabela | 🔴 não iniciada (consome o contrato definido em 3a) |

**Divisão Fase 3 / Fase 5:** a UI foi separada da rota (3a é puro backend + contrato JSON; 4 é UI que consome o contrato). Justificativa em `openspec/changes/rebalance-route/design.md` Decision 1 e `proposal.md` "Next change".

Changes 3a, 3b e 4 podem ser paralelizadas técnica e temporalmente
(3a define o contrato, 3b é independente, 4 depende apenas de 3a).

## Riscos e Observações

1. **CVXPY + SQLite:** O solver é puramente computacional (sem I/O),
   então não há conflito com SQLite. O CVXPY precisa estar instalado
   no ambiente — verificar se cabe no Docker image size.

2. **Tempo de solver:** CLARABEL resolve LP em milissegundos para
   dezenas de ativos. Mesmo com fallback SCS, o tempo deve ser
   < 1s. O endpoint pode ser síncrono sem problema.

3. **Regressões acopladas (Apêndice B):** Os bugs RBRX11 (Phase 1
   drenando categoria subponderada + Phase 2 vendendo ativo no alvo)
   precisam ser portados JUNTOS. Testes de regressão validam ambos.

4. **Precisão numérica:** As tolerâncias `1e-6` (ALLOCATION_TOLERANCE)
   e `1e-4` (DISPLAY_TOLERANCE) precisam ser literais. Erro de
   unidade (R$ vs adimensional) foi o erro #1 do documento de
   referência.

5. **Escala de target_pct:** DB usa 0-100. Algoritmo usa 0-1.
   O builder do `PortfolioSetup` precisa fazer `target_pct / 100`
   e `target_pct_class * target_pct_class / 10000` para
   `target_weight_total`. Inverter na exibição.

## Referências

- Algoritmo original: `~/github/investing/docs/portfolio-rebalance-algorithm-reference.md`
- Código original: `~/github/investing/src/portfolio_rebalancing/domain/rebalancing.py`
- Análise de gaps completa: sessão `/opsx-explore` do dia 2026-06-26
