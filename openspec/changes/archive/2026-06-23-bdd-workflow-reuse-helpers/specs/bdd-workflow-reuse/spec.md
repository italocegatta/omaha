# bdd-workflow-reuse Specification

## Purpose

Define the reuse pattern for multi-step sequences in the BDD e2e
suite under ``tests/bdd/``: any sequence of ≥2 Gherkin steps that
appears in ≥2 scenarios AND shows a clear growth trend SHALL be
extracted into a Python workflow in
``tests/bdd/step_defs/_workflows.py`` and exposed via a thin
step-definition wrapper. This contract exists so that business-
rule changes in the underlying flows (login, profile switch,
class creation, asset creation) require editing ONE Python
workflow rather than rewriting N ``.feature`` scenarios.

The threshold of "≥2 scenarios with growth trend" (rather than
"≥3 scenarios") reflects the natural shape of the BDD suite: a
multi-step setup usually appears in 2-3 places today and is
expected to grow as new feature files land. The growth-trend
qualifier prevents over-extraction of one-off sequences.

## ADDED Requirements

### Requirement: Python workflow for repeated multi-step sequences

The system SHALL provide a ``_workflows.py`` module at
``tests/bdd/step_defs/_workflows.py`` containing Python workflow
functions for each multi-step Gherkin sequence that appears in
≥2 scenarios with a clear growth trend.

Each workflow SHALL:

- Be a plain Python function (no ``@given``/``@when``/``@then``
  decorator) — the file is a workflow library, not a step
  registry.
- Take ``page`` and ``live_url`` as positional arguments (matches
  the step-def signature so wrappers can call workflows
  directly).
- Take any scenario-specific values as keyword arguments with
  sensible defaults.
- Document the data-testids it touches in the docstring
  (format: ``data-testids:`` block, one per line) so PR review
  can catch UI drift.
- Document its pre-conditions in the docstring (format:
  ``Pré-condição:`` line) and assert them at the top of the
  function body with a clear ``RuntimeError`` message.

#### Scenario: Workflows live in _workflows.py

- **WHEN** the BDD suite grows a new multi-step setup that
  appears in ≥2 scenarios with growth trend
- **THEN** a new workflow function is added to
  ``tests/bdd/step_defs/_workflows.py``
- **AND** the workflow takes ``page`` and ``live_url`` as
  positional args
- **AND** the workflow has no pytest-bdd decorator
- **AND** the workflow docstring lists its data-testids and
  pre-conditions

### Requirement: Dataclasses for workflow inputs

The system SHALL provide two frozen dataclasses for workflow
inputs that involve domain objects:

- ``ClassSpec(name: str, target_pct: int)`` — describes a
  single asset class
- ``AssetSpec(class_name: str, ticker: str, target_pct: int)``
  — describes a single asset, including the class it belongs to

Workflows that create classes SHALL accept
``classes: list[ClassSpec] | None`` (``None`` = use
``DEFAULT_TWO_CLASSES`` constant). Workflows that create assets
SHALL accept ``assets: list[AssetSpec] | None`` (``None`` = use
``DEFAULT_FOUR_ASSETS`` constant).

#### Scenario: Dataclasses exported from _workflows.py

- **WHEN** ``tests/bdd/step_defs/_workflows.py`` is imported
- **THEN** the module exports ``ClassSpec`` and ``AssetSpec``
- **AND** both are decorated with ``@dataclass(frozen=True)``
- **AND** the module exports
  ``DEFAULT_TWO_CLASSES: list[ClassSpec]`` and
  ``DEFAULT_FOUR_ASSETS: list[AssetSpec]``

### Requirement: Pre-condition assertion in workflows

The system SHALL require every workflow that depends on a prior
step (login, classes exist, etc.) to assert that pre-condition
explicitly at the top of the function body. The assertion SHALL:

- Check the relevant state (URL pattern, page element
  presence)
- Raise ``RuntimeError`` with a message naming the missing
  pre-condition and the actual observed state

#### Scenario: create_two_default_classes asserts login

- **WHEN** ``create_two_default_classes`` is called
- **AND** ``page.url`` does not end with ``"/"``
- **THEN** the workflow raises ``RuntimeError`` with a message
  that mentions ``login_and_pick_profile`` and the actual URL

### Requirement: Thin step-wrapper for each workflow

The system SHALL provide a thin step-definition wrapper in
``tests/bdd/step_defs/`` (e.g. ``common_steps.py``,
``class_steps.py``, ``asset_steps.py``) for each workflow in
``_workflows.py``. The wrapper SHALL:

- Be a single ``@given``/``@when``/``@then`` function with one
  positional body (typically 3 lines: call the workflow).
- Use a PT-BR step text matching the workflow's name (e.g.
  ``Que estou logado como "<profile>"`` wraps
  ``login_and_pick_profile``).
- Use ``parsers.parse`` or ``parsers.re`` if the step text
  carries captured parameters; otherwise a plain string match.
- Use ``@given`` for preconditions (login, classes, assets
  created); use ``@when`` only for actions (PATCH, save, click
  on a non-bootstrap button).
