## Context

Rebalance page already renders class summary cards in `_rebalance_plan.html`, with card-level state coming from the current deviation sign. Current CSS gives cards a shared base, but the visual result still reads as lightly varied panels instead of one coherent family.

Scope stays inside rebalance page template + `app.css`. No data, route, or solver changes.

## Goals / Non-Goals

**Goals:**
- Make rebalance class cards read as one card family.
- Encode target relationship with clear positive/negative color cues.
- Remove redundant header label text and keep hierarchy on class name + metrics.

**Non-Goals:**
- Change rebalance calculations or route contract.
- Add new UI surfaces or additional card types.
- Introduce per-user customization for card colors.

## Decisions

1. **Use one shared base card pattern with state modifiers**
   - Keep a single `.rebalance-class-card` shell and vary only accent treatment for above/below target.
   - Rationale: preserves family resemblance while still making state obvious.
   - Alternatives considered: separate card molds per state (too fragmented); inline per-card styles (harder to keep coherent).

2. **Keep state cues subtle, not full-surface swaps**
   - Use border / tint / accent hierarchy rather than radically different fills.
   - Rationale: cards should feel related, not like separate alert widgets.
   - Alternatives considered: full green/red surfaces (too loud and fights legibility); monochrome cards with only text color (too weak).

3. **Remove kicker label `CLASSE` from card header**
   - Class name becomes primary header text.
   - Rationale: label repeats what the surrounding section already implies and adds visual noise.
   - Alternatives considered: keep kicker for structure (rejected because it makes every card look more templated).

4. **Keep accent source tied to existing deviation state**
   - Above-target cards stay mapped to positive state; below-target cards stay mapped to negative state.
   - Rationale: no new data contract required, and current state semantics already exist.
   - Alternatives considered: introduce new semantic states per target band (unnecessary for this slice).

## Risks / Trade-offs

- [Accent too strong] → Mitigate with restrained tint/border changes and preserve current typography.
- [Cards still feel templated] → Mitigate by tuning spacing, header hierarchy, and metric grouping together.
- [Color-only cue may be missed] → Keep class name, metric layout, and projected row unchanged so meaning remains readable without color.

## Migration Plan

- Update template markup and CSS in one pass.
- Verify rendered cards on populated rebalance page and confirm empty-state/plan behavior unchanged.
- Rollback is trivial: revert template/CSS change only; no schema or data migration.

## Open Questions

- Exact accent intensity: should positive/negative treatment stay close to current palette tokens or get a slightly softer tint for better family resemblance?
