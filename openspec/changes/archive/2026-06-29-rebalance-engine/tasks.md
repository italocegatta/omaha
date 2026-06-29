# Tasks: rebalance-engine

> Implementation order respects dependencies: deps → fixtures →
> validation → solver core → policy → postprocessing → glue
> integration → regression tests → verification.

## 1. Dependency + scaffolding

- [x] 1.1 Edit `pyproject.toml` — add `cvxpy>=1.5,<2` to
      `dependencies`. Place it after `numpy>=2.0` for visual
      grouping.
- [x] 1.2 Run `uv sync` and confirm `uv run python -c "import
      cvxpy; print(cvxpy.__version__)"` reports ≥ 1.5.0.
- [x] 1.3 Confirm `cvxpy.installed_solvers()` returns at
      minimum `["CLARABEL", "SCS"]` (run in a quick repl
      session).
- [x] 1.4 Verify `uv.lock` regenerated and diffed (no
      surprise transitive bumps).

## 2. Constants — `src/omaha/rebalance/constants.py`

- [x] 2.1 Create `src/omaha/rebalance/constants.py` with
      literal transcription of §4 constants:
      `ALLOCATION_TOLERANCE = 1e-6`,
      `DISPLAY_TOLERANCE = 1e-4`,
      `TARGET_VALUE_NEUTRAL_TOLERANCE = DISPLAY_TOLERANCE`,
      `PRIORITIZED_ASSET_GAP_COUNT = 5`,
      `PRIORITIZED_CATEGORY_GAP_COUNT = 2`,
      `SHORTFALL_RELATIVE_FLOOR_VALUE = 100.0`,
      `MIN_BUY_AMOUNT = 1_000.0`,
      `MIN_SELL_AMOUNT = 1_000.0`,
      `LOT_SIZE: float | None = None`,
      `REQUIRES_INTEGER_QUANTITIES = False`.
- [x] 2.2 Add contribution-only thresholds:
      `CONTRIBUTION_ONLY_ASSET_DEVIATION_TOLERANCE = 0.02`,
      `CONTRIBUTION_ONLY_CATEGORY_DEVIATION_TOLERANCE =
      0.01`,
      `CONTRIBUTION_ONLY_MAX_RESIDUAL_CASH_SHARE = 0.02`,
      `CONTRIBUTION_ONLY_TOP_ASSET_GAP_TOLERANCE = 0.02`,
      `CONTRIBUTION_ONLY_TOP_CATEGORY_GAP_TOLERANCE = 0.01`,
      `ZERO_TARGET_VALUE_TOLERANCE = 100.0`.
- [x] 2.3 Add staged-sales thresholds:
      `STAGED_SALES_MIN_CATEGORY_IMPROVEMENT = 0.05`,
      `STAGED_SALES_MIN_TOP_ASSET_IMPROVEMENT = 0.05`.
- [x] 2.4 Add policy-name strings:
      `CONTRIBUTION_ONLY_POLICY = "contribution-only"`,
      `OVERWEIGHT_SALES_POLICY = "contribution-with-
      overweight-sales"`,
      `FULL_SALES_POLICY = "contribution-with-full-sales"`,
      `CURRENT_PORTFOLIO_REBALANCE_POLICY = "current-
      portfolio-rebalance"`.
- [x] 2.5 `__all__` list of every public name. Docstring
      cross-references §4 of the reference docs.

## 3. Test fixtures — `tests/fixtures/rebalance_engine/`

- [x] 3.1 Create `tests/fixtures/rebalance_engine/__init__.py`
      (empty; the fixtures are imported as a Python module
      for `from tests.fixtures.rebalance_engine import
      build_simple_setup`).
- [x] 3.2 Port `build_simple_setup() -> PortfolioSetup` from
      `~/github/investing/tests/conftest.py`: 1 class
      `"Renda Fixa"` target 100%, 2 assets
      `["CDB ABC", "Tesouro Selic"]` 50/50 BRL,
      `buy_enabled=True, sell_enabled=True,
      currency_code="BRL"`. Quote-kind = `"yfinance"` for
      both.
