# I03 Spec Changes

No spec-level changes. This slice is pure tooling/plumbing — the `prek-hooks` spec
requirement "Pytest full gate on pre-push" already allows one or more `uv run task ...`
commands. The existing spec language is compatible with two separate hooks; only
`prek.toml` implementation changes.
