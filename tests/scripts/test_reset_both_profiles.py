"""Unit tests for ``scripts.reset_both_profiles`` — pure orchestration logic.

The wrapper opens one ``SessionLocal()``, calls ``run_reset`` once
for ``italo`` then once for ``ana`` (in order), and prints a
per-profile ``classes=… assets=… positions=…`` line. If a profile's
``run_reset`` raises (validation abort), the failure is scoped to
that profile — the other profile's earlier data remains intact, and
the wrapper exits non-zero.

These tests monkey-patch ``run_reset`` so they exercise the
orchestration without spinning up a real DB.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from scripts.reset_both_profiles import main


def test_main_invokes_run_reset_for_both_profiles_in_order(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The wrapper calls ``run_reset`` for every profile in
    ``PROFILES`` — the canonical pair (``italo`` + ``ana``) plus
    the F01 fixture (``italo_rf2``).

    We don't care about the rest of the call signature (the wrapper
    reads the CSVs and passes them in); only the order + the profile
    names matter. The order matches ``PROFILES`` so the per-profile
    reset is deterministic across runs.
    """
    call_log: list[tuple[str, str, str, str]] = []

    def fake_run_reset(db, profile, classes, assets, positions):
        call_log.append(
            (profile, type(classes).__name__, type(assets).__name__, type(positions).__name__)
        )
        return {"classes": 6, "assets": 10, "positions": 5}

    def fake_load_classes(profile):
        return []

    def fake_load_assets(profile):
        return []

    def fake_load_positions(profile):
        return []

    with (
        patch("scripts.reset_both_profiles.run_reset", side_effect=fake_run_reset),
        patch("scripts.reset_both_profiles.load_classes", side_effect=fake_load_classes),
        patch("scripts.reset_both_profiles.load_assets", side_effect=fake_load_assets),
        patch("scripts.reset_both_profiles.load_positions", side_effect=fake_load_positions),
        patch("scripts.reset_both_profiles.SessionLocal"),
    ):
        rc = main()

    assert rc == 0
    from scripts.seed_from_csv import PROFILES

    assert [name for name, *_ in call_log] == list(PROFILES)
    captured = capsys.readouterr()
    for profile in PROFILES:
        assert f"profile={profile} mode=reset classes=6 assets=10 positions=5" in captured.out, (
            f"missing log line for {profile!r} in {captured.out!r}"
        )


def test_main_prints_per_profile_counts(capsys: pytest.CaptureFixture[str]) -> None:
    """Each profile gets a ``profile=X mode=reset classes=… assets=… positions=…`` line.

    The exact counts come from ``run_reset``'s return value; the
    wrapper just forwards them. Asserts on the shape of the line so
    a future refactor doesn't accidentally drop a field.
    """

    def fake_run_reset(db, profile, classes, assets, positions):
        return {"classes": 7, "assets": 13, "positions": 11}

    with (
        patch("scripts.reset_both_profiles.run_reset", side_effect=fake_run_reset),
        patch("scripts.reset_both_profiles.load_classes", return_value=[]),
        patch("scripts.reset_both_profiles.load_assets", return_value=[]),
        patch("scripts.reset_both_profiles.load_positions", return_value=[]),
        patch("scripts.reset_both_profiles.SessionLocal"),
    ):
        main()

    captured = capsys.readouterr()
    from scripts.seed_from_csv import PROFILES

    for profile in PROFILES:
        expected = "classes=7 assets=13 positions=11"
        line = next(r for r in captured.out.splitlines() if r.startswith(f"profile={profile}"))
        assert expected in line, f"missing fields in {line!r}"


def test_main_exits_non_zero_when_one_profile_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """A failure in ``run_reset`` (via ``SystemExit`` from validation) is scoped to that profile.

    The wrapper increments the failure count and exits non-zero. The
    other profile's ``run_reset`` still runs because the wrapper
    catches ``SystemExit`` per-profile and continues.
    """

    from scripts.seed_from_csv import PROFILES

    fail_profile = PROFILES[0]
    # Preserve order so we know which profile(s) ran after the failure.
    failures: list[str] = []

    def fake_run_reset(db, profile, classes, assets, positions):
        if profile == fail_profile:
            failures.append(profile)
            # seed_from_csv.abort() does sys.exit(1) on validation
            # failures; emulate by raising SystemExit.
            raise SystemExit(1)
        return {"classes": 6, "assets": 10, "positions": 5}

    with (
        patch("scripts.reset_both_profiles.run_reset", side_effect=fake_run_reset),
        patch("scripts.reset_both_profiles.load_classes", return_value=[]),
        patch("scripts.reset_both_profiles.load_assets", return_value=[]),
        patch("scripts.reset_both_profiles.load_positions", return_value=[]),
        patch("scripts.reset_both_profiles.SessionLocal"),
    ):
        rc = main()

    assert rc == 1, f"expected 1 failure, got rc={rc}"
    captured = capsys.readouterr()
    assert f"profile={fail_profile} FAILED" in captured.err
    # The other profiles still ran.
    for other in PROFILES[1:]:
        assert f"profile={other} mode=reset" in captured.out


def test_main_exits_with_failure_count_when_all_profiles_fail(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """All-profile failures → exit code equals ``len(PROFILES)``.

    Tracks the number of seeded profiles so adding the F01 fixture
    (``italo_rf2``) does not silently lower the bar.
    """

    def fake_run_reset(db, profile, classes, assets, positions):
        raise SystemExit(1)

    with (
        patch("scripts.reset_both_profiles.run_reset", side_effect=fake_run_reset),
        patch("scripts.reset_both_profiles.load_classes", return_value=[]),
        patch("scripts.reset_both_profiles.load_assets", return_value=[]),
        patch("scripts.reset_both_profiles.load_positions", return_value=[]),
        patch("scripts.reset_both_profiles.SessionLocal"),
    ):
        rc = main()

    from scripts.seed_from_csv import PROFILES

    assert rc == len(PROFILES), f"expected {len(PROFILES)} failures, got rc={rc}"
