## Context

Current state: `opencode.json` hardcodes model per agent role. The roadmap
agent's `roadmap.md` has a separate model assignment table. Switching
models requires manual edits to both files. No mechanism exists to run
different model configurations in parallel terminal sessions.

The omaha repo uses OpenCode as its AI coding agent framework. Agent
roles: `roadmap` (primary), `propose`, `apply`, `explore`, `slice`
(subagents using xiaomi-pro), `review`, `finalize` (subagents using
xiaomi base). OpenAI `gpt-5.4-mini` is used only for `roadmap`.

Taskipy is the canonical task runner (`uv run task <name>`).

## Goals / Non-Goals

**Goals:**
- Single command to launch OpenCode with a named profile.
- Profile defines (provider, model, effort) per agent role.
- Multiple terminals can run different profiles simultaneously.
- Clean seam for TOML profile file — works without it (built-in
  defaults), enhances with it.
- Day-to-day switching is documented clearly.

**Non-Goals:**
- Modifying OpenCode source code or config format.
- Runtime profile switching (restart required).
- Profile inheritance or composition.
- GUI/CLI profile selector beyond taskipy task.
- Changing which roles exist or their responsibilities.

## Decisions

### D1: Launcher script (`scripts/oc_profile.py`) + taskipy task

**Decision**: A Python script resolves the profile and exports env vars,
then `execv`s into OpenCode. Taskipy task `oc` wraps it.

**Why**: Taskipy is the canonical runner (PRD §4.8). Python script keeps
logic testable and avoids shell quoting issues. `execv` replaces the
process so signals propagate correctly.

**Alternatives considered**:
- Shell script: harder to test, quoting nightmares with TOML parsing.
- Direct taskipy task with inline logic: too complex for taskipy's
  `{cmd}` syntax.

### D2: Environment variables as config transport

**Decision**: Launcher exports per-role env vars before exec'ing
OpenCode. Env var naming: `OPENCODE_{ROLE}_MODEL`,
`OPENCODE_{ROLE}_PROVIDER`, `OPENCODE_{ROLE}_EFFORT`.

Role names (uppercase): `ROADMAP`, `PROPOSE`, `APPLY`, `REVIEW`,
`FINALIZE`, `EXPLORE`, `SLICE`.

**Why**: Env vars are the standard mechanism for per-session config
isolation. Each terminal gets its own shell, so env vars are naturally
isolated. No file conflicts between sessions.

**How OpenCode reads them**: `opencode.json` agent definitions will use
env var references (e.g., `"model": "${OPENCODE_ROADMAP_MODEL}"`) if
OpenCode supports interpolation. If not, the launcher generates a
session-local `opencode.json` from a template.

### D3: Resolution chain

Priority (highest to lowest):
1. CLI argument: `uv run task oc -- --profile <name>`
2. Env var: `OPENCODE_PROFILE=<name>`
3. TOML file: `[default] profile = "<name>"` in `profiles.toml`
4. Built-in default: `xiaomi-balanced`

TOML file is optional. Script works without it using built-in profiles.

### D4: Built-in profile definitions

Four profiles, each mapping 7 agent roles to (provider, model, effort):

**`openai-cheap`** — all roles use cheap OpenAI model, high effort:
| Role | Provider | Model | Effort |
|------|----------|-------|--------|
| roadmap | openai | gpt-5.4-mini | high |
| propose | openai | gpt-5.4-mini | high |
| apply | openai | gpt-5.4-mini | high |
| review | openai | gpt-5.4-mini | high |
| finalize | openai | gpt-5.4-mini | high |
| explore | openai | gpt-5.4-mini | high |
| slice | openai | gpt-5.4-mini | high |

**`openai-balanced`** — all roles use capable OpenAI model, high effort:
| Role | Provider | Model | Effort |
|------|----------|-------|--------|
| roadmap | openai | gpt-5.4 | high |
| propose | openai | gpt-5.4 | high |
| apply | openai | gpt-5.4 | high |
| review | openai | gpt-5.4-mini | high |
| finalize | openai | gpt-5.4-mini | high |
| explore | openai | gpt-5.4 | high |
| slice | openai | gpt-5.4 | high |

