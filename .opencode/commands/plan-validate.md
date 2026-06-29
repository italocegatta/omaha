---
description: Drift check — reconcile the plan's checkboxes against real change state
---

Validate the **Plan** against reality. Follow the **validate** procedure in the
`plan-workflow` skill. Report mismatches; fix only what the user approves. Check:

- every `Carried by: <name>` resolves to a real change (active or archived);
- every `[x]` phase's change is archived (not still active);
- every archived change is reflected by a done (`[x]`) phase (no silent drift);
- sources-of-truth links resolve.

## Active plan

```bash
test -f PLAN.md && cat PLAN.md || echo "No PLAN.md found. Run /plan-create to start one."
```

## Change engine state (OpenSpec)

```bash
openspec list --json 2>/dev/null || echo "(openspec not available)"
```

## Change directories

```bash
echo "--- active change dirs ---"
ls openspec/changes 2>/dev/null | grep -v '^archive$' || true
echo "--- archived change dirs ---"
ls openspec/changes/archive 2>/dev/null || true
```