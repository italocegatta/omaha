# Agent Profile Launcher

## Purpose

Profile-based agent configuration (provider, model, effort per role) with
taskipy launcher for OpenCode sessions.

## Requirements

### Requirement: Profile selection via taskipy launcher
The system SHALL provide a taskipy task that launches an OpenCode session
with a named profile. The task SHALL accept a profile name as argument.
If no profile name is given, the system SHALL use the default profile.

#### Scenario: Launch with explicit profile
- **WHEN** user runs `uv run task oc -- --profile openai-cheap`
- **THEN** the launcher resolves the `openai-cheap` profile and exec's
  OpenCode with that profile's (provider, model, effort) per role

#### Scenario: Launch with default profile
- **WHEN** user runs `uv run task oc` without `--profile` argument
- **THEN** the launcher uses the default profile (`xiaomi-balanced`)
  and exec's OpenCode with that profile's configuration

#### Scenario: Launch with unknown profile
- **WHEN** user runs `uv run task oc -- --profile nonexistent`
- **THEN** the launcher prints an error listing available profiles
  and exits with code 1

### Requirement: Built-in profile definitions
The system SHALL include four built-in profiles: `openai-cheap`,
`openai-balanced`, `openai-xiaomi-balanced`, `xiaomi-balanced`. Each
profile SHALL define a (provider, model, effort) triple for each agent
role: `roadmap`, `propose`, `apply`, `review`, `finalize`, `explore`,
`slice`.

#### Scenario: All four profiles are available
- **WHEN** user runs `uv run task oc -- --list-profiles`
- **THEN** the launcher prints the four profile names and their
  description

#### Scenario: Profile defines all seven roles
- **WHEN** a profile is loaded (built-in or TOML)
- **THEN** the profile SHALL contain entries for all seven roles:
  `roadmap`, `propose`, `apply`, `review`, `finalize`, `explore`, `slice`

### Requirement: Environment variable export per role
The launcher SHALL export environment variables for each agent role
before exec'ing OpenCode. Variable naming:
`OPENCODE_{ROLE_UPPER}_MODEL`, `OPENCODE_{ROLE_UPPER}_PROVIDER`,
`OPENCODE_{ROLE_UPPER}_EFFORT`.

#### Scenario: Env vars are set for all roles
- **WHEN** launcher resolves profile `openai-cheap`
- **THEN** the following env vars are exported (among others):
  `OPENCODE_ROADMAP_MODEL=gpt-5.4-mini`,
  `OPENCODE_ROADMAP_PROVIDER=openai`,
  `OPENCODE_ROADMAP_EFFORT=high`

#### Scenario: Different sessions have isolated env vars
- **WHEN** terminal A runs profile `openai-cheap` and terminal B runs
  profile `xiaomi-balanced`
- **THEN** terminal A's `OPENCODE_ROADMAP_MODEL` is `gpt-5.4-mini`
  and terminal B's `OPENCODE_ROADMAP_MODEL` is `mimo-v2.5-pro`,
  with no cross-contamination

### Requirement: Resolution chain
The launcher SHALL resolve the active profile using this priority
(highest first): CLI `--profile` argument, `OPENCODE_PROFILE` env var,
TOML default, built-in default.

#### Scenario: CLI argument overrides env var
- **WHEN** `OPENCODE_PROFILE=openai-cheap` is set but user runs
  `uv run task oc -- --profile xiaomi-balanced`
- **THEN** the launcher uses `xiaomi-balanced`

#### Scenario: Env var overrides TOML default
- **WHEN** `profiles.toml` sets `default.profile = "openai-balanced"`
  and `OPENCODE_PROFILE=openai-cheap` is set
- **THEN** the launcher uses `openai-cheap`

#### Scenario: TOML default overrides built-in
- **WHEN** `profiles.toml` sets `default.profile = "openai-balanced"`
  and no CLI arg or env var is set
- **THEN** the launcher uses `openai-balanced`

### Requirement: TOML profile file seam
The launcher SHALL load `profiles.toml` from the repo root if the file
exists. TOML profiles SHALL override built-in profiles with the same
name. If the file does not exist, the launcher SHALL use built-in
profiles only.

#### Scenario: TOML file absent
- **WHEN** `profiles.toml` does not exist in the repo root
- **THEN** the launcher uses built-in profiles without error

#### Scenario: TOML file present with custom profile
- **WHEN** `profiles.toml` defines `[profiles.my-custom.roadmap]` with
  `provider = "openai"`, `model = "gpt-5.4"`, `effort = "high"`
- **THEN** `uv run task oc -- --profile my-custom` uses those values
  for the `roadmap` role

#### Scenario: TOML overrides built-in profile
- **WHEN** `profiles.toml` redefines `openai-cheap` with different
  model values
- **THEN** the TOML values take precedence over built-in defaults

### Requirement: Effort values per provider
Xiaomi models SHALL use `effort = "medium"`. OpenAI models for `roadmap`
role and subagent roles using OpenAI SHALL use `effort = "high"`.

#### Scenario: Xiaomi profile has medium effort
- **WHEN** profile `xiaomi-balanced` is resolved
- **THEN** all roles have `effort = "medium"`

#### Scenario: OpenAI profile has high effort
- **WHEN** profile `openai-cheap` is resolved
- **THEN** all roles have `effort = "high"`

### Requirement: Documentation for day-to-day usage
The system SHALL document: how to launch with a profile, how to switch
profiles (restart the session), how to run multiple sessions with
different profiles, and how to create custom profiles in `profiles.toml`.

#### Scenario: Documentation exists and is accurate
- **WHEN** user reads the profile documentation
- **THEN** they can successfully launch OpenCode with any of the four
  built-in profiles and understand how to create custom profiles
