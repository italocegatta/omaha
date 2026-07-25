## Why

Profile-based model/provider/effort management was implemented in I07 but
the core mechanism doesn't work: OpenCode reads model configuration from
`opencode.json` hardcoded values, ignoring environment variables exported
by `scripts/oc_profile.py`. The launcher sets env vars
(`OPENCODE_ROADMAP_MODEL`, etc.) that OpenCode never reads. Result:
all profiles behave identically — the `xiaomi-balanced` config in
`opencode.json` always prevails regardless of selected profile.

Root cause confirmed: OpenCode config format does not support `${env:VAR}`
interpolation. The env var approach (design decision D2 in original I07)
was predicated on an unverified assumption.

This correction reopens I07 to fix the config delivery mechanism.

## What Changes

- `scripts/oc_profile.py` generates an effective `opencode.json` from a
  template, writing it atomically to a temp directory before `execv`.
- New template file `scripts/opencode_template.json` with `{ROLE_MODEL}`
  and `{ROLE_PROVIDER}` placeholders.
- Generated config written to `<repo>/.opencode-profiles/<profile>.json`
  (or temp dir), passed to OpenCode via `OPENCODE_CONFIG` env var or
  equivalent mechanism.
- Env var export retained as secondary signal (for tools that read them)
  but no longer the primary config delivery path.
- Documentation updated to reflect that profile is single source of truth
  for config generation.

No production code change. Dev tooling only.

## Capabilities

### New Capabilities

(none — correction of existing `agent-profile-launcher` capability)

### Modified Capabilities

- `agent-profile-launcher`: Spec SHALL be updated to require
  template-based config generation instead of env var export as the
  primary mechanism for delivering profile config to OpenCode.

## Impact

- `scripts/oc_profile.py`: add template rendering + atomic write.
- `scripts/opencode_template.json`: new template file.
- `.opencode-profiles/` or temp dir: generated configs (gitignored).
- `opencode.json`: may become a symlink to the active profile's generated
  config, or remain as-is with the launcher overriding via env var.
- `pyproject.toml`: no change (taskipy task already exists).
- No impact on omaha application code, tests, or runtime behavior.
