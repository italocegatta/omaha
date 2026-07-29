---
description: Orchestrate OpenSpec roadmap workflow — decompose demand into slices and route through propose → apply → review → finalize
---

When the user types `/roadmap <demanda>`, invoke the roadmap agent.

**Input:** The argument after `/roadmap` is the user's demand — a feature request, bug report, or change they want to make. Pass it verbatim as the prompt to the roadmap agent.

**Steps:**

1. The roadmap agent is defined at `.commandcode/agents/roadmap.md`. It reads the roadmap file, delegates decomposition to the `slice` subagent, then routes each slice through `propose` → `apply` → `review` → `finalize`.

2. Call `agent(subagent_type: "roadmap", prompt: "<demanda>")`.

3. The roadmap agent runs autonomously. When it returns, report the results to the user — what was done, what slices were completed, what's pending.

**Guardrails:**
- Pass the user's demand exactly as given, with no editing or rephrasing
- Do NOT attempt to implement anything yourself — the roadmap agent handles everything via its subagents
- Do NOT call `agent()` with `run_in_background: true` — the user needs to see progress in real time
