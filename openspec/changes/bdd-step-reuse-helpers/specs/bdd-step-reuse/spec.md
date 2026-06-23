# bdd-step-reuse Specification

## Purpose

Define the reuse pattern for multi-step sequences in the BDD e2e
suite under ``tests/bdd/``: any sequence of ≥3 Gherkin steps that
appears in ≥3 scenarios SHALL be extracted into a Python helper
in ``tests/bdd/step_defs/_workflows.py`` and exposed via a thin
step-definition wrapper. This contract exists so that business-
rule changes in the underlying flows (login, class creation,
asset creation) require editing ONE Python helper rather than
rewriting N ``.feature`` scenarios.

## Requirements

### Requirement: Python helper for repeated multi-step sequences

The system SHALL provide a ``_workflows.py`` module at
``tests/bdd/step_defs/_workflows.py`` containing Python helper
functions for each multi-step Gherkin sequence that appears in
≥3 scenarios across the BDD suite.

Each helper SHALL:

- Be a plain Python function (no ``@given``/``@when``/``@then``
  decorator) — the file is a helper library, not a step
  registry.
- Take ``page`` and ``live_url`` as positional arguments (matches
  the step-def signature so wrappers can call helpers directly).
- Take any scenario-specific values as keyword arguments with
  sensible defaults (e.g. ``pct_rfpos: int = 50``).
- Document the data-testids it touches in a module-level
  comment so PR review can catch UI drift.

#### Scenario: Helpers live in _workflows.py

- **WHEN** the BDD suite grows a new multi-step setup that
  appears in ≥3 scenarios
- **THEN** a new helper function is added to
  ``tests/bdd/step_defs/_workflows.py``
- **AND** the helper takes ``page`` and ``live_url`` as
  positional args
- **AND** the helper has no pytest-bdd decorator

### Requirement: Thin step-wrapper for each helper

The system SHALL provide a thin step-definition wrapper in
``tests/bdd/step_defs/`` (e.g. ``common_steps.py``) for each
helper in ``_workflows.py``. The wrapper SHALL:

- Be a single ``@given``/``@when``/``@then`` function with one
  positional body (typically 3 lines: call the helper).
- Use a PT-BR step text matching the helper's name (e.g.
  ``Que estou logado como "<profile>"`` wraps
  ``login_and_pick_profile``).
- Use ``parsers.parse`` or ``parsers.re`` if the step text
  carries captured parameters; otherwise a plain string match.

#### Scenario: Login helper wrapped as a single step

- **WHEN** a scenario needs to log in as a profile
- **AND** the scenario does NOT test the login flow itself
- **THEN** the scenario writes the single step
  ``Quando que estou logado como "<profile>"``
- **AND** the step invokes
  ``login_and_pick_profile(page, live_url, profile)`` from
  ``_workflows.py``
- **AND** the scenario contains no other login-related steps

### Requirement: Carve-out — login-tester scenarios use inline steps

The system SHALL NOT use the login step wrapper in scenarios
that exist specifically to test the login flow. Specifically:

- Every scenario in ``tests/bdd/features/login.feature`` MUST
  contain the inline login steps
  (``que estou na página "/login"`` →
  ``clico no botão do perfil``).
- Every scenario in ``tests/bdd/features/profile_isolation.feature``
  MUST contain the inline login AND logout steps (these
  scenarios test the cross-profile transition).

#### Scenario: login.feature uses inline steps

- **WHEN** ``tests/bdd/features/login.feature`` is collected
- **THEN** every scenario in that file contains the inline
  login step sequence
- **AND** no scenario in that file uses the
  ``que estou logado como ...`` wrapper

#### Scenario: profile_isolation.feature uses inline steps

- **WHEN** ``tests/bdd/features/profile_isolation.feature`` is
  collected
- **THEN** every scenario in that file contains the inline
  login AND logout step sequences
- **AND** no scenario in that file uses the
  ``que estou logado como ...`` wrapper

### Requirement: Single source of truth for flow changes

When the underlying business flow changes (e.g. login form
adds a 2FA field; class creation gains a 3rd required
attribute; asset modal layout changes), the operator SHALL
edit the Python helper in ``_workflows.py`` ONCE. All scenarios
that use the corresponding step wrapper SHALL pick up the new
behavior automatically.

#### Scenario: Login form change propagates via helper

- **WHEN** the login form gains a new field (e.g. 2FA token)
- **AND** the operator edits ``login_and_pick_profile`` in
  ``_workflows.py`` to fill the new field
- **THEN** every scenario that uses the
  ``que estou logado como ...`` wrapper inherits the new
  behavior without any edits to its ``.feature`` file

### Requirement: Helper count ceiling

The system SHALL NOT exceed 10 helper functions in
``_workflows.py``. If a new multi-step setup pushes the helper
count above 10, the operator SHALL re-evaluate whether the
suite's scenarios share enough structure to justify another
helper, or whether the new setup is too specific to warrant
inline steps.

#### Scenario: Helper count stays within ceiling

- **WHEN** ``tests/bdd/step_defs/_workflows.py`` is inspected
- **THEN** the file contains ≤10 function definitions
- **AND** each function has a docstring describing the flow
  it encapsulates
