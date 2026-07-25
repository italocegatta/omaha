## MODIFIED Requirements

### Requirement: Config delivery via template generation
The launcher SHALL generate an effective `opencode.json` from a template
before exec'ing OpenCode. The template SHALL contain placeholders for
per-role model and provider values. The launcher SHALL render the template
with the resolved profile's values and write the result atomically to
`.opencode-profiles/<profile>.json`.

#### Scenario: Template renders correctly for all profiles
- **WHEN** launcher resolves profile `openai-cheap`
- **THEN** the template is rendered with that profile's (provider, model)
  values for all seven roles and the result is valid JSON

#### Scenario: Generated config is written atomically
- **WHEN** launcher writes the rendered config
- **THEN** the write uses atomic operation (write to temp, rename) to
  prevent partial configs if the process crashes

#### Scenario: Generated config location
- **WHEN** launcher generates config for profile `xiaomi-balanced`
- **THEN** the config is written to `.opencode-profiles/xiaomi-balanced.json`

### Requirement: OpenCode config delivery via atomic replace
The launcher SHALL deliver the generated config to OpenCode by
atomically replacing `opencode.json` in the repo root. This is the
primary and only delivery mechanism — OpenCode does not support
`OPENCODE_CONFIG` env var or `--config` CLI flag.

#### Scenario: Config delivered to OpenCode
- **WHEN** launcher renders config for profile `openai-cheap`
- **THEN** the rendered config atomically replaces `opencode.json` in the
  repo root before exec'ing OpenCode

#### Scenario: Atomic replace prevents partial config
- **WHEN** launcher writes to `opencode.json`
- **THEN** the write uses temp file + rename to prevent OpenCode reading
  a partially-written config

### Requirement: One-profile-at-a-time limitation
The system SHALL document that, since OpenCode reads config from
`opencode.json` at a fixed path, only one profile can be active per repo at a
time. Concurrent sessions using different profiles require separate
worktrees.

#### Scenario: Concurrent sessions with same profile
- **WHEN** terminal A and terminal B both run profile `openai-cheap`
- **THEN** both sessions use the same generated config without conflict

#### Scenario: Concurrent sessions with different profiles
- **WHEN** terminal A runs `openai-cheap` and terminal B runs `xiaomi-balanced`
- **THEN** the second launcher overwrites `opencode.json` with its profile's
  config; the first session's config is replaced (documented limitation)

### Requirement: Environment variable export retained
The launcher SHALL continue to export per-role environment variables
(`OPENCODE_{ROLE}_MODEL`, `OPENCODE_{ROLE}_PROVIDER`,
`OPENCODE_{ROLE}_EFFORT`) as secondary config signal and backward
compatibility. The primary delivery mechanism is template-based config
generation with atomic replace of `opencode.json`.

#### Scenario: Env vars are still set
- **WHEN** launcher resolves profile `openai-cheap`
- **THEN** env vars like `OPENCODE_ROADMAP_MODEL=gpt-5.4-mini` are set
  in addition to the generated config file

## UNCHANGED Requirements

The following requirements from the original spec remain unchanged:
- Profile selection via taskipy launcher
- Built-in profile definitions (four profiles, seven roles each)
- Resolution chain (CLI > env > TOML > built-in)
- TOML profile file seam
- Effort values per provider
- Documentation for day-to-day usage
