## 1. Backend — calculation helpers

- [ ] 1.1 Em `src/omaha/calculation/rentabilidade.py` (novo módulo),
      implementar `compute_window_summary(positions, quotes_by_asset,
      asset_id_to_class, as_of: date) -> WindowSummary` (pure): filtra
      posições com `imported_at <= as_of`, aplica carry-forward
      (`last_known_quote(quotes_by_asset[asset_id], as_of)` por ativo;
      fallback em `Position.current_price` quando ausente), retorna
      `{invested, current, gain, gain_pct}`. Garantir divisão segura
      (`invested == 0` → `gain_pct = None`).

- [ ] 1.2 No mesmo módulo, implementar `compute_class_breakdown(
      positions, quotes_by_asset, asset_id_to_class, as_of) ->
      list[ClassRow]` agregando por `class_id` (soma de investido,
      current, gain; `gain_pct` segue a mesma regra de janela).

- [ ] 1.3 Implementar `compute_monthly_series(positions,
      quotes_by_asset, asset_id_to_class, *, window: int | str = 12,
      now: date | None = None) -> list[Point]`: gera pontos mensais
      (primeiro dia do mês, UTC) do `min(imported_at)` (se
      `window="all"`) ou dos últimos `window` meses; cada ponto
      reaplica `compute_window_summary(as_of=point_date)`.

- [ ] 1.4 Implementar `quote_stale_assets(quotes_by_asset, as_of:
      date, *, threshold_days: int = 30) -> list[int]`: retorna
      `asset_id` cuja última `Quote.fetched_at` é anterior a
      `as_of - threshold_days`.

- [ ] 1.5 Exportar o módulo em `src/omaha/calculation/__init__.py`
      (criar `__init__.py` se ainda não existir) com `__all__`
      contendo os 4 helpers.

## 2. Backend — routes

- [ ] 2.1 Criar `src/omaha/routes/rentabilidade.py` com dois routers
      (FastAPI APIRouter):

      - `GET /api/rentabilidade/summary` → resolve perfil via
        `require_user` + `require_active_profile`; detecta modo
        Família (`?view=household` ou sentinel bind) e usa
        `family_aggregates` (F06) para alimentar
        `compute_class_breakdown` quando aplicável; senão agrega
        sobre `AssetClass` + `Position` + `Quote` do perfil.
      - `GET /api/rentabilidade/series?window=<int|"all">` (default
        `12`) → mesma resolução de perfil; chama
        `compute_monthly_series`.

      Garantir `Cache-Control: no-store` em ambas as respostas
      autenticadas.

- [ ] 2.2 Em `src/omaha/routes/pages.py`, substituir o handler atual
      `/rentabilidade` (stub): extrair contexto (perfis reais + Família
      sentinel via `_real_profiles` se Família; classe/asset via
      `family_asset_classes` ou `AssetClass` direto); renderizar o
      template novo passando `as_of`, `windows`, `classes`,
      `quote_stale_assets`. Reusar `patrimonio-portfolio-header`
      include.

- [ ] 2.3 Registrar o router criado em 2.1 via `src/omaha/main.py`
      (FastAPI `include_router`); verificar `require_user` +
      `require_active_profile` aplicados como dependencies em ambos
      endpoints (gate de Família via `require_profile_writable` em
      eventuais PATCH/POST que venham a existir — F03 não cria
      mutações, mas garantir coerência de assinatura de dependency
      igual a `/rebalanceamento`).

## 3. Templates + CSS

- [ ] 3.1 Substituir `src/omaha/templates/rentabilidade.html`
      (stub) por página com:

      - Banner read-only quando `view == "family"` (mesmo componente
        já existente em `patrimonio.html`).
      - Hero: include de `patrimonio-portfolio-header` com
        `window="all-time"` (3 métricas).
      - Tabela `Por janela` (label, investido, current, gain, %).
      - Tabela `Por classe (All-time)` (nome classe, investido,
        current, gain, %; coluna `Alvo %` suprimida quando
        `view == "family"`).
      - Tabela `Série mensal` (data, investido, current, gain, %).
      - Botão "Atualizar cotações" que chama
        `POST /api/quotes/refresh` e re-renderiza summary + series
        via Alpine AJAX (mesmo padrão do botão de refresh em
        `rebalance.html`).
      - `data-testid="rentabilidade-page"` na section raiz,
        `data-testid="rentabilidade-windows-table"` na tabela de
        janelas, `data-testid="rentabilidade-classes-table"`,
        `data-testid="rentabilidade-series-table"`,
        `data-testid="rentabilidade-refresh-btn"`.

- [ ] 3.2 Em `src/omaha/static/app.css`, adicionar regras
      `.rentabilidade-page`, `.rentabilidade-hero`,
      `.rentabilidade-windows-table`, `.rentabilidade-classes-table`,
      `.rentabilidade-series-table`, `.rentabilidade-refresh-btn`.
      Reusar tokens já existentes
      (`--accent`, `--ink`, `--bg`, `--paper`,
      `--muted-text`); sem adição de token novo.

- [ ] 3.3 Garantir que `base.html` marca a tab `Rentabilidade`
      como ativa quando `request.url.path` é `/rentabilidade`
      (já existe em F02; verificar nos smoke).

## 4. Tests

- [ ] 4.1 `tests/test_rentabilidade_summary.py` (novo, unit): cenários
      sintéticos em memória (sem DB) — perfil com 2 classes e 3
      posições, valida `compute_window_summary` para 6 janelas
      (1M/3M/6M/12M/YTD/All), confirma `gain_pct=None` quando
      `invested=0`, confirma soma acumulada via `imported_at`.

- [ ] 4.2 `tests/test_rentabilidade_series.py` (novo, unit):
      cenários de `compute_monthly_series`:

      - perfil com `imported_at` em jun/2024, `window=12` retorna
        12 pontos, primeiro ponto com `gain_pct=None` em meses
        anteriores a jun/2024;
      - `window="all"` retorna todos os meses desde jun/2024 até
        `now()` (≥12 conforme `now` rodar);
      - ativo sem quote no mês usa carry-forward da última
        cotação conhecida (Quote mais recente anterior ao `as_of`).

- [ ] 4.3 `tests/test_rentabilidade_quote_carry.py` (novo, unit):
      cenários de `quote_stale_assets` — ativo com quote fresca
      (5 dias) NÃO entra na lista; ativo com quote antiga (40 dias)
      ENTRA; ativo sem quote rows usa `Position.current_price` como
      valor final (não é stale).

- [ ] 4.4 `tests/integration/test_rentabilidade_route.py` (novo):
      `GET /rentabilidade` autenticado retorna 200 com
      `Cache-Control: no-store`; renderiza as 3 seções + hero;
      `GET /api/rentabilidade/summary` retorna JSON com shape
      documentado; `GET /api/rentabilidade/series?window=12`
      retorna 12 pontos; `GET /api/rentabilidade/summary` sem auth
      retorna 401; Família view agrega cross-User (classes
      duplicadas colapsam) e omite coluna `target_pct`.

- [ ] 4.5 Adicionar prefixos `test_rentabilidade_*` em
      `tests/conftest.py::_INTEGRATION_PREFIXES` (regra §4.6 /
      AGENTS.md — explicit allow-list, sem pattern matching).

- [ ] 4.6 `tests/bdd/features/rentabilidade.feature` (novo): cenário
      "Operador vê rentabilidade por janela e por classe em modo
      perfil" + cenário "Família agrega rentabilidade cross-User".

- [ ] 4.7 `tests/bdd/test_scenarios.py`: registrar os cenários novos
      de rentabilidade.feature via `@scenarios(...)` no test runner
      e step defs correspondentes em `tests/bdd/step_defs/` (matcher
      para "Vejo rentabilidade com <N> janelas listadas" e "Vejo
      tabela 'Por classe' com <N> classes listadas").

- [ ] 4.8 `tests/e2e/selectors.py`: adicionar helpers
      `rentabilidade_page`, `rentabilidade_windows_table`,
      `rentabilidade_classes_table`, `rentabilidade_series_table`,
      `rentabilidade_refresh_btn`.

- [ ] 4.9 Smoke visual via `task test-e2e` (sem novos selectors
      críticos para chart, mas o smoke de seletor_inventory deve
      passar após os data-testids serem aplicados).

## 5. Spec verification + delivery

- [ ] 5.1 Rodar `openspec validate f03-rentabilidade-page --json` e
      confirmar `valid: true`. Resolver issues antes de arquivar.

- [ ] 5.2 Rodar `opsx list --specs` (pós-apply) e confirmar que
      `rentabilidade` aparece com os 4 requirements adicionados em
      `openspec/specs/rentabilidade/spec.md`.

- [ ] 5.3 Rodar `task test-unit`, `task test-integration`,
      `task test-bdd`, `task test-e2e`. Todos verdes (BDD pode
      continuar com 4 fails pre-existentes do T05 fora do escopo).

- [ ] 5.4 Invocar `refresh-for-test` skill antes de reportar done:
      reiniciar `uvicorn` (`task serve`), conferir seed canonical
      (`db-reset` → 2 perfis reais + Família sentinel), abrir
      `/rentabilidade` no LAN URL (`bash scripts/print_lan_url.sh`),
      conferir hero + 3 tabelas, conferir modo Família via
      `?view=household`.

- [ ] 5.5 Após archive do apply: emitir delivery receipt conforme
      PRD §4.9 (refresh-for-test checklist).
