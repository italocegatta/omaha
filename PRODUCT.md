# Product

## Register

product

## Users

Two people — Italo and Ana Livia — tracking the family's investment portfolio
together. Both are non-professional, non-expert investors who already understand
the basics: classes (Renda Fixa, Acoes, FIIs), target allocations, brokers, CSV
statements, gain/loss math. They are not learning investing through this tool;
they are using it to *see* what they already hold and where it is drifting.

Italo is the operator. He runs the imports, edits classes and assets, manages
the SQLite backup cycle, and handles the nginx/cert renewals. He treats the app
the way he treats a personal finance spreadsheet: useful when it is accurate,
ignored when it is wrong. Ana Livia is a viewer — she signs in to check the
current distribution and the gain, not to manage state.

Usage context: a single household, on a self-hosted machine, accessed from
laptops and phones on the home network. The dev server is bound to 0.0.0.0
because the client is never localhost. There is no multi-tenant traffic, no
load, no public visitors. Speed and correctness matter; the page can be small,
the page does not need to scale.

The product is not for sale. There is no marketing surface, no onboarding
funnel, no free tier. It exists because the family wants a private ledger
that they own, with a CSV import from their broker, and a distribution view
that shows drift from target.

## Product Purpose

Omaha is a self-hosted family portfolio ledger. It does five things and only
those five:

1. Stores a profile's holdings (assets → positions) against user-defined
   classes with target percentage allocations.
2. Imports broker CSV statements and matches them to known assets, surfacing
   the unmatched rows for manual class assignment before committing.
3. Renders the current distribution by class, the target-vs-current compare
   bar, and the per-asset progress fill — the three reads the family actually
   wants.
4. Validates class percentage totals before save (must sum to 100), preventing
   the drift that an unvalidated editor would allow.
5. Authenticates with a shared family password; per-profile data isolation
   keeps Italo's positions and Ana's positions separated.

Success means the family opens the app, sees where the portfolio is, trusts
the numbers, and closes the tab. Anything that gets in the way of that single
loop is a defect.

## Brand Personality

**Domestic. Personal. Lived-in.**

The app should feel like a private notebook on a desk, not a tool issued by
a vendor. Not "premium" (no oxblood, no gold accents, no family-office
typography). Not "playful" (no illustrations, no mascot, no pastel). Closer
to a well-used Moleskine than to a fintech app: confident about the data,
quiet about itself, the kind of thing you stop noticing once it is on
screen — which is exactly the goal.

The two named profiles ("Italo", "Ana Livia") should read as the people they
are, not as rows in a table. The dashboard is a household view, not a
portfolio dashboard. The empty state when Ana Livia has no positions is not
a "Get started" screen; it is a quiet line that says the account exists and
nothing is in it yet.

Voice: third-person, matter-of-fact, Portuguese (PT-BR). No exclamation
points. No "Welcome back!". No marketing copy anywhere in the product.

## Anti-references

- **Bloomberg terminal** — dense, dark, monospaced, alarmist. We are a quiet
  household ledger, not a trading floor.
- **Generic SaaS dashboard** — card-grid-of-card-grids, gradient hero,
  eyebrow-above-every-section, "All your work in one place" copy. The skill
  calls this AI-default; we treat it as anti-default too.
- **Family-office luxury branding** — oxblood and gold, serif display,
  crme-anne color, the visual grammar of "we manage generational wealth".
  We are two people tracking their own savings; that posture would be
  embarrassing.
- **Crypto dashboard neon** — black + green/red price tickers, glow, dense
  sparklines. Wrong genre entirely.
- **The cream / sand / beige body-bg default** — `#fafaf7` and its cousins
  are the saturated AI scaffold of the moment. We do not use a tinted-warm
  body. Warmth, when it appears, lives in accent, in a small amount of
  visible texture or grain on a surface, and in typography — never in the
  background tint.

## Design Principles

1. **Show, do not label.** Numbers, percentages, bars, and class swatches
   carry the information. The chrome around them should be invisible. If a
   label is required to explain the data, the data shape is wrong; rewrite
   the data shape.
2. **The dashboard is the product.** Login, profile picker, classes editor,
   assets editor, import flow, and review flow all exist to feed the
   distribution view. They can be functional and unlovely; the dashboard
   cannot. Design effort goes where the family looks.
3. **Warmth lives in detail, not in tint.** Body background is a true
   neutral (or a barely-tinted neutral toward the brand's own hue, *not*
   toward warm-by-default). The lived-in feeling comes from a single
   considered accent, type choices that feel like a magazine, generous
   spacing on the dashboard, and a couple of intentional micro-interactions
   (e.g. the compare-bar filling, the per-asset progress bar settling).
4. **Two profiles, two slightly different views.** The data is per-profile,
   isolated, and the chrome should acknowledge that. The current profile
   name appears near the page title, not buried in a menu.
5. **Conservative on motion.** Transitions are short and serve a reading
   purpose (state change, completion of an action). No bounce, no elastic,
   no decorative parallax. Reduced-motion is a hard requirement, not a
   fallback.

## Accessibility & Inclusion

- WCAG 2.1 AA target. Body text contrast ≥ 4.5:1 against its background;
  large text ≥ 3:1. The single most common failure in the current CSS is
  muted gray body text on a tinted near-white; that combination will not
  appear in the polished design.
- Keyboard navigation through every interactive control, in a sensible
  order. The class editor, asset editor, and import review flow are
  form-heavy and must be tabbable end-to-end.
- `prefers-reduced-motion: reduce` is honored. Every animation has a
  crossfade or instant fallback.
- No information conveyed by color alone. The compare bar uses
  position + fill; the per-asset progress bar uses fill; class swatches
  are paired with class names; the gain value pairs color with a sign
  (`+` / `-`) and the word "gain".
- PT-BR is the working language of the UI. All user-visible strings in
  templates are Portuguese. English may appear in code, comments, and the
  README.
