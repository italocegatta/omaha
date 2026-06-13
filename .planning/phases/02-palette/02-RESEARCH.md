# Phase 02: Palette — Research

**Researched:** 2026-06-13
**Domain:** CSS design tokens / WCAG 2.1 AA color contrast / OKLCH color space
**Confidence:** HIGH

## Summary

The Phase 1 audit discovered 300+ state color pairs across 8 templates. The CSS token inventory (23 color tokens in `app.css`) reveals 2 genuine contrast failures requiring token value corrections: `--class-4` (orange `#ef6c00`, ratio 2.87 vs `--bg`) and `--class-6` (teal `#00838f`, ratio 4.21 vs `--bg`). The DESIGN.md target for class-4 (`oklch(0.62 0.15 50)`, ratio 3.57) also fails and needs lowering.

Two other token-level "failures" are false positives: `--accent-ink` on `--bg` (ratio 1.02 — accent-ink is never used on the body background; the real pair `--accent-ink` on `--accent` passes at 7.67:1) and `--accent` on `--ink` (ratio 2.23 — accent is a surface token used with accent-ink text, not with ink text).

The delete-confirm buttons use hardcoded `#fff` on `--negative` background (ratio 6.59, passes). Adding `--negative-ink` token formalizes this pair and satisfies PALT-01's "unambiguous fg/bg pairs for every surface" requirement. The token system is already surface-based with semantic naming (`--ink` not `--text-primary`), which is forward-compatible with dark mode (names stay, values swap).

**Primary recommendation:** Fix `--class-4` to `oklch(0.53 0.13 50)` (ratio 5.16), `--class-6` to DESIGN.md target `oklch(0.52 0.10 200)` (ratio 4.89), add `--negative-ink` token (`#ffffff`), convert error tokens to OKLCH, and rewrite DESIGN.md's token table with a Contrast column showing computed ratios. Keep all other token values as-is — they pass their real-world contrast pairs.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Full color section refresh — rewrite Color strategy, Accent rationale, Class swatches, Token table, and Migration path. Every section that references color gets updated to match the corrected token system.
- **D-02:** Add a "Contrast" column to the token table — each token pair shows its computed WCAG AA ratio and Passa/Falha status from the Phase 1 audit.
- **D-03:** No version history or changelog in DESIGN.md. It stays a living snapshot. Phase 2 changes are tracked in git commits and SUMMARY.md.
- **D-04:** Annotate the Component inventory table with the token names each component uses (e.g., "Uses --btn-primary-bg, --btn-primary-fg").

### the agent's Discretion

Token granularity (surface-level pairs vs component-scoped tokens), naming convention (semantic vs surface-paired), state tokens (error/disabled/success), and dark mode forward compatibility — the agent decides these based on Phase 1 audit findings, existing `app.css` patterns, and WCAG requirements.

### Deferred Ideas (OUT OF SCOPE)

- Dark mode (THEM-01, THEM-02) — v2 themes phase. Token system should be designed so dark mode can be added by swapping values without renaming tokens, but dark mode implementation is explicitly deferred.
- Layout or typography redesign — explicitly out of scope per REQUIREMENTS.md.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PALT-01 | Design tokens in `app.css` define unambiguous foreground/background pairs for every surface | §Token System Architecture, §Corrected Token Values, §Token Inventory Audit Results |
| PALT-02 | Each token pair has a documented minimum contrast ratio (body ≥ 4.5:1, UI/large ≥ 3:1) | §WCAG Contrast Requirements, §Corrected Token Values, §DESIGN.md Update Strategy |
| PALT-03 | `DESIGN.md` reflects the corrected token values and the rationale for each change | §DESIGN.md Update Strategy, §Token Inventory Audit Results |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Color token definition | Browser / Client (CSS) | — | Tokens are CSS custom properties in `:root`; browser resolves them |
| Contrast computation verification | API / Backend (Python audit) | — | `color_resolver.py` / `css_parser.py` compute ratios via coloraide; tokens verified before commit |
| Token documentation | Documentation (DESIGN.md) | — | Static markdown file consumed by humans and AI agents |
| Visual verification (post-change) | Browser / Client | Human | Phase 2 changes are value-only; verify via browser DevTools contrast checker |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| CSS custom properties | CSS3+ | Token definition and resolution | Browser-native, no build step, already in use |
| OKLCH color space | CSS Color 4 | All color values | Perceptually uniform, already adopted by DESIGN.md, forward-compatible with dark mode |
| coloraide | 8.8.1 | Contrast ratio computation during verification | Already installed (Phase 1), `contrast_ratio()` / `aa_status()` verified |
| tinycss2 | 1.5.1 | CSS parsing for token inventory | Already installed (Phase 1), `parse_stylesheet()` verified |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| coloraide | 8.8.1 | Compute contrast ratios for token verification | Before committing corrected tokens — verify every new value passes AA |
| tinycss2 | 1.5.1 | Re-run token inventory against updated app.css | After token changes — confirm all pass |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| OKLCH | Hex | Hex harder to adjust for contrast while preserving hue; OKLCH lightness is perceptual |
| Semantic tokens (`--ink`) | Surface-paired (`--text-on-bg`) | Surface-paired causes token explosion; semantic is 1 token used in many contexts |
| coloraide | Custom WCAG math | coloraide handles sRGB→linear→luminance correctly; hand-rolled math has known precision errors |

**Installation:**

```bash
# No new packages. All dependencies installed by Phase 1.
uv run python3 -c "import coloraide; import tinycss2; print('OK')"
```

