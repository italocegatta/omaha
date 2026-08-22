## Context

R42 is a bounded compatibility repair identified by F60's blocked browser
evidence. `src/omaha/logging_config.py` currently defines `JsonFormatter` and
`configure_logging`, but not `get_logger`. During FastAPI startup,
`src/omaha/main.py::_prune_snapshots_on_startup` imports that missing symbol
only when `scripts.snapshot_db.prune_snapshots` deletes one or more files.
Thus ordinary startup can pass while a retention-prune startup crashes with
`ImportError`, preventing app/E2E startup.

### Code map

| File / symbol | Current role in flow |
|---|---|
| `src/omaha/logging_config.py::JsonFormatter` | Converts `LogRecord` to the seven-key JSON log shape. |
| `src/omaha/logging_config.py::configure_logging` | Installs JSON/text handlers and levels for `omaha` and `omaha.access`; owns logger configuration. |
| `src/omaha/logging_config.py::__all__` | Declares current public module surface (`JsonFormatter`, `configure_logging`). |
| `src/omaha/main.py::_prune_snapshots_on_startup` | Calls `prune_snapshots(Path("data/snapshots"), retention=DEFAULT_RETENTION)` once at startup; logs deletion count only when count is nonzero. |
| `src/omaha/main.py::create_app` | Registers `_prune_snapshots_on_startup` in FastAPI startup when `OMAHA_SKIP_STARTUP` is not `1`. |
| `src/omaha/main.py` module-load wiring | Calls `configure_logging` outside pytest, then builds module-level `app`. |
| `tests/test_logging.py` | Unit oracle for formatter shape and configured JSON output. |
| `tests/test_db_snapshot.py` | Unit oracle for snapshot creation, retention, naming, and no-op boundaries. |

### Current relevant flow

1. FastAPI lifespan startup invokes `_prune_snapshots_on_startup`.
2. Function imports `DEFAULT_RETENTION` and `prune_snapshots`, then passes the
   fixed relative destination `data/snapshots` and retention value.
3. `prune_snapshots` returns deleted-file count. Zero is a no-op for logging;
   positive count enters a local import of `omaha.logging_config.get_logger`.
4. The missing symbol raises before the intended `INFO` event can be emitted.
   A valid logger factory must return a logger that accepts the existing
   `.info(message, *args)` call and participates in `configure_logging`'s
   hierarchy.

Boundary conditions preserved: missing snapshot directory remains a no-op;
retention and deletion remain owned by `scripts.snapshot_db`; prune errors
continue to propagate; logging is attempted only when `deleted` is truthy;
pytest keeps existing handler behavior.

## Goals / Non-Goals

**Goals:**

- Restore minimal `omaha.logging_config.get_logger(name)` compatibility.
- Keep returned logger behavior compatible with standard `logging.Logger` and
  existing `configure_logging` handlers/levels.
- Prove positive-count startup-prune logging and zero-count retention behavior
  without starting a server or touching the live database.
- Leave F60 unblocked only at code level; owner-authorized PID stop, refresh,
  and browser validation remain subsequent work outside R42.

**Non-Goals:**

- No F60 templates, CSS, browser workflow, or notification behavior.
- No F59 job/endpoint semantics, MyProfit connector, credentials, or network
  calls.
- No broad logging redesign, formatter/schema change, handler change,
  environment-mode change, rotation, filtering, or third-party dependency.
- No `main.py` edit unless implementation proves a direct compatibility need;
  preferred change is confined to `logging_config.py` plus focused tests.
- No snapshot retention, database mutation, seed, test harness, task runner,
  server process, PID, or production DB operation.

## Decisions

### 1. Use thin standard-library factory

Implement `get_logger(name)` as a direct wrapper around
`logging.getLogger(name)` and include it in `__all__`. This restores the
smallest contract and preserves logger identity, hierarchy, propagation, and
handler configuration already defined by `configure_logging`.

Rejected: creating a custom logger, installing handlers in the factory, or
calling `configure_logging` from the factory. Those choices duplicate global
configuration and can disrupt pytest capture or duplicate production output.

