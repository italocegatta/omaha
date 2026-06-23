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
  2. ``login.feature`` + ``profile_isolation.feature`` MUST NOT
     use the ``login_and_pick_profile`` / ``switch_profile``
     wrappers (per-workflow carve-out — they test the flow
     itself).
  3. Every ``_w_*`` function body must ``Call`` at least one
     name defined in ``_workflows.py`` (no inlined workflow
     logic, which would silently bypass the workflow's
     pre-condition assertion and data-testid documentation).

## Workflows

| Workflow | Purpose | Pre-condition | Carve-out |
|---|---|---|---|
| ``login_and_pick_profile`` | Bootstrap: log in + select profile | none (entry point) | ``login.feature``, ``profile_isolation.feature`` |
| ``switch_profile`` | Log out + log in as another profile | logged in (``page.url`` ends with ``/``) | ``profile_isolation.feature`` |
| ``create_one_class`` | Inline ``+ Nova classe`` form | logged in | none |
| ``create_two_default_classes`` | Loop ``create_one_class`` over ``DEFAULT_TWO_CLASSES`` | logged in | none |
| ``add_one_asset`` | Per-class ``+ Ativo`` modal | logged in + class exists | none |
| ``create_four_assets`` | Loop ``add_one_asset`` over ``DEFAULT_FOUR_ASSETS`` | logged in + classes exist | none |

Dataclasses ``ClassSpec(name, target_pct)`` and
``AssetSpec(class_name, ticker, target_pct)`` are the canonical
input shapes. ``DEFAULT_TWO_CLASSES`` and ``DEFAULT_FOUR_ASSETS``
are the "happy path" payloads used when the wrapper doesn't
parameterize.

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
keep login / switch steps inline. The contract test
``test_carve_out_files_use_inline_steps`` enforces this so a
contributor can't sneak the wrapper back in.
