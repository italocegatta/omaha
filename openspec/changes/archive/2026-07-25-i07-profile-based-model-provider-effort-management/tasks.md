## 1. Profile data model and built-in definitions

- [x] 1.1 Create `scripts/oc_profile.py` with `BUILTIN_PROFILES` dict
  defining four profiles (`openai-cheap`, `openai-balanced`,
  `openai-xiaomi-balanced`, `xiaomi-balanced`) with (provider, model,
  effort) per role (roadmap, propose, apply, review, finalize, explore,
  slice)
- [x] 1.2 Define `Profile` TypedDict or dataclass: `provider: str`,
  `model: str`, `effort: str` per role
- [x] 1.3 Implement `resolve_profile(name: str) -> dict[str, Profile]`
  that looks up built-in profiles by name, raises `ValueError` on
  unknown name
- [x] 1.4 Add `--list-profiles` flag that prints available profiles
  with one-line descriptions and exits

## 2. Resolution chain

- [x] 2.1 Implement CLI argument parsing: `--profile <name>` takes
  precedence over env var
- [x] 2.2 Implement env var fallback: read `OPENCODE_PROFILE` if no
  CLI arg
- [x] 2.3 Implement TOML fallback: load `profiles.toml` from repo root
  if file exists, read `[default] profile = "<name>"`, merge TOML
  profiles with built-in (TOML overrides). Use `tomllib` (stdlib 3.12)
- [x] 2.4 Implement built-in default: `xiaomi-balanced` when no other
  source provides a profile name
- [x] 2.5 Error handling: print clear message with available profiles
  when name is invalid, exit code 1

## 3. Environment variable export

- [x] 3.1 Implement `export_env_vars(profile: dict[str, Profile])`
  that sets `OPENCODE_{ROLE}_MODEL`, `OPENCODE_{ROLE}_PROVIDER`,
  `OPENCODE_{ROLE}_EFFORT` for all seven roles in `os.environ`
- [x] 3.2 Verify env vars are correctly formatted (uppercase role
  names, exact values from profile)

## 4. OpenCode integration

- [x] 4.1 Verify whether OpenCode supports `${env:VAR}` interpolation
  in `opencode.json` model fields (test with a simple env var)
- [x] 4.a IF interpolation supported: update `opencode.json` agent
  definitions to reference env vars with hardcoded fallbacks (e.g.,
  `"model": "${OPENCODE_ROADMAP_MODEL:-xiaomi-token-plan-sgp/mimo-v2.5-pro}"`)
- [x] 4.b IF interpolation NOT supported: create
  `scripts/opencode_template.json` with `{ROLE_MODEL}` placeholders;
  launcher renders template to temp file and sets `OPENCODE_CONFIG` or
  equivalent before exec
- [x] 4.3 Implement `exec_opencode()` that calls `os.execvp("opencode",
  ["opencode"])` after env vars are set

## 5. Taskipy task

- [x] 5.1 Add `oc` task to `pyproject.toml` `[tool.taskipy.tasks]`:
  `oc = { cmd = "uv run python -m scripts.oc_profile", help = "Launch OpenCode with a named profile (use -- --profile <name>)" }`
- [x] 5.2 Verify `uv run task oc -- --profile openai-cheap` works end-to-end

## 6. Documentation

- [x] 6.1 Document day-to-day usage in `AGENTS.md` (or new
  `docs/agent-profiles.md`): how to launch, how to switch (restart),
  how to run multiple sessions, how to list profiles
- [x] 6.2 Document the four built-in profiles with their role →
  (provider, model, effort) mapping
- [x] 6.3 Document the TOML seam: how to create `profiles.toml`,
  format, override behavior
- [x] 6.4 Document resolution chain priority: CLI → env → TOML →
  built-in

## 7. Testing

- [x] 7.1 Unit test: `resolve_profile` returns correct mapping for
  each built-in profile
- [x] 7.2 Unit test: `resolve_profile` raises `ValueError` for
  unknown profile name
- [x] 7.3 Unit test: resolution chain priority (CLI > env > TOML >
  built-in)
- [x] 7.4 Unit test: TOML merge overrides built-in correctly
- [x] 7.5 Unit test: env var export produces correct variable names
  and values
- [x] 7.6 Integration test: `--list-profiles` prints all four profiles
