"""Dual-profile reset wrapper.

The canonical dev delivery task (``uv run task db-reset``) seeds
BOTH seeded profiles (Italo + Ana) from their CSV triplets in one
invocation, so Ana's dashboard renders populated (not empty) after
a fresh seed.

This module is a thin wrapper around :func:`scripts.seed_from_csv.run_reset`
that opens one :class:`SessionLocal`, runs the reset for ``italo``
then ``ana`` in order, and prints a per-profile count line. If a
profile's CSV fails validation (sum != 100, missing class
reference, etc.), the failure is scoped to that profile — the
other profile's earlier data remains intact.

Single-profile entry points remain reachable via
``uv run task db-seed-from-csv -- --profile ana`` etc. (back-compat
for callers that only want one profile).

Run with::

    uv run python -m scripts.reset_both_profiles
"""

from __future__ import annotations

import sys

from omaha.db import SessionLocal
from scripts.seed_from_csv import load_assets, load_classes, load_positions, run_reset


def main() -> int:
    """Reset + reseed both profiles in one session; print per-profile counts.

    Returns the count of profiles that failed (0 = success). The exit
    code is the count of failures so a partial failure surfaces
    distinctly from a full success in CI / shell scripts.
    """
    db = SessionLocal()
    failures = 0
    try:
        for profile in ("italo", "ana"):
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