- Use the ``_w_`` name prefix (workflow-wrapper convention) so
  the contract test can identify them.

#### Scenario: Login workflow wrapped as @given

- **WHEN** a scenario needs to log in as a profile
- **AND** the scenario does NOT test the login flow itself
- **THEN** the scenario writes the step
  ``Dado que estou logado como "<profile>"``
- **AND** the step invokes
  ``login_and_pick_profile(page, live_url, profile)`` from
  ``_workflows.py``
- **AND** the scenario contains no other login-related steps

### Requirement: Per-workflow carve-out table

The system SHALL maintain a carve-out table in ``design.md``
(§Decisão 2) mapping each workflow to the feature files that
MUST NOT use its wrapper. Scenarios in carve-out files test the
workflow itself and would silently pass on bugs in the workflow.

A scenario in a carve-out file MAY still use wrappers for
workflows OTHER than the carved-out one (e.g. a scenario in
``login.feature`` can use the ``create_two_default_classes``
wrapper; it just cannot use the ``login_and_pick_profile``
wrapper).

The carve-out table SHALL cover at minimum:

- ``login_and_pick_profile`` → carve-out:
  ``login.feature``, ``profile_isolation.feature``
- ``switch_profile`` → carve-out: ``profile_isolation.feature``

Other workflows have no carve-out in this change.

#### Scenario: Carve-out table is in design.md

- **WHEN** the operator inspects ``design.md`` §Decisão 2
- **THEN** a table maps each of the 6 workflows to its
  carve-out feature files
- **AND** the table covers ``login_and_pick_profile``,
  ``switch_profile``, ``create_one_class``,
  ``create_two_default_classes``, ``add_one_asset``,
  ``create_four_assets``

### Requirement: Single source of truth for flow changes

The system SHALL guarantee that editing one Python workflow in
``_workflows.py`` is the only edit needed when the underlying
business flow changes (e.g. login form gains a 2FA field; class
creation gains a 3rd required attribute; asset modal layout
changes). All scenarios that use the corresponding step
wrapper SHALL pick up the new behavior automatically.

#### Scenario: Login form change propagates via workflow

- **WHEN** the login form gains a new field (e.g. 2FA token)
- **AND** the operator edits ``login_and_pick_profile`` in
  ``_workflows.py`` to fill the new field
- **THEN** every scenario that uses the
  ``estou logado como ...`` wrapper inherits the new behavior
  without any edits to its ``.feature`` file

### Requirement: Workflow count ceiling

The system SHALL NOT exceed 10 public workflow functions in
``_workflows.py``. If a new multi-step setup pushes the workflow
count above 10, the operator SHALL re-evaluate whether the
suite's scenarios share enough structure to justify another
workflow, or whether the new setup is too specific to warrant
inline steps.

#### Scenario: Workflow count stays within ceiling

- **WHEN** ``tests/bdd/step_defs/_workflows.py`` is inspected
- **THEN** the file contains ≤10 public function definitions
- **AND** each function has a docstring describing the flow
  it encapsulates, its data-testids, and its pre-conditions

### Requirement: Contract test — workflow count ceiling

The system SHALL provide
``tests/bdd/test_workflow_contracts.py::test_workflow_count_under_ceiling``
that asserts ``_workflows.py`` contains ≤10 public function
definitions (callables whose name does not start with ``_``).

#### Scenario: Workflow count contract enforces ceiling

- **WHEN** pytest collects
  ``tests/bdd/test_workflow_contracts.py``
- **THEN** the test inspects
  ``tests/bdd/step_defs/_workflows.py``
- **AND** fails if the count of public callables exceeds 10

### Requirement: Contract test — carve-out enforcement

The system SHALL provide
``test_carve_out_files_use_inline_steps`` that parses the
carve-out feature files and asserts no scenario contains a
step that matches any wrapper regex for the carved-out
workflow.

#### Scenario: login.feature has no login wrapper

- **WHEN** pytest parses ``tests/bdd/features/login.feature``
- **THEN** no scenario in that file contains a step matching
  ``estou logado como``
- **AND** the test fails otherwise

#### Scenario: profile_isolation.feature has no login wrapper

- **WHEN** pytest parses
  ``tests/bdd/features/profile_isolation.feature``
- **THEN** no scenario in that file contains a step matching
  ``estou logado como``
- **AND** the test fails otherwise

### Requirement: Contract test — wrapper delegates to workflow

The system SHALL provide ``test_wrappers_delegate_to_workflows``
that for each step definition in ``tests/bdd/step_defs/`` whose
name starts with ``_w_`` (workflow-wrapper convention) asserts
the wrapper body calls a function defined in
``tests/bdd/step_defs/_workflows.py``.

This catches the regression where a contributor copies workflow
logic into the wrapper instead of calling the workflow, which
would silently bypass the workflow's pre-condition assertions
and data-testid documentation.

#### Scenario: Wrapper delegates to workflow

- **WHEN** pytest collects
  ``tests/bdd/test_workflow_contracts.py``
- **THEN** the test iterates step definitions in
  ``tests/bdd/step_defs/``
- **AND** fails if any wrapper has duplicated logic instead of
  calling a function in ``_workflows.py``