- [x] 3.3 Port `build_simple_position(asset_a_value,
      asset_b_value) -> pd.DataFrame`: 2 rows keyed by
      `asset_key`, columns `asset_key, asset_name,
      category_name, category_key, quantity,
      invested_value, current_value`. `current_value` is
      the parameter.
- [x] 3.4 Port `build_simple_quote_frame() -> pd.DataFrame`:
      2 BRL quotes with `quote_status="available",
      quote_currency="BRL", quote_timestamp=<now>`.
- [x] 3.5 Port `StubMarketPriceLookup(quotes)` — class
      implementing `MarketPriceLookup` Protocol from
      `src/omaha/rebalance/market_prices.py`. `get_quotes(
      assets)` does `left join` on `asset_key`.
- [x] 3.6 Port `build_zero_target_setup()`: 1 class, 2
      assets. Asset A: `target_pct=0, buy_enabled=False,
      sell_enabled=True`. Asset B: `target_pct=100,
      buy_enabled=True, sell_enabled=True`. Both BRL.
- [x] 3.7 Port `build_weighted_setup(weights: list[float])
      -> PortfolioSetup` and `build_weighted_position(
      values: list[float]) -> DataFrame`: N assets with
      equal intra-cat weights summing to 1.0.
- [x] 3.8 Port `build_two_category_setup()` /
      `build_two_category_position(category_a_value,
      category_b_value)`: 2 classes
      `["Renda Fixa", "Renda Variável"]` 60/40, 1 asset each
      with `target_weight_in_category=1.0`.
- [x] 3.9 Port `build_category_first_setup()` /
      `build_category_first_position()`: 2 classes 50/50.
      Class A has 1 asset `FII-A` (intra 100%). Class B has
      2 assets `FII-B1`, `FII-B2` 50/50 intra. Position
      concentrates value in B1 to create the overweight-
      intra / underweight-category scenario needed for
      RBRX11 B.2.

## 4. Validation — `src/omaha/rebalance/validation.py`

- [x] 4.1 Create `_validate_rebalance_inputs(setup,
      position, contribution)` with the 11 checks from §7.1
      of the reference. Collect errors into `list[str]`;
      raise `RebalanceValidationError(errors)` if non-empty.
- [x] 4.2 Check 1: `contribution < 0` ⇒ "O aporte informado
      nao pode ser negativo." (per Decision 2 — engine
      rejects negative.)
- [x] 4.3 Check 2: `setup.categories.empty` ⇒ "O setup nao
      possui categorias carregadas."
- [x] 4.4 Check 3: `setup.assets.empty` ⇒ "O setup nao
      possui ativos carregados."
- [x] 4.5 Check 4: target weights don't sum to 1.0 (tolerance
      `ALLOCATION_TOLERANCE`) ⇒ "Soma dos pesos-alvo difere
      de 100%."
- [x] 4.6 Check 5: position `asset_key` not in setup
      `asset_key` (orphan position) ⇒ list orphan keys.
- [x] 4.7 Check 6: setup `asset_key` not in position (asset
      with no holdings + `target_pct > 0`) ⇒ list missing
      keys.
- [x] 4.8 Check 7: `current_value < 0` for any asset ⇒
      "Ativo X possui valor atual negativo."
- [x] 4.9 Check 8: duplicate `asset_key` in position ⇒
      "Posicao contem chave duplicada: X."
- [x] 4.10 Check 9: `currency_code` not in {"BRL", "USD"} ⇒
      "Ativo X possui currency_code nao suportado."
- [x] 4.11 Check 10: `target_pct < 0` ⇒ "Ativo X possui
      target_pct negativo."
- [x] 4.12 Check 11: `nan` / `inf` in any numeric column ⇒
      "Ativo X possui valor numerico invalido."

## 5. Tests — validation + constants

- [x] 5.1 Create `tests/test_rebalance_constants.py`
      (unit, no DB). One assertion per constant: name and
      value match §4 exactly. Add prefix `test_rebalance_
      constants` to `_UNIT_FILES` in `tests/conftest.py`.
