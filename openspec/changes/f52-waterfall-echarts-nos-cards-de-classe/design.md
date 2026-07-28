# Design — F52 Waterfall ECharts nos cards de classe

Normative inputs: `openspec/.temp_assets/f49-bridge-handoff.md` (§1-§5),
approved mock `src/omaha/templates/rebalance_bridge_mock.html`, roadmap F52
block, and Apache ECharts current docs consulted via Context7
(`/apache/echarts-handbook`). The mock is normative — this design reproduces
it, it does not reinterpret it (handoff §3 lesson 4/5).

## Context

`/rebalanceamento` class cards currently render a manual HTML/CSS waterfall
(`_rebalance_plan.html` L52-83 + `_bridgeData` CSS-var emitters in
`rebalance.html` L158-199 + `.rebalance-waterfall-*` CSS L2893-3002). Labels
are hand-positioned (`--label-bottom: Math.min(90, y(end)+4)%`,
rebalance.html:184) and collide when levels converge. Owner approved the mock
(HTML/CSS static geometry) and directed ECharts for runtime (handoff §5).
App is dark-only (`app.css:4 color-scheme: dark`, no runtime theme toggle),
PT-BR, no JS build step, LAN-served (PRD §4.2).

## Goals / Non-goals

**Goals:** pixel-faithful reproduction of the approved mock per card; ONE
render helper for all cards; all business rules of handoff §2 preserved
verbatim; dead manual-implementation code removed; deterministic rendering
for visual snapshots; legible at 320px.

**Non-goals:** touching the mock route/template; changing solver, wire
schemas, thresholds, global metrics, seed; reintroducing removed texts;
fixing the unrelated pre-existing accent inconsistency between the two
`rebalance-page` requirements (L320-348 says green-above/red-below; shell CSS
and handoff say red-above/blue-below — out of scope, shell preserved as-is);
Alpine CDN vendoring (pre-existing, separate concern).

## Decisions

### D1 — Vendored ECharts in `static/vendor/`, not CDN

**Decision:** vendor the pinned minified UMD build at
`src/omaha/static/vendor/echarts.min.js` (full build — no bundler/tree-shaking
in this repo), loaded with `<script defer>` via a new additive
`{% block head_extra %}{% endblock %}` in `base.html` (inserted after the
Alpine tag), overridden in `rebalance.html` only.

**Rationale:**
- *Offline:* Omaha binds `0.0.0.0` and is used on a home LAN (PRD §4.2); the
  family network may lose internet while the server stays up. A CDN script
  would blank every chart. Vendored = zero external runtime dependency for
  the feature.
- *Maintenance:* one file, one pinned version, updated deliberately per
  release. ECharts is stable/Apache-2.0; upgrade = replace file + run
  snapshots. No lockfile/npm in repo today — vendoring fits the existing
  no-build static model (`src/omaha/static/`).
- *Determinism:* version cannot drift under us (contrast: Alpine is loaded
  from `unpkg.com/alpinejs@3.x.x` — floating range, pre-existing debt we do
  not extend).

**Alternatives rejected:** CDN (unpkg/jsdelivr) — offline failure mode +
version float; npm + bundler — introduces a build pipeline for one consumer;
custom build via ECharts online builder — opaque provenance.

**Version:** pin the latest stable at implementation time (Context7 shows the
current line is ECharts 6 — handbook references `v6-feature.md` /
`v6-upgrade-guide.md`; the waterfall/stack/axis APIs used here are stable
across 5→6). Exact version + file SHA recorded in `tasks.md` during apply.
`defer` guarantees availability before `alpine:init` (DOMContentLoaded), so
`x-init` render callbacks always see `window.echarts`.

### D2 — ONE render helper, same-file inline script

**Decision:** add `renderBridgeChart(container, category, plan)` inside the
existing `alpine:init` IIFE in `rebalance.html` (repo pattern: all page JS
inline there). Signature: pure-ish builder `_bridgeOption(model, tokens,
compact)` → ECharts option object + thin lifecycle wrapper (init once,
observe, dispose guard). Each card wires via
`x-init="$nextTick(() => renderBridgeChart($el, c))"` on the bridge div. No
new static JS file, no Alpine component API changes beyond dropping the
manual-geometry exports.

**Rationale:** single source of truth for option construction = the
owner-stated "gráficos de fácil manutenção"; matches existing inline-JS
convention; `_bridgeData` math (stages, ε, availability guard) is reused
unchanged — only its CSS-var/`stage.x`/`stage.style`/connector-string
emitters (L179-198) are removed (dead after this slice).

### D3 — ECharts option mapping (Context7-grounded)

Waterfall per the official handbook recipe
(`how-to/chart-types/bar/waterfall.md`): "ECharts does not have a built-in
waterfall series... simulated using a stacked bar chart" — a transparent,
non-interactive base series + a value series, both `stack: 'bridge'`.

