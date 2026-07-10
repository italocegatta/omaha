# T12 — spec changes

No spec changes needed. T12 is a debug-only harness slice:

- No new product capability introduced.
- No existing capability's REQUIREMENTS modified.
- Harness behavior changes (teardown ordering, wait timeout, fixture cleanup) are internal implementation details of `tests/e2e/conftest.py`, `tests/bdd/conftest.py` — not contracted capabilities.

See `proposal.md` for scope rationale.
