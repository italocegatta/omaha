"""Pytest-bdd scenario bindings for the BDD e2e suite.

Each :func:`pytest_bdd.scenario` binds a Gherkin scenario in
``tests/bdd/features/*.feature`` to a pytest test function. The
``Esquema do Cenário`` + ``Exemplos`` blocks in each feature
file drive the dual-profile parametrization natively — pytest
creates one test instance per Examples row.

Step definitions live in ``tests/bdd/step_defs/`` — this module
is purely the scenario ↔ test-function glue.
"""

from __future__ import annotations

from pytest_bdd import scenario

# Side-effect imports: register all step definitions with pytest-bdd.
# pytest-bdd scans the test file + conftest.py for steps but does NOT
# walk subdirectories — these explicit imports are the bridge.
from tests.bdd.step_defs import (  # noqa: F401
    asset_steps,
    class_steps,
    common_steps,
    dashboard_steps,
    import_steps,
    target_steps,
)

# ─────────────────────────────────────────────────────────────────────
# login.feature
# ─────────────────────────────────────────────────────────────────────


@scenario("login.feature", "Login + dashboard direto", features_base_dir="tests/bdd/features")
def test_login_ok():
    pass


@scenario("login.feature", "Login fail — senha errada", features_base_dir="tests/bdd/features")
def test_login_fail_wrong_password():
    pass


# ─────────────────────────────────────────────────────────────────────
# class_crud.feature
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "class_crud.feature",
    "Inline create 2 classes — soma 100%",
    features_base_dir="tests/bdd/features",
)
def test_inline_create_2_classes_soma_100():
    pass


@scenario(
    "class_crud.feature",
    "Inline create 2 classes — soma 90%",
    features_base_dir="tests/bdd/features",
)
def test_inline_create_2_classes_soma_90():
    pass


@scenario(
    "class_crud.feature",
    "Inline create 2 classes — soma 110%",
    features_base_dir="tests/bdd/features",
)
def test_inline_create_2_classes_soma_110():
    pass


@scenario(
    "class_crud.feature",
    "Inline add + PATCH class target",
    features_base_dir="tests/bdd/features",
)
def test_inline_add_with_patch_target():
    pass


@scenario(
    "target_pct.feature",
    "PATCH per-asset total reflects in dashboard",
    features_base_dir="tests/bdd/features",
)
def test_patch_per_asset_target():
    pass


@scenario(
    "class_crud.feature", "Negative — duplicate class name", features_base_dir="tests/bdd/features"
)
def test_duplicate_class_name_409():
    pass


# ─────────────────────────────────────────────────────────────────────
# asset_crud.feature
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "asset_crud.feature",
    "Manual add 4 ativos não-igual por classe",
    features_base_dir="tests/bdd/features",
)
def test_manual_add_4_assets_unequal():
    pass


@scenario(
    "asset_crud.feature",
    "Edição inline preserva a posição visual da linha (row pin)",
    features_base_dir="tests/bdd/features",
)
def test_row_pin_preserves_visual_position():
    pass


# ─────────────────────────────────────────────────────────────────────
# import.feature
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "import.feature",
    "Import 4-row CSV happy (auto-match por categoria)",
    features_base_dir="tests/bdd/features",
)
def test_import_happy_auto_match():
    pass


@scenario("import.feature", "Import CSV vazio", features_base_dir="tests/bdd/features")
def test_import_empty_csv():
    pass


# ─────────────────────────────────────────────────────────────────────
# target_pct.feature
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "target_pct.feature",
    "PATCH per-class target reflects in dashboard",
    features_base_dir="tests/bdd/features",
)
def test_patch_per_class_target():
    pass


@scenario(
    "target_pct.feature",
    "Per-class sum off-100 é aceito (D006)",
    features_base_dir="tests/bdd/features",
)
def test_per_class_sum_off_100_accepted_target_pct():
    pass


# ─────────────────────────────────────────────────────────────────────
# derived_display.feature
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "derived_display.feature",
    "Derived portfolio % recomputes on class PATCH",
    features_base_dir="tests/bdd/features",
)
def test_derived_recomputes_on_class_patch():
    pass


@scenario(
    "derived_display.feature",
    "Derived portfolio % recomputes on asset PATCH",
    features_base_dir="tests/bdd/features",
)
def test_derived_recomputes_on_asset_patch():
    pass


# ─────────────────────────────────────────────────────────────────────
# profile_sharing.feature (direct-landing-with-header-profile-switcher:
# was profile_isolation.feature; renamed + flipped assertions because
# any logged-in user can now view any profile via the header chip).
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "profile_sharing.feature",
    "Ana vê as classes de Italo após trocar pelo chip",
    features_base_dir="tests/bdd/features",
)
def test_ana_sees_italo_classes_after_switch():
    pass


@scenario(
    "profile_sharing.feature",
    "Italo vê as classes de Ana após trocar pelo chip",
    features_base_dir="tests/bdd/features",
)
def test_italo_sees_ana_classes_after_switch():
    pass


# ─────────────────────────────────────────────────────────────────────
# dashboard_inline_editing.feature
# dashboard-inline-edit-friction: one-click focus + empty→zero.
# ─────────────────────────────────────────────────────────────────────


@scenario(
    "dashboard_inline_editing.feature",
    "Clique único no alvo da classe foca o input",
    features_base_dir="tests/bdd/features",
)
def test_click_class_target_pill_focuses_input():
    pass


@scenario(
    "dashboard_inline_editing.feature",
    "Clique único no alvo % classe do ativo foca o input",
    features_base_dir="tests/bdd/features",
)
def test_click_asset_class_cell_focuses_input():
    pass


@scenario(
    "dashboard_inline_editing.feature",
    "Clique único no alvo % total do ativo foca o input",
    features_base_dir="tests/bdd/features",
)
def test_click_asset_total_cell_focuses_input():
    pass


@scenario(
    "dashboard_inline_editing.feature",
    "Limpar o alvo da classe e pressionar Enter salva zero",
    features_base_dir="tests/bdd/features",
)
def test_clear_class_target_enter_saves_zero():
    pass


@scenario(
    "dashboard_inline_editing.feature",
    "Limpar o alvo % classe do ativo e pressionar Enter salva zero",
    features_base_dir="tests/bdd/features",
)
def test_clear_asset_class_target_enter_saves_zero():
    pass


@scenario(
    "dashboard_inline_editing.feature",
    "Limpar o alvo % total do ativo e pressionar Enter salva zero",
    features_base_dir="tests/bdd/features",
)
def test_clear_asset_total_target_enter_saves_zero():
    pass


@scenario(
    "dashboard_inline_editing.feature",
    "Tirar o foco de input vazio da classe salva zero",
    features_base_dir="tests/bdd/features",
)
def test_blur_empty_class_input_saves_zero():
    pass
