- [x] 1.1 In `src/omaha/templates/login.html`, wrap the existing
      block content in `<div class="auth-card">...</div>`.
- [x] 1.2 In `src/omaha/templates/profiles.html`, wrap the existing
      block content in `<div class="auth-card">...</div>`.
- [x] 1.3 In `src/omaha/static/app.css`, add `.auth-card` rule set
      (480px max-width, 4rem top margin, --surface, 1px border,
      8px radius) plus scoped input/button styles.
- [x] 1.4 `uv run task lint` + `uv run task test-unit` pass (CSS
      + template only, no logic).