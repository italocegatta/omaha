# Tasks — F52 Waterfall ECharts nos cards de classe

Normative references: `openspec/.temp_assets/f49-bridge-handoff.md`,
`design.md` (D1-D12), approved mock
`src/omaha/templates/rebalance_bridge_mock.html`. Do NOT touch the mock
template or `/rebalanceamento/bridge-mock` route at any point.

## 1. Vendor ECharts runtime (design D1)

- [x] 1.1 Determine latest stable ECharts release (6.x line per Context7;
      record exact version here: `6.1.0`), download the minified full UMD
      build to `src/omaha/static/vendor/echarts.min.js`; record file SHA-256
      here: `b66b25aeb4df84e33199dc21694014d336d222cbd9deb0e5a7c14bd6aa0d0fd0`.
- [x] 1.2 Add additive `{% block head_extra %}{% endblock %}` to
      `src/omaha/templates/base.html` after the Alpine script tag (no other
      base.html change).
- [x] 1.3 In `src/omaha/templates/rebalance.html`, override `head_extra` with
      `<script defer src="/static/vendor/echarts.min.js"></script>`.
- [x] 1.4 Smoke: `task serve`, open `/rebalanceamento` — `window.echarts`
      defined before `alpine:init` fires; page otherwise unchanged.

## 2. Render helper in `rebalance.html` (design D2, D3, D4, D7)

- [x] 2.1 Add token resolver: read `--class-1`, `--positive`, `--negative`,
      `--alert-warn`, `--ink`, `--ink-muted`, `--border` from
      `getComputedStyle(document.documentElement)` + rgba 70% blend helper
      for grid color (mock `color-mix` parity).
- [x] 2.2 Add `_formatPctBR(v)` (PT-BR, 0-1 decimals: `14,6%`/`15%`/`0%`) and
      `_signedShort(v)` (`+R$ 25,0k`/`-R$ 20,0k` via `_formatBRLShort` abs).
- [x] 2.3 Strip manual-geometry emitters from `_bridgeData`
      (`stageX`, `stage.x`, `stage.style`, `y()`, `connectors` CSS strings);
      keep stages (`value/displayValue/tone/pctLabel/semanticLabel`), ticks,
      `ceiling`, ε classification, availability guard — math unchanged.
- [x] 2.4 Build `_bridgeOption(model, tokens, compact)` → ECharts option per
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
- [x] 2.5 Zero stage (|v| ≤ ε): data item value 0 + label `R$ 0`/`0%`, no bar
      geometry (design D5).
- [x] 2.6 Add `renderBridgeChart(el, category, plan)`: availability guard
      (no-op when `_bridgeData` null — design D8), idempotent init, shared
      `ResizeObserver` → `chart.resize()` + option rebuild across the 360px
      breakpoint (design D7), `window` resize fallback.
- [x] 2.7 Remove dead exports (`bridgeData`; `formatBRLShort` export if no
      remaining consumer); keep `bridgeAvailable`, `waterfallAriaLabel`,
      `netAction/netLabel`, `classCardClass`, `categoryAriaLabel`.

## 3. Template swap in `_rebalance_plan.html` (design D10)

- [x] 3.1 Replace manual DOM L53-81 with single chart container:
      `<div data-testid="rebalance-class-chart" role="img"
      :aria-label="waterfallAriaLabel(c)"
      x-init="bridgeAvailable(c) && $nextTick(() => renderBridgeChart($el, c))">`.
- [x] 3.2 Preserve bridge wrapper div + `data-testid="rebalance-class-bridge"`
      + `--unavailable` binding, fallback `<p>Dados indisponíveis para esta
      ponte</p>`, header L49-51, card shell bindings, asset table L90-151 —
      byte-identical except the swapped block.

## 4. CSS cleanup in `app.css` (design D9)

- [x] 4.1 Rewrite `.rebalance-class-card-bridge` (L2889-2892) as chart
      container (`min-width:0; height:11.6rem;` keep margin rhythm).