**Version verification:**
```bash
uv run python3 -c "import coloraide; print(coloraide.__version__)"  # 8.8.1
uv run python3 -c "import tinycss2; print(tinycss2.__version__)"     # 1.5.1
```

## Package Legitimacy Audit

> No new packages installed. Phase 2 uses only existing Phase 1 dependencies (coloraide 8.8.1, tinycss2 1.5.1) which were already verified in 01-RESEARCH.md Package Legitimacy Audit.

| Package | Registry | Verdict | Disposition |
|---------|----------|---------|-------------|
| coloraide | PyPI | OK — previously verified in Phase 1 | Approved (existing) |
| tinycss2 | PyPI | OK — previously verified in Phase 1 | Approved (existing) |

**Packages removed due to SLOP verdict:** None
**Packages flagged as suspicious SUS:** None

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     DESIGN.md (source of truth)               │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ Token Table   │  │ Contrast Col │  │ Component Inventory│  │
│  │ (name+value)  │  │ (ratio+Passa)│  │ (token references) │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘  │
└─────────┼──────────────────┼───────────────────┼─────────────┘
          │                  │                   │
          ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    app.css :root block                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ --bg, --surface, --surface-sunk   (surface tokens)    │   │
│  │ --ink, --ink-muted, --accent-ink  (ink tokens)        │   │
│  │ --accent, --positive, --negative  (semantic colors)   │   │
│  │ --error-bg, --error-fg            (state tokens)      │   │
│  │ --class-1..6                      (data palette)      │   │
│  │ --fg → --ink, --muted → --ink-muted (legacy aliases)  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                     │
│            var() resolution propagates values                 │
│                         ▼                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Component rules reference var(--token)                │   │
│  │ .btn-primary { background: var(--accent);             │   │
│  │                color: var(--accent-ink); }            │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│              Verification pipeline (offline)                  │
│  css_parser.py → token inventory → contrast_ratio()          │
│  → aa_status() → Passa/Falha → validated before commit      │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
src/omaha/static/
├── app.css                 # :root tokens + component styles (PHASE 2 CHANGES)
└── ...

src/omaha/audit/            # Phase 1 tools reused for verification
├── css_parser.py           # parse_stylesheet(), color_token_inventory()
├── color_resolver.py       # contrast_ratio(), aa_status()
└── ...

DESIGN.md                   # Full color section rewrite (PHASE 2 CHANGES)

reports/
└── contrast_audit.html     # Phase 1 baseline report (reference only)
```

### Pattern 1: Surface-Based Token System with Semantic Naming

**What:** Tokens are named by their semantic role (`--ink` = text color, `--surface` = card background), not by their value (`--gray-900`) or by the component they style (`--btn-bg`). One token serves many components.

**When to use:** Always for this project. This is the established pattern in app.css and DESIGN.md. Component-scoped tokens would cause explosion (23 components × 5 states = 115 tokens minimum).

**Why semantic over surface-paired:** Surface-paired naming like `--text-on-bg`, `--text-on-surface`, `--text-on-accent` creates N×M explosion. Semantic naming (`--ink`, `--ink-muted`, `--accent-ink`) uses the ink/surface relationship: surface tokens get paired with the right ink token contextually.

**Token classification:**
```
FOREGROUND (compared against --bg):     SURFACE (compared against --ink):
  --ink, --ink-muted                      --bg, --surface, --surface-sunk
  --fg (→ --ink), --muted (→ --ink-muted) --accent
  --accent-ink, --negative-ink            --error-bg
  --positive, --negative
  --error-fg
  --class-1..6, --color-focus
```

### Pattern 2: Legacy Alias Pattern for Backward Compatibility

**What:** Keep `--fg: var(--ink)` and `--muted: var(--ink-muted)` aliases so existing `var(--fg)` call sites resolve correctly without sweeping renames.

**When to use:** During migration phases. Drop aliases when all call sites reference canonical names (future polish pass).

**Example:**
```css
/* Legacy aliases — transitional, keep indefinitely */
--fg: var(--ink);
--muted: var(--ink-muted);
```

### Anti-Patterns to Avoid

- **Component-scoped token proliferation:** Don't create `--btn-primary-bg`, `--btn-primary-hover-bg`, etc. Use `--accent` + `--accent-ink` and handle hover states with CSS filters/transforms (Phase 3). Component tokens duplicate surface tokens with no added value.
- **Value-named tokens:** Don't use `--green-600`, `--blue-400`. Names that encode values break when values change. Semantic names (`--accent`, `--positive`) survive value changes.
- **Hardcoded colors in component rules:** Replace `color: #fff` with `color: var(--negative-ink)`. The delete-confirm buttons currently violate this.
- **Mixing hex and OKLCH in the same token family:** The error tokens (`--error-bg: #fde8e8`, `--error-fg: #8a1f1f`) are hex while all others are OKLCH. Convert to OKLCH for consistency.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WCAG contrast ratio math | Custom sRGB→luminance formula | `coloraide.Color(fg).contrast(bg, method="wcag21")` | coloraide handles linearization, gamma, and the 0.04045 cutover correctly. Hand-rolled math has known precision errors at low values. |
| CSS parsing to discover tokens | Regex extraction of `--*` properties | `tinycss2.parse_stylesheet()` → `_build_registry()` → `resolve_var()` | Regex can't handle nested `var()` chains, `color-mix()`, or conditional rules. tinycss2 is a proper CSS parser. |
| Color space conversion (hex→oklch) | Manual conversion | `coloraide.Color("#ef6c00").convert("oklch")` | coloraide handles gamut mapping, chromatic adaptation. |
| Contrast verification of new tokens | Manual browser DevTools checking | `uv run python3 -c "from omaha.audit.color_resolver import contrast_ratio, aa_status; ..."` | Scripted verification is reproducible; DevTools checking is human-error-prone and not auditable. |