- **Series `base`:** `type:'bar'`, `stack:'bridge'`, `itemStyle.color:
  'transparent'`, `emphasis.disabled: true`, no label, `silent:true`. Data:
  `[0, min(C1,C2), min(C2,C3), 0]` (totals anchored at zero — matches mock
  where Atual/Alvo start at R$0).
- **Series `value`:** `stack:'bridge'`, `barWidth:'45%'` (mock L81
  `width: 45%`, centered — ECharts centers bars in category columns), data
  items `{ value, itemStyle: { color: token } }` per stage: totals
  `var(--class-1)`, Compra `var(--positive)`, Venda `var(--negative)`,
  non-zero Desvio `var(--alert-warn)`, zero stage value `0`.
  `itemStyle.borderRadius: [2,2,0,0]` (mock L81 `2px 2px 0 0`).
- **Connectors (C1→C2→C3, dashed, no dots):** `markLine` on the value series
  with three coord pairs `[ {coord:[0,C1]},{coord:[1,C1]} ]`,
  `[1→2 at C2]`, `[2→3 at C3]`; `symbol:['none','none']`,
  `lineStyle:{ type:'dashed', width:1, color: tokens.inkMuted }`,
  `silent:true`, `label.show:false`, `animation:false`. Matches mock
  `.f49-mock-connector` (`1px dashed var(--ink-muted)`, L93).
- **xAxis:** `type:'category'`, `data` = stage display names
  `['Atual', 'Compra'|'Venda'|<zero-op name>, 'Desvio', 'Alvo']`,
  `axisTick:{ show:false }`, `axisLine:{ lineStyle: { color: tokens.border } }`
  (mock plot `border-bottom: 1px solid var(--border)`, L77), labels
  `color: tokens.inkMuted`, size per mock L107 (`.72rem` ≈ 11.5px; compact
  `.63rem` at ≤360px). Names NEVER repeated in bar labels (handoff §3
  lesson 6).
- **yAxis:** `min:0`, `max: axis.ceiling`, `interval: axis.step` — reusing
  the approved `_niceAxis` (rebalance.html:130-145) verbatim;
  `axisLabel.formatter: _formatBRLShort` (approved, reused as-is — mock ticks
  `R$ 0`/`R$ 50,0k` match its output exactly), `axisLabel.color:
  tokens.inkMuted`, `splitLine:{ show:true, lineStyle:{ width:1, color:
  gridColor } }` on every tick (handoff §1; mock L78).
- **Labels:** value series `label:{ show:true, position:'top' }` with `rich`
  text: line 1 value (weight 700, `color: tokens.ink`, size per mock L106
  `.56rem`≈9px / compact `.42rem`), line 2 percentage (`color:
  tokens.inkMuted`, `.48rem` / compact `.42rem`). Formatter per stage: totals
  `_formatBRLShort(v)`; deltas signed `+`/`-` + short abs (mock shows
  `+R$ 25,0k`, `-R$ 20,0k`; current `_formatBRLShort` has no `+` — a small
  `_signedShort(v)` wraps it, abs + explicit sign); pct via new
  `_formatPctBR(v)` = `toLocaleString('pt-BR',{min:0,max:1 fraction})+'%'`
  (mock: `14,6%`, `0,2%`, `15%`, `0%` — note current `formatPct1` uses
  `toFixed(1)` → `15.0%`/dot separator, which does NOT match the mock;
  `_formatPctBR` is the mock-exact formatter). **No manual repositioning** —
  library handles collision (handoff §3 lesson 3); `labelLayout` untouched.
- **grid:** `left/containLabel:true` tuned to mock's `2.2rem` axis gutter
  (compact `1.9rem`, mock L108), `top` ≈ `2.4rem` headroom for labels above
  the tallest bar (mock labels float above bar top, L96-99), `bottom` ≈
  `1.8rem` x-label zone (mock `margin-bottom:1.8rem`, L77). Container height
  `11.6rem` total (mock `9.8rem` plot + `1.8rem` labels, L75/L77) via
  `.rebalance-class-card-bridge` CSS.
- **`tooltip: { show: false }`** — spec forbids tooltip-only info; hover
  carries nothing.
- **`animation: false`** — deterministic canvas for visual snapshots and
  honest side-by-side comparison; the page is a data tool, chart motion is
  not part of the approved contract.

### D4 — Theming: token resolution at render time, no registerTheme

**Decision:** resolve colors per render pass via
`getComputedStyle(document.documentElement).getPropertyValue('--class-1' |
'--positive' | '--negative' | '--alert-warn' | '--ink' | '--ink-muted' |
'--border')` into a `tokens` object consumed by the option builder. No
`echarts.registerTheme`, no ECharts theme JSON.

