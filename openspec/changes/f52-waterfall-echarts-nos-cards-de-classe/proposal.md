## Why

The F49 manual HTML/CSS waterfall inside the real `/rebalanceamento` class
cards is broken: absolutely-positioned labels (`--label-bottom: Math.min(90,
y(end) + 4)`) collide and mislevel whenever cumulative levels are close
(handoff §3, lesson 3). The owner-approved visual contract lives in the mock
(`src/omaha/templates/rebalance_bridge_mock.html`, route
`/rebalanceamento/bridge-mock`), and the owner has directed Apache ECharts as
the runtime renderer (handoff §5): a chart library resolves label collision
and scaling, and ONE reusable render helper keeps maintenance simple. The
normative reference for this slice is
`openspec/.temp_assets/f49-bridge-handoff.md` (§1 visual contract, §2 business
rules, §3 lessons, §4 verified inventory, §5 ECharts directive).

## What Changes

- Replace the manual `.rebalance-waterfall*` DOM inside
  `_rebalance_plan.html` (L52-83) with a single ECharts container per class
  card, rendered by ONE shared JS helper in `rebalance.html` that consumes the
  existing `window.__rebalancePlan` payload.
- Vendor Apache ECharts (pinned minified UMD build) at
  `src/omaha/static/vendor/echarts.min.js`, loaded via a new additive
  `{% block head_extra %}` in `base.html` (design decision D1: vendored, not
  CDN — offline LAN app, deterministic version, single-file maintenance).
- Reproduce the approved mock exactly: sequence
  `Atual → Compra/Venda → Desvio → Alvo`; blue `--class-1` totals anchored at
  zero; green `--positive` / red `--negative` floating deltas; amber
  `--alert-warn` non-zero Desvio; zero stage = `R$ 0` + `0%` label, no bar;
  dashed cumulative connectors without endpoint dots; local BRL scale per card
  via the approved `_niceAxis`; grid on every tick; 45% centered bars; stage
  names only on the X axis; bar labels only absolute short scale + percentage.
- Preserve unchanged: all business rules (ε = `DISPLAY_TOLERANCE = 0.0001`,
  percentage denominator `total_final_planned = Σ asset_plan.target_value`,
  never `target_pct`; fallback `Dados indisponíveis para esta ponte` with NO
  chart instance), the exact `.rebalance-class-card*` shell CSS,
  `.rebalance-class-summary` grid, `data-testid`s, aria-labels, the
  unavailable fallback, and the asset-plan table.
- **BREAKING (internal only):** remove the manual waterfall implementation —
  `.rebalance-waterfall-*` DOM and its JS geometry emitters
  (`stage.x`/`stage.style`/connector CSS strings in `_bridgeData`), dead CSS
  `.rebalance-waterfall-*` (~L2893-3002), `.rebalance-bridge-svg/-track/
  -residual/-marker/-legend` (~L3009-3056), and the 360px waterfall overrides
  (~L3066-3073). Rewrite `.rebalance-class-card-bridge` as the chart
  container.
- Do NOT touch the mock route `/rebalanceamento/bridge-mock` or
  `rebalance_bridge_mock.html` during implementation. Retirement is a minimal
  follow-up in finalize, only after the owner approves the ECharts version
  side-by-side (registered here per roadmap F52 note).
- Removed texts MUST NOT return: `Sugestões abaixo dos mínimos viram Manter.`
  and any visible `Compra/Venda líquida` line + value (net stage name remains
  aria-label-only).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rebalance-page`: the class-card bridge requirement changes its rendering
  contract from manual HTML/CSS plot geometry (F49, superseded and never
  visually approved in runtime) to an ECharts-rendered waterfall with the same
  business semantics, mandatory short-scale labels (`R$ 113,7k`) on bars and Y
  axis, disabled tooltip, and token-resolved colors; manual DOM/CSS selectors
  are removed from the contract.

## Impact

- Templates: `src/omaha/templates/_rebalance_plan.html` (bridge DOM swap),
  `src/omaha/templates/rebalance.html` (one render helper + removal of manual
  geometry emitters), `src/omaha/templates/base.html` (additive
  `{% block head_extra %}` + vendored script tag only).
- Static: new `src/omaha/static/vendor/echarts.min.js` (pinned);
  `src/omaha/static/app.css` dead-selector removal +
  `.rebalance-class-card-bridge` rewrite. Shell `.rebalance-class-card*`
  (L2855-2888) and `.rebalance-class-summary` (L2848-2854) preserved EXACTLY.
- Tests: `tests/test_rebalance_page.py` (bridge assertions updated —
  `rebalance-waterfall-grid/zero-line/connector` markers disappear),
  `tests/visual/test_snapshots.py` baselines regenerated
  (`UPDATE_VISUAL_BASELINES=1`).
- No changes to routes (except the untouched mock route), `schemas.py` wire,
  solver, thresholds, global metrics, seed, or migrations.
- Dependency: + Apache ECharts (Apache-2.0, vendored, version pinned in
  tasks.md). No build step — full UMD min build.
- Follow-up after owner approval (finalize, minimal): delete
  `rebalance_bridge_mock.html`, the `/rebalanceamento/bridge-mock` route
  (`pages.py:667-698`), and `openspec/.temp_assets/f49-bridge-handoff.md`.
- Risks: canvas text rendering differs subtly from the CSS mock (mitigation:
  side-by-side owner gate at desktop + 320px + dark); ECharts ~1 MB asset
  (mitigation: vendored once, LAN-served, `defer`).