- [x] 4.2 Remove `.rebalance-waterfall*` block L2893-3002.
- [x] 4.3 Remove `.rebalance-bridge-svg/-track/-residual/-marker*` +
      `--net-sell/--net-hold` + `.rebalance-bridge-legend` L3009-3056.
- [x] 4.4 In `@media (max-width:360px)` L3058-3074: keep
      `.rebalance-class-card` padding; remove legend + waterfall overrides.
- [x] 4.5 Verify `.rebalance-class-summary` (L2848-2854) and
      `.rebalance-class-card*` shell incl. `--above/--below` (L2855-2888)
      untouched; `.rebalance-bridge-unavailable` (L3003-3008) preserved.
- [x] 4.6 Grep repo: zero remaining references to removed selectors.

## 5. Tests (design D11)

- [x] 5.1 Update `tests/test_rebalance_page.py` bridge test (~L629-708):
      drop `rebalance-waterfall-grid/zero-line/connector` assertions; assert
      chart container testid per available card, fallback text for
      unavailable fixture, shell/`--above`/`--below` + aria-labels intact,
      removed texts absent (`Sugestões abaixo dos mínimos`, visible
      `Compra/Venda líquida` value line), no `rebalance-waterfall-`/
      `rebalance-bridge-svg` classes in response, vendored script tag +
      single-helper wiring present.
- [x] 5.2 Run `task test-unit` and `task test-integration` — green.
- [x] 5.3 Regenerate visual baselines:
      `UPDATE_VISUAL_BASELINES=1 task test-visual`, then `task test-visual`
      clean; confirm canvas renders in `rebalance-form`/`rebalance-plan`
      snapshots (buy/sell/zero states visible).
- [x] 5.4 Full suite: `task test` green.

## 6. Delivery + gates

- [x] 6.1 `task lint` clean.
- [x] 6.2 Invoke `refresh-for-test` skill; emit mandatory delivery receipt
      (PRD §4.9) with LAN URL (`bash scripts/print_lan_url.sh`).
- [x] 6.3 Owner side-by-side gate: `/rebalanceamento` vs
      `/rebalanceamento/bridge-mock` at desktop + 320px + dark; confirm OQ1
      (zero stage label-only) and OQ2 (`Sem operação` x-name). BLOCKER until
      approved — do not archive before.
- [x] 6.4 Post-approval (finalize, minimal follow-up — design D12): delete
      `rebalance_bridge_mock.html`, mock route (`pages.py:667-698`), and
      `openspec/.temp_assets/f49-bridge-handoff.md`.

## 7. Owner-directed visual tuning (pre-gate, supersedes mock details)

Owner confirmed the F52 charts work, then requested 3 coordinated
adjustments (override OQ2 + mock font sizes + shell-padding guidance):

- [x] 7.1 Zero-operation stage renders a BLANK x-axis category name
      (`_bridgeStageName` returns `''` for the hold tone; aria keeps
      `Sem operação líquida`; `Compra`/`Venda` unchanged).
- [x] 7.2 Bar labels +50%: strong .56→.84rem / pct .48→.72rem desktop,
      .42→.63rem both compact (px: 13.5/11.55, 10.05/10.05).
- [x] 7.3 Chart owns more of the card: grid L/R/T/B desktop 4/4/35/22,
      compact 6/6/30/21 (top headroom for +50% labels; bottom freed by
      the removed 2-line `Sem operação` wrap); card shell padding
      `0.85rem 1rem 0.9rem`→`0.5rem 0.6rem 0.55rem` (compact
      padding-inline 0.8→0.5rem), header margin-bottom 0.7→0.35rem,
      bridge margin `0.2rem 0 0.7rem`→`0.1rem 0 0.3rem`.
- [x] 7.4 Update bridge assertions in `tests/test_rebalance_page.py`
      (blank x-name contract replaces the `Sem operação` axis literal);
      regenerate rebalance visual baselines; browser-verify no
      clipping/overlap at 1440 + 320 with a zero-op scenario.