**Rationale:** Context7 (`concepts/style.md`) shows `registerTheme` +
`init(dom, theme)` for reusable/multi-theme setups and `setTheme` for dark
swaps. This app has exactly one dark theme with no runtime toggle
(`color-scheme: dark`), so a registered ECharts theme would be a second copy
of the palette — the CSS tokens stay the single source of truth (DESIGN.md
§6, handoff §5 "proibido cor hardcoded"). Reading tokens at render also makes
`splitLine` alpha trivial: mock grid is `color-mix(in srgb, var(--border) 70%,
transparent)` (L78) — canvas cannot resolve `var()`, so the helper computes
the 70% blend itself (small `rgba(r,g,b,0.7)` conversion from the computed
`--border`; computed values return concrete `rgb()`). If a theme toggle ever
lands, the render function is already idempotent (dispose + re-render on
swap).

### D5 — Zero stage: label-only, mock-exact

**Decision:** zero-tolerance stage (|delta| ≤ ε or |desvio| ≤ ε) renders a
bar-data item of value `0` with `label.show:true` (label floats at the
cumulative level via the base series) and NO bar geometry. This reproduces
the mock exactly: FII residual has no `.f49-mock-bar` element at all, only
the `R$ 0` / `0%` label (mock L52-53).

**Note (open question OQ1):** handoff §1 wording says "zero = linha sólida
neutra sem barra" while the normative mock renders no line element for the
zero stage — the dashed connector at that level passes through
continuously. Mock wins (handoff §5: "reproduzir o contrato visual do item 1;
aceite = side-by-side com mock"). Flagged for owner confirmation at the
side-by-side gate; if a solid hairline is wanted, it is a one-line `markLine`
addition — no structural change.

### D6 — Zero-operation x-axis name (OQ2)

Mock fixtures cover only buy (Ações) and sell (FII); the zero-op stage name
on the x-axis is not fixed by the mock. **Decision:** `Sem operação`
(shortened form of the approved aria semantic `Sem operação líquida`,
rebalance.html:172). Flagged for owner confirmation at the gate; the aria
label keeps the full `Sem operação líquida` either way.

### D7 — Resize: one shared ResizeObserver + breakpoint option rebuild

**Decision:** one `ResizeObserver` watches all bridge containers and calls
`chart.resize()` per instance (Context7 `concepts/chart-size.md`: "For
scenarios where container size changes without triggering the browser's
resize event... consider using the ResizeObserver API"); `window` resize is a
secondary fallback. When a container crosses the 360px breakpoint (either
direction) the helper rebuilds the option with the compact font set (mock
L108 media query) — canvas does not read CSS media queries. Cards are
server-rendered once per page load (MPA, full reload on navigation), so there
is no teardown lifecycle beyond page unload; init is guarded against double
invocation (`chart` instance cached on the element).

### D8 — Unavailable state: no chart instance

`_bridgeData` returns `null` (non-finite input, no matching `asset_plan`
rows, `total_final_planned <= 0`) → the template's existing
`x-show="!bridgeAvailable(c)"` fallback `<p>Dados indisponíveis para esta
ponte</p>` renders and `renderBridgeChart` is never called (guard in the
`x-init` expression: `bridgeAvailable(c) && renderBridgeChart($el, c)`). No
canvas, no `R$0`, no geometry. `bridgeAvailable` export stays; `bridgeData`
export (manual-geometry consumer) is removed with the manual DOM.

### D9 — Dead CSS removal inventory (verified 2026-07-27)

Remove from `src/omaha/static/app.css`:

| Range (approx) | Selectors | Action |
|---|---|---|
| L2889-2892 | `.rebalance-class-card-bridge` | **Rewrite** as chart container: `min-width:0; height:11.6rem; margin:0.2rem 0 0.7rem;` |
| L2893-3002 | `.rebalance-waterfall`, `-plot`, `-axis`, `-tick`, `-grid-lines`, `-grid`, `-bar` (+ `--total/--purchase/--sale/--residual/--hold`), `-connector`, `-zero-line`, `-zero`, `-stages`, `-stage`, `-stage-name`, `-label` (+ `strong`/`small`), `-stage--*` label colors | **Remove** |
| L3003-3008 | `.rebalance-bridge-unavailable` | **Preserve** (fallback copy styling) |
| L3009-3056 | `.rebalance-bridge-svg`, `-track`, `-residual`, `-marker(--current/--target/--projected)`, `--net-sell`/`--net-hold` variants, `.rebalance-bridge-legend` | **Remove** (dead SVG-attempt code) |
| L3058-3074 | `@media (max-width:360px)`: keep `.rebalance-class-card` padding rule (L3059-3061); remove `.rebalance-bridge-legend` (L3062-3065) and all `.rebalance-waterfall-*` overrides (L3066-3073) | **Partial remove** |

Preserve EXACTLY: `.rebalance-class-summary` (L2848-2854) and
`.rebalance-class-card*` shell incl. `--above`/`--below` (L2855-2888).

### D10 — Template/JS surgery map

`_rebalance_plan.html`: replace L53-81 (manual DOM inside
`.rebalance-class-card-bridge`) with a single
`<div data-testid="rebalance-class-chart" role="img"
:aria-label="waterfallAriaLabel(c)" x-init=...>`; keep the bridge wrapper
div, its `data-testid="rebalance-class-bridge"`, the
`--unavailable` class binding, the fallback `<p>` (L82), header L49-51, and
the asset table L90-151 untouched.

`rebalance.html`: keep `_niceAxis`, `_plannedTotal`, `_formatBRLShort`,
`_targetForCategory`, `DISPLAY_TOLERANCE`, `_netAction`/`_netLabel`,
`_categoryAriaLabel`, `classCardClass`, `bridgeAvailable`,
`waterfallAriaLabel`; add `_bridgeOption`/`renderBridgeChart`/token +
`_formatPctBR`/`_signedShort`/rgba-blend helpers; remove from `_bridgeData`
the `stage.x`, `stage.style`, `y()`, `stageX`, `connectors` CSS-string
emitters (L176-198 minus the ticks/stages math that the option builder
reuses — stages keep `value/displayValue/tone/pctLabel/semanticLabel`), and
remove now-unused exports (`bridgeData`; `formatBRLShort` export stays only
if another consumer uses it — table cells do not; drop it from exports, keep
the function).

### D11 — Test strategy

Canvas is invisible to httpx TestClient; assertions split by layer:

1. **Server-rendered DOM (tests/test_rebalance_page.py):** update the bridge
   test (~L629-708): remove `rebalance-waterfall-grid/zero-line/connector`
   assertions; assert per-card chart container testid inside
   `rebalance-class-bridge`, fallback text for unavailable fixtures, shell +
   `--above`/`--below` intact, removed texts absent, and no
   `rebalance-waterfall-`/`rebalance-bridge-svg` class remaining in the
   response; assert the vendored script tag + single-helper wiring exist in
   the rendered HTML.
2. **Browser-level (tests/visual/test_snapshots.py):** real Chromium executes
   ECharts — regenerate `rebalance-form`/`rebalance-plan` baselines with
   `UPDATE_VISUAL_BASELINES=1 task test-visual` (chart canvas is inside the
   snapshotted regions). This is the behavioral evidence for render-per-card,
   buy/sell/zero states, and 320px/dark legibility, alongside the owner
   side-by-side gate.
3. No POC/mock tests (handoff §3 lesson 9). No new BDD scenarios (PRD §4.7 —
   extraction by growth; no new workflow shape here).

### D12 — Mock retirement plan (registered, not implemented here)

During apply: `/rebalanceamento/bridge-mock` +
`rebalance_bridge_mock.html` + mock-only CSS stay byte-identical. After owner
approves side-by-side, finalize performs the minimal follow-up: delete
template, route (`src/omaha/routes/pages.py:667-698`), and
`openspec/.temp_assets/f49-bridge-handoff.md` in the archive commit. If the
owner requests changes instead, the mock remains the reference.

## Risks

- **Canvas ≠ CSS pixel deltas:** ECharts text metrics differ subtly from the
  mock's HTML labels. Mitigation: mock-exact font sizes/colors/weights fed
  into the option; owner side-by-side gate at desktop + 320px + dark before
  archive.
- **`rich` label two-line layout:** value+pct stacked lines must not wrap at
  320px. Mitigation: compact font set below 360px (mock L108 parity) +
  snapshot at 320px viewport.
- **ECharts 6 API deltas:** waterfall recipe verified via Context7 handbook
  (stable across 5→6 for `stack`/`markLine`/`axisLabel`); exact version pinned
  + smoke-tested in apply task 1 before any integration work.
- **Full bundle size (~1 MB):** LAN-served, `defer`, single page consumer.
  Acceptable; custom build would need a toolchain the repo doesn't have.
- **Superseded F49 change folder** still carries an unarchived delta on the
  same requirement. F52's MODIFIED text is self-contained (replaces the main
  spec requirement wholesale); orchestrator keeps F49 `Blocked`/superseded so
  its delta never syncs.

## Open questions (for owner confirmation at the side-by-side gate)

- **OQ1:** zero stage = label-only (mock-exact) vs handoff §1's "linha sólida
  neutra" wording — implemented label-only; one-line `markLine` addition if
  owner wants the hairline.
- **OQ2:** zero-operation x-axis name `Sem operação` (no mock fixture covers
  this case).
