## 1. Audit residual literals

- [x] 1.1 Confirm runtime CSS sites still using `background: #fff` / `#ffffff` and capture exact selectors affected by R05
- [x] 1.2 Confirm `.import-class-cell--cls-0..7` remain the only hex-based class tint rules in runtime CSS

## 2. Token-backed CSS migration

- [x] 2.1 Replace residual shared UI white surfaces with `var(--surface)` or existing sunk token where selector semantics require it
- [x] 2.2 Add `--class-1-tint` through `--class-8-tint` to `app.css :root` using `color-mix(in srgb, var(--class-N) 38%, var(--surface))`
- [x] 2.3 Rebind `.import-class-cell--cls-0..7` to the matching `var(--class-N-tint)` tokens
- [x] 2.4 Verify no runtime `#fff` or inline class-tint hex literals remain in `src/omaha/static/app.css`

## 3. Docs and spec sync

- [x] 3.1 Update `openspec/changes/r05-hex-literal-audit-and-migration/specs/color-tokens/spec.md` if apply-time reality changes token count or selector mapping
- [x] 3.2 Update `DESIGN.md` polish-pass section so items 1-2 are no longer future backlog and describe delivered token migration

## 4. Verification

- [x] 4.1 Run `task lint`
- [x] 4.2 Run `task test-unit`
- [x] 4.3 Run `task test-integration`
- [x] 4.4 Run `openspec validate r05-hex-literal-audit-and-migration --json`
- [x] 4.5 Run `refresh-for-test` and smoke the authenticated import/patrimonio surfaces on LAN URL
