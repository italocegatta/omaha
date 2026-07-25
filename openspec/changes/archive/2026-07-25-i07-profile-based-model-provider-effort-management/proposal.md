## Why

Agent model configuration is hardcoded in `opencode.json` and the roadmap
agent's routing table. Switching providers or models requires manual file
edits, which is error-prone and prevents quick A/B testing of model
quality vs cost. A profile system lets the user select a named
(provider, model, effort) configuration per agent role via a single
taskipy command, with each terminal session running its own profile
independently.

## What Changes

- New taskipy task `oc` (or `oc-profile`) that launches an OpenCode
  session with a named profile selected.
- Profile resolution script (`scripts/oc_profile.py`) that reads a
  profile name, resolves (provider, model, effort) per agent role, and
  exports environment variables before exec'ing OpenCode.
- Four built-in profiles: `openai-cheap`, `openai-balanced`,
  `openai-xiaomi-balanced`, `xiaomi-balanced`.
- Clean seam for future TOML profile file (`profiles.toml`) — script
  reads it if present, falls back to built-in defaults.
- Documentation in AGENTS.md (or new `docs/agent-profiles.md`) covering
  day-to-day usage: how to switch profiles, how to run multiple sessions
  with different profiles, how the resolution chain works.
- `opencode.json` modified to read model from environment variables
  where possible, or the launcher generates a session-local override.

No production code change. Dev tooling only.

## Capabilities

### New Capabilities

- `agent-profile-launcher`: Profile-based model/provider/effort
  management for OpenCode agent sessions. Covers profile selection,
  environment variable export, resolution chain (TOML → env → built-in),
  and multi-session isolation.

### Modified Capabilities

(none — no existing spec behavior changes)

## Impact

- `pyproject.toml`: new taskipy task entry.
- `scripts/oc_profile.py`: new launcher script.
- `opencode.json`: may add env-var interpolation support or document
  that launcher generates session-local config.
- `AGENTS.md` or new doc: profile usage documentation.
- No impact on omaha application code, tests, or runtime behavior.
