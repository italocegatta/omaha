"""Measure BDD step reuse — count Gherkin lines per scenario before/after.

Compares the refactored 6 ``.feature`` files in
``tests/bdd/features/`` against the baseline tracked in
``scripts/baseline_gherkin_lines.json`` (a JSON dict mapping
``scenario_id`` → Gherkin line count). Asserts the
post-refactor reduction is ≥ 25 %.

Why a hard threshold
--------------------
The change's value proposition is "edit one workflow instead
of N scenarios" — that only holds if the Gherkin actually
shrinks. A 25 % floor matches the proposal's "5–10 lines per
scenario instead of 15–25" claim and is loose enough to absorb
one-off padding (Examples blocks, blank lines) without
letting a silent regression slip through.

Usage
-----
::

    uv run python scripts/measure_bdd_reuse.py

The script reads the post-refactor features directly from
``tests/bdd/features/`` (no second copy of the source of
truth). The baseline JSON must be refreshed manually when
extracting the numbers from a ``git checkout`` of the pre-
refactor commit:

::

    git checkout main~ -- tests/bdd/features
    uv run python scripts/measure_bdd_reuse.py --emit-baseline \\
        > scripts/baseline_gherkin_lines.json
    git checkout -
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FEATURES_DIR = REPO_ROOT / "tests" / "bdd" / "features"
BASELINE_PATH = REPO_ROOT / "scripts" / "baseline_gherkin_lines.json"

REFACTORED_FEATURES: tuple[str, ...] = (
    "class_crud.feature",
    "asset_crud.feature",
    "import.feature",
    "target_pct.feature",
    "derived_display.feature",
    "full_journey.feature",
)
CARVE_OUT_FEATURES: tuple[str, ...] = (
    "login.feature",
    "profile_isolation.feature",
)
MIN_REDUCTION_PCT = 25.0


def _scenario_id(feature_filename: str, scenario_name: str) -> str:
    return f"{feature_filename}::{scenario_name}"


def _feature_gherkin_lines(feature_path: Path) -> dict[str, int]:
    """Return ``{scenario_id: gherkin_line_count}`` for one feature file.

    A "Gherkin line" is any non-blank line inside the scenario
    block (``Cenário:`` / ``Esquema do Cenário:``) until the
    next scenario or end-of-file. ``Exemplos:`` blocks are
    included — they are Gherkin syntax the operator authors.
    """
    text = feature_path.read_text(encoding="utf-8")
    counts: dict[str, int] = {}
    current_name: str | None = None
    current_lines = 0
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith(("Cenário:", "Esquema do Cenário:", "Scenario:", "Scenario Outline:")):
            if current_name is not None:
                counts[current_name] = current_lines
            current_name = line.split(":", 1)[1].strip()
            current_lines = 0
            continue
        if line.startswith(("Funcionalidade:", "Feature:", "Contexto:", "Background:", "#")):
            if current_name is not None:
                counts[current_name] = current_lines
                current_name = None
            continue
        if current_name is not None and line:
            current_lines += 1
    if current_name is not None:
        counts[current_name] = current_lines
    return counts


def collect_current() -> dict[str, int]:
    """Collect Gherkin line counts for the 6 refactored features."""
    counts: dict[str, int] = {}
    for feature_filename in REFACTORED_FEATURES:
        feature_path = FEATURES_DIR / feature_filename
        if not feature_path.exists():
            print(f"warning: {feature_filename} not found, skipping", file=sys.stderr)
            continue
        for scenario_name, line_count in _feature_gherkin_lines(feature_path).items():
            counts[_scenario_id(feature_filename, scenario_name)] = line_count
    return counts


def emit_baseline() -> None:
    """Print the current counts as JSON to stdout (for snapshotting)."""
    print(json.dumps(collect_current(), indent=2, sort_keys=True))


def compare(baseline: dict[str, int], current: dict[str, int]) -> int:
    """Compare current counts to baseline; return process exit code."""
    if not baseline:
        print("error: baseline is empty — pass --baseline <path> or seed the JSON", file=sys.stderr)
        return 2
    missing = sorted(set(baseline) - set(current))
    if missing:
        print(
            f"error: {len(missing)} baseline scenarios missing from current features "
            f"(e.g. {missing[0]!r}) — did the refactor rename a scenario?",
            file=sys.stderr,
        )
        return 2
    total_before = sum(baseline[s] for s in baseline)
    total_after = sum(current[s] for s in baseline)
    reduction_pct = (total_before - total_after) / total_before * 100
    print(f"baseline scenarios: {len(baseline)}")
    print(f"total Gherkin lines before: {total_before}")
    print(f"total Gherkin lines after:  {total_after}")
    print(f"reduction: {reduction_pct:.1f}% (floor: {MIN_REDUCTION_PCT:.1f}%)")
    per_scenario = sorted(
        ((s, baseline[s], current[s]) for s in baseline),
        key=lambda row: row[1] - row[2],
    )
    print("top 5 shrinks:")
    for scenario_id, before, after in per_scenario[:5]:
        print(f"  {scenario_id}: {before} → {after} (-{before - after})")
    if reduction_pct < MIN_REDUCTION_PCT:
        print(
            f"FAIL: reduction {reduction_pct:.1f}% below the {MIN_REDUCTION_PCT:.1f}% "
            f"floor — refactor did not pay off",
            file=sys.stderr,
        )
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--baseline",
        type=Path,
        default=BASELINE_PATH,
        help=f"path to baseline JSON (default: {BASELINE_PATH})",
    )
    parser.add_argument(
        "--emit-baseline",
        action="store_true",
        help="print current counts as JSON to stdout (snapshot pre-refactor state) and exit",
    )
    args = parser.parse_args()
    if args.emit_baseline:
        emit_baseline()
        return 0
    baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
    current = collect_current()
    return compare(baseline, current)


if __name__ == "__main__":
    sys.exit(main())
