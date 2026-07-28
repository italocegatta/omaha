# Tasks — F52 Waterfall ECharts nos cards de classe

Normative references: `openspec/.temp_assets/f49-bridge-handoff.md`,
`design.md` (D1-D12), approved mock
`src/omaha/templates/rebalance_bridge_mock.html`. Do NOT touch the mock
template or `/rebalanceamento/bridge-mock` route at any point.

## 1. Vendor ECharts runtime (design D1)

- [ ] 1.1 Determine latest stable ECharts release (6.x line per Context7;
      record exact version here: `____`), download the minified full UMD
      build to `src/omaha/static/vendor/echarts.min.js`; record file SHA-256
      here: `____`.
- [ ] 1.2 Add additive `{% block head_extra %}{% endblock %}` to
      `src/omaha/templates/base.html` after the Alpine script tag (no other
      base.html change).
- [ ] 1.3 In `src/omaha/templates/rebalance.html`, override `head_extra` with
      `<script defer src="/static/vendor/echarts.min.js"></script>`.
- [ ] 1.4 Smoke: `task serve`, open `/rebalanceamento` — `window.echarts`
      defined before `alpine:init` fires; page otherwise unchanged.

## 2. Render helper in `rebalance.html` (design D2, D3, D4, D7)

- [ ] 2.1 Add token resolver: read `--class-1`, `--positive`, `--negative`,
      `--alert-warn`, `--ink`, `--ink-muted`, `--border` from
      `getComputedStyle(document.documentElement)` + rgba 70% blend helper
      for grid color (mock `color-mix` parity).
- [ ] 2.2 Add `_formatPctBR(v)` (PT-BR, 0-1 decimals: `14,6%`/`15%`/`0%`) and
      `_signedShort(v)` (`+R$ 25,0k`/`-R$ 20,0k` via `_formatBRLShort` abs).
- [ ] 2.3 Strip manual-geometry emitters from `_bridgeData`
      (`stageX`, `stage.x`, `stage.style`, `y()`, `connectors` CSS strings);
      keep stages (`value/displayValue/tone/pctLabel/semanticLabel`), ticks,
      `ceiling`, ε classification, availability guard — math unchanged.
- [ ] 2.4 Build `_bridgeOption(model, tokens, compact)` → ECharts option per
      design D3: transparent base + value series (`stack:'bridge'`,
      `barWidth:'45%'`, per-item token colors, `borderRadius:[2,2,0,0]`),
      `markLine` dashed connectors (`symbol:['none','none']`, inkMuted,
      silent), yAxis `min:0/max:ceiling/interval:step` +
      `axisLabel.formatter=_formatBRLShort` + splitLine every tick (70%
      border), category xAxis with stage names only (`Atual`,
      `Compra`/`Venda`/`Sem operação` [OQ2], `Desvio`, `Alvo`), rich two-line
      labels (value bold ink + pct muted; mock font sizes; compact set at
      ≤360px), `tooltip:{show:false}`, `animation:false`, grid gutters per
      mock (2.2rem/1.9rem axis, 1.8rem bottom, ~2.4rem top).
- [ ] 2.5 Zero stage (|v| ≤ ε): data item value 0 + label `R$ 0`/`0%`, no bar
      geometry (design D5).
- [ ] 2.6 Add `renderBridgeChart(el, category, plan)`: availability guard
      (no-op when `_bridgeData` null — design D8), idempotent init, shared
      `ResizeObserver` → `chart.resize()` + option rebuild across the 360px
      breakpoint (design D7), `window` resize fallback.
- [ ] 2.7 Remove dead exports (`bridgeData`; `formatBRLShort` export if no
      remaining consumer); keep `bridgeAvailable`, `waterfallAriaLabel`,
      `netAction/netLabel`, `classCardClass`, `categoryAriaLabel`.

## 3. Template swap in `_rebalance_plan.html` (design D10)

- [ ] 3.1 Replace manual DOM L53-81 with single chart container:
      `<div data-testid="rebalance-class-chart" role="img"
      :aria-label="waterfallAriaLabel(c)"
      x-init="bridgeAvailable(c) && $nextTick(() => renderBridgeChart($el, c))">`.
- [ ] 3.2 Preserve bridge wrapper div + `data-testid="rebalance-class-bridge"`
      + `--unavailable` binding, fallback `<p>Dados indisponíveis para esta
      ponte</p>`, header L49-51, card shell bindings, asset table L90-151 —
      byte-identical except the swapped block.

## 4. CSS cleanup in `app.css` (design D9)

- [ ] 4.1 Rewrite `.rebalance-class-card-bridge` (L2889-2892) as chart
      container (`min-width:0; height:11.6rem;` keep margin rhythm).
- [ ] 4.2 Remove `.rebalance-waterfall*` block L2893-3002.
- [ ] 4.3 Remove `.rebalance-bridge-svg/-track/-residual/-marker*` +
      `--net-sell/--net-hold` + `.rebalance-bridge-legend` L3009-3056.
- [ ] 4.4 In `@media (max-width:360px)` L3058-3074: keep
      `.rebalance-class-card` padding; remove legend + waterfall overrides.
- [ ] 4.5 Verify `.rebalance-class-summary` (L2848-2854) and
      `.rebalance-class-card*` shell incl. `--above/--below` (L2855-2888)
      untouched; `.rebalance-bridge-unavailable` (L3003-3008) preserved.
- [ ] 4.6 Grep repo: zero remaining references to removed selectors.

## 5. Tests (design D11)

- [ ] 5.1 Update `tests/test_rebalance_page.py` bridge test (~L629-708):
      drop `rebalance-waterfall-grid/zero-line/connector` assertions; assert
      chart container testid per available card, fallback text for
      unavailable fixture, shell/`--above`/`--below` + aria-labels intact,
      removed texts absent (`Sugestões abaixo dos mínimos`, visible
      `Compra/Venda líquida` value line), no `rebalance-waterfall-`/
      `rebalance-bridge-svg` classes in response, vendored script tag +
      single-helper wiring present.
- [ ] 5.2 Run `task test-unit` and `task test-integration` — green.
- [ ] 5.3 Regenerate visual baselines:
      `UPDATE_VISUAL_BASELINES=1 task test-visual`, then `task test-visual`
      clean; confirm canvas renders in `rebalance-form`/`rebalance-plan`
      snapshots (buy/sell/zero states visible).
- [ ] 5.4 Full suite: `task test` green.

## 6. Delivery + gates

- [ ] 6.1 `task lint` clean.
- [ ] 6.2 Invoke `refresh-for-test` skill; emit mandatory delivery receipt
      (PRD §4.9) with LAN URL (`bash scripts/print_lan_url.sh`).
- [ ] 6.3 Owner side-by-side gate: `/rebalanceamento` vs
      `/rebalanceamento/bridge-mock` at desktop + 320px + dark; confirm OQ1
      (zero stage label-only) and OQ2 (`Sem operação` x-name). BLOCKER until
      approved — do not archive before.
- [ ] 6.4 Post-approval (finalize, minimal follow-up — design D12): delete
      `rebalance_bridge_mock.html`, mock route (`pages.py:667-698`), and
      `openspec/.temp_assets/f49-bridge-handoff.md`.