### 2. Keep caller unchanged

Preserve the local import and `.info("snapshot prune: ...", deleted, dest_dir)`
call in `_prune_snapshots_on_startup`. Caller already expresses desired
behavior and changing it would widen R42 beyond restoring its dependency.

Rejected: moving prune logging to module load, changing the message, or
logging zero deletions. None is required to restore startup compatibility.

### 3. Test through existing boundaries

Extend `tests/test_logging.py` with factory identity/namespace coverage and
`tests/test_db_snapshot.py` with a direct `_prune_snapshots_on_startup`
regression using isolated monkeypatches and `caplog`. The latter proves the
positive deletion branch reaches a logger instead of failing at import, while
existing snapshot tests continue to own retention semantics.

Rejected: E2E/browser startup, live `data/snapshots`, live `data/portfolio.db`,
or PID/server operations. Those are explicitly prohibited in this propose
gate and belong to owner-authorized post-R42 F60 validation.

### Change map

| File / symbol | From → to | Reason |
|---|---|---|
| `src/omaha/logging_config.py::get_logger`, `__all__` | Symbol absent and not exported → thin `logging.getLogger(name)` factory exported with existing public symbols unchanged | Restore exact dependency consumed by startup prune. |
| `src/omaha/main.py::_prune_snapshots_on_startup` | Existing caller retained → no behavior change; edit only if an implementation-level compatibility proof requires it | Avoid rewriting functional F60-adjacent startup code. |
| `tests/test_logging.py` | Formatter/configuration coverage only → add factory returns named standard logger and repeated lookup preserves identity | Pin minimal public logging contract. |
| `tests/test_db_snapshot.py` | Snapshot helper coverage → add positive prune-startup logging regression with isolated fake deletion count | Pin app-startup boundary without DB/server side effects. |
| `specs/logging-contract/spec.md` | No stable capability contract → add normative factory and prune-startup scenarios | Give apply/review independent behavioral oracle. |

## Risks / Trade-offs

- **[Risk]** `logging.getLogger` global state leaks across tests → **Mitigation:**
  factory test asserts identity/name only; startup test uses `caplog` and does
  not reconfigure global handlers.
- **[Risk]** Test imports `omaha.main` and triggers unrelated composition →
  **Mitigation:** call only `_prune_snapshots_on_startup` with monkeypatched
  `prune_snapshots`; do not create a live client or startup lifespan.
- **[Risk]** A future caller expects richer factory behavior → **Mitigation:**
  R42 documents only standard `Logger` compatibility; richer behavior needs a
  separate scoped change.
- **[Risk]** F60 still fails due stale PID/runtime state → **Mitigation:**
  record this as post-R42 owner gate; do not stop PID 115075 or refresh here.

## Migration Plan

No migration or deployment step. Apply adds the factory and focused tests,
runs prescribed taskipy checks, then review records canonical full suite as
`NOT RUN — maintenance-suspended` per config. Rollback removes only R42 code,
tests, and change artifacts; no database or process rollback is needed.

## Open Questions

None. Compatibility requirement is concrete: standard-library logger lookup
for the existing `main.py:107` call, with no caller redesign.

## Implementation Decisions

### Thin factory is sufficient; caller remains untouched

- **Context:** Pre-edit `git diff HEAD~1` showed only unrelated F59 startup
  service additions in `main.py`; the missing dependency is isolated to
  `logging_config.py`.
- **Decision:** Implement only `get_logger(name) -> logging.Logger` as
  `logging.getLogger(name)` and export it. Keep
  `_prune_snapshots_on_startup` unchanged; do not configure handlers in the
  factory.
- **Impact:** Existing logger identity, hierarchy, propagation, configured
  handlers, formatter shape, and positive/zero prune branches remain owned by
  current code. No `main.py` compatibility edit is needed.
- **Evidence:** Focused R42 tests passed (`15 passed`), including positive
  startup-prune logging and zero-deletion silence; exact and stable OpenSpec
  validation passed.