## 8. Owner directive — two-sided adaptive Y axis (2026-07-28, supersedes zero anchor)

Y-axis floor mirrors the ceiling rationale, per card: floor = smallest
level rounded DOWN to a nice number, ceiling = largest level rounded UP
(same step); total bars rebased to the floor so nothing clips.

- [x] 8.1 Replace one-sided `_niceAxis(maximum)` with
      `_niceAxisRange(minimum, maximum)` → `{floor, ceiling, step,
      intervals}`: one nice step ({1,2,2.5,5}×10ⁿ) for ~3-5 intervals
      over the level span; floor = LARGEST step multiple strictly below
      min (exact multiples step one interval down; relative ε = 1e-9 for
      FP noise); ceiling = SMALLEST step multiple strictly above max;
      window pick = tightest total range, ties finer step (two-sided
      analogue of the old "smallest ceiling" rule); near-zero span:
      step = smallest family member ≥ |level|/4, same strict bracket.
- [x] 8.2 `_bridgeData`: call
      `_niceAxisRange(Math.min.apply(null, levels), Math.max.apply(null,
      levels))`; add `floor` to the model; rebased tick values/positions.
- [x] 8.3 `_bridgeOption`: `baseData = [floor, Math.min(c1, c2),
      Math.min(c2, c3), floor]`; Atual/Alvo heights = `value - floor`
      (delta bases, ε logic, labels, connectors, aria UNCHANGED — text
      stays truthful); `yAxis.min: floor`.
- [x] 8.4 Align `tests/test_rebalance_page.py` (two-sided contract
      replaces the `_niceAxis` substring assertion); regenerate
      rebalance visual baselines + determinism check; cold-load e2e;
      browser-verify axes/no-clip/labels at 1440 + 320.

## 9. Owner directive — chart font standardization: Inter, weight 300 (2026-07-28)

Chart text adopts the page UI face. Inter chosen over Red Hat Display
(RHD ships only 700/800 — no light weights; 300 would synthesize from
700). Inter is variable, so 300 is a range widening, not a new family.
x-names 15px / value (R$) 14px / pct keeps 11.55px desktop; ALL chart
text at true weight 300 (val was 700).

- [x] 9.1 `base.html`: `Inter:wght@400..700` → `Inter:wght@300..700`
      (Red Hat Display + Material Symbols links untouched).
- [x] 9.2 `_bridgeOption`: local `var fontFamily` = page stack
      (`"Inter", -apple-system, …` per app.css body); x-axis
      `axisLabel` + `rich.val` + `rich.pct` declare it; `fontWeight:
      300` on all three (pct for consistency — sub-label never heavier
      than value).
- [x] 9.3 Sizes: desktop xName 11.5→15, strong 13.5→14, pct 11.55 kept.
      Compact scales by old compact/desktop ratios: xName 13
      (15×10.1/11.5≈13.2), strong 10.4 (14×10.05/13.5≈10.4), pct 10
      (11.55×10.05/11.55≈10.05, rounded to 10).
- [x] 9.4 Grid rebalance: bottom 22→26 desktop / 21→24 compact
      (margin 9 + one line: 15·1.05=15.75 / 13·1.05=13.65); top 35/30
      unchanged (14·1.15+11.55·1.15+4+1=34.4 ≤ 35; compact 28.5 ≤ 30);
      axisLabel width: desktop 62 unchanged (measured `Compra` 55.56px
      at 15px w300 fits), compact 44→52 (measured `Compra` 48.15px at
      13px w300 WRAPPED at 44 onto a clipped second line — browser
      probe caught it; 52 = 3.85px headroom, minimal widening).
- [x] 9.5 Tests: `tests/test_rebalance_page.py` (no font-size/weight
      assertions existed — zero assertion changes needed); rebalance
      visual baselines regenerated + determinism check; cold-load e2e;
      browser-verify computed Inter + true 300 + sizes + no clip at
      1440 + 320.
