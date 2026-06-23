# BDD e2e suite

PT-BR Gherkin scenarios over a real chromium driving a real
uvicorn. Each ``.feature`` file is bound to pytest functions in
``test_scenarios.py``; step definitions live under
``step_defs/`` and are wired in via the autouse import block
at the bottom of ``conftest.py``.

## Running

```
task test-bdd           # full suite (real chromium, ~30-90s)
task test-bdd -k login  # one feature
task test-pattern login # pytest -k substring match
```

BDD scenarios run serial — the autouse
``clean_seeded_profiles`` fixture wipes both seeded profiles
before each scenario, and sharing SQLite session-scoped under
``pytest-xdist`` would race the wipe. Don't add xdist here
without revisiting that fixture.

## Architecture: workflow + wrapper pattern

The suite follows the **workflow + wrapper** contract
documented in ``openspec/specs/bdd-workflow-reuse/spec.md``:

- **Multi-step Gherkin sequences** that repeat in ≥2 scenarios
  with growth trend are extracted into a Python **workflow**
  in ``step_defs/_workflows.py``.
- A thin **step wrapper** under ``step_defs/<area>_steps.py``
  exposes the workflow to Gherkin via ``@given`` / ``@when``
  / ``@then``. Wrapper names carry the ``_w_`` prefix so the
  contract test can identify them.
- The contract is enforced by
  ``test_workflow_contracts.py`` (runs under ``task test-unit``,
  no DB / no Playwright). Three rules:
  1. ≤10 public workflows in ``_workflows.py`` (ceiling).
  2. Workflows that declare ``@carve_out(...)`` in
     ``_workflows.py`` MUST NOT be used in their declared
     carve-out feature files. Currently
     ``login_and_pick_profile`` is carved out from
     ``login.feature`` + ``profile_isolation.feature``
     (they test the auth flow itself).
  3. Every ``_w_*`` function body must ``Call`` at least one
     name defined in ``_workflows.py`` (no inlined workflow
     logic, which would silently bypass the workflow's
     pre-condition assertion and data-testid documentation).

## Workflows

| Workflow | Purpose | Pre-condition | Carve-out |
|---|---|---|---|
| ``login_and_pick_profile`` | Bootstrap: log in + select profile | none (entry point) | ``login.feature``, ``profile_isolation.feature`` |
| ``create_one_class`` | Inline ``+ Nova classe`` form | logged in | none |
| ``create_two_default_classes`` | Loop ``create_one_class`` over ``DEFAULT_TWO_CLASSES`` (or any ``list[ClassSpec]``) | logged in | none |
| ``add_one_asset`` | Single ``+ Ativo`` global button + class ``<select>`` picker modal | logged in + class exists | none |

Dataclasses ``ClassSpec(name, target_pct)`` and
``AssetSpec(class_name, ticker, target_pct)`` are the canonical
input shapes. ``DEFAULT_TWO_CLASSES`` is the "happy path"
payload used when ``create_two_default_classes`` is called
without an explicit list.

**Note:** ``_w_rf_pos_rf_dinamica_pct`` (in
``step_defs/class_steps.py``) is hardcoded to "RF Pós" and
"RF Dinâmica" — only the ``{p1}`` / ``{p2}`` percentages are
parametrized. For 2 classes with custom names, call
``create_two_default_classes(page, live_url, [ClassSpec(name1,
pct1), ClassSpec(name2, pct2)])`` directly from a custom
``@given`` step in ``step_defs/``.

The full per-workflow data-testid list (for PR review on UI
drift) lives in each function's docstring.

## Threshold & ceiling

Extract a workflow when the sequence appears in **≥2 scenarios
with growth trend**. Loose enough to absorb new feature files
landing; tight enough to avoid one-off sequences growing into
god modules. The **ceiling** is 10 public workflows — past that,
re-evaluate whether the suite really shares that much structure.

## Adding a new scenario

1. Pick the wrapper that already does the bootstrap you need
   (login, classes, assets). If the multi-step sequence is
   new and meets the threshold, add a workflow +
   ``_w_<name>`` wrapper first.
2. Author the scenario body in PT-BR. Keep PATCH / modal-fill
   steps inline — those test specific behavior and don't
   repeat across files.
3. Bind the new scenario to a test function in
   ``test_scenarios.py``:
   ```python
   @scenario("class_crud.feature", "New scenario name", features_base_dir="tests/bdd/features")
   def test_new_scenario():
       pass
   ```
4. Run ``task test-bdd -k class_crud`` before pushing.

## Adding a new workflow

1. Add the function in ``step_defs/_workflows.py`` with:
   - Pré-condição line in the docstring
   - data-testids block (one per line)
   - explicit ``RuntimeError`` on pre-condition failure
2. Add a ``_w_<name>`` wrapper in the relevant
   ``step_defs/<area>_steps.py`` that calls the workflow.
3. Run ``task test-unit`` — ``test_wrappers_delegate_to_workflows``
   asserts the wrapper actually delegates.

## Carve-out

``login.feature`` and ``profile_isolation.feature`` deliberately
keep login steps inline (the wrapper step text would silently
pass on auth-flow regressions). The carve-out is declared on
the workflow itself via the
``@carve_out(files=..., step_regex=...)`` decorator in
``_workflows.py``. The contract test
``test_carve_out_files_use_inline_steps`` parses these
decorators via AST and asserts each carve-out file does NOT
contain a step matching the declared regex. Adding a new
carve-out workflow = add the decorator; the test enforces
automatically (no hardcoded dict to maintain).
