# 2.2 Planning notes for S03/T05 /assets retirement

## Resolves: design §OQ1

## Search
```
grep -rln "T05\|/assets.*redirect\|retired" .planning/
```

## Results

`.planning/MILESTONES.md`:
- Line 13: `Class collapse/expand, inline class CRUD, retired \`/classes\` route.`
- Line 14: `Asset inline create/delete, retired \`/assets\` route.`
- Line 15: `Import modal two-step flow, retired \`/import\` route.`

`.planning/STATE.md:43`:
- `Import modal + retired \`/import\` route.`

No other planning docs reference S03/T05 or /assets retirement
explicitly. The retirement is recorded as a one-line milestone
achievement; the operational details (which tests pin the 302
contract, which route handlers remain) live in the test
docstrings and the route's own module docstring.

## Decision input
MILESTONES.md confirms: `/assets` route was retired by S03.
The retire test docstring (test_s03_t05_assets_retire.py)
describes the same contract. Two independent sources agree.

This pins the direction for §3.3: **code edit** (retire GET /assets
→ 302 redirect to `/`).