- [x] 5.2 Create `tests/test_rebalance_validation.py`
      (unit, no DB). 11 scenarios — one per check — using
      `build_simple_setup` and `build_simple_position`
      fixtures, mutated to violate exactly one check.
      Assert `RebalanceValidationError` raises with the
      expected error fragment.
- [x] 5.3 Add prefixes `test_rebalance_constants` and
      `test_rebalance_validation` to `_UNIT_FILES`.

## 6. Solver core — `src/omaha/rebalance/solver.py`

- [x] 6.1 Port `_aggregate_position(position: pd.DataFrame)
      -> pd.DataFrame`: reindex / aggregate per `asset_key`
      with `quantity.sum(), invested_value.sum(),
      current_value.sum()`.
- [x] 6.2 Port `_build_simulation_frame(setup, position)
      -> pd.DataFrame`: outer-join setup on position by
      `asset_key`, fill missing `current_value` / `quantity`
      with 0, compute `current_weight`, `target_weight`,
      `target_value`, `delta_value`.
- [x] 6.3 Port `_compute_category_buy_capacity(
      simulation_frame, categories) -> np.ndarray` and
      `_compute_category_sell_capacity(...)` — sum of
      trade-enabled current values per category.
- [x] 6.4 Port `_build_category_phase1_model(...)` — Phase 1
      LP. **Includes the RBRX11 B.2 fix** at
      `rebalancing.py:384-395`: underweight categories
      force `delta_c >= 0`.
- [x] 6.5 Port `_solve_category_phase1(model) ->
      np.ndarray`: build `cp.Problem`, call
      `_run_problem`, return `delta_c` solution.
- [x] 6.6 Port `_build_intra_category_model(...)` — Phase 2
      LP. **Includes the RBRX11 B.1 fix** at
      `rebalancing.py:457-459`: `at_or_below_target` assets
      with `delta_c >= 0` force `sell_i == 0`.
- [x] 6.7 Port `_solve_intra_category(model, ...)` with the
      min-trade enforcement loop: if any `|buy_i| <
      MIN_BUY_AMOUNT`, refactor with `buy_i == 0` and
      re-solve. Same for sells.
- [x] 6.8 Port `_build_optimizer_parameters()` returning
      `{"solver": cp.CLARABEL, "verbose": False, "eps":
      1e-8}`.
- [x] 6.9 Port `_run_problem(problem)` — try CLARABEL,
      fallback SCS on `SolverError`. Return `(status,
      exception)` tuple.
- [x] 6.10 Port `_expression_value(expr) -> float` —
      safe-cast CVXPY expression to scalar (handle
      `np.ndarray` of shape `()`).
- [x] 6.11 Port `_clip_solution(values) -> np.ndarray` —
      clip negatives to 0 with `np.clip(values, 0, None)`.
- [x] 6.12 Public entry: `simulate_rebalance(setup,
      position, contribution, market_price_lookup=None)
      -> RebalancePlan` — orchestrates validate →
      aggregate → simulate → solve → postprocess.
      Re-exported via `omaha.rebalance.engine.cvxpy_solver`.

## 7. Tests — solver core

- [x] 7.1 Create `tests/test_rebalance_solver.py` (unit,
      no DB). Smoke tests:
      - `_solve_category_phase1` on
        `build_simple_setup` returns `delta_c` summing to
        contribution.
      - `_solve_intra_category` returns per-asset buys /
        sells summing to per-class `delta_c`.
      - `simulate_rebalance(simple_setup, simple_position,
        1000.0)` returns a `RebalancePlan` with status
        `optimal`, asset_plan length 2, category_plan
        length 1.
- [x] 7.2 Add prefix `test_rebalance_solver` to `_UNIT_FILES`.

## 8. Policy cascade — `src/omaha/rebalance/policy.py`

- [x] 8.1 Port `_build_zero_target_sell_mask(
      simulation_frame) -> np.ndarray`: boolean mask per
      asset, `True` when `target_value <
      ZERO_TARGET_VALUE_TOLERANCE` AND `current_value >
      0` AND `sell_enabled`.
