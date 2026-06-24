## MODIFIED Requirements

### Requirement: Per-workflow carve-out table

The system SHALL enforce the per-workflow carve-out contract
via the ``@carve_out`` decorator in
``tests/bdd/step_defs/_carve_out.py``. Each workflow that
must not be used by certain feature files (because those
files test the flow itself) declares its carve-out via:

```python
@carve_out(
    files=frozenset({"login.feature", "profile_isolation.feature"}),
    step_regex=r"estou logado como",
)
def login_and_pick_profile(...): ...
```

The contract test
``test_carve_out_files_use_inline_steps`` SHALL parse these
decorators via AST and assert that each carve-out file does
NOT contain a step matching the workflow's ``step_regex``.
Adding a new carve-out workflow = add the decorator; the
test enforces automatically — no hardcoded regex dict to
maintain.

A scenario in a carve-out file MAY still use wrappers for
workflows OTHER than the carved-out one.

#### Scenario: Carve-out decorator enforces inline-only

- **WHEN** a workflow is annotated with
  ``@carve_out(files={"X.feature"}, step_regex=r"Y")``
- **AND** ``X.feature`` contains a step matching ``r"Y"``
- **THEN** the contract test
  ``test_carve_out_files_use_inline_steps`` fails with a
  message naming the workflow and the offending file

#### Scenario: Carve-out only applies to annotated workflows

- **WHEN** a workflow is NOT annotated with ``@carve_out``
- **THEN** the contract test does not assert anything about
  its usage in any feature file

### Requirement: Python workflow for repeated multi-step sequences

The system SHALL provide a ``_workflows.py`` module at
``tests/bdd/step_defs/_workflows.py`` containing Python
workflow functions for each multi-step Gherkin sequence
that appears in ≥2 scenarios with a clear growth trend.

**Threshold is mandatory.** A workflow with 0 or 1 callers
violates this requirement and SHALL NOT land. If the only
caller uses a hardcoded payload (e.g. ``DEFAULT_FOUR_ASSETS``),
either inline the steps in that caller or wait until a 2nd
caller materializes before extracting.

The four remaining workflows as of 2026-06-23:
``login_and_pick_profile`` (14 callers, 7 features),
``create_one_class`` (6 callers, 4 features),
``create_two_default_classes`` (5 callers, 4 features),
``add_one_asset`` (4 callers, 3 features).

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
- **AND** the workflow has ≥2 callers across the BDD
  feature files

### Requirement: Workflow count ceiling

The system SHALL NOT exceed 10 public workflow functions in
``tests/bdd/step_defs/_workflows.py``. If a new multi-step
setup pushes the workflow count above 10, the operator
SHALL re-evaluate whether the suite's scenarios share
enough structure to justify another workflow, or whether
the new setup is too specific to warrant inline steps.

As of 2026-06-23 the file exposes **4 public workflows**:
``login_and_pick_profile``, ``create_one_class``,
``create_two_default_classes``, ``add_one_asset``.
Workflows with 0 or 1 callers are forbidden — they violate
the "≥2 scenarios with growth trend" extraction threshold
and SHALL be deleted before merge (or never created in the
first place).

#### Scenario: Workflow count stays within ceiling

- **WHEN** ``tests/bdd/step_defs/_workflows.py`` is
  inspected
- **THEN** the file contains ≤10 public function
  definitions
- **AND** each function has a docstring describing the flow
  it encapsulates, its data-testids, and its pre-conditions
- **AND** every workflow has ≥2 callers across the BDD
  feature files

## REMOVED Requirements

### Requirement: switch_profile workflow

**REMOVED 2026-06-23.** Was a workflow in
``tests/bdd/step_defs/_workflows.py`` + wrapper
``_w_switched_profile`` in ``common_steps.py``. Had 0
callers across all ``.feature`` files — violated the
"≥2 scenarios with growth trend" extraction threshold.
Deleted in change ``fix-bdd-workflow-reuse-gaps``.

**Reactivation rule:** if a future scenario genuinely
needs mid-test profile switch (e.g. cross-profile
visibility test in a feature file OTHER than
``profile_isolation.feature``), recreate the workflow +
wrapper + ``@carve_out(files={"profile_isolation.feature"},
step_regex=r"troquei para o perfil")`` annotation at that
point. Do NOT pre-create without a 2nd caller.

### Requirement: create_four_assets workflow

**REMOVED 2026-06-23.** Was a workflow in
``tests/bdd/step_defs/_workflows.py`` + wrapper
``_w_four_assets`` in ``asset_steps.py``. Had 1 caller
(``asset_crud.feature::Manual add 4 ativos não-igual por
classe``) — violated the "≥2 scenarios" extraction
threshold. Deleted in change ``fix-bdd-workflow-reuse-gaps``.

The single caller now uses 4× ``_w_one_asset`` inline
(2 lines Gherkin longer than the deleted wrapper, but 0
god-workflow debt). Reactivation rule: if a 2nd scenario
that creates multiple assets with non-equal distribution
lands, recreate the workflow + wrapper.

### Requirement: Carve-out hardcoded regex dict

**REMOVED 2026-06-23.** Was a ``WRAPPER_REGEXES``
``dict[str, str]`` hardcoded in
``tests/bdd/test_workflow_contracts.py`` mapping workflow
names to their Gherkin step regexes. Replaced by
marker-based enforcement (see MODIFIED Requirement:
Per-workflow carve-out table) — carve-out metadata now
lives on the workflow function itself via ``@carve_out``.

## ADDED Requirements

### Requirement: Marker-based carve-out enforcement

The system SHALL provide a ``@carve_out`` decorator in
``tests/bdd/step_defs/_carve_out.py`` that accepts
``files: Iterable[str]`` and ``step_regex: str`` keyword
arguments. The decorator SHALL return a callable that
attaches a ``CarveOut`` frozen dataclass to the function's
``__carve_out__`` attribute and returns the function
unchanged.

The contract test
``test_carve_out_files_use_inline_steps`` SHALL:

1. Parse ``tests/bdd/step_defs/_workflows.py`` via ``ast``
   to discover every top-level ``FunctionDef`` with a
   ``@carve_out(...)`` decorator.
2. For each annotated workflow, parse the decorator
   arguments to extract ``files`` and ``step_regex``
   (accepting both set literals and ``frozenset({...})``
   calls).
3. For each file in ``files``, assert the file body does
   NOT match ``step_regex``.

This eliminates the hardcoded ``WRAPPER_REGEXES`` dict
that required manual maintenance when new carve-out
workflows were added.

#### Scenario: Adding new carve-out workflow

- **WHEN** a contributor adds a new workflow annotated
  with ``@carve_out(files={"X.feature"}, step_regex=...)``
- **AND** ``X.feature`` does not contain a matching step
- **THEN** the contract test passes automatically (no
  manual edit to the test required)

#### Scenario: Carve-out violation caught at unit-test time

- **WHEN** a contributor adds
  ``@carve_out(files={"login.feature"}, step_regex=r"Y")``
  to a new workflow
- **AND** ``login.feature`` contains a step matching
  ``r"Y"``
- **THEN** ``task test-unit`` fails with a message naming
  the workflow, the regex, and the offending file
