---
description: Run roadmap orchestration from command line style entrypoint.
agent: roadmap
---

Use `@roadmap` orchestration flow for this request.

User request:

`$ARGUMENTS`

Rules:
- Keep this session as monitor only.
- Use provider-specific subagents for each lifecycle gate.
- If primary provider fails, hand off to secondary provider.
- Report concise step-by-step progress back here.