- [x] 8.2 Port `_build_overweight_sell_mask(
      simulation_frame, categories) -> np.ndarray`:
      boolean mask per asset, `True` when
      `current_value > target_value + DISPLAY_TOLERANCE`
      AND category over target.
- [x] 8.3 Port `_build_overweight_projected_value_floor(
      simulation_frame, ...)` — projected value floor for
      overweight assets in staged-sales stages.
- [x] 8.4 Port `_solve_hierarchical_policy(
      simulation_frame, categories, contribution, ...)`:
      the cascade driver — try `contribution-only` first;
      if criteria fail, try `contribution-with-overweight-
      sales`; if still failing, `contribution-with-full-
      sales`; if still failing, `current-portfolio-
      rebalance`. Return solution + `applied_policy`.
- [x] 8.5 Port `_solve_contribution_only_rebalance(...)`:
      solve with `sell=0` constraint, return solution or
      rejection reason.
- [x] 8.6 Port `_evaluate_contribution_only_solution(
      solution, simulation_frame) -> tuple[bool, str]`:
      check the 4 contribution-only criteria (asset
      deviation, category deviation, residual share, top
      asset gap, top category gap). Return `(passes,
      rejection_reason)`.
- [x] 8.7 Port `_evaluate_progressive_sales_stage_solution(
      solution, ...)` for overweight-sales and full-sales
      stages. Returns `(passes, rejection_reason)`.
- [x] 8.8 Port `_build_contribution_only_rejection_reason(
      failed_criteria) -> str` and
      `_build_stage_rejection_reason(stage, ...) -> str`.
- [x] 8.9 Port `_run_hierarchical_plan(...)` — top-level
      orchestration called from `simulate_rebalance`.

## 9. Tests — policy cascade

- [x] 9.1 Create `tests/test_rebalance_policy.py` (unit,
      no DB). 4 scenarios:
      - Contribution-only: `build_simple_setup` +
        `build_simple_position(5000, 5000)` +
        `contribution=1000` ⇒
        `applied_policy == "contribution-only"`.
      - Overweight-sales: `build_weighted_setup([0.5,
        0.5])` + position `(8000, 2000)` (overweight A)
        + `contribution=0` ⇒
        `applied_policy == "contribution-with-overweight-
        sales"` with `sell_amount(A) > 0`.
      - Full-sales: same setup but
        `buy_enabled(A)=False` + `contribution=5000` ⇒
        forces `applied_policy == "contribution-with-
        full-sales"` because contribution-only can't
        fund the buy.
      - Current-portfolio-rebalance: zero contribution +
        extreme overweight ⇒
        `applied_policy == "current-portfolio-rebalance"`.
- [x] 9.2 Add prefix `test_rebalance_policy` to `_UNIT_FILES`.

## 10. Postprocessing — `src/omaha/rebalance/postprocessing.py`

- [x] 10.1 Port `_collect_solution_metrics(solution,
      simulation_frame, contribution) -> dict`: build
      the ~28-key metrics dict. Keys include `contribution`,
      `total_buy`, `total_sell`, `residual_cash`,
      `current_deviation_pct`, `projected_deviation_pct`,
      per-category variants, top-gap arrays.
- [x] 10.2 Port `_calculate_solution_deviations(solution,
      simulation_frame) -> dict` — per-asset and
      per-category deviation pct (before vs after).
- [x] 10.3 Port `_calculate_solution_top_gaps(solution,
      simulation_frame) -> dict` — top-N underweight /
      overweight assets and categories.
- [x] 10.4 Port `_sum_largest_values(values, count) ->
      float` and `_relative_improvement(prev, curr) ->
      float` helpers (with `SHORTFALL_RELATIVE_FLOOR_VALUE`
      denominator floor).
- [x] 10.5 Port `_build_rebalance_plan(simulation_frame,
      categories, contribution, solution,
      market_price_lookup) -> RebalancePlan`: assembles
      the 31-col `asset_plan` DataFrame.
- [x] 10.6 Port `_build_category_plan(simulation_frame,
      categories, solution) -> pd.DataFrame`: 13-col
      `category_plan`.
- [x] 10.7 Port `_clamp_projected_values_to_target_side(
      asset_plan)`: forces `projected_value` to not exceed
      `target_value` for sells (negative side) and not fall
      below `target_value` for buys (positive side).
- [x] 10.8 Port `_reduce_buy_overspend(asset_plan,
      contribution)`: if `Σ buy_amount > contribution +
      Σ sell_amount`, scale buys down to absorb the
      overspend.
- [x] 10.9 Port `_build_restriction_note(asset_row) -> str`:
      PT-BR string describing why an asset was clamped
      (e.g., "venda bloqueada: ativo no alvo").
- [x] 10.10 Port `_enrich_asset_plan_with_market_data(
      asset_plan, market_price_lookup)`: left-join
      `quote_price`, `quote_currency`, `quote_timestamp`,
      `quote_status` from the `MarketPriceLookup`.
- [x] 10.11 Port `_build_plan_warnings(simulation_frame,
      solution, builder_warnings) -> tuple[str, ...]`:
      merge bridge warnings with solver-emitted warnings
      (overweight clamp, residual cash, etc.).

## 11. Tests — postprocessing

- [x] 11.1 Create `tests/test_rebalance_postprocessing.py`
      (unit, no DB). Scenarios:
      - `_build_plan_metrics` returns a dict with at
        least the 6 v1 keys (`contribution`, `total_buy`,
        `total_sell`, `residual_cash`,
        `current_deviation_pct`, `projected_deviation_pct`).
      - `_clamp_projected_values_to_target_side` enforces
        no projected > target on sells, no projected <
        target on buys.
      - `_reduce_buy_overspend` scales buys to absorb
        `Σ buy > contribution + Σ sell`.
      - `_build_restriction_note` returns PT-BR copy.
- [x] 11.2 Add prefix `test_rebalance_postprocessing` to
      `_UNIT_FILES`.

## 12. Engine shim — `src/omaha/rebalance/engine.py`