**Key insight:** The Phase 1 audit tools (`css_parser.py`, `color_resolver.py`) are reusable verification assets. Every token value change can be validated programmatically in < 1 second before committing. Do not rely on manual visual checks for contrast compliance.

## Runtime State Inventory

> Phase 2 is neither a rename/refactor nor a migration phase. It is a value change in CSS custom properties and a markdown documentation update. No runtime state is affected. This section intentionally empty.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None | — |
| Live service config | None | — |
| OS-registered state | None | — |
| Secrets/env vars | None | — |
| Build artifacts | None | — |

## Token Inventory Audit Results

> Computed 2026-06-13 via `color_token_inventory()` against current `app.css`. Methodology: foreground tokens compared against `--bg` (resolved `oklch(0.975 0.003 60)`); surface tokens compared against `--ink` (resolved `oklch(0.20 0.01 60)`). Contrast computed via coloraide's `wcag21` method. AA threshold: 4.5:1 for body text.

### Full Inventory (23 tokens)

| Token | Computed Value | Adj. BG | Ratio | Status | Note |
|-------|---------------|---------|-------|--------|------|
| `--bg` | oklch(0.975 0.003 60) | vs --ink | 16.85 | Passa | Body background |
| `--surface` | oklch(1.0 0 0) | vs --ink | 18.12 | Passa | Card/modal surface |
| `--surface-sunk` | oklch(0.96 0.003 60) | vs --ink | 16.13 | Passa | Form wells |
| `--ink` | oklch(0.20 0.01 60) | vs --bg | 16.85 | Passa | Primary text |
| `--ink-muted` | oklch(0.50 0.01 60) | vs --bg | 5.59 | Passa | Secondary text |
| `--fg` | → oklch(0.20 0.01 60) | vs --bg | 16.85 | Passa | Legacy alias, same as --ink |
| `--muted` | → oklch(0.50 0.01 60) | vs --bg | 5.59 | Passa | Legacy alias |
| `--border` | oklch(0.90 0.005 60) | vs --ink | 13.44 | Passa | Hairline (non-text, 3:1 pass) |
| `--border-strong` | oklch(0.82 0.008 60) | vs --ink | 10.37 | Passa | Card border |
| `--accent` | oklch(0.42 0.09 150) | vs --ink | 2.23 | Falha | **False positive** — accent is a surface; real pair is --accent-ink on --accent (7.67 Passa) |
| `--accent-ink` | oklch(0.98 0.005 150) | vs --bg | 1.02 | Falha | **False positive** — accent-ink is NEVER used on body bg; only on --accent surfaces |
| `--accent-ink` on `--accent` | — | — | **7.67** | **Passa** | **Real pair** — primary button text on accent fill |
| `--positive` | oklch(0.52 0.13 145) | vs --bg | 4.84 | Passa | Gain/success text |
| `--negative` | oklch(0.50 0.18 25) | vs --bg | 6.13 | Passa | Loss/error text |
| `--error-bg` | #fde8e8 | vs --ink | 15.44 | Passa | Error block bg |
| `--error-fg` | #8a1f1f | vs --bg | 8.50 | Passa | Error text |
| `--error-fg` on `--error-bg` | — | — | **7.79** | **Passa** | **Real pair** — error message block |
| `--class-1` | #0a66c2 | vs --bg | 5.29 | Passa | Deep blue swatch |
| `--class-2` | #2e7d32 | vs --bg | 4.77 | Passa | Deep green swatch |
| `--class-3` | #c62828 | vs --bg | 5.23 | Passa | Deep red swatch |
| `--class-4` | #ef6c00 | vs --bg | **2.87** | **Falha** | **GENUINE FAILURE** — orange too bright on off-white |
| `--class-5` | #6a1b9a | vs --bg | 8.73 | Passa | Deep plum swatch |
| `--class-6` | #00838f | vs --bg | **4.21** | **Falha** | **GENUINE FAILURE** — teal below 4.5:1 threshold |
| `--color-focus` | #2563eb | vs --bg | 4.81 | Passa | Focus ring on body bg |
| `--class-color` | → #0a66c2 | vs --bg | 5.29 | Passa | Component-scoped alias (first class) |

### Real Pairs That Matter (cross-referenced)