**`openai-xiaomi-balanced`** — mixed: OpenAI for heavy reasoning,
Xiaomi for execution:
| Role | Provider | Model | Effort |
|------|----------|-------|--------|
| roadmap | openai | gpt-5.4-mini | high |
| propose | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| apply | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| review | xiaomi-token-plan-sgp | mimo-v2.5 | medium |
| finalize | xiaomi-token-plan-sgp | mimo-v2.5 | medium |
| explore | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| slice | openai | gpt-5.4-mini | high |

**`xiaomi-balanced`** — all roles use Xiaomi models, medium effort
(current default, cheapest):
| Role | Provider | Model | Effort |
|------|----------|-------|--------|
| roadmap | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| propose | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| apply | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| review | xiaomi-token-plan-sgp | mimo-v2.5 | medium |
| finalize | xiaomi-token-plan-sgp | mimo-v2.5 | medium |
| explore | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |
| slice | xiaomi-token-plan-sgp | mimo-v2.5-pro | medium |

**Default**: `xiaomi-balanced` (matches current `opencode.json`).

### D5: TOML profile file seam

File: `profiles.toml` at repo root. Optional — script works without it.

```toml
[default]
profile = "xiaomi-balanced"

[profiles.openai-cheap.roadmap]
provider = "openai"
model = "gpt-5.4-mini"
effort = "high"

[profiles.openai-cheap.propose]
provider = "openai"
model = "gpt-5.4-mini"
effort = "high"

# ... etc for each role in each profile
```

Script loads TOML if `profiles.toml` exists, merges with built-in
defaults (TOML overrides built-in). If file missing, uses built-in only.

### D6: Multi-session isolation

Each terminal runs its own `oc` invocation. The launcher:
1. Resolves profile (TOML → env → built-in).
2. Exports per-role env vars to the terminal's shell.
3. `execv`s into OpenCode.

Since env vars are per-process, different terminals with different
profiles have completely isolated configs. No shared state, no file
conflicts.

### D7: `opencode.json` env var support

**Decision**: Check if OpenCode supports `${env:VAR}` interpolation in
JSON config values. If yes, update `opencode.json` to reference env vars
with fallbacks to current hardcoded values. If no, launcher generates
a session-local `opencode.json` from a template.

**Fallback**: Template at `scripts/opencode_template.json` with
placeholders. Launcher renders it to a temp dir, sets
`OPENCODE_CONFIG=<path>`, execs OpenCode.

## Risks / Trade-offs

- **[Risk]** OpenCode may not support env var interpolation in config.
  → **Mitigation**: Fallback to template-based config generation (D7).
  Verify OpenCode config capabilities before implementation.

- **[Risk]** Profile names in env vars may conflict with other tools.
  → **Mitigation**: Use `OPENCODE_` prefix consistently. Document
  prefix convention.

- **[Risk]** TOML parsing adds dependency on `tomllib` (Python 3.11+,
  stdlib). → **Mitigation**: Already on Python 3.12, `tomllib` is
  stdlib. No new dependency.

- **[Trade-off]** Restart required to switch profiles. → Acceptable.
  Runtime switching would require OpenCode API support, which is out of
  scope.

## Migration Plan

1. Create `scripts/oc_profile.py` with built-in profiles.
2. Add taskipy task `oc` to `pyproject.toml`.
3. Verify OpenCode env var or config interpolation support.
4. Update `opencode.json` if env var interpolation works (preferred).
5. Document usage in AGENTS.md or dedicated doc.
6. User creates `profiles.toml` when ready (future slice).

## Open Questions

1. **OQ1**: Does OpenCode support `${env:VAR}` interpolation in
   `opencode.json` model fields? If not, what is the mechanism for
   per-session config override?
2. **OQ2**: Should the taskipy task be `oc` (short) or `oc-profile`
   (explicit)? `oc` may conflict with an existing shell alias.
3. **OQ3**: Exact effort parameter name in OpenCode API — is it
   `effort`, `reasoning_effort`, or something else?
4. **OQ4**: Should `opencode.json` keep hardcoded values as fallback
   when env vars are unset, or should the launcher always generate a
   resolved config?
