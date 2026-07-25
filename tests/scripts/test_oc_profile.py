"""Unit tests for ``scripts.oc_profile`` — profile resolution and env export.

Pure-function tests, no DB, no HTTP, no subprocess. Exercises:
- Built-in profile definitions (all 4 profiles, all 7 roles)
- Resolution chain priority (CLI > env > TOML > built-in)
- TOML merge/override behavior
- Env var export naming and values
- ``--list-profiles`` output
- Error handling for unknown profiles
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.oc_profile import (
    BUILTIN_PROFILES,
    DEFAULT_PROFILE,
    ROLES,
    export_env_vars,
    main,
    resolve_profile,
)

# ── Task 7.1: resolve_profile returns correct mapping for each built-in ─────


class TestResolveProfileBuiltin:
    """Each built-in profile resolves to the expected role→Profile map."""

    @pytest.mark.parametrize("profile_name", sorted(BUILTIN_PROFILES))
    def test_all_roles_present(self, profile_name: str) -> None:
        result = resolve_profile(profile_name)
        assert set(result.keys()) == set(ROLES)

    def test_openai_cheap_values(self) -> None:
        result = resolve_profile("openai-cheap")
        for role in ROLES:
            assert result[role].provider == "openai"
            assert result[role].model == "gpt-5.4-mini"
            assert result[role].effort == "high"

    def test_openai_balanced_values(self) -> None:
        result = resolve_profile("openai-balanced")
        # Heavy roles use gpt-5.4
        for role in ("roadmap", "propose", "apply", "explore", "slice"):
            assert result[role].model == "gpt-5.4"
            assert result[role].effort == "high"
        # Light roles use gpt-5.4-mini
        for role in ("review", "finalize"):
            assert result[role].model == "gpt-5.4-mini"
            assert result[role].effort == "high"

    def test_openai_xiaomi_balanced_values(self) -> None:
        result = resolve_profile("openai-xiaomi-balanced")
        # OpenAI roles
        for role in ("roadmap", "slice"):
            assert result[role].provider == "openai"
            assert result[role].model == "gpt-5.4-mini"
            assert result[role].effort == "high"
        # Xiaomi pro roles
        for role in ("propose", "apply", "explore"):
            assert result[role].provider == "xiaomi-token-plan-sgp"
            assert result[role].model == "mimo-v2.5-pro"
            assert result[role].effort == "medium"
        # Xiaomi base roles
        for role in ("review", "finalize"):
            assert result[role].provider == "xiaomi-token-plan-sgp"
            assert result[role].model == "mimo-v2.5"
            assert result[role].effort == "medium"

    def test_xiaomi_balanced_values(self) -> None:
        result = resolve_profile("xiaomi-balanced")
        for role in ROLES:
            assert result[role].provider == "xiaomi-token-plan-sgp"
            assert result[role].effort == "medium"
        # Pro roles
        for role in ("roadmap", "propose", "apply", "explore", "slice"):
            assert result[role].model == "mimo-v2.5-pro"
        # Base roles
        for role in ("review", "finalize"):
            assert result[role].model == "mimo-v2.5"


# ── Task 7.2: resolve_profile raises ValueError for unknown ─────────────────


class TestResolveProfileUnknown:
    def test_unknown_name_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown profile: 'nonexistent'"):
            resolve_profile("nonexistent")

    def test_error_message_lists_available(self) -> None:
        with pytest.raises(ValueError) as exc_info:
            resolve_profile("bogus")
        msg = str(exc_info.value)
        for name in BUILTIN_PROFILES:
            assert name in msg


# ── Task 7.3: Resolution chain priority (CLI > env > TOML > built-in) ───────


class TestResolutionChain:
    def test_cli_arg_takes_precedence(self, tmp_path: Path) -> None:
        toml = tmp_path / "profiles.toml"
        toml.write_text('[default]\nprofile = "openai-cheap"\n')
        # CLI arg wins over TOML default
        result = resolve_profile(name="xiaomi-balanced", toml_path=toml)
        assert result["roadmap"].model == "mimo-v2.5-pro"

    def test_env_var_overrides_toml(self, tmp_path: Path) -> None:
        toml = tmp_path / "profiles.toml"
        toml.write_text('[default]\nprofile = "openai-cheap"\n')
        with patch.dict(os.environ, {"OPENCODE_PROFILE": "xiaomi-balanced"}):
            result = resolve_profile(toml_path=toml)
            assert result["roadmap"].model == "mimo-v2.5-pro"

    def test_toml_default_overrides_builtin(self, tmp_path: Path) -> None:
        toml = tmp_path / "profiles.toml"
        toml.write_text('[default]\nprofile = "openai-cheap"\n')
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OPENCODE_PROFILE", None)
            result = resolve_profile(toml_path=toml)
            assert result["roadmap"].model == "gpt-5.4-mini"

    def test_builtin_default_when_nothing_set(self, tmp_path: Path) -> None:
        toml = tmp_path / "nonexistent.toml"
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OPENCODE_PROFILE", None)
            result = resolve_profile(toml_path=toml)
            assert result["roadmap"].model == "mimo-v2.5-pro"
            assert result["roadmap"].provider == "xiaomi-token-plan-sgp"


# ── Task 7.4: TOML merge overrides built-in correctly ───────────────────────


class TestTomlMerge:
    def test_toml_overrides_builtin_profile(self, tmp_path: Path) -> None:
        toml = tmp_path / "profiles.toml"
        toml.write_text(
            textwrap.dedent("""\
            [default]
            profile = "openai-cheap"

            [profiles.openai-cheap.roadmap]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"
        """)
        )
        result = resolve_profile(toml_path=toml)
        # TOML overrides the roadmap model from gpt-5.4-mini to gpt-5.4
        assert result["roadmap"].model == "gpt-5.4"
        # Other roles keep built-in values
        assert result["propose"].model == "gpt-5.4-mini"

    def test_toml_custom_profile(self, tmp_path: Path) -> None:
        toml = tmp_path / "profiles.toml"
        toml.write_text(
            textwrap.dedent("""\
            [profiles.my-custom.roadmap]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"

            [profiles.my-custom.propose]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"

            [profiles.my-custom.apply]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"

            [profiles.my-custom.review]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"

            [profiles.my-custom.finalize]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"

            [profiles.my-custom.explore]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"

            [profiles.my-custom.slice]
            provider = "openai"
            model = "gpt-5.4"
            effort = "high"
        """)
        )
        result = resolve_profile(name="my-custom", toml_path=toml)
        for role in ROLES:
            assert result[role].model == "gpt-5.4"
            assert result[role].provider == "openai"

    def test_toml_absent_uses_builtin_only(self, tmp_path: Path) -> None:
        toml = tmp_path / "nonexistent_profiles.toml"
        result = resolve_profile(name="openai-cheap", toml_path=toml)
        assert result["roadmap"].model == "gpt-5.4-mini"


# ── Task 7.5: Env var export produces correct variable names and values ──────


class TestExportEnvVars:
    def test_env_vars_set_for_all_roles(self) -> None:
        profile = resolve_profile("openai-cheap")
        with patch.dict(os.environ, {}, clear=False):
            # Clear any existing OPENCODE_ vars
            for key in list(os.environ):
                if key.startswith("OPENCODE_") and key != "OPENCODE_PROFILE":
                    del os.environ[key]
            export_env_vars(profile)
            for role in ROLES:
                prefix = f"OPENCODE_{role.upper()}"
                assert os.environ[f"{prefix}_MODEL"] == "gpt-5.4-mini"
                assert os.environ[f"{prefix}_PROVIDER"] == "openai"
                assert os.environ[f"{prefix}_EFFORT"] == "high"

    def test_xiaomi_profile_effort_medium(self) -> None:
        profile = resolve_profile("xiaomi-balanced")
        with patch.dict(os.environ, {}, clear=False):
            for key in list(os.environ):
                if key.startswith("OPENCODE_") and key != "OPENCODE_PROFILE":
                    del os.environ[key]
            export_env_vars(profile)
            for role in ROLES:
                prefix = f"OPENCODE_{role.upper()}"
                assert os.environ[f"{prefix}_EFFORT"] == "medium"

    def test_mixed_profile_correct_per_role(self) -> None:
        profile = resolve_profile("openai-xiaomi-balanced")
        with patch.dict(os.environ, {}, clear=False):
            for key in list(os.environ):
                if key.startswith("OPENCODE_") and key != "OPENCODE_PROFILE":
                    del os.environ[key]
            export_env_vars(profile)
            # Roadmap is OpenAI
            assert os.environ["OPENCODE_ROADMAP_PROVIDER"] == "openai"
            assert os.environ["OPENCODE_ROADMAP_MODEL"] == "gpt-5.4-mini"
            # Propose is Xiaomi
            assert os.environ["OPENCODE_PROPOSE_PROVIDER"] == "xiaomi-token-plan-sgp"
            assert os.environ["OPENCODE_PROPOSE_MODEL"] == "mimo-v2.5-pro"


# ── Task 7.6: --list-profiles prints all four profiles ──────────────────────


class TestListProfiles:
    def test_list_profiles_prints_all_four(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--list-profiles"])
        assert exit_code == 0
        output = capsys.readouterr().out
        for name in BUILTIN_PROFILES:
            assert name in output

    def test_list_profiles_mentions_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        main(["--list-profiles"])
        output = capsys.readouterr().out
        assert DEFAULT_PROFILE in output
        assert "(default)" in output


# ── Error handling ───────────────────────────────────────────────────────────


class TestErrorHandling:
    def test_unknown_profile_exits_1(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--profile", "nonexistent"])
        assert exit_code == 1
        err = capsys.readouterr().err
        assert "Unknown profile" in err

    def test_export_only_mode(self, capsys: pytest.CaptureFixture[str]) -> None:
        exit_code = main(["--profile", "openai-cheap", "--export-only"])
        assert exit_code == 0
        output = capsys.readouterr().out
        assert "OPENCODE_ROADMAP_MODEL=gpt-5.4-mini" in output
        assert "OPENCODE_ROADMAP_PROVIDER=openai" in output
        assert "OPENCODE_ROADMAP_EFFORT=high" in output