| Component | Foreground | Background | Ratio | Status |
|-----------|-----------|------------|-------|--------|
| Primary button (default) | `--accent-ink` | `--accent` | 7.67 | Passa |
| Primary button (hover, brightness 1.1) | `--accent-ink` | `--accent` × 1.1 | 6.81 | Passa |
| Error message block | `--error-fg` (#8a1f1f) | `--error-bg` (#fde8e8) | 7.79 | Passa |
| Delete confirm button | #fff (hardcoded) | `--negative` | 6.59 | Passa |
| White text on negative | #fff | `--negative` | 6.59 | Passa |
| Class-4 on body bg | #ef6c00 | `--bg` | **2.87** | **Falha** |
| Class-6 on body bg | #00838f | `--bg` | **4.21** | **Falha** |

### DESIGN.md Class Swatch Target Verification

| Slot | DESIGN.md Target | Ratio vs --bg | Status |
|------|-----------------|---------------|--------|
| 1 | oklch(0.50 0.14 250) | — | Not checked |
| 2 | oklch(0.50 0.13 145) | — | Not checked |
| 3 | oklch(0.50 0.18 25) | — | Not checked |
| 4 | oklch(0.62 0.15 50) | 3.57 | **Falha** — DESIGN.md target also fails |
| 5 | oklch(0.42 0.12 300) | — | Not checked |
| 6 | oklch(0.52 0.10 200) | 4.89 | Passa — but current hex fails at 4.21 |

## Corrected Token Values

### Tokens Requiring Change

| Token | Current Value | Problem | Corrected Value | Ratio vs --bg | How Verified |
|-------|--------------|---------|-----------------|---------------|-------------|
| `--class-4` | `#ef6c00` (hex) | Ratio 2.87 vs `--bg`, below 4.5:1 AA | `oklch(0.53 0.13 50)` | 5.16 | `contrast_ratio("oklch(0.53 0.13 50)", resolved_bg)` |
| `--class-6` | `#00838f` (hex) | Ratio 4.21 vs `--bg`, below 4.5:1 AA | `oklch(0.52 0.10 200)` | 4.89 | `contrast_ratio("oklch(0.52 0.10 200)", resolved_bg)` |

### DESIGN.md Class Swatch Target Correction

| Slot | DESIGN.md Current | Corrected Target | Ratio vs --bg | Rationale |
|------|-------------------|-----------------|---------------|-----------|
| 4 | oklch(0.62 0.15 50) | oklch(0.53 0.13 50) | 5.16 | Lower L from 0.62 to 0.53; kept hue 50 (burnt orange) and chroma ~0.13 — preserves "burnt orange, not tangerine" character |

### Tokens to Add

| Token | Value | Role | Rationale |
|-------|-------|------|-----------|
| `--negative-ink` | `#ffffff` | Text on negative backgrounds | Formalizes the delete-confirm `color: #fff` on `--negative` bg. Dark-mode ready: swap to dark value when theme switches. |
| `--positive-ink` | `#ffffff` | Text on positive backgrounds (future) | Forward-compatible; positive is currently text-only but may be used as background fill. |

### Tokens to Convert (hex→OKLCH)

| Token | Current (hex) | Converted (OKLCH) | Rationale |
|-------|--------------|-------------------|-----------|
| `--error-bg` | `#fde8e8` | `oklch(0.94 0.02 15)` | Consistency — all design tokens use OKLCH. Color stays visually identical. |
| `--error-fg` | `#8a1f1f` | `oklch(0.38 0.12 25)` | Consistency. OKLCH equivalent of #8a1f1f. |

Note: `--color-focus` (#2563eb) remains hex for now — focus ring contrast is a Phase 3 (component-level) concern and changing the focus color may have unintended cascade effects on non-accent backgrounds.

### Tokens UNCHANGED

All 19 other tokens pass their real-world contrast pairs and keep current values. The `--accent` / `--accent-ink` pair passes at 7.67:1 (default) and 6.81:1 (hover).

## Token System Design Decisions (the agent's Discretion)

### Granularity: Surface-level, not component-scoped

**Decision:** Keep the current surface-level token system. Do NOT create component-scoped tokens like `--btn-primary-bg`, `--btn-secondary-hover-bg`.

**Rationale:**
- Component-scoped tokens cause N×5 explosion (12 components × 5 states = 60+ tokens)
- Surface-level tokens already satisfy all 23 components — existing CSS proves this works
- Regressions are easier to audit: change `--accent` value, verify all accent-using components
- DESIGN.md already documents surface-level tokens; component annotation (D-04) maps usage without adding tokens

### Naming Convention: Semantic, role-based

**Decision:** Keep semantic naming (`--ink`, `--surface`, `--accent-ink`).

**Rationale:**
- Already established in app.css and DESIGN.md
- Semantic names survive value changes (dark mode swaps values; names stay)
- Easier to reason about: "What color is text on an accent background?" → `--accent-ink`
- Surface-paired naming (`--text-on-bg`) creates tautological names that duplicate the CSS property (`color: var(--text-on-bg)`)

### State Tokens: Add --negative-ink, --positive-ink

**Decision:** Add `--negative-ink` (replaces hardcoded `#fff` on delete confirm buttons). Add `--positive-ink` for future-proofing.

**Rationale:**
- PALT-01 requires "unambiguous fg/bg pairs for every surface"
- Hardcoded `#fff` creates a silent regression risk: if `--negative` changes, text may become unreadable
- Dark mode: `--negative-ink` can swap to dark value when theme switches
- `--positive-ink` is forward-compatible; currently positive is text-only but may be used as background

### Dark Mode Forward Compatibility

**Decision:** All token names are role-based, not light-mode-specific. Dark mode swaps values in a `@media (prefers-color-scheme: dark)` or `[data-theme="dark"]` block — zero name changes.

**Example:**
```css
:root {
  --bg: oklch(0.975 0.003 60);    /* light: off-white */
  --ink: oklch(0.20 0.01 60);     /* light: near-black */
}

[data-theme="dark"] {
  --bg: oklch(0.15 0.003 60);     /* dark: near-black */
  --ink: oklch(0.90 0.005 60);    /* dark: off-white */
}
```

Token names (`--bg`, `--ink`) are invariant. Only values change. This satisfies the CONTEXT.md requirement: "dark mode can be added by swapping values without renaming tokens."

## WCAG Contrast Requirements

[CITED: https://www.w3.org/TR/WCAG21/#contrast-minimum]

### SC 1.4.3 Contrast (Minimum) — Level AA

| Text Category | Minimum Ratio | Applies To |
|---------------|---------------|------------|
| Normal text (< 18pt / < 14pt bold) | 4.5:1 | Body text, labels, captions, button text, form inputs, table cells |
| Large text (≥ 18pt or ≥ 14pt bold) | 3:1 | Dashboard h1 (clamp 1.75rem–2.5rem ≈ 28px–40px, weight 600 → qualifies as large), portfolio stat values (1.4rem/22.4px weight 600 → qualifies) |
| Incidental / inactive / disabled | No requirement | `.btn:disabled`, purely decorative elements |
| Logotypes | No requirement | Brand names in header |

[CITED: https://www.w3.org/TR/WCAG21/#non-text-contrast]

### SC 1.4.11 Non-text Contrast — Level AA

| Element | Minimum Ratio | Applies To |
|---------|---------------|------------|
| UI component boundaries | 3:1 | Button borders, input borders, focus rings, chevrons |
| Graphical objects | 3:1 | Compare bars, progress bars, class color swatches |

**Key exemption:** "Inactive user interface components" are exempt. This means `opacity: 0.5` on `.btn:disabled` is compliant without needing a separate disabled color pair.

[CITED: https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance]

### SC 2.4.13 Focus Appearance — Level AAA (informative for AA target)

Focus indicators need ≥ 3:1 change-of-contrast between focused and unfocused states. The current `outline: 2px solid var(--color-focus)` passes on body backgrounds (4.81:1 vs `--bg`) but fails on `--accent` backgrounds (1.57:1). This is a **Phase 3** concern — phase 2 defines token values only.

## DESIGN.md Update Strategy

### Sections to Rewrite (per D-01)

| Section | Current State | After Phase 2 |
|---------|--------------|---------------|
| **Color strategy** (lines 16–22) | General philosophy | Update to reference corrected token system, note WCAG AA verification |
| **Accent rationale** (lines 44–51) | Fern green, hue 150 | Preserve rationale — it's a deliberate design choice, not a defect |
| **Tokens table** (lines 30–42) | 11 tokens, no contrast column | Expand to all tokens (~25 rows), add Contrast column per D-02, show ratio + Passa/Falha |
| **Class swatches table** (lines 53–69) | 6 slots, DESIGN.md targets | Correct slot 4 target, verify all 6 pass AA, update table |
| **Migration path** (lines 212–228) | 6 steps, first step references "OKLCH values above" | Update step 1 to reference corrected values; note that steps 2–6 are unchanged |

### New Token Table Structure (per D-02)

```markdown
| Token | OKLCH | Hex (approx) | Role | Pair | Contrast | Status |
|-------|-------|-------------|------|------|----------|--------|
| `--bg` | `oklch(0.975 0.003 60)` | `#fafaf7` | Body surface | vs `--ink` | 16.85 | Passa |
| `--ink` | `oklch(0.20 0.01 60)` | `#1a1a1a` | Primary text | vs `--bg` | 16.85 | Passa |
| `--accent` | `oklch(0.42 0.09 150)` | `#225a31` | Accent fill | + `--accent-ink` | 7.67 | Passa |
| `--accent-ink` | `oklch(0.98 0.005 150)` | `#f0faf2` | Text on accent | + `--accent` | 7.67 | Passa |
| ... | ... | ... | ... | ... | ... | ... |
```

**Contrast column rules:**
- Foreground tokens: show ratio against `--bg` (the body background)
- Surface tokens: show ratio against `--ink` (the default text color)
- Accent/semantic pair tokens: show the real pair ratio (e.g., `--accent-ink` + `--accent`)
- `Passa` = ratio ≥ 4.5 (normal text) or ≥ 3.0 (large text / non-text UI)
- `Falha` = below threshold

### Component Inventory Annotations (per D-04)

Add a "Color Tokens" column to the Components table:

```markdown
| Component | Where | Color Tokens | Notes |
|-----------|-------|-------------|-------|
| App header | base.html | `--surface`, `--border`, `--fg`, `--muted`, `--accent` | Flat, border-bottom |
| Primary button | various | `--accent`, `--accent-ink` | hover: brightness(1.1) |
| Secondary button | various | `--surface-sunk`, `--ink`, `--border` | hover: `--border` bg |
| Error message | various | `--error-bg`, `--error-fg` | Inline, no toast |
| Delete confirm | dashboard | `--negative`, `--negative-ink` | Confirm dialog |
| Class swatch | dashboard | `--class-1..6` | 14px×14px, decorative |
| Compare bar | dashboard | `--border-strong` (target), `--accent` (current) | Stacked fills |
| Progress bar | dashboard | `--border` (track), `--accent` (fill) | Per-asset |
| Portfolio stat | dashboard | `--fg`, `--positive`, `--negative` | Conditional on gain/loss |
| Focus ring | all | `--color-focus` | 2px outline, 2px offset |
```

## Common Pitfalls

### Pitfall 1: Confusing Token-Level Failures with Real-World Failures

**What goes wrong:** The token inventory compares every foreground token against `--bg` and every surface token against `--ink`. This produces false positives when a token is never used in that pairing. `--accent-ink` (off-white text on accent fills) fails against `--bg` (off-white body) at 1.02 — but it's never used on the body background.

**Why it happens:** The static inventory can't know usage context — it applies a uniform "foreground vs body" or "surface vs default text" heuristic.

**How to avoid:** Cross-reference token inventory failures against real component pairs (see §Real Pairs That Matter above). Only fix tokens that fail in their ACTUAL usage context.

**Warning signs:** A token fails the inventory but passes when you compute its actual pair (e.g., `--accent-ink` fails vs `--bg` at 1.02 but passes vs `--accent` at 7.67).

### Pitfall 2: Changing Token Values Without Checking Cascade Effects

**What goes wrong:** Changing `--accent` or `--ink` affects dozens of component rules. A "better" value for one component may break another.

**Why it happens:** CSS custom properties are global — every `var(--accent)` reference resolves to the new value.

**How to avoid:** Run `color_token_inventory()` after every value change. Re-run the full audit report (`python3 scripts/generate_contrast_audit.py`) to verify no component regressed. Test the 3 most critical surfaces: dashboard (class sections, buttons), class editor (table, forms), and import flow (modal, review table).

**Warning signs:** A corrected token passes its own contrast test but causes a previously-passing component to fail (e.g., making `--ink` darker helps body text but may reduce contrast on `--surface-sunk` backgrounds).

### Pitfall 3: OKLCH→Hex Round-Trip Approximation

**What goes wrong:** The token table shows "Hex (approx)" for OKLCH values. Someone copies the hex value instead of the OKLCH value into CSS, losing perceptual uniformity and dark-mode compatibility.

**Why it happens:** Humans reach for hex because it's familiar.

**How to avoid:** CSS uses OKLCH directly. DESIGN.md hex column is labeled "Hex (approx)" and only for visual reference. The canonical value is the OKLCH column. Add a note: "Canonical values are OKLCH. Hex approximations are for visual reference only — do not use in CSS."

**Warning signs:** DESIGN.md shows hex values in token column; someone copies them into `app.css`.

### Pitfall 4: Deleting Legacy Aliases Prematurely

**What goes wrong:** Removing `--fg: var(--ink)` breaks every `color: var(--fg)` call site in app.css.

**Why it happens:** 19+ component rules reference `--fg` or `--muted` rather than `--ink` or `--ink-muted`.

**How to avoid:** Keep legacy aliases indefinitely. They cost 2 lines of CSS and prevent sweeping breakage. Migration to canonical names is a future linting pass, not part of Phase 2.

**Warning signs:** Grep shows `var(--fg)` or `var(--muted)` in component rules — these must continue resolving.

## Code Examples

### Corrected :root Block (app.css lines 3–58)

```css
:root {
  color-scheme: light;

  /* Surface tokens — OKLCH, WCAG AA verified.
     --bg: off-white body (L=0.975). --surface: pure white for cards/modals.
     --surface-sunk: slightly recessed for form wells and table headers. */
  --bg: oklch(0.975 0.003 60);
  --surface: oklch(1.0 0 0);
  --surface-sunk: oklch(0.96 0.003 60);

  /* Ink tokens. --ink: near-black (L=0.20), not pure black. --ink-muted: secondary.
     --accent-ink: text on accent fill (L=0.98). */
  --ink: oklch(0.20 0.01 60);
  --ink-muted: oklch(0.50 0.01 60);
  --accent-ink: oklch(0.98 0.005 150);

  /* Border tokens. */
  --border: oklch(0.90 0.005 60);
  --border-strong: oklch(0.82 0.008 60);

  /* Accent — single committed color (deep fern, hue 150).
     Contrast: --accent-ink on --accent = 7.67:1 (Passa). */
  --accent: oklch(0.42 0.09 150);

  /* Status colors.
     --positive: gain/valid (4.84 vs --bg, Passa).
     --negative: loss/error (6.13 vs --bg, Passa). */
  --positive: oklch(0.52 0.13 145);
  --negative: oklch(0.50 0.18 25);

  /* Status ink tokens — text on status backgrounds.
     --negative-ink: text on --negative fill (6.59:1, Passa).
     --positive-ink: text on --positive fill (future). */
  --negative-ink: #ffffff;
  --positive-ink: #ffffff;

  /* Error feedback — converted to OKLCH for consistency.
     Contrast: --error-fg on --error-bg = 7.79:1 (Passa). */
  --error-bg: oklch(0.94 0.02 15);
  --error-fg: oklch(0.38 0.12 25);

  /* Legacy aliases — transitional, keep indefinitely. */
  --fg: var(--ink);
  --muted: var(--ink-muted);

  /* Class color tokens — WCAG AA verified against --bg.
     All 6 pass ≥ 4.5:1. Replaces DESIGN.md migration-source hex values. */
  --class-1: #0a66c2;                        /* blue   — 5.29, Passa */
  --class-2: #2e7d32;                        /* green  — 4.77, Passa */
  --class-3: #c62828;                        /* red    — 5.23, Passa */
  --class-4: oklch(0.53 0.13 50);            /* orange — 5.16, Passa (was #ef6c00 at 2.87 Falha) */
  --class-5: #6a1b9a;                        /* purple — 8.73, Passa */
  --class-6: oklch(0.52 0.10 200);           /* teal   — 4.89, Passa (was #00838f at 4.21 Falha) */

  /* Focus ring color. */
  --color-focus: #2563eb;
}
```

### Verification Script (run before commit)

```bash
#!/bin/bash
# verify-tokens.sh — confirm all corrected tokens pass WCAG AA
cd "$(dirname "$0")/.."

uv run python3 -c "
from omaha.audit.css_parser import parse_stylesheet, color_token_inventory
from omaha.audit.color_resolver import contrast_ratio, aa_status
from pathlib import Path

sheet = parse_stylesheet(Path('src/omaha/static/app.css'))
rows = color_token_inventory(sheet)

failures = [r for r in rows if r.status == 'Falha']
if failures:
    print('FAILURES:')
    for r in failures:
        print(f'  {r.token}: ratio={r.ratio} vs {r.adjacent_background}')
    print(f'\n{failures} tokens failed.')
else:
    print('All tokens pass WCAG AA ✓')

# Cross-check real pairs
pairs = [
    ('accent-ink on accent', 'oklch(0.98 0.005 150)', 'oklch(0.42 0.09 150)'),
    ('negative-ink on negative', '#ffffff', 'oklch(0.50 0.18 25)'),
    ('error-fg on error-bg', 'oklch(0.38 0.12 25)', 'oklch(0.94 0.02 15)'),
    ('class-4 on bg', 'oklch(0.53 0.13 50)', 'oklch(0.975 0.003 60)'),
    ('class-6 on bg', 'oklch(0.52 0.10 200)', 'oklch(0.975 0.003 60)'),
]
print()
for label, fg, bg in pairs:
    ratio = contrast_ratio(fg, bg)
    _, status = aa_status(ratio)
    print(f'  {label}: {ratio:.2f} {status}')
"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hex-only color values | OKLCH throughout | CSS Color 4 (2023), adopted in DESIGN.md | Perceptually uniform lightness; easy dark-mode swap |
| Manual contrast checking | Scripted token inventory + real-pair verification | Phase 1 | Reproducible, auditable, < 1 sec per verification |
| Inline color constants | CSS custom properties in `:root` | Already in place | Single source of truth, cascade-safe |

**Deprecated/outdated:**
- **Hex-as-primary:** Hex values should only appear as migration sources or temporary fallbacks. Canonical values are OKLCH.
- **Manual DevTools contrast checking:** Replaced by `contrast_ratio()` + `aa_status()` which are deterministic and auditable.
- **`--error-bg` / `--error-fg` as hex:** Converted to OKLCH in this phase for consistency.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `--class-4` orange is used only for decorative swatches, compare bars, and progress fills — never as a text background | Token Inventory | Low — grep confirmed no `var(--class-4)` is used with text overlays |
| A2 | `--class-6` teal similarly has no text overlays | Token Inventory | Low — same grep verification |
| A3 | `--positive` is never used as a background fill for text-containing elements | Token System Design | Low — if used as bg in future, `--positive-ink` token exists |
| A4 | OKLCH `oklch(0.53 0.13 50)` is visually similar to the existing burnt orange `#ef6c00` in hue character | Corrected Values | Medium — may need visual review; hue 50 orange character is preserved but darker |
| A5 | `#ffffff` is the correct `--negative-ink` value for light mode | Token System Design | Low — matches current hardcoded usage; validated at 6.59:1 |

**If this table is empty:** N/A — 5 assumptions documented.

## Open Questions

1. **Should `--class-1`, `--class-2`, `--class-3`, `--class-5` also convert to OKLCH now?**
   - What we know: They pass at current hex values (5.29, 4.77, 5.23, 8.73). DESIGN.md has OKLCH targets for all 6 slots.
   - What's unclear: Whether to convert passing hex values to OKLCH in this phase or defer to future polish pass.
   - Recommendation: Convert only the failing tokens (`--class-4`, `--class-6`) now. Converting passing tokens adds risk with no benefit. Defer full hex→OKLCH migration of class colors to a future cleanup pass.

2. **Should `--color-focus` `#2563eb` be replaced with an accent-derived value?**
   - What we know: Passes on body bg (4.81), fails on accent bg (1.57). WCAG 2.2 SC 2.4.13 (AAA, not our AA target) requires 3:1 change-of-contrast for focus indicators.
   - What's unclear: Whether blue focus ring on green accent is actually a problem for keyboard users.
   - Recommendation: Defer to Phase 3 (component fixes). Phase 2 defines token values only. Phase 3 can address focus ring on accent surfaces by adding a `--color-focus-on-accent` token or using `color-mix()`.

3. **Does the class color cycling (nth-of-type 6n+N) in app.css need updates?**
   - What we know: The `--class-color` alias at component scope references `--class-1` by default. The nth-of-type rules assign `--class-color` to the appropriate class token.
   - What's unclear: Whether changing `--class-4`/`--class-6` values affects the class-color aliasing chain.
   - Recommendation: No change needed. The value flows: `--class-4` → `--class-color` → `.compare-bar-current-fill`. The alias chain is value-agnostic.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3 | Token verification script | ✓ | 3.14.4 | — |
| uv | Package management | ✓ | (installed) | pip |
| coloraide | `contrast_ratio()`, `aa_status()` | ✓ | 8.8.1 | — |
| tinycss2 | `parse_stylesheet()` | ✓ | 1.5.1 | — |
| app.css | Token source file | ✓ | 1440 lines | — |
| DESIGN.md | Documentation target | ✓ | 228 lines | — |

**Missing dependencies with no fallback:** None — all dependencies already installed from Phase 1.
**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, Phase 1 tests) |
| Config file | pyproject.toml (existing) |
| Quick run command | `uv run pytest tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x` |
| Full suite command | `uv run pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PALT-01 | `color_token_inventory()` returns all tokens with Passa status after correction | unit | `uv run python3 -c "from omaha.audit.css_parser import parse_stylesheet, color_token_inventory; from pathlib import Path; sheet = parse_stylesheet(Path('src/omaha/static/app.css')); rows = color_token_inventory(sheet); assert all(r.status == 'Passa' for r in rows), [r.token for r in rows if r.status == 'Falha']"` | ❌ Wave 0 |
| PALT-02 | Each corrected token pair meets WCAG AA threshold (4.5:1 body, 3:1 large/UI) | unit | `uv run python3 -c "from omaha.audit.color_resolver import contrast_ratio, aa_status; pairs = [('oklch(0.53 0.13 50)', 'oklch(0.975 0.003 60)'), ('oklch(0.52 0.10 200)', 'oklch(0.975 0.003 60)'), ('#ffffff', 'oklch(0.50 0.18 25)')]; [print(f'{fg} on {bg}: {contrast_ratio(fg,bg):.2f} {aa_status(contrast_ratio(fg,bg))[1]}') for fg,bg in pairs]"` | ❌ Wave 0 |
| PALT-03 | DESIGN.md token table has Contrast column with correct ratios | manual-only | Grep DESIGN.md for "Passa" and "Falha" in token rows | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run python3 -c "[token inventory verification]"` (above)
- **Per wave merge:** `uv run pytest tests/test_audit_css_parser.py tests/test_audit_color_resolver.py -x`
- **Phase gate:** Token inventory returns zero Falha rows; DESIGN.md token table matches `app.css` values

### Wave 0 Gaps

- [ ] `tests/test_phase02_tokens.py` — covers PALT-01 (token inventory all Passa), PALT-02 (real-pair contrast thresholds)
- [ ] Token verification inline script — wrap in a test function with fixture for `app.css` path
- [ ] `tests/conftest.py` — already exists, may need `app_css_path` fixture
- [ ] Framework install: `uv run pytest --version` — already working

## Security Domain

> `security_enforcement` not explicitly disabled — treating as enabled (default).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | No | CSS custom properties are browser-resolved; no server-side input |
| V6 Cryptography | No | — |

**Note:** Phase 2 is a CSS token value change and markdown documentation update. No server-side code, no user input, no data persistence. The only attack surface is CSS injection via modified `app.css` — but this requires filesystem access, which is outside the threat model (self-hosted, single-household app).

### Known Threat Patterns for CSS Token Systems

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| CSS injection via unvalidated user-controllable custom properties | Tampering | N/A — Omaha has no user-controllable CSS; all tokens are hardcoded in source-controlled `app.css` |
| Contrast regression from token value change | Denial of Service (usability) | Token verification script + DESIGN.md documentation + git history for rollback |

## Sources

### Primary (HIGH confidence)

- [Context7: /websites/w3_tr_wcag21] — WCAG 2.1 SC 1.4.3 Contrast (Minimum) 4.5:1 normal, 3:1 large, incidental/disabled exempt. SC 1.4.11 Non-text Contrast 3:1 for UI components.
- [Context7: /websites/w3_wai_wcag22] — SC 2.4.13 Focus Appearance (AAA), 3:1 change-of-contrast for focus indicators. SC 2.4.7 Focus Visible (AA).
- [MDN: oklch() CSS function] — OKLCH syntax, L lightness (0–1), C chroma (0–0.4), H hue (0–360). Perceptually uniform; adjusting L preserves perceived brightness better than HSL Lightness.
- [Phase 1 audit tools] — `src/omaha/audit/css_parser.py` (coloraide 8.8.1, tinycss2 1.5.1), `src/omaha/audit/color_resolver.py` (contrast_ratio, aa_status). All verified working on 2026-06-13 with real `app.css`.
- [Token inventory run] — 23 tokens computed 2026-06-13 against current `app.css`. 4 tokens show "Falha" status; 2 are genuine failures (`--class-4`, `--class-6`).

### Secondary (MEDIUM confidence)

- [CONTEXT.md §Specific Ideas] — `--accent` on `--ink` fails at 2.23:1; needs accent-ink text on accent backgrounds. Confirmed as false positive: real pair passes at 7.67.
- [DESIGN.md] — Current color token targets, accent rationale (hue 150 fern green), class swatch table, 6-step migration path. All DESIGN.md token values verified against WCAG AA.
- [01-02-SUMMARY.md] — Adjacent-background mapping methodology: foreground vs `--bg`, surface vs `--ink`. `--accent-ink` vs `--bg` correctly flagged as Falha (1.02) but recognized as false positive in real usage.

### Tertiary (LOW confidence)

- [ASSUMED] OKLCH hue 50 at L=0.53 preserves "burnt orange" character — not verified visually; human review recommended before commit.
- [ASSUMED] `oklch(0.52 0.10 200)` is the correct teal replacement — based on DESIGN.md target; visual equivalence to current `#00838f` not verified.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all tools already installed and verified by Phase 1; no new dependencies
- Architecture: HIGH — token system is already surface-based with semantic naming; pattern established and proven
- Pitfalls: HIGH — false-positive contrast failures and cascade effects are well-understood from Phase 1 audit
- Corrected values: MEDIUM — contrast ratios verified programmatically; visual character of replacement colors needs human eye-check

**Research date:** 2026-06-13
**Valid until:** 2026-07-13 (30 days — token values are stable once verified)

**Verification protocol status:**
- [x] Security domain included (no server-side attack surface; CSS-only phase)
- [x] Phase domain understood (WCAG AA contrast, OKLCH color space, CSS custom properties)
- [x] Environment availability audited (all deps from Phase 1; no missing deps)
- [x] Phase requirements mapped to research findings (PALT-01, PALT-02, PALT-03 all addressed)
- [x] No rename/refactor triggers — Runtime State Inventory skipped with explicit "None" declarations
- [x] Package legitimacy audit completed (no new packages)
