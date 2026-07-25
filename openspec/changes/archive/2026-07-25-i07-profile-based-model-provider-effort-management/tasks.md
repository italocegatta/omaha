## 1. Template creation

- [x] 1.1 Create `scripts/opencode_template.json` from current `opencode.json` structure with `{ROLE_MODEL}` and `{ROLE_PROVIDER}` placeholders for all seven roles
- [x] 1.2 Verify template renders without error for all four built-in profiles using `str.format()`

## 2. Config generation in oc_profile.py

- [x] 2.1 Add `render_template(profile: dict[str, Profile]) -> str` function that fills template placeholders with profile values
- [x] 2.2 Add `write_config_atomic(content: str, path: Path) -> None` function that writes to temp file and renames atomically
- [x] 2.3 Create `.opencode-profiles/` directory (gitignored) for generated configs
- [x] 2.4 Update `main()` to render template + write config before `execv`

## 3. OpenCode config delivery verification

- [x] 3.1 Verify if OpenCode supports `OPENCODE_CONFIG` env var or `--config <path>` CLI flag → not supported; atomic replace of `opencode.json` is the mechanism
- [x] 3.2 If supported: set env var/flag to point to generated config → N/A (not supported)
- [x] 3.3 If not supported: implement atomic replace of `opencode.json` (write to temp, rename) with backup of original

## 4. Documentation and gitignore

- [x] 4.1 Add `.opencode-profiles/` to `.gitignore`
- [x] 4.2 Update AGENTS.md profile documentation to reflect template-based config generation
- [x] 4.3 Document one-profile-at-a-time limitation (if `OPENCODE_CONFIG` unsupported)

## 5. Testing

- [x] 5.1 Unit test: `render_template()` produces valid JSON for all four profiles
- [x] 5.2 Unit test: generated config contains correct model/provider per role
- [x] 5.3 Integration test: `uv run task agent-profile -- --profile openai-cheap --export-only` shows correct env vars AND generates config file (covered by `test_export_only_mode` + `test_export_only_generates_config`)
- [x] 5.4 Smoke test: load generated JSON and validate structure matches OpenCode config schema