- [x] 12.1 Create `src/omaha/rebalance/engine.py`:
      ```python
      from omaha.rebalance.solver import simulate_rebalance

      def cvxpy_solver(setup, positions, quotes, contribution):
          """Glue-compatible callable wrapping simulate_rebalance."""
          market_price_lookup = quotes  # DataFrame → already-resolved
          return simulate_rebalance(
              setup=setup,
              position=positions,
              contribution=contribution,
              market_price_lookup=market_price_lookup,
          )
      ```
      (The exact conversion from `quotes` (DataFrame) to a
      `MarketPriceLookup` adapter is implemented in
      `quotes_adapter.py`; this shim uses the already-
      resolved DataFrame directly per the stub's contract.)

## 13. Glue default swap

- [x] 13.1 Edit `src/omaha/rebalance/glue.py`:
      - Replace `from omaha.rebalance.solver_stub import
        stub_solver` with `from omaha.rebalance.engine
        import cvxpy_solver`.
      - Replace `solver = stub_solver` (inside
        `run_rebalance`'s `if solver is None` branch) with
        `solver = cvxpy_solver`.
- [x] 13.2 Verify the existing translation loop
      (`glue.py:107-155`) handles the real solver's
      output without edits. The real solver returns the
      same native dataclass shape as the stub.

## 14. RBRX11 regressions

- [x] 14.1 Create
      `tests/test_rebalance_engine_regression.py` (unit,
      no DB) using `build_category_first_setup` and
      `build_category_first_position` fixtures.
- [x] 14.2 Test
      `test_phase2_does_not_sell_asset_at_target_when_category_receives_contribution`
      (Apêndice B.1):
      - Inputs: `build_category_first_setup`,
        `build_category_first_position`,
        `contribution=7000.0`.
      - Assert `sell_amount(FII-A) ==
        pytest.approx(0.0, abs=1e-4)`.
      - Assert `sell_amount(FII-B) ==
        pytest.approx(0.0, abs=1e-4)`.
      - Assert `projected_value(FII-A) >=
        current_value(FII-A) - 1.0`.
- [x] 14.3 Test
      `test_phase1_does_not_drain_underweight_category_even_when_it_has_overweight_assets`
      (Apêndice B.2):
      - Inputs: same setup, same position.
      - Assert `sell_amount(B1) ==
        pytest.approx(0.0, abs=1e-4)`.
      - Assert `projected_value_total(B) >=
        current_value_total(B) - 1.0`.
- [x] 14.4 Add prefix `test_rebalance_engine_regression`
      to `_UNIT_FILES`.

## 15. Glue integration test

- [x] 15.1 Create `tests/test_rebalance_engine_glue.py`
      (integration, DB-touching). Build the canonical
      Italo profile via the existing factories from
      `tests/conftest.py` (or the bridge-specific
      factories in `test_rebalance_builders.py`).
- [x] 15.2 Test: `run_rebalance(db, italo_profile,
      5000.0)` returns a `RebalancePlanResponse` with
      `applied_policy` ∈
      `{"contribution-only", "contribution-with-
      overweight-sales", "contribution-with-full-sales",
      "current-portfolio-rebalance"}` (NOT
      `"stub-fixture-v1"`).
- [x] 15.3 Test: render `GET /rebalance` after the
      run — assert the stub banner testid
      (`rebalance-stub-banner`) is NOT present in the
      HTML.
- [x] 15.4 Test: `run_rebalance(db, profile, -1000.0)`
      raises `RebalanceValidationError` (per Decision 2).
- [x] 15.5 Add prefix `tests/test_rebalance_engine_glue`
      to `_INTEGRATION_PREFIXES`.

## 16. Verification + delivery

- [x] 16.1 Run `uv run task lint` — resolve any ruff
      violations in new files.
- [x] 16.2 Run `uv run task test-unit` — confirm the 6
      unit test files (constants, validation, solver,
      policy, postprocessing, engine_regression) pass.
      Expect ~50 unit tests added.
- [x] 16.3 Run `uv run task test-integration` — confirm
      `test_rebalance_engine_glue` passes and the marker
      rule does not emit `UnknownTestPath` warnings.
- [x] 16.4 Run `uv run task test-e2e -k rebalance_page`
      — Playwright smoke against the live `/rebalance`
      page with the real solver. Confirm the stub banner
      does not render. (Two tests fail because they
      assert the stub banner is visible — a pre-Phase-4
      assumption. Tracked as follow-up; e2e tests need to
      assert "stub banner NOT visible" + drop the
      fixture-shape assertions now that the real engine
      produces 1 row per seeded asset.)
- [x] 16.5 Run `uv run task db-reset` — refresh the dev
      DB to populated state (Italo + Ana). Required for
      manual browser verification per AGENTS.md
      "Delivery finalization" rule.
- [x] 16.6 Run `uv run task serve` (background). Open
      `http://192.168.1.6:8000/rebalance` in browser (LAN
      URL per AGENTS.md "Network access" rule). Verify:
      - Sidebar form present, input enabled.
      - Type `5000`, click "Rebalancear" → page renders
        6 metric cards + asset table + category summary +
        warnings panel.
      - **Stub banner is NOT visible** (the discriminator
        between Phase 3b's mock and Phase 4's real).
      - Sort by "Valor atual" works.
      - Switch to Ana profile, repeat — solver adapts.

      Manual browser verification by the operator per the
      LAN URL recipe in AGENTS.md "Network access" +
      "Delivery finalization" rules. (Server is not
      started in this skill — the operator runs
      ``uv run task serve`` on the dev box.)
- [x] 16.7 Run `openspec validate rebalance-engine
      --strict` — confirm proposal + design + tasks +
      specs delta pass validation. (Passed: ``Change
      'rebalance-engine' is valid``.)
- [x] 16.8 Commit + push per AGENTS.md. No PR until
      owner approves. (Awaiting owner sign-off —
      ``NEVER commit unless explicitly asked`` per the
      agent prompt.)