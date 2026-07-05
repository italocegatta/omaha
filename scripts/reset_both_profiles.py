"""Dual-profile reset wrapper.

The canonical dev delivery task (``uv run task db-reset``) seeds
all seeded profiles from their CSV triplets in one invocation, so
the dashboard renders populated (not empty) after a fresh seed.

Profiles seeded (see :data:`scripts.seed_from_csv.PROFILES`):

* ``italo`` — Italo / Italo
* ``ana`` — Ana / Ana

F07 retired the F01 ``Italo RF2`` fixture profile (it was a
synthetic multi-profile row used to exercise the F01 intra-User
household aggregate; F06 superseded the toggle with cross-User
full-join, and F07 promoted Família to a sentinel peer in the
profile-switcher chip). The wrapper iterates only the two real
profiles; the Família sentinel is owned by the password-less
``User("family")`` and carries zero ``AssetClass`` rows (see
``omaha/seed.py``).

This module is a thin wrapper around :func:`scripts.seed_from_csv.run_reset`
that opens one :class:`SessionLocal`, runs the reset for each
profile in order, and prints a per-profile count line. If a
profile's CSV fails validation (sum != 100, missing class
reference, etc.), the failure is scoped to that profile — the
other profiles' earlier data remains intact.

Single-profile entry points remain reachable via
``uv run task db-seed-from-csv -- --profile ana`` etc. (back-compat
for callers that only want one profile).

Run with::

    uv run python -m scripts.reset_both_profiles
"""

from __future__ import annotations

import sys

from omaha.db import SessionLocal
from scripts.seed_from_csv import PROFILES, load_assets, load_classes, load_positions, run_reset


def main() -> int:
    """Reset + reseed all profiles in one session; print per-profile counts.

    Returns the count of profiles that failed (0 = success). The exit
    code is the count of failures so a partial failure surfaces
    distinctly from a full success in CI / shell scripts.
    """
    db = SessionLocal()
    failures = 0
    try:
        for profile in PROFILES:
            try:
                classes = load_classes(profile)
                assets = load_assets(profile)
                positions = load_positions(profile)
                counts = run_reset(db, profile, classes, assets, positions)
                print(
                    f"profile={profile} mode=reset "
                    f"classes={counts['classes']} "
                    f"assets={counts['assets']} "
                    f"positions={counts['positions']}"
                )
            except SystemExit as exc:
                # seed_from_csv.abort() calls sys.exit(1) on validation
                # failures. Treat as a profile-level failure so the
                # other profile's data remains intact.
                print(
                    f"profile={profile} FAILED: validation aborted (exit {exc.code})",
                    file=sys.stderr,
                )
                failures += 1
    finally:
        db.close()

    return failures


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
