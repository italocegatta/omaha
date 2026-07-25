## Context

I07 implemented profile-based model/provider/effort management with a
launcher script (`scripts/oc_profile.py`) that exports per-role env vars
before `execv`'ing into OpenCode. The assumption was that OpenCode would
read these env vars for model configuration.

**Root cause**: OpenCode does not support `${env:VAR}` interpolation in
`opencode.json`. The hardcoded model values in `opencode.json` always
prevail. The env var approach (original design D2) was predicated on an
unverified assumption and does not work.

Current state:
- `scripts/oc_profile.py`: exports env vars correctly, but they're ignored.
- `opencode.json`: hardcoded `xiaomi-balanced` config always active.
- All four profiles behave identically — no actual profile switching.

## Goals / Non-Goals

**Goals:**
- Make profile selection actually change the model/provider/effort that
  OpenCode uses.
- Single atomic operation: resolve profile → generate config → launch.
- No manual `opencode.json` edits when switching profiles.
- Preserve multi-session isolation (each terminal gets its own config).

**Non-Goals:**
- Modifying OpenCode source code or config format.
- Runtime profile switching (restart required).
- Profile inheritance or composition.
- Changing which roles exist or their responsibilities.

## Decisions

### D1: Template + atomic config generation (replaces original D2)

**Decision**: `oc_profile.py` renders an `opencode_template.json` with
profile-specific values and writes the result atomically to
`.opencode-profiles/<profile>.json`. The launcher then either:
- (a) sets `OPENCODE_CONFIG=<path>` env var before `execv` (if OpenCode
  supports it), or
- (b) replaces `opencode.json` atomically (write to temp, rename).

**Why**: This is the only reliable mechanism since OpenCode doesn't
support env var interpolation. Template rendering is deterministic and
testable. Atomic write prevents partial configs if the process crashes.

**Alternatives considered**:
- Keep env vars only: doesn't work (confirmed root cause).
- Modify OpenCode source: out of scope, too invasive.
- Shell wrapper that edits `opencode.json` before launch: fragile,
  race-prone with concurrent sessions.

**Verification needed**: Does OpenCode support `OPENCODE_CONFIG` env var
or `--config <path>` CLI flag? If not, fallback to atomic replace of
`opencode.json` (with backup).

### D2: Config file location

**Decision**: Generated configs go to `.opencode-profiles/<profile>.json`.
This directory is gitignored.

**Why**: Keeps generated files separate from source-controlled
`opencode.json`. Each profile gets its own file — no overwriting between
concurrent sessions.

### D3: Concurrency model — one profile per terminal

**Decision**: Each terminal session runs one profile. Multiple terminals
can run different profiles simultaneously.

**Constraint**: If OpenCode reads `opencode.json` from a fixed path
(no `OPENCODE_CONFIG` support), concurrent sessions writing to the same
file would race. In that case:
- Each session writes to `.opencode-profiles/<profile>.json`.
- Before launch, the script atomically renames the profile's config to
  `opencode.json` (replacing the previous one).
- **Limitation**: only one profile can be active per repo at a time.
  Concurrent sessions must use the same profile, or use separate
  worktrees.

**Why**: This is a pragmatic constraint. Profile switching is a developer
convenience, not a production requirement. The trade-off is acceptable.

### D4: Template structure

**Decision**: `scripts/opencode_template.json` is a JSON file with
Python `str.format()` placeholders: `{ROADMAP_MODEL}`, `{ROADMAP_PROVIDER}`,
`{PROPOSE_MODEL}`, etc. The template includes all seven roles with their
descriptions and temperature settings.

**Why**: `str.format()` is stdlib, no new dependencies. Placeholders are
explicit and grep-able. Template is version-controlled alongside the script.

### D5: Env var export retained as secondary signal

**Decision**: Keep `export_env_vars()` in `oc_profile.py`. Env vars are
still set for any tool that reads them (e.g., future OpenCode versions,
custom scripts). But they are no longer the primary config delivery path.

**Why**: Defense in depth. If OpenCode adds env var support later, it
"just works". No code removal needed.

## Risks / Trade-offs

- **[Risk]** OpenCode may not support `OPENCODE_CONFIG` or `--config`.
  → **Mitigation**: Fallback to atomic replace of `opencode.json`.
  Document the one-profile-at-a-time limitation.

- **[Risk]** Atomic replace of `opencode.json` races with concurrent
  sessions using different profiles.
  → **Mitigation**: Document constraint. Use `os.replace()` (atomic on
  POSIX). Accept one-profile-at-a-time as documented limitation.

- **[Risk]** Template drift — `opencode.json` changes but template
  doesn't.
  → **Mitigation**: Add a test that validates template renders without
  error for all four profiles. Consider a smoke test that loads the
  generated JSON and validates structure.

- **[Trade-off]** One profile at a time (if `OPENCODE_CONFIG` unsupported).
  → Acceptable. Developer convenience, not production requirement.

## Migration Plan

1. Create `scripts/opencode_template.json` from current `opencode.json`
   structure with placeholders.
2. Modify `scripts/oc_profile.py`:
   - Add `render_template(profile) -> str` function.
   - Add `write_config_atomic(content, path)` function.
   - Update `main()` to render + write before `execv`.
3. Verify OpenCode config loading mechanism (`OPENCODE_CONFIG`, `--config`,
   or fixed path).
4. Update documentation in AGENTS.md to reflect template-based approach.
5. Add `.opencode-profiles/` to `.gitignore`.

## Open Questions

1. **OQ1**: Does OpenCode support `OPENCODE_CONFIG` env var or
   `--config <path>` CLI flag? If yes, use it. If no, atomic replace.
2. **OQ2**: Should the template include `temperature` per role, or only
   `model` and `provider`?
3. **OQ3**: Should the launcher backup the original `opencode.json`
   before replacing it?